"""Log Miner for Thelawala Search.

Extracts customer behavioral signals from search_log.jsonl:
- Query-to-SKU conversion frequencies (clicks and add_to_cart)
- Global SKU popularity scores
- Recovery mappings from browse sessions following zero-result searches
"""

import json
import os
from collections import defaultdict, Counter
from typing import Dict, Tuple

class SearchLogSignals:
    def __init__(
        self,
        query_sku_scores: Dict[str, Dict[str, float]],
        global_sku_scores: Dict[str, float]
    ):
        self.query_sku_scores = query_sku_scores
        self.global_sku_scores = global_sku_scores

    def get_query_boost(self, query: str, sku_id: str) -> float:
        """Returns the learned relevance boost for a query-SKU pair."""
        q = query.strip().lower()
        if q in self.query_sku_scores and sku_id in self.query_sku_scores[q]:
            raw_score = self.query_sku_scores[q][sku_id]
            # Logarithmic dampening to prevent outlier overfitting
            import math
            return round(math.log1p(raw_score) * 2.5, 3)
        return 0.0

    def get_popularity_boost(self, sku_id: str) -> float:
        """Returns a normalized global popularity boost for an SKU."""
        raw = self.global_sku_scores.get(sku_id, 0.0)
        if raw <= 0:
            return 0.0
        import math
        return round(math.log1p(raw) * 0.4, 3)


def mine_search_logs(
    log_path: str = "thelawala-search-data/search_log.jsonl"
) -> SearchLogSignals:
    """Parses search_log.jsonl and extracts historical conversion priors."""
    query_sku_scores: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
    global_sku_scores: Dict[str, float] = defaultdict(float)

    if not os.path.exists(log_path):
        return SearchLogSignals({}, {})

    with open(log_path, mode="r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            raw_q = record.get("query", "").strip().lower()
            if not raw_q:
                continue

            events = record.get("events", [])
            for ev in events:
                sku_id = ev.get("sku_id")
                if not sku_id:
                    continue
                action = ev.get("action", "")
                
                # Weight add-to-cart higher than simple click
                weight = 3.0 if action == "add_to_cart" else 1.0

                query_sku_scores[raw_q][sku_id] += weight
                global_sku_scores[sku_id] += weight

    # Convert inner defaultdict to regular dict
    final_query_scores = {q: dict(skus) for q, skus in query_sku_scores.items()}
    final_global_scores = dict(global_sku_scores)

    return SearchLogSignals(
        query_sku_scores=final_query_scores,
        global_sku_scores=final_global_scores
    )
