"""
Integrated RAG Pipeline
Module 2 — Phase 4: Hybrid RAG Engine Integration

Provides a unified multi-paper retrieval engine integrating Member 1's
intelligent paper processing with Member 2's hybrid dense-vector (ChromaDB)
and sparse-lexical (BM25) search with Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.hybrid_search import HybridSearch
from rag_engine.keyword_search import KeywordSearch
from rag_engine.paper_adapter import EnhancedVectorStore, PaperIngestionAdapter
from rag_engine.paper_loader import load_papers
from rag_engine.semantic_search import SemanticSearch

logger = logging.getLogger(__name__)

DEFAULT_CHROMA_PATH = str(repo_root / "data" / "chroma_db")


def check_paper_index_status(
    vector_store: EnhancedVectorStore,
    paper_id: str,
    new_chunks: list[dict[str, Any]],
) -> tuple[bool, dict[str, Any]]:
    """
    Performs consistency verification specifically for a single paper_id within
    the persistent ChromaDB collection.

    Verifies:
    1. Chunk ID exact presence.
    2. Document text character-level exact match.
    3. Metadata exact match (page_number, section, chunk_type).
    4. Stale chunk detection for this specific paper_id.

    Returns:
        (is_consistent: bool, details: dict)
    """
    new_chunk_ids = {c["chunk_id"] for c in new_chunks}
    new_chunk_map = {c["chunk_id"]: c for c in new_chunks}

    try:
        stored = vector_store.collection.get(
            where={"paper_id": paper_id},
            include=["documents", "metadatas"],
        )
        stored_ids = stored.get("ids", []) or []
        stored_docs = stored.get("documents", []) or []
        stored_metas = stored.get("metadatas", []) or []
    except Exception as exc:
        return False, {
            "status": "error",
            "error": str(exc),
            "paper_id": paper_id,
            "missing_ids": sorted(list(new_chunk_ids)),
            "modified_ids": [],
            "stale_ids": [],
        }

    stored_map: dict[str, dict[str, Any]] = {}
    for i, s_id in enumerate(stored_ids):
        doc = stored_docs[i] if i < len(stored_docs) else ""
        meta = stored_metas[i] if i < len(stored_metas) else {}
        stored_map[s_id] = {"text": doc, "metadata": meta or {}}

    missing_ids: set[str] = set()
    modified_ids: set[str] = set()

    for c_id, chunk in new_chunk_map.items():
        if c_id not in stored_map:
            missing_ids.add(c_id)
            continue

        item = stored_map[c_id]
        if item["text"] != chunk["text"]:
            modified_ids.add(c_id)
            continue

        item_meta = item.get("metadata", {})
        expected_page = int(chunk.get("page_number") or 0)
        actual_page = int(item_meta.get("page_number") or 0)
        if actual_page != expected_page:
            modified_ids.add(c_id)
            continue

        expected_sec = str(chunk.get("section") or "FULL_TEXT")
        actual_sec = str(item_meta.get("section") or "FULL_TEXT")
        if actual_sec != expected_sec:
            modified_ids.add(c_id)
            continue

    stale_ids = set(stored_ids) - new_chunk_ids

    is_consistent = (
        len(missing_ids) == 0
        and len(modified_ids) == 0
        and len(stale_ids) == 0
        and len(new_chunk_ids) > 0
    )

    details = {
        "paper_id": paper_id,
        "is_consistent": is_consistent,
        "matching_chunks": len(new_chunk_ids) - len(missing_ids) - len(modified_ids),
        "total_new_chunks": len(new_chunk_ids),
        "total_stored_chunks": len(stored_ids),
        "missing_ids": sorted(list(missing_ids)),
        "modified_ids": sorted(list(modified_ids)),
        "stale_ids": sorted(list(stale_ids)),
        "status": "consistent" if is_consistent else "outdated",
    }
    return is_consistent, details


class IntegratedRAGPipeline:
    """
    Unified RAG retrieval pipeline orchestrating multi-paper indexing,
    extended metadata persistence in ChromaDB, synchronized BM25 search,
    and metadata-filtered hybrid retrieval with Reciprocal Rank Fusion.
    """

    def __init__(
        self,
        database_path: str = DEFAULT_CHROMA_PATH,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        self.database_path = database_path
        os.makedirs(database_path, exist_ok=True)

        self.adapter = PaperIngestionAdapter()
        self.vector_store = EnhancedVectorStore(database_path=database_path)
        self.embedding_generator = EmbeddingGenerator(model_name=embedding_model_name)
        self.semantic_engine = SemanticSearch(self.vector_store, self.embedding_generator)

        # In-memory chunk corpus and BM25 search engine
        self.chunks: list[dict[str, Any]] = []
        self.keyword_engine: KeywordSearch | None = None
        self.hybrid_engine: HybridSearch | None = None

        # Synchronize BM25 with any existing ChromaDB records
        self.rebuild_keyword_index()

    def rebuild_keyword_index(self) -> int:
        """
        Reconstructs the in-memory BM25 KeywordSearch index from all active records
        currently stored in ChromaDB, guaranteeing index parity across all papers.
        """
        try:
            stored = self.vector_store.collection.get(include=["documents", "metadatas"])
            stored_ids = stored.get("ids", []) or []
            stored_docs = stored.get("documents", []) or []
            stored_metas = stored.get("metadatas", []) or []
        except Exception as exc:
            logger.warning("Could not read ChromaDB collection for BM25 rebuild: %s", exc)
            stored_ids, stored_docs, stored_metas = [], [], []

        active_chunks: list[dict[str, Any]] = []
        for i, chunk_id in enumerate(stored_ids):
            meta = stored_metas[i] if i < len(stored_metas) else {}
            doc_text = stored_docs[i] if i < len(stored_docs) else ""
            active_chunks.append({
                "chunk_id": chunk_id,
                "text": doc_text,
                "paper_id": meta.get("paper_id", "unknown"),
                "paper_title": meta.get("paper_title", ""),
                "page_number": meta.get("page_number", 0),
                "section": meta.get("section", "FULL_TEXT"),
                "chunk_type": meta.get("chunk_type", "body_passage"),
                "dimension": meta.get("dimension", "body"),
                "provenance": meta.get("provenance", "unknown"),
                "source_type": meta.get("source_type", "unknown"),
                "confidence": float(meta.get("confidence", 1.0)),
                "metadata": meta,
            })

        self.chunks = active_chunks
        if active_chunks:
            self.keyword_engine = KeywordSearch(active_chunks)
            self.hybrid_engine = HybridSearch(self.semantic_engine, self.keyword_engine)
        else:
            self.keyword_engine = None
            self.hybrid_engine = None

        return len(active_chunks)

    def ingest_paper(
        self,
        paper_record: dict[str, Any],
        nlp_analysis: dict[str, Any] | None = None,
        force_reindex: bool = False,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> dict[str, Any]:
        """
        Ingests a single processed research paper (full-text or abstract-only)
        into the persistent ChromaDB collection and refreshes BM25.

        Applies per-paper consistency checking and reindexes only this paper,
        never deleting chunks belonging to other papers.
        """
        adapted_chunks = self.adapter.adapt_paper(
            paper_record=paper_record,
            nlp_analysis=nlp_analysis,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        if not adapted_chunks:
            return {
                "paper_id": paper_record.get("paper_id"),
                "status": "skipped_no_chunks",
                "chunks_ingested": 0,
            }

        paper_id = adapted_chunks[0]["paper_id"]

        # Check targeted index consistency for this paper
        is_consistent, details = check_paper_index_status(
            self.vector_store, paper_id, adapted_chunks
        )

        if is_consistent and not force_reindex:
            # Paper is already indexed and unchanged; keep existing embeddings
            self.rebuild_keyword_index()
            return {
                "paper_id": paper_id,
                "status": "already_indexed",
                "action": "skipped_reindex",
                "chunks_count": len(adapted_chunks),
                "details": details,
            }

        # Targeted reindexing: delete ONLY this paper's chunks from ChromaDB
        try:
            self.vector_store.collection.delete(where={"paper_id": paper_id})
        except Exception:
            pass  # Harmless if paper did not exist

        texts = [c["text"] for c in adapted_chunks]
        embeddings = self.embedding_generator.generate_embeddings(texts)
        self.vector_store.add_documents(adapted_chunks, embeddings)

        # Synchronize BM25 across all active records
        total_chunks = self.rebuild_keyword_index()

        return {
            "paper_id": paper_id,
            "status": "indexed",
            "action": "reindexed" if force_reindex else "newly_indexed",
            "chunks_ingested": len(adapted_chunks),
            "total_corpus_chunks": total_chunks,
            "details": details,
        }

    def ingest_paper_batch(
        self,
        papers: list[tuple[dict[str, Any], dict[str, Any] | None]],
        force_reindex: bool = False,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Ingests a list of (paper_record, nlp_analysis) tuples.
        """
        results: list[dict[str, Any]] = []
        for paper_record, nlp_analysis in papers:
            res = self.ingest_paper(
                paper_record=paper_record,
                nlp_analysis=nlp_analysis,
                force_reindex=force_reindex,
                chunk_size=chunk_size,
                overlap=overlap,
            )
            results.append(res)
        return results

    def ingest_sample_data(
        self,
        folder_path: str | Path | None = None,
        force_reindex: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Ingests Member 2's sample papers (paper_001.txt ... paper_005.txt),
        preserving backward compatibility with Member 2's benchmark suite.
        """
        raw_papers = load_papers(folder_path=folder_path)
        results: list[dict[str, Any]] = []

        for p in raw_papers:
            adapted_chunks = self.adapter.adapt_legacy_paper(p)
            paper_id = p["paper_id"]

            is_consistent, details = check_paper_index_status(
                self.vector_store, paper_id, adapted_chunks
            )

            if is_consistent and not force_reindex:
                results.append({
                    "paper_id": paper_id,
                    "status": "already_indexed",
                    "chunks_ingested": len(adapted_chunks),
                })
                continue

            try:
                self.vector_store.collection.delete(where={"paper_id": paper_id})
            except Exception:
                pass

            texts = [c["text"] for c in adapted_chunks]
            embeddings = self.embedding_generator.generate_embeddings(texts)
            self.vector_store.add_documents(adapted_chunks, embeddings)

            results.append({
                "paper_id": paper_id,
                "status": "indexed",
                "chunks_ingested": len(adapted_chunks),
            })

        self.rebuild_keyword_index()
        return results

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 3,
        k: int = 60,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Executes search using hybrid (RRF), semantic, or keyword retrieval.
        Applies metadata filters consistently across both retrieval streams before RRF.
        Normalizes all returned items to a standardized schema with abstract page numbers
        converted from sentinel 0 to None.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Search query cannot be empty.")

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        normalized_mode = mode.strip().lower()
        if normalized_mode not in ("hybrid", "semantic", "keyword"):
            raise ValueError(f"Invalid mode '{mode}'. Choose 'hybrid', 'semantic', or 'keyword'.")

        if not self.chunks:
            return []

        # Prepare ChromaDB where clause for semantic search
        where_clause: dict[str, Any] | None = None
        if filters:
            valid_filters = {k: v for k, v in filters.items() if v is not None}
            if len(valid_filters) == 1:
                where_clause = valid_filters
            elif len(valid_filters) > 1:
                where_clause = {"$and": [{k: v} for k, v in valid_filters.items()]}

        # Filter helper for in-memory keyword chunks
        def matches_filters(meta: dict[str, Any]) -> bool:
            if not filters:
                return True
            for fk, fv in filters.items():
                if fv is not None and meta.get(fk) != fv:
                    return False
            return True

        pool_size = max(top_k * 5, 20)

        # 1. Semantic Retrieval Stream
        semantic_results_list: list[dict[str, Any]] = []
        if normalized_mode in ("hybrid", "semantic"):
            query_emb = self.embedding_generator.generate_single_embedding(query.strip())
            kwargs: dict[str, Any] = {
                "query_embeddings": [query_emb.tolist()],
                "n_results": min(pool_size, self.vector_store.collection.count() or 1),
            }
            if where_clause:
                kwargs["where"] = where_clause

            try:
                raw_sem = self.vector_store.collection.query(**kwargs)
                s_ids = raw_sem["ids"][0] if raw_sem.get("ids") else []
                s_docs = raw_sem["documents"][0] if raw_sem.get("documents") else []
                s_metas = raw_sem["metadatas"][0] if raw_sem.get("metadatas") else []
                s_dists = raw_sem["distances"][0] if raw_sem.get("distances") else [0.0] * len(s_ids)

                for idx in range(len(s_ids)):
                    semantic_results_list.append({
                        "chunk_id": s_ids[idx],
                        "text": s_docs[idx],
                        "metadata": s_metas[idx],
                        "distance": float(s_dists[idx]),
                    })
            except Exception as exc:
                logger.warning("Semantic query failed: %s", exc)

        # 2. Keyword (BM25) Retrieval Stream
        keyword_results_list: list[dict[str, Any]] = []
        if normalized_mode in ("hybrid", "keyword") and self.keyword_engine:
            raw_kw = self.keyword_engine.search(query.strip(), top_k=len(self.chunks))
            for item in raw_kw:
                if matches_filters(item["metadata"]):
                    keyword_results_list.append(item)
                    if len(keyword_results_list) >= pool_size:
                        break

        # 3. Mode Selection & Fusion
        normalized_results: list[dict[str, Any]] = []

        if normalized_mode == "hybrid":
            fused: dict[str, dict[str, Any]] = {}

            # Process semantic ranks
            for rank, item in enumerate(semantic_results_list, start=1):
                c_id = item["chunk_id"]
                fused[c_id] = {
                    "chunk_id": c_id,
                    "text": item["text"],
                    "metadata": item["metadata"],
                    "rrf_score": 1.0 / (k + rank),
                }

            # Process keyword ranks
            for rank, item in enumerate(keyword_results_list, start=1):
                c_id = item["chunk_id"]
                if c_id not in fused:
                    fused[c_id] = {
                        "chunk_id": c_id,
                        "text": item["text"],
                        "metadata": item["metadata"],
                        "rrf_score": 0.0,
                    }
                fused[c_id]["rrf_score"] += 1.0 / (k + rank)

            ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)[:top_k]
            for r in ranked:
                normalized_results.append(
                    self._normalize_result(
                        chunk_id=r["chunk_id"],
                        text=r["text"],
                        metadata=r["metadata"],
                        score=float(r["rrf_score"]),
                        score_type="rrf_score",
                    )
                )

        elif normalized_mode == "semantic":
            for item in semantic_results_list[:top_k]:
                normalized_results.append(
                    self._normalize_result(
                        chunk_id=item["chunk_id"],
                        text=item["text"],
                        metadata=item["metadata"],
                        score=float(item["distance"]),
                        score_type="distance",
                    )
                )

        elif normalized_mode == "keyword":
            for item in keyword_results_list[:top_k]:
                normalized_results.append(
                    self._normalize_result(
                        chunk_id=item["chunk_id"],
                        text=item["text"],
                        metadata=item["metadata"],
                        score=float(item["score"]),
                        score_type="bm25_score",
                    )
                )

        return normalized_results

    def _normalize_result(
        self,
        chunk_id: str,
        text: str,
        metadata: dict[str, Any],
        score: float,
        score_type: str,
    ) -> dict[str, Any]:
        """
        Produces a standardized user-facing dictionary. Converts ChromaDB sentinel
        page numbers (0 or None) into None for abstract-only records.
        """
        raw_page = metadata.get("page_number")
        user_page = None if raw_page in (0, None, -1) else int(raw_page)

        return {
            "chunk_id": chunk_id,
            "paper_id": metadata.get("paper_id", "unknown"),
            "paper_title": metadata.get("paper_title", ""),
            "page_number": user_page,
            "section": metadata.get("section", "FULL_TEXT"),
            "chunk_type": metadata.get("chunk_type", "body_passage"),
            "dimension": metadata.get("dimension", "body"),
            "provenance": metadata.get("provenance", "unknown"),
            "source_type": metadata.get("source_type", "unknown"),
            "confidence": float(metadata.get("confidence", 1.0)),
            "text": text,
            "score": score,
            "score_type": score_type,
            "metadata": metadata,
        }

    def clear_paper(self, paper_id: str) -> None:
        """Deletes all chunks belonging to paper_id from ChromaDB and rebuilds BM25."""
        try:
            self.vector_store.collection.delete(where={"paper_id": paper_id})
        except Exception as exc:
            logger.warning("Error deleting paper %s from ChromaDB: %s", paper_id, exc)
        self.rebuild_keyword_index()
