import React from 'react';

export function Breadcrumb({ items = [], className = '' }) {
  return (
    <nav className={`flex items-center gap-2 text-xs text-[var(--text-muted)] ${className}`}>
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <React.Fragment key={idx}>
            {idx > 0 && <span className="text-[var(--text-dim)]">/</span>}
            {isLast ? (
              <span className="font-semibold text-[var(--text-main)]">{item.label}</span>
            ) : item.onClick ? (
              <button onClick={item.onClick} className="hover:text-[var(--text-main)] transition-colors">
                {item.label}
              </button>
            ) : (
              <span>{item.label}</span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
}
