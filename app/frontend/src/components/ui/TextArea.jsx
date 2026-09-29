import React from 'react';

export function TextArea({
  label,
  error,
  helperText,
  rows = 4,
  className = '',
  containerClassName = '',
  id,
  ...props
}) {
  const areaId = id || `textarea-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div className={`flex flex-col gap-1.5 w-full ${containerClassName}`}>
      {label && (
        <label htmlFor={areaId} className="text-xs font-semibold text-[var(--text-muted)] tracking-wide uppercase">
          {label}
        </label>
      )}
      <textarea
        id={areaId}
        rows={rows}
        className={`w-full bg-[var(--bg-surface)] text-[var(--text-main)] border text-sm rounded-lg p-3 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed ${
          error ? 'border-[var(--danger)]' : 'border-[var(--border-medium)]'
        } ${className}`}
        {...props}
      />
      {error ? (
        <span className="text-xs text-[var(--danger)] font-medium">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-[var(--text-muted)]">{helperText}</span>
      ) : null}
    </div>
  );
}
