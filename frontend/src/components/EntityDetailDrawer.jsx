import React, { useState, useEffect } from 'react';
import { X, Sliders, Activity, Clock, Share2, Save, Check } from 'lucide-react';
import { updateEntity } from '../services/api';

export default function EntityDetailDrawer({ entity, sessionId, onClose, onUpdated }) {
  const [importance, setImportance] = useState(entity.importance_score || 0.7);
  const [description, setDescription] = useState(entity.description || '');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setImportance(entity.importance_score || 0.7);
    setDescription(entity.description || '');
    setSaved(false);
  }, [entity]);

  const handleSave = async () => {
    try {
      setSaving(true);
      await updateEntity(entity.id, {
        importance_score: parseFloat(importance),
        description: description,
      });
      setSaved(true);
      if (onUpdated) onUpdated();
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error('Failed to update entity:', err);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="glass-panel" style={{ height: '100%', padding: '18px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <span className={`badge badge-${entity.entity_type}`} style={{ marginBottom: '4px' }}>
            {entity.entity_type}
          </span>
          <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f8fafc' }}>
            {entity.name}
          </h2>
          <span className="font-mono" style={{ fontSize: '0.7rem', color: '#64748b' }}>
            key: {entity.normalized_name}
          </span>
        </div>

        <button
          onClick={onClose}
          style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', padding: '4px' }}
        >
          <X size={18} />
        </button>
      </div>

      {/* Memory Decay & Metrics */}
      <div style={{
        background: 'rgba(15, 23, 42, 0.7)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '8px',
        padding: '12px',
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '10px'
      }}>
        <div>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Decayed Score</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#818cf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Activity size={14} />
            {(entity.decayed_score || 0.7).toFixed(3)}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Access / Recalls</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Clock size={14} />
            {entity.access_count || 0}
          </div>
        </div>
      </div>

      {/* Importance Score Tuning */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label style={{ fontSize: '0.75rem', color: '#94a3b8', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Sliders size={13} />
            Base Importance Prior
          </label>
          <span className="font-mono" style={{ fontSize: '0.8rem', color: '#cbd5e1' }}>
            {parseFloat(importance).toFixed(2)}
          </span>
        </div>

        <input
          type="range"
          min="0.1"
          max="1.0"
          step="0.05"
          value={importance}
          onChange={(e) => setImportance(e.target.value)}
          style={{ width: '100%', accentColor: '#6366f1', cursor: 'pointer' }}
        />
      </div>

      {/* Description */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <label style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Description / Summary</label>
        <textarea
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Entity role or summary..."
          style={{
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '6px',
            padding: '8px 10px',
            color: '#f8fafc',
            fontSize: '0.8rem',
            outline: 'none',
            resize: 'none',
          }}
        />
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={saving}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          background: saved ? '#10b981' : 'rgba(99, 102, 241, 0.3)',
          border: '1px solid rgba(99, 102, 241, 0.5)',
          color: '#ffffff',
          padding: '8px',
          borderRadius: '6px',
          fontSize: '0.8rem',
          fontWeight: 600,
          cursor: saving ? 'not-allowed' : 'pointer',
        }}
      >
        {saved ? <Check size={14} /> : <Save size={14} />}
        {saved ? 'Saved!' : saving ? 'Updating...' : 'Save Updates'}
      </button>

      {/* Timestamps */}
      <div style={{ marginTop: 'auto', borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', fontSize: '0.7rem', color: '#64748b', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <div>Created: {new Date(entity.created_at).toLocaleString()}</div>
        <div>Last Accessed: {new Date(entity.last_accessed_at).toLocaleString()}</div>
      </div>
    </div>
  );
}
