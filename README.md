# Thelawala Search Engine

High-performance, local product search engine engineered for **Thelawala**—a quick-commerce grocery delivery platform in Hyderabad. Built to handle colloquial customer vocabulary, mobile typos, intent disambiguation, price filtering, and stock availability with zero external API calls.

---

## Quick Start

### 1. Requirements & Setup
- **Python 3.10+** (Tested on Python 3.13)
- No external search infrastructure or cloud APIs required (runs 100% locally on standard laptop-class hardware).

Optional dependencies for the interactive Web UI:
```bash
pip install fastapi uvicorn
```

---

### 2. How to Run

#### Option A: Run in Batch Mode (Automated Evaluation)
Takes a newline-delimited text file of search queries and produces `results.jsonl` (up to 10 ranked `sku_id`s per query):
```bash
python batch_search.py sample_queries.txt results.jsonl
```

Format of `results.jsonl`:
```json
{"query": "milk", "results": ["MF10230", "MF40423", "MF79574", "MF20227", "TW17197", "MF24704", "TW84111", "MF33192", "MF45456", "TW34635"]}
{"query": "oil under 200", "results": ["MF66242", "MF12176", "TW57522", "MF80849", "TW35302", "TW55892", "TW91315", "TW26280", "MF95538", "MF75573"]}
```

#### Option B: Interactive Human CLI
Allows team members to test queries interactively in their terminal with real-time score breakdowns:
```bash
# Interactive REPL mode:
python cli.py

# Single-query mode:
python cli.py "milk"
python cli.py "oil under 200"
python cli.py "venna"
```

#### Option C: Interactive Modern Web UI
Start the local FastAPI web server:
```bash
python web_app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser for a warm beige and mocha search interface featuring search-as-you-type (< 5ms latency), quick preset chips, price indicators, stock badges, and scoring signals.

#### Option D: Run Test Suite
```bash
python -m unittest tests/test_api_and_engine.py
# or
python test_search_engine.py
```

---

## Search Architecture & Pipeline

```
                                 [ Customer Query ]
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │         1. Query Understanding        │
                     │  • Natural language price parsing     │
                     │    ("oil under 200" -> max_price=200) │
                     │  • Punctuation cleanup (Amma's)       │
                     │  • Telugu & Hinglish synonym mapping  │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │          2. In-Memory BM25            │
                     │  • Field-weighted scoring:            │
                     │    Name (3.5x), Brand (2.5x),         │
                     │    Category (2.0x), Desc (1.0x)       │
                     │  • Typo tolerance (Levenshtein & char │
                     │    n-gram candidate recovery)         │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                     ┌───────────────────────────────────────┐
                     │      3. Multi-Signal Re-Ranking       │
                     │  • Category intent priority (Milk)    │
                     │  • Brand protection (Kavya's rule)    │
                     │  • Private label boost (Thela Select) │
                     │  • Behavioral CTR / browse recovery   │
                     │  • Stock hierarchy (In-stock first)   │
                     └───────────────────┬───────────────────┘
                                         │
                                         ▼
                          [ Top 10 Ranked sku_ids ]
```

### 1. Ingestion & Data Hygiene
- **Price Normalization:** The catalog contained prices from multiple suppliers. Specifically, `supplier == 'metro_feed'` stored prices in **paise** (e.g. `16700` for 1kg Toor Dal = ₹167.00), while other suppliers stored in **Rupees**. All `metro_feed` prices are automatically divided by 100 upon ingestion.
- **Inventory Merging:** Discontinued products (`status == 'discontinued'`) are removed from searchable space. Active products are indexed with stock quantity and restock ETAs.

### 2. Query Understanding & Price Filtering
- Queries like `"oil under 200"`, `"ghee below 500"`, and `"curd < 40"` are parsed using regular expressions to extract `max_price` and `min_price`.
- The price clause is stripped from the search query so numerical values and stop words do not pollute token matching.

### 3. Regional Vocabulary & Synonym Layer
In Hyderabad, customers type colloquially or in regional languages:
- **Telugu (Latin & Script):** `paalu` / `పాలు` (milk), `gede paalu` (buffalo milk), `venna` / `వెన్న` (butter), `biyyam pindi` (rice flour), `munagakaya` (drumstick), `kandi pappu` (toor dal), `perugu` (curd), `majiga` (buttermilk), `neyyi` (ghee).
- **Hindi / Hinglish:** `doodh` / `दूध`, `dahi` / `दही`, `atta`, `haldi`, `jeera`.
- **Equivalences:** `red lentils` $\leftrightarrow$ `masoor dal`, `refined oil` $\leftrightarrow$ `sunflower oil`, `low fat milk` $\leftrightarrow$ `toned milk`.

### 4. Behavioral Prior from Search Logs (Log Mining)
Analysis of `thelawala-search-data/search_log.jsonl` revealed that 42.3% of searches historically returned 0 results, forcing 2,181 users to navigate category browse to find and buy their desired product. The engine extracts:
1. **Query-to-SKU conversion score:** Prior session clicks and `add_to_cart` actions are indexed as relevance priors.
2. **Global SKU popularity:** Frequency of purchase interest across the catalog.

### 5. Multi-Signal Scoring Function
Each candidate SKU is scored according to:

$$\text{Final Score} = S_{\text{BM25}} + S_{\text{exact\_name}} + S_{\text{intent}} + S_{\text{brand}} + S_{\text{private\_label}} + S_{\text{behavior}} + S_{\text{stock}}$$

1. **$S_{\text{BM25}}$**: Inverted index BM25Okapi across weighted fields.
2. **$S_{\text{exact\_name}}$**: Boost for exact query matching product title or token subset.
3. **$S_{\text{intent}}$ (Intent Disambiguation):** When searching `"milk"`, pure drinking milk packets (Full Cream, Toned, Buffalo Milk) receive $+12.0$, while confectionary ("Milk Chocolate"), bakery ("Rusk - Milk"), and buttermilk receive negative intent penalties.
4. **$S_{\text{brand}}$ (Brand Intent Protection):** If the customer explicitly queries a brand (e.g. `Godavari Dairy`, `Ammas Kitchen`, `Gomatha`), that brand receives a $+10.0$ boost, and competing brands are de-ranked.
5. **$S_{\text{private\_label}}$ (Thela Select Boost):** For generic product queries, private-label products receive a $+1.8$ margin preference. If the user explicitly searched for a competing brand, this boost is suppressed.
6. **$S_{\text{behavior}}$:** Logarithmic boost based on historical query clicks and add-to-carts.
7. **$S_{\text{stock}}$ (Stock Hierarchy):** In-stock products receive $+100.0$. Out-of-stock products remain in the catalog and appear below in-stock alternatives with their restock dates.

---

## Key Decisions & Trade-offs

| Decision | Trade-off / Rationale |
|---|---|
| **Sandeep vs Farah: Out-of-Stock Handling** | **Resolution:** In-stock items receive a $+100$ score priority. Out-of-stock items are not hidden; they rank below in-stock alternatives with restock ETAs displayed. This satisfies Sandeep (prevents order cancellations/bad reviews) while honoring Farah (customers see the catalog breadth rather than abandoning to competitors). Discontinued items are completely pruned. |
| **Kavya vs Farah: Brand Intent vs Store Margin** | **Resolution:** If a query explicitly names a brand (e.g., *"Godavari milk"* or *"Ammas Kitchen"*), brand relevance takes strict precedence over store brand boost. "Thela Select" receives its margin boost exclusively on category/generic searches (e.g., *"curd"*, *"ghee"*, *"bread"*). Customer intent first, margin second. |
| **Solving the 'Milk' Problem** | A naive keyword search for "milk" returned chocolate, milk biscuits, and milk powder first. We implemented categorical intent disambiguation so single-token dairy staples prioritize actual liquid milk packets. |
| **Normalizing `metro_feed` Prices** | Discovered that `metro_feed` encoded prices in paise while `thela_direct` used rupees. Normalizing `/ 100` fixed price display and enabled numerical price queries (`"oil under 200"`). |
| **Zero External Network Calls at Runtime** | To comply with Arjun's latency and cost constraints, the engine relies on an in-memory inverted index, custom BM25, and local lookup tables. End-to-end query latency is **< 3ms**, achieving > 750 queries/second on a single CPU core. |

---

## Future Roadmap

1. **Lightweight Local Embedding Ranker (Cross-Encoder / ONNX):**
   - Incorporate a 20MB local quantized multilingual MiniLM model via ONNX runtime for sub-millisecond semantic re-ranking of the top 50 BM25 candidates.
2. **Dynamic Learning-to-Rank (LTR):**
   - Train a lightweight LambdaMART (LightGBM) model using features from session search logs, click positions, and conversion rates.
3. **Real-time Inventory & Price Webhooks:**
   - Expose incremental catalog update APIs (`POST /catalog/sku`, `PATCH /inventory/stock`) so daily catalog updates refresh in-memory posting lists without full index rebuilds.
4. **Personalization & Location-based Assortment:**
   - Factor in warehouse pin-code proximity and individual re-order frequency for staple items.
