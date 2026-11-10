import React, { useState } from 'react';
import { Search, Sparkles, Copy, Check, Clock, Anchor, Layers, ArrowRight } from 'lucide-react';
import { recallMemory } from '../services/api';

const SAMPLE_QUERIES = [
  "What database does the backend rely on and who authored the spec?",
  "What are the user's primary framework preferences?",
  "Where are the servers and services hosted?",
];

export default function AssociativeRecallSimulator({ sessionId, onHighlightNodes, onSelectEntity }) {
  const [queryText, setQueryText] = useState(SAMPLE_QUERIES[0]);
  const [maxHops, setMaxHops] = useState(2);
  const [loading, setLoading] = useState(false);
  const [recallResult, setRecallResult] = useState(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  const handleRecall = async (textToRun) => {
    const query = textToRun || queryText;
    if (!query.trim()) return;

    try {
      setLoading(true);
      setError(null);
      const res = await recallMemory(sessionId, query, maxHops);
      setRecallResult(res);

      if (res?.subgraph?.nodes && onHighlightNodes) {
        const names = res.subgraph.nodes.map(n => n.name);
        onHighlightNodes(names);
      }
    } catch (err) {
      setError(err.message || 'Recall failed');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyContext = () => {
    if (recallResult?.assembled_context) {
      navigator.clipboard.writeText(recallResult.assembled_context);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', height: '100%' }}>
      {/* Left Input & Control Panel */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.2)', padding: '8px', borderRadius: '8px' }}>
            <Sparkles size={18} color="#818cf8" />
          </div>
          <div>
            <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
              Associative Recall Simulator
            </h2>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Test multi-hop retrieval and context assembly for agent prompts
            </p>
          </div>
        </div>

        {/* Quick Sample Prompts */}
        <div>
          <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Quick Prompts
          </span>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px' }}>
            {SAMPLE_QUERIES.map((sq, i) => (
              <button
                key={i}
                onClick={() => {
                  setQueryText(sq);
                  handleRecall(sq);
                }}
                style={{
                  textAlign: 'left',
                  background: 'rgba(30, 41, 59, 0.4)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '6px',
                  padding: '7px 10px',
                  fontSize: '0.78rem',
                  color: '#cbd5e1',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}
              >
                <span>{sq}</span>
                <ArrowRight size={12} color="#6366f1" />
              </button>
            ))}
          </div>
        </div>

        {/* Input Box */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600 }}>
            Query Prompt
          </label>
          <textarea
            rows={4}
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            placeholder="Ask a question or enter context query..."
            style={{
              width: '100%',
              background: 'rgba(15, 23, 42, 0.8)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '8px',
              padding: '10px 12px',
              color: '#f8fafc',
              fontSize: '0.85rem',
              outline: 'none',
              resize: 'none',
              fontFamily: 'var(--font-sans)',
            }}
          />
        </div>

        {/* Controls: Hops & Button */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Max Hops:</span>
            {[1, 2, 3].map(h => (
              <button
                key={h}
                onClick={() => setMaxHops(h)}
                style={{
                  padding: '4px 10px',
                  borderRadius: '5px',
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  background: maxHops === h ? '#6366f1' : 'rgba(30, 41, 59, 0.6)',
                  color: maxHops === h ? '#ffffff' : '#94a3b8',
                }}
              >
                {h} {h === 1 ? 'Hop' : 'Hops'}
              </button>
            ))}
          </div>

          <button
            onClick={() => handleRecall()}
            disabled={loading || !queryText.trim()}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              border: 'none',
              padding: '8px 18px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
              boxShadow: '0 0 12px rgba(99, 102, 241, 0.35)'
            }}
          >
            <Search size={14} />
            {loading ? 'Traversing...' : 'Execute Recall'}
          </button>
        </div>

        {error && (
          <div style={{ padding: '8px 12px', borderRadius: '6px', background: 'rgba(239, 68, 68, 0.15)', color: '#f87171', fontSize: '0.75rem' }}>
            {error}
          </div>
        )}
      </div>

      {/* Right Result & Assembled Context */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc' }}>
              Assembled Prompt Context
            </span>
            {recallResult && (
              <span className="badge badge-tool" style={{ fontSize: '0.65rem' }}>
                <Clock size={10} style={{ marginRight: '3px' }} />
                {recallResult.execution_time_ms} ms
              </span>
            )}
          </div>

          {recallResult && (
            <button
              onClick={handleCopyContext}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '5px',
                background: 'rgba(30, 41, 59, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '5px 10px',
                color: copied ? '#34d399' : '#94a3b8',
                fontSize: '0.75rem',
                cursor: 'pointer',
              }}
            >
              {copied ? <Check size={12} /> : <Copy size={12} />}
              {copied ? 'Copied!' : 'Copy Context'}
            </button>
          )}
        </div>

        {/* Anchors and Facts summary pills */}
        {recallResult && (
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {recallResult.matched_entities?.map((anchor, i) => (
              <span key={i} className="badge badge-concept" style={{ fontSize: '0.7rem' }}>
                <Anchor size={10} style={{ marginRight: '4px' }} />
                Anchor: {anchor}
              </span>
            ))}
            <span className="badge badge-tool" style={{ fontSize: '0.7rem' }}>
              <Layers size={10} style={{ marginRight: '4px' }} />
              {recallResult.recalled_facts?.length || 0} Associative Facts
            </span>
          </div>
        )}

        {/* Code / Markdown Box */}
        <div style={{
          flex: 1,
          background: 'rgba(7, 9, 14, 0.9)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '8px',
          padding: '14px',
          overflowY: 'auto',
          fontSize: '0.8rem',
          lineHeight: '1.5',
          color: '#cbd5e1',
          fontFamily: 'var(--font-mono)',
          whiteSpace: 'pre-wrap'
        }}>
          {recallResult ? (
            recallResult.assembled_context
          ) : (
            <span style={{ color: '#475569' }}>
              Run a recall query to inspect multi-hop graph expansion and prompt-ready memory context.
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

