import React, { useState } from 'react';
import { MOCK_RECENT_ACTIVITIES, MOCK_SUGGESTED_QUERIES } from '../../mock/mockData';

export default function HybridRagView({ activeQuery: propQuery }) {
  const [query, setQuery] = useState(
    propQuery || 'How are CNNs used to detect diseases in MRI images?'
  );

  return (
    <div className="fade-in">
      {/* View Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Hybrid RAG Retrieval Results
            </h1>
            <span className="badge badge-indigo">Core RAG</span>
            <span className="badge badge-demo">Simulated Mock Results</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Inspect Reciprocal Rank Fusion (RRF) scores combining dense vector cosine similarity and sparse BM25 term matches.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge badge-demo">k = 60 constant</span>
        </div>
      </div>

      {/* RRF Formula Explanation Banner */}
      <div
        className="card"
        style={{
          padding: '16px 20px',
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.4) 100%)',
          border: '1px solid rgba(99, 102, 241, 0.25)',
          marginBottom: '20px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span
              style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: 'rgba(99, 102, 241, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'var(--primary-400)',
                flexShrink: 0,
              }}
            >
              ∑
            </span>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                Reciprocal Rank Fusion Pipeline
              </div>
              <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                RRF Score = <code>1 / (60 + DenseRank)</code> + <code>1 / (60 + SparseRank)</code>
              </div>
            </div>
          </div>
          <div style={{ fontSize: '11px', color: '#fbbf24', background: 'rgba(245, 158, 11, 0.1)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(245, 158, 11, 0.2)' }}>
            Notice: Showing mock RRF scores until FastAPI backend is live.
          </div>
        </div>
      </div>

      {/* Query Bar */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1,
              padding: '12px 16px',
              fontSize: '13px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-medium)',
              color: 'var(--text-primary)',
              outline: 'none',
            }}
          />
          <button className="btn btn-primary" onClick={() => {}}>
            Re-run Hybrid Search
          </button>
        </div>
      </div>

      {/* Ranked Retrieved Results List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {MOCK_RECENT_ACTIVITIES.map((item, idx) => (
          <div key={item.id} className="card card-interactive" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span
                  style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '999px',
                    background: 'var(--primary-600)',
                    color: '#fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '11px',
                    fontWeight: '700',
                  }}
                >
                  #{idx + 1}
                </span>
                <span style={{ fontFamily: 'monospace', fontWeight: '600', color: 'var(--accent-cyan)', fontSize: '13px' }}>
                  {item.topChunkId}
                </span>
                <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 6px' }}>
                  SIMULATED RESULT
                </span>
              </div>

              {/* Score Badges */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'rgba(245, 158, 11, 0.1)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    color: '#fbbf24',
                  }}
                >
                  RRF Score: <strong>{item.mockRrfScore.toFixed(6)}</strong>
                </div>
              </div>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6', marginBottom: '12px', background: 'var(--bg-surface-elevated)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              "{item.topChunkSnippet}"
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)' }}>
              <div>
                Associated Paper: <strong style={{ color: 'var(--text-secondary)' }}>{item.matchedPapers.join(', ')}</strong>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: '11px', padding: '2px 8px' }}
                  onClick={() => alert(`Chunk ${item.topChunkId} metadata inspection.`)}
                >
                  Inspect Chunk Metadata
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
