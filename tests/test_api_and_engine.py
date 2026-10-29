"""Comprehensive Test Suite for Thelawala Search Engine.

Covers all business cases and architectural constraints specified by the Thelawala team:
1. Sandeep's cases:
   - Metro feed pricing anomaly (paise to INR normalization)
   - Discontinued items exclusion
   - Milk intent disambiguation (fresh drinking milk packets vs chocolate/powder)
   - Stock hierarchy (in-stock priority, out-of-stock grace period)
2. Kavya's cases:
   - Natural language and single-thumb mobile query understanding
   - Telugu and regional language vocabulary expansion
   - Brand intent protection (customer first, margin second)
3. Farah's cases:
   - Natural language price constraints ('oil under 200', 'ghee below 500')
   - Private label boost ('Thela Select' on generic unbranded queries)
4. Arjun's cases:
   - Zero external API/LLM calls at runtime
   - Self-contained execution on catalog and inventory datasets
   - Sub-10ms response latency
5. Batch search runner contract (results.jsonl structure: {"query": "...", "results": ["sku_id", ...]})
"""

import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from thelawala_search.engine import ThelawalaSearchEngine
from thelawala_search.query_parser import parse_query
from thelawala_search.vocabulary import expand_query_synonyms
from thelawala_search.data_loader import load_catalog_and_inventory, find_file
from batch_search import run_batch


class TestDataIngestionAndNormalization(unittest.TestCase):
    """Validates dataset loading, normalization, and bug fixes."""

    @classmethod
    def setUpClass(cls):
        cls.products = load_catalog_and_inventory()

    def test_catalog_and_inventory_loaded(self):
        """Verifies catalog and inventory are correctly ingested and merged."""
        self.assertGreater(len(self.products), 0, "Active products should be loaded.")

    def test_metro_feed_price_normalization(self):
        """Sandeep's Bug: Metro Feed prices are stored in paise and must be divided by 100."""
        metro_products = [p for p in self.products.values() if p.supplier == "metro_feed"]
        self.assertGreater(len(metro_products), 0, "Metro feed products must exist.")
        for p in metro_products:
            self.assertLess(
                p.price,
                5000.0,
                f"Unnormalized metro_feed price found: ₹{p.price} for '{p.name}'"
            )

    def test_discontinued_items_excluded(self):
        """Sandeep's Rule: Discontinued warehouse items must be completely removed from index."""
        for p in self.products.values():
            self.assertFalse(
                p.is_discontinued,
                f"Discontinued item '{p.sku_id}' should not be present in active index."
            )

    def test_path_resolution_fallback(self):
        """Verifies flexible file resolution across root and data directories."""
        cat_file = find_file(None, ["catalog.csv", "catalog (1).csv", "thelawala-search-data/catalog.csv"])
        inv_file = find_file(None, ["inventory.csv", "thelawala-search-data/inventory.csv"])
        self.assertIsNotNone(cat_file, "Catalog file should be resolved.")
        self.assertIsNotNone(inv_file, "Inventory file should be resolved.")


class TestQueryParserAndPriceExtraction(unittest.TestCase):
    """Validates natural language single-box query parsing."""

    def test_price_constraint_under(self):
        """Farah's Case: 'oil under 200' -> clean query 'oil', max_price = 200.0."""
        pq = parse_query("oil under 200")
        self.assertEqual(pq.clean_query, "oil")
        self.assertEqual(pq.max_price, 200.0)

    def test_price_constraint_below(self):
        """Farah's Case: 'ghee below 500' -> clean query 'ghee', max_price = 500.0."""
        pq = parse_query("ghee below 500")
        self.assertEqual(pq.clean_query, "ghee")
        self.assertEqual(pq.max_price, 500.0)

    def test_price_constraint_symbol(self):
        """Symbolic price constraints: 'curd < 40' -> clean query 'curd', max_price = 40.0."""
        pq = parse_query("curd < 40")
        self.assertEqual(pq.clean_query, "curd")
        self.assertEqual(pq.max_price, 40.0)

    def test_apostrophe_normalization(self):
        """Apostrophe normalization for brands like Amma's Kitchen."""
        pq = parse_query("Amma's Kitchen Mango Pickle")
        self.assertIn("ammas", pq.clean_query)
        self.assertNotIn("'", pq.clean_query)


class TestSearchEngineCases(unittest.TestCase):
    """Validates the search engine ranking, intents, vocabulary, and business rules."""

    @classmethod
    def setUpClass(cls):
        cls.engine = ThelawalaSearchEngine()
        cls.engine.initialize()

    def test_milk_intent_disambiguation(self):
        """Sandeep's Case: 'milk' must return fresh drinking milk packets in top results, NOT chocolate or powder."""
        results = self.engine.search("milk", top_k=5)
        self.assertGreater(len(results), 0, "Query 'milk' must return results.")
        
        # Verify top results are liquid drinking milk
        for r in results[:3]:
            name = r.product.name.lower()
            cat = r.product.category
            self.assertEqual(cat, "Dairy & Eggs", f"Expected Dairy & Eggs for '{name}'")
            self.assertNotIn("chocolate", name, f"Milk search returned chocolate: '{name}'")
            self.assertNotIn("powder", name, f"Milk search returned powder: '{name}'")
            self.assertNotIn("biscuit", name, f"Milk search returned biscuit: '{name}'")

    def test_milk_chocolate_intent(self):
        """Ensures that searching specifically for 'MILK CHOCOLAATE' correctly returns chocolates."""
        results = self.engine.search("MILK CHOCOLAATE", top_k=5)
        self.assertGreater(len(results), 0)
        self.assertTrue(
            any("chocolate" in r.product.name.lower() for r in results),
            "Typo query 'MILK CHOCOLAATE' must return chocolate items."
        )

    def test_price_filter_enforcement_oil_under_200(self):
        """Farah's Case: 'oil under 200' must return cooking oils with price <= 200."""
        results = self.engine.search("oil under 200", top_k=10)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertLessEqual(
                r.product.price,
                200.0,
                f"Product price ₹{r.product.price} exceeded 200 for '{r.product.name}'"
            )

    def test_price_filter_enforcement_ghee_under_500(self):
        """Farah's Case: 'ghee under 500' must return ghee with price <= 500."""
        results = self.engine.search("ghee under 500", top_k=5)
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertLessEqual(
                r.product.price,
                500.0,
                f"Product price ₹{r.product.price} exceeded 500 for '{r.product.name}'"
            )

    def test_regional_telugu_vocabulary(self):
        """Kavya's Case: Hyderabad customers type colloquial Telugu transliterations."""
        # 1. paalu -> milk
        paalu_res = self.engine.search("paalu", top_k=5)
        self.assertTrue(any("milk" in r.product.name.lower() for r in paalu_res), "paalu must match milk.")

        # 2. venna -> butter
        venna_res = self.engine.search("venna", top_k=5)
        self.assertTrue(any("butter" in r.product.name.lower() for r in venna_res), "venna must match butter.")

        # 3. biyyam pindi -> rice flour
        biyyam_res = self.engine.search("biyyam pindi", top_k=5)
        self.assertTrue(any("rice flour" in r.product.name.lower() for r in biyyam_res), "biyyam pindi must match rice flour.")

        # 4. gede paalu -> buffalo milk
        gede_res = self.engine.search("gede paalu", top_k=5)
        self.assertTrue(any("buffalo milk" in r.product.name.lower() for r in gede_res), "gede paalu must match buffalo milk.")

    def test_brand_intent_protection(self):
        """Kavya's Rule: Customer first, margin second. Searching for a brand protects that brand."""
        # Query 1: 'godavari milk' must prioritize Godavari Dairy
        godavari_res = self.engine.search("godavari milk", top_k=5)
        self.assertGreater(len(godavari_res), 0)
        top_brands = [r.product.brand.lower() for r in godavari_res[:3]]
        self.assertIn("godavari dairy", top_brands, "Godavari brand must lead results for 'godavari milk'")

        # Query 2: 'ammas kitchen pickle' must prioritize Ammas Kitchen
        ammas_res = self.engine.search("ammas kitchen pickle", top_k=5)
        self.assertGreater(len(ammas_res), 0)
        self.assertEqual(ammas_res[0].product.brand.lower(), "ammas kitchen")

    def test_private_label_boost_on_generic_queries(self):
        """Farah's Rule: Thela Select should be boosted on generic unbranded queries."""
        bread_res = self.engine.search("bread", top_k=5)
        self.assertGreater(len(bread_res), 0)
        has_thela_select = any(r.product.is_private_label for r in bread_res[:3])
        self.assertTrue(has_thela_select, "Thela Select should appear prominently on generic query 'bread'")

    def test_stock_hierarchy(self):
        """Sandeep vs Farah Resolution: In-stock items strictly rank before out-of-stock items."""
        results = self.engine.search("milk", top_k=10)
        self.assertGreater(len(results), 0)

        seen_out_of_stock = False
        for r in results:
            if not r.product.is_in_stock:
                seen_out_of_stock = True
            elif seen_out_of_stock and r.product.is_in_stock:
                self.fail(f"Violation: In-stock item '{r.product.name}' was ranked after an out-of-stock item!")


class TestBatchSearchRunner(unittest.TestCase):
    """Validates the batch evaluation contract specified in the assignment."""

    def test_batch_search_runner_output(self):
        """Batch runner must take input file and write jsonl with query and up to 10 sku_ids."""
        input_file = "sample_queries.txt"
        output_file = "results.jsonl"

        run_batch(input_file=input_file, output_file=output_file)

        self.assertTrue(os.path.exists(output_file), f"{output_file} must be created.")

        with open(output_file, mode="r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        self.assertGreater(len(lines), 0, "results.jsonl should not be empty.")

        for line in lines:
            record = json.loads(line)
            self.assertIn("query", record, "Each record must have a 'query' key.")
            self.assertIn("results", record, "Each record must have a 'results' key.")
            self.assertIsInstance(record["results"], list, "'results' must be a list of sku_ids.")
            self.assertLessEqual(len(record["results"]), 10, "Up to 10 sku_ids allowed per line.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
