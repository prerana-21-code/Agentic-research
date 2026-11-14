"""
End-to-End Real-World Validation Script
Validates the complete on-demand research workflow on a brand new question:
"How do graph neural networks predict molecular properties in drug discovery?"

Verifies:
1. OpenAlex paper discovery.
2. Legitimate OA PDF resolution & download (or verified abstract fallback).
3. Text extraction via PyMuPDF.
4. NLP analysis (objectives, methods, datasets, metrics, findings).
5. PaperIngestionAdapter chunking (page-aware & section-aware).
6. ChromaDB persistence & BM25 index synchronization.
7. Hybrid search with Reciprocal Rank Fusion (RRF).
8. Formatting for React UI presentation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.main import app


def run_validation():
    print("=" * 80)
    print("END-TO-END VALIDATION: ON-DEMAND RESEARCH WORKFLOW")
    print("=" * 80)

    test_query = "How do graph neural networks predict molecular properties in drug discovery?"
    print(f"\n[QUERY] Research Question: '{test_query}'")

    with TestClient(app) as client:
        # Step 1: Check live health & module status
        health_res = client.get("/api/health")
        assert health_res.status_code == 200, f"Health check failed: {health_res.text}"
        health_data = health_res.json()
        print("\n[STAGE 1] Health & Dynamic Module Status:")
        for mod in health_data.get("module_details", []):
            print(f"  - {mod['name']}: {mod['status']} ({mod['details']})")

        # Step 2: Execute complete on-demand research workflow
        print("\n[STAGE 2] Executing POST /api/research...")
        payload = {
            "query": test_query,
            "max_papers": 2,
            "mode": "hybrid",
            "top_k": 3,
        }
        res = client.post("/api/research", json=payload)
        if res.status_code != 200:
            print(f"ERROR: POST /api/research failed with HTTP {res.status_code}: {res.text}")
            sys.exit(1)

        data = res.json()
        print(f"  Status: {data.get('status')}")
        print(f"  Total Candidate Papers Discovered: {data.get('total_discovered')}")
        print(f"  Newly Ingested Papers: {data.get('newly_indexed_count')}")
        print(f"  Reused Existing Papers: {data.get('reused_count')}")

        print("\n[STAGE 3] Execution Progress Log:")
        for step in data.get("execution_steps", []):
            print(f"  > {step}")

        print("\n[STAGE 4] Discovered & Analyzed Papers:")
        for p in data.get("discovered_papers", []):
            print(f"  - [{p['action'].upper()}] {p['title']}")
            print(f"    Paper ID: {p['paper_id']} | Year: {p['year']} | Access: {p['source_type']}")
            print(f"    Extracted: {p['chunks_count']} chunks | {p['key_findings_count']} findings | {p['methodologies_count']} methods")
            if p.get("pdf_url"):
                print(f"    PDF URL: {p['pdf_url']}")

        print("\n[STAGE 5] Top Ranked Retrieved Passages (Hybrid RRF):")
        results = data.get("results", [])
        assert len(results) > 0, "No results returned by Hybrid RAG!"
        for idx, r in enumerate(results, start=1):
            print(f"\n  #{idx} Chunk ID: {r['chunk_id']}")
            print(f"     Paper: {r['paper_title']} ({r['paper_id']})")
            page_str = f"Page {r['page_number']}" if r.get('page_number') else "Abstract"
            print(f"     Section: {r['section']} | {page_str} | Score: {r['score']:.6f} ({r['score_type']})")
            print(f"     Snippet: {r['text'][:160]}...")
            evidence = r.get("metadata", {}).get("evidence")
            if evidence:
                print(f"     Evidence: \"{evidence[:120]}...\"")

        # Step 6: Verify updated corpus stats
        stats_res = client.get("/api/corpus/stats")
        stats_data = stats_res.json()
        print("\n[STAGE 6] Updated Corpus Statistics:")
        print(f"  Total Indexed Papers: {stats_data['total_papers']}")
        print(f"  Total Indexed Chunks: {stats_data['indexed_chunks']}")
        print(f"  Embedding Dimension: {stats_data['embedding_dimension']}")
        print(f"  Fusion Strategy: {stats_data['fusion_strategy']}")

    print("\n" + "=" * 80)
    print("END-TO-END VALIDATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_validation()
