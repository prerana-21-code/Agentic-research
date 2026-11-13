import React, { useState } from 'react';

export default function ResearchWorkspaceView() {
  const [notes, setNotes] = useState(
    '# Research Notes & Hypothesis Generation\n\n- Key finding: CNNs show strong local texture extraction for chest X-ray scans.\n- Vision Transformers (ViTs) excel at global long-range context in brain MRI, but require higher computational resources.\n- Opportunity: Hybrid CNN-Transformer architectures to balance spatial precision and receptive field.'
  );

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Research Workspace
            </h1>
            <span className="badge badge-demo">Interactive Mock Workspace</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Draft research summaries, organize evidence snippets, and prepare multi-paper syntheses.
          </p>
        </div>
        <button
          className="btn btn-secondary"
          onClick={() => alert('Demo Mode: Notes are preserved in the current browser session.')}
        >
          Export Notes (Markdown)
        </button>
      </div>

      <div className="grid-2">
        {/* Editor Side */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
              Active Research Draft
            </span>
            <span className="badge badge-indigo">Markdown</span>
          </div>

          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={16}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-medium)',
              color: 'var(--text-primary)',
              fontFamily: 'monospace',
              fontSize: '13px',
              lineHeight: '1.6',
              resize: 'vertical',
              outline: 'none',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '11px', color: 'var(--text-muted)' }}>
            <span>Words: {notes.split(/\s+/).filter(Boolean).length}</span>
            <span>Local draft state</span>
          </div>
        </div>

        {/* Evidence Pins Side */}
        <div className="card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
            <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
              Pinned Evidence Snippets
            </span>
            <span className="badge badge-demo">Sample Pins</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div
              style={{
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--accent-cyan)' }}>
                  paper_001_chunk_1
                </span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Score: 0.032258</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                "Convolutional Neural Networks (CNNs) are widely used for analysing X-ray images, MRI scans, and CT scans..."
              </p>
            </div>

            <div
              style={{
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--accent-cyan)' }}>
                  paper_002_chunk_1
                </span>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Score: 0.031746</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                "Vision Transformers (ViTs) demonstrate remarkable performance in capturing global context across biomedical scans..."
              </p>
            </div>

            <div
              style={{
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'rgba(245, 158, 11, 0.05)',
                border: '1px dashed rgba(245, 158, 11, 0.3)',
                textAlign: 'center',
                color: 'var(--text-muted)',
                fontSize: '12px',
              }}
            >
              Pin additional chunks from the <strong>Hybrid RAG Results</strong> tab.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
