import React, { useState } from 'react';

export function Tabs({ tabs = [], defaultTab, onChange, className = '' }) {
  const [activeTab, setActiveTab] = useState(defaultTab || (tabs[0] && tabs[0].id));

  const handleTabClick = (id) => {
    setActiveTab(id);
    if (onChange) onChange(id);
  };

  const activeContent = tabs.find((t) => t.id === activeTab)?.content;

  return (
    <div className={`w-full flex flex-col gap-4 ${className}`}>
      <div className="flex border-b border-[var(--border-subtle)] gap-2 overflow-x-auto no-scrollbar">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`pb-3 px-4 text-sm font-medium transition-all relative border-b-2 whitespace-nowrap ${
                isActive
                  ? 'border-[var(--primary)] text-[var(--primary)] font-semibold'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-main)]'
              }`}
            >
              {tab.label}
              {tab.badge && <span className="ml-2 text-xs px-2 py-0.5 rounded-full bg-[var(--primary-light)] text-[var(--primary)]">{tab.badge}</span>}
            </button>
          );
        })}
      </div>
      <div className="pt-2">{activeContent}</div>
    </div>
  );
}
