import React from 'react';

export function EmptyState({ icon, title = 'No Data Found', description = 'There are no items to display at this time.', action = null, className = '' }) {
  const renderIcon = () => {
    if (!icon) return null;
    if (React.isValidElement(icon)) return icon;
    if (typeof icon === 'function' || (typeof icon === 'object' && icon !== null)) {
      const IconComp = icon;
      return <IconComp className="w-8 h-8 text-[var(--primary)]" />;
    }
    return null;
  };

  return (
    <div className={`flex flex-col items-center justify-center p-8 text-center border border-dashed border-[var(--border-medium)] rounded-2xl bg-[var(--bg-surface)]/50 ${className}`}>
      {icon && <div className="p-4 mb-4 rounded-full bg-[var(--primary-light)] text-[var(--primary)]">{renderIcon()}</div>}
      <h4 className="text-base font-bold text-[var(--text-main)] mb-1">{title}</h4>
      <p className="text-xs text-[var(--text-muted)] max-w-sm mb-6">{description}</p>
      {action}
    </div>
  );
}
