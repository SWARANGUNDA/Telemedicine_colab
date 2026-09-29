import React from 'react';

export function Switch({
  label,
  checked = false,
  onChange,
  isDisabled = false,
  className = '',
  id,
  ...props
}) {
  const switchId = id || `sw-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <label htmlFor={switchId} className={`inline-flex items-center gap-3 select-none cursor-pointer ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
      <input
        id={switchId}
        type="checkbox"
        checked={checked}
        disabled={isDisabled}
        onChange={onChange}
        className="sr-only peer"
        {...props}
      />
      <div className="relative w-11 h-6 bg-[var(--border-medium)] rounded-full peer-checked:bg-[var(--primary)] transition-colors duration-200 peer-focus-visible:ring-2 peer-focus-visible:ring-[var(--primary)]">
        <div className="absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform duration-200 peer-checked:translate-x-5 shadow-sm" />
      </div>
      {label && <span className="text-sm font-medium text-[var(--text-main)]">{label}</span>}
    </label>
  );
}
