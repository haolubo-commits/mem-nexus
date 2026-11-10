"""
Unit tests for Graph Traverser and Topology calculation.
"""

import pytest
from app.services.graph import GraphTraverser
from app.db.mongodb import db_manager


@pytest.mark.asyncio
async def test_graph_traversal_cycle_resilience():
    session_id = "test-cycle-sess"
    relations_col = db_manager.get_collection("relations")
    entities_col = db_manager.get_collection("entities")

    # Clean
    await relations_col.delete_many({"session_id": session_id})
    await entities_col.delete_many({"session_id": session_id})

    # Create cycle: NodeA -> NodeB -> NodeC -> NodeA
    edges = [
        ("NodeA", "NodeB", "points_to"),
        ("NodeB", "NodeC", "points_to"),
        ("NodeC", "NodeA", "points_to"),
    ]
    for s, t, p in edges:
        await relations_col.insert_one({
            "session_id": session_id,
            "source_entity": s,
            "target_entity": t,
            "predicate": p,
            "confidence": 0.9,
            "weight": 1.0,
        })

    subgraph, elapsed = await GraphTraverser.traverse(
        session_id=session_id,
        seed_entities=["NodeA"],
        max_hops=3,
        min_confidence=0.5
    )

    # All 3 nodes should be visited without infinite loop
    assert subgraph.total_nodes == 3
    assert subgraph.total_edges == 3
    assert elapsed >= 0.0


@pytest.mark.asyncio
async def test_graph_stats():
    session_id = "test-stats-sess"
    relations_col = db_manager.get_collection("relations")
    entities_col = db_manager.get_collection("entities")

    await relations_col.delete_many({"session_id": session_id})
    await entities_col.delete_many({"session_id": session_id})

    # Insert 2 entities and 1 relation
    await entities_col.insert_one({"session_id": session_id, "name": "E1", "normalized_name": "e1"})
    await entities_col.insert_one({"session_id": session_id, "name": "E2", "normalized_name": "e2"})
    await relations_col.insert_one({
        "session_id": session_id,
        "source_entity": "E1",
        "target_entity": "E2",
        "predicate": "connects",
        "confidence": 0.9,
    })

    stats = await GraphTraverser.get_graph_stats(session_id)
    assert stats["total_entities"] == 2
    assert stats["total_relations"] == 1
    assert len(stats["top_connected_hubs"]) >= 1

