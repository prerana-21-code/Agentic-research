"""
Record Enrichment Service
Module 1 — Phase 2: PDF Discovery and Full-Text Extraction

Combines Phase 1 metadata with Phase 2 PDF discovery, download, and extraction results
into an enriched standardized paper record while preserving original abstract data
and maintaining strict distinction between full-text and abstract-only documents.
"""

from __future__ import annotations

import copy
from typing import Any


def enrich_paper_record(
    paper: dict[str, Any],
    discovery_result: dict[str, Any] | None = None,
    download_result: dict[str, Any] | None = None,
    extraction_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Integrates PDF discovery, download, and text extraction results into a standardized paper record.

    Enriched Fields:
    - source_type: "open_access_full_text" if text was extracted, else "abstract_only"
    - full_text: Extracted text string if available, else None
    - pdf_url: Verified PDF URL or None
    - pdf_path: Local filesystem path to PDF or None
    - access_type: "open_access_pdf", "abstract_only", or "metadata_only"
    - extraction_status: "success", "partial", "no_text", "encrypted", "invalid_pdf", "error", or "not_attempted"
    - total_pages: Number of pages in the PDF (0 if no PDF)
    - pages: List of {"page_number": int, "text": str}

    Preserved Invariant Fields:
    - paper_id, openalex_id, title, authors, year, doi, abstract, publication_type, concepts, landing_page_url

    Args:
        paper: Standardized paper record from Phase 1.
        discovery_result: Result from PDFDiscoveryService.discover().
        download_result: Optional result from PDFDownloader.download().
        extraction_result: Optional result from PDFExtractor.extract().

    Returns:
        New enriched paper record dictionary.
    """
    enriched = copy.deepcopy(paper)

    # 1. Initialize Phase 2 fields with safe defaults
    enriched["pdf_url"] = None
    enriched["pdf_path"] = None
    enriched["access_type"] = "abstract_only"
    enriched["extraction_status"] = "not_attempted"
    enriched["total_pages"] = 0
    enriched["pages"] = []
    enriched["full_text"] = None
    enriched["source_type"] = "abstract_only"

    # 2. Integrate Discovery Result
    if discovery_result and isinstance(discovery_result, dict):
        if discovery_result.get("pdf_url"):
            enriched["pdf_url"] = discovery_result.get("pdf_url")
        if discovery_result.get("access_type"):
            enriched["access_type"] = discovery_result.get("access_type")

    # 3. Integrate Download Result
    if download_result and isinstance(download_result, dict):
        if download_result.get("file_path"):
            enriched["pdf_path"] = download_result.get("file_path")
        if not enriched.get("pdf_url") and download_result.get("pdf_url"):
            enriched["pdf_url"] = download_result.get("pdf_url")

    # 4. Integrate Extraction Result
    if extraction_result and isinstance(extraction_result, dict):
        status = extraction_result.get("extraction_status", "error")
        enriched["extraction_status"] = status
        enriched["total_pages"] = extraction_result.get("total_pages", 0)
        enriched["pages"] = extraction_result.get("pages", [])

        extracted_text = extraction_result.get("full_text") or ""
        pages_with_text = extraction_result.get("pages_with_text", 0)

        # Only promote to full_text if extractable text is actually present
        if status in ("success", "partial") and pages_with_text > 0 and extracted_text.strip():
            enriched["full_text"] = extracted_text.strip()
            enriched["source_type"] = "open_access_full_text"
        else:
            # Revert to abstract_only if extraction yielded no text
            enriched["full_text"] = None
            enriched["source_type"] = "abstract_only"

    return enriched
