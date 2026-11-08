"""
Knowledge Graph Entity management API router.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from fastapi import APIRouter, HTTPException, Query, status

from app.db.mongodb import db_manager
from app.models.entity import (
    EntityCreate,
    EntityUpdate,
    EntityResponse,
    EntityType,
)
from app.services.extractor import TripletExtractor
from app.services.decay import DecayEngine

router = APIRouter(prefix="/entities", tags=["Entities"])


@router.post("", response_model=EntityResponse, status_code=status.HTTP_201_CREATED, summary="Create or Upsert Entity")
async def create_entity(payload: EntityCreate):
    entities_col = db_manager.get_collection("entities")
    now = datetime.now(timezone.utc)
    norm = TripletExtractor.normalize_name(payload.name)

    existing = await entities_col.find_one({"session_id": payload.session_id, "normalized_name": norm})
    if existing:
        entity_id = str(existing.get("_id"))
        await entities_col.update_one(
            {"_id": entity_id},
            {
                "$set": {
                    "name": payload.name,
                    "entity_type": payload.entity_type.value,
                    "description": payload.description or existing.get("description", ""),
                    "importance_score": payload.importance_score,
                    "attributes": {**existing.get("attributes", {}), **payload.attributes},
                    "last_accessed_at": now,
                },
                "$inc": {"access_count": 1}
            }
        )
        updated = await entities_col.find_one({"_id": entity_id})
        decayed = DecayEngine.apply_to_entity(updated)
        return EntityResponse(
            id=entity_id,
            session_id=payload.session_id,
            name=payload.name,
            normalized_name=norm,
            entity_type=payload.entity_type,
            description=updated.get("description", ""),
            importance_score=payload.importance_score,
            decayed_score=decayed,
            access_count=updated.get("access_count", 1),
            last_accessed_at=now,
            created_at=updated.get("created_at", now),
            attributes=updated.get("attributes", {}),
        )

    entity_id = str(uuid.uuid4())
    doc = {
        "_id": entity_id,
        "session_id": payload.session_id,
        "name": payload.name,
        "normalized_name": norm,
        "entity_type": payload.entity_type.value,
        "description": payload.description or "",
        "importance_score": payload.importance_score,
        "decayed_score": payload.importance_score,
        "access_count": 1,
        "last_accessed_at": now,
        "created_at": now,
        "attributes": payload.attributes,
    }
    await entities_col.insert_one(doc)

    return EntityResponse(
        id=entity_id,
        session_id=payload.session_id,
        name=payload.name,
        normalized_name=norm,
        entity_type=payload.entity_type,
        description=payload.description or "",
        importance_score=payload.importance_score,
        decayed_score=payload.importance_score,
        access_count=1,
        last_accessed_at=now,
        created_at=now,
        attributes=payload.attributes,
    )


@router.get("", response_model=List[EntityResponse], summary="List Entities with Decayed Scores")
async def list_entities(
    session_id: str = Query(..., description="Target session scope"),
    search: Optional[str] = Query(None, description="Search by name or keyword"),
    entity_type: Optional[EntityType] = Query(None, description="Filter by entity type"),
    limit: int = Query(100, ge=1, le=500),
):
    entities_col = db_manager.get_collection("entities")
    query: Dict[str, Any] = {"session_id": session_id}
    if entity_type:
        query["entity_type"] = entity_type.value

    cursor = entities_col.find(query).limit(limit)
    docs = await cursor.to_list(limit)

    results = []
    search_lower = search.lower().strip() if search else None

    for d in docs:
        name = d.get("name", "")
        desc = d.get("description", "")
        if search_lower and (search_lower not in name.lower() and search_lower not in desc.lower()):
            continue

        decayed = DecayEngine.apply_to_entity(d)
        results.append(EntityResponse(
            id=str(d.get("_id")),
            session_id=d.get("session_id"),
            name=name,
            normalized_name=d.get("normalized_name", ""),
            entity_type=EntityType(d.get("entity_type", EntityType.CONCEPT.value)),
            description=desc,
            importance_score=float(d.get("importance_score", 0.7)),
            decayed_score=decayed,
            access_count=int(d.get("access_count", 0)),
            last_accessed_at=d.get("last_accessed_at", datetime.now(timezone.utc)),
            created_at=d.get("created_at", datetime.now(timezone.utc)),
            attributes=d.get("attributes", {}),
        ))

    # Sort by decayed retention score descending
    results.sort(key=lambda x: x.decayed_score, reverse=True)
    return results


@router.get("/{entity_id}", summary="Get Entity Detail & Linked Relations")
async def get_entity(entity_id: str):
    entities_col = db_manager.get_collection("entities")
    relations_col = db_manager.get_collection("relations")

    doc = await entities_col.find_one({"_id": entity_id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

    session_id = doc.get("session_id")
    name = doc.get("name")

    # Fetch incident relations
    out_cursor = relations_col.find({"session_id": session_id, "source_entity": name})
    outgoing = await out_cursor.to_list(50)

    in_cursor = relations_col.find({"session_id": session_id, "target_entity": name})
    incoming = await in_cursor.to_list(50)

    decayed = DecayEngine.apply_to_entity(doc)

    return {
        "entity": EntityResponse(
            id=str(doc.get("_id")),
            session_id=session_id,
            name=name,
            normalized_name=doc.get("normalized_name", ""),
            entity_type=EntityType(doc.get("entity_type", EntityType.CONCEPT.value)),
            description=doc.get("description", ""),
            importance_score=float(doc.get("importance_score", 0.7)),
            decayed_score=decayed,
            access_count=int(doc.get("access_count", 0)),
            last_accessed_at=doc.get("last_accessed_at", datetime.now(timezone.utc)),
            created_at=doc.get("created_at", datetime.now(timezone.utc)),
            attributes=doc.get("attributes", {}),
        ),
        "outgoing_relations": outgoing,
        "incoming_relations": incoming,
    }


@router.put("/{entity_id}", response_model=EntityResponse, summary="Update Entity Attributes & Score")
async def update_entity(entity_id: str, payload: EntityUpdate):
    entities_col = db_manager.get_collection("entities")
    existing = await entities_col.find_one({"_id": entity_id})
    if not existing:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found")

    update_fields: Dict[str, Any] = {}
    if payload.description is not None:
        update_fields["description"] = payload.description
    if payload.entity_type is not None:
        update_fields["entity_type"] = payload.entity_type.value
    if payload.importance_score is not None:
        update_fields["importance_score"] = payload.importance_score
    if payload.attributes is not None:
        merged_attrs = {**existing.get("attributes", {}), **payload.attributes}
        update_fields["attributes"] = merged_attrs

    if update_fields:
        await entities_col.update_one({"_id": entity_id}, {"$set": update_fields})

    updated = await entities_col.find_one({"_id": entity_id})
    decayed = DecayEngine.apply_to_entity(updated)

    return EntityResponse(
        id=str(updated.get("_id")),
        session_id=updated.get("session_id"),
        name=updated.get("name"),
        normalized_name=updated.get("normalized_name", ""),
        entity_type=EntityType(updated.get("entity_type", EntityType.CONCEPT.value)),
        description=updated.get("description", ""),
        importance_score=float(updated.get("importance_score", 0.7)),
        decayed_score=decayed,
        access_count=int(updated.get("access_count", 0)),
        last_accessed_at=updated.get("last_accessed_at", datetime.now(timezone.utc)),
        created_at=updated.get("created_at", datetime.now(timezone.utc)),
        attributes=updated.get("attributes", {}),
    )
