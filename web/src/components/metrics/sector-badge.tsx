'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface SectorBadgeProps {
  sector: string;
  size?: 'sm' | 'md';
  className?: string;
}

const sectorColors: Record<string, string> = {
  'Technology': 'bg-blue-100 text-blue-800 hover:bg-blue-200 border-blue-200',
  'Healthcare': 'bg-emerald-100 text-emerald-800 hover:bg-emerald-200 border-emerald-200',
  'Financial Services': 'bg-purple-100 text-purple-800 hover:bg-purple-200 border-purple-200',
  'Financials': 'bg-purple-100 text-purple-800 hover:bg-purple-200 border-purple-200',
  'Energy': 'bg-orange-100 text-orange-800 hover:bg-orange-200 border-orange-200',
  'Consumer Cyclical': 'bg-pink-100 text-pink-800 hover:bg-pink-200 border-pink-200',
  'Consumer Defensive': 'bg-amber-100 text-amber-800 hover:bg-amber-200 border-amber-200',
  'Industrials': 'bg-slate-100 text-slate-800 hover:bg-slate-200 border-slate-200',
  'Basic Materials': 'bg-lime-100 text-lime-800 hover:bg-lime-200 border-lime-200',
  'Materials': 'bg-lime-100 text-lime-800 hover:bg-lime-200 border-lime-200',
  'Utilities': 'bg-cyan-100 text-cyan-800 hover:bg-cyan-200 border-cyan-200',
  'Real Estate': 'bg-teal-100 text-teal-800 hover:bg-teal-200 border-teal-200',
  'Communication Services': 'bg-rose-100 text-rose-800 hover:bg-rose-200 border-rose-200',
  'Communication': 'bg-rose-100 text-rose-800 hover:bg-rose-200 border-rose-200',
};

export function SectorBadge({ sector, size = 'sm', className }: SectorBadgeProps) {
  const colorClass = sectorColors[sector] || 'bg-gray-100 text-gray-800 hover:bg-gray-200 border-gray-200';

  return (
    <Badge
      variant="outline"
      className={cn(
        'font-medium border transition-colors',
        colorClass,
        size === 'sm' ? 'text-xs px-2 py-0.5' : 'text-sm px-2.5 py-1',
        className
      )}
    >
      {sector}
    </Badge>
  );
}
