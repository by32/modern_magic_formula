import { NextResponse } from 'next/server';
import { readFileSync } from 'fs';
import { join } from 'path';

export async function GET() {
  try {
    // Read metadata to get data quality info
    const metadataPath = join(process.cwd(), '..', 'data', 'metadata_hybrid.json');
    const metadata = JSON.parse(readFileSync(metadataPath, 'utf-8'));
    
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
    
    return NextResponse.json({
      quality_score: Math.max(0, qualityScore),
      last_updated: metadata.last_updated,
      data_age_days: ageInDays,
      total_stocks: stockCount,
      data_sources: metadata.data_sources || ['SEC EDGAR', 'Yahoo Finance'],
      status: qualityScore >= 0.75 ? 'healthy' : qualityScore >= 0.5 ? 'warning' : 'critical'
    });

  } catch (error) {
    console.error('Error loading quality data:', error);
    return NextResponse.json(
      { 
        error: 'Failed to load quality data',
        quality_score: 0,
        status: 'unknown'
      },
      { status: 500 }
    );
  }
}