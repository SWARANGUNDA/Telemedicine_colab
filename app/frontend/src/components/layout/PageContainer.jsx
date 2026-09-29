import React from 'react';

export function PageContainer({ children, className = '' }) {
  return (
    <div className={`w-full max-w-[1600px] mx-auto px-4 md:px-6 lg:px-8 py-6 space-y-6 ${className}`}>
      {children}
    </div>
  );
}
