import React from 'react';

export default function TopHeader({ activeView, viewLabels }) {
  const currentLabel = viewLabels[activeView] || 'Dashboard';

  return (
    <header
      style={{
        height: 'var(--header-height)',
        padding: '0 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(13, 18, 28, 0.75)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Left: Breadcrumb */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Workspace</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '12px' }}>/</span>
        <span style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>
          {currentLabel}
        </span>
      </div>

      {/* Right: Environment & Integration Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {/* Backend Connectivity Status */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '5px 12px',
            borderRadius: '999px',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-medium)',
            fontSize: '12px',
          }}
          title="FastAPI server not yet connected. Dashboard is presenting isolated mock data."
        >
          <span className="indicator-dot disconnected" />
          <span style={{ color: 'var(--text-secondary)' }}>FastAPI Bridge:</span>
          <span style={{ fontWeight: '600', color: '#fb7185' }}>Not Connected</span>
        </div>

        {/* Git Branch Tag */}
        <div
          style={{
            padding: '4px 10px',
            borderRadius: 'var(--radius-sm)',
            background: 'rgba(99, 102, 241, 0.1)',
            border: '1px solid rgba(99, 102, 241, 0.25)',
            fontSize: '12px',
            color: 'var(--text-accent)',
            fontFamily: 'monospace',
          }}
        >
          git: mvp-review
        </div>
      </div>
    </header>
  );
}
