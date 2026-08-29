import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { DisclaimerBanner } from './DisclaimerBanner';
import { SnapshotStatusBar } from './SnapshotStatusBar';

export const AppShell: React.FC = () => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-slate-100 font-sans">
      {/* 1. Mandatory Scientific Disclaimer Banner (Pinned Top) */}
      <DisclaimerBanner />

      {/* 2. Main Middle Area (Sidebar + Content Workspace) */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop Sidebar */}
        <div className="hidden md:flex flex-col h-full">
          <Sidebar
            isCollapsed={isSidebarCollapsed}
            onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />
        </div>

        {/* Mobile Sidebar Overlay */}
        {isMobileMenuOpen && (
          <div className="fixed inset-0 z-50 flex md:hidden">
            <div
              className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity"
              onClick={() => setIsMobileMenuOpen(false)}
            />
            <div className="relative flex flex-col w-64 max-w-xs bg-navy-900 shadow-xl">
              <Sidebar
                isCollapsed={false}
                onToggleCollapse={() => setIsMobileMenuOpen(false)}
              />
            </div>
          </div>
        )}

        {/* Workspace Container */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {/* Header */}
          <Header onToggleMobileMenu={() => setIsMobileMenuOpen(!isMobileMenuOpen)} />

          {/* Main Content Area with scroll */}
          <main className="flex-1 overflow-y-auto bg-slate-100 p-4 md:p-6">
            <div className="max-w-7xl mx-auto">
              <Outlet />
            </div>
          </main>

          {/* Persistent Data Freshness / Snapshot Status Footer */}
          <SnapshotStatusBar />
        </div>
      </div>
    </div>
  );
};
