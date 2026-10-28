import json
import csv
from collections import Counter, defaultdict

def explore():
    print("=== EXPLORING CATALOG.CSV ===")
    catalog = []
    with open('thelawala-search-data/catalog.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            catalog.append(row)
    print(f"Total catalog rows: {len(catalog)}")
    if catalog:
        print("Sample row:", catalog[0])
        
    suppliers = Counter(r['supplier'] for r in catalog)
    print("Suppliers:", suppliers)
    
    categories = Counter(r['category'] for r in catalog)
    print("Categories:", categories)

    # Inspect prices by supplier
    print("\n--- Price inspection by supplier ---")
    for supp in suppliers:
        prices = [float(r['price']) for r in catalog if r['supplier'] == supp and r['price']]
        print(f"Supplier {supp}: min={min(prices)}, max={max(prices)}, avg={sum(prices)/len(prices):.1f}, median={sorted(prices)[len(prices)//2]}")
        # sample 5 items
        sample = [(r['name'], r['price']) for r in catalog if r['supplier'] == supp][:5]
        print(f"Sample from {supp}: {sample}")

    # Inspect brands, especially "Thela Select"
    thela_select_items = [r for r in catalog if 'thela' in r['brand'].lower() or 'thela select' in r['name'].lower()]
    print(f"\nThela Select items count: {len(thela_select_items)}")
    for item in thela_select_items[:5]:
        print(f"  {item['sku_id']} | {item['brand']} | {item['name']} | {item['category']} | {item['price']}")

    # Inspect "milk" items in catalog
    print("\n--- Items with 'milk' in name, brand, or category ---")
    milk_items = [r for r in catalog if 'milk' in r['name'].lower() or 'milk' in r['brand'].lower() or 'milk' in r['category'].lower()]
    print(f"Count of 'milk' items: {len(milk_items)}")
    for item in milk_items[:15]:
        print(f"  {item['sku_id']} | {item['brand']} | {item['name']} | Cat: {item['category']} | Price: {item['price']}")

    print("\n=== EXPLORING INVENTORY.CSV ===")
    inventory = {}
    with open('thelawala-search-data/inventory.csv', mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            inventory[row['sku_id']] = row
    print(f"Total inventory rows: {len(inventory)}")
    
    inv_statuses = Counter(r['status'] for r in inventory.values())
    print("Inventory statuses:", inv_statuses)
    out_of_stock = [r for r in inventory.values() if int(r['stock_qty']) == 0]
    print(f"Out of stock items: {len(out_of_stock)}")
    has_eta = [r for r in inventory.values() if r.get('restock_eta')]
    print(f"Items with restock_eta: {len(has_eta)}")
    for r in has_eta[:5]:
        print("  Restock sample:", r)

    # Missing from inventory?
    missing_from_inv = [r['sku_id'] for r in catalog if r['sku_id'] not in inventory]
    print(f"Catalog items missing from inventory: {len(missing_from_inv)}")

    print("\n=== EXPLORING SEARCH_LOG.JSONL ===")
    logs = []
    with open('thelawala-search-data/search_log.jsonl', mode='r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    print(f"Total search logs: {len(logs)}")
    
    zero_results = [log for log in logs if log['results_count'] == 0]
    print(f"Zero results searches: {len(zero_results)} ({len(zero_results)/len(logs)*100:.1f}%)")
    
    # Check queries for "milk"
    print("\n--- Search queries containing 'milk' ---")
    milk_queries = [log for log in logs if 'milk' in log['query'].lower()]
    print(f"Total milk queries: {len(milk_queries)}")
    for q in milk_queries[:10]:
        print(f"  Query: '{q['query']}', results_count: {q['results_count']}, events: {len(q['events'])}")
        for ev in q['events']:
            print(f"    -> {ev}")

    # Check queries with "under" or numbers
    print("\n--- Queries with 'under' or price hints ---")
    price_queries = [log for log in logs if 'under' in log['query'].lower() or 'below' in log['query'].lower() or '<' in log['query']]
    print(f"Total price-filtered queries: {len(price_queries)}")
    for q in price_queries[:10]:
        print(f"  Query: '{q['query']}', results_count: {q['results_count']}")

    # Click and cart conversions
    sku_clicks = Counter()
    sku_carts = Counter()
    query_to_sku_clicks = defaultdict(Counter)
    
    for log in logs:
        q = log['query'].strip().lower()
        for ev in log.get('events', []):
            sku = ev.get('sku_id')
            if not sku:
                continue
            if ev.get('action') == 'click':
                sku_clicks[sku] += 1
                query_to_sku_clicks[q][sku] += 1
            elif ev.get('action') == 'add_to_cart':
                sku_carts[sku] += 1
                
    print(f"\nUnique SKUs clicked: {len(sku_clicks)}")
    print(f"Top 5 most clicked SKUs: {sku_clicks.most_common(5)}")
    print(f"Top 5 most added to cart SKUs: {sku_carts.most_common(5)}")

if __name__ == '__main__':
    explore()
