"""
MongoDB connection management and index initialization for MemNexus.
Supports Motor async driver with graceful in-memory fallback for local development.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

logger = logging.getLogger("mem_nexus.db")

try:
    from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
    MOTOR_AVAILABLE = True
except ImportError:
    MOTOR_AVAILABLE = False
    AsyncIOMotorClient = None
    AsyncIOMotorDatabase = None

from app.config import settings


class InMemoryCollection:
    """Mock in-memory collection providing basic MongoDB-compatible async semantics for offline runs."""
    def __init__(self, name: str):
        self.name = name
        self.docs: List[Dict[str, Any]] = []

    async def insert_one(self, doc: Dict[str, Any]):
        item = dict(doc)
        if "_id" not in item:
            item["_id"] = str(uuid.uuid4())
        self.docs.append(item)
        class Result:
            inserted_id = item["_id"]
        return Result()

    async def find_one(self, query: Dict[str, Any]):
        for d in self.docs:
            match = True
            for k, v in query.items():
                if d.get(k) != v:
                    match = False
                    break
            if match:
                return dict(d)
        return None

    def find(self, query: Optional[Dict[str, Any]] = None):
        filtered = []
        q = query or {}
        for d in self.docs:
            match = True
            for k, v in q.items():
                if isinstance(v, dict) and "$in" in v:
                    if d.get(k) not in v["$in"]:
                        match = False
                        break
                elif d.get(k) != v:
                    match = False
                    break
            if match:
                filtered.append(dict(d))
        
        class Cursor:
            def __init__(self, items):
                self.items = items
            def sort(self, key, direction=1):
                reverse = direction < 0
                self.items = sorted(self.items, key=lambda x: x.get(key) or "", reverse=reverse)
                return self
            def limit(self, n):
                self.items = self.items[:n]
                return self
            async def to_list(self, length=None):
                if length is not None:
                    return self.items[:length]
                return self.items
            def __aiter__(self):
                self._iter = iter(self.items)
                return self
            async def __anext__(self):
                try:
                    return next(self._iter)
                except StopIteration:
                    raise StopAsyncIteration
        return Cursor(filtered)

    async def update_one(self, query: Dict[str, Any], update: Dict[str, Any], upsert: bool = False):
        existing = await self.find_one(query)
        if existing:
            for op, fields in update.items():
                if op == "$set":
                    existing.update(fields)
                elif op == "$inc":
                    for fk, fv in fields.items():
                        existing[fk] = existing.get(fk, 0) + fv
            # update in list
            for i, d in enumerate(self.docs):
                if d["_id"] == existing["_id"]:
                    self.docs[i] = existing
                    break
            class Res:
                matched_count = 1
                modified_count = 1
            return Res()
        elif upsert:
            new_item = dict(query)
            for op, fields in update.items():
                if op == "$set":
                    new_item.update(fields)
            await self.insert_one(new_item)
            class Res:
                matched_count = 0
                modified_count = 0
            return Res()
        class Res:
            matched_count = 0
            modified_count = 0
        return Res()

    async def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        c = self.find(query)
        res = await c.to_list(None)
        return len(res)

    async def create_index(self, keys, **kwargs):
        return "mock_index_created"

    async def delete_many(self, query: Dict[str, Any]):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not all(d.get(k) == v for k, v in query.items())]
        deleted = before - len(self.docs)
        class Res:
            deleted_count = deleted
        return Res()


class InMemoryDatabase:
    """Mock in-memory MongoDB database adapter."""
    def __init__(self, name: str):
        self.name = name
        self.collections: Dict[str, InMemoryCollection] = {}

    def __getitem__(self, item: str) -> InMemoryCollection:
        if item not in self.collections:
            self.collections[item] = InMemoryCollection(item)
        return self.collections[item]

    def get_collection(self, item: str) -> InMemoryCollection:
        return self[item]


class DatabaseManager:
    client: Optional[Any] = None
    db: Optional[Any] = None
    is_fallback: bool = False

    async def connect(self):
        """Establish database connection or initialize mock fallback if offline."""
        if MOTOR_AVAILABLE:
            try:
                self.client = AsyncIOMotorClient(
                    settings.MONGODB_URL,
                    serverSelectionTimeoutMS=1500
                )
                # Verify server ping
                await self.client.admin.command("ping")
                self.db = self.client[settings.DATABASE_NAME]
                self.is_fallback = False
                logger.info(f"Connected to live MongoDB at {settings.MONGODB_URL} (DB: {settings.DATABASE_NAME})")
                await self.init_indexes()
                return
            except Exception as e:
                logger.warning(f"MongoDB live connection failed ({e}). Falling back to in-memory store for development/testing.")

        # In-memory fallback
        self.is_fallback = True
        self.db = InMemoryDatabase(settings.DATABASE_NAME)
        logger.info("Initialized MemNexus in-memory database adapter.")

    async def close(self):
        if self.client and not self.is_fallback:
            self.client.close()
            logger.info("MongoDB connection closed.")

    async def init_indexes(self):
        """Create high-performance indexes for graph traversals and memory decay lookups."""
        if self.is_fallback or self.db is None:
            return

        try:
            # 1. Episodes collection indexes
            episodes = self.db.episodes
            await episodes.create_index([("session_id", 1), ("created_at", -1)])
            await episodes.create_index([("status", 1)])

            # 2. Entities collection indexes
            entities = self.db.entities
            await entities.create_index(
                [("session_id", 1), ("normalized_name", 1)],
                unique=True
            )
            await entities.create_index([("session_id", 1), ("entity_type", 1)])
            await entities.create_index([("importance_score", -1)])

            # 3. Relations collection indexes (critical for $graphLookup and multi-hop queries)
            relations = self.db.relations
            await relations.create_index([("session_id", 1), ("source_entity", 1)])
            await relations.create_index([("session_id", 1), ("target_entity", 1)])
            await relations.create_index([("source_entity", 1), ("target_entity", 1), ("predicate", 1)])
            await relations.create_index([("confidence", -1)])
            logger.info("MongoDB indexes verified successfully.")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")

    def get_collection(self, name: str):
        if self.db is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        return self.db[name]


db_manager = DatabaseManager()


def get_db():
    return db_manager.db
