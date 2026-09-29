import React from 'react';

export function Checkbox({
  label,
  checked = false,
  onChange,
  isDisabled = false,
  className = '',
  id,
  ...props
}) {
  const boxId = id || `chk-${Math.random().toString(36).substring(2, 9)}`;

  return (
    <label htmlFor={boxId} className={`inline-flex items-center gap-2.5 select-none cursor-pointer ${isDisabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
      <input
        id={boxId}
        type="checkbox"
        checked={checked}
        disabled={isDisabled}
        onChange={onChange}
        className="sr-only peer"
        {...props}
      />
      <div className="w-5 h-5 rounded border border-[var(--border-medium)] bg-[var(--bg-surface)] peer-checked:bg-[var(--primary)] peer-checked:border-[var(--primary)] transition-all duration-200 flex items-center justify-center peer-focus-visible:ring-2 peer-focus-visible:ring-[var(--primary)]">
        <svg className="w-3.5 h-3.5 text-white opacity-0 peer-checked:opacity-100 transition-opacity duration-150" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M5 13l4 4L19 7" />
        </svg>
      </div>
      {label && <span className="text-sm font-medium text-[var(--text-main)]">{label}</span>}
    </label>
  );
}
