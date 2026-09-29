import React, { useEffect } from 'react';

export function Drawer({ isOpen = false, onClose, title, position = 'right', children, className = '' }) {
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

  const posStyles = {
    right: 'top-0 right-0 h-full w-80 md:w-96 border-l',
    left: 'top-0 left-0 h-full w-80 md:w-96 border-r',
  };

  return (
    <div className="fixed inset-0 z-[var(--z-drawer)]">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className={`fixed bg-[var(--bg-surface)] text-[var(--text-main)] border-[var(--border-subtle)] p-6 shadow-2xl flex flex-col justify-between transition-transform duration-300 ${posStyles[position] || posStyles.right} ${className}`}>
        <div>
          <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)] mb-4">
            <h3 className="text-base font-bold text-[var(--text-main)]">{title}</h3>
            <button onClick={onClose} className="p-1 text-[var(--text-muted)] hover:text-[var(--text-main)]">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
          </div>
          <div className="space-y-4 overflow-y-auto max-h-[calc(100vh-120px)]">{children}</div>
        </div>
      </div>
    </div>
  );
}
