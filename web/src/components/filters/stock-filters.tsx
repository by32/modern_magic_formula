'use client';

import { X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';

export interface FilterState {
  limit: number;
  min_fscore: number;
  min_market_cap: number;
  min_momentum: number;
  exclude_financials: boolean;
}

interface StockFiltersProps {
  filters: FilterState;
  onFiltersChange: (filters: FilterState) => void;
}

export function StockFilters({ filters, onFiltersChange }: StockFiltersProps) {
  const updateFilter = <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
    onFiltersChange({ ...filters, [key]: value });
  };

  const activeFilters = getActiveFilters(filters);

  return (
    <Card>
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Customize Your Picks</CardTitle>
          {activeFilters.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {activeFilters.map((filter) => (
                <Badge
                  key={filter.key}
                  variant="secondary"
                  className="cursor-pointer hover:bg-destructive/10 hover:text-destructive transition-colors"
                  onClick={() => filter.onClear()}
                >
                  {filter.label}
                  <X className="ml-1 h-3 w-3" />
                </Badge>
              ))}
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Number of Stocks */}
          <div className="space-y-2">
            <Label htmlFor="limit">Number of Stocks</Label>
            <Select
              value={filters.limit.toString()}
              onValueChange={(value) => updateFilter('limit', parseInt(value))}
            >
              <SelectTrigger id="limit">
                <SelectValue placeholder="Select count" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="15">15 stocks</SelectItem>
                <SelectItem value="20">20 stocks</SelectItem>
                <SelectItem value="25">25 stocks</SelectItem>
                <SelectItem value="30">30 stocks</SelectItem>
                <SelectItem value="50">50 stocks</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Minimum F-Score */}
          <div className="space-y-2">
            <Label htmlFor="fscore">Minimum F-Score</Label>
            <Select
              value={filters.min_fscore.toString()}
              onValueChange={(value) => updateFilter('min_fscore', parseInt(value))}
            >
              <SelectTrigger id="fscore">
                <SelectValue placeholder="Select F-Score" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="0">
                  <div className="flex items-center gap-2">
                    <span>All F-Scores</span>
                    <span className="text-xs text-muted-foreground">No filter</span>
                  </div>
                </SelectItem>
                <SelectItem value="4">
                  <div className="flex items-center gap-2">
                    <span>4+ (Moderate)</span>
                  </div>
                </SelectItem>
                <SelectItem value="5">
                  <div className="flex items-center gap-2">
                    <span>5+ (Good)</span>
                    <span className="text-xs text-muted-foreground">Recommended</span>
                  </div>
                </SelectItem>
                <SelectItem value="6">
                  <div className="flex items-center gap-2">
                    <span>6+ (Strong)</span>
                  </div>
                </SelectItem>
                <SelectItem value="7">
                  <div className="flex items-center gap-2">
                    <span>7+ (Excellent)</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Minimum Market Cap */}
          <div className="space-y-2">
            <Label htmlFor="marketcap">Minimum Market Cap</Label>
            <Select
              value={filters.min_market_cap.toString()}
              onValueChange={(value) => updateFilter('min_market_cap', parseFloat(value))}
            >
              <SelectTrigger id="marketcap">
                <SelectValue placeholder="Select cap" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1000000000">$1B+ (Large Cap)</SelectItem>
                <SelectItem value="500000000">$500M+ (Mid Cap)</SelectItem>
                <SelectItem value="100000000">$100M+ (Small Cap)</SelectItem>
                <SelectItem value="0">Any size</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Minimum Momentum */}
          <div className="space-y-2">
            <Label htmlFor="momentum">6M Momentum</Label>
            <Select
              value={filters.min_momentum.toString()}
              onValueChange={(value) => updateFilter('min_momentum', parseFloat(value))}
            >
              <SelectTrigger id="momentum">
                <SelectValue placeholder="Select momentum" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="-999">
                  <span>Any momentum</span>
                </SelectItem>
                <SelectItem value="-0.1">
                  <div className="flex items-center gap-2">
                    <span>≥-10%</span>
                    <span className="text-xs text-muted-foreground">Mild decline OK</span>
                  </div>
                </SelectItem>
                <SelectItem value="0">
                  <div className="flex items-center gap-2">
                    <span>Positive only</span>
                    <span className="text-xs text-muted-foreground">≥0%</span>
                  </div>
                </SelectItem>
                <SelectItem value="0.1">
                  <div className="flex items-center gap-2">
                    <span>Strong</span>
                    <span className="text-xs text-muted-foreground">≥+10%</span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Exclude Financials Checkbox */}
        <div className="mt-6 pt-4 border-t">
          <div className="flex items-start space-x-3">
            <Checkbox
              id="exclude-financials"
              checked={filters.exclude_financials}
              onCheckedChange={(checked) =>
                updateFilter('exclude_financials', checked === true)
              }
            />
            <div className="grid gap-1">
              <Label
                htmlFor="exclude-financials"
                className="font-medium cursor-pointer"
              >
                Exclude Financial & Utility stocks
              </Label>
              <p className="text-xs text-muted-foreground">
                Like magicformulainvesting.com, excludes these sectors due to unique accounting practices
                that make earnings yield and ROC comparisons less meaningful.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function getActiveFilters(filters: FilterState) {
  const active: Array<{ key: string; label: string; onClear: () => void }> = [];

  // We don't show limit as an "active filter" since it's always set
  // but we show the others when they differ from defaults

  if (filters.min_fscore > 0) {
    active.push({
      key: 'fscore',
      label: `F-Score ≥${filters.min_fscore}`,
      onClear: () => {}, // Will be handled by parent
    });
  }

  if (filters.min_market_cap > 0 && filters.min_market_cap !== 1000000000) {
    const label = filters.min_market_cap >= 1e9
      ? `≥$${filters.min_market_cap / 1e9}B`
      : `≥$${filters.min_market_cap / 1e6}M`;
    active.push({
      key: 'marketcap',
      label: `Market Cap ${label}`,
      onClear: () => {},
    });
  }

  if (filters.min_momentum > -999) {
    const label = filters.min_momentum >= 0
      ? `Momentum ≥${(filters.min_momentum * 100).toFixed(0)}%`
      : `Momentum ≥${(filters.min_momentum * 100).toFixed(0)}%`;
    active.push({
      key: 'momentum',
      label,
      onClear: () => {},
    });
  }

  if (filters.exclude_financials) {
    active.push({
      key: 'exclude',
      label: 'Excl. Financials',
      onClear: () => {},
    });
  }

  return active;
}
