import React from 'react';

export function Select({
  label,
  options = [],
  error,
  helperText,
  className = '',
  id,
  children,
  ...props
}) {
  const selectId = id || `select-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label htmlFor={selectId} className="text-xs font-semibold text-[var(--text-muted)] tracking-wide uppercase">
          {label}
        </label>
      )}
      <div className="relative w-full">
        <select
          id={selectId}
          className={`w-full bg-[var(--bg-surface)] text-[var(--text-main)] border text-sm rounded-lg px-3.5 py-2.5 pr-10 appearance-none transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed ${
            error ? 'border-[var(--danger)]' : 'border-[var(--border-medium)]'
          } ${className}`}
          {...props}
        >
          {children ? children : options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-[var(--text-muted)]">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
      {error ? (
        <span className="text-xs text-[var(--danger)] font-medium">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-[var(--text-muted)]">{helperText}</span>
      ) : null}
    </div>
  );
}
