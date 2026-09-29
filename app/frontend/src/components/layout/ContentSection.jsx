import React from 'react';

export function ContentSection({ title, subtitle, actions, children, className = '' }) {
  return (
    <section className={`space-y-4 ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between gap-4">
          <div>
            {title && <h3 className="text-base font-bold text-[var(--text-main)] tracking-tight">{title}</h3>}
            {subtitle && <p className="text-xs text-[var(--text-muted)]">{subtitle}</p>}
          </div>
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </div>
      )}
      <div>{children}</div>
    </section>
  );
}
