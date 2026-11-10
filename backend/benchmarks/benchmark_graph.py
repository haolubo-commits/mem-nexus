"""
MemNexus Multi-Hop Knowledge Graph & Memory Decay Benchmark Suite.
Profiles 1-hop, 2-hop, and 3-hop associative graph retrieval latencies and Ebbinghaus throughput.
"""

import sys
import os
import time
import statistics
import asyncio
from datetime import datetime, timezone, timedelta

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.decay import DecayEngine
from app.services.extractor import TripletExtractor
from app.services.graph import GraphTraverser
from app.db.mongodb import db_manager


async def benchmark_ebbinghaus_decay(iterations: int = 50_000):
    print("=" * 65)
    print(f" 1. Ebbinghaus Memory Decay Math Throughput ({iterations:,} iterations)")
    print("=" * 65)

    base_time = datetime.now(timezone.utc)
    times = [base_time - timedelta(hours=i % 720) for i in range(1000)]

    start = time.perf_counter()
    for i in range(iterations):
        t = times[i % 1000]
        _ = DecayEngine.compute_decay(
            base_importance=0.85,
            last_accessed_at=t,
            access_count=i % 15,
            current_time=base_time,
            decay_rate=0.05,
        )
    elapsed = time.perf_counter() - start
    ops_sec = iterations / elapsed
    avg_us = (elapsed / iterations) * 1_000_000

    print(f"Total Time : {elapsed:.4f}s")
    print(f"Throughput : {ops_sec:,.1f} evaluations/sec")
    print(f"Avg Latency: {avg_us:.3f} µs/op")
    print("-" * 65)
    return ops_sec, avg_us


async def benchmark_triplet_extraction(iterations: int = 5_000):
    print("\n" + "=" * 65)
    print(f" 2. Heuristic Triplet & Entity Extraction ({iterations:,} turns)")
    print("=" * 65)

    sample_texts = [
        "User prefers Python and Rust over Java for systems programming.",
        "The distributed worker relies on Redis and connects to PostgreSQL for transactions.",
        "Dr. Aris authored the distributed consensus paper. Aris works at DeepMind.",
        "Production cluster is located in us-east-1 and utilizes Kubernetes for orchestration.",
        "Agent interacts with User. Service connects to Database. Database version is 16.",
    ]

    start = time.perf_counter()
    total_triplets = 0
    for i in range(iterations):
        t = sample_texts[i % len(sample_texts)]
        triplets = TripletExtractor.extract(t)
        total_triplets += len(triplets)
    elapsed = time.perf_counter() - start
    ops_sec = iterations / elapsed
    avg_us = (elapsed / iterations) * 1_000_000

    print(f"Total Time      : {elapsed:.4f}s")
    print(f"Total Triplets  : {total_triplets:,}")
    print(f"Throughput      : {ops_sec:,.1f} turns/sec")
    print(f"Avg Turn Latency: {avg_us:.3f} µs/turn")
    print("-" * 65)
    return ops_sec, avg_us


async def benchmark_graph_traversal():
    print("\n" + "=" * 65)
    print(" 3. Multi-Hop Graph Traversal Latency by Hop Depth")
    print("=" * 65)

    await db_manager.connect()
    session_id = "bench-graph-cluster"

    entities_col = db_manager.get_collection("entities")
    relations_col = db_manager.get_collection("relations")

    # Clean existing benchmark data
    await entities_col.delete_many({"session_id": session_id})
    await relations_col.delete_many({"session_id": session_id})

    # Build a synthetic dense graph (120 entities, ~250 directed relations)
    print("Populating synthetic interconnected knowledge graph...")
    now = datetime.now(timezone.utc)
    for i in range(120):
        name = f"Node_{i}"
        await entities_col.insert_one({
            "_id": f"ent_{i}",
            "session_id": session_id,
            "name": name,
            "normalized_name": name.lower(),
            "entity_type": "concept",
            "importance_score": 0.5 + (i % 5) * 0.1,
            "access_count": i % 10,
            "last_accessed_at": now - timedelta(hours=i),
            "created_at": now,
            "attributes": {},
        })

    # Interconnect edges
    predicates = ["depends_on", "relates_to", "author_of", "part_of", "prefers"]
    for i in range(120):
        # Connect to next node (linear chain)
        next_i = (i + 1) % 120
        await relations_col.insert_one({
            "_id": f"rel_chain_{i}",
            "session_id": session_id,
            "source_entity": f"Node_{i}",
            "target_entity": f"Node_{next_i}",
            "predicate": predicates[i % len(predicates)],
            "confidence": 0.85,
            "weight": 1.0,
            "created_at": now,
            "last_reinforced_at": now,
        })
        # Connect cross-hub shortcuts
        cross_i = (i * 3 + 7) % 120
        if cross_i != i:
            await relations_col.insert_one({
                "_id": f"rel_cross_{i}",
                "session_id": session_id,
                "source_entity": f"Node_{i}",
                "target_entity": f"Node_{cross_i}",
                "predicate": "cross_links",
                "confidence": 0.80,
                "weight": 1.5,
                "created_at": now,
                "last_reinforced_at": now,
            })

    hop_tests = [1, 2, 3]
    trials = 250

    print(f"Running {trials} randomized trials per hop depth...")
    print(f"{'Hops':<6} | {'Avg Nodes':<10} | {'Avg Edges':<10} | {'p50 (ms)':<10} | {'p95 (ms)':<10} | {'Throughput (qps)':<15}")
    print("-" * 72)

    for hops in hop_tests:
        latencies = []
        node_counts = []
        edge_counts = []

        for trial in range(trials):
            seed = f"Node_{(trial * 17) % 120}"
            subgraph, elapsed_ms = await GraphTraverser.traverse(
                session_id=session_id,
                seed_entities=[seed],
                max_hops=hops,
                min_confidence=0.6,
                limit_nodes=50,
            )
            latencies.append(elapsed_ms)
            node_counts.append(subgraph.total_nodes)
            edge_counts.append(subgraph.total_edges)

        latencies.sort()
        p50 = latencies[int(len(latencies) * 0.50)]
        p95 = latencies[int(len(latencies) * 0.95)]
        avg_nodes = statistics.mean(node_counts)
        avg_edges = statistics.mean(edge_counts)
        qps = 1000.0 / statistics.mean(latencies) if statistics.mean(latencies) > 0 else 0

        print(f"{hops:<6} | {avg_nodes:<10.1f} | {avg_edges:<10.1f} | {p50:<10.3f} | {p95:<10.3f} | {qps:<15.1f}")

    print("-" * 72)
    await db_manager.close()


async def main():
    print("\n🚀 Starting MemNexus Benchmarking Suite...\n")
    await benchmark_ebbinghaus_decay()
    await benchmark_triplet_extraction()
    await benchmark_graph_traversal()
    print("\n✅ All benchmarks completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(main())

