# 📖 MemNexus API Reference & Architectural Guide

## 🌐 Base URL
```text
http://localhost:8000/api/v1
```

All responses conform to standard JSON formatting. Interactive OpenAPI documentation is hosted at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

---

## 🛠️ Endpoints Overview

| Category | Method | Path | Summary |
| :--- | :--- | :--- | :--- |
| **System** | `GET` | `/health` | Liveness, engine mode, and DB connection status |
| **Episodes** | `POST` | `/episodes` | Ingest turn & auto-extract semantic triplets |
| | `GET` | `/episodes` | Query and filter conversation history |
| | `GET` | `/episodes/{id}` | Inspect episodic turn detail |
| **Entities** | `GET` | `/entities` | List entities with dynamic Ebbinghaus decay scores |
| | `POST` | `/entities` | Create or update entity node |
| | `GET` | `/entities/{id}` | Entity detail with incident graph edges |
| | `PUT` | `/entities/{id}` | Update entity attributes and base importance |
| **Relations** | `POST` | `/relations` | Create or reinforce knowledge graph edge |
| | `GET` | `/relations` | Filter $(S \xrightarrow{P} O)$ edges with confidence |
| **Graph** | `POST` | `/graph/traverse` | Multi-hop associative subgraph traversal |
| | `GET` | `/graph/stats` | Network topology, hub degrees, and graph density |
| **Recall** | `POST` | `/recall` | Associative prompt recall with prompt-ready context |

---

## 🔍 Detailed Endpoint Documentation

### 1. Ingest Conversation Turn (`POST /api/v1/episodes`)
Ingests raw text interaction turns from users or agents, triggers automated semantic extraction, upserts entity vertices, and records relational edges.

#### Request Body
```json
{
  "session_id": "agent-session-001",
  "role": "user",
  "content": "Alice authored the backend architecture. Alice works at Google. The backend depends on MongoDB.",
  "importance_hint": 0.85,
  "tags": ["architecture", "team"]
}
```

#### Response (`201 Created`)
```json
{
  "id": "e96f1d2e-3378-4e56-9761-fae120da3e33",
  "session_id": "agent-session-001",
  "role": "user",
  "content": "Alice authored the backend architecture. Alice works at Google. The backend depends on MongoDB.",
  "extracted_triplets_count": 3,
  "importance_score": 0.85,
  "status": "processed",
  "created_at": "2026-11-08T10:45:00Z",
  "tags": ["architecture", "team"],
  "metadata": {}
}
```

---

### 2. Multi-Hop Graph Traversal (`POST /api/v1/graph/traverse`)
Performs a bounded breadth-first or `$graphLookup` traversal starting from anchor seed entities.

#### Request Body
```json
{
  "session_id": "agent-session-001",
  "seed_entities": ["Alice"],
  "max_hops": 2,
  "min_confidence": 0.7,
  "limit_nodes": 50
}
```

#### Response (`200 OK`)
```json
{
  "session_id": "agent-session-001",
  "seed_entities": ["Alice"],
  "subgraph": {
    "nodes": [
      {
        "id": "alice",
        "name": "Alice",
        "entity_type": "person",
        "importance_score": 0.85,
        "decayed_score": 0.85,
        "hop_distance": 0,
        "access_count": 2
      },
      {
        "id": "google",
        "name": "Google",
        "entity_type": "organization",
        "importance_score": 0.70,
        "decayed_score": 0.70,
        "hop_distance": 1,
        "access_count": 1
      }
    ],
    "edges": [
      {
        "id": "rel-01",
        "source": "Alice",
        "target": "Google",
        "predicate": "works_at",
        "confidence": 0.94,
        "weight": 1.5,
        "hop_level": 1
      }
    ],
    "total_nodes": 2,
    "total_edges": 1,
    "hop_depth_reached": 1
  },
  "execution_time_ms": 1.25
}
```

---

### 3. Associative Memory Recall (`POST /api/v1/recall`)
Synthesizes multi-hop memory context directly into structured Markdown blocks for autonomous LLM agent prompts.

#### Request Body
```json
{
  "session_id": "agent-session-001",
  "query_text": "What company does Alice work for and what database is used?",
  "max_hops": 2,
  "min_confidence": 0.6
}
```

#### Response (`200 OK`)
```json
{
  "session_id": "agent-session-001",
  "query": "What company does Alice work for and what database is used?",
  "matched_entities": ["Alice", "database"],
  "recalled_facts": [
    "Alice works_at Google (conf: 0.94)",
    "backend depends_on MongoDB (conf: 0.88)"
  ],
  "assembled_context": "=== RECALLED MEMNEXUS KNOWLEDGE GRAPH CONTEXT ===\nActive Session: agent-session-001\nQuery Prompt: \"What company does Alice work for and what database is used?\"\nAnchor Seeds: Alice\nRecalled Subgraph: 3 entities, 2 relations (1-hop depth)\n\nAssociative Facts:\n  • Alice works_at Google (conf: 0.94)\n  • backend depends_on MongoDB (conf: 0.88)\n\nEntity State & Memory Decay:\n  • Alice [person] — decayed retention: 0.85, accesses: 3\n  • Google [organization] — decayed retention: 0.70, accesses: 1\n==================================================",
  "execution_time_ms": 2.15
}
```

---

## 📈 Ebbinghaus Memory Decay Formulation

MemNexus implements continuous memory retention scoring:

$$R(t) = I_0 \cdot \exp\left(-\lambda \cdot \frac{\Delta t_{\text{hours}}}{24}\right) + \beta \cdot \ln(1 + N_{\text{access}})$$

- $I_0$: Initial importance assigned at observation.
- $\lambda$: Forgetting decay parameter (default `0.05`).
- $\Delta t$: Elapsed time since last recall.
- $\beta$: Reinforcement boost multiplier (default `0.15`).
- $N_{\text{access}}$: Total recall frequency. Repeated associative references dynamically revive memories before they decay.

