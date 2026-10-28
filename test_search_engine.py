"""Validation test suite for Thelawala Search Engine."""

import sys
sys.stdout.reconfigure(encoding='utf-8')
from thelawala_search.engine import ThelawalaSearchEngine

def run_tests():
    engine = ThelawalaSearchEngine()
    engine.initialize()

    test_queries = [
        "milk",
        "oil under 200",
        "ghee under 500",
        "venna",
        "paalu",
        "gede paalu",
        "biyyam pindi",
        "MILK CHOCOLAATE",
        "godavari milk",
        "ammas kitchen pickle",
        "atta under 300",
        "bread"
    ]

    print("\n" + "="*80)
    print("RUNNING THELAWALA SEARCH EVALUATION")
    print("="*80)

    for q in test_queries:
        results = engine.search(q, top_k=5)
        print(f"\n--- QUERY: '{q}' (Found {len(results)} results) ---")
        for i, r in enumerate(results, 1):
            p = r.product
            print(
                f"  {i}. [{p.sku_id}] {p.brand} - {p.name} | "
                f"Cat: {p.category} | Price: ₹{p.price:.2f} | "
                f"Stock: {p.stock_qty} ({r.stock_status}) | Score: {r.total_score:.1f}"
            )

    # Specific Assertion 1: 'milk' top 3 should all be Dairy & Eggs drinking milk, NOT chocolate
    milk_res = engine.search("milk", top_k=5)
    assert len(milk_res) > 0, "Milk should return results"
    for r in milk_res[:3]:
        assert r.product.category == "Dairy & Eggs", f"Expected Dairy & Eggs for 'milk', got {r.product.category}"
        assert "chocolate" not in r.product.name.lower(), f"Top milk results must not be chocolate: {r.product.name}"

    # Specific Assertion 2: 'oil under 200' prices must all be <= 200
    oil_res = engine.search("oil under 200", top_k=10)
    assert len(oil_res) > 0, "oil under 200 should return results"
    for r in oil_res:
        assert r.product.price <= 200.0, f"Expected price <= 200, got {r.product.price}"

    # Specific Assertion 3: 'venna' (Telugu for butter) should return Butter
    venna_res = engine.search("venna", top_k=5)
    assert any("butter" in r.product.name.lower() for r in venna_res), "venna must return butter items"

    # Specific Assertion 4: 'godavari milk' should match Godavari Dairy milk
    godavari_res = engine.search("godavari milk", top_k=5)
    assert any("godavari" in r.product.brand.lower() for r in godavari_res), "godavari milk must return Godavari brand"

    print("\n" + "="*80)
    print("ALL CORE INTEGRATION ASSERTIONS PASSED SUCCESSFULLY!")
    print("="*80)

if __name__ == '__main__':
    run_tests()
