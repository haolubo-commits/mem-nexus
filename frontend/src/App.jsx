import React, { useState, useEffect, useCallback } from 'react';
import { 
  Brain, 
  Network, 
  Search, 
  MessageSquare, 
  Activity, 
  RefreshCw, 
  Layers, 
  Sparkles,
  Database,
  Sliders
} from 'lucide-react';
import { 
  fetchHealth, 
  fetchEntities, 
  fetchRelations, 
  fetchEpisodes, 
  fetchGraphStats,
  ingestEpisode 
} from './services/api';
import KnowledgeGraphCanvas from './components/KnowledgeGraphCanvas';
import AssociativeRecallSimulator from './components/AssociativeRecallSimulator';
import EpisodicTurnStream from './components/EpisodicTurnStream';
import EntityDetailDrawer from './components/EntityDetailDrawer';
import TopologyStatsBar from './components/TopologyStatsBar';

export default function App() {
  const [sessionId, setSessionId] = useState('agent-workspace-alpha');
  const [activeTab, setActiveTab] = useState('graph'); // 'graph' | 'recall' | 'episodes'
  const [systemHealth, setSystemHealth] = useState(null);
  const [entities, setEntities] = useState([]);
  const [relations, setRelations] = useState([]);
  const [episodes, setEpisodes] = useState([]);
  const [graphStats, setGraphStats] = useState(null);
  const [selectedEntity, setSelectedEntity] = useState(null);
  const [loading, setLoading] = useState(true);
  const [highlightedNodes, setHighlightedNodes] = useState([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [health, entList, relList, epList, stats] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchEntities(sessionId).catch(() => []),
        fetchRelations(sessionId).catch(() => []),
        fetchEpisodes(sessionId).catch(() => []),
        fetchGraphStats(sessionId).catch(() => null),
      ]);
      setSystemHealth(health);
      setEntities(entList);
      setRelations(relList);
      setEpisodes(epList);
      setGraphStats(stats);
    } catch (err) {
      console.error('Failed to load MemNexus data:', err);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleEntitySelect = (entity) => {
    setSelectedEntity(entity);
  };

  const handleHighlightNodes = (nodeNames) => {
    setHighlightedNodes(nodeNames || []);
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <header style={{
        borderBottom: '1px solid var(--border-subtle)',
        background: 'rgba(7, 9, 14, 0.85)',
        backdropFilter: 'blur(12px)',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 40
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{
            background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
            padding: '8px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
          }}>
            <Brain size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.15rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#ffffff' }}>
                MemNexus
              </h1>
              <span className="badge badge-concept" style={{ fontSize: '0.65rem' }}>v0.1.0</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
              Episodic Memory & Multi-Hop Knowledge Graph Cockpit
            </p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{
          display: 'flex',
          gap: '6px',
          background: 'rgba(15, 23, 42, 0.6)',
          padding: '4px',
          borderRadius: '8px',
          border: '1px solid var(--border-subtle)'
        }}>
          <button
            onClick={() => setActiveTab('graph')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              border: 'none',
              background: activeTab === 'graph' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
              color: activeTab === 'graph' ? '#818cf8' : '#94a3b8',
              transition: 'all 0.15s ease'
            }}
          >
            <Network size={15} />
            Knowledge Graph
          </button>
          <button
            onClick={() => setActiveTab('recall')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              border: 'none',
              background: activeTab === 'recall' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
              color: activeTab === 'recall' ? '#818cf8' : '#94a3b8',
              transition: 'all 0.15s ease'
            }}
          >
            <Search size={15} />
            Recall Simulator
          </button>
          <button
            onClick={() => setActiveTab('episodes')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              border: 'none',
              background: activeTab === 'episodes' ? 'rgba(99, 102, 241, 0.25)' : 'transparent',
              color: activeTab === 'episodes' ? '#818cf8' : '#94a3b8',
              transition: 'all 0.15s ease'
            }}
          >
            <MessageSquare size={15} />
            Episodic Turns
          </button>
        </nav>

        {/* Right Session & Health Cockpit */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: '0.8rem',
            padding: '5px 10px',
            borderRadius: '6px',
            background: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid var(--border-subtle)'
          }}>
            <Database size={13} color="#06b6d4" />
            <span style={{ color: '#94a3b8' }}>Session:</span>
            <span className="font-mono" style={{ color: '#e2e8f0', fontWeight: 600 }}>{sessionId}</span>
          </div>

          <button
            onClick={loadData}
            title="Refresh Memory State"
            style={{
              padding: '7px',
              borderRadius: '6px',
              background: 'rgba(30, 41, 59, 0.6)',
              border: '1px solid var(--border-subtle)',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </header>

      {/* Main Body */}
      <main style={{ flex: 1, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        {/* Topology Statistics Bar */}
        <TopologyStatsBar stats={graphStats} entitiesCount={entities.length} relationsCount={relations.length} />

        {/* Dynamic Tab Views */}
        <div style={{ flex: 1, display: 'flex', gap: '20px', minHeight: '560px' }}>
          {activeTab === 'graph' && (
            <div style={{ flex: 1, display: 'flex', gap: '20px' }}>
              <div style={{ flex: 1 }}>
                <KnowledgeGraphCanvas 
                  entities={entities} 
                  relations={relations} 
                  highlightedNodes={highlightedNodes}
                  onSelectEntity={handleEntitySelect} 
                />
              </div>
              {selectedEntity && (
                <div style={{ width: '360px' }}>
                  <EntityDetailDrawer 
                    entity={selectedEntity} 
                    sessionId={sessionId}
                    onClose={() => setSelectedEntity(null)}
                    onUpdated={loadData}
                  />
                </div>
              )}
            </div>
          )}

          {activeTab === 'recall' && (
            <div style={{ flex: 1 }}>
              <AssociativeRecallSimulator 
                sessionId={sessionId} 
                onHighlightNodes={handleHighlightNodes}
                onSelectEntity={handleEntitySelect}
              />
            </div>
          )}

          {activeTab === 'episodes' && (
            <div style={{ flex: 1 }}>
              <EpisodicTurnStream 
                sessionId={sessionId} 
                episodes={episodes} 
                onIngested={loadData} 
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

