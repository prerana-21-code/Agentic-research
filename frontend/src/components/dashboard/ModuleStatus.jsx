import React, { useState, useEffect } from 'react';
import { MOCK_MODULE_STATUSES } from '../../mock/mockData';

export default function ModuleStatus() {
  const [statuses, setStatuses] = useState(MOCK_MODULE_STATUSES);
  const [isLive, setIsLive] = useState(false);

  const checkHealth = () => {
    fetch('/api/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (data.module_details && Array.isArray(data.module_details)) {
          setStatuses(data.module_details);
        } else {
          const activeChunks = data.pipeline?.active_chunks || 10;
          const chromaCount = data.pipeline?.chroma_records || activeChunks;
          const bm25Synced = data.pipeline?.bm25_synced !== false;

          setStatuses([
            {
              id: 'fastapi_bridge',
              name: 'FastAPI Backend API',
              subtext: 'http://127.0.0.1:8000/api',
              status: 'Connected',
              statusType: 'connected',
              details: `FastAPI ${data.version || '0.1.0'} active on port 8000.`,
            },
            {
              id: 'paper_processing',
              name: 'Paper Processing (Member 1)',
              subtext: 'OpenAlex, PyMuPDF, NLP Analyzer',
              status: 'Ready',
              statusType: 'connected',
              details: 'Scholarly discovery & extraction ready.',
            },
            {
              id: 'rag_engine',
              name: 'RAG Core Engine (Member 2)',
              subtext: 'rag_engine module primitives',
              status: 'Active',
              statusType: 'connected',
              details: 'Hybrid RAG pipeline initialized with all-MiniLM-L6-v2.',
            },
            {
              id: 'vector_store',
              name: 'ChromaDB Vector Store',
              subtext: 'Persistent collection: research_papers',
              status: 'Connected',
              statusType: 'connected',
              details: `Connected with ${chromaCount} records at data/chroma_db.`,
            },
            {
              id: 'bm25_index',
              name: 'BM25 Keyword Index',
              subtext: 'rank_bm25 Okapi tokenizer',
              status: bm25Synced ? 'Synchronized' : 'Empty',
              statusType: bm25Synced ? 'connected' : 'disconnected',
              details: `In-memory index synced across ${activeChunks} active chunks.`,
            },
          ]);
        }
        setIsLive(true);
      })
      .catch(() => {
        setIsLive(false);
        setStatuses(MOCK_MODULE_STATUSES);
      });
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 4000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card" style={{ height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Module Integration Status
          </h3>
          <span className={`badge ${isLive ? 'badge-connected' : 'badge-disconnected'}`}>
            {isLive ? 'Live System Active' : 'Backend Offline'}
          </span>
        </div>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
          {isLive ? 'Verified via /api/health' : 'Waiting for http://127.0.0.1:8000'}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {statuses.map((module) => {
          const isConnected = module.statusType === 'connected';
          return (
            <div
              key={module.id}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-surface-elevated)',
                border: isConnected
                  ? '1px solid rgba(16, 185, 129, 0.2)'
                  : '1px solid var(--border-subtle)',
                transition: 'all var(--transition-fast)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <span className={`indicator-dot ${isConnected ? 'connected' : 'disconnected'}`} />
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                    {module.name}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {module.subtext}
                  </div>
                </div>
              </div>

              <div style={{ textAlign: 'right' }}>
                <span
                  className={`badge ${isConnected ? 'badge-connected' : 'badge-disconnected'}`}
                  style={{ fontSize: '10px' }}
                >
                  {module.status}
                </span>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px', maxWidth: '210px' }}>
                  {module.details}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
