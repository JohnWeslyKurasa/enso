"""Interactive Web Application for Thelawala Search.

Provides:
- FastAPI backend serving instant search results (< 5ms)
- Professional Warm Beige & Mocha UI design
- Real-time search-as-you-type, intent chips, price filters, stock indicators, and signal inspection
- Zero emojis; clean SVG icons and executive typography
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

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thelawala Search · Enterprise Grocery Discovery Platform</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      /* Warm Beige & Mocha Palette */
      --bg-canvas: #F8F5F0;
      --bg-subtle: #EFE9E0;
      --surface-card: #FFFFFF;
      --surface-border: #E4D9CC;
      --surface-border-subtle: #EFE6DC;
      --surface-hover: #FDFBF8;

      --mocha-900: #261A14;
      --mocha-800: #38261E;
      --mocha-700: #4D352A;
      --mocha-600: #68493B;
      --mocha-500: #8C6450;
      --mocha-400: #A8826D;
      --mocha-200: #D8C6B6;
      --mocha-100: #EFE4DA;
      --mocha-50:  #F8F3ED;

      --accent-warm: #8A4F32;
      --accent-glow: rgba(138, 79, 50, 0.15);

      --text-primary: #261A14;
      --text-secondary: #5E463A;
      --text-muted: #8A7365;

      --status-in-stock: #276749;
      --status-in-stock-bg: #EDF7F1;
      --status-in-stock-border: #C6E7D2;

      --status-out-stock: #8C371E;
      --status-out-stock-bg: #FDF1ED;
      --status-out-stock-border: #F5CCBE;

      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 14px;
      --radius-xl: 18px;

      --shadow-sm: 0 1px 3px rgba(38, 26, 20, 0.04), 0 1px 2px rgba(38, 26, 20, 0.02);
      --shadow-md: 0 4px 12px rgba(38, 26, 20, 0.05), 0 1px 3px rgba(38, 26, 20, 0.04);
      --shadow-lg: 0 10px 24px -4px rgba(38, 26, 20, 0.08), 0 4px 8px -2px rgba(38, 26, 20, 0.04);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-canvas);
      background-image: 
        radial-gradient(at 15% 15%, rgba(223, 208, 192, 0.35) 0px, transparent 65%),
        radial-gradient(at 85% 85%, rgba(235, 222, 208, 0.45) 0px, transparent 65%);
      color: var(--text-primary);
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      min-height: 100vh;
      padding: 3rem 1.25rem 5rem;
      -webkit-font-smoothing: antialiased;
    }

    .container {
      max-width: 960px;
      margin: 0 auto;
    }

    /* Header */
    header {
      text-align: center;
      margin-bottom: 2.75rem;
    }

    .brand-eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 5px 14px;
      border-radius: 999px;
      background: var(--mocha-100);
      border: 1px solid var(--surface-border);
      color: var(--mocha-700);
      font-weight: 700;
      font-size: 0.76rem;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      margin-bottom: 1.1rem;
    }

    .eyebrow-dot {
      width: 6px;
      height: 6px;
      background: var(--accent-warm);
      border-radius: 50%;
    }

    h1 {
      font-size: 2.5rem;
      font-weight: 800;
      letter-spacing: -0.6px;
      color: var(--mocha-900);
      margin-bottom: 0.65rem;
      line-height: 1.15;
    }

    .subtitle {
      color: var(--text-secondary);
      font-size: 1.05rem;
      line-height: 1.6;
      max-width: 620px;
      margin: 0 auto;
      font-weight: 400;
    }

    /* Search Box */
    .search-card {
      background: var(--surface-card);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-xl);
      padding: 0.5rem;
      box-shadow: var(--shadow-lg);
      margin-bottom: 1.25rem;
      transition: all 0.2s ease;
    }

    .search-card:focus-within {
      border-color: var(--accent-warm);
      box-shadow: 0 0 0 4px var(--accent-glow), var(--shadow-lg);
    }

    .search-inner {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0.5rem 0.85rem;
    }

    .search-icon-svg {
      width: 22px;
      height: 22px;
      color: var(--mocha-500);
      flex-shrink: 0;
    }

    .search-input-box {
      width: 100%;
      border: none;
      background: transparent;
      color: var(--text-primary);
      font-size: 1.12rem;
      font-family: inherit;
      outline: none;
      font-weight: 500;
    }

    .search-input-box::placeholder {
      color: var(--mocha-400);
      font-weight: 400;
    }

    .clear-btn {
      background: var(--bg-subtle);
      border: 1px solid var(--surface-border);
      color: var(--mocha-600);
      cursor: pointer;
      border-radius: var(--radius-sm);
      padding: 4px 8px;
      font-size: 0.75rem;
      font-weight: 600;
      display: none;
      transition: all 0.15s ease;
    }

    .clear-btn:hover {
      background: var(--mocha-200);
      color: var(--mocha-900);
    }

    /* Preset Query Chips */
    .filter-section {
      margin-bottom: 1.75rem;
    }

    .filter-label {
      font-size: 0.76rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--mocha-500);
      margin-bottom: 0.55rem;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .chip-container {
      display: flex;
      flex-wrap: wrap;
      gap: 7px;
    }

    .chip {
      background: var(--surface-card);
      border: 1px solid var(--surface-border);
      color: var(--mocha-700);
      padding: 6px 12px;
      border-radius: var(--radius-md);
      font-size: 0.82rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s ease;
      box-shadow: var(--shadow-sm);
    }

    .chip:hover {
      background: var(--mocha-800);
      color: #FFFFFF;
      border-color: var(--mocha-800);
      transform: translateY(-1px);
    }

    .chip.active {
      background: var(--accent-warm);
      color: #FFFFFF;
      border-color: var(--accent-warm);
    }

    /* Status Bar */
    .status-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.1rem;
      padding: 0 0.25rem;
      font-size: 0.85rem;
      color: var(--text-secondary);
      flex-wrap: wrap;
      gap: 10px;
    }

    .results-count {
      font-weight: 600;
      color: var(--mocha-800);
    }

    .metrics-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.78rem;
      color: var(--mocha-700);
      background: var(--mocha-100);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--surface-border);
      font-weight: 500;
    }

    /* Results List */
    .results-grid {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .product-card {
      background: var(--surface-card);
      border: 1px solid var(--surface-border);
      border-radius: var(--radius-lg);
      padding: 1.15rem 1.4rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: all 0.18s cubic-bezier(0.16, 1, 0.3, 1);
      box-shadow: var(--shadow-sm);
    }

    .product-card:hover {
      border-color: var(--mocha-200);
      box-shadow: var(--shadow-md);
      transform: translateY(-1px);
      background: var(--surface-hover);
    }

    .card-left {
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-width: 68%;
    }

    .brand-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-name {
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.6px;
      color: var(--mocha-600);
    }

    .private-label-pill {
      background: var(--mocha-100);
      border: 1px solid var(--surface-border);
      color: var(--accent-warm);
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .product-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--mocha-900);
      line-height: 1.3;
    }

    .product-details {
      font-size: 0.83rem;
      color: var(--text-muted);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 14px;
    }

    .detail-item {
      display: inline-flex;
      align-items: center;
      gap: 4px;
    }

    .detail-item strong {
      color: var(--text-secondary);
      font-weight: 600;
    }

    .card-right {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 6px;
      text-align: right;
    }

    .price-value {
      font-size: 1.35rem;
      font-weight: 800;
      color: var(--mocha-900);
      font-feature-settings: "tnum" 1;
    }

    .stock-pill {
      font-size: 0.75rem;
      font-weight: 600;
      padding: 3px 8px;
      border-radius: var(--radius-sm);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }

    .stock-indicator-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
    }

    .stock-pill.in-stock {
      background: var(--status-in-stock-bg);
      color: var(--status-in-stock);
      border: 1px solid var(--status-in-stock-border);
    }

    .stock-pill.in-stock .stock-indicator-dot {
      background: var(--status-in-stock);
    }

    .stock-pill.out-stock {
      background: var(--status-out-stock-bg);
      color: var(--status-out-stock);
      border: 1px solid var(--status-out-stock-border);
    }

    .stock-pill.out-stock .stock-indicator-dot {
      background: var(--status-out-stock);
    }

    .score-badge {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.73rem;
      color: var(--text-muted);
      background: var(--bg-canvas);
      padding: 2px 7px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--surface-border);
      cursor: help;
    }

    /* Empty State */
    .empty-state {
      text-align: center;
      padding: 4.5rem 1.5rem;
      background: var(--surface-card);
      border: 1px dashed var(--surface-border);
      border-radius: var(--radius-xl);
      color: var(--text-secondary);
    }

    .empty-state-title {
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--mocha-900);
      margin-bottom: 0.5rem;
    }

    .empty-state-desc {
      font-size: 0.9rem;
      color: var(--text-muted);
      max-width: 440px;
      margin: 0 auto;
      line-height: 1.5;
    }

    /* Footer */
    footer {
      margin-top: 3.5rem;
      text-align: center;
      padding-top: 1.5rem;
      border-top: 1px solid var(--surface-border);
      color: var(--text-muted);
      font-size: 0.82rem;
    }

    @media (max-width: 680px) {
      body {
        padding: 1.5rem 1rem 3rem;
      }
      h1 {
        font-size: 1.9rem;
      }
      .product-card {
        flex-direction: column;
        align-items: flex-start;
        gap: 14px;
      }
      .card-left {
        max-width: 100%;
      }
      .card-right {
        align-items: flex-start;
        text-align: left;
        width: 100%;
        border-top: 1px solid var(--surface-border-subtle);
        padding-top: 10px;
      }
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand-eyebrow">
        <span class="eyebrow-dot"></span>
        <span>Quick-Commerce Discovery Platform · Hyderabad</span>
      </div>
      <h1>Thelawala Search</h1>
      <p class="subtitle">High-precision local grocery discovery with regional Telugu synonym resolution, price constraint parsing, and real-time inventory hierarchy.</p>
    </header>

    <div class="search-card">
      <div class="search-inner">
        <svg class="search-icon-svg" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <circle cx="11" cy="11" r="8"></circle>
          <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
        </svg>
        <input 
          type="text" 
          id="searchInput" 
          class="search-input-box" 
          placeholder="Search products (e.g., 'milk', 'oil under 200', 'venna', 'godavari milk')..."
          autofocus 
          autocomplete="off"
        />
        <button id="clearBtn" class="clear-btn" onclick="clearSearch()">Clear</button>
      </div>
    </div>

    <div class="filter-section">
      <div class="filter-label">
        <span>Suggested Queries & Test Scenarios:</span>
      </div>
      <div class="chip-container">
        <span class="chip" onclick="setQuery('milk')">Milk (Staple)</span>
        <span class="chip" onclick="setQuery('oil under 200')">Oil under 200</span>
        <span class="chip" onclick="setQuery('ghee under 500')">Ghee under 500</span>
        <span class="chip" onclick="setQuery('venna')">Venna (Butter)</span>
        <span class="chip" onclick="setQuery('paalu')">Paalu (Fresh Milk)</span>
        <span class="chip" onclick="setQuery('gede paalu')">Gede Paalu (Buffalo)</span>
        <span class="chip" onclick="setQuery('biyyam pindi')">Biyyam Pindi (Rice Flour)</span>
        <span class="chip" onclick="setQuery('MILK CHOCOLAATE')">Milk Chocolate</span>
        <span class="chip" onclick="setQuery('godavari milk')">Godavari Milk</span>
        <span class="chip" onclick="setQuery('ammas kitchen pickle')">Ammas Kitchen</span>
      </div>
    </div>

    <div class="status-bar">
      <div id="resultsCount" class="results-count">Type a query to search</div>
      <div id="metricsBadge" class="metrics-pill" style="display: none;">
        <span id="latencyText">0.0 ms</span>
      </div>
    </div>

    <div id="resultsList" class="results-grid"></div>

    <footer>
      Thelawala Search Engine · Sub-millisecond BM25 & Multi-Signal Re-Ranking · Pure In-Memory Runtime
    </footer>
  </div>

  <script>
    const input = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearBtn');
    const resultsContainer = document.getElementById('resultsList');
    const resultsCount = document.getElementById('resultsCount');
    const metricsBadge = document.getElementById('metricsBadge');
    const latencyText = document.getElementById('latencyText');
    let debounceTimer = null;

    function setQuery(q) {
      input.value = q;
      clearBtn.style.display = 'block';
      updateActiveChip(q);
      performSearch(q);
    }

    function clearSearch() {
      input.value = '';
      clearBtn.style.display = 'none';
      resultsContainer.innerHTML = '';
      resultsCount.textContent = 'Type a query to search';
      metricsBadge.style.display = 'none';
      updateActiveChip('');
      input.focus();
    }

    function updateActiveChip(query) {
      document.querySelectorAll('.chip').forEach(chip => {
        const chipText = chip.getAttribute('onclick') || '';
        if (chipText.includes(`'${query}'`)) {
          chip.classList.add('active');
        } else {
          chip.classList.remove('active');
        }
      });
    }

    input.addEventListener('input', (e) => {
      const val = e.target.value;
      clearBtn.style.display = val.length > 0 ? 'block' : 'none';
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        performSearch(val);
      }, 120);
    });

    async function performSearch(query) {
      const q = query.trim();
      if (!q) {
        resultsContainer.innerHTML = '';
        resultsCount.textContent = 'Type a query to search';
        metricsBadge.style.display = 'none';
        return;
      }

      const t0 = performance.now();
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        const latency = (performance.now() - t0).toFixed(1);

        latencyText.textContent = `${latency} ms latency · Engine: ${data.latency_ms} ms`;
        metricsBadge.style.display = 'inline-flex';
        resultsCount.textContent = `Displaying ${data.results.length} results for "${q}"`;

        renderResults(data.results, q);
      } catch (err) {
        console.error('Search request failed:', err);
      }
    }

    function renderResults(results, query) {
      if (!results || results.length === 0) {
        resultsContainer.innerHTML = `
          <div class="empty-state">
            <div class="empty-state-title">No products found for "${escapeHtml(query)}"</div>
            <div class="empty-state-desc">Try searching with regional vocabulary (e.g., "paalu", "venna"), standard categories, or price bounds like "under 200".</div>
          </div>
        `;
        return;
      }

      resultsContainer.innerHTML = results.map(item => {
        const isThela = item.brand.toLowerCase() === 'thela select' || item.name.toLowerCase().includes('thela select');
        const inStock = item.is_in_stock;

        const stockHtml = inStock 
          ? `<span class="stock-pill in-stock"><span class="stock-indicator-dot"></span>In Stock (${item.stock_qty})</span>`
          : `<span class="stock-pill out-stock"><span class="stock-indicator-dot"></span>Out of Stock (ETA: ${item.restock_eta || 'Pending'})</span>`;

        const signals = Object.entries(item.score_breakdown || {})
          .filter(([k]) => k !== 'final_total' && k !== 'in_stock_boost')
          .slice(0, 3)
          .map(([k, v]) => `${k}: ${v > 0 ? '+' : ''}${v}`)
          .join(' · ');

        return `
          <div class="product-card">
            <div class="card-left">
              <div class="brand-row">
                <span class="brand-name">${escapeHtml(item.brand)}</span>
                ${isThela ? '<span class="private-label-pill">Thela Select</span>' : ''}
              </div>
              <div class="product-title">${escapeHtml(item.name)}</div>
              <div class="product-details">
                <span class="detail-item"><strong>Category:</strong> ${escapeHtml(item.category)}</span>
                <span class="detail-item"><strong>Size:</strong> ${escapeHtml(item.size)}</span>
                <span class="detail-item"><strong>SKU:</strong> ${escapeHtml(item.sku_id)}</span>
              </div>
            </div>
            <div class="card-right">
              <div class="price-value">₹${Number(item.price).toFixed(2)}</div>
              ${stockHtml}
              <div class="score-badge" title="Ranking factors: ${signals || 'BM25 base'}">
                Score: ${item.total_score}
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    // Initial search on page load
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
