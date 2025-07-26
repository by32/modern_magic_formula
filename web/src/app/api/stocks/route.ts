import { NextRequest, NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';
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

export async function GET(request: NextRequest) {
  try {
    // Read CSV data from the parent data directory
    const dataPath = join(process.cwd(), '..', 'data', 'latest_screening_hybrid.csv');
    const csvData = readFileSync(dataPath, 'utf-8');
    
    // Parse CSV
    const parsed = Papa.parse<StockData>(csvData, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true,
    });

    if (parsed.errors.length > 0) {
      return NextResponse.json(
        { error: 'Error parsing CSV data', details: parsed.errors },
        { status: 500 }
      );
    }

    const { searchParams } = new URL(request.url);
    const limit = parseInt(searchParams.get('limit') || '20');
    const minFScore = parseInt(searchParams.get('min_fscore') || '5');
    const minMarketCap = parseFloat(searchParams.get('min_market_cap') || '1000000000');

    // Apply DIY filters
    let filteredData = parsed.data.filter((stock: StockData) => 
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
      sector_distribution: sectorCounts
    });

  } catch (error) {
    console.error('Error loading stock data:', error);
    return NextResponse.json(
      { error: 'Failed to load stock data', details: error.message },
      { status: 500 }
    );
  }
}