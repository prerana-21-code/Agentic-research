/**
 * =========================================================================
 * MOCK / DEMO DATA STORE
 * =========================================================================
 * IMPORTANT:
 * All entries in this file represent synthetic demo data for initial UI layout
 * and testing. Real research data, actual retrieval queries, and verified metrics
 * will be populated dynamically once the FastAPI backend is integrated.
 * =========================================================================
 */

export const MOCK_CORPUS_STATS = {
  isMockData: true,
  dataSourceLabel: 'Sample Corpus (Demo Data)',
  totalPapers: 5,
  indexedChunks: 11,
  embeddingDimension: 384,
  embeddingModel: 'all-MiniLM-L6-v2',
  fusionStrategy: 'Reciprocal Rank Fusion (k=60)',
  lastIndexed: 'Sample Baseline (pre-loaded)',
};

export const MOCK_MODULE_STATUSES = [
  {
    id: 'fastapi_bridge',
    name: 'FastAPI Backend API',
    subtext: 'http://127.0.0.1:8000/api',
    status: 'Not Connected',
    statusType: 'disconnected',
    details: 'Backend service offline or awaiting initialization.',
  },
  {
    id: 'paper_processing',
    name: 'Paper Processing (Member 1)',
    subtext: 'OpenAlex, PyMuPDF, NLP Analyzer',
    status: 'Awaiting Backend',
    statusType: 'disconnected',
    details: 'Requires live FastAPI service on port 8000.',
  },
  {
    id: 'rag_engine',
    name: 'RAG Core Engine (Member 2)',
    subtext: 'rag_engine module primitives',
    status: 'Awaiting Backend',
    statusType: 'disconnected',
    details: 'Requires live FastAPI service on port 8000.',
  },
  {
    id: 'vector_store',
    name: 'ChromaDB Vector Store',
    subtext: 'Persistent collection: research_papers',
    status: 'Awaiting Backend',
    statusType: 'disconnected',
    details: 'Requires live FastAPI service on port 8000.',
  },
  {
    id: 'bm25_index',
    name: 'BM25 Keyword Index',
    subtext: 'rank_bm25 Okapi tokenizer',
    status: 'Awaiting Backend',
    statusType: 'disconnected',
    details: 'Requires live FastAPI service on port 8000.',
  },
];

export const MOCK_RECENT_ACTIVITIES = [
  {
    id: 'act-001',
    isMock: true,
    query: 'How are CNNs used to detect diseases in MRI images?',
    timestamp: '10 mins ago (Mock)',
    searchMode: 'Hybrid RAG',
    matchedPapers: ['paper_001', 'paper_003'],
    topChunkId: 'paper_001_chunk_1',
    topChunkSnippet:
      'Convolutional Neural Networks (CNNs) are widely used for analysing X-ray images, MRI scans, and CT scans. CNN models learn visual features from medical images...',
    mockRrfScore: 0.032258,
    status: 'Sample Result',
  },
  {
    id: 'act-002',
    isMock: true,
    query: 'How do Vision Transformers analyse medical images?',
    timestamp: '42 mins ago (Mock)',
    searchMode: 'Hybrid RAG',
    matchedPapers: ['paper_002'],
    topChunkId: 'paper_002_chunk_1',
    topChunkSnippet:
      'Vision Transformers (ViTs) apply self-attention mechanisms to image patches for biomedical anomaly segmentation and classification...',
    mockRrfScore: 0.031746,
    status: 'Sample Result',
  },
  {
    id: 'act-003',
    isMock: true,
    query: 'What techniques are used for brain tumour detection?',
    timestamp: '2 hours ago (Mock)',
    searchMode: 'Semantic Search',
    matchedPapers: ['paper_003'],
    topChunkId: 'paper_003_chunk_1',
    topChunkSnippet:
      'Multimodal MRI analysis integrates T1-weighted, T2-weighted, and FLAIR sequences with automated deep segmentation networks...',
    mockRrfScore: 0.031250,
    status: 'Sample Result',
  },
  {
    id: 'act-004',
    isMock: true,
    query: 'Which machine learning algorithms predict disease risk?',
    timestamp: 'Yesterday (Mock)',
    searchMode: 'BM25 Keyword',
    matchedPapers: ['paper_004'],
    topChunkId: 'paper_004_chunk_1',
    topChunkSnippet:
      'Predictive clinical modeling commonly utilizes gradient boosted trees, logistic regression, and ensemble classifiers trained on patient electronic health records...',
    mockRrfScore: 0.029851,
    status: 'Sample Result',
  },
];

export const MOCK_SAMPLE_PAPERS = [
  {
    paperId: 'paper_001',
    title: 'Deep Learning Techniques for Medical Image Classification',
    category: 'Computer Vision & Healthcare',
    chunksCount: 2,
    abstract:
      'Medical image classification is an important application of artificial intelligence in healthcare. Deep learning techniques can automatically identify patterns in medical images and support disease diagnosis.',
  },
  {
    paperId: 'paper_002',
    title: 'Vision Transformers in Biomedical Signal Processing',
    category: 'Transformer Architectures',
    chunksCount: 2,
    abstract:
      'Exploration of self-attention architectures replacing standard convolutional operators for multi-resolution diagnostic imagery.',
  },
  {
    paperId: 'paper_003',
    title: 'Automated Brain Tumour Segmentation Using Multimodal MRI',
    category: 'Neuroimaging & AI',
    chunksCount: 2,
    abstract:
      'Comparative benchmarking of deep segmentation models applied to FLAIR and T1 contrast-enhanced magnetic resonance scans.',
  },
  {
    paperId: 'paper_004',
    title: 'Predictive Disease Risk Stratification via Machine Learning',
    category: 'Clinical Informatics',
    chunksCount: 2,
    abstract:
      'Utilizing gradient boosting and survival analysis to predict 5-year patient outcomes across longitudinal cohorts.',
  },
  {
    paperId: 'paper_005',
    title: 'Natural Language Processing for Biomedical Literature Mining',
    category: 'BioNLP',
    chunksCount: 3,
    abstract:
      'Information extraction and knowledge graph construction from unstructured biomedical research publications.',
  },
];

export const MOCK_SUGGESTED_QUERIES = [
  'How are CNNs used to detect diseases in MRI images?',
  'How do Vision Transformers analyse medical images?',
  'What techniques are used for brain tumour detection?',
  'Which machine learning algorithms predict disease risk?',
  'How is NLP used to analyse biomedical research papers?',
];
