"""
Paper Processing Package
Module 1 of the Hybrid ML-NLP and Agentic RAG-Based Research Assistant.
Handles paper retrieval, ingestion, metadata extraction, and text processing.
"""

from paper_processing.openalex_client import (
    OpenAlexClient,
    OpenAlexError,
    OpenAlexAPIError,
    OpenAlexNetworkError,
    OpenAlexTimeoutError,
)

__all__ = [
    "OpenAlexClient",
    "OpenAlexError",
    "OpenAlexAPIError",
    "OpenAlexNetworkError",
    "OpenAlexTimeoutError",
]
