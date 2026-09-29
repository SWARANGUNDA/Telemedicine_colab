import React from 'react';

export function Pagination({ currentPage = 1, totalPages = 1, onPageChange, className = '' }) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className={`flex items-center gap-1.5 ${className}`}>
      <button
        disabled={currentPage <= 1}
        onClick={() => onPageChange(currentPage - 1)}
        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border-medium)] bg-[var(--bg-surface)] text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Prev
      </button>

      {pages.map((p) => (
        <button
          key={p}
          onClick={() => onPageChange(p)}
          className={`w-8 h-8 text-xs font-mono font-medium rounded-lg transition-colors ${
            p === currentPage
              ? 'bg-[var(--primary)] text-white font-bold'
              : 'border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
          }`}
        >
          {p}
        </button>
      ))}

      <button
        disabled={currentPage >= totalPages}
        onClick={() => onPageChange(currentPage + 1)}
        className="px-3 py-1.5 text-xs font-medium rounded-lg border border-[var(--border-medium)] bg-[var(--bg-surface)] text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)] disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        Next
      </button>
    </div>
  );
}
