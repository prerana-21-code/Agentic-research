import React from 'react';
import { MOCK_CORPUS_STATS } from '../../mock/mockData';

export default function StatsOverview() {
  const stats = [
    {
      id: 'papers',
      label: 'Sample Papers',
      value: MOCK_CORPUS_STATS.totalPapers,
      subtext: 'Pre-loaded in sample_data',
      tag: 'DEMO DATA',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
        </svg>
      ),
      color: 'var(--accent-cyan)',
    },
    {
      id: 'chunks',
      label: 'Indexed Chunks',
      value: MOCK_CORPUS_STATS.indexedChunks,
      subtext: 'Sentence-aware (500c/100o)',
      tag: 'DEMO DATA',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <rect width="8" height="8" x="3" y="3" rx="2"/>
          <rect width="8" height="8" x="13" y="3" rx="2"/>
          <rect width="8" height="8" x="3" y="13" rx="2"/>
          <rect width="8" height="8" x="13" y="13" rx="2"/>
        </svg>
      ),
      color: 'var(--primary-400)',
    },
    {
      id: 'embeddings',
      label: 'Vector Dimensions',
      value: `${MOCK_CORPUS_STATS.embeddingDimension}d`,
      subtext: MOCK_CORPUS_STATS.embeddingModel,
      tag: 'DEMO DATA',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        </svg>
      ),
      color: 'var(--accent-emerald)',
    },
    {
      id: 'fusion',
      label: 'Fusion Strategy',
      value: 'RRF (k=60)',
      subtext: 'ChromaDB + BM25 Okapi',
      tag: 'DEMO DATA',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="2" y1="12" x2="22" y2="12"/>
          <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
      ),
      color: '#f59e0b',
    },
  ];

  return (
    <div style={{ marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Corpus Statistics
          </h2>
          <span className="badge badge-demo">Sample / Demo Data</span>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Actual measured latency & live counts will display after backend integration
        </span>
      </div>

      <div className="grid-4">
        {stats.map((stat) => (
          <div key={stat.id} className="card card-interactive" style={{ padding: '18px 20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
              <div
                style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-surface-elevated)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: stat.color,
                  border: '1px solid var(--border-medium)',
                }}
              >
                {stat.icon}
              </div>
              <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 6px' }}>
                {stat.tag}
              </span>
            </div>

            <div style={{ fontSize: '24px', fontWeight: '700', color: 'var(--text-primary)', marginBottom: '4px' }}>
              {stat.value}
            </div>

            <div style={{ fontSize: '13px', fontWeight: '500', color: 'var(--text-secondary)' }}>
              {stat.label}
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              {stat.subtext}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
