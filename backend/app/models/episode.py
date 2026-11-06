"""
Episodic memory schemas and validation models.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class EpisodeRole(str, Enum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"


class EpisodeStatus(str, Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    ARCHIVED = "archived"


class EpisodeCreate(BaseModel):
    session_id: str = Field(..., description="Unique session or agent workspace identifier")
    role: EpisodeRole = Field(default=EpisodeRole.USER, description="Actor role for the episode turn")
    content: str = Field(..., min_length=1, description="Raw interaction turn content")
    importance_hint: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Optional manual importance prior")
    tags: List[str] = Field(default_factory=list, description="Categorical tags (e.g. ['code', 'preference'])")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom contextual metadata")


class EpisodeResponse(BaseModel):
    id: str = Field(..., description="Unique episode ID")
    session_id: str
    role: EpisodeRole
    content: str
    extracted_triplets_count: int = 0
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    status: EpisodeStatus = EpisodeStatus.PROCESSED
    created_at: datetime
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EpisodeInDB(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: EpisodeRole
    content: str
    extracted_triplets_count: int = 0
    importance_score: float = 0.5
    status: EpisodeStatus = EpisodeStatus.PROCESSED
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
