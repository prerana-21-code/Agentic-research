import React, { useState, useEffect } from 'react';
import { MOCK_RECENT_ACTIVITIES } from '../../mock/mockData';

export default function HybridRagView({ activeQuery: propQuery }) {
  const [query, setQuery] = useState(
    propQuery || 'How are CNNs used to detect diseases in MRI images?'
  );
  const [results, setResults] = useState(MOCK_RECENT_ACTIVITIES);
  const [loading, setLoading] = useState(false);
  const [isLive, setIsLive] = useState(false);
  const [selectedChunkMeta, setSelectedChunkMeta] = useState(null);
  const [autoDiscover, setAutoDiscover] = useState(true);
  const [maxPapers, setMaxPapers] = useState(2);
  const [workflowSteps, setWorkflowSteps] = useState([]);
  const [discoveredPapers, setDiscoveredPapers] = useState([]);
  const [workflowStats, setWorkflowStats] = useState(null);

  const fetchSearchResults = async (searchQuery) => {
    if (!searchQuery || !searchQuery.trim()) return;
    setLoading(true);
    setWorkflowSteps([
      'Initiating on-demand research pipeline...',
      'Checking existing ChromaDB collection for previously indexed papers...',
    ]);

    try {
      const endpoint = autoDiscover ? '/api/research' : '/api/search';
      const payload = autoDiscover
        ? {
            query: searchQuery.trim(),
            max_papers: maxPapers,
            mode: 'hybrid',
            top_k: 5,
          }
        : {
            query: searchQuery.trim(),
            mode: 'hybrid',
            top_k: 5,
          };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }

      const data = await response.json();
      const rawResults = data.results || [];

      if (rawResults.length > 0) {
        const mapped = rawResults.map((r, idx) => ({
          id: r.chunk_id || `res-${idx}`,
          topChunkId: r.chunk_id,
          topChunkSnippet: r.text,
          mockRrfScore: r.score,
          scoreType: r.score_type,
          matchedPapers: [r.paper_title ? `${r.paper_title} (${r.paper_id})` : r.paper_id],
          paperId: r.paper_id,
          paperTitle: r.paper_title,
          pageNumber: r.page_number,
          section: r.section,
          chunkType: r.chunk_type,
          dimension: r.dimension,
          provenance: r.provenance,
          sourceType: r.source_type,
          confidence: r.confidence,
          evidence: r.metadata?.evidence || r.evidence || '',
          metadata: r.metadata || {},
          isLive: true,
        }));
        setResults(mapped);
      } else {
        setResults([]);
      }

      setWorkflowSteps(data.execution_steps || ['Retrieved ranked passages successfully']);
      setDiscoveredPapers(data.discovered_papers || []);
      if (data.total_discovered !== undefined) {
        setWorkflowStats({
          totalDiscovered: data.total_discovered,
          newlyIndexed: data.newly_indexed_count,
          reused: data.reused_count,
        });
      }
      setIsLive(true);
    } catch (err) {
      console.warn('Backend research API unavailable, showing simulation:', err);
      setIsLive(false);
      setResults(MOCK_RECENT_ACTIVITIES);
      setWorkflowSteps(['Backend unavailable. Showing baseline simulation data.']);
      setDiscoveredPapers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (propQuery) {
      setQuery(propQuery);
      fetchSearchResults(propQuery);
    } else {
      fetchSearchResults(query);
    }
  }, [propQuery]);

  return (
    <div className="fade-in">
      {/* View Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <h1 style={{ fontSize: '22px', fontWeight: '700', color: 'var(--text-primary)' }}>
              On-Demand Research & Hybrid RAG
            </h1>
            <span className="badge badge-indigo">End-to-End Pipeline</span>
            <span className={`badge ${isLive ? 'badge-connected' : 'badge-disconnected'}`}>
              {isLive ? 'Live System Active' : 'Simulated Baseline'}
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
            Enter any research question. The assistant automatically queries OpenAlex, retrieves open-access PDFs, extracts text via PyMuPDF, executes NLP analysis, indexes into ChromaDB & BM25, and computes Reciprocal Rank Fusion (RRF).
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span className="badge badge-cyan">RRF k=60</span>
          {isLive && (
            <span className="badge badge-connected">
              OpenAlex + ChromaDB + BM25
            </span>
          )}
        </div>
      </div>

      {/* Query Bar & Controls */}
      <div
        className="card"
        style={{
          marginBottom: '20px',
          padding: '18px 20px',
          background: 'var(--bg-surface)',
          border: '1px solid var(--border-subtle)',
        }}
      >
        <form
          onSubmit={(e) => {
            e.preventDefault();
            fetchSearchResults(query);
          }}
        >
          <div style={{ display: 'flex', gap: '10px', marginBottom: '14px', flexWrap: 'wrap' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter a research question (e.g., 'How do graph neural networks predict molecular properties?')..."
              style={{
                flex: 1,
                minWidth: '280px',
                padding: '12px 16px',
                fontSize: '13px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--bg-input)',
                border: '1px solid var(--border-medium)',
                color: 'var(--text-primary)',
                outline: 'none',
              }}
            />
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ minWidth: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
            >
              {loading ? (
                <>
                  <span className="indicator-dot connected" style={{ width: '8px', height: '8px' }} />
                  Processing Pipeline...
                </>
              ) : (
                'Run Research Assistant'
              )}
            </button>
          </div>

          {/* Workflow Toggle & Options */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={autoDiscover}
                  onChange={(e) => setAutoDiscover(e.target.checked)}
                  style={{ accentColor: 'var(--primary-500)', cursor: 'pointer' }}
                />
                <span style={{ fontWeight: '500', color: autoDiscover ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                  Auto-Discover & Ingest Papers (Member 1 OpenAlex + PDF + NLP)
                </span>
              </label>

              {autoDiscover && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span>Max Papers:</span>
                  <select
                    value={maxPapers}
                    onChange={(e) => setMaxPapers(Number(e.target.value))}
                    style={{
                      background: 'var(--bg-surface-elevated)',
                      border: '1px solid var(--border-medium)',
                      color: 'var(--text-primary)',
                      borderRadius: 'var(--radius-sm)',
                      padding: '2px 8px',
                      fontSize: '12px',
                    }}
                  >
                    <option value={1}>1 paper</option>
                    <option value={2}>2 papers</option>
                    <option value={3}>3 papers</option>
                    <option value={5}>5 papers</option>
                  </select>
                </div>
              )}
            </div>

            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              {autoDiscover ? 'Full On-Demand Workflow Active' : 'Direct Search (Current ChromaDB & BM25 only)'}
            </span>
          </div>
        </form>
      </div>

      {/* Processing Indicator / Workflow Progress */}
      {loading && (
        <div
          className="card"
          style={{
            marginBottom: '20px',
            padding: '20px',
            background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%)',
            border: '1px solid rgba(99, 102, 241, 0.3)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '12px' }}>
            <span className="indicator-dot connected" style={{ width: '10px', height: '10px' }} />
            <h3 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>
              Executing Autonomous Research Pipeline...
            </h3>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
            <div style={{ color: 'var(--accent-cyan)' }}>• Searching OpenAlex for peer-reviewed literature</div>
            <div>• Identifying verified open-access PDFs (respecting paywalls)</div>
            <div>• Extracting page-level text via PyMuPDF</div>
            <div>• Extracting research dimensions via NLPResearchAnalyzer (objectives, methods, metrics)</div>
            <div>• Ingesting page-aware facts into ChromaDB vector store</div>
            <div>• Synchronizing in-memory BM25 Okapi keyword index</div>
            <div>• Computing Reciprocal Rank Fusion scores across dense & sparse rankings</div>
          </div>
        </div>
      )}

      {/* Discovered Papers Summary Card */}
      {discoveredPapers.length > 0 && (
        <div
          className="card"
          style={{
            marginBottom: '20px',
            padding: '18px 20px',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid rgba(6, 182, 212, 0.25)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h3 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--text-primary)' }}>
                Academic Papers Processed for this Question
              </h3>
              <span className="badge badge-cyan">{discoveredPapers.length} Papers</span>
              {workflowStats && (
                <span className="badge badge-connected">
                  {workflowStats.newlyIndexed} Newly Ingested • {workflowStats.reused} Reused
                </span>
              )}
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Member 1 Processing + Member 2 Indexing
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {discoveredPapers.map((p) => {
              const isNewlyIndexed = p.action === 'newly_indexed';
              const isFullText = p.source_type === 'open_access_full_text';
              return (
                <div
                  key={p.paper_id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--bg-surface)',
                    border: '1px solid var(--border-subtle)',
                    flexWrap: 'wrap',
                    gap: '10px',
                  }}
                >
                  <div style={{ flex: 1, minWidth: '240px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '2px' }}>
                      <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-primary)' }}>
                        {p.title}
                      </span>
                      {p.year && (
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                          ({p.year})
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      {p.authors && p.authors.length > 0 ? p.authors.slice(0, 3).join(', ') : 'Authors listed'}
                      {p.authors && p.authors.length > 3 ? ` et al.` : ''}
                      {' • ID: '}{p.paper_id}
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                    <span className={`badge ${isNewlyIndexed ? 'badge-connected' : 'badge-indigo'}`} style={{ fontSize: '10px' }}>
                      {isNewlyIndexed ? 'Newly Indexed' : 'Previously Indexed'}
                    </span>
                    <span className={`badge ${isFullText ? 'badge-cyan' : 'badge-demo'}`} style={{ fontSize: '10px' }}>
                      {isFullText ? `Full-Text (${p.total_pages}p)` : 'Abstract Only'}
                    </span>
                    {p.chunks_count > 0 && (
                      <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        +{p.chunks_count} chunks
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Metadata Modal / Inspector Popup */}
      {selectedChunkMeta && (
        <div
          className="card"
          style={{
            marginBottom: '20px',
            padding: '18px 22px',
            background: 'var(--bg-surface-elevated)',
            border: '1px solid var(--border-glow)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--accent-cyan)' }}>
              Passage Provenance & NLP Evidence: {selectedChunkMeta.topChunkId}
            </h4>
            <button
              className="btn btn-ghost"
              style={{ fontSize: '11px', padding: '2px 8px' }}
              onClick={() => setSelectedChunkMeta(null)}
            >
              Close
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '10px', fontSize: '12px', marginBottom: '12px' }}>
            <div><strong>Paper ID:</strong> {selectedChunkMeta.paperId || 'N/A'}</div>
            <div><strong>Paper Title:</strong> {selectedChunkMeta.paperTitle || 'N/A'}</div>
            <div><strong>Section:</strong> {selectedChunkMeta.section || 'FULL_TEXT'}</div>
            <div><strong>Page Number:</strong> {selectedChunkMeta.pageNumber !== null && selectedChunkMeta.pageNumber !== undefined ? selectedChunkMeta.pageNumber : 'Abstract'}</div>
            <div><strong>Chunk Type:</strong> {selectedChunkMeta.chunkType || 'body_passage'}</div>
            <div><strong>Dimension:</strong> {selectedChunkMeta.dimension || 'body'}</div>
            <div><strong>Source Type:</strong> {selectedChunkMeta.sourceType || 'open_access'}</div>
            <div><strong>Provenance:</strong> {selectedChunkMeta.provenance || 'N/A'}</div>
            <div><strong>Confidence:</strong> {selectedChunkMeta.confidence || 1.0}</div>
          </div>
          {selectedChunkMeta.evidence && (
            <div style={{ background: 'var(--bg-surface)', padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
              <strong style={{ color: 'var(--accent-cyan)' }}>Supporting Evidence Sentence:</strong>
              <div style={{ marginTop: '4px', fontStyle: 'italic', color: 'var(--text-secondary)' }}>
                "{selectedChunkMeta.evidence}"
              </div>
            </div>
          )}
        </div>
      )}

      {/* Ranked Retrieved Results List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Ranked Passages ({results.length})
          </h2>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Ordered by Reciprocal Rank Fusion Score
          </span>
        </div>

        {results.length === 0 && !loading && (
          <div className="card" style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
            No matching passages found for query "{query}".
          </div>
        )}

        {results.map((item, idx) => (
          <div key={item.id} className="card card-interactive" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px', flexWrap: 'wrap', gap: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
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

                {item.isLive ? (
                  <span className="badge badge-connected" style={{ fontSize: '9px', padding: '1px 6px' }}>
                    LIVE RRF RESULT
                  </span>
                ) : (
                  <span className="badge badge-demo" style={{ fontSize: '9px', padding: '1px 6px' }}>
                    SIMULATED RESULT
                  </span>
                )}

                {item.section && (
                  <span className="badge badge-indigo" style={{ fontSize: '9px', padding: '1px 6px' }}>
                    {item.section}
                  </span>
                )}

                {item.pageNumber !== undefined && (
                  <span className="badge badge-cyan" style={{ fontSize: '9px', padding: '1px 6px' }}>
                    {item.pageNumber !== null && item.pageNumber > 0 ? `Page ${item.pageNumber}` : 'Abstract'}
                  </span>
                )}

                {item.chunkType && item.chunkType !== 'body_passage' && (
                  <span className="badge badge-cyan" style={{ fontSize: '9px', padding: '1px 6px' }}>
                    {item.chunkType}
                  </span>
                )}
              </div>

              {/* RRF Score Badges */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div
                  style={{
                    padding: '4px 10px',
                    borderRadius: 'var(--radius-sm)',
                    background: item.isLive ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                    border: item.isLive ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                    fontSize: '12px',
                    fontFamily: 'monospace',
                    color: item.isLive ? '#34d399' : '#fbbf24',
                  }}
                >
                  RRF Score: <strong>{typeof item.mockRrfScore === 'number' ? item.mockRrfScore.toFixed(6) : item.mockRrfScore}</strong>
                </div>
              </div>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-primary)', lineHeight: '1.6', marginBottom: '12px', background: 'var(--bg-surface-elevated)', padding: '12px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
              "{item.topChunkSnippet}"
            </p>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--text-muted)', flexWrap: 'wrap', gap: '8px' }}>
              <div>
                Paper: <strong style={{ color: 'var(--text-secondary)' }}>{item.matchedPapers.join(', ')}</strong>
              </div>
              <div style={{ display: 'flex', gap: '10px' }}>
                <button
                  className="btn btn-ghost"
                  style={{ fontSize: '11px', padding: '2px 8px' }}
                  onClick={() => setSelectedChunkMeta(item)}
                >
                  Inspect Evidence & Provenance
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
