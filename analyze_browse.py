import json
import csv
from collections import defaultdict, Counter

def analyze_browse_conversions():
    # Load catalog
    catalog = {}
    with open('thelawala-search-data/catalog.csv', mode='r', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            catalog[r['sku_id']] = r

    # Analyze logs
    query_to_skus = defaultdict(Counter)
    zero_result_conversions = defaultdict(Counter)
    
    total_logs = 0
    zero_results = 0
    browse_after_zero = 0

    with open('thelawala-search-data/search_log.jsonl', mode='r', encoding='utf-8') as f:
        for line in f:
            total_logs += 1
            data = json.loads(line)
            q = data['query'].strip().lower()
            res_cnt = data['results_count']
            if res_cnt == 0:
                zero_results += 1
            
            for ev in data.get('events', []):
                sku = ev.get('sku_id')
                action = ev.get('action')
                source = ev.get('source')
                weight = 3 if action == 'add_to_cart' else 1
                
                query_to_skus[q][sku] += weight
                if res_cnt == 0 and source == 'browse':
                    zero_result_conversions[q][sku] += weight
                    browse_after_zero += 1

    print(f"Total logs: {total_logs}")
    print(f"Zero results count: {zero_results}")
    print(f"Browse events captured after zero result: {browse_after_zero}")
    
    print("\n--- SAMPLE ZERO-RESULT QUERIES AND WHAT USERS ACTUALLY BOUGHT IN BROWSE ---")
    sample_queries = ['venna', 'paalu', 'gede paalu', 'biyyam pindi', 'red lentils', 'munagakaya', 'oil under 200', 'milk under 50', 'godavari milk', 'ammas kitchen pickle', 'refined oil']
    for sq in sample_queries:
        if sq in zero_result_conversions:
            top_skus = zero_result_conversions[sq].most_common(3)
            print(f"\nQuery: '{sq}'")
            for sku, count in top_skus:
                prod = catalog.get(sku, {})
                print(f"   -> {sku} (score: {count}): {prod.get('brand')} - {prod.get('name')} | Cat: {prod.get('category')} | Price: {prod.get('price')}")
        else:
            print(f"\nQuery: '{sq}' not found in zero-result browse conversions")

if __name__ == '__main__':
    analyze_browse_conversions()
