import React from 'react';

export function PageHeader({ title, description, badge, actions, className = '' }) {
  return (
    <div className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-[var(--border-subtle)] ${className}`}>
      <div className="space-y-1">
        <div className="flex items-center gap-3">
          <h1 className="text-xl md:text-2xl font-extrabold text-[var(--text-main)] tracking-tight">{title}</h1>
          {badge && <span className="px-2.5 py-0.5 text-xs font-mono font-semibold rounded-full bg-[var(--primary-light)] text-[var(--primary)] border border-[var(--primary)]/20">{badge}</span>}
        </div>
        {description && <p className="text-xs md:text-sm text-[var(--text-muted)] max-w-2xl">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
    </div>
  );
}
