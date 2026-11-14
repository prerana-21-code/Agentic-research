"""
PDF Discovery Component
Module 1 — Phase 2: PDF Discovery and Full-Text Extraction

Identifies legitimate, open-access full-text PDF URLs from OpenAlex metadata,
recognized institutional repositories, and verified open-access locations
without bypassing paywalls or access controls.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class PDFDiscoveryService:
    """
    Discovers legitimate open-access PDF URLs for papers retrieved from OpenAlex.
    """

    # Recognized trusted Open Access preprint & institutional repository patterns
    ARXIV_ABS_PATTERN = re.compile(r"^https?://arxiv\.org/abs/([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?|[a-z\-]+/[0-9]{7})", re.IGNORECASE)

    def __init__(self) -> None:
        pass

    @classmethod
    def _validate_url(cls, url: str | None) -> bool:
        """Verifies if the URL is well-formed with http/https scheme."""
        if not url or not isinstance(url, str):
            return False
        url = url.strip()
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    def discover(
        self,
        paper: dict[str, Any],
        openalex_work: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Discovers open-access full-text PDF URLs for a standardized paper record.

        Args:
            paper: Standardized paper record dictionary from Phase 1.
            openalex_work: Optional raw OpenAlex work dictionary containing full location metadata.

        Returns:
            Structured discovery result dictionary:
            {
                "paper_id": str,
                "pdf_available": bool,
                "pdf_url": str | None,
                "source_url": str | None,
                "access_type": str,       # "open_access_pdf" | "abstract_only" | "metadata_only"
                "discovery_method": str,  # e.g. "openalex_best_oa_location", "arxiv_open_access"
                "license": str | None,
                "status": str             # "found" | "not_found" | "restricted" | "invalid_url" | "error"
            }
        """
        paper_id = paper.get("paper_id") or ""
        landing_page = paper.get("landing_page_url") or ""

        # Default fallback result (abstract-only)
        result: dict[str, Any] = {
            "paper_id": paper_id,
            "pdf_available": False,
            "pdf_url": None,
            "source_url": landing_page or None,
            "access_type": "abstract_only",
            "discovery_method": "none",
            "license": None,
            "status": "not_found",
        }

        try:
            # Step 1: Check OpenAlex raw metadata if provided
            if openalex_work and isinstance(openalex_work, dict):
                # 1a. Inspect best_oa_location
                best_oa = openalex_work.get("best_oa_location")
                if isinstance(best_oa, dict) and best_oa.get("is_oa"):
                    pdf_url = best_oa.get("pdf_url")
                    if pdf_url and isinstance(pdf_url, str):
                        clean_pdf_url = pdf_url.strip()
                        if self._validate_url(clean_pdf_url):
                            result.update({
                                "pdf_available": True,
                                "pdf_url": clean_pdf_url,
                                "source_url": best_oa.get("landing_page_url") or clean_pdf_url,
                                "access_type": "open_access_pdf",
                                "discovery_method": "openalex_best_oa_location",
                                "license": best_oa.get("license"),
                                "status": "found",
                            })
                            return result
                        else:
                            result["status"] = "invalid_url"

                # 1b. Inspect primary_location if it has an OA PDF
                primary_loc = openalex_work.get("primary_location")
                if isinstance(primary_loc, dict) and primary_loc.get("is_oa"):
                    pdf_url = primary_loc.get("pdf_url")
                    if pdf_url and isinstance(pdf_url, str):
                        clean_pdf_url = pdf_url.strip()
                        if self._validate_url(clean_pdf_url):
                            result.update({
                                "pdf_available": True,
                                "pdf_url": clean_pdf_url,
                                "source_url": primary_loc.get("landing_page_url") or clean_pdf_url,
                                "access_type": "open_access_pdf",
                                "discovery_method": "openalex_primary_location",
                                "license": primary_loc.get("license"),
                                "status": "found",
                            })
                            return result

                # 1c. Inspect all locations list
                locations = openalex_work.get("locations")
                if isinstance(locations, list):
                    for loc in locations:
                        if isinstance(loc, dict) and loc.get("is_oa"):
                            pdf_url = loc.get("pdf_url")
                            if pdf_url and isinstance(pdf_url, str):
                                clean_pdf_url = pdf_url.strip()
                                if self._validate_url(clean_pdf_url):
                                    result.update({
                                        "pdf_available": True,
                                        "pdf_url": clean_pdf_url,
                                        "source_url": loc.get("landing_page_url") or clean_pdf_url,
                                        "access_type": "open_access_pdf",
                                        "discovery_method": "openalex_locations",
                                        "license": loc.get("license"),
                                        "status": "found",
                                    })
                                    return result

                # 1d. Check overall open_access status
                oa_info = openalex_work.get("open_access")
                if isinstance(oa_info, dict):
                    if oa_info.get("oa_status") == "closed" or not oa_info.get("is_oa"):
                        result["status"] = "restricted"
                        result["access_type"] = "abstract_only"
                        return result

            # Step 2: Check landing page URL for direct PDF or trusted OA repository
            if landing_page and isinstance(landing_page, str):
                clean_landing = landing_page.strip()

                # 2a. Direct PDF URL
                if clean_landing.lower().endswith(".pdf"):
                    if self._validate_url(clean_landing):
                        result.update({
                            "pdf_available": True,
                            "pdf_url": clean_landing,
                            "source_url": clean_landing,
                            "access_type": "open_access_pdf",
                            "discovery_method": "direct_pdf_url",
                            "license": "open_access",
                            "status": "found",
                        })
                        return result
                    else:
                        result["status"] = "invalid_url"
                        return result

                # 2b. ArXiv Abstract -> ArXiv PDF resolution
                arxiv_match = self.ARXIV_ABS_PATTERN.match(clean_landing)
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    arxiv_pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                    result.update({
                        "pdf_available": True,
                        "pdf_url": arxiv_pdf_url,
                        "source_url": clean_landing,
                        "access_type": "open_access_pdf",
                        "discovery_method": "arxiv_open_access",
                        "license": "arXiv_open_access",
                        "status": "found",
                    })
                    return result

            return result

        except Exception as exc:
            logger.error("Error during PDF discovery for paper_id '%s': %s", paper_id, exc)
            result.update({
                "status": "error",
                "pdf_available": False,
                "pdf_url": None,
            })
            return result


def discover_pdf(
    paper: dict[str, Any],
    openalex_work: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience function delegating to PDFDiscoveryService."""
    service = PDFDiscoveryService()
    return service.discover(paper=paper, openalex_work=openalex_work)
