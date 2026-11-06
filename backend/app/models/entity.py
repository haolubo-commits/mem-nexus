"""
Entity node models representing semantic graph vertices and dynamic importance scores.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    TOOL = "tool"
    CONCEPT = "concept"
    PREFERENCE = "preference"
    LOCATION = "location"
    TASK = "task"
    ATTRIBUTE = "attribute"
    OTHER = "other"


class EntityCreate(BaseModel):
    session_id: str = Field(..., description="Agent or conversation scope")
    name: str = Field(..., min_length=1, description="Entity display label (e.g. 'PostgreSQL')")
    entity_type: EntityType = Field(default=EntityType.CONCEPT, description="Taxonomy classification")
    description: Optional[str] = Field(default="", description="Descriptive summary or role")
    importance_score: float = Field(default=0.7, ge=0.0, le=1.0, description="Base significance weight")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom key-value properties")


class EntityUpdate(BaseModel):
    description: Optional[str] = None
    entity_type: Optional[EntityType] = None
    importance_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    attributes: Optional[Dict[str, Any]] = None


class EntityResponse(BaseModel):
    id: str
    session_id: str
    name: str
    normalized_name: str
    entity_type: EntityType
    description: str = ""
    importance_score: float
    decayed_score: float
    access_count: int = 0
    last_accessed_at: datetime
    created_at: datetime
    attributes: Dict[str, Any] = Field(default_factory=dict)


class EntityInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    name: str
    normalized_name: str
    entity_type: EntityType = EntityType.CONCEPT
    description: str = ""
    importance_score: float = 0.7
    decayed_score: float = 0.7
    access_count: int = 0
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: Dict[str, Any] = Field(default_factory=dict)
