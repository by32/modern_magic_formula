'use client';

import { ColumnDef } from '@tanstack/react-table';
import { ArrowUpDown, ChevronDown, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MetricValue, FScoreBar, SectorBadge, MarketCapBadge } from '@/components/metrics';

export interface StockData {
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
  revenue?: number;
  net_income?: number;
  operating_income?: number;
  current_price?: number;
  momentum_6m?: number;
  debt_to_equity?: number;
}

export const columns: ColumnDef<StockData>[] = [
  {
    id: 'expander',
    header: () => null,
    cell: ({ row }) => (
      <Button
        variant="ghost"
        size="sm"
        className="h-8 w-8 p-0"
        onClick={(e) => {
          e.stopPropagation();
          row.toggleExpanded();
        }}
      >
        {row.getIsExpanded() ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
      </Button>
    ),
    enableSorting: false,
  },
  {
    accessorKey: 'magic_formula_rank',
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        #
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row, table }) => {
      const pageIndex = table.getState().pagination.pageIndex;
      const pageSize = table.getState().pagination.pageSize;
      const displayRank = pageIndex * pageSize + row.index + 1;
      return (
        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
          {displayRank}
        </div>
      );
    },
  },
  {
    accessorKey: 'ticker',
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        Ticker
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => (
      <div>
        <div className="font-semibold text-foreground">{row.getValue('ticker')}</div>
        <div className="text-xs text-muted-foreground truncate max-w-[180px]">
          {row.original.company_name}
        </div>
      </div>
    ),
  },
  {
    accessorKey: 'sector',
    header: 'Sector',
    cell: ({ row }) => <SectorBadge sector={row.getValue('sector')} />,
    filterFn: (row, id, value) => {
      return value.includes(row.getValue(id));
    },
  },
  {
    accessorKey: 'market_cap',
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        Market Cap
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => <MarketCapBadge value={row.getValue('market_cap')} />,
  },
  {
    accessorKey: 'earnings_yield',
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        Earnings Yield
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => (
      <MetricValue
        value={row.getValue('earnings_yield')}
        type="percent"
        colorScale="positive"
      />
    ),
  },
  {
    accessorKey: 'roc',
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        ROC
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => (
      <MetricValue
        value={row.getValue('roc')}
        type="percent"
        colorScale="positive"
      />
    ),
  },
  {
    accessorKey: 'f_score',
    header: ({ column }) => (
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8"
        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
      >
        F-Score
        <ArrowUpDown className="ml-1 h-3 w-3" />
      </Button>
    ),
    cell: ({ row }) => <FScoreBar score={row.getValue('f_score')} />,
  },
];
