import React from 'react';

export function Toast({ title, message, variant = 'info', onClose, className = '' }) {
  const variantStyles = {
    info: 'border-[var(--primary)] text-[var(--primary)]',
    success: 'border-[var(--success)] text-[var(--success)]',
    warning: 'border-[var(--warning)] text-[var(--warning)]',
    danger: 'border-[var(--danger)] text-[var(--danger)]',
  };

  return (
    <div className={`glass-card p-4 border-l-4 shadow-xl flex items-start gap-3 w-80 max-w-full ${variantStyles[variant] || variantStyles.info} ${className}`}>
      <div className="flex-1">
        {title && <h5 className="text-sm font-bold text-[var(--text-main)] mb-0.5">{title}</h5>}
        {message && <p className="text-xs text-[var(--text-muted)]">{message}</p>}
      </div>
      {onClose && (
        <button onClick={onClose} className="text-[var(--text-muted)] hover:text-[var(--text-main)] p-1">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      )}
    </div>
  );
}
