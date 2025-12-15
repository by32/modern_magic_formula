'use client';

import { cn } from '@/lib/utils';

interface MetricValueProps {
  value: number | null | undefined;
  type?: 'percent' | 'currency' | 'number';
  colorScale?: 'positive' | 'negative' | 'bidirectional' | 'none';
  decimals?: number;
  className?: string;
  showSign?: boolean;
}

export function MetricValue({
  value,
  type = 'percent',
  colorScale = 'none',
  decimals = 1,
  className,
  showSign = false,
}: MetricValueProps) {
  if (value === null || value === undefined || isNaN(value)) {
    return <span className={cn('text-muted-foreground', className)}>N/A</span>;
  }

  const formattedValue = formatValue(value, type, decimals, showSign);
  const colorClass = getColorClass(value, colorScale);

  return (
    <span className={cn('font-medium tabular-nums', colorClass, className)}>
      {formattedValue}
    </span>
  );
}

function formatValue(
  value: number,
  type: 'percent' | 'currency' | 'number',
  decimals: number,
  showSign: boolean
): string {
  const sign = showSign && value > 0 ? '+' : '';

  switch (type) {
    case 'percent':
      return `${sign}${(value * 100).toFixed(decimals)}%`;
    case 'currency':
      return formatCurrency(value);
    case 'number':
      return `${sign}${value.toFixed(decimals)}`;
    default:
      return value.toString();
  }
}

function formatCurrency(value: number): string {
  if (value >= 1e12) return `$${(value / 1e12).toFixed(1)}T`;
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(1)}K`;
  return `$${value.toLocaleString()}`;
}

function getColorClass(
  value: number,
  colorScale: 'positive' | 'negative' | 'bidirectional' | 'none'
): string {
  switch (colorScale) {
    case 'positive':
      // Higher is better - green intensity based on value
      if (value >= 0.3) return 'text-positive font-semibold';
      if (value >= 0.15) return 'text-positive';
      if (value >= 0.05) return 'text-positive/80';
      return 'text-foreground';

    case 'negative':
      // Lower is better (like debt ratios)
      if (value >= 2) return 'text-negative font-semibold';
      if (value >= 1) return 'text-negative';
      if (value >= 0.5) return 'text-warning';
      return 'text-positive';

    case 'bidirectional':
      // Positive = green, negative = red (like momentum)
      if (value > 0.1) return 'text-positive font-semibold';
      if (value > 0) return 'text-positive';
      if (value < -0.1) return 'text-negative font-semibold';
      if (value < 0) return 'text-negative';
      return 'text-foreground';

    default:
      return 'text-foreground';
  }
}
