"""
Knowledge Graph Relations & Triplet Edges API router.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, Query, status

from app.db.mongodb import db_manager
from app.models.relation import (
    RelationCreate,
    RelationResponse,
)

router = APIRouter(prefix="/relations", tags=["Relations"])


@router.post("", response_model=RelationResponse, status_code=status.HTTP_201_CREATED, summary="Create or Reinforce Relation")
async def create_relation(payload: RelationCreate):
    relations_col = db_manager.get_collection("relations")
    now = datetime.now(timezone.utc)

    existing = await relations_col.find_one({
        "session_id": payload.session_id,
        "source_entity": payload.source_entity,
        "target_entity": payload.target_entity,
        "predicate": payload.predicate,
    })

    if existing:
        rel_id = str(existing.get("_id"))
        new_weight = float(existing.get("weight", 1.0)) + payload.weight
        await relations_col.update_one(
            {"_id": rel_id},
            {
                "$set": {
                    "confidence": max(float(existing.get("confidence", 0.8)), payload.confidence),
                    "evidence_text": payload.evidence_text or existing.get("evidence_text", ""),
                    "last_reinforced_at": now,
                    "weight": new_weight,
                }
            }
        )
        updated = await relations_col.find_one({"_id": rel_id})
        return RelationResponse(
            id=rel_id,
            session_id=payload.session_id,
            source_entity=payload.source_entity,
            target_entity=payload.target_entity,
            predicate=payload.predicate,
            confidence=float(updated.get("confidence", 0.8)),
            weight=float(updated.get("weight", 1.0)),
            evidence_text=updated.get("evidence_text", ""),
            evidence_episode_id=updated.get("evidence_episode_id"),
            created_at=updated.get("created_at", now),
            last_reinforced_at=now,
        )

    rel_id = str(uuid.uuid4())
    doc = {
        "_id": rel_id,
        "session_id": payload.session_id,
        "source_entity": payload.source_entity,
        "target_entity": payload.target_entity,
        "predicate": payload.predicate,
        "confidence": payload.confidence,
        "weight": payload.weight,
        "evidence_text": payload.evidence_text or "",
        "evidence_episode_id": payload.evidence_episode_id,
        "created_at": now,
        "last_reinforced_at": now,
    }
    await relations_col.insert_one(doc)

    return RelationResponse(
        id=rel_id,
        session_id=payload.session_id,
        source_entity=payload.source_entity,
        target_entity=payload.target_entity,
        predicate=payload.predicate,
        confidence=payload.confidence,
        weight=payload.weight,
        evidence_text=payload.evidence_text or "",
        evidence_episode_id=payload.evidence_episode_id,
        created_at=now,
        last_reinforced_at=now,
    )


@router.get("", response_model=List[RelationResponse], summary="List Relations with Query Filters")
async def list_relations(
    session_id: str = Query(..., description="Target session scope"),
    source_entity: Optional[str] = Query(None, description="Filter by source entity"),
    target_entity: Optional[str] = Query(None, description="Filter by target entity"),
    predicate: Optional[str] = Query(None, description="Filter by relation predicate"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=500),
):
    relations_col = db_manager.get_collection("relations")
    query: Dict[str, Any] = {"session_id": session_id}
    if source_entity:
        query["source_entity"] = source_entity
    if target_entity:
        query["target_entity"] = target_entity
    if predicate:
        query["predicate"] = predicate

    cursor = relations_col.find(query).limit(limit)
    docs = await cursor.to_list(limit)

    results = []
    for d in docs:
        conf = float(d.get("confidence", 0.8))
        if conf < min_confidence:
            continue
        results.append(RelationResponse(
            id=str(d.get("_id")),
            session_id=d.get("session_id"),
            source_entity=d.get("source_entity", ""),
            target_entity=d.get("target_entity", ""),
            predicate=d.get("predicate", ""),
            confidence=conf,
            weight=float(d.get("weight", 1.0)),
            evidence_text=d.get("evidence_text", ""),
            evidence_episode_id=d.get("evidence_episode_id"),
            created_at=d.get("created_at", datetime.now(timezone.utc)),
            last_reinforced_at=d.get("last_reinforced_at", datetime.now(timezone.utc)),
        ))
    return results

