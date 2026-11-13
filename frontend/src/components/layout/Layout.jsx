import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopHeader from './TopHeader';

export default function Layout({ activeView, setActiveView, children }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const viewLabels = {
    dashboard: 'Research Dashboard',
    discovery: 'Paper Discovery',
    workspace: 'Research Workspace',
    hybrid_rag: 'Hybrid RAG Retrieval Results',
    comparison: 'Paper Comparison Matrix',
    gaps: 'AI Research Gaps Identifier',
    reports: 'Research Reports & Syntheses',
  };

  return (
    <div className="app-container">
      {/* Collapsible Left Sidebar */}
      <Sidebar
        activeView={activeView}
        setActiveView={setActiveView}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
      />

      {/* Main Content Area */}
      <div className="main-content-wrapper">
        <TopHeader activeView={activeView} viewLabels={viewLabels} />
        <main className="page-content">{children}</main>
      </div>
    </div>
  );
}
