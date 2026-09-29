import React from 'react';

export function ProgressBar({ value = 0, max = 100, variant = 'primary', showLabel = false, className = '' }) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));

  const variantStyles = {
    primary: 'bg-[var(--primary)]',
    secondary: 'bg-[var(--secondary)]',
    success: 'bg-[var(--success)]',
    warning: 'bg-[var(--warning)]',
    danger: 'bg-[var(--danger)]',
  };

  return (
    <div className={`w-full flex flex-col gap-1.5 ${className}`}>
      {showLabel && (
        <div className="flex items-center justify-between text-xs font-mono font-medium text-[var(--text-muted)]">
          <span>Progress</span>
          <span>{Math.round(pct)}%</span>
        </div>
      )}
      <div className="w-full h-2.5 bg-[var(--border-medium)]/30 rounded-full overflow-hidden">
        <div
          className={`h-full transition-all duration-300 rounded-full ${variantStyles[variant] || variantStyles.primary}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}
