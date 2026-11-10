"""
Integration tests for MemNexus REST APIs.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "database" in data


def test_episodes_crud_and_auto_extraction(client: TestClient):
    session_id = "test-api-session"
    turn_text = "User prefers React for dashboard rendering. The UI relies on Vite."

    res = client.post("/api/v1/episodes", json={
        "session_id": session_id,
        "role": "user",
        "content": turn_text,
        "tags": ["frontend", "preferences"]
    })
    assert res.status_code == 201
    ep = res.json()
    assert ep["session_id"] == session_id
    assert ep["extracted_triplets_count"] >= 1
    episode_id = ep["id"]

    # Read back episode
    get_res = client.get(f"/api/v1/episodes/{episode_id}")
    assert get_res.status_code == 200
    assert get_res.json()["content"] == turn_text

    # List episodes
    list_res = client.get(f"/api/v1/episodes?session_id={session_id}")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_entities_and_update(client: TestClient):
    session_id = "test-ent-session"
    create_res = client.post("/api/v1/entities", json={
        "session_id": session_id,
        "name": "Redis Cache",
        "entity_type": "tool",
        "description": "In-memory caching layer",
        "importance_score": 0.85,
    })
    assert create_res.status_code == 201
    ent = create_res.json()
    ent_id = ent["id"]

    # Update entity
    put_res = client.put(f"/api/v1/entities/{ent_id}", json={
        "importance_score": 0.95,
        "description": "Primary high-speed cache",
    })
    assert put_res.status_code == 200
    assert put_res.json()["importance_score"] == 0.95
    assert put_res.json()["description"] == "Primary high-speed cache"

    # Detail view
    detail_res = client.get(f"/api/v1/entities/{ent_id}")
    assert detail_res.status_code == 200
    assert "outgoing_relations" in detail_res.json()


def test_relations_crud(client: TestClient):
    session_id = "test-rel-session"
    create_res = client.post("/api/v1/relations", json={
        "session_id": session_id,
        "source_entity": "Microservice A",
        "target_entity": "Database B",
        "predicate": "queries",
        "confidence": 0.88,
        "weight": 1.2,
    })
    assert create_res.status_code == 201
    rel = create_res.json()
    assert rel["predicate"] == "queries"

    # Query relations
    list_res = client.get(f"/api/v1/relations?session_id={session_id}&source_entity=Microservice A")
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_memory_recall_flow(client: TestClient):
    session_id = "test-recall-flow"
    # Seed knowledge turn
    client.post("/api/v1/episodes", json={
        "session_id": session_id,
        "role": "user",
        "content": "Alice works at Anthropic. Alice created Claude Code.",
    })

    # Perform recall
    recall_res = client.post("/api/v1/recall", json={
        "session_id": session_id,
        "query_text": "Where does Alice work?",
        "max_hops": 2,
    })
    assert recall_res.status_code == 200
    data = recall_res.json()
    assert "Alice" in data["matched_entities"]
    assert "Anthropic" in data["assembled_context"]
    assert data["execution_time_ms"] > 0.0

