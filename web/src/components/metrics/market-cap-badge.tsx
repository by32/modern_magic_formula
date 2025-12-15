'use client';

import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface MarketCapBadgeProps {
  value: number;
  className?: string;
}

export function MarketCapBadge({ value, className }: MarketCapBadgeProps) {
  const formatted = formatMarketCap(value);
  const category = getMarketCapCategory(value);

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant="secondary"
            className={cn(
              'font-mono tabular-nums',
              category.className,
              className
            )}
          >
            {formatted}
          </Badge>
        </TooltipTrigger>
        <TooltipContent>
          <p className="font-medium">{category.label}</p>
          <p className="text-xs text-muted-foreground">
            ${value.toLocaleString()}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function formatMarketCap(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(0)}M`;
  return `$${(value / 1e3).toFixed(0)}K`;
}

function getMarketCapCategory(value: number): { label: string; className: string } {
  if (value >= 200e9) {
    return { label: 'Mega Cap (>$200B)', className: 'bg-blue-100 text-blue-800' };
  }
  if (value >= 10e9) {
    return { label: 'Large Cap ($10B-$200B)', className: 'bg-indigo-100 text-indigo-800' };
  }
  if (value >= 2e9) {
    return { label: 'Mid Cap ($2B-$10B)', className: 'bg-violet-100 text-violet-800' };
  }
  if (value >= 300e6) {
    return { label: 'Small Cap ($300M-$2B)', className: 'bg-purple-100 text-purple-800' };
  }
  return { label: 'Micro Cap (<$300M)', className: 'bg-fuchsia-100 text-fuchsia-800' };
}
