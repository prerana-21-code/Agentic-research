import React from 'react';
import WelcomeBanner from '../dashboard/WelcomeBanner';
import ResearchQueryInput from '../dashboard/ResearchQueryInput';
import StatsOverview from '../dashboard/StatsOverview';
import ModuleStatus from '../dashboard/ModuleStatus';
import RecentActivity from '../dashboard/RecentActivity';
import QuickNavGrid from '../dashboard/QuickNavGrid';

export default function DashboardView({ onNavigate, onSearchSubmit }) {
  return (
    <div className="fade-in">
      {/* 1. Welcome section */}
      <WelcomeBanner
        onQuickSearch={(query) => {
          onSearchSubmit && onSearchSubmit(query, 'hybrid');
        }}
      />

      {/* 2. Research question input area */}
      <ResearchQueryInput onSearchSubmit={onSearchSubmit} />

      {/* 3. Paper statistics */}
      <StatsOverview />

      {/* 4. Two-Column Layout: Module integration status & Recent research activity */}
      <div className="grid-2" style={{ marginBottom: '24px' }}>
        <ModuleStatus />
        <RecentActivity onViewAll={() => onNavigate('hybrid_rag')} />
      </div>

      {/* 5. Quick navigation cards */}
      <QuickNavGrid onNavigate={onNavigate} />
    </div>
  );
}
