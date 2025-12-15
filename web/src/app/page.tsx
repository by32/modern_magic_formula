'use client';

import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  Shield,
  BarChart3,
  AlertCircle,
  Info,
  Calculator,
  Target,
  DollarSign,
  Download,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { DataTable, columns, TableSkeleton, type StockData } from '@/components/stock-table';
import { StockFilters, type FilterState } from '@/components/filters';
import { QualityStatus } from '@/components/quality-status';

interface QualityData {
  quality_score: number;
  last_updated: string;
  data_age_days: number;
  total_stocks: number;
  status: string;
}

export default function HomePage() {
  const [stocks, setStocks] = useState<StockData[]>([]);
  const [quality, setQuality] = useState<QualityData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalStocksCount, setTotalStocksCount] = useState<number>(0);
  const [totalUniverseCount, setTotalUniverseCount] = useState<number>(0);
  const [filters, setFilters] = useState<FilterState>({
    limit: 20,
    min_fscore: 5,
    min_market_cap: 1000000000,
    min_momentum: -999,
    exclude_financials: true,
  });

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [stocksRes, qualityRes] = await Promise.all([
        fetch(
          `/api/stocks?limit=${filters.limit}&min_fscore=${filters.min_fscore}&min_market_cap=${filters.min_market_cap}&min_momentum=${filters.min_momentum}&exclude_financials=${filters.exclude_financials}`
        ),
        fetch('/api/quality'),
      ]);

      if (stocksRes.ok) {
        const stocksData = await stocksRes.json();
        setStocks(stocksData.stocks || []);
        setTotalStocksCount(stocksData.total || 0);
        setTotalUniverseCount(stocksData.total_universe || 0);
      } else {
        setError('Failed to load stock data');
      }

      if (qualityRes.ok) {
        const qualityData = await qualityRes.json();
        setQuality(qualityData);
      }
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to connect to the server');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const exportToCSV = () => {
    if (stocks.length === 0) return;

    const csvHeaders = [
      'Rank',
      'Ticker',
      'Company Name',
      'Sector',
      'Market Cap',
      'Current Price',
      'Earnings Yield',
      'ROC',
      'F-Score',
      'Magic Formula Rank',
      '6M Momentum',
      'P/E Ratio',
      'P/B Ratio',
      'Revenue',
      'Net Income',
      'Operating Income',
    ];

    const csvData = stocks.map((stock, index) => [
      index + 1,
      stock.ticker,
      stock.company_name,
      stock.sector,
      stock.market_cap,
      stock.current_price || 'N/A',
      (stock.earnings_yield * 100).toFixed(1) + '%',
      (stock.roc * 100).toFixed(1) + '%',
      stock.f_score,
      stock.magic_formula_rank,
      stock.momentum_6m ? (stock.momentum_6m * 100).toFixed(1) + '%' : 'N/A',
      stock.pe_ratio?.toFixed(1) || 'N/A',
      stock.pb_ratio?.toFixed(1) || 'N/A',
      stock.revenue || 'N/A',
      stock.net_income || 'N/A',
      stock.operating_income || 'N/A',
    ]);

    const csvContent = [
      csvHeaders.join(','),
      ...csvData.map((row) =>
        row
          .map((cell) => {
            if (
              typeof cell === 'string' &&
              (cell.includes(',') || cell.includes('"') || cell.includes('\n'))
            ) {
              return `"${cell.replace(/"/g, '""')}"`;
            }
            return cell;
          })
          .join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute(
      'download',
      `magic-formula-stocks-${new Date().toISOString().split('T')[0]}.csv`
    );
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <header className="text-center mb-10">
          <h1 className="text-4xl font-bold text-foreground mb-3 tracking-tight">
            Modern Magic Formula
          </h1>
          <p className="text-xl text-muted-foreground mb-2">
            DIY Stock Picks for Individual Investors
          </p>
          <p className="text-sm text-muted-foreground">
            Based on Joel Greenblatt&apos;s proven value investing strategy
          </p>
        </header>

        {/* Quality Status */}
        <QualityStatus quality={quality} />

        <div className="h-8" />

        {/* Key Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <FeatureCard
            icon={TrendingUp}
            iconColor="text-primary"
            title="Magic Formula"
            description="Combines earnings yield and return on capital to find undervalued, profitable companies"
          />
          <FeatureCard
            icon={Shield}
            iconColor="text-positive"
            title="Quality Filter"
            description="F-Score analysis ensures financial strength and eliminates potential value traps"
          />
          <FeatureCard
            icon={BarChart3}
            iconColor="text-violet-600"
            title="Diversification"
            description="Automatic sector balancing to reduce concentration risk"
          />
        </div>

        {/* Magic Formula Explanation */}
        <Card className="mb-8 bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-4">
              <div className="rounded-full bg-primary/10 p-2">
                <Info className="w-5 h-5 text-primary" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-foreground mb-4 text-lg">
                  How the Magic Formula Works
                </h3>
                <div className="grid md:grid-cols-2 gap-6 text-sm">
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <Calculator className="w-4 h-4 text-primary" />
                      <span className="font-medium text-foreground">
                        Step 1: Calculate Earnings Yield
                      </span>
                    </div>
                    <p className="text-muted-foreground ml-6">
                      EBIT ÷ Enterprise Value = How much the business earns relative to
                      its price. Higher is better (cheap + profitable).
                    </p>
                  </div>
                  <div>
                    <div className="flex items-center space-x-2 mb-2">
                      <Target className="w-4 h-4 text-primary" />
                      <span className="font-medium text-foreground">
                        Step 2: Calculate Return on Capital
                      </span>
                    </div>
                    <p className="text-muted-foreground ml-6">
                      EBIT ÷ (Working Capital + Fixed Assets) = How efficiently the
                      business generates profits. Higher means better management.
                    </p>
                  </div>
                </div>
                <Separator className="my-4" />
                <div className="bg-background/50 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <DollarSign className="w-4 h-4 text-positive" />
                    <span className="font-medium text-foreground">Final Ranking</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Stocks are ranked on both metrics, then combined. The top-ranked
                    stocks are both cheap AND high quality. You&apos;re seeing the top{' '}
                    <span className="font-medium text-foreground">{filters.limit}</span>{' '}
                    out of{' '}
                    <span className="font-medium text-foreground">
                      {totalStocksCount}
                    </span>{' '}
                    qualifying stocks from the{' '}
                    <span className="font-medium text-foreground">
                      {totalUniverseCount || '~1000'}
                    </span>{' '}
                    Russell 1000 universe.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Filters */}
        <div className="mb-8">
          <StockFilters filters={filters} onFiltersChange={setFilters} />
        </div>

        {/* Stock Table */}
        <Card>
          <CardHeader className="flex flex-row items-start justify-between space-y-0">
            <div>
              <CardTitle>Your Magic Formula Stock Picks</CardTitle>
              <p className="text-sm text-muted-foreground mt-1">
                Ranked by Magic Formula score &bull; Updated weekly
              </p>
            </div>
            {stocks.length > 0 && (
              <Button variant="outline" size="sm" onClick={exportToCSV}>
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {error ? (
              <ErrorState message={error} onRetry={loadData} />
            ) : loading ? (
              <TableSkeleton rows={10} />
            ) : (
              <DataTable
                columns={columns}
                data={stocks}
                totalStocks={totalUniverseCount}
              />
            )}
          </CardContent>
        </Card>

        {/* Disclaimer */}
        <Card className="mt-8 border-warning/30 bg-warning-light/30">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-warning-foreground mt-0.5 flex-shrink-0" />
              <div className="text-sm text-warning-foreground">
                <h4 className="font-medium mb-1">Investment Disclaimer</h4>
                <p>
                  This tool is for educational purposes only and does not constitute
                  investment advice. Past performance does not guarantee future results.
                  Always conduct your own research and consult with qualified financial
                  advisors before making investment decisions.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

interface FeatureCardProps {
  icon: React.ElementType;
  iconColor: string;
  title: string;
  description: string;
}

function FeatureCard({ icon: Icon, iconColor, title, description }: FeatureCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="pt-6">
        <div className="flex items-center space-x-3 mb-3">
          <div className="rounded-lg bg-muted p-2">
            <Icon className={`w-6 h-6 ${iconColor}`} />
          </div>
          <h3 className="font-semibold text-foreground">{title}</h3>
        </div>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry: () => void;
}

function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-destructive/10 p-3 mb-4">
        <AlertCircle className="w-8 h-8 text-destructive" />
      </div>
      <h3 className="font-semibold text-foreground mb-2">Failed to load stocks</h3>
      <p className="text-sm text-muted-foreground mb-4 max-w-md">{message}</p>
      <Button variant="outline" onClick={onRetry}>
        Try Again
      </Button>
    </div>
  );
}
