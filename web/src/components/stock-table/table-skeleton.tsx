'use client';

import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export function TableSkeleton({ rows = 10, columns = 8 }: TableSkeletonProps) {
  return (
    <div className="space-y-4">
      {/* Controls Skeleton */}
      <div className="flex items-center justify-between">
        <Skeleton className="h-5 w-[180px]" />
        <Skeleton className="h-9 w-[100px]" />
      </div>

      {/* Table Skeleton */}
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {Array.from({ length: columns }).map((_, i) => (
                <TableHead key={i} className="bg-muted/50">
                  <Skeleton className="h-4 w-[80px]" />
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {Array.from({ length: rows }).map((_, rowIndex) => (
              <TableRow key={rowIndex}>
                {/* Expander */}
                <TableCell>
                  <Skeleton className="h-8 w-8 rounded" />
                </TableCell>
                {/* Rank */}
                <TableCell>
                  <Skeleton className="h-8 w-8 rounded-full" />
                </TableCell>
                {/* Ticker + Company */}
                <TableCell>
                  <div className="space-y-1">
                    <Skeleton className="h-4 w-[60px]" />
                    <Skeleton className="h-3 w-[120px]" />
                  </div>
                </TableCell>
                {/* Sector */}
                <TableCell>
                  <Skeleton className="h-6 w-[80px] rounded-full" />
                </TableCell>
                {/* Market Cap */}
                <TableCell>
                  <Skeleton className="h-6 w-[60px] rounded" />
                </TableCell>
                {/* EY */}
                <TableCell>
                  <Skeleton className="h-4 w-[50px]" />
                </TableCell>
                {/* ROC */}
                <TableCell>
                  <Skeleton className="h-4 w-[50px]" />
                </TableCell>
                {/* F-Score */}
                <TableCell>
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-4 w-6" />
                    <Skeleton className="h-2 w-[60px] rounded-full" />
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
