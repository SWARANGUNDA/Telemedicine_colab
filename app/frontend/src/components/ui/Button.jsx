import React from 'react';

/**
 * Reusable Production-Grade Button Component.
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  isDisabled = false,
  leftIcon = null,
  rightIcon = null,
  className = '',
  onClick,
  type = 'button',
  ...props
}) {
  const baseStyles = "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed select-none active:scale-[0.98]";

  const variantStyles = {
    primary: "bg-[var(--primary)] text-white hover:bg-[var(--primary-hover)] shadow-sm",
    secondary: "bg-[var(--secondary)] text-white hover:bg-[var(--secondary-hover)] shadow-sm",
    accent: "bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] shadow-sm",
    outline: "border border-[var(--border-medium)] bg-transparent text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]",
    ghost: "bg-transparent text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]",
    danger: "bg-[var(--danger)] text-white hover:bg-[var(--danger-hover)] shadow-sm",
  };

  const sizeStyles = {
    sm: "px-3 py-1.5 text-xs gap-1.5 min-h-[32px]",
    md: "px-4 py-2 text-sm gap-2 min-h-[40px]",
    lg: "px-6 py-3 text-base gap-2.5 min-h-[48px]",
  };

  return (
    <button
      type={type}
      disabled={isDisabled || isLoading}
      onClick={onClick}
      className={`${baseStyles} ${variantStyles[variant] || variantStyles.primary} ${sizeStyles[size] || sizeStyles.md} ${className}`}
      {...props}
    >
      {isLoading ? (
        <svg className="animate-spin h-4 w-4 text-current mr-1.5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      ) : leftIcon ? (
        <span className="inline-flex shrink-0">{leftIcon}</span>
      ) : null}

      <span>{children}</span>

      {!isLoading && rightIcon && (
        <span className="inline-flex shrink-0">{rightIcon}</span>
      )}
    </button>
  );
}
