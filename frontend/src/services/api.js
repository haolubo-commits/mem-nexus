/**
 * API client service for MemNexus Backend.
 */

const BASE_URL = '/api/v1';

export async function fetchHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function fetchEpisodes(sessionId) {
  const res = await fetch(`${BASE_URL}/episodes?session_id=${encodeURIComponent(sessionId)}&limit=50`);
  if (!res.ok) throw new Error('Failed to fetch episodes');
  return res.json();
}

export async function ingestEpisode(sessionId, content, role = 'user', tags = []) {
  const res = await fetch(`${BASE_URL}/episodes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      content,
      role,
      tags,
    }),
  });
  if (!res.ok) throw new Error('Failed to ingest episode turn');
  return res.json();
}

export async function fetchEntities(sessionId) {
  const res = await fetch(`${BASE_URL}/entities?session_id=${encodeURIComponent(sessionId)}&limit=100`);
  if (!res.ok) throw new Error('Failed to fetch entities');
  return res.json();
}

export async function fetchRelations(sessionId) {
  const res = await fetch(`${BASE_URL}/relations?session_id=${encodeURIComponent(sessionId)}&limit=200`);
  if (!res.ok) throw new Error('Failed to fetch relations');
  return res.json();
}

export async function traverseGraph(sessionId, seedEntities, maxHops = 2) {
  const res = await fetch(`${BASE_URL}/graph/traverse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      seed_entities: seedEntities,
      max_hops: maxHops,
    }),
  });
  if (!res.ok) throw new Error('Failed to traverse graph');
  return res.json();
}

export async function fetchGraphStats(sessionId) {
  const res = await fetch(`${BASE_URL}/graph/stats?session_id=${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error('Failed to fetch graph stats');
  return res.json();
}

export async function recallMemory(sessionId, queryText, maxHops = 2) {
  const res = await fetch(`${BASE_URL}/recall`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      query_text: queryText,
      max_hops: maxHops,
    }),
  });
  if (!res.ok) throw new Error('Failed to perform memory recall');
  return res.json();
}

export async function updateEntity(entityId, updates) {
  const res = await fetch(`${BASE_URL}/entities/${entityId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates),
  });
  if (!res.ok) throw new Error('Failed to update entity');
  return res.json();
}

