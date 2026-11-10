import React from 'react';
import { Network, Database, Share2, Layers, Cpu } from 'lucide-react';

export default function TopologyStatsBar({ stats, entitiesCount, relationsCount }) {
  const density = stats?.graph_density !== undefined ? `${(stats.graph_density * 100).toFixed(1)}%` : '0.0%';
  const hubs = stats?.top_connected_hubs || [];

  return (
    <div className="glass-panel" style={{ padding: '14px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '24px', flexWrap: 'wrap' }}>
        {/* Metric 1 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(99, 102, 241, 0.15)', padding: '7px', borderRadius: '8px' }}>
            <Network size={16} color="#818cf8" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Entity Nodes
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              {entitiesCount}
            </div>
          </div>
        </div>

        {/* Metric 2 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(6, 182, 212, 0.15)', padding: '7px', borderRadius: '8px' }}>
            <Share2 size={16} color="#38bdf8" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Relational Edges
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              {relationsCount}
            </div>
          </div>
        </div>

        {/* Metric 3 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(16, 185, 129, 0.15)', padding: '7px', borderRadius: '8px' }}>
            <Layers size={16} color="#34d399" />
          </div>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Graph Density
            </div>
            <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              {density}
            </div>
          </div>
        </div>
      </div>

      {/* Top Connected Hubs */}
      {hubs.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Cpu size={12} color="#f59e0b" />
            Top Hubs:
          </span>
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {hubs.slice(0, 3).map((hub, idx) => (
              <span
                key={idx}
                className="badge badge-tool"
                style={{ fontSize: '0.7rem', padding: '2px 7px' }}
                title={`${hub.degree} connections`}
              >
                {hub.entity} ({hub.degree})
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

