"""
Knowledge Graph Traversal & Topology Statistics API router.
"""

from typing import Dict, Any
from fastapi import APIRouter, Query
from app.models.query import (
    GraphTraversalRequest,
    GraphTraversalResponse,
)
from app.services.graph import GraphTraverser

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.post("/traverse", response_model=GraphTraversalResponse, summary="Multi-Hop Subgraph Traversal")
async def traverse_subgraph(payload: GraphTraversalRequest):
    """
    Expands a depth-bounded multi-hop associative subgraph starting from one or more seed entities.
    Returns connected nodes (with computed decay scores) and directed relation edges.
    """
    subgraph, elapsed_ms = await GraphTraverser.traverse(
        session_id=payload.session_id,
        seed_entities=payload.seed_entities,
        max_hops=payload.max_hops,
        min_confidence=payload.min_confidence,
        limit_nodes=payload.limit_nodes,
    )

    return GraphTraversalResponse(
        session_id=payload.session_id,
        seed_entities=payload.seed_entities,
        subgraph=subgraph,
        execution_time_ms=elapsed_ms,
    )


@router.get("/stats", summary="Graph Topology & Hub Analytics")
async def get_graph_stats(
    session_id: str = Query(..., description="Target session scope"),
) -> Dict[str, Any]:
    """
    Retrieves global network topology metrics including node degrees, top connected hubs,
    graph density, and entity counts.
    """
    return await GraphTraverser.get_graph_stats(session_id)
