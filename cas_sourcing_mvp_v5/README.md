# CAS Sourcing MVP v3 — Layered Live Extraction

This Streamlit MVP accepts CAS numbers and desired quantities, discovers supplier/product pages, extracts visible product/pricing evidence when available, normalizes catalog pricing, estimates bulk pricing scenarios, ranks suppliers, and exports results.

## What v3 adds on top of v2

- Keeps the stable mock mode intact.
- Keeps live supplier discovery mode intact.
- Upgrades page parsing from basic text scraping to layered extraction:
  - Schema.org / JSON-LD product and offer data
  - OpenGraph/meta price tags
  - HTML product/variant tables
  - Visible text windows around CAS numbers and pack sizes
  - Availability / quote-only language detection
  - Raw evidence snippets for manual audit
- Adds extraction method and raw match fields to exports.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Optional SerpAPI setup

Live discovery can work with direct supplier links, but search coverage improves with SerpAPI.

Create `.streamlit/secrets.toml`:

```toml
SERPAPI_KEY = "your_key_here"
```

## Important limitation

Visible catalog price is factual only when extracted from a supplier page. Bulk price remains modeled until confirmed by RFQ.

## v4 notes

v4 fixes the main limitation found in v3: the app was often parsing supplier search pages rather than product-detail pages. It now expands same-domain links that look like product/catalog pages, prioritizes those for extraction, and ignores pack/price fields unless the requested CAS is confirmed on the page or in the discovery evidence. This prevents false positives from unrelated products.

## v5 notes

v5 addresses the tougher CAS test behavior where supplier search pages produced generic links such as order status, quick order, promotions, or category pages. The live discovery layer now treats direct supplier search pages mainly as seed pages, expands only high-confidence product candidates, and extracts from those product-detail candidates first. It also adds CAS-neighborhood extraction for product-card style pages and filters zero/suspicious prices.

For best real-world discovery, use a SerpAPI key. Without a search API key, the app relies on supplier direct-search pages, many of which hide product data behind JavaScript or login gates.
