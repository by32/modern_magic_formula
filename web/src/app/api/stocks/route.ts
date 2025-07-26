import { NextRequest, NextResponse } from 'next/server';
import Papa from 'papaparse';

interface StockData {
  ticker: string;
  company_name: string;
  sector: string;
  market_cap: number;
  earnings_yield: number;
  roc: number;
  f_score: number;
  magic_formula_rank: number;
  pe_ratio?: number;
  pb_ratio?: number;
}

// Cache data for 5 minutes to avoid excessive GitHub API calls
let dataCache: { data: StockData[], timestamp: number } | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

async function fetchDataFromGitHub(): Promise<StockData[]> {
  // Check cache first
  if (dataCache && Date.now() - dataCache.timestamp < CACHE_DURATION) {
    return dataCache.data;
  }

  try {
    // Fetch from GitHub raw content (public repo)
    const response = await fetch(
      'https://raw.githubusercontent.com/by32/modern_magic_formula/main/data/latest_screening_hybrid.csv',
      { 
        cache: 'no-store',
        headers: {
          'Accept': 'text/csv'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`GitHub fetch failed: ${response.status}`);
    }

    const csvData = await response.text();
    
    // Parse CSV
    const parsed = Papa.parse<StockData>(csvData, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
    });

    if (parsed.errors.length > 0) {
      console.error('CSV parsing errors:', parsed.errors);
    }

    // Update cache
    dataCache = {
      data: parsed.data,
      timestamp: Date.now()
    };

    return parsed.data;
  } catch (error) {
    console.error('Error fetching data from GitHub:', error);
    // Return empty array if fetch fails
    return [];
  }
}

export async function GET(request: NextRequest) {
  try {
    // Fetch fresh data from GitHub
    const stockData = await fetchDataFromGitHub();

    if (!stockData || stockData.length === 0) {
      return NextResponse.json(
        { error: 'No stock data available', stocks: [], total: 0 },
        { status: 503 }
      );
    }

    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '20');
    const minFScore = parseInt(searchParams.get('min_fscore') || '5');
    const minMarketCap = parseFloat(searchParams.get('min_market_cap') || '1000000000');

    // Apply DIY filters
    let filteredData = stockData.filter((stock: StockData) => 
      stock.f_score >= minFScore &&
      stock.market_cap >= minMarketCap &&
      stock.earnings_yield > 0 &&
      stock.roc > 0 &&
      stock.magic_formula_rank <= 100 // Top 100 Magic Formula picks
    );

    // Sort by Magic Formula rank
    filteredData.sort((a, b) => a.magic_formula_rank - b.magic_formula_rank);

    // Apply sector diversification
    const sectorCounts: { [key: string]: number } = {};
    const maxPerSector = Math.max(1, Math.floor(limit / 4)); // Max 25% per sector
    
    const diversifiedPicks: StockData[] = [];
    
    for (const stock of filteredData) {
      const sector = stock.sector || 'Unknown';
      const currentCount = sectorCounts[sector] || 0;
      
      if (currentCount < maxPerSector && diversifiedPicks.length < limit) {
        diversifiedPicks.push(stock);
        sectorCounts[sector] = currentCount + 1;
      }
    }

    // If we don't have enough stocks, fill from remaining
    if (diversifiedPicks.length < limit) {
      const remaining = filteredData.filter(stock => 
        !diversifiedPicks.find(pick => pick.ticker === stock.ticker)
      );
      
      diversifiedPicks.push(...remaining.slice(0, limit - diversifiedPicks.length));
    }

    return NextResponse.json({
      stocks: diversifiedPicks.slice(0, limit),
      total: filteredData.length,
      filters: {
        min_fscore: minFScore,
        min_market_cap: minMarketCap,
        limit
      },
      sector_distribution: sectorCounts,
      data_source: 'github',
      cache_status: dataCache && Date.now() - dataCache.timestamp < CACHE_DURATION ? 'hit' : 'miss'
    });

  } catch (error) {
    console.error('Error in stocks API:', error);
    return NextResponse.json(
      { error: 'Failed to load stock data', details: error.message },
      { status: 500 }
    );
  }
}