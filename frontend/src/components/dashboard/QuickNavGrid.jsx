import React from 'react';

export default function QuickNavGrid({ onNavigate }) {
  const cards = [
    {
      viewId: 'discovery',
      title: 'Paper Discovery',
      description: 'Explore the 5 pre-loaded research papers, chunk partitions, and metadata.',
      tag: '5 Papers',
      tagType: 'badge-cyan',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.3-4.3"/>
          <path d="M11 8v6"/>
          <path d="M8 11h6"/>
        </svg>
      ),
    },
    {
      viewId: 'hybrid_rag',
      title: 'Hybrid RAG Inspector',
      description: 'Deep dive into Reciprocal Rank Fusion, ChromaDB distances, and BM25 scores.',
      tag: 'Core RAG',
      tagType: 'badge-indigo',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="m12 3-1.9 5.8a2 2 0 0 1-1.3 1.3L3 12l5.8 1.9a2 2 0 0 1 1.3 1.3L12 21l1.9-5.8a2 2 0 0 1 1.3-1.3L21 12l-5.8-1.9a2 2 0 0 1-1.3-1.3Z"/>
        </svg>
      ),
    },
    {
      viewId: 'workspace',
      title: 'Research Workspace',
      description: 'Synthesize insights, cross-reference chunk citations, and draft evidence.',
      tag: 'Analysis',
      tagType: 'badge-demo',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/>
          <path d="M6 6h10"/>
          <path d="M6 10h10"/>
        </svg>
      ),
    },
    {
      viewId: 'gaps',
      title: 'Research Gaps',
      description: 'Pinpoint contradictions, unaddressed questions, and methodology gaps.',
      tag: 'AI Reasoning',
      tagType: 'badge-indigo',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      ),
    },
  ];

  return (
    <div style={{ marginTop: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
          Quick Navigation
        </h3>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
          Access dedicated research tools
        </span>
      </div>

      <div className="grid-4">
        {cards.map((card) => (
          <div
            key={card.viewId}
            className="card card-interactive"
            onClick={() => onNavigate && onNavigate(card.viewId)}
            style={{ cursor: 'pointer', padding: '20px' }}
          >
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
                  color: 'var(--primary-400)',
                  border: '1px solid var(--border-medium)',
                }}
              >
                {card.icon}
              </div>
              <span className={`badge ${card.tagType}`} style={{ fontSize: '9px', padding: '1px 6px' }}>
                {card.tag}
              </span>
            </div>

            <div style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              {card.title}
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '14px' }}>
              {card.description}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--primary-400)', fontWeight: '600' }}>
              <span>Open tool</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
