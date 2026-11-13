import React from 'react';

/**
 * Sidebar Navigation Component
 * Features 7 dedicated research assistant views + collapse toggle
 */
export default function Sidebar({ activeView, setActiveView, isCollapsed, setIsCollapsed }) {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect width="7" height="9" x="3" y="3" rx="1"/>
          <rect width="7" height="5" x="14" y="3" rx="1"/>
          <rect width="7" height="9" x="14" y="12" rx="1"/>
          <rect width="7" height="5" x="3" y="16" rx="1"/>
        </svg>
      ),
      badge: null,
    },
    {
      id: 'discovery',
      label: 'Paper Discovery',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.3-4.3"/>
          <path d="M11 8v6"/>
          <path d="M8 11h6"/>
        </svg>
      ),
      badge: '5 Papers',
    },
    {
      id: 'workspace',
      label: 'Research Workspace',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
          <path d="M6 6h10"/>
          <path d="M6 10h10"/>
          <path d="M6 14h6"/>
        </svg>
      ),
      badge: null,
    },
    {
      id: 'hybrid_rag',
      label: 'Hybrid RAG Results',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>
        </svg>
      ),
      badge: 'Core RAG',
    },
    {
      id: 'comparison',
      label: 'Paper Comparison',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m16 3 4 4-4 4"/>
          <path d="M20 7H4"/>
          <path d="m8 21-4-4 4-4"/>
          <path d="M4 17h16"/>
        </svg>
      ),
      badge: null,
    },
    {
      id: 'gaps',
      label: 'Research Gaps',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 2v4"/>
          <path d="m4.93 4.93 2.83 2.83"/>
          <path d="M2 12h4"/>
          <path d="m4.93 19.07 2.83-2.83"/>
          <path d="M12 22v-4"/>
          <path d="m19.07 19.07-2.83-2.83"/>
          <path d="M22 12h-4"/>
          <path d="m19.07 4.93-2.83 2.83"/>
        </svg>
      ),
      badge: 'AI Insight',
    },
    {
      id: 'reports',
      label: 'Research Reports',
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <line x1="10" y1="9" x2="8" y2="9"/>
        </svg>
      ),
      badge: null,
    },
  ];

  return (
    <aside
      className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}
      style={{
        width: isCollapsed ? 'var(--sidebar-width-collapsed)' : 'var(--sidebar-width)',
        background: 'var(--bg-sidebar)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        transition: 'width var(--transition-smooth)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}
    >
      {/* Brand Header */}
      <div
        style={{
          padding: '18px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: isCollapsed ? 'center' : 'space-between',
          borderBottom: '1px solid var(--border-subtle)',
          minHeight: 'var(--header-height)',
        }}
      >
        {!isCollapsed ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', overflow: 'hidden' }}>
            <div
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--accent-cyan) 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                boxShadow: '0 2px 8px rgba(99, 102, 241, 0.4)',
                flexShrink: 0,
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"/>
                <path d="m4.93 4.93 4.24 4.24"/>
                <path d="m14.83 9.17 4.24-4.24"/>
                <path d="m14.83 14.83 4.24 4.24"/>
                <path d="m9.17 14.83-4.24 4.24"/>
              </svg>
            </div>
            <div style={{ overflow: 'hidden' }}>
              <div style={{ fontWeight: '700', fontSize: '14px', letterSpacing: '-0.2px', color: 'var(--text-primary)' }}>
                Agentic Research
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Hybrid RAG Assistant
              </div>
            </div>
          </div>
        ) : (
          <div
            style={{
              width: '32px',
              height: '32px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, var(--primary-500) 0%, var(--accent-cyan) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
            </svg>
          </div>
        )}

        {/* Collapse Button */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '6px',
            borderRadius: 'var(--radius-sm)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'color var(--transition-fast)',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text-primary)')}
          onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{
              transform: isCollapsed ? 'rotate(180deg)' : 'none',
              transition: 'transform var(--transition-smooth)',
            }}
          >
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
      </div>

      {/* Navigation List */}
      <nav style={{ padding: '12px 8px', flex: 1, overflowY: 'auto' }}>
        <div
          style={{
            fontSize: '11px',
            fontWeight: '600',
            textTransform: 'uppercase',
            letterSpacing: '0.6px',
            color: 'var(--text-muted)',
            padding: isCollapsed ? '8px 0' : '8px 12px 6px',
            textAlign: isCollapsed ? 'center' : 'left',
          }}
        >
          {isCollapsed ? '•' : 'WORKSPACE SECTIONS'}
        </div>

        <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '3px' }}>
          {navItems.map((item) => {
            const isActive = activeView === item.id;
            return (
              <li key={item.id}>
                <button
                  onClick={() => setActiveView(item.id)}
                  title={isCollapsed ? item.label : undefined}
                  style={{
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: isCollapsed ? '10px 0' : '10px 12px',
                    justifyContent: isCollapsed ? 'center' : 'flex-start',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid',
                    borderColor: isActive ? 'var(--border-glow)' : 'transparent',
                    background: isActive
                      ? 'linear-gradient(90deg, rgba(99, 102, 241, 0.16) 0%, rgba(99, 102, 241, 0.05) 100%)'
                      : 'transparent',
                    color: isActive ? '#ffffff' : 'var(--text-secondary)',
                    fontWeight: isActive ? '600' : '500',
                    fontSize: '13px',
                    cursor: 'pointer',
                    transition: 'all var(--transition-fast)',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = 'var(--bg-surface-hover)';
                      e.currentTarget.style.color = 'var(--text-primary)';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!isActive) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.color = 'var(--text-secondary)';
                    }
                  }}
                >
                  <span
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: isActive ? 'var(--primary-400)' : 'var(--text-muted)',
                    }}
                  >
                    {item.icon}
                  </span>

                  {!isCollapsed && (
                    <>
                      <span style={{ flex: 1, textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.label}
                      </span>
                      {item.badge && (
                        <span
                          style={{
                            fontSize: '10px',
                            fontWeight: '600',
                            padding: '1px 6px',
                            borderRadius: '999px',
                            background: isActive ? 'rgba(99, 102, 241, 0.3)' : 'var(--bg-surface-elevated)',
                            color: isActive ? '#c7d2fe' : 'var(--text-muted)',
                            border: '1px solid var(--border-subtle)',
                          }}
                        >
                          {item.badge}
                        </span>
                      )}
                    </>
                  )}
                </button>
              </li>
            );
          })}
        </ul>
      </nav>

      {/* Footer Status Pill */}
      <div
        style={{
          padding: '14px',
          borderTop: '1px solid var(--border-subtle)',
          background: 'rgba(0, 0, 0, 0.2)',
        }}
      >
        {!isCollapsed ? (
          <div
            style={{
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)' }}>
                PIPELINE STATUS
              </span>
              <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 6px' }}>
                DEMO MODE
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
              Branch: <code style={{ color: 'var(--accent-cyan)' }}>mvp-review</code>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <span className="indicator-dot demo" title="Pipeline Status: Demo Mode" />
          </div>
        )}
      </div>
    </aside>
  );
}
