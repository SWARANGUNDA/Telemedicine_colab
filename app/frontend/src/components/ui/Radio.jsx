import React from 'react';

export function Radio({
  label,
  value,
  name,
  checked = false,
  onChange,
  isDisabled = false,
  className = '',
  id,
  ...props
}) {
  const radioId = id || `rad-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <label htmlFor={radioId} className={`inline-flex items-center gap-2.5 select-none cursor-pointer ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
      <input
        id={radioId}
        type="radio"
        name={name}
        value={value}
        checked={checked}
        disabled={isDisabled}
        onChange={onChange}
        className="sr-only peer"
        {...props}
      />
      <div className="w-5 h-5 rounded-full border border-[var(--border-medium)] bg-[var(--bg-surface)] peer-checked:border-[var(--primary)] transition-all duration-200 flex items-center justify-center peer-focus-visible:ring-2 peer-focus-visible:ring-[var(--primary)]">
        <div className="w-2.5 h-2.5 rounded-full bg-[var(--primary)] opacity-0 peer-checked:opacity-100 transition-opacity duration-150" />
      </div>
      {label && <span className="text-sm font-medium text-[var(--text-main)]">{label}</span>}
    </label>
  );
}
