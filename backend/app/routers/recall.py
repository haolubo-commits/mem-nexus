"""
Associative Memory Recall API router.
"""

from fastapi import APIRouter
from app.models.query import (
    MemoryRecallRequest,
    MemoryRecallResponse,
)
from app.services.recall import RecallConsolidator

router = APIRouter(prefix="/recall", tags=["Recall"])


@router.post("", response_model=MemoryRecallResponse, summary="Recall Contextual Memories for Prompt")
async def recall_memories(payload: MemoryRecallRequest):
    """
    Main associative memory retrieval endpoint for AI Agents.
    Scans query text for seed entities, traverses multi-hop associative subgraphs,
    applies Ebbinghaus forgetting decay, reinforces accessed nodes,
    and returns a structured, prompt-ready memory context block.
    """
    return await RecallConsolidator.recall(payload)
