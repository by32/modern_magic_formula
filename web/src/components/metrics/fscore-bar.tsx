'use client';

import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface FScoreBarProps {
  score: number;
  max?: number;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function FScoreBar({
  score,
  max = 9,
  showLabel = true,
  size = 'md',
  className,
}: FScoreBarProps) {
  const percentage = (score / max) * 100;
  const colorClass = getFScoreColor(score);
  const rating = getFScoreRating(score);

  const sizeClasses = {
    sm: 'h-1.5',
    md: 'h-2',
    lg: 'h-3',
  };

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn('flex items-center gap-2', className)}>
            {showLabel && (
              <span className={cn('font-semibold tabular-nums min-w-[1.5rem]', colorClass)}>
                {score}
              </span>
            )}
            <div className={cn('flex-1 min-w-[3rem] max-w-[5rem]')}>
              <div className={cn('w-full bg-muted rounded-full overflow-hidden', sizeClasses[size])}>
                <div
                  className={cn('h-full rounded-full transition-all duration-300', getProgressColor(score))}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          </div>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-[200px]">
          <div className="space-y-1">
            <p className="font-medium">Piotroski F-Score: {score}/{max}</p>
            <p className={cn('text-xs', colorClass)}>{rating}</p>
            <p className="text-xs text-muted-foreground">
              Measures financial strength based on profitability, leverage, and operating efficiency.
            </p>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

function getFScoreColor(score: number): string {
  if (score >= 7) return 'text-positive';
  if (score >= 5) return 'text-warning-foreground';
  return 'text-negative';
}

function getProgressColor(score: number): string {
  if (score >= 7) return 'bg-positive';
  if (score >= 5) return 'bg-warning';
  return 'bg-negative';
}

function getFScoreRating(score: number): string {
  if (score >= 8) return 'Excellent - Very strong financials';
  if (score >= 7) return 'Strong - Good financial health';
  if (score >= 5) return 'Moderate - Average financials';
  if (score >= 3) return 'Weak - Below average';
  return 'Poor - Financial concerns';
}
