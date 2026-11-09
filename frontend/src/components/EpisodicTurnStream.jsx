import React, { useState } from 'react';
import { Send, User, Bot, Wrench, Sparkles, Tag, Clock } from 'lucide-react';
import { ingestEpisode } from '../services/api';

const ROLE_ICONS = {
  user: <User size={14} color="#818cf8" />,
  agent: <Bot size={14} color="#34d399" />,
  tool: <Wrench size={14} color="#38bdf8" />,
};

export default function EpisodicTurnStream({ sessionId, episodes = [], onIngested }) {
  const [content, setContent] = useState('');
  const [role, setRole] = useState('user');
  const [tagsInput, setTagsInput] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;

    try {
      setSubmitting(true);
      const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean);
      await ingestEpisode(sessionId, content, role, tags);
      setContent('');
      setTagsInput('');
      if (onIngested) onIngested();
    } catch (err) {
      console.error('Failed to ingest episode:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '400px 1fr', gap: '20px', height: '100%' }}>
      {/* Turn Ingestion Cockpit */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
            Ingest Interaction Turn
          </h2>
          <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
            Turns are automatically parsed into entities and relation triplets
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
          {/* Role selector */}
          <div style={{ display: 'flex', gap: '6px' }}>
            {['user', 'agent', 'tool'].map(r => (
              <button
                key={r}
                type="button"
                onClick={() => setRole(r)}
                style={{
                  flex: 1,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                  padding: '6px',
                  borderRadius: '6px',
                  border: 'none',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  background: role === r ? 'rgba(99, 102, 241, 0.25)' : 'rgba(30, 41, 59, 0.6)',
                  color: role === r ? '#818cf8' : '#94a3b8',
                }}
              >
                {ROLE_ICONS[r]}
                {r}
              </button>
            ))}
          </div>

          {/* Turn Text */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Interaction Content</label>
            <textarea
              required
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="e.g. Alice works at Google. The system uses FastAPI and MongoDB for graph storage..."
              style={{
                flex: 1,
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '10px 12px',
                color: '#f8fafc',
                fontSize: '0.82rem',
                outline: 'none',
                resize: 'none',
                fontFamily: 'var(--font-sans)',
              }}
            />
          </div>

          {/* Tags */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Tags (comma-separated)</label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="architecture, tech-stack, preference"
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '8px 12px',
                color: '#f8fafc',
                fontSize: '0.8rem',
                outline: 'none',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={submitting || !content.trim()}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              background: 'linear-gradient(135deg, #6366f1, #4f46e5)',
              color: '#ffffff',
              border: 'none',
              padding: '10px',
              borderRadius: '8px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: submitting ? 'not-allowed' : 'pointer',
              opacity: submitting ? 0.7 : 1,
            }}
          >
            <Send size={14} />
            {submitting ? 'Extracting & Ingesting...' : 'Ingest Turn'}
          </button>
        </form>
      </div>

      {/* Episode Timeline Feed */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', overflowY: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
            Episodic Turn History ({episodes.length})
          </h2>
          <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Latest first</span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {episodes.map((ep) => (
            <div
              key={ep.id}
              style={{
                background: 'rgba(15, 23, 42, 0.6)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge badge-${ep.role === 'user' ? 'person' : ep.role === 'agent' ? 'tool' : 'concept'}`}>
                    {ep.role}
                  </span>
                  <span style={{ fontSize: '0.7rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={11} />
                    {new Date(ep.created_at).toLocaleTimeString()}
                  </span>
                </div>

                <span className="badge badge-org" style={{ fontSize: '0.68rem' }}>
                  <Sparkles size={10} style={{ marginRight: '3px' }} />
                  {ep.extracted_triplets_count} Triplets
                </span>
              </div>

              <p style={{ fontSize: '0.85rem', color: '#e2e8f0', lineHeight: '1.45' }}>
                {ep.content}
              </p>

              {ep.tags && ep.tags.length > 0 && (
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {ep.tags.map((tag, idx) => (
                    <span key={idx} style={{ fontSize: '0.7rem', color: '#94a3b8', background: 'rgba(30, 41, 59, 0.6)', padding: '2px 6px', borderRadius: '4px' }}>
                      #{tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}

          {episodes.length === 0 && (
            <div style={{ textAlign: 'center', color: '#64748b', padding: '40px 0' }}>
              No interaction turns in this session. Ingest one on the left to start memory consolidation!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
