import React from 'react';
import { MOCK_RECENT_ACTIVITIES } from '../../mock/mockData';

export default function RecentActivity({ onViewAll }) {
  return (
    <div className="card" style={{ height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Recent Research Activity
          </h3>
          <span className="badge badge-demo">Simulated Mock Data</span>
        </div>
        <button
          className="btn btn-ghost"
          style={{ fontSize: '11px', padding: '4px 8px' }}
          onClick={onViewAll}
        >
          View in RAG Results →
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {MOCK_RECENT_ACTIVITIES.map((activity) => (
          <div
            key={activity.id}
            style={{
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-subtle)',
              transition: 'border-color var(--transition-fast)',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'var(--border-glow)')}
            onMouseLeave={(e) => (e.currentTarget.style.borderColor = 'var(--border-subtle)')}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px', marginBottom: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                <span className="badge badge-cyan" style={{ fontSize: '10px' }}>
                  {activity.searchMode}
                </span>
                <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 5px' }}>
                  MOCK RECORD
                </span>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {activity.timestamp}
              </span>
            </div>

            <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              "{activity.query}"
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '8px' }}>
              {activity.topChunkSnippet}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', paddingTop: '6px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              <div>
                Matched: <code style={{ color: 'var(--text-accent)' }}>{activity.matchedPapers.join(', ')}</code>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span>Simulated RRF Score:</span>
                <strong style={{ color: '#fbbf24', fontFamily: 'monospace' }}>
                  {activity.mockRrfScore.toFixed(6)}
                </strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
