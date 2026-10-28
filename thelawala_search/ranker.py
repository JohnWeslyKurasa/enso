"""Multi-Signal Search Ranker for Thelawala Search.

Balances:
- BM25 text relevance and token overlap
- Intent precision (e.g., 'milk' prioritizes fresh drinking milk over chocolates/powder)
- Brand intent protection (Kavya's rule: customer first, margin second)
- Private label boost for Thela Select on generic queries (Farah's rule)
- Historical search log click & cart priors
- Price constraint enforcement (e.g., 'oil under 200')
- Stock hierarchy (in-stock items rank first; out-of-stock items at bottom with restock notice)
"""

from typing import List, Dict, Tuple, Optional
from thelawala_search.data_loader import Product
from thelawala_search.query_parser import ParsedQuery
from thelawala_search.log_miner import SearchLogSignals
from thelawala_search.vocabulary import KNOWN_BRANDS

class RankedResult:
    def __init__(
        self,
        product: Product,
        total_score: float,
        relevance_score: float,
        popularity_score: float,
        stock_status: str,
        score_breakdown: Dict[str, float]
    ):
        self.product = product
        self.sku_id = product.sku_id
        self.total_score = total_score
        self.relevance_score = relevance_score
        self.popularity_score = popularity_score
        self.stock_status = stock_status
        self.score_breakdown = score_breakdown

    def to_dict(self) -> Dict:
        return {
            "sku_id": self.sku_id,
            "name": self.product.name,
            "brand": self.product.brand,
            "category": self.product.category,
            "size": self.product.size,
            "price": self.product.price,
            "stock_qty": self.product.stock_qty,
            "is_in_stock": self.product.is_in_stock,
            "restock_eta": self.product.restock_eta,
            "total_score": round(self.total_score, 3),
            "score_breakdown": self.score_breakdown
        }


def rank_candidates(
    products: Dict[str, Product],
    bm25_scores: Dict[str, float],
    parsed_query: ParsedQuery,
    signals: SearchLogSignals,
    top_k: int = 10
) -> List[RankedResult]:
    """Ranks candidate products using the multi-signal scoring pipeline."""
    clean_q = parsed_query.clean_query.lower()
    query_tokens = set(parsed_query.tokens)

    # 1. Detect if user requested a specific brand
    requested_brand: Optional[str] = None
    for brand in KNOWN_BRANDS:
        if brand in clean_q:
            requested_brand = brand
            break

    # 2. Identify key query intents
    is_pure_milk_query = clean_q in {"milk", "paalu", "doodh", "fresh milk", "milk packet", "packet milk"}
    is_pure_butter_query = clean_q in {"butter", "venna", "table butter"}
    is_pure_oil_query = clean_q in {"oil", "refined oil", "cooking oil", "nune"}
    is_ghee_query = "ghee" in clean_q or "neyyi" in clean_q
    is_atta_query = clean_q in {"atta", "wheat atta", "flour"}

    candidates: List[RankedResult] = []

    # Iterate through products with positive BM25 scores or historical query matches
    candidate_skus = set(bm25_scores.keys())
    # Add historical query-converted SKUs even if BM25 missed them
    if clean_q in signals.query_sku_scores:
        candidate_skus.update(signals.query_sku_scores[clean_q].keys())

    for sku_id in candidate_skus:
        prod = products.get(sku_id)
        if not prod or prod.is_discontinued:
            continue

        # Price constraints
        if parsed_query.max_price is not None and prod.price > parsed_query.max_price:
            continue
        if parsed_query.min_price is not None and prod.price < parsed_query.min_price:
            continue

        breakdown: Dict[str, float] = {}

        # Signal 1: Base BM25 relevance
        base_bm25 = bm25_scores.get(sku_id, 0.0)
        breakdown["bm25"] = base_bm25
        score = base_bm25

        # Signal 2: Token match & exact phrasing
        prod_name_lower = prod.name.lower()
        prod_brand_lower = prod.brand.lower()
        prod_cat_lower = prod.category.lower()

        # Exact product name match boost
        if clean_q == prod_name_lower:
            score += 8.0
            breakdown["exact_name_match"] = 8.0
        elif clean_q in prod_name_lower:
            score += 4.0
            breakdown["phrase_in_name"] = 4.0

        # All-tokens match boost
        prod_all_text = f"{prod_name_lower} {prod_brand_lower} {prod_cat_lower}"
        if all(t in prod_all_text for t in query_tokens):
            score += 3.0
            breakdown["all_tokens_match"] = 3.0

        # Signal 3: Intent Disambiguation (The "Milk" problem & similar)
        if is_pure_milk_query:
            # Fresh drinking milk is in 'Dairy & Eggs' and has milk in name
            if prod.category == "Dairy & Eggs":
                if any(k in prod_name_lower for k in ["powder", "pwdr"]):
                    score -= 8.0  # Powder is not liquid milk
                elif "buttermilk" in prod_name_lower:
                    score -= 10.0 # Buttermilk is not milk
                elif any(m in prod_name_lower for m in ["full cream milk", "toned milk", "double toned milk", "buffalo milk", "cow milk", "milk 1 l", "milk 500 ml", "milk 1ltr"]):
                    score += 12.0 # Prime liquid drinking milk packets
                    breakdown["fresh_milk_intent"] = 12.0
            else:
                # Chocolate, biscuits, etc.
                if any(c in prod_name_lower for c in ["chocolate", "biscuit", "rusk", "cake"]):
                    score -= 15.0 # Severe penalty for chocolate/biscuits when searching 'milk'

        elif is_pure_butter_query:
            if "peanut butter" in prod_name_lower:
                score -= 8.0
            elif "buttermilk" in prod_name_lower:
                score -= 10.0
            elif prod.category == "Dairy & Eggs" and "butter" in prod_name_lower:
                score += 10.0
                breakdown["butter_intent"] = 10.0

        elif is_pure_oil_query:
            if prod.category == "Oils & Ghee" and any(k in prod_name_lower for k in ["sunflower", "groundnut", "oil"]):
                score += 8.0
                breakdown["cooking_oil_intent"] = 8.0

        # Signal 4: Brand Intent Protection (Kavya's rule: Customer first, margin second)
        if requested_brand:
            if requested_brand in prod_brand_lower or requested_brand in prod_name_lower:
                score += 10.0
                breakdown["brand_match_boost"] = 10.0
            else:
                score -= 5.0  # De-rank other brands if user explicitly named one

        # Signal 5: Private Label ("Thela Select" - Farah's rule)
        # Only boost if user did NOT explicitly ask for a competitor brand
        if prod.is_private_label:
            if requested_brand and requested_brand not in ["thela select", "thela"]:
                pass  # Do NOT boost private label if customer asked for Amul/Godavari/etc.
            else:
                score += 1.8
                breakdown["thela_select_margin_boost"] = 1.8

        # Signal 6: Historical Search Log CTR / Conversions
        query_boost = signals.get_query_boost(clean_q, sku_id)
        if query_boost > 0:
            score += query_boost
            breakdown["historical_query_conversion"] = query_boost

        pop_boost = signals.get_popularity_boost(sku_id)
        if pop_boost > 0:
            score += pop_boost
            breakdown["global_popularity"] = pop_boost

        # Signal 7: Stock Hierarchy (Sandeep vs Farah resolution)
        # In-stock items receive heavy priority (+100.0) over out-of-stock items (+0.0)
        # Out-of-stock items remain in results, placed gracefully below in-stock options
        if prod.is_in_stock:
            score += 100.0
            breakdown["in_stock_boost"] = 100.0
            status_desc = "In Stock"
        else:
            status_desc = f"Out of Stock (Restock: {prod.restock_eta or 'Soon'})"

        breakdown["final_total"] = score

        candidates.append(
            RankedResult(
                product=prod,
                total_score=score,
                relevance_score=base_bm25,
                popularity_score=pop_boost,
                stock_status=status_desc,
                score_breakdown=breakdown
            )
        )

    # Sort descending by total_score
    candidates.sort(key=lambda r: r.total_score, reverse=True)
    return candidates[:top_k]
