import React, { useState } from 'react';
import { MOCK_SAMPLE_PAPERS } from '../../mock/mockData';

export default function PaperDiscoveryView({ onSelectPaper }) {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredPapers = MOCK_SAMPLE_PAPERS.filter(
    (p) =>
      p.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.paperId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.category.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Paper Discovery & Corpus
            </h1>
            <span className="badge badge-demo">Sample Corpus</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Corpus loaded from <code style={{ color: 'var(--accent-cyan)' }}>rag_engine/sample_data/</code> (paper_001 to paper_005).
          </p>
        </div>

        {/* Search filter input */}
        <div style={{ minWidth: '280px' }}>
          <input
            type="text"
            placeholder="Filter papers by title, ID, or domain..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-surface-elevated)',
              border: '1px solid var(--border-medium)',
              color: 'var(--text-primary)',
              fontSize: '13px',
              outline: 'none',
            }}
          />
        </div>
      </div>

      {/* Notice box */}
      <div
        style={{
          padding: '14px 18px',
          borderRadius: 'var(--radius-md)',
          background: 'rgba(99, 102, 241, 0.08)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
        }}
      >
        <span className="indicator-dot demo" />
        <span style={{ fontSize: '12px', color: 'var(--text-accent)' }}>
          <strong>Demo Notice:</strong> These 5 documents represent the initial medical imaging baseline in <code>rag_engine</code>. Dynamic PDF uploads will be enabled once the FastAPI ingestion endpoint is live.
        </span>
      </div>

      {/* Papers Grid */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {filteredPapers.map((paper) => (
          <div
            key={paper.paperId}
            className="card card-interactive"
            style={{ padding: '20px' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    fontWeight: '600',
                    color: 'var(--accent-cyan)',
                    background: 'rgba(6, 182, 212, 0.12)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid rgba(6, 182, 212, 0.25)',
                  }}
                >
                  {paper.paperId}
                </span>
                <span className="badge badge-indigo" style={{ fontSize: '10px' }}>
                  {paper.category}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Chunks: <strong style={{ color: 'var(--text-primary)' }}>{paper.chunksCount}</strong>
                </span>
                <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 5px' }}>
                  SAMPLE DATA
                </span>
              </div>
            </div>

            <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
              {paper.title}
            </h3>

            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '14px' }}>
              {paper.abstract}
            </p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Source: <code>rag_engine/sample_data/{paper.paperId}.txt</code>
              </span>
              <button
                className="btn btn-secondary"
                style={{ fontSize: '11px', padding: '4px 10px' }}
                onClick={() => onSelectPaper && onSelectPaper(paper)}
              >
                Inspect Paper Chunks →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
