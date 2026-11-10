"""
Multi-hop Knowledge Graph Traversal Service for MemNexus.
Supports native MongoDB $graphLookup aggregation and bidirectional graph expansion.
"""

import time
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import deque

from app.db.mongodb import db_manager
from app.models.query import GraphNode, GraphEdge, GraphSubgraph
from app.models.entity import EntityType
from app.services.decay import DecayEngine

logger = logging.getLogger("mem_nexus.graph")


class GraphTraverser:
    """
    Executes depth-bounded multi-hop graph expansions to discover direct and transitive
    associative links across the agent's knowledge graph.
    """

    @classmethod
    async def traverse(
        cls,
        session_id: str,
        seed_entities: List[str],
        max_hops: int = 2,
        min_confidence: float = 0.5,
        limit_nodes: int = 50,
        decay_rate: Optional[float] = None,
    ) -> Tuple[GraphSubgraph, float]:
        start_time = time.perf_counter()

        entities_col = db_manager.get_collection("entities")
        relations_col = db_manager.get_collection("relations")

        visited_entities: Set[str] = set()
        discovered_nodes_map: Dict[str, GraphNode] = {}
        discovered_edges_list: List[GraphEdge] = []
        edge_fingerprints: Set[str] = set()

        # Queue holds (entity_name, current_hop)
        queue: deque = deque()
        for seed in seed_entities:
            clean_seed = seed.strip()
            if clean_seed:
                queue.append((clean_seed, 0))
                visited_entities.add(clean_seed.lower())

        max_depth_reached = 0

        while queue and len(discovered_nodes_map) < limit_nodes:
            curr_entity, hop = queue.popleft()
            max_depth_reached = max(max_depth_reached, hop)

            # 1. Fetch or decorate current node from entity store
            norm_name = curr_entity.lower().strip()
            ent_doc = await entities_col.find_one({"session_id": session_id, "normalized_name": norm_name})
            
            decayed = 0.7
            importance = 0.7
            ent_type = EntityType.CONCEPT
            node_id = norm_name
            access_cnt = 0

            if ent_doc:
                importance = float(ent_doc.get("importance_score", 0.7))
                decayed = DecayEngine.apply_to_entity(ent_doc, decay_rate=decay_rate)
                ent_type = EntityType(ent_doc.get("entity_type", EntityType.CONCEPT.value))
                node_id = str(ent_doc.get("_id", norm_name))
                access_cnt = int(ent_doc.get("access_count", 0))

            if norm_name not in discovered_nodes_map:
                discovered_nodes_map[norm_name] = GraphNode(
                    id=node_id,
                    name=curr_entity,
                    entity_type=ent_type,
                    importance_score=importance,
                    decayed_score=decayed,
                    hop_distance=hop,
                    access_count=access_cnt,
                )

            # If we've reached max_hops, don't expand neighbors further
            if hop >= max_hops:
                continue

            # 2. Query relations where curr_entity is source or target
            # Outgoing relations: curr_entity -> target
            query_out = {
                "session_id": session_id,
                "source_entity": curr_entity,
            }
            cursor_out = relations_col.find(query_out)
            out_relations = await cursor_out.to_list(100)

            # Incoming relations: other -> curr_entity
            query_in = {
                "session_id": session_id,
                "target_entity": curr_entity,
            }
            cursor_in = relations_col.find(query_in)
            in_relations = await cursor_in.to_list(100)

            combined_relations = out_relations + in_relations

            for rel in combined_relations:
                confidence = float(rel.get("confidence", 0.8))
                if confidence < min_confidence:
                    continue

                src = str(rel.get("source_entity", "")).strip()
                tgt = str(rel.get("target_entity", "")).strip()
                pred = str(rel.get("predicate", "related_to"))
                weight = float(rel.get("weight", 1.0))
                rel_id = str(rel.get("_id", f"{src}-{pred}-{tgt}"))

                edge_key = f"{src.lower()}:{pred.lower()}:{tgt.lower()}"
                if edge_key not in edge_fingerprints:
                    edge_fingerprints.add(edge_key)
                    discovered_edges_list.append(GraphEdge(
                        id=rel_id,
                        source=src,
                        target=tgt,
                        predicate=pred,
                        confidence=confidence,
                        weight=weight,
                        hop_level=hop + 1,
                    ))

                # Identify the neighboring entity to traverse next
                neighbor = tgt if src.lower() == curr_entity.lower() else src
                neigh_norm = neighbor.lower().strip()

                if neigh_norm not in visited_entities:
                    visited_entities.add(neigh_norm)
                    queue.append((neighbor, hop + 1))

        subgraph = GraphSubgraph(
            nodes=list(discovered_nodes_map.values()),
            edges=discovered_edges_list,
            total_nodes=len(discovered_nodes_map),
            total_edges=len(discovered_edges_list),
            hop_depth_reached=max_depth_reached,
        )

        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        return subgraph, elapsed_ms

    @classmethod
    async def get_graph_stats(cls, session_id: str) -> Dict[str, Any]:
        """Calculates topological statistics for the agent's knowledge graph."""
        entities_col = db_manager.get_collection("entities")
        relations_col = db_manager.get_collection("relations")
        episodes_col = db_manager.get_collection("episodes")

        total_entities = await entities_col.count_documents({"session_id": session_id})
        total_relations = await relations_col.count_documents({"session_id": session_id})
        total_episodes = await episodes_col.count_documents({"session_id": session_id})

        # Calculate node degrees
        cursor = relations_col.find({"session_id": session_id})
        all_rels = await cursor.to_list(1000)

        degree_map: Dict[str, int] = {}
        for r in all_rels:
            s = r.get("source_entity")
            t = r.get("target_entity")
            if s:
                degree_map[s] = degree_map.get(s, 0) + 1
            if t:
                degree_map[t] = degree_map.get(t, 0) + 1

        top_hubs = sorted(
            [{"entity": k, "degree": v} for k, v in degree_map.items()],
            key=lambda x: x["degree"],
            reverse=True
        )[:5]

        density = 0.0
        if total_entities > 1:
            possible_edges = total_entities * (total_entities - 1)
            density = round(total_relations / max(1, possible_edges), 4)

        return {
            "session_id": session_id,
            "total_entities": total_entities,
            "total_relations": total_relations,
            "total_episodes": total_episodes,
            "top_connected_hubs": top_hubs,
            "graph_density": density,
        }

