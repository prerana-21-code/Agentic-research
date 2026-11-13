import React, { useState } from 'react';
import Layout from './components/layout/Layout';
import DashboardView from './components/views/DashboardView';
import PaperDiscoveryView from './components/views/PaperDiscoveryView';
import ResearchWorkspaceView from './components/views/ResearchWorkspaceView';
import HybridRagView from './components/views/HybridRagView';
import PaperComparisonView from './components/views/PaperComparisonView';
import ResearchGapsView from './components/views/ResearchGapsView';
import ResearchReportsView from './components/views/ResearchReportsView';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [activeQuery, setActiveQuery] = useState('');

  const handleSearchSubmit = (query, mode) => {
    setActiveQuery(query);
    setActiveView('hybrid_rag');
  };

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return (
          <DashboardView
            onNavigate={(viewId) => setActiveView(viewId)}
            onSearchSubmit={handleSearchSubmit}
          />
        );
      case 'discovery':
        return <PaperDiscoveryView />;
      case 'workspace':
        return <ResearchWorkspaceView />;
      case 'hybrid_rag':
        return <HybridRagView activeQuery={activeQuery} />;
      case 'comparison':
        return <PaperComparisonView />;
      case 'gaps':
        return <ResearchGapsView />;
      case 'reports':
        return <ResearchReportsView />;
      default:
        return (
          <DashboardView
            onNavigate={(viewId) => setActiveView(viewId)}
            onSearchSubmit={handleSearchSubmit}
          />
        );
    }
  };

  return (
    <Layout activeView={activeView} setActiveView={setActiveView}>
      {renderActiveView()}
    </Layout>
  );
}
