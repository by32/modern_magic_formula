'use client';

import { CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface QualityData {
  quality_score: number;
  last_updated: string;
  data_age_days: number;
  total_stocks: number;
  status: string;
}

interface QualityStatusProps {
  quality: QualityData | null;
}

export function QualityStatus({ quality }: QualityStatusProps) {
  if (!quality) return null;

  const statusConfig = getStatusConfig(quality.status);
  const scorePercent = quality.quality_score * 100;

  return (
    <Card className={cn('overflow-hidden', statusConfig.borderClass)}>
      <CardContent className="p-0">
        <div className="flex items-stretch">
          {/* Left - Status Icon & Info */}
          <div className="flex-1 p-4 flex items-center gap-4">
            <div className={cn(
              'flex items-center justify-center w-12 h-12 rounded-full',
              statusConfig.bgClass
            )}>
              <statusConfig.icon className={cn('w-6 h-6', statusConfig.iconClass)} />
            </div>
            <div>
              <h3 className="font-semibold text-foreground flex items-center gap-2">
                Data Quality
                {quality.status === 'healthy' && (
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-positive opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-positive"></span>
                  </span>
                )}
              </h3>
              <p className="text-sm text-muted-foreground">
                Updated {quality.last_updated ? formatDate(quality.last_updated) : 'N/A'}
                {' '}&bull;{' '}
                {quality.total_stocks.toLocaleString()} stocks analyzed
              </p>
            </div>
          </div>

          {/* Right - Score */}
          <div className="w-32 bg-muted/30 p-4 flex flex-col items-center justify-center border-l">
            <div className={cn('text-3xl font-bold tabular-nums', statusConfig.textClass)}>
              {scorePercent.toFixed(0)}%
            </div>
            <div className="text-xs text-muted-foreground">Quality Score</div>
            <Progress
              value={scorePercent}
              className="h-1.5 mt-2 w-full"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getStatusConfig(status: string) {
  switch (status) {
    case 'healthy':
      return {
        icon: CheckCircle,
        iconClass: 'text-positive',
        bgClass: 'bg-positive/10',
        textClass: 'text-positive',
        borderClass: 'border-positive/20',
      };
    case 'warning':
      return {
        icon: AlertCircle,
        iconClass: 'text-warning',
        bgClass: 'bg-warning/10',
        textClass: 'text-warning-foreground',
        borderClass: 'border-warning/20',
      };
    case 'critical':
      return {
        icon: AlertCircle,
        iconClass: 'text-negative',
        bgClass: 'bg-negative/10',
        textClass: 'text-negative',
        borderClass: 'border-negative/20',
      };
    default:
      return {
        icon: Clock,
        iconClass: 'text-muted-foreground',
        bgClass: 'bg-muted',
        textClass: 'text-muted-foreground',
        borderClass: '',
      };
  }
}

function formatDate(dateString: string): string {
  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  } catch {
    return dateString;
  }
}
