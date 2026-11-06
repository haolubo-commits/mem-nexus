"""
Query, graph traversal, and context recall models for associative memory retrieval.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.models.entity import EntityType


class GraphNode(BaseModel):
    id: str
    name: str
    entity_type: EntityType = EntityType.CONCEPT
    importance_score: float
    decayed_score: float
    hop_distance: int = 0
    access_count: int = 0


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    predicate: str
    confidence: float
    weight: float
    hop_level: int = 1


class GraphSubgraph(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    total_nodes: int = 0
    total_edges: int = 0
    hop_depth_reached: int = 0


class GraphTraversalRequest(BaseModel):
    session_id: str
    seed_entities: List[str] = Field(..., min_length=1, description="Entity names to initiate traversal from")
    max_hops: int = Field(default=2, ge=1, le=4, description="Maximum graph lookup depth")
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    limit_nodes: int = Field(default=50, ge=1, le=200)


class GraphTraversalResponse(BaseModel):
    session_id: str
    seed_entities: List[str]
    subgraph: GraphSubgraph
    execution_time_ms: float


class MemoryRecallRequest(BaseModel):
    session_id: str
    query_text: str = Field(..., min_length=1, description="Natural language prompt or query")
    seed_entities: Optional[List[str]] = Field(default=None, description="Optional explicit entity seeds")
    max_hops: int = Field(default=2, ge=1, le=4)
    min_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    include_subgraph: bool = Field(default=True)
    decay_rate: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class MemoryRecallResponse(BaseModel):
    session_id: str
    query: str
    matched_entities: List[str] = Field(default_factory=list)
    recalled_facts: List[str] = Field(default_factory=list)
    assembled_context: str = Field(..., description="Consolidated context string ready for LLM prompt injection")
    subgraph: Optional[GraphSubgraph] = None
    execution_time_ms: float
