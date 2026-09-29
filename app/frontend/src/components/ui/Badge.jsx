import React from 'react';

export function Badge({ children, variant = 'primary', size = 'md', className = '', ...props }) {
  const variantStyles = {
    primary: "bg-[var(--primary-light)] text-[var(--primary)] border-[var(--primary)]/20",
    secondary: "bg-[var(--secondary-light)] text-[var(--secondary)] border-[var(--secondary)]/20",
    accent: "bg-[var(--accent-light)] text-[var(--accent)] border-[var(--accent)]/20",
    success: "bg-[var(--success-light)] text-[var(--success)] border-[var(--success)]/20",
    warning: "bg-[var(--warning-light)] text-[var(--warning)] border-[var(--warning)]/20",
    danger: "bg-[var(--danger-light)] text-[var(--danger)] border-[var(--danger)]/20",
    info: "bg-slate-500/10 text-slate-400 border-slate-500/20",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-[10px] font-semibold tracking-wider",
    md: "px-2.5 py-1 text-xs font-semibold tracking-wide",
    lg: "px-3 py-1.5 text-sm font-semibold",
  };

  return (
    <span
      className={`inline-flex items-center rounded-full border uppercase font-mono ${variantStyles[variant] || variantStyles.primary} ${sizeStyles[size] || sizeStyles.md} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
