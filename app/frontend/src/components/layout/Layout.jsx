import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { PageContainer } from './PageContainer';
import { Drawer } from '../ui/Drawer';

export function Layout({ children, user, onLogout, onToggleTheme, theme = 'dark', className = '', noPageContainer = false }) {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const userRole = user?.role || 'PATIENT';

  return (
    <div className="min-h-screen bg-[var(--bg-primary)] text-[var(--text-main)] flex flex-col font-sans transition-colors duration-200">
      {/* Desktop Fixed Left Sidebar */}
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        userRole={userRole}
      />

      {/* Main Content Area */}
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          isSidebarCollapsed ? 'lg:pl-[80px]' : 'lg:pl-[280px]'
        }`}
      >
        {/* Sticky Topbar */}
        <Topbar
          user={user}
          onLogout={onLogout}
          onToggleTheme={onToggleTheme}
          theme={theme}
          onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
        />

        {/* Page Container */}
        <main className="flex-1 flex flex-col" style={{ '--sidebar-width': isSidebarCollapsed ? '80px' : '280px' }}>
          {noPageContainer ? (
            children
          ) : (
            <PageContainer className={className}>
              {children}
            </PageContainer>
          )}
        </main>
      </div>

      {/* Mobile Menu Drawer */}
      <Drawer
        isOpen={isMobileMenuOpen}
        onClose={() => setIsMobileMenuOpen(false)}
        title="TeleMed AI Navigation"
        position="left"
      >
        <div className="py-2">
          <Sidebar
            isCollapsed={false}
            onToggleCollapse={() => {}}
            userRole={userRole}
            className="!flex !static !w-full !border-none"
          />
        </div>
      </Drawer>
    </div>
  );
}
