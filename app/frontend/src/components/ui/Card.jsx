import React from 'react';

export function Card({ children, className = '', isGlass = true, ...props }) {
  return (
    <div
      className={`${
        isGlass ? 'glass-card' : 'bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-sm'
      } p-6 transition-all duration-200 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = '' }) {
  return <div className={`mb-4 pb-3 border-b border-[var(--border-subtle)] flex items-center justify-between ${className}`}>{children}</div>;
}

export function CardBody({ children, className = '' }) {
  return <div className={`space-y-4 ${className}`}>{children}</div>;
}

export function CardFooter({ children, className = '' }) {
  return <div className={`mt-6 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-end gap-3 ${className}`}>{children}</div>;
}
