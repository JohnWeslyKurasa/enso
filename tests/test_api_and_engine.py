import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
from thelawala_search.engine import ThelawalaSearchEngine
from thelawala_search.query_parser import parse_query
from thelawala_search.vocabulary import expand_query_synonyms
from thelawala_search.data_loader import load_catalog_and_inventory

def test_query_parser():
    # Price tests
    p1 = parse_query("oil under 200")
    assert p1.clean_query == "oil"
    assert p1.max_price == 200.0

    p2 = parse_query("ghee below 500")
    assert p2.clean_query == "ghee"
    assert p2.max_price == 500.0

    p3 = parse_query("curd < 40")
    assert p3.clean_query == "curd"
    assert p3.max_price == 40.0

    # Apostrophe test
    p4 = parse_query("Amma's Kitchen Pickle")
    assert "ammas" in p4.clean_query

def test_data_loader_normalization():
    products = load_catalog_and_inventory()
    assert len(products) > 0

    # Metro feed price verification
    metro_products = [p for p in products.values() if p.supplier == "metro_feed"]
    assert len(metro_products) > 0
    for p in metro_products:
        # All metro_feed prices should now be normalized from paise to rupees
        assert p.price < 5000.0, f"Unnormalized metro_feed price found: {p.price} for {p.name}"

    # Discontinued items must be excluded
    assert not any(p.is_discontinued for p in products.values())

def test_search_engine_results():
    engine = ThelawalaSearchEngine()
    engine.initialize()

    # 1. Milk query returns drinking milk packets
    milk_res = engine.search("milk", top_k=5)
    assert len(milk_res) > 0
    for r in milk_res[:3]:
        assert r.product.category == "Dairy & Eggs"
        assert "chocolate" not in r.product.name.lower()
        assert "powder" not in r.product.name.lower()

    # 2. Regional Telugu queries
    paalu_res = engine.search("paalu", top_k=5)
    assert any("milk" in r.product.name.lower() for r in paalu_res)

    venna_res = engine.search("venna", top_k=5)
    assert any("butter" in r.product.name.lower() for r in venna_res)

    # 3. Typo tolerance
    typo_res = engine.search("MILK CHOCOLAATE", top_k=5)
    assert any("chocolate" in r.product.name.lower() for r in typo_res)

    # 4. Out of stock items must not be above in-stock items
    results = engine.search("milk", top_k=10)
    seen_out_of_stock = False
    for r in results:
        if not r.product.is_in_stock:
            seen_out_of_stock = True
        elif seen_out_of_stock and r.product.is_in_stock:
            assert False, "Found in-stock item ranked after an out-of-stock item!"

if __name__ == "__main__":
    test_query_parser()
    test_data_loader_normalization()
    test_search_engine_results()
    print("All pytest-compatible unit tests passed!")
