import React from 'react';

export default function ResearchReportsView() {
  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Synthesized Research Reports
            </h1>
            <span className="badge badge-demo">Sample Synthesis Report</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Automated executive summary synthesized across multi-paper evidence.
          </p>
        </div>

        <button
          className="btn btn-secondary"
          onClick={() => alert('Demo Mode: Report export will be connected in a future phase.')}
        >
          Export Report (.pdf / .md)
        </button>
      </div>

      <div className="card" style={{ padding: '28px 32px' }}>
        <div style={{ borderBottom: '1px solid var(--border-medium)', paddingBottom: '16px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <span className="badge badge-cyan">Automated Evidence Synthesis</span>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Corpus: 5 Papers (11 Chunks)</span>
          </div>
          <h2 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-primary)' }}>
            Deep Learning in Diagnostic Neuroimaging: State of the Art & Open Questions
          </h2>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', fontSize: '13px', lineHeight: '1.7', color: 'var(--text-secondary)' }}>
          <section>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              1. Executive Summary
            </h3>
            <p>
              Across the evaluated corpus (paper_001 through paper_005), artificial intelligence applications in healthcare have demonstrated notable advances in medical image classification and biomedical literature mining. Convolutional neural networks (CNNs) remain the foundational baseline for local feature extraction in X-ray and CT scans (paper_001), while vision transformer architectures (paper_002) offer expanded receptive fields for complex anomalies at the cost of elevated compute demand.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              2. Multi-Modal Neuroimaging Evidence
            </h3>
            <p>
              In brain tumour detection (paper_003), fusing multi-parametric magnetic resonance sequences (T1, T2, FLAIR) yields superior segmentation accuracy over single-sequence approaches. However, clinical translation remains gated by dataset scarcity and high intra-scanner variability across clinical sites.
            </p>
          </section>

          <section>
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '6px' }}>
              3. Retrieval Engine Validation
            </h3>
            <p>
              Evaluation of the RAG engine on this corpus demonstrates that <strong>Hybrid Retrieval (Dense Semantic + BM25 Sparse with RRF)</strong> consistently outscores standalone semantic and keyword retrievers on high-specificity medical prompts, achieving high Precision@3 and reciprocal rank benchmarks.
            </p>
          </section>
        </div>
      </div>
    </div>
  );
}
