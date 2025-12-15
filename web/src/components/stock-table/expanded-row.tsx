'use client';

import { ExternalLink, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { MetricValue } from '@/components/metrics';
import type { StockData } from './columns';

interface ExpandedRowProps {
  stock: StockData;
  totalStocks: number;
}

export function ExpandedRow({ stock, totalStocks }: ExpandedRowProps) {
  return (
    <div className="p-4 bg-muted/30 space-y-4">
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard
          label="Current Price"
          value={stock.current_price}
          format="currency"
        />
        <MetricCard
          label="6M Momentum"
          value={stock.momentum_6m}
          format="momentum"
        />
        <MetricCard
          label="P/E Ratio"
          value={stock.pe_ratio}
          format="ratio"
        />
        <MetricCard
          label="P/B Ratio"
          value={stock.pb_ratio}
          format="ratio"
        />
      </div>

      <Separator />

      {/* Financial Details */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <MetricCard
          label="Revenue"
          value={stock.revenue}
          format="largeCurrency"
        />
        <MetricCard
          label="Operating Income"
          value={stock.operating_income}
          format="largeCurrency"
        />
        <MetricCard
          label="Net Income"
          value={stock.net_income}
          format="largeCurrency"
        />
      </div>

      <Separator />

      {/* Explanation Card */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="pt-4">
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">{stock.ticker}</span> ranks{' '}
            <span className="font-semibold text-primary">#{stock.magic_formula_rank}</span> of{' '}
            {totalStocks} stocks with an earnings yield of{' '}
            <MetricValue value={stock.earnings_yield} type="percent" colorScale="positive" className="inline" /> and
            return on capital of{' '}
            <MetricValue value={stock.roc} type="percent" colorScale="positive" className="inline" />.
            This combination of being both undervalued and profitable gives it a strong Magic Formula score.
          </p>
        </CardContent>
      </Card>

      {/* Research Links */}
      <div className="flex flex-wrap gap-2">
        <ResearchSheet stock={stock} />
      </div>
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: number | undefined | null;
  format: 'currency' | 'largeCurrency' | 'momentum' | 'ratio';
}

function MetricCard({ label, value, format }: MetricCardProps) {
  const renderValue = () => {
    if (value === null || value === undefined || isNaN(value)) {
      return <span className="text-muted-foreground">N/A</span>;
    }

    switch (format) {
      case 'currency':
        return <span className="font-semibold">${value.toFixed(2)}</span>;
      case 'largeCurrency':
        return <MetricValue value={value} type="currency" />;
      case 'momentum':
        const isPositive = value >= 0;
        return (
          <div className="flex items-center gap-1">
            {isPositive ? (
              <TrendingUp className="h-4 w-4 text-positive" />
            ) : (
              <TrendingDown className="h-4 w-4 text-negative" />
            )}
            <MetricValue value={value} type="percent" colorScale="bidirectional" showSign />
          </div>
        );
      case 'ratio':
        return <span className="font-semibold">{value.toFixed(1)}</span>;
      default:
        return <span>{value}</span>;
    }
  };

  return (
    <div className="space-y-1">
      <p className="text-xs text-muted-foreground uppercase tracking-wide">{label}</p>
      <div className="text-lg">{renderValue()}</div>
    </div>
  );
}

interface ResearchSheetProps {
  stock: StockData;
}

function ResearchSheet({ stock }: ResearchSheetProps) {
  const links = [
    {
      name: 'Yahoo Finance',
      url: `https://finance.yahoo.com/quote/${stock.ticker}`,
      color: 'bg-purple-100 text-purple-800 hover:bg-purple-200',
    },
    {
      name: 'Morningstar',
      url: `https://www.morningstar.com/stocks/xnas/${stock.ticker}/quote`,
      color: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
    },
    {
      name: 'SEC Filings',
      url: `https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=${stock.ticker}&type=10-K`,
      color: 'bg-green-100 text-green-800 hover:bg-green-200',
    },
    {
      name: 'Finviz',
      url: `https://finviz.com/quote.ashx?t=${stock.ticker}`,
      color: 'bg-amber-100 text-amber-800 hover:bg-amber-200',
    },
  ];

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm">
          <ExternalLink className="h-4 w-4 mr-2" />
          Research {stock.ticker}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Research {stock.ticker}</SheetTitle>
        </SheetHeader>
        <div className="mt-6 space-y-4">
          <div>
            <h4 className="font-semibold mb-2">{stock.company_name}</h4>
            <p className="text-sm text-muted-foreground">
              View detailed information about {stock.ticker} from multiple trusted sources.
            </p>
          </div>

          <Separator />

          <div className="space-y-2">
            {links.map((link) => (
              <a
                key={link.name}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`flex items-center justify-between p-3 rounded-lg transition-colors ${link.color}`}
              >
                <span className="font-medium">{link.name}</span>
                <ExternalLink className="h-4 w-4" />
              </a>
            ))}
          </div>

          <Separator />

          <div className="text-xs text-muted-foreground">
            <p className="font-medium mb-1">Due Diligence Reminder</p>
            <p>
              Always research companies thoroughly before investing. Check recent earnings,
              management changes, industry trends, and competitive positioning.
            </p>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}
