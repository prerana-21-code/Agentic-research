import React from 'react';

export default function WelcomeBanner({ onQuickSearch }) {
  return (
    <div
      className="card fade-in"
      style={{
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
        border: '1px solid rgba(99, 102, 241, 0.25)',
        padding: '28px 32px',
        marginBottom: '24px',
        position: 'relative',
      }}
    >
      {/* Decorative ambient glow */}
      <div
        style={{
          position: 'absolute',
          top: '-40px',
          right: '-40px',
          width: '180px',
          height: '180px',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%)',
          pointerEvents: 'none',
        }}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
            <span className="badge badge-indigo">Agentic Research Assistant</span>
            <span className="badge badge-demo">Demo Mode UI</span>
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: '700', color: 'var(--text-primary)', letterSpacing: '-0.3px', marginBottom: '8px' }}>
            Welcome to your Autonomous Research Assistant
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', maxWidth: '720px', lineHeight: '1.6' }}>
            Accelerate literature review, multi-paper synthesis, and evidence extraction using
            hybrid dense-sparse retrieval (ChromaDB + BM25 with Reciprocal Rank Fusion).
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            className="btn btn-secondary"
            onClick={() => onQuickSearch && onQuickSearch('How are CNNs used to detect diseases in MRI images?')}
            style={{ fontSize: '12px' }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Try Sample Query
          </button>
        </div>
      </div>
    </div>
  );
}
