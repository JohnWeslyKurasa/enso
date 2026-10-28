"""Interactive CLI for Thelawala Search.

Usage:
    python cli.py
    python cli.py "milk"
"""

import sys
from thelawala_search.engine import ThelawalaSearchEngine

def format_cli():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    engine = ThelawalaSearchEngine()
    engine.initialize()

    def run_query(query: str):
        results = engine.search(query, top_k=10)
        print("\n" + "=" * 90)
        print(f"SEARCH RESULTS FOR: '{query}' ({len(results)} items found)")
        print("=" * 90)
        if not results:
            print("No matching products found. Try a different query.")
            return

        for i, r in enumerate(results, 1):
            p = r.product
            tag = "★ PRIVATE LABEL" if p.is_private_label else ""
            stock_str = f"In Stock ({p.stock_qty})" if p.is_in_stock else f"OUT OF STOCK (ETA: {p.restock_eta or 'TBD'})"
            print(f"{i:2d}. [{p.sku_id}] {p.brand} - {p.name} {tag}")
            print(f"    Category: {p.category} | Size: {p.size} | Price: Rs. {p.price:.2f}")
            print(f"    Availability: {stock_str} | Rank Score: {r.total_score:.2f}")
            # Top signals breakdown
            signals_summary = ", ".join(f"{k}: {v:+.1f}" for k, v in list(r.score_breakdown.items())[:4] if k != "final_total")
            print(f"    Signals: {signals_summary}")
            print("-" * 90)

    if len(sys.argv) > 1:
        run_query(" ".join(sys.argv[1:]))
    else:
        print("\n=== Thelawala Interactive Search Console ===")
        print("Type a search query (e.g., 'milk', 'oil under 200', 'venna', 'ammas kitchen pickle').")
        print("Type 'exit' or 'quit' to stop.\n")
        while True:
            try:
                q = input("thelawala-search> ").strip()
                if not q:
                    continue
                if q.lower() in {"exit", "quit", "q"}:
                    break
                run_query(q)
            except (KeyboardInterrupt, EOFError):
                break
        print("\nExiting search console.")

if __name__ == "__main__":
    format_cli()
