import React from 'react';

export function Skeleton({ width = 'w-full', height = 'h-4', rounded = 'rounded-md', className = '' }) {
  return <div className={`animate-pulse bg-[var(--border-medium)]/40 ${width} ${height} ${rounded} ${className}`} />;
}
