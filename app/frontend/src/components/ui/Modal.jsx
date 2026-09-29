import React, { useEffect } from 'react';

export function Modal({ isOpen = false, onClose, title, children, footer, className = '', contentClassName = '' }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen && onClose) onClose();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[var(--z-modal)] flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Backdrop with 16px blur */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-md transition-opacity animate-fade-in"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className={`relative z-10 w-full my-auto max-h-[90vh] flex flex-col ${className.includes('max-w-') ? '' : 'max-w-lg'} p-5 sm:p-6 border border-[var(--border-subtle)] shadow-2xl rounded-3xl bg-[var(--bg-surface)] text-[var(--text-main)] transition-all animate-scale-in ${className}`}>
        <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)] shrink-0">
          <h3 className="text-lg font-bold text-[var(--text-main)] tracking-tight">{title}</h3>
          <button
            onClick={onClose}
            className="text-[var(--text-muted)] hover:text-[var(--text-main)] p-1.5 rounded-xl hover:bg-[var(--bg-primary)] transition-colors cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className={`py-4 space-y-4 flex-1 min-h-0 ${contentClassName.includes('overflow-') ? contentClassName : `overflow-y-auto ${contentClassName}`}`}>
          {children}
        </div>

        {footer && <div className="pt-4 border-t border-[var(--border-subtle)] flex items-center justify-end gap-3 shrink-0">{footer}</div>}
      </div>
    </div>
  );
}
