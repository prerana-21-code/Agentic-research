import React from 'react';

export default function ResearchGapsView() {
  const gaps = [
    {
      id: 'gap-001',
      category: 'Cross-Modal Generalization',
      title: 'Lack of Unified Multimodal Benchmarking Across MRI and CT Scans',
      description:
        'While paper_001 focuses on 2D X-ray classification and paper_003 assesses 3D FLAIR MRI, there is no unified transfer learning framework demonstrated that generalizes across scanner manufacturer variance.',
      impact: 'High',
      suggestedExploration: 'Evaluate cross-modality domain adaptation models with adversarial loss.',
    },
    {
      id: 'gap-002',
      category: 'Computational Efficiency',
      title: 'High FLOP Overhead in Biomedical Vision Transformers',
      description:
        'Paper_002 shows superior patch-level representation with ViTs, but memory constraints hinder deployment on bedside clinical workstation hardware.',
      impact: 'Medium',
      suggestedExploration: 'Investigate knowledge distillation from ViT teacher models into lightweight CNN student backbones.',
    },
    {
      id: 'gap-003',
      category: 'Clinical Explainability',
      title: 'Black-Box Decision Boundaries in Longitudinal Survival Prediction',
      description:
        'Paper_004 demonstrates high AUC-ROC for disease prediction, but lacks local feature attribution (SHAP/LIME) required for clinician adoption.',
      impact: 'Critical',
      suggestedExploration: 'Integrate interpretable tree ensembles with physician-in-the-loop audit dashboards.',
    },
  ];

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Research Gaps & Unaddressed Questions
            </h1>
            <span className="badge badge-demo">Simulated AI Gaps</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Synthesized literature gaps identified across the current 5-paper corpus.
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {gaps.map((gap) => (
          <div key={gap.id} className="card card-interactive" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span className="badge badge-indigo">{gap.category}</span>
                <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 5px' }}>
                  SAMPLE GAP
                </span>
              </div>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: '600',
                  padding: '2px 8px',
                  borderRadius: '999px',
                  background: gap.impact === 'Critical' ? 'rgba(244, 63, 94, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                  color: gap.impact === 'Critical' ? '#fb7185' : '#fbbf24',
                  border: '1px solid',
                  borderColor: gap.impact === 'Critical' ? 'rgba(244, 63, 94, 0.3)' : 'rgba(245, 158, 11, 0.3)',
                }}
              >
                Impact: {gap.impact}
              </span>
            </div>

            <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '8px' }}>
              {gap.title}
            </h3>

            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '14px' }}>
              {gap.description}
            </p>

            <div
              style={{
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                fontSize: '12px',
                color: 'var(--text-accent)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <span style={{ fontWeight: '600', color: 'var(--accent-cyan)' }}>Proposed Hypothesis:</span>
              <span>{gap.suggestedExploration}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
