"""
Main Entry Point for the RAG Engine.
Orchestrates ingestion, sentence-aware chunking, dense vector embeddings,
dedicated workspace ChromaDB storage, BM25 keyword indexing, hybrid RRF retrieval,
and optional benchmarking.
"""

import os
import sys
import argparse
from pathlib import Path

# Ensure repository root is in sys.path when executed directly
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from rag_engine.paper_loader import load_papers
from rag_engine.chunking import create_chunks
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore
from rag_engine.semantic_search import SemanticSearch
from rag_engine.keyword_search import KeywordSearch
from rag_engine.hybrid_search import HybridSearch
from rag_engine.evaluation import precision_at_k, recall_at_k, mean_reciprocal_rank

# Dedicated workspace ChromaDB storage path (Option A: Workspace Isolation)
DEFAULT_CHROMA_PATH = str(repo_root / "data" / "chroma_db")


class RAGPipeline:
    """
    Encapsulates all initialized RAG components, in-memory chunk indexes,
    and search engines for the research assistant.
    """

    def __init__(
        self,
        papers,
        chunks,
        vector_store,
        embedding_generator,
        semantic_engine,
        keyword_engine,
        hybrid_engine,
        database_path: str = DEFAULT_CHROMA_PATH,
        index_status: dict = None
    ):
        self.papers = papers
        self.chunks = chunks
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.semantic_engine = semantic_engine
        self.keyword_engine = keyword_engine
        self.hybrid_engine = hybrid_engine
        self.database_path = database_path
        self.index_status = index_status or {}

    def search(self, query: str, mode: str = "hybrid", top_k: int = 3, k: int = 60) -> list:
        """Convenience method delegating to the top-level search function."""
        return search(self, query=query, mode=mode, top_k=top_k, k=k)


def check_index_consistency(vector_store: VectorStore, current_chunks: list) -> tuple:
    """
    Performs a deep consistency verification between the current in-memory chunks
    and the stored ChromaDB collection records.

    Verifies:
    1. Chunk ID presence.
    2. Character-level document text exact match.
    3. Metadata exact match (paper_id, paper_title, page_number).
    4. Detects stale chunk IDs belonging to current papers that are no longer in current_chunks.

    Returns:
    (is_consistent: bool, details: dict)
    """
    current_chunk_ids = {c["chunk_id"] for c in current_chunks}
    current_chunk_map = {c["chunk_id"]: c for c in current_chunks}
    current_paper_ids = {c["paper_id"] for c in current_chunks}

    try:
        stored = vector_store.collection.get(include=["documents", "metadatas"])
        stored_ids = stored.get("ids", []) or []
        stored_docs = stored.get("documents", []) or []
        stored_metas = stored.get("metadatas", []) or []
    except Exception as e:
        return False, {
            "error": str(e),
            "missing_ids": sorted(list(current_chunk_ids)),
            "modified_ids": [],
            "stale_ids": [],
            "status": "unreachable"
        }

    stored_map = {}
    for i, s_id in enumerate(stored_ids):
        doc = stored_docs[i] if i < len(stored_docs) else ""
        meta = stored_metas[i] if i < len(stored_metas) else {}
        stored_map[s_id] = {"text": doc, "metadata": meta or {}}

    missing_ids = set()
    modified_ids = set()

    for chunk_id, chunk in current_chunk_map.items():
        if chunk_id not in stored_map:
            missing_ids.add(chunk_id)
            continue

        stored_item = stored_map[chunk_id]
        stored_text = stored_item.get("text", "")
        stored_meta = stored_item.get("metadata", {})

        # Compare document text
        if stored_text != chunk["text"]:
            modified_ids.add(chunk_id)
            continue

        # Compare metadata fields
        if (
            stored_meta.get("paper_id") != chunk["paper_id"]
            or stored_meta.get("paper_title") != chunk["paper_title"]
            or stored_meta.get("page_number") != chunk.get("page_number", 1)
        ):
            modified_ids.add(chunk_id)

    # Identify stale chunks in ChromaDB for current papers that are no longer in current_chunks
    stale_ids = set()
    for s_id, s_data in stored_map.items():
        s_meta = s_data.get("metadata", {})
        if s_meta.get("paper_id") in current_paper_ids and s_id not in current_chunk_ids:
            stale_ids.add(s_id)

    is_consistent = (
        len(missing_ids) == 0
        and len(modified_ids) == 0
        and len(stale_ids) == 0
        and len(current_chunk_ids) > 0
    )

    details = {
        "total_current_chunks": len(current_chunk_ids),
        "total_stored_records": len(stored_ids),
        "matching_chunks": len(current_chunk_ids) - len(missing_ids) - len(modified_ids),
        "missing_ids": sorted(list(missing_ids)),
        "modified_ids": sorted(list(modified_ids)),
        "stale_ids": sorted(list(stale_ids)),
        "status": "consistent" if is_consistent else "outdated"
    }

    return is_consistent, details


def initialize_rag_pipeline(
    folder_path=None,
    database_path: str = None,
    force_reindex: bool = False,
    chunk_size: int = 500,
    overlap: int = 100
) -> RAGPipeline:
    """
    Initializes the RAG pipeline using a dedicated workspace database path.

    1. Loads papers from disk.
    2. Generates sentence-aware chunks.
    3. Resolves database_path (defaults to repo_root/data/chroma_db) and ensures directories exist.
    4. Connects to VectorStore(database_path=database_path).
    5. Performs deep index consistency check (comparing IDs, texts, and metadata).
    6. If consistent and force_reindex=False:
       - Skips embedding generation and ChromaDB writes completely.
    7. If outdated or force_reindex=True:
       - Prunes ONLY specific stale chunk IDs verified to belong to this corpus.
       - Generates embeddings and upserts current chunks.
    8. Builds in-memory BM25 index and connects HybridSearch.
    """
    # 1. Resolve and ensure dedicated database directory
    if database_path is None:
        database_path = DEFAULT_CHROMA_PATH

    os.makedirs(database_path, exist_ok=True)

    # 2. Load papers
    papers = load_papers(folder_path=folder_path)
    if not papers:
        raise ValueError("No research papers found in the specified directory.")

    # 3. Chunk papers
    all_chunks = []
    for paper in papers:
        chunks = create_chunks(
            text=paper["text"],
            paper_id=paper["paper_id"],
            paper_title=paper["paper_title"],
            page_number=1,
            chunk_size=chunk_size,
            overlap=overlap
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError("No text chunks generated from the loaded papers.")

    # 4. Connect to persistent ChromaDB at the dedicated workspace path
    vector_store = VectorStore(database_path=database_path)

    # 5. Deep Index Consistency Verification
    is_consistent, details = check_index_consistency(vector_store, all_chunks)

    if not force_reindex and is_consistent:
        print(f"[RAG Engine] Index verified consistent: {details['matching_chunks']} chunks match ChromaDB exactly.")
        print(f"[RAG Engine] Dedicated workspace DB: {database_path}")
        print("[RAG Engine] Skipping embedding re-computation and re-indexing.")
        embedding_generator = EmbeddingGenerator()
    else:
        # Determine specific reason
        reasons = []
        if force_reindex:
            reasons.append("force_reindex requested")
        if details["missing_ids"]:
            reasons.append(f"{len(details['missing_ids'])} missing chunks")
        if details["modified_ids"]:
            reasons.append(f"{len(details['modified_ids'])} modified chunks")
        if details["stale_ids"]:
            reasons.append(f"{len(details['stale_ids'])} stale chunks")

        reason_str = ", ".join(reasons) if reasons else "index mismatch or empty store"
        print(f"[RAG Engine] Indexing required ({reason_str}).")
        print(f"[RAG Engine] Dedicated workspace DB: {database_path}")

        # Safe targeted cleanup of stale chunks belonging to this corpus
        if details["stale_ids"]:
            print(f"[RAG Engine] Pruning {len(details['stale_ids'])} stale chunk IDs from current papers: {details['stale_ids']}")
            try:
                vector_store.collection.delete(ids=details["stale_ids"])
            except Exception as e:
                print(f"[RAG Engine] Warning: Could not prune stale chunks: {e}")

        print(f"[RAG Engine] Computing embeddings for {len(all_chunks)} chunks...")
        embedding_generator = EmbeddingGenerator()
        texts = [chunk["text"] for chunk in all_chunks]
        embeddings = embedding_generator.generate_embeddings(texts)

        # Upsert adds new chunks and updates modified ones in-place
        vector_store.add_documents(all_chunks, embeddings)

    # 6. Initialize search engines
    semantic_engine = SemanticSearch(vector_store, embedding_generator)
    keyword_engine = KeywordSearch(all_chunks)
    hybrid_engine = HybridSearch(semantic_engine, keyword_engine)

    return RAGPipeline(
        papers=papers,
        chunks=all_chunks,
        vector_store=vector_store,
        embedding_generator=embedding_generator,
        semantic_engine=semantic_engine,
        keyword_engine=keyword_engine,
        hybrid_engine=hybrid_engine,
        database_path=database_path,
        index_status=details
    )


def search(
    pipeline: RAGPipeline,
    query: str,
    mode: str = "hybrid",
    top_k: int = 3,
    k: int = 60
) -> list:
    """
    Executes search against the RAG pipeline using the requested mode.

    Parameters:
    - pipeline: Initialized RAGPipeline instance.
    - query: Research question string.
    - mode: Search mode ('hybrid', 'semantic', 'keyword').
    - top_k: Number of ranked passages to return (must be positive).
    - k: RRF smoothing constant (for hybrid search).

    Returns:
    - list[dict]: Standardized structured results.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query cannot be empty.")

    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be a positive integer.")

    normalized_mode = mode.strip().lower()
    results = []

    if normalized_mode == "hybrid":
        raw_results = pipeline.hybrid_engine.search(query.strip(), top_k=top_k, k=k)
        for item in raw_results:
            results.append({
                "chunk_id": item["chunk_id"],
                "paper_id": item["metadata"]["paper_id"],
                "paper_title": item["metadata"]["paper_title"],
                "page_number": item["metadata"].get("page_number", 1),
                "text": item["text"],
                "score": float(item["rrf_score"]),
                "score_type": "rrf_score"
            })

    elif normalized_mode == "semantic":
        raw_results = pipeline.semantic_engine.search(query.strip(), top_k=top_k)
        ids = raw_results["ids"][0] if raw_results["ids"] else []
        documents = raw_results["documents"][0] if raw_results["documents"] else []
        metadatas = raw_results["metadatas"][0] if raw_results["metadatas"] else []
        distances = raw_results["distances"][0] if raw_results.get("distances") else [0.0] * len(ids)

        for i in range(len(ids)):
            results.append({
                "chunk_id": ids[i],
                "paper_id": metadatas[i]["paper_id"],
                "paper_title": metadatas[i]["paper_title"],
                "page_number": metadatas[i].get("page_number", 1),
                "text": documents[i],
                "score": float(distances[i]),
                "score_type": "distance"  # Accurately labelled as ChromaDB distance
            })

    elif normalized_mode == "keyword":
        raw_results = pipeline.keyword_engine.search(query.strip(), top_k=top_k)
        for item in raw_results:
            results.append({
                "chunk_id": item["chunk_id"],
                "paper_id": item["metadata"]["paper_id"],
                "paper_title": item["metadata"]["paper_title"],
                "page_number": item["metadata"].get("page_number", 1),
                "text": item["text"],
                "score": float(item["score"]),
                "score_type": "bm25_score"
            })

    else:
        raise ValueError(
            f"Invalid search mode '{mode}'. Choose from 'hybrid', 'semantic', or 'keyword'."
        )

    return results


def evaluate_pipeline(
    pipeline: RAGPipeline,
    evaluation_data: list = None,
    k: int = 3,
    mode: str = "hybrid"
) -> dict:
    """
    Evaluates retrieval performance against labeled benchmark question/relevant_ids pairs.
    Optional and kept separate from normal query flow.
    """
    if evaluation_data is None:
        # Default benchmark set from test_evaluation.py
        evaluation_data = [
            {
                "question": "How are CNNs used to detect diseases in MRI images?",
                "relevant_ids": ["paper_001_chunk_1", "paper_003_chunk_1"]
            },
            {
                "question": "How do Vision Transformers analyse medical images?",
                "relevant_ids": ["paper_002_chunk_1", "paper_002_chunk_2"]
            },
            {
                "question": "What techniques are used for brain tumour detection?",
                "relevant_ids": ["paper_003_chunk_1", "paper_003_chunk_2"]
            },
            {
                "question": "Which machine learning algorithms predict disease risk?",
                "relevant_ids": ["paper_004_chunk_1", "paper_004_chunk_2"]
            },
            {
                "question": "How is NLP used to analyse biomedical research papers?",
                "relevant_ids": ["paper_005_chunk_1", "paper_005_chunk_2"]
            }
        ]

    precision_scores = []
    recall_scores = []
    mrr_scores = []
    detailed_results = []

    for item in evaluation_data:
        q = item["question"]
        relevant = item["relevant_ids"]

        search_results = search(pipeline, query=q, mode=mode, top_k=k)
        retrieved_ids = [res["chunk_id"] for res in search_results]

        p = precision_at_k(retrieved_ids, relevant, k=k)
        r = recall_at_k(retrieved_ids, relevant, k=k)
        mrr = mean_reciprocal_rank(retrieved_ids, relevant)

        precision_scores.append(p)
        recall_scores.append(r)
        mrr_scores.append(mrr)

        detailed_results.append({
            "question": q,
            "relevant_ids": relevant,
            "retrieved_ids": retrieved_ids,
            "precision_at_k": p,
            "recall_at_k": r,
            "mrr": mrr
        })

    avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
    avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0
    avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0

    return {
        "mode": mode,
        "k": k,
        "average_precision_at_k": round(avg_precision, 4),
        "average_recall_at_k": round(avg_recall, 4),
        "average_mrr": round(avg_mrr, 4),
        "detailed_results": detailed_results
    }


def main():
    """Command-line demonstration interface."""
    parser = argparse.ArgumentParser(
        description="Agentic Research Assistant - Hybrid RAG Engine"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default="How are CNNs used to detect diseases in MRI images?",
        help="Research question to retrieve passages for."
    )
    parser.add_argument(
        "--mode",
        choices=["hybrid", "semantic", "keyword"],
        default="hybrid",
        help="Search strategy: 'hybrid' (RRF, default), 'semantic' (ChromaDB), or 'keyword' (BM25)."
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of passages to return (default: 3)."
    )
    parser.add_argument(
        "--db-path",
        default=DEFAULT_CHROMA_PATH,
        help=f"Path to ChromaDB storage directory (default: {DEFAULT_CHROMA_PATH})."
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Force re-chunking and re-generating embeddings into ChromaDB."
    )
    parser.add_argument(
        "--eval",
        action="store_true",
        help="Run optional benchmark evaluation across all 3 search modes."
    )

    args = parser.parse_args()

    print("=" * 70)
    print("      AGENTIC RESEARCH ASSISTANT - HYBRID RAG PIPELINE")
    print("=" * 70)

    pipeline = initialize_rag_pipeline(
        database_path=args.db_path,
        force_reindex=args.reindex
    )

    print(f"\n[Database Path]   : {pipeline.database_path}")
    print(f"[Search Mode]     : {args.mode.upper()}")
    print(f"[Research Query]  : {args.query}")
    print(f"[Passages (Top-K)]: {args.top_k}")
    print("-" * 70)

    results = search(pipeline, query=args.query, mode=args.mode, top_k=args.top_k)

    for rank, res in enumerate(results, start=1):
        print(f"\n[Rank {rank}] Chunk ID: {res['chunk_id']}")
        print(f"Paper Title: {res['paper_title']} (Paper ID: {res['paper_id']})")
        print(f"Score ({res['score_type']}): {round(res['score'], 6)}")
        print(f"Text Passage: {res['text']}")

    if args.eval:
        print("\n" + "=" * 70)
        print("          BENCHMARK EVALUATION (PRECISION, RECALL, MRR)")
        print("=" * 70)
        for eval_mode in ["semantic", "keyword", "hybrid"]:
            eval_metrics = evaluate_pipeline(pipeline, mode=eval_mode, k=args.top_k)
            print(f"\nMode: {eval_mode.upper()} Retrieval")
            print(f"  • Avg Precision@{args.top_k}: {eval_metrics['average_precision_at_k']}")
            print(f"  • Avg Recall@{args.top_k}   : {eval_metrics['average_recall_at_k']}")
            print(f"  • Avg MRR        : {eval_metrics['average_mrr']}")

    print("\n" + "=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()
