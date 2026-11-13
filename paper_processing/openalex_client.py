"""
OpenAlex Paper Retrieval Client
Module 1 — Phase 1: OpenAlex Paper Retrieval

Provides a reusable client to search and retrieve scholarly research papers
from the OpenAlex Works API, reconstruct inverted-index abstracts, and
standardize paper metadata into a uniform record schema.
"""

from __future__ import annotations

import logging
import os
from typing import Any
import requests

logger = logging.getLogger(__name__)


class OpenAlexError(Exception):
    """Base exception for all OpenAlex client operations."""
    pass


class OpenAlexAPIError(OpenAlexError):
    """Raised when the OpenAlex API returns an HTTP error or invalid response."""

    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class OpenAlexNetworkError(OpenAlexError):
    """Raised when a network transport or connection issue occurs."""
    pass


class OpenAlexTimeoutError(OpenAlexNetworkError):
    """Raised when an OpenAlex API request times out."""
    pass


class OpenAlexClient:
    """
    Client for querying the OpenAlex Works API.

    Attributes:
        base_url: Base URL for OpenAlex API endpoints (default: https://api.openalex.org).
        timeout: Request timeout in seconds.
        api_key: Optional OpenAlex API key.
        email: Optional contact email (polite pool).
    """

    DEFAULT_BASE_URL = "https://api.openalex.org"
    DEFAULT_TIMEOUT = 15.0

    def __init__(
        self,
        api_key: str | None = None,
        email: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        base_url: str = DEFAULT_BASE_URL,
        session: requests.Session | None = None,
    ) -> None:
        """
        Initializes the OpenAlex client.

        Args:
            api_key: Optional API key. If omitted, checks OPENALEX_API_KEY environment variable.
            email: Optional email for the polite pool. If omitted, checks OPENALEX_MAILTO environment variable.
            timeout: HTTP request timeout in seconds (default: 15.0).
            base_url: Root URL for OpenAlex endpoints (default: https://api.openalex.org).
            session: Optional custom requests.Session instance (useful for testing or connection reuse).
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = float(timeout)
        self.api_key = api_key or os.getenv("OPENALEX_API_KEY")
        self.email = email or os.getenv("OPENALEX_MAILTO")
        self.session = session or requests.Session()

        # Build User-Agent header
        user_agent_parts = ["AgenticResearchAssistant/1.0"]
        if self.email:
            user_agent_parts.append(f"(mailto:{self.email.strip()})")
        self.default_headers = {
            "User-Agent": " ".join(user_agent_parts),
            "Accept": "application/json",
        }

    @staticmethod
    def reconstruct_abstract(inverted_index: dict[str, list[int]] | None) -> str:
        """
        Reconstructs plain text from OpenAlex's abstract_inverted_index format.

        OpenAlex represents abstracts as a dictionary where keys are words and
        values are lists of integer token positions in the passage.

        Args:
            inverted_index: Mapping of word string to list of zero-based position indices.

        Returns:
            Reconstructed abstract string, or an empty string if missing or malformed.
        """
        if not inverted_index or not isinstance(inverted_index, dict):
            return ""

        token_list: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            if not isinstance(word, str) or not isinstance(positions, (list, tuple)):
                continue
            for pos in positions:
                if isinstance(pos, int) and pos >= 0:
                    token_list.append((pos, word))

        if not token_list:
            return ""

        token_list.sort(key=lambda item: item[0])
        return " ".join(word for _, word in token_list).strip()

    def _normalize_work(self, work: dict[str, Any]) -> dict[str, Any]:
        """
        Normalizes a raw OpenAlex work object into the standardized paper record schema.

        Schema:
        {
            "paper_id": "",
            "openalex_id": "",
            "title": "",
            "authors": [],
            "year": null,
            "doi": null,
            "abstract": "",
            "publication_type": "",
            "concepts": [],
            "landing_page_url": "",
            "source_type": "abstract_only",
            "full_text": null
        }

        Args:
            work: Dictionary representing an OpenAlex work response.

        Returns:
            Standardized paper record dictionary.
        """
        # OpenAlex ID & deterministic paper_id
        openalex_id = str(work.get("id") or "").strip()
        if openalex_id:
            paper_id = openalex_id.split("/")[-1]
        else:
            paper_id = ""

        # Title normalization
        title = (work.get("title") or "").strip()

        # Authors extraction
        authors: list[str] = []
        authorships = work.get("authorships")
        if isinstance(authorships, list):
            for authorship in authorships:
                if isinstance(authorship, dict):
                    author_obj = authorship.get("author")
                    if isinstance(author_obj, dict):
                        author_name = author_obj.get("display_name")
                        if author_name and isinstance(author_name, str):
                            authors.append(author_name.strip())

        # Publication year
        year = work.get("publication_year")
        if not isinstance(year, int):
            year = None

        # DOI normalization
        doi = work.get("doi")
        if doi and isinstance(doi, str):
            doi = doi.strip()
        else:
            doi = None

        # Abstract reconstruction
        abstract = self.reconstruct_abstract(work.get("abstract_inverted_index"))

        # Publication type
        pub_type = work.get("type")
        if pub_type and isinstance(pub_type, str):
            publication_type = pub_type.strip()
        else:
            publication_type = ""

        # Primary research concepts or topics
        concepts: list[str] = []
        raw_concepts = work.get("concepts")
        if isinstance(raw_concepts, list):
            for concept in raw_concepts:
                if isinstance(concept, dict):
                    c_name = concept.get("display_name")
                    if c_name and isinstance(c_name, str):
                        concepts.append(c_name.strip())

        # Fallback to primary_topic if concepts is empty
        if not concepts:
            primary_topic = work.get("primary_topic")
            if isinstance(primary_topic, dict):
                t_name = primary_topic.get("display_name")
                if t_name and isinstance(t_name, str):
                    concepts.append(t_name.strip())

        # Landing page URL
        landing_page_url = ""
        primary_location = work.get("primary_location")
        if isinstance(primary_location, dict):
            landing_page_url = primary_location.get("landing_page_url") or ""

        if not landing_page_url and doi:
            landing_page_url = doi
        if not landing_page_url:
            landing_page_url = openalex_id

        return {
            "paper_id": paper_id,
            "openalex_id": openalex_id,
            "title": title,
            "authors": authors,
            "year": year,
            "doi": doi,
            "abstract": abstract,
            "publication_type": publication_type,
            "concepts": concepts,
            "landing_page_url": str(landing_page_url).strip(),
            "source_type": "abstract_only",
            "full_text": None,
        }

    def search_papers(
        self,
        topic: str,
        max_results: int = 10,
        per_page: int = 25,
    ) -> list[dict[str, Any]]:
        """
        Searches the OpenAlex Works API for scholarly papers matching the given topic.

        Supports cursor-based pagination and enforces result limits and deduplication.

        Args:
            topic: Search query or research topic.
            max_results: Maximum number of papers to retrieve (default: 10).
            per_page: Number of items per API page request (default: 25, max: 200).

        Returns:
            List of standardized paper record dictionaries.

        Raises:
            ValueError: If topic is empty or max_results <= 0.
            OpenAlexTimeoutError: If request times out.
            OpenAlexNetworkError: If a connection error occurs.
            OpenAlexAPIError: If the API returns an HTTP error status or malformed payload.
        """
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError("Search topic cannot be empty.")

        if not isinstance(max_results, int) or max_results <= 0:
            raise ValueError("max_results must be a positive integer.")

        clean_topic = topic.strip()
        effective_per_page = max(1, min(per_page, max_results, 200))
        url = f"{self.base_url}/works"

        params: dict[str, Any] = {
            "search": clean_topic,
            "per_page": effective_per_page,
            "cursor": "*",
        }

        if self.api_key:
            params["api_key"] = self.api_key

        headers = dict(self.default_headers)

        papers: list[dict[str, Any]] = []
        seen_ids: set[str] = set()

        logger.info(
            "Searching OpenAlex Works for topic='%s' (max_results=%d, per_page=%d)",
            clean_topic,
            max_results,
            effective_per_page,
        )

        while len(papers) < max_results:
            try:
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout as exc:
                logger.error("Timeout connecting to OpenAlex API: %s", exc)
                raise OpenAlexTimeoutError(
                    f"Request to OpenAlex API timed out after {self.timeout}s: {exc}"
                ) from exc
            except requests.exceptions.RequestException as exc:
                logger.error("Network error communicating with OpenAlex API: %s", exc)
                raise OpenAlexNetworkError(
                    f"Network error during OpenAlex API request: {exc}"
                ) from exc

            # Check HTTP status
            if response.status_code >= 400:
                logger.error(
                    "OpenAlex API returned HTTP error %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                raise OpenAlexAPIError(
                    f"OpenAlex API error (HTTP {response.status_code}): {response.text[:200]}",
                    status_code=response.status_code,
                    response_body=response.text,
                )

            # Parse JSON payload
            try:
                data = response.json()
            except Exception as exc:
                logger.error("Failed to parse OpenAlex response as JSON: %s", exc)
                raise OpenAlexAPIError(
                    f"Invalid JSON returned by OpenAlex API: {exc}",
                    status_code=response.status_code,
                    response_body=response.text,
                ) from exc

            if not isinstance(data, dict) or "results" not in data:
                logger.error("Malformed response from OpenAlex: missing 'results' key")
                raise OpenAlexAPIError(
                    "Malformed response from OpenAlex: 'results' key not found.",
                    status_code=response.status_code,
                )

            raw_results = data.get("results")
            if not isinstance(raw_results, list) or len(raw_results) == 0:
                # No more results returned
                break

            for raw_work in raw_results:
                if not isinstance(raw_work, dict):
                    continue

                normalized = self._normalize_work(raw_work)
                work_id = normalized["paper_id"] or normalized["openalex_id"]

                # Deduplicate records
                if work_id and work_id in seen_ids:
                    continue

                if work_id:
                    seen_ids.add(work_id)

                papers.append(normalized)

                if len(papers) >= max_results:
                    break

            # Handle cursor-based pagination
            meta = data.get("meta")
            next_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None

            if not next_cursor or next_cursor == params.get("cursor"):
                # No further pages available
                break

            params["cursor"] = next_cursor

        logger.info(
            "Retrieved %d papers for topic='%s'",
            len(papers),
            clean_topic,
        )
        return papers[:max_results]
