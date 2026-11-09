import React, { useState, useMemo } from 'react';
import { Search, Filter, Maximize2, ZoomIn, ZoomOut, Compass } from 'lucide-react';

const ENTITY_COLORS = {
  tool: '#38bdf8',
  person: '#c084fc',
  concept: '#818cf8',
  organization: '#fbbf24',
  preference: '#fb7185',
  location: '#34d399',
  task: '#a78bfa',
  attribute: '#94a3b8',
  other: '#64748b',
};

export default function KnowledgeGraphCanvas({ entities = [], relations = [], highlightedNodes = [], onSelectEntity }) {
  const [search, setSearch] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [zoom, setZoom] = useState(1);

  // Filter entities
  const filteredEntities = useMemo(() => {
    return entities.filter(ent => {
      const matchType = selectedType === 'all' || ent.entity_type === selectedType;
      const matchSearch = !search || ent.name.toLowerCase().includes(search.toLowerCase());
      return matchType && matchSearch;
    });
  }, [entities, selectedType, search]);

  const filteredEntityNames = useMemo(() => {
    return new Set(filteredEntities.map(e => e.name.toLowerCase()));
  }, [filteredEntities]);

  // Compute organic 2D layout coordinates for nodes
  const nodePositions = useMemo(() => {
    const coords = {};
    const total = filteredEntities.length;
    if (total === 0) return coords;

    const centerX = 400;
    const centerY = 280;
    const radiusBase = Math.min(220, Math.max(120, total * 22));

    filteredEntities.forEach((ent, i) => {
      // Golden angle spiral distribution
      const angle = i * 2.39996; // Golden ratio in radians
      const r = Math.sqrt(i + 1) / Math.sqrt(total) * radiusBase;
      const x = centerX + r * Math.cos(angle);
      const y = centerY + r * Math.sin(angle);
      coords[ent.name.toLowerCase()] = { x, y, entity: ent };
    });

    return coords;
  }, [filteredEntities]);

  // Filter relations that link visible nodes
  const visibleEdges = useMemo(() => {
    return relations.filter(rel => {
      const s = rel.source_entity?.toLowerCase();
      const t = rel.target_entity?.toLowerCase();
      return filteredEntityNames.has(s) && filteredEntityNames.has(t);
    });
  }, [relations, filteredEntityNames]);

  return (
    <div className="glass-panel" style={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* Top Canvas Toolbar */}
      <div style={{
        padding: '12px 18px',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '12px',
        background: 'rgba(15, 23, 42, 0.4)'
      }}>
        {/* Search & Type filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ position: 'relative' }}>
            <Search size={14} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
            <input
              type="text"
              placeholder="Search entity node..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                background: 'rgba(15, 23, 42, 0.8)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '6px',
                padding: '6px 10px 6px 30px',
                color: '#f8fafc',
                fontSize: '0.8rem',
                outline: 'none',
                width: '180px'
              }}
            />
          </div>

          <div style={{ display: 'flex', gap: '4px' }}>
            {['all', 'tool', 'person', 'concept', 'organization', 'preference'].map(t => (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                style={{
                  fontSize: '0.72rem',
                  padding: '4px 8px',
                  borderRadius: '5px',
                  border: 'none',
                  cursor: 'pointer',
                  textTransform: 'capitalize',
                  background: selectedType === t ? 'rgba(99, 102, 241, 0.3)' : 'rgba(30, 41, 59, 0.5)',
                  color: selectedType === t ? '#818cf8' : '#94a3b8',
                }}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Zoom Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => setZoom(z => Math.max(0.6, z - 0.15))}
            style={{ padding: '5px', borderRadius: '5px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid var(--border-subtle)', color: '#94a3b8', cursor: 'pointer' }}
          >
            <ZoomOut size={13} />
          </button>
          <span style={{ fontSize: '0.75rem', color: '#64748b', minWidth: '40px', textAlign: 'center' }}>
            {(zoom * 100).toFixed(0)}%
          </span>
          <button
            onClick={() => setZoom(z => Math.min(2.0, z + 0.15))}
            style={{ padding: '5px', borderRadius: '5px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid var(--border-subtle)', color: '#94a3b8', cursor: 'pointer' }}
          >
            <ZoomIn size={13} />
          </button>
          <button
            onClick={() => setZoom(1)}
            style={{ padding: '5px', borderRadius: '5px', background: 'rgba(30, 41, 59, 0.6)', border: '1px solid var(--border-subtle)', color: '#94a3b8', cursor: 'pointer' }}
            title="Reset View"
          >
            <Compass size={13} />
          </button>
        </div>
      </div>

      {/* Interactive SVG Canvas */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg
          viewBox="0 0 800 560"
          style={{
            width: '100%',
            height: '100%',
            transform: `scale(${zoom})`,
            transformOrigin: 'center center',
            transition: 'transform 0.15s ease-out'
          }}
        >
          <defs>
            <marker
              id="arrow"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="rgba(148, 163, 184, 0.45)" />
            </marker>
            <marker
              id="arrow-active"
              viewBox="0 0 10 10"
              refX="18"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="#818cf8" />
            </marker>
          </defs>

          {/* Render Relations / Edges */}
          {visibleEdges.map((rel, idx) => {
            const sCoord = nodePositions[rel.source_entity?.toLowerCase()];
            const tCoord = nodePositions[rel.target_entity?.toLowerCase()];
            if (!sCoord || !tCoord) return null;

            const isHighlighted = highlightedNodes.some(hn => 
              hn.toLowerCase() === rel.source_entity?.toLowerCase() ||
              hn.toLowerCase() === rel.target_entity?.toLowerCase()
            );

            const midX = (sCoord.x + tCoord.x) / 2;
            const midY = (sCoord.y + tCoord.y) / 2;

            return (
              <g key={`edge-${idx}`}>
                <line
                  x1={sCoord.x}
                  y1={sCoord.y}
                  x2={tCoord.x}
                  y2={tCoord.y}
                  stroke={isHighlighted ? '#818cf8' : 'rgba(148, 163, 184, 0.2)'}
                  strokeWidth={isHighlighted ? 2.5 : 1.2}
                  strokeDasharray={rel.confidence < 0.8 ? '4 3' : 'none'}
                  markerEnd={isHighlighted ? 'url(#arrow-active)' : 'url(#arrow)'}
                />
                <text
                  x={midX}
                  y={midY - 4}
                  textAnchor="middle"
                  fill={isHighlighted ? '#c7d2fe' : '#64748b'}
                  fontSize="9px"
                  fontFamily="var(--font-mono)"
                  style={{ pointerEvents: 'none', userSelect: 'none' }}
                >
                  {rel.predicate}
                </text>
              </g>
            );
          })}

          {/* Render Entities / Nodes */}
          {filteredEntities.map((ent) => {
            const coord = nodePositions[ent.name.toLowerCase()];
            if (!coord) return null;

            const isHighlighted = highlightedNodes.some(hn => hn.toLowerCase() === ent.name.toLowerCase());
            const color = ENTITY_COLORS[ent.entity_type] || '#818cf8';
            // Size scales with decayed score (min 14, max 28)
            const radius = 14 + (ent.decayed_score || 0.7) * 14;

            return (
              <g
                key={ent.id || ent.name}
                transform={`translate(${coord.x}, ${coord.y})`}
                onClick={() => onSelectEntity && onSelectEntity(ent)}
                style={{ cursor: 'pointer' }}
              >
                {/* Glow ring if highlighted */}
                {isHighlighted && (
                  <circle
                    r={radius + 8}
                    fill="none"
                    stroke="#6366f1"
                    strokeWidth="2"
                    strokeDasharray="4 2"
                    opacity="0.8"
                  />
                )}

                {/* Node Outer Halo */}
                <circle
                  r={radius}
                  fill="rgba(15, 23, 42, 0.85)"
                  stroke={color}
                  strokeWidth={isHighlighted ? 3 : 2}
                  style={{ filter: `drop-shadow(0 0 6px ${color}66)` }}
                />

                {/* Inner Core */}
                <circle
                  r={radius * 0.4}
                  fill={color}
                  opacity={ent.decayed_score || 0.7}
                />

                {/* Label */}
                <text
                  y={radius + 14}
                  textAnchor="middle"
                  fill="#f1f5f9"
                  fontSize="11px"
                  fontWeight="600"
                  fontFamily="var(--font-sans)"
                  style={{ userSelect: 'none', textShadow: '0 1px 3px rgba(0,0,0,0.8)' }}
                >
                  {ent.name}
                </text>

                {/* Score Pill */}
                <text
                  y={radius + 25}
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize="8.5px"
                  fontFamily="var(--font-mono)"
                  style={{ userSelect: 'none' }}
                >
                  R:{(ent.decayed_score || 0.7).toFixed(2)}
                </text>
              </g>
            );
          })}
        </svg>

        {filteredEntities.length === 0 && (
          <div style={{ position: 'absolute', textAlign: 'center', color: '#64748b' }}>
            <Compass size={36} style={{ margin: '0 auto 8px', opacity: 0.5 }} />
            <p style={{ fontSize: '0.9rem' }}>No entity nodes discovered yet.</p>
            <p style={{ fontSize: '0.75rem' }}>Ingest episodic turns or seed the graph to explore.</p>
          </div>
        )}
      </div>
    </div>
  );
}
