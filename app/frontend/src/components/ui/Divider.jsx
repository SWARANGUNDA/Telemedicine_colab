import React from 'react';

export function Divider({ orientation = 'horizontal', label, className = '' }) {
  if (orientation === 'vertical') {
    return <div className={`w-[1px] bg-[var(--border-subtle)] self-stretch mx-2 ${className}`} />;
  }

  if (label) {
    return (
      <div className={`flex items-center gap-3 my-4 ${className}`}>
        <div className="flex-1 h-[1px] bg-[var(--border-subtle)]" />
        <span className="text-xs font-mono font-medium text-[var(--text-dim)] uppercase">{label}</span>
        <div className="flex-1 h-[1px] bg-[var(--border-subtle)]" />
      </div>
    );
  }

  return <div className={`w-full h-[1px] bg-[var(--border-subtle)] my-4 ${className}`} />;
}
