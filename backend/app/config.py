"""
Application configuration for MemNexus using Pydantic Settings.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True
    )

    PROJECT_NAME: str = "MemNexus"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "Long-Term Episodic Memory & Knowledge Graph Engine for AI Agents"
    API_V1_PREFIX: str = "/api/v1"
    
    # MongoDB Settings
    MONGODB_URL: str = Field(default="mongodb://localhost:27017", validation_alias="MONGODB_URL")
    DATABASE_NAME: str = Field(default="mem_nexus_db", validation_alias="DATABASE_NAME")
    
    # Memory Decay & Graph Settings
    DEFAULT_DECAY_RATE: float = 0.05  # lambda decay parameter in Ebbinghaus curve
    REINFORCEMENT_BOOST_FACTOR: float = 0.15  # weight for access count boost
    DEFAULT_MAX_HOPS: int = 3
    MIN_CONFIDENCE_THRESHOLD: float = 0.6
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
