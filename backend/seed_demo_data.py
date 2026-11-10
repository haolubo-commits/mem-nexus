"""
Realistic Demo Data Seeder for MemNexus.
Populates agent interactions, knowledge graph entities, multi-hop relation edges,
and Ebbinghaus decay states for demonstration and testing.
"""

import sys
import os
import asyncio
from datetime import datetime, timezone, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.db.mongodb import db_manager
from app.services.extractor import TripletExtractor
from app.models.episode import EpisodeRole, EpisodeStatus
from app.models.entity import EntityType


DEMO_TURNS = [
    {
        "role": EpisodeRole.USER,
        "content": "Dr. Aris created the distributed consensus engine. Dr. Aris works at DeepMind. The engine relies on Python for orchestration.",
        "tags": ["team", "architecture"],
        "hours_ago": 72,
    },
    {
        "role": EpisodeRole.AGENT,
        "content": "I confirmed the consensus engine specification. Project depends on FastAPI for high-throughput serving and utilizes MongoDB for graph storage.",
        "tags": ["stack", "backend"],
        "hours_ago": 48,
    },
    {
        "role": EpisodeRole.USER,
        "content": "User prefers React over Vue for building the dashboard. The frontend utilizes Tailwind and connects to FastAPI.",
        "tags": ["frontend", "preferences"],
        "hours_ago": 24,
    },
    {
        "role": EpisodeRole.TOOL,
        "content": "Cluster deployment verified. Server is located in us-east-1 and depends on Docker for containerization.",
        "tags": ["devops", "cloud"],
        "hours_ago": 8,
    },
    {
        "role": EpisodeRole.USER,
        "content": "Alice works at OpenAI. Alice authored the evaluation benchmark. Benchmark utilizes Pytest.",
        "tags": ["evals", "team"],
        "hours_ago": 2,
    },
]


async def seed_data(session_id: str = "agent-workspace-alpha"):
    print(f"🌱 Seeding MemNexus demo dataset for session: '{session_id}'...")
    await db_manager.connect()

    episodes_col = db_manager.get_collection("episodes")
    entities_col = db_manager.get_collection("entities")
    relations_col = db_manager.get_collection("relations")

    # Clean existing session
    await episodes_col.delete_many({"session_id": session_id})
    await entities_col.delete_many({"session_id": session_id})
    await relations_col.delete_many({"session_id": session_id})

    now = datetime.now(timezone.utc)

    for idx, turn in enumerate(DEMO_TURNS):
        created_time = now - timedelta(hours=turn["hours_ago"])
        triplets = TripletExtractor.extract(turn["content"])

        # Insert episode
        ep_id = f"demo_ep_{idx + 1}"
        await episodes_col.insert_one({
            "_id": ep_id,
            "session_id": session_id,
            "role": turn["role"].value,
            "content": turn["content"],
            "extracted_triplets_count": len(triplets),
            "importance_score": 0.8,
            "status": EpisodeStatus.PROCESSED.value,
            "created_at": created_time,
            "tags": turn["tags"],
            "metadata": {"seed": True},
        })

        # Upsert entities & relations
        for t in triplets:
            norm_src = TripletExtractor.normalize_name(t.source)
            await entities_col.update_one(
                {"session_id": session_id, "normalized_name": norm_src},
                {
                    "$set": {
                        "name": t.source,
                        "normalized_name": norm_src,
                        "entity_type": t.source_type.value,
                        "last_accessed_at": created_time,
                    },
                    "$setOnInsert": {
                        "_id": f"ent_{norm_src}",
                        "session_id": session_id,
                        "description": f"Extracted from {turn['role'].value} turn",
                        "importance_score": 0.75,
                        "access_count": 1,
                        "created_at": created_time,
                        "attributes": {},
                    }
                },
                upsert=True
            )

            norm_tgt = TripletExtractor.normalize_name(t.target)
            await entities_col.update_one(
                {"session_id": session_id, "normalized_name": norm_tgt},
                {
                    "$set": {
                        "name": t.target,
                        "normalized_name": norm_tgt,
                        "entity_type": t.target_type.value,
                        "last_accessed_at": created_time,
                    },
                    "$setOnInsert": {
                        "_id": f"ent_{norm_tgt}",
                        "session_id": session_id,
                        "description": f"Extracted from {turn['role'].value} turn",
                        "importance_score": 0.75,
                        "access_count": 1,
                        "created_at": created_time,
                        "attributes": {},
                    }
                },
                upsert=True
            )

            await relations_col.update_one(
                {
                    "session_id": session_id,
                    "source_entity": t.source,
                    "target_entity": t.target,
                    "predicate": t.predicate,
                },
                {
                    "$set": {
                        "confidence": t.confidence,
                        "evidence_text": t.evidence,
                        "evidence_episode_id": ep_id,
                        "last_reinforced_at": created_time,
                    },
                    "$inc": {"weight": 0.5},
                    "$setOnInsert": {
                        "_id": f"rel_{norm_src}_{norm_tgt}_{t.predicate}",
                        "session_id": session_id,
                        "source_entity": t.source,
                        "target_entity": t.target,
                        "predicate": t.predicate,
                        "created_at": created_time,
                    }
                },
                upsert=True
            )

    total_ep = await episodes_col.count_documents({"session_id": session_id})
    total_ent = await entities_col.count_documents({"session_id": session_id})
    total_rel = await relations_col.count_documents({"session_id": session_id})

    print(f"✅ Seeding complete:")
    print(f"   • {total_ep} Episodic Turns")
    print(f"   • {total_ent} Knowledge Graph Entities")
    print(f"   • {total_rel} Multi-Hop Relational Edges")
    await db_manager.close()


if __name__ == "__main__":
    asyncio.run(seed_data())
