import React from 'react';
import { MOCK_SAMPLE_PAPERS } from '../../mock/mockData';

export default function PaperComparisonView() {
  const comparisonRows = [
    {
      paperId: 'paper_001',
      title: 'Deep Learning Techniques for Medical Image Classification',
      architecture: 'Convolutional Neural Networks (CNN)',
      modalities: 'X-Ray, MRI, CT scans',
      keyMetric: 'Disease classification accuracy',
      limitation: 'Limited labelled datasets & interpretability',
    },
    {
      paperId: 'paper_002',
      title: 'Vision Transformers in Biomedical Signal Processing',
      architecture: 'Self-Attention Vision Transformers (ViT)',
      modalities: 'Multispectral diagnostic imagery',
      keyMetric: 'Global patch attention & feature retention',
      limitation: 'High computational overhead & training latency',
    },
    {
      paperId: 'paper_003',
      title: 'Automated Brain Tumour Segmentation Using Multimodal MRI',
      architecture: 'Multimodal Deep Segmentation',
      modalities: 'T1, T2, and FLAIR MRI sequences',
      keyMetric: 'Dice similarity coefficient for tumour boundaries',
      limitation: 'Sensitivity to scan artifact variations across hospitals',
    },
    {
      paperId: 'paper_004',
      title: 'Predictive Disease Risk Stratification via Machine Learning',
      architecture: 'Gradient Boosted Trees & Survival Ensembles',
      modalities: 'Electronic Health Records (EHR)',
      keyMetric: 'Area Under ROC Curve (AUC-ROC)',
      limitation: 'Class imbalance and missing longitudinal patient observations',
    },
    {
      paperId: 'paper_005',
      title: 'Natural Language Processing for Biomedical Literature Mining',
      architecture: 'Transformer-based BioNLP',
      modalities: 'Unstructured PubMed texts & clinical trials',
      keyMetric: 'Named Entity Recognition (NER) F1 Score',
      limitation: 'Domain-specific medical acronyms and syntax ambiguity',
    },
  ];

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              Paper Comparison Matrix
            </h1>
            <span className="badge badge-demo">Demo Comparison Matrix</span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Side-by-side comparative analysis of architecture, modalities, and limitations across the sample corpus.
          </p>
        </div>
      </div>

      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
          <thead>
            <tr style={{ background: 'var(--bg-surface-elevated)', borderBottom: '1px solid var(--border-medium)' }}>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase' }}>Paper ID</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase' }}>Architecture</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase' }}>Data Modality</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase' }}>Key Benchmark</th>
              <th style={{ padding: '14px 16px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '11px', textTransform: 'uppercase' }}>Identified Bottleneck</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row) => (
              <tr
                key={row.paperId}
                style={{ borderBottom: '1px solid var(--border-subtle)', transition: 'background var(--transition-fast)' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-surface-hover)')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <td style={{ padding: '14px 16px' }}>
                  <code style={{ color: 'var(--accent-cyan)', fontWeight: '600' }}>{row.paperId}</code>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px', maxWidth: '220px' }}>
                    {row.title}
                  </div>
                </td>
                <td style={{ padding: '14px 16px', color: 'var(--text-primary)', fontWeight: '500' }}>
                  {row.architecture}
                </td>
                <td style={{ padding: '14px 16px', color: 'var(--text-secondary)' }}>
                  {row.modalities}
                </td>
                <td style={{ padding: '14px 16px', color: 'var(--text-accent)' }}>
                  {row.keyMetric}
                </td>
                <td style={{ padding: '14px 16px', color: '#fb7185', fontSize: '12px' }}>
                  {row.limitation}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
