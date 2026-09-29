import React from 'react';

export function CircularProgress({ value = 0, size = 64, strokeWidth = 6, variant = 'primary', label, className = '' }) {
  const pct = Math.min(100, Math.max(0, value));
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  const colorMap = {
    primary: 'var(--primary)',
    secondary: 'var(--secondary)',
    success: 'var(--success)',
    warning: 'var(--warning)',
    danger: 'var(--danger)',
  };

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`} style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--border-medium)"
          strokeWidth={strokeWidth}
          fill="none"
          className="opacity-30"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={colorMap[variant] || colorMap.primary}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <span className="absolute font-mono text-xs font-bold text-[var(--text-main)]">
        {label ? label : `${Math.round(pct)}%`}
      </span>
    </div>
  );
}
