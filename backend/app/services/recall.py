"""
Context Recall & Consolidation Service for MemNexus.
Synthesizes multi-hop subgraphs into prompt-ready context blocks for LLM agents.
"""

import time
import re
from datetime import datetime, timezone
from typing import List, Optional, Set
from app.db.mongodb import db_manager
from app.models.query import (
    MemoryRecallRequest,
    MemoryRecallResponse,
    GraphSubgraph,
)
from app.services.graph import GraphTraverser
from app.services.decay import DecayEngine


class RecallConsolidator:
    """
    Coordinates associative entity discovery, multi-hop relation traversal,
    memory reinforcement, and prompt context synthesis.
    """

    @classmethod
    async def extract_query_seeds(cls, session_id: str, query_text: str) -> List[str]:
        """Detect known entity mentions in the query string."""
        entities_col = db_manager.get_collection("entities")
        cursor = entities_col.find({"session_id": session_id})
        all_entities = await cursor.to_list(200)

        seeds: List[str] = []
        tokens = set(re.findall(r"[a-zA-Z0-9_\-]+", query_text.lower()))

        for ent in all_entities:
            norm = ent.get("normalized_name", "").lower()
            name = ent.get("name", "")
            if norm in tokens or name.lower() in query_text.lower():
                seeds.append(name)

        return seeds

    @classmethod
    async def reinforce_recalled_nodes(cls, session_id: str, node_names: List[str]):
        """Boost access count and update last_accessed_at for recalled entities."""
        if not node_names:
            return

        entities_col = db_manager.get_collection("entities")
        now = datetime.now(timezone.utc)

        for name in node_names:
            norm = name.lower().strip()
            await entities_col.update_one(
                {"session_id": session_id, "normalized_name": norm},
                {
                    "$inc": {"access_count": 1},
                    "$set": {"last_accessed_at": now}
                }
            )

    @classmethod
    async def recall(cls, req: MemoryRecallRequest) -> MemoryRecallResponse:
        start_time = time.perf_counter()

        seeds = list(req.seed_entities or [])
        detected_seeds = await cls.extract_query_seeds(req.session_id, req.query_text)
        
        # Combine unique seeds
        for d in detected_seeds:
            if d not in seeds:
                seeds.append(d)

        # Fallback if no specific entity matched: pick top importance entities in session
        if not seeds:
            entities_col = db_manager.get_collection("entities")
            top_cursor = entities_col.find({"session_id": req.session_id}).sort("importance_score", -1).limit(3)
            top_docs = await top_cursor.to_list(3)
            seeds = [d.get("name") for d in top_docs if d.get("name")]

        subgraph: Optional[GraphSubgraph] = None
        recalled_facts: List[str] = []
        node_names: List[str] = []

        if seeds:
            subgraph, _ = await GraphTraverser.traverse(
                session_id=req.session_id,
                seed_entities=seeds,
                max_hops=req.max_hops,
                min_confidence=req.min_confidence,
                decay_rate=req.decay_rate,
            )

            # Format relational facts
            for edge in subgraph.edges:
                fact_str = f"{edge.source} {edge.predicate} {edge.target} (conf: {edge.confidence:.2f})"
                recalled_facts.append(fact_str)

            node_names = [n.name for n in subgraph.nodes]

            # Reinforce memory access
            await cls.reinforce_recalled_nodes(req.session_id, node_names)

        # Assemble clean, compact LLM prompt context block
        context_lines = [
            "=== RECALLED MEMNEXUS KNOWLEDGE GRAPH CONTEXT ===",
            f"Active Session: {req.session_id}",
            f"Query Prompt: \"{req.query_text}\"",
        ]

        if seeds:
            context_lines.append(f"Anchor Seeds: {', '.join(seeds)}")

        if subgraph and subgraph.nodes:
            context_lines.append(
                f"Recalled Subgraph: {subgraph.total_nodes} entities, "
                f"{subgraph.total_edges} relations ({subgraph.hop_depth_reached}-hop depth)"
            )
            context_lines.append("\nAssociative Facts:")
            for fact in recalled_facts[:12]:
                context_lines.append(f"  • {fact}")

            context_lines.append("\nEntity State & Memory Decay:")
            # Sort nodes by decayed score descending
            sorted_nodes = sorted(subgraph.nodes, key=lambda n: n.decayed_score, reverse=True)
            for node in sorted_nodes[:8]:
                context_lines.append(
                    f"  • {node.name} [{node.entity_type.value}] "
                    f"— decayed retention: {node.decayed_score:.2f}, accesses: {node.access_count}"
                )
        else:
            context_lines.append("No related graph memories located for this query.")

        context_lines.append("==================================================")
        assembled_context = "\n".join(context_lines)

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)

        return MemoryRecallResponse(
            session_id=req.session_id,
            query=req.query_text,
            matched_entities=seeds,
            recalled_facts=recalled_facts,
            assembled_context=assembled_context,
            subgraph=subgraph if req.include_subgraph else None,
            execution_time_ms=elapsed_ms,
        )

