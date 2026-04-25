from __future__ import annotations

import pandas as pd

from services.search_service import (
    build_cas_supplier_queries,
    direct_supplier_search_urls,
    filter_likely_supplier_results,
    serpapi_search,
    discover_product_links_from_page,
)
from services.page_extractor import extract_product_data_from_url


def _dedupe_results(results):
    seen = set()
    unique = []
    for result in results:
        if result.url in seen:
            continue
        seen.add(result.url)
        unique.append(result)
    return unique


def discover_live_suppliers(
    cas_number: str,
    chemical_name: str | None = None,
    serpapi_key: str | None = None,
    max_pages_to_extract: int = 12,
    include_direct_links: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Discover supplier pages and extract visible product/pricing fields.

    v5 behavior:
    - Broad discovery still uses SerpAPI when provided.
    - Direct supplier search pages are used mainly as *seed pages*.
    - We extract from strong product-detail candidates first.
    - Generic direct/search pages are only extracted as a fallback, reducing false rows.
    """
    queries = build_cas_supplier_queries(cas_number, chemical_name)
    serp_results = filter_likely_supplier_results(serpapi_search(queries, serpapi_key or ""))
    direct_results = direct_supplier_search_urls(cas_number) if include_direct_links else []

    seed_results = _dedupe_results(serp_results + direct_results)

    expanded = []
    for result in seed_results[:30]:
        expanded.extend(discover_product_links_from_page(result, cas_number, max_links=5))
    expanded = _dedupe_results(expanded)

    # Extract product-detail candidates first. Search-page seed extraction is fallback only.
    if expanded:
        candidate_results = expanded + serp_results
    else:
        candidate_results = serp_results + direct_results
    candidate_results = _dedupe_results(candidate_results)

    discovery_records = []
    for r in _dedupe_results(expanded + seed_results):
        discovery_records.append(r.__dict__)
    discovery_df = pd.DataFrame(discovery_records)

    extracted_rows = []
    for result in candidate_results[:max_pages_to_extract]:
        extracted = extract_product_data_from_url(
            cas_number,
            result.url,
            supplier_hint=result.supplier_hint or None,
            discovery_title=result.title,
            discovery_snippet=result.snippet,
        )
        # Reduce table noise: keep confirmed CAS rows, visible-price rows, or rows that clearly communicate quote/availability.
        keep = (
            extracted.cas_exact_match
            or extracted.listed_price_usd is not None
            or extracted.stock_status not in ["Not visible", "Extraction failed"]
            or result.source.startswith("serpapi")
        )
        if not keep:
            continue
        extracted_rows.append(
            {
                "cas_number": cas_number,
                "chemical_name": chemical_name or "",
                "supplier": extracted.supplier,
                "region": "Unknown",
                "purity": extracted.purity or "Not visible",
                "pack_size": extracted.pack_size,
                "pack_unit": extracted.pack_unit,
                "listed_price_usd": extracted.listed_price_usd,
                "stock_status": extracted.stock_status,
                "lead_time": "Not visible",
                "product_url": extracted.product_url,
                "notes": extracted.evidence,
                "page_title": extracted.title,
                "cas_exact_match": extracted.cas_exact_match,
                "extraction_status": extracted.extraction_status,
                "extraction_confidence": extracted.confidence,
                "extraction_method": extracted.extraction_method,
                "raw_matches": extracted.raw_matches,
                "data_source": "live_extraction_v5",
            }
        )

    return pd.DataFrame(extracted_rows), discovery_df
