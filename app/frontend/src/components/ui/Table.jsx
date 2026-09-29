import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export function Table({ headers = [], children, className = '', maxRows = 5, collapsible = true }) {
  const [expanded, setExpanded] = useState(false);
  const rows = React.Children.toArray(children);
  const isCollapsible = collapsible && rows.length > maxRows;
  
  const displayRows = isCollapsible && !expanded ? rows.slice(0, maxRows) : rows;
  const hiddenCount = rows.length - maxRows;

  return (
    <div className={`w-full flex flex-col gap-2 ${className}`}>
      {isCollapsible && (
        <div className="flex justify-between items-center bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg p-2 px-4 shadow-sm">
          <span className="text-xs font-semibold text-[var(--text-muted)]">
            Showing <strong className="text-[var(--text-main)]">{expanded ? rows.length : maxRows}</strong> of <strong className="text-[var(--text-main)]">{rows.length}</strong> items
          </span>
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold text-[var(--primary)] bg-[var(--primary)]/5 hover:bg-[var(--primary)]/15 transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--primary)]/20"
          >
            {expanded ? (
              <>Show Less <ChevronUp className="w-4 h-4" /></>
            ) : (
              <>Show All ({hiddenCount} More) <ChevronDown className="w-4 h-4" /></>
            )}
          </button>
        </div>
      )}
      <div className="w-full overflow-x-auto border border-[var(--border-subtle)] rounded-xl bg-[var(--bg-surface)]">
        <table className="w-full text-left text-sm text-[var(--text-main)] border-collapse">
          {headers.length > 0 && (
            <thead className="sticky top-0 z-10 bg-[var(--bg-primary)] text-xs uppercase font-semibold text-[var(--text-muted)] border-b border-[var(--border-subtle)]">
              <tr>
                {headers.map((h, i) => (
                  <th key={i} className="px-4 py-3 font-mono">{h}</th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className="divide-y divide-[var(--border-subtle)]">{displayRows}</tbody>
        </table>
      </div>
    </div>
  );
}

export function TableRow({ children, className = '' }) {
  return <tr className={`hover:bg-[var(--bg-surface-hover)] transition-colors ${className}`}>{children}</tr>;
}

export function TableCell({ children, className = '' }) {
  return <td className={`px-4 py-3.5 align-middle ${className}`}>{children}</td>;
}
