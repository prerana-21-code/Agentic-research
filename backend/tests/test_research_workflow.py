"""
Backend Research Workflow & On-Demand Ingestion Tests
Validates POST /api/research endpoint, paper deduplication,
Member 1 discovery integration, ChromaDB indexing, and RRF retrieval.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.main import app


class TestResearchWorkflowEndpoints(unittest.TestCase):
    """Test suite for on-demand research workflow."""

    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_01_validation_empty_query(self):
        """Verify POST /api/research rejects empty query with 422."""
        res = self.client.post("/api/research", json={"query": ""})
        self.assertEqual(res.status_code, 422)

    def test_02_health_contains_all_modules(self):
        """Verify GET /api/health contains dynamic module details for all 5 modules."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("module_details", data)
        module_ids = {m["id"] for m in data["module_details"]}
        self.assertTrue({"fastapi_bridge", "paper_processing", "rag_engine", "vector_store", "bm25_index"}.issubset(module_ids))
        for m in data["module_details"]:
            self.assertEqual(m["statusType"], "connected")

    def test_03_research_workflow_with_reused_corpus(self):
        """Verify POST /api/research identifies existing corpus papers and reuses them."""
        payload = {
            "query": "How are CNNs used to detect diseases in MRI images?",
            "max_papers": 2,
            "mode": "hybrid",
            "top_k": 3,
        }
        res = self.client.post("/api/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "completed")
        self.assertGreater(len(data.get("execution_steps", [])), 0)
        self.assertGreater(len(data.get("results", [])), 0)
        first_res = data["results"][0]
        self.assertIn("chunk_id", first_res)
        self.assertIn("score", first_res)
        self.assertEqual(first_res["score_type"], "rrf_score")

    def test_04_search_with_auto_discover_flag(self):
        """Verify POST /api/search with auto_discover=True runs research workflow."""
        payload = {
            "query": "What are deep learning models for brain tumor classification?",
            "mode": "hybrid",
            "top_k": 3,
            "auto_discover": True,
            "max_papers": 1,
        }
        res = self.client.post("/api/search", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreater(len(data.get("results", [])), 0)
        self.assertIsNotNone(data.get("execution_steps"))

    @patch("backend.research_workflow.OpenAlexClient.search_papers")
    def test_05_mocked_openalex_ingestion(self, mock_search):
        """Verify end-to-end ingestion of a newly discovered mock paper."""
        import uuid
        unique_id = f"W_test_{uuid.uuid4().hex[:8]}"
        mock_paper = {
            "paper_id": unique_id,
            "openalex_id": f"https://openalex.org/{unique_id}",
            "title": f"Quantum Error Correction with Surface Codes {unique_id}",
            "authors": ["Alice Quantum", "Bob Code"],
            "year": 2025,
            "doi": f"https://doi.org/10.1000/{unique_id}",
            "abstract": "We evaluate surface codes for quantum error correction. Our method achieves a threshold error rate of 1.0 percent on the simulated planar lattice benchmark.",
            "publication_type": "journal-article",
            "concepts": ["Quantum Computing", "Surface Code", "Fault Tolerance"],
            "landing_page_url": f"https://doi.org/10.1000/{unique_id}",
            "source_type": "abstract_only",
            "full_text": None,
        }
        mock_search.return_value = [mock_paper]

        payload = {
            "query": f"What are surface codes in quantum error correction {unique_id}?",
            "max_papers": 1,
            "mode": "hybrid",
            "top_k": 3,
        }
        res = self.client.post("/api/research", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "completed")
        self.assertEqual(data.get("newly_indexed_count"), 1)
        self.assertTrue(any(p["paper_id"] == unique_id for p in data.get("discovered_papers", [])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
