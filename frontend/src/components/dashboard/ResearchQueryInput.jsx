import React, { useState } from 'react';
import { MOCK_SUGGESTED_QUERIES } from '../../mock/mockData';

export default function ResearchQueryInput({ onSearchSubmit, initialQuery = '' }) {
  const [query, setQuery] = useState(initialQuery);
  const [searchMode, setSearchMode] = useState('hybrid'); // 'hybrid' | 'semantic' | 'bm25'
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    if (onSearchSubmit) {
      onSearchSubmit(query, searchMode);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    if (onSearchSubmit) {
      onSearchSubmit(suggestion, searchMode);
    }
  };

  return (
    <div
      className="card fade-in"
      style={{
        marginBottom: '24px',
        padding: '24px',
        background: 'var(--bg-surface)',
        border: isFocused ? '1px solid var(--border-glow)' : '1px solid var(--border-subtle)',
        boxShadow: isFocused ? 'var(--shadow-glow)' : 'var(--shadow-sm)',
        transition: 'all var(--transition-normal)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ fontSize: '15px', fontWeight: '600', color: 'var(--text-primary)' }}>
            Ask a Research Question
          </h2>
          <span className="badge badge-indigo">Multi-Paper RAG</span>
        </div>

        {/* Search Mode Toggles */}
        <div
          style={{
            display: 'flex',
            background: 'var(--bg-surface-elevated)',
            padding: '3px',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-medium)',
            gap: '2px',
          }}
        >
          {[
            { id: 'hybrid', label: 'Hybrid RAG (RRF)', badge: 'Recommended' },
            { id: 'semantic', label: 'Semantic (ChromaDB)', badge: null },
            { id: 'bm25', label: 'BM25 Keyword', badge: null },
          ].map((mode) => {
            const isSelected = searchMode === mode.id;
            return (
              <button
                key={mode.id}
                type="button"
                onClick={() => setSearchMode(mode.id)}
                style={{
                  background: isSelected ? 'var(--primary-600)' : 'transparent',
                  color: isSelected ? '#ffffff' : 'var(--text-secondary)',
                  border: 'none',
                  padding: '5px 12px',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '12px',
                  fontWeight: isSelected ? '600' : '500',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  transition: 'all var(--transition-fast)',
                }}
              >
                {mode.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Main Query Bar */}
      <form onSubmit={handleSubmit} style={{ position: 'relative', marginBottom: '14px' }}>
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <span
            style={{
              position: 'absolute',
              left: '16px',
              color: isFocused ? 'var(--primary-400)' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              pointerEvents: 'none',
              transition: 'color var(--transition-fast)',
            }}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </span>

          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="e.g. How are CNNs used to detect diseases in MRI images? Or analyze biomedical papers..."
            style={{
              width: '100%',
              padding: '14px 140px 14px 48px',
              fontSize: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--bg-input)',
              border: '1px solid var(--border-medium)',
              color: 'var(--text-primary)',
              outline: 'none',
              transition: 'border-color var(--transition-fast)',
            }}
          />

          <button
            type="submit"
            className="btn btn-primary"
            style={{
              position: 'absolute',
              right: '6px',
              padding: '8px 18px',
              fontSize: '13px',
            }}
          >
            <span>Search</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="5" y1="12" x2="19" y2="12"/>
              <polyline points="12 5 19 12 12 19"/>
            </svg>
          </button>
        </div>
      </form>

      {/* Suggestion Chips */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
            Sample Questions:
          </span>
          {MOCK_SUGGESTED_QUERIES.slice(0, 3).map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSuggestionClick(item)}
              style={{
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '999px',
                padding: '4px 12px',
                fontSize: '12px',
                color: 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all var(--transition-fast)',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-glow)';
                e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-subtle)';
                e.currentTarget.style.color = 'var(--text-secondary)';
              }}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
