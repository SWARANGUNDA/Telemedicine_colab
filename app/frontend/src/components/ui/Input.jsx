import React from 'react';

export function Input({
  label,
  error,
  helperText,
  leftIcon,
  rightIcon,
  className = '',
  id,
  type = 'text',
  ...props
}) {
  const inputId = id || `input-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {label && (
        <label htmlFor={inputId} className="text-xs font-semibold text-[var(--text-muted)] tracking-wide uppercase">
          {label}
        </label>
      )}
      <div className="relative flex items-center w-full">
        {leftIcon && (
          <div className="absolute left-3 text-[var(--text-muted)] pointer-events-none flex items-center justify-center">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          type={type}
          className={`w-full h-10 bg-[var(--bg-surface)] text-[var(--text-main)] border text-sm rounded-xl px-3.5 py-2 transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-[var(--primary)] focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed ${
            leftIcon ? 'pl-10' : ''
          } ${rightIcon ? 'pr-10' : ''} ${
            error ? 'border-[var(--danger)] focus:ring-[var(--danger)]' : 'border-[var(--border-medium)]'
          } ${className}`}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 text-[var(--text-muted)] flex items-center justify-center">
            {rightIcon}
          </div>
        )}
      </div>
      {error ? (
        <span className="text-xs text-[var(--danger)] font-medium">{error}</span>
      ) : helperText ? (
        <span className="text-xs text-[var(--text-muted)]">{helperText}</span>
      ) : null}
    </div>
  );
}
