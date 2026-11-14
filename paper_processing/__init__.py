"""
Paper Processing Package
Module 1 of the Hybrid ML-NLP and Agentic RAG-Based Research Assistant.
Handles paper retrieval, ingestion, metadata extraction, text processing, and NLP analysis.
"""

# Phase 1: OpenAlex Paper Retrieval
from paper_processing.openalex_client import (
    OpenAlexClient,
    OpenAlexError,
    OpenAlexAPIError,
    OpenAlexNetworkError,
    OpenAlexTimeoutError,
)

# Phase 2: PDF Discovery, Download, Extraction & Enrichment
from paper_processing.pdf_discovery import (
    PDFDiscoveryService,
    discover_pdf,
)
from paper_processing.pdf_downloader import (
    PDFDownloader,
    PDFDownloadError,
    download_pdf,
)
from paper_processing.pdf_extractor import (
    PDFExtractor,
    PDFExtractionError,
    extract_text_from_pdf,
)
from paper_processing.record_enrichment import (
    enrich_paper_record,
)

# Phase 3: NLP-Based Research Paper Analysis
from paper_processing.text_preprocessor import (
    AcademicTextPreprocessor,
)
from paper_processing.section_segmenter import (
    SectionSegmenter,
)
from paper_processing.keyword_extractor import (
    KeywordExtractor,
)
from paper_processing.information_extractor import (
    InformationExtractor,
)
from paper_processing.nlp_analyzer import (
    NLPResearchAnalyzer,
    analyze_paper,
)

__all__ = [
    # Phase 1
    "OpenAlexClient",
    "OpenAlexError",
    "OpenAlexAPIError",
    "OpenAlexNetworkError",
    "OpenAlexTimeoutError",
    # Phase 2
    "PDFDiscoveryService",
    "discover_pdf",
    "PDFDownloader",
    "PDFDownloadError",
    "download_pdf",
    "PDFExtractor",
    "PDFExtractionError",
    "extract_text_from_pdf",
    "enrich_paper_record",
    # Phase 3
    "AcademicTextPreprocessor",
    "SectionSegmenter",
    "KeywordExtractor",
    "InformationExtractor",
    "NLPResearchAnalyzer",
    "analyze_paper",
]
