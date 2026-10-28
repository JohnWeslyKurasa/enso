"""Core ThelawalaSearchEngine Interface.

Connects data loading, indexing, query parsing, synonym expansion, and multi-signal ranking.
"""

import time
from typing import List, Dict, Any, Optional
from thelawala_search.data_loader import load_catalog_and_inventory, Product
from thelawala_search.query_parser import parse_query, ParsedQuery
from thelawala_search.vocabulary import expand_query_synonyms
from thelawala_search.log_miner import mine_search_logs, SearchLogSignals
from thelawala_search.indexer import BM25Index, tokenize
from thelawala_search.ranker import rank_candidates, RankedResult

class ThelawalaSearchEngine:
    def __init__(
        self,
        catalog_path: str = "thelawala-search-data/catalog.csv",
        inventory_path: str = "thelawala-search-data/inventory.csv",
        log_path: str = "thelawala-search-data/search_log.jsonl"
    ):
        self.catalog_path = catalog_path
        self.inventory_path = inventory_path
        self.log_path = log_path
        
        self.products: Dict[str, Product] = {}
        self.index = BM25Index()
        self.signals = SearchLogSignals({}, {})
        self.is_ready = False

    def initialize(self) -> None:
        """Loads data, trains search priors from logs, and builds BM25 index."""
        t0 = time.time()
        print("Loading catalog and inventory...")
        self.products = load_catalog_and_inventory(
            catalog_path=self.catalog_path,
            inventory_path=self.inventory_path
        )
        print(f"Loaded {len(self.products)} active products (discontinued items filtered).")

        print("Mining search logs for behavioral click/cart signals...")
        self.signals = mine_search_logs(self.log_path)
        print(f"Mined signals across {len(self.signals.query_sku_scores)} query patterns.")

        print("Building in-memory BM25 index with typo tolerance...")
        self.index.build_index(self.products)
        self.is_ready = True
        print(f"Index built in {time.time() - t0:.2f}s. Total searchable vocabulary: {len(self.index.vocabulary)} words.")

    def search(self, raw_query: str, top_k: int = 10) -> List[RankedResult]:
        """Executes a search query and returns ranked results."""
        if not self.is_ready:
            self.initialize()

        # Step 1: Parse query for price constraints and clean tokens
        parsed = parse_query(raw_query)
        if not parsed.clean_query:
            return []

        # Step 2: Expand Telugu, Hinglish, and colloquial synonyms
        expanded_query_str = expand_query_synonyms(parsed.clean_query)
        expanded_tokens = tokenize(expanded_query_str)

        # Step 3: Compute BM25 scores
        bm25_scores = self.index.score_bm25(expanded_tokens)

        # Step 4: Multi-signal ranking
        results = rank_candidates(
            products=self.products,
            bm25_scores=bm25_scores,
            parsed_query=parsed,
            signals=self.signals,
            top_k=top_k
        )
        return results

    def search_sku_ids(self, raw_query: str, top_k: int = 10) -> List[str]:
        """Returns just the list of top SKU IDs for batch evaluation."""
        results = self.search(raw_query, top_k=top_k)
        return [r.sku_id for r in results]
