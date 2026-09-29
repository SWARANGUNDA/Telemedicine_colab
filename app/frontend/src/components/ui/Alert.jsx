import React from 'react';

export function Alert({ title, children, variant = 'info', icon, className = '' }) {
  const variantStyles = {
    info: 'bg-[var(--primary-light)] text-[var(--primary)] border-[var(--primary)]/20',
    success: 'bg-[var(--success-light)] text-[var(--success)] border-[var(--success)]/20',
    warning: 'bg-[var(--warning-light)] text-[var(--warning)] border-[var(--warning)]/20',
    danger: 'bg-[var(--danger-light)] text-[var(--danger)] border-[var(--danger)]/20',
  };

  return (
    <div className={`p-4 rounded-xl border flex items-start gap-3 text-sm ${variantStyles[variant] || variantStyles.info} ${className}`}>
      {icon && <div className="shrink-0 mt-0.5">{icon}</div>}
      <div className="flex-1">
        {title && <h5 className="font-bold text-sm mb-1">{title}</h5>}
        <div className="text-xs opacity-90">{children}</div>
      </div>
    </div>
  );
}
