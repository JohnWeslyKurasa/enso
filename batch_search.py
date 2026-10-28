"""Batch Search Runner for Thelawala Search.

Usage:
    python batch_search.py <input_queries.txt> [output_results.jsonl]

Specification:
    Takes a text file with one query per line.
    Writes a jsonl file with lines:
    {"query": "...", "results": ["sku_id", "sku_id", ...]}
    results holds up to 10 sku_ids, best first.
"""

import sys
import json
import os
import time
from thelawala_search.engine import ThelawalaSearchEngine

def run_batch(input_file: str, output_file: str = "results.jsonl") -> None:
    if not os.path.exists(input_file):
        print(f"Error: Input queries file '{input_file}' not found.")
        sys.exit(1)

    print(f"Initializing Thelawala Search Engine...")
    t0 = time.time()
    engine = ThelawalaSearchEngine()
    engine.initialize()

    print(f"Reading queries from '{input_file}'...")
    queries = []
    with open(input_file, mode="r", encoding="utf-8") as f:
        for line in f:
            q = line.strip()
            if q:
                queries.append(q)

    print(f"Processing {len(queries)} queries...")
    t_start = time.time()
    processed_count = 0

    with open(output_file, mode="w", encoding="utf-8") as out:
        for q in queries:
            sku_ids = engine.search_sku_ids(q, top_k=10)
            record = {
                "query": q,
                "results": sku_ids
            }
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            processed_count += 1

    duration = time.time() - t_start
    qps = processed_count / max(0.001, duration)
    print(f"Successfully processed {processed_count} queries in {duration:.2f}s ({qps:.1f} queries/sec).")
    print(f"Batch results saved to '{output_file}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_search.py <queries_file> [output_file]")
        sys.exit(1)

    inp = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "results.jsonl"
    run_batch(inp, out)
