"""
Episodic memory turn ingestion and retrieval API router.
"""

from typing import List, Optional
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, Query, status

from app.db.mongodb import db_manager
from app.models.episode import (
    EpisodeCreate,
    EpisodeResponse,
    EpisodeRole,
    EpisodeStatus,
)
from app.models.entity import EntityType
from app.services.extractor import TripletExtractor
from app.services.decay import DecayEngine

router = APIRouter(prefix="/episodes", tags=["Episodes"])


@router.post("", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED, summary="Ingest Conversation Turn")
async def ingest_episode(payload: EpisodeCreate):
    """
    Ingest a new interaction turn. Automatically triggers semantic triplet extraction,
    upserting identified entities and knowledge graph relation edges into the session graph.
    """
    episodes_col = db_manager.get_collection("episodes")
    entities_col = db_manager.get_collection("entities")
    relations_col = db_manager.get_collection("relations")

    now = datetime.now(timezone.utc)
    episode_id = str(uuid.uuid4())

    # 1. Extract semantic triplets
    triplets = TripletExtractor.extract(payload.content)
    base_importance = payload.importance_hint if payload.importance_hint is not None else 0.7

    # 2. Upsert extracted entities and relations
    for t in triplets:
        # Upsert source entity
        norm_source = TripletExtractor.normalize_name(t.source)
        await entities_col.update_one(
            {"session_id": payload.session_id, "normalized_name": norm_source},
            {
                "$set": {
                    "name": t.source,
                    "normalized_name": norm_source,
                    "entity_type": t.source_type.value,
                    "last_accessed_at": now,
                },
                "$setOnInsert": {
                    "_id": str(uuid.uuid4()),
                    "session_id": payload.session_id,
                    "description": f"Extracted from episode {episode_id}",
                    "importance_score": base_importance,
                    "access_count": 1,
                    "created_at": now,
                    "attributes": {},
                }
            },
            upsert=True
        )

        # Upsert target entity
        norm_target = TripletExtractor.normalize_name(t.target)
        await entities_col.update_one(
            {"session_id": payload.session_id, "normalized_name": norm_target},
            {
                "$set": {
                    "name": t.target,
                    "normalized_name": norm_target,
                    "entity_type": t.target_type.value,
                    "last_accessed_at": now,
                },
                "$setOnInsert": {
                    "_id": str(uuid.uuid4()),
                    "session_id": payload.session_id,
                    "description": f"Extracted from episode {episode_id}",
                    "importance_score": base_importance,
                    "access_count": 1,
                    "created_at": now,
                    "attributes": {},
                }
            },
            upsert=True
        )

        # Upsert relation edge
        await relations_col.update_one(
            {
                "session_id": payload.session_id,
                "source_entity": t.source,
                "target_entity": t.target,
                "predicate": t.predicate,
            },
            {
                "$set": {
                    "confidence": max(t.confidence, 0.7),
                    "evidence_text": t.evidence,
                    "evidence_episode_id": episode_id,
                    "last_reinforced_at": now,
                },
                "$inc": {"weight": 0.5},
                "$setOnInsert": {
                    "_id": str(uuid.uuid4()),
                    "session_id": payload.session_id,
                    "source_entity": t.source,
                    "target_entity": t.target,
                    "predicate": t.predicate,
                    "created_at": now,
                }
            },
            upsert=True
        )

    # 3. Save episode document
    episode_doc = {
        "_id": episode_id,
        "session_id": payload.session_id,
        "role": payload.role.value,
        "content": payload.content,
        "extracted_triplets_count": len(triplets),
        "importance_score": base_importance,
        "status": EpisodeStatus.PROCESSED.value,
        "created_at": now,
        "tags": payload.tags,
        "metadata": payload.metadata,
    }
    await episodes_col.insert_one(episode_doc)

    return EpisodeResponse(
        id=episode_id,
        session_id=payload.session_id,
        role=payload.role,
        content=payload.content,
        extracted_triplets_count=len(triplets),
        importance_score=base_importance,
        status=EpisodeStatus.PROCESSED,
        created_at=now,
        tags=payload.tags,
        metadata=payload.metadata,
    )


@router.get("", response_model=List[EpisodeResponse], summary="List Session Episodes")
async def list_episodes(
    session_id: str = Query(..., description="Target session scope"),
    role: Optional[EpisodeRole] = Query(None, description="Filter by actor role"),
    limit: int = Query(50, ge=1, le=200),
):
    episodes_col = db_manager.get_collection("episodes")
    query = {"session_id": session_id}
    if role:
        query["role"] = role.value

    cursor = episodes_col.find(query).sort("created_at", -1).limit(limit)
    docs = await cursor.to_list(limit)

    results = []
    for d in docs:
        results.append(EpisodeResponse(
            id=str(d.get("_id")),
            session_id=d.get("session_id"),
            role=EpisodeRole(d.get("role", EpisodeRole.USER.value)),
            content=d.get("content", ""),
            extracted_triplets_count=d.get("extracted_triplets_count", 0),
            importance_score=float(d.get("importance_score", 0.5)),
            status=EpisodeStatus(d.get("status", EpisodeStatus.PROCESSED.value)),
            created_at=d.get("created_at", datetime.now(timezone.utc)),
            tags=d.get("tags", []),
            metadata=d.get("metadata", {}),
        ))
    return results


@router.get("/{episode_id}", response_model=EpisodeResponse, summary="Get Episode Detail")
async def get_episode(episode_id: str):
    episodes_col = db_manager.get_collection("episodes")
    doc = await episodes_col.find_one({"_id": episode_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Episode '{episode_id}' not found")

    return EpisodeResponse(
        id=str(doc.get("_id")),
        session_id=doc.get("session_id"),
        role=EpisodeRole(doc.get("role", EpisodeRole.USER.value)),
        content=doc.get("content", ""),
        extracted_triplets_count=doc.get("extracted_triplets_count", 0),
        importance_score=float(doc.get("importance_score", 0.5)),
        status=EpisodeStatus(doc.get("status", EpisodeStatus.PROCESSED.value)),
        created_at=doc.get("created_at", datetime.now(timezone.utc)),
        tags=doc.get("tags", []),
        metadata=doc.get("metadata", {}),
    )
