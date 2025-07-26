import { NextResponse } from 'next/server';

// Cache data for 5 minutes
let metadataCache: { data: any, timestamp: number } | null = null;
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

async function fetchMetadataFromGitHub() {
  // Check cache first
  if (metadataCache && Date.now() - metadataCache.timestamp < CACHE_DURATION) {
    return metadataCache.data;
  }

  try {
    const response = await fetch(
      'https://raw.githubusercontent.com/by32/modern_magic_formula/main/data/metadata_hybrid.json',
      { 
        cache: 'no-store',
        headers: {
          'Accept': 'application/json'
        }
      }
    );

    if (!response.ok) {
      throw new Error(`GitHub fetch failed: ${response.status}`);
    }

    const metadata = await response.json();
    
    // Update cache
    metadataCache = {
      data: metadata,
      timestamp: Date.now()
    };

    return metadata;
  } catch (error) {
    console.error('Error fetching metadata from GitHub:', error);
    return null;
  }
}

export async function GET() {
  try {
    // Fetch metadata from GitHub
    const metadata = await fetchMetadataFromGitHub();
    
    if (!metadata) {
      // Return default quality data if fetch fails
      return NextResponse.json({
        quality_score: 0.75,
        last_updated: new Date().toISOString(),
        data_age_days: 0,
        total_stocks: 0,
        data_sources: ['SEC EDGAR', 'Yahoo Finance'],
        status: 'unknown',
        error: 'Could not fetch metadata'
      });
    }
    
    // Calculate data age
    const lastUpdated = new Date(metadata.last_updated);
    const now = new Date();
    const ageInDays = Math.floor((now.getTime() - lastUpdated.getTime()) / (1000 * 60 * 60 * 24));
    
    // Simple quality score calculation
    let qualityScore = 1.0;
    
    // Penalize old data
    if (ageInDays > 30) qualityScore -= 0.2;
    if (ageInDays > 60) qualityScore -= 0.3;
    
    // Check stock count
    const stockCount = metadata.total_stocks || 0;
    if (stockCount < 100) qualityScore -= 0.3;
    if (stockCount < 50) qualityScore -= 0.5;
    
    // Ensure quality score is between 0 and 1
    qualityScore = Math.max(0, Math.min(1, qualityScore));
    
    return NextResponse.json({
      quality_score: qualityScore,
      last_updated: metadata.last_updated,
      data_age_days: ageInDays,
      total_stocks: stockCount,
      data_sources: metadata.data_sources || ['SEC EDGAR', 'Yahoo Finance'],
      status: qualityScore >= 0.75 ? 'healthy' : qualityScore >= 0.5 ? 'warning' : 'critical',
      russell_1000_coverage: metadata.russell_1000_coverage || 0,
      sec_coverage: metadata.sec_coverage || 0,
      data_source: 'github',
      cache_status: metadataCache && Date.now() - metadataCache.timestamp < CACHE_DURATION ? 'hit' : 'miss'
    });

  } catch (error) {
    console.error('Error loading quality data:', error);
    return NextResponse.json(
      { 
        error: 'Failed to load quality data',
        quality_score: 0,
        status: 'error'
      },
      { status: 500 }
    );
  }
}