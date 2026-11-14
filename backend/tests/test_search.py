"""
Backend Search & Corpus Stats Tests
Validates POST /api/search and GET /api/corpus/stats endpoints.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.main import app


class TestSearchEndpoints(unittest.TestCase):
    """Test suite for search and corpus statistics endpoints."""

    @classmethod
    def setUpClass(cls):
        """Initialize TestClient which triggers the application lifespan."""
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        """Exit client context, triggering lifespan shutdown."""
        cls.client_context.__exit__(None, None, None)

    def test_01_corpus_stats(self):
        """Verify GET /api/corpus/stats returns live corpus metrics."""
        res = self.client.get("/api/corpus/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(data.get("total_papers", 0), 0)
        self.assertGreater(data.get("indexed_chunks", 0), 0)
        self.assertEqual(data.get("embedding_dimension"), 384)
        self.assertEqual(data.get("embedding_model"), "all-MiniLM-L6-v2")
        self.assertIn("Reciprocal Rank Fusion", data.get("fusion_strategy"))
        self.assertIn("paper_001", data.get("indexed_paper_ids", []))

    def test_02_hybrid_search(self):
        """Verify POST /api/search executes hybrid search with RRF scores."""
        payload = {
            "query": "How are CNNs used to detect diseases in MRI images?",
            "mode": "hybrid",
            "top_k": 3,
        }
        res = self.client.post("/api/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("mode"), "hybrid")
        self.assertEqual(data.get("top_k"), 3)
        self.assertGreater(data.get("total_results", 0), 0)

        results = data.get("results", [])
        self.assertGreater(len(results), 0)

        # Check result structure
        top_res = results[0]
        self.assertIn("chunk_id", top_res)
        self.assertIn("paper_id", top_res)
        self.assertIn("text", top_res)
        self.assertEqual(top_res.get("score_type"), "rrf_score")
        self.assertGreater(top_res.get("score", 0), 0)

    def test_03_semantic_search(self):
        """Verify POST /api/search executes semantic vector search."""
        payload = {
            "query": "Vision Transformers in biomedical imagery",
            "mode": "semantic",
            "top_k": 2,
        }
        res = self.client.post("/api/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("mode"), "semantic")
        results = data.get("results", [])
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].get("score_type"), "distance")

    def test_04_keyword_search(self):
        """Verify POST /api/search executes BM25 keyword search."""
        payload = {
            "query": "tumour segmentation multimodal MRI FLAIR",
            "mode": "keyword",
            "top_k": 2,
        }
        res = self.client.post("/api/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("mode"), "keyword")
        results = data.get("results", [])
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].get("score_type"), "bm25_score")

    def test_05_search_with_metadata_filter(self):
        """Verify POST /api/search applies pre-RRF metadata filters."""
        payload = {
            "query": "deep learning disease classification",
            "mode": "hybrid",
            "top_k": 3,
            "filters": {"paper_id": "paper_001"},
        }
        res = self.client.post("/api/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        for item in data.get("results", []):
            self.assertEqual(item.get("paper_id"), "paper_001")

    def test_06_validation_empty_query(self):
        """Verify POST /api/search rejects empty query with 422 Unprocessable Entity."""
        res = self.client.post("/api/search", json={"query": "", "mode": "hybrid"})
        self.assertEqual(res.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)
