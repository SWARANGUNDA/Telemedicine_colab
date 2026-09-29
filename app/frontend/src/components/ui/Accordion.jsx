import React, { useState } from 'react';

export function Accordion({ items = [], className = '' }) {
  const [openIdx, setOpenIdx] = useState(null);

  const toggle = (idx) => {
    setOpenIdx(openIdx === idx ? null : idx);
  };

  return (
    <div className={`divide-y divide-[var(--border-subtle)] border border-[var(--border-subtle)] rounded-xl overflow-hidden ${className}`}>
      {items.map((item, idx) => {
        const isOpen = openIdx === idx;
        return (
          <div key={idx} className="bg-[var(--bg-surface)]">
            <button
              onClick={() => toggle(idx)}
              className="w-full p-4 flex items-center justify-between text-left font-medium text-sm text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)] transition-colors"
            >
              <span>{item.title}</span>
              <svg
                className={`w-4 h-4 text-[var(--text-muted)] transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
            {isOpen && <div className="p-4 pt-0 text-sm text-[var(--text-muted)] border-t border-[var(--border-subtle)] bg-[var(--bg-primary)]/50">{item.content}</div>}
          </div>
        );
      })}
    </div>
  );
}
