import React, { useState } from 'react';

export function Tooltip({ content, position = 'top', children, className = '' }) {
  const [isVisible, setIsVisible] = useState(false);

  const posStyles = {
    top: '-top-10 left-1/2 -translate-x-1/2 mb-2',
    bottom: '-bottom-10 left-1/2 -translate-x-1/2 mt-2',
    left: 'top-1/2 -left-32 -translate-y-1/2 mr-2',
    right: 'top-1/2 -right-32 -translate-y-1/2 ml-2',
  };

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {children}
      {isVisible && (
        <div className={`absolute z-[var(--z-dropdown)] px-3 py-1.5 text-xs font-medium text-white bg-slate-900/90 dark:bg-slate-800/90 backdrop-blur-md rounded-md shadow-lg whitespace-nowrap pointer-events-none transition-all duration-150 ${posStyles[position] || posStyles.top} ${className}`}>
          {content}
        </div>
      )}
    </div>
  );
}
