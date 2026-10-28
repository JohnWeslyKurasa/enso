import json
import csv

def analyze_milk_and_failures():
    # Load catalog
    catalog = {}
    with open('thelawala-search-data/catalog.csv', mode='r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            catalog[r['sku_id']] = r

    # Load inventory
    inventory = {}
    with open('thelawala-search-data/inventory.csv', mode='r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            inventory[r['sku_id']] = r

    # What are the items containing 'milk' in catalog?
    print("--- ALL ITEMS WITH 'MILK' IN NAME ---")
    for sku, item in catalog.items():
        if 'milk' in item['name'].lower():
            inv = inventory.get(sku, {})
            stock = inv.get('stock_qty', 'missing')
            status = inv.get('status', 'missing')
            print(f"{sku} | {item['brand']} | {item['name']} | Cat: {item['category']} | Price: {item['price']} | Stock: {stock} ({status})")

    # Let's inspect search logs for what users searched and clicked for "milk"
    print("\n--- SEARCH LOGS FOR EXACT QUERY 'milk' ---")
    with open('thelawala-search-data/search_log.jsonl', mode='r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if data['query'].strip().lower() == 'milk':
                print(f"Results count: {data['results_count']}, Events: {data['events']}")
                break

    # Check top zero-result queries
    from collections import Counter
    zero_queries = Counter()
    with open('thelawala-search-data/search_log.jsonl', mode='r', encoding='utf-8') as f:
        for line in f:
            data = json.loads(line)
            if data['results_count'] == 0:
                zero_queries[data['query'].strip().lower()] += 1

    print("\n--- TOP 25 ZERO-RESULT QUERIES ---")
    for q, count in zero_queries.most_common(25):
        print(f"  '{q}': {count} times")

if __name__ == '__main__':
    analyze_milk_and_failures()
