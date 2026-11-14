"""
Research Workflow Service
Phase 5: On-Demand Multi-Paper Discovery, Ingestion, and Hybrid Retrieval

Orchestrates the complete research workflow:
1. Receives research question from user.
2. Checks previously indexed papers in ChromaDB to avoid duplicate processing.
3. Searches OpenAlex for relevant scholarly papers.
4. Discovers legitimate open-access PDFs (never bypassing paywalls).
5. Safely downloads and extracts page-level text via PyMuPDF.
6. Analyzes papers using the NLPResearchAnalyzer to extract research dimensions.
7. Adapts records and facts into page-aware and section-aware chunks via PaperIngestionAdapter.
8. Indexes chunks in persistent ChromaDB collection and synchronizes BM25 index.
9. Executes Hybrid RAG search with Reciprocal Rank Fusion (RRF).
10. Returns ranked results with complete provenance, evidence, and workflow summary.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from paper_processing.nlp_analyzer import NLPResearchAnalyzer
from paper_processing.openalex_client import (
    OpenAlexAPIError,
    OpenAlexClient,
    OpenAlexError,
    OpenAlexNetworkError,
    OpenAlexTimeoutError,
)
from paper_processing.pdf_discovery import PDFDiscoveryService, discover_pdf
from paper_processing.pdf_downloader import DEFAULT_PAPERS_DIR, PDFDownloader
from paper_processing.pdf_extractor import PDFExtractor
from paper_processing.record_enrichment import enrich_paper_record
from rag_engine.integrated_pipeline import IntegratedRAGPipeline

logger = logging.getLogger(__name__)


class ResearchWorkflowService:
    """
    Coordinates on-demand scholarly paper retrieval, NLP analysis,
    indexing, and hybrid RAG retrieval for research queries.
    """

    def __init__(
        self,
        pipeline: IntegratedRAGPipeline,
        papers_storage_dir: Path | str | None = None,
        max_papers_default: int = 3,
    ) -> None:
        self.pipeline = pipeline
        self.papers_storage_dir = Path(papers_storage_dir or DEFAULT_PAPERS_DIR)
        self.max_papers_default = max_papers_default

        # Initialize Member 1 services
        self.openalex_client = OpenAlexClient()
        self.pdf_discovery = PDFDiscoveryService()
        self.pdf_downloader = PDFDownloader(storage_dir=self.papers_storage_dir)
        self.pdf_extractor = PDFExtractor()
        self.nlp_analyzer = NLPResearchAnalyzer()

    def get_indexed_paper_ids(self) -> set[str]:
        """Returns the set of paper_ids already indexed in ChromaDB."""
        try:
            stored = self.pipeline.vector_store.collection.get(include=["metadatas"])
            metas = stored.get("metadatas", []) or []
            return {
                str(m.get("paper_id")).strip()
                for m in metas
                if m.get("paper_id") and str(m.get("paper_id")).strip()
            }
        except Exception as exc:
            logger.warning("Could not read paper_ids from ChromaDB: %s", exc)
            return set()

    def get_indexed_titles(self) -> set[str]:
        """Returns the normalized set of paper titles already indexed in ChromaDB."""
        try:
            stored = self.pipeline.vector_store.collection.get(include=["metadatas"])
            metas = stored.get("metadatas", []) or []
            return {
                str(m.get("paper_title", "")).strip().lower()
                for m in metas
                if m.get("paper_title") and str(m.get("paper_title", "")).strip()
            }
        except Exception as exc:
            logger.warning("Could not read paper titles from ChromaDB: %s", exc)
            return set()

    def execute_workflow(
        self,
        query: str,
        max_papers: int = 3,
        mode: str = "hybrid",
        top_k: int = 5,
        k: int = 60,
        filters: dict[str, Any] | None = None,
        force_reindex: bool = False,
    ) -> dict[str, Any]:
        """
        Executes the full end-to-end research workflow for a given query.

        Args:
            query: The research question or topic.
            max_papers: Maximum new papers to discover & ingest.
            mode: Search mode: 'hybrid', 'semantic', or 'keyword'.
            top_k: Number of ranked passages to return.
            k: RRF smoothing constant (default: 60).
            filters: Optional metadata filters.
            force_reindex: Whether to reindex already indexed papers.

        Returns:
            Dictionary containing workflow status, steps, discovered papers,
            and ranked retrieval results with full provenance.
        """
        clean_query = query.strip()
        execution_steps: list[str] = []
        discovered_summaries: list[dict[str, Any]] = []

        execution_steps.append(f"Received research question: '{clean_query}'")

        # 1. Inspect existing corpus to identify previously indexed papers
        indexed_ids = self.get_indexed_paper_ids()
        indexed_titles = self.get_indexed_titles()
        execution_steps.append(
            f"Corpus check: {len(indexed_ids)} papers ({len(self.pipeline.chunks)} chunks) currently indexed in ChromaDB"
        )

        # 2. Search OpenAlex for relevant scholarly works
        candidate_works: list[dict[str, Any]] = []
        search_limit = max(max_papers * 2, 6)
        try:
            execution_steps.append(f"Searching OpenAlex Works API for topic: '{clean_query}'")
            candidate_works = self.openalex_client.search_papers(
                topic=clean_query,
                max_results=search_limit,
            )
            execution_steps.append(f"OpenAlex returned {len(candidate_works)} candidate papers")
        except (OpenAlexTimeoutError, OpenAlexNetworkError) as net_err:
            logger.warning("OpenAlex network error during search: %s", net_err)
            execution_steps.append(f"OpenAlex network unreachable ({net_err}); querying existing indexed corpus")
        except OpenAlexError as oa_err:
            logger.warning("OpenAlex API error during search: %s", oa_err)
            execution_steps.append(f"OpenAlex API error ({oa_err}); querying existing indexed corpus")
        except Exception as exc:
            logger.error("Unexpected error querying OpenAlex: %s", exc)
            execution_steps.append(f"Search error ({exc}); querying existing indexed corpus")

        # 3. Filter candidates and distinguish newly discovered from previously indexed
        papers_to_ingest: list[dict[str, Any]] = []
        reused_count = 0
        newly_indexed_count = 0

        for paper in candidate_works:
            pid = str(paper.get("paper_id", "")).strip()
            title = str(paper.get("title", "")).strip()
            norm_title = title.lower()

            if pid in indexed_ids or (norm_title and norm_title in indexed_titles):
                reused_count += 1
                discovered_summaries.append({
                    "paper_id": pid,
                    "title": title,
                    "year": paper.get("year"),
                    "authors": paper.get("authors", []),
                    "doi": paper.get("doi"),
                    "landing_page_url": paper.get("landing_page_url"),
                    "source_type": paper.get("source_type", "abstract_only"),
                    "pdf_url": None,
                    "extraction_status": "previously_indexed",
                    "total_pages": 0,
                    "action": "already_indexed",
                    "chunks_count": 0,
                    "key_findings_count": 0,
                    "methodologies_count": 0,
                })
            else:
                if len(papers_to_ingest) < max_papers:
                    papers_to_ingest.append(paper)

        if reused_count > 0:
            execution_steps.append(f"Identified {reused_count} candidate papers already indexed in corpus (reusing existing embeddings)")

        # 4. Ingest new candidate papers
        if papers_to_ingest:
            execution_steps.append(f"Processing {len(papers_to_ingest)} new papers through Member 1 pipeline (PDF + NLP)")

            for idx, paper in enumerate(papers_to_ingest, start=1):
                pid = str(paper.get("paper_id", "")).strip() or f"discovered_paper_{idx}"
                title = str(paper.get("title", "")).strip() or "Untitled Scholarly Work"

                # Step 4a: Retrieve full OpenAlex work metadata if available for OA location info
                work_info: dict[str, Any] | None = None
                try:
                    openalex_id = paper.get("openalex_id") or pid
                    work_url = f"{self.openalex_client.base_url}/works/{pid}"
                    resp = self.openalex_client.session.get(
                        work_url,
                        headers=self.openalex_client.default_headers,
                        timeout=self.openalex_client.timeout,
                    )
                    if resp.status_code == 200:
                        work_info = resp.json()
                except Exception:
                    pass

                # Step 4b: Discover legitimate open-access PDF URL
                discovery_res = self.pdf_discovery.discover(paper, openalex_work=work_info)
                pdf_url = discovery_res.get("pdf_url")
                pdf_available = bool(discovery_res.get("pdf_available") and pdf_url)

                # Step 4c: Safely download & extract PDF if available
                download_res: dict[str, Any] | None = None
                extraction_res: dict[str, Any] | None = None

                if pdf_available and pdf_url:
                    execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] Legitimate OA PDF discovered for '{pid}': downloading...")
                    try:
                        download_res = self.pdf_downloader.download(
                            paper_id=pid,
                            pdf_url=pdf_url,
                        )
                        if download_res.get("success") and download_res.get("file_path"):
                            f_path = download_res["file_path"]
                            execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] Downloaded PDF to {Path(f_path).name}; extracting text with PyMuPDF...")
                            extraction_res = self.pdf_extractor.extract(
                                paper_id=pid,
                                file_path=f_path,
                            )
                            pages_extracted = extraction_res.get("pages_with_text", 0)
                            execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] Extracted {pages_extracted} pages of text")
                    except Exception as exc:
                        logger.warning("PDF processing failed for %s (%s); falling back to abstract-only: %s", pid, title, exc)
                        execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] PDF extraction unavailable for '{pid}'; using abstract fallback")
                else:
                    execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] No open-access PDF available for '{pid}'; using verified abstract & metadata")

                # Step 4d: Enrich record (preserves abstract and sets source_type)
                enriched_paper = enrich_paper_record(
                    paper=paper,
                    discovery_result=discovery_res,
                    download_result=download_res,
                    extraction_result=extraction_res,
                )

                # Step 4e: Run NLP Research Analyzer
                execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] Running NLP analyzer (objectives, methods, findings, metrics)...")
                nlp_analysis: dict[str, Any] | None = None
                try:
                    nlp_analysis = self.nlp_analyzer.analyze(enriched_paper)
                except Exception as nlp_err:
                    logger.warning("NLP analysis encountered an issue on %s: %s", pid, nlp_err)
                    nlp_analysis = None

                # Step 4f: Index into ChromaDB & update BM25
                execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] Adapting & indexing into ChromaDB collection '{self.pipeline.vector_store.collection.name}'...")
                ingest_res = self.pipeline.ingest_paper(
                    paper_record=enriched_paper,
                    nlp_analysis=nlp_analysis,
                    force_reindex=force_reindex,
                )

                chunks_added = ingest_res.get("chunks_ingested", 0)
                newly_indexed_count += 1
                indexed_ids.add(pid)
                if norm_title:
                    indexed_titles.add(norm_title)

                findings_count = len(nlp_analysis.get("findings", [])) if nlp_analysis else 0
                methods_count = len(nlp_analysis.get("methodologies", [])) if nlp_analysis else 0

                discovered_summaries.append({
                    "paper_id": pid,
                    "title": title,
                    "year": enriched_paper.get("year"),
                    "authors": enriched_paper.get("authors", []),
                    "doi": enriched_paper.get("doi"),
                    "landing_page_url": enriched_paper.get("landing_page_url"),
                    "source_type": enriched_paper.get("source_type", "abstract_only"),
                    "pdf_url": enriched_paper.get("pdf_url"),
                    "extraction_status": enriched_paper.get("extraction_status", "not_attempted"),
                    "total_pages": enriched_paper.get("total_pages", 0),
                    "action": "newly_indexed",
                    "chunks_count": chunks_added,
                    "key_findings_count": findings_count,
                    "methodologies_count": methods_count,
                })
                execution_steps.append(f"[{idx}/{len(papers_to_ingest)}] Successfully indexed {chunks_added} chunks for '{title}'")
        else:
            execution_steps.append("No new unindexed papers to process; searching current corpus")

        # 5. Execute Hybrid RAG Search across the updated corpus
        execution_steps.append(f"Executing {mode.upper()} search with top_k={top_k}, k={k} across {len(self.pipeline.chunks)} active corpus chunks")
        results = self.pipeline.search(
            query=clean_query,
            mode=mode,
            top_k=top_k,
            k=k,
            filters=filters,
        )
        execution_steps.append(f"Retrieved {len(results)} ranked passages with Reciprocal Rank Fusion scores")

        # 6. Gather updated corpus statistics
        metas = self.pipeline.vector_store.collection.get(include=["metadatas"]).get("metadatas", [])
        corpus_paper_ids = sorted(list({m.get("paper_id") for m in metas if m.get("paper_id")}))

        return {
            "query": clean_query,
            "status": "completed",
            "execution_steps": execution_steps,
            "discovered_papers": discovered_summaries,
            "total_discovered": len(discovered_summaries),
            "newly_indexed_count": newly_indexed_count,
            "reused_count": reused_count,
            "results": results,
            "corpus_stats": {
                "total_papers": len(corpus_paper_ids),
                "indexed_chunks": len(self.pipeline.chunks),
                "embedding_dimension": 384,
                "embedding_model": "all-MiniLM-L6-v2",
                "fusion_strategy": "Reciprocal Rank Fusion (k=60)",
                "database_path": self.pipeline.database_path,
                "indexed_paper_ids": corpus_paper_ids,
            },
        }
