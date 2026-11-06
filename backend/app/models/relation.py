"""
Relation edge schemas representing $(Subject -> Predicate -> Object)$ triplets.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class RelationCreate(BaseModel):
    session_id: str = Field(..., description="Agent or conversation scope")
    source_entity: str = Field(..., min_length=1, description="Source subject entity name")
    target_entity: str = Field(..., min_length=1, description="Target object entity name")
    predicate: str = Field(..., min_length=1, description="Directed predicate relation (e.g. 'depends_on', 'prefers')")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Extraction certainty")
    weight: float = Field(default=1.0, ge=0.1, le=10.0, description="Edge strength / traversal weight")
    evidence_text: Optional[str] = Field(default="", description="Original utterance context")
    evidence_episode_id: Optional[str] = Field(default=None, description="Linked episodic turn ID")


class RelationResponse(BaseModel):
    id: str
    session_id: str
    source_entity: str
    target_entity: str
    predicate: str
    confidence: float
    weight: float
    evidence_text: str = ""
    evidence_episode_id: Optional[str] = None
    created_at: datetime
    last_reinforced_at: datetime


class RelationInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    source_entity: str
    target_entity: str
    predicate: str
    confidence: float = 0.85
    weight: float = 1.0
    evidence_text: str = ""
    evidence_episode_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_reinforced_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
