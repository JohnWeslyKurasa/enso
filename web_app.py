"""Interactive Web Application for Thelawala Search.

Provides:
- FastAPI backend serving instant search results (< 5ms)
- Premium, dark-mode glassmorphic Web UI
- Live search-as-you-type, intent chips, price filters, stock indicators, and signal inspection
"""

import time
from typing import Optional, List
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
import uvicorn
from thelawala_search.engine import ThelawalaSearchEngine

app = FastAPI(title="Thelawala Product Search", version="1.0.0")

# Initialize search engine on startup
engine = ThelawalaSearchEngine()
engine.initialize()

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thelawala Search · Hyderabad Grocery Delivery</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-gradient: radial-gradient(circle at 10% 20%, #0d1117 0%, #161b22 90%);
      --surface: rgba(22, 27, 34, 0.85);
      --surface-border: rgba(255, 255, 255, 0.08);
      --surface-hover: rgba(33, 38, 45, 0.95);
      --accent: #2ea043;
      --accent-glow: rgba(46, 160, 67, 0.35);
      --brand-thela: #f0883e;
      --text-primary: #f0f6fc;
      --text-secondary: #8b949e;
      --text-muted: #6e7681;
      --stock-green: #3fb950;
      --stock-red: #f85149;
      --card-radius: 14px;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background: var(--bg-gradient);
      color: var(--text-primary);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      padding: 2rem 1rem 4rem;
    }

    .container {
      max-width: 980px;
      margin: 0 auto;
    }

    header {
      text-align: center;
      margin-bottom: 2.5rem;
    }

    .logo-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 16px;
      border-radius: 999px;
      background: rgba(240, 136, 62, 0.12);
      border: 1px solid rgba(240, 136, 62, 0.3);
      color: var(--brand-thela);
      font-weight: 600;
      font-size: 0.85rem;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      margin-bottom: 1rem;
    }

    h1 {
      font-size: 2.6rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #ffffff 30%, #8b949e 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.5rem;
    }

    .subtitle {
      color: var(--text-secondary);
      font-size: 1.05rem;
      max-width: 580px;
      margin: 0 auto;
    }

    .search-wrapper {
      position: relative;
      margin-bottom: 1.5rem;
    }

    .search-input-box {
      width: 100%;
      background: var(--surface);
      border: 2px solid var(--surface-border);
      border-radius: 16px;
      padding: 1.2rem 1.4rem 1.2rem 3.4rem;
      color: var(--text-primary);
      font-size: 1.15rem;
      font-family: inherit;
      outline: none;
      backdrop-filter: blur(12px);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
      transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .search-input-box:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 4px var(--accent-glow), 0 16px 36px rgba(0, 0, 0, 0.5);
    }

    .search-icon {
      position: absolute;
      left: 1.2rem;
      top: 50%;
      transform: translateY(-50%);
      width: 22px;
      height: 22px;
      stroke: var(--text-secondary);
      pointer-events: none;
    }

    .meta-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.5rem;
      font-size: 0.88rem;
      color: var(--text-secondary);
      flex-wrap: wrap;
      gap: 12px;
    }

    .chip-container {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .chip {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--surface-border);
      color: var(--text-secondary);
      padding: 5px 12px;
      border-radius: 8px;
      font-size: 0.82rem;
      font-weight: 500;
      cursor: pointer;
      transition: all 0.2s;
    }

    .chip:hover {
      background: rgba(255, 255, 255, 0.12);
      color: var(--text-primary);
      border-color: rgba(255, 255, 255, 0.2);
    }

    .metrics-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.8rem;
      color: var(--stock-green);
      background: rgba(63, 185, 80, 0.1);
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid rgba(63, 185, 80, 0.25);
    }

    .results-grid {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .product-card {
      background: var(--surface);
      border: 1px solid var(--surface-border);
      border-radius: var(--card-radius);
      padding: 1.2rem 1.4rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      backdrop-filter: blur(8px);
      transition: all 0.2s ease;
    }

    .product-card:hover {
      background: var(--surface-hover);
      border-color: rgba(255, 255, 255, 0.18);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
    }

    .card-left {
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-width: 70%;
    }

    .brand-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-name {
      font-size: 0.82rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--text-secondary);
    }

    .thela-badge {
      background: rgba(240, 136, 62, 0.15);
      border: 1px solid rgba(240, 136, 62, 0.4);
      color: var(--brand-thela);
      font-size: 0.72rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }

    .product-title {
      font-size: 1.12rem;
      font-weight: 600;
      color: var(--text-primary);
    }

    .product-meta {
      font-size: 0.85rem;
      color: var(--text-muted);
      display: flex;
      gap: 12px;
    }

    .card-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
      text-align: right;
    }

    .price-tag {
      font-size: 1.35rem;
      font-weight: 800;
      color: #fff;
      font-family: 'JetBrains Mono', monospace;
    }

    .stock-badge {
      font-size: 0.78rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: 6px;
      display: inline-flex;
      align-items: center;
      gap: 5px;
    }

    .stock-badge.in-stock {
      background: rgba(63, 185, 80, 0.15);
      color: var(--stock-green);
      border: 1px solid rgba(63, 185, 80, 0.3);
    }

    .stock-badge.out-stock {
      background: rgba(248, 81, 73, 0.15);
      color: var(--stock-red);
      border: 1px solid rgba(248, 81, 73, 0.3);
    }

    .score-breakdown-btn {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.75rem;
      color: var(--text-secondary);
      background: rgba(255, 255, 255, 0.04);
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid var(--surface-border);
    }

    .empty-state {
      text-align: center;
      padding: 4rem 1rem;
      color: var(--text-secondary);
    }

    .empty-icon {
      font-size: 2.5rem;
      margin-bottom: 0.8rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="logo-badge">
        <span>⚡ Quick Commerce · Hyderabad</span>
      </div>
      <h1>Thelawala Search</h1>
      <p class="subtitle">Real-time neural-grade local product search with typo tolerance, Telugu synonym understanding, and stock precision.</p>
    </header>

    <div class="search-wrapper">
      <svg class="search-icon" fill="none" stroke-width="2" viewBox="0 0 24 24">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input 
        type="text" 
        id="searchInput" 
        class="search-input-box" 
        placeholder="Search 'milk', 'oil under 200', 'venna', 'paalu', 'godavari milk'..."
        autofocus 
        autocomplete="off"
      />
    </div>

    <div class="meta-bar">
      <div class="chip-container">
        <span class="chip" onclick="setQuery('milk')">🥛 milk</span>
        <span class="chip" onclick="setQuery('oil under 200')">🛢️ oil under 200</span>
        <span class="chip" onclick="setQuery('ghee under 500')">🧈 ghee under 500</span>
        <span class="chip" onclick="setQuery('venna')">🇮🇳 venna (butter)</span>
        <span class="chip" onclick="setQuery('paalu')">🇮🇳 paalu (milk)</span>
        <span class="chip" onclick="setQuery('gede paalu')">🐄 gede paalu</span>
        <span class="chip" onclick="setQuery('biyyam pindi')">🌾 biyyam pindi</span>
        <span class="chip" onclick="setQuery('MILK CHOCOLAATE')">🍫 MILK CHOCOLAATE</span>
        <span class="chip" onclick="setQuery('godavari milk')">🏷️ godavari milk</span>
        <span class="chip" onclick="setQuery('ammas kitchen pickle')">🥭 ammas kitchen pickle</span>
      </div>
      <div id="metricsBadge" class="metrics-badge" style="display: none;">
        <span>⚡ 0.0ms</span>
      </div>
    </div>

    <div id="resultsList" class="results-grid"></div>
  </div>

  <script>
    const input = document.getElementById('searchInput');
    const resultsContainer = document.getElementById('resultsList');
    const metricsBadge = document.getElementById('metricsBadge');
    let debounceTimer = null;

    function setQuery(q) {
      input.value = q;
      performSearch(q);
    }

    input.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        performSearch(e.target.value);
      }, 120);
    });

    async function performSearch(query) {
      const q = query.trim();
      if (!q) {
        resultsContainer.innerHTML = '';
        metricsBadge.style.display = 'none';
        return;
      }

      const t0 = performance.now();
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        const latency = (performance.now() - t0).toFixed(1);

        metricsBadge.textContent = `⚡ ${latency}ms · ${data.results.length} items`;
        metricsBadge.style.display = 'inline-flex';

        renderResults(data.results, q);
      } catch (err) {
        console.error(err);
      }
    }

    function renderResults(results, query) {
      if (!results || results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <h3>No products found for "${query}"</h3>
            <p>Try searching with colloquial terms like "paalu", "venna", or a price filter like "under 200".</p>
          </div>
        `;
        return;
      }

      resultsContainer.innerHTML = results.map(item => {
        const isThela = item.brand.toLowerCase() === 'thela select' || item.name.toLowerCase().includes('thela select');
        const inStock = item.is_in_stock;
        const stockHtml = inStock 
          ? `<span class="stock-badge in-stock">● In Stock (${item.stock_qty})</span>`
          : `<span class="stock-badge out-stock">● Out of Stock (ETA: ${item.restock_eta || 'Soon'})</span>`;

        const signals = Object.entries(item.score_breakdown || {})
          .filter(([k]) => k !== 'final_total' && k !== 'in_stock_boost')
          .slice(0, 3)
          .map(([k, v]) => `${k}: ${v > 0 ? '+' : ''}${v}`)
          .join(' | ');

        return `
          <div class="product-card">
            <div class="card-left">
              <div class="brand-row">
                <span class="brand-name">${item.brand}</span>
                ${isThela ? '<span class="thela-badge">★ Thela Select</span>' : ''}
              </div>
              <div class="product-title">${item.name}</div>
              <div class="product-meta">
                <span>📁 ${item.category}</span>
                <span>⚖️ ${item.size}</span>
                <span>🏷️ ${item.sku_id}</span>
              </div>
            </div>
            <div class="card-right">
              <div class="price-tag">₹${Number(item.price).toFixed(2)}</div>
              ${stockHtml}
              <div class="score-breakdown-btn" title="Ranking signals: ${signals}">
                Score: ${item.total_score}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    // Initial search for 'milk' on page load
    window.addEventListener('DOMContentLoaded', () => {
      setQuery('milk');
    });
  </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def index_view():
    return HTML_PAGE

@app.get("/api/search")
def search_api(q: str = Query(..., min_length=1), limit: int = 10):
    t0 = time.time()
    results = engine.search(q, top_k=limit)
    latency_ms = round((time.time() - t0) * 1000, 2)
    return {
        "query": q,
        "latency_ms": latency_ms,
        "count": len(results),
        "results": [r.to_dict() for r in results]
    }

if __name__ == "__main__":
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
