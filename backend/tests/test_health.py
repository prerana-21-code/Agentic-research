"""
Backend Health & System Integration Tests
Validates FastAPI application startup, lifespan pipeline initialization,
CORS configuration, GET /api/health response, and Swagger docs availability.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# Ensure repo root is in sys.path
repo_root = Path(__file__).resolve().parent.parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from fastapi.testclient import TestClient
from backend.main import app


class TestBackendFoundation(unittest.TestCase):
    """Test suite for Phase 5 FastAPI backend foundation."""

    @classmethod
    def setUpClass(cls):
        """Initialize TestClient which triggers the application lifespan."""
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        """Exit client context, triggering lifespan shutdown."""
        cls.client_context.__exit__(None, None, None)

    def test_01_root_endpoint(self):
        """Verify GET / returns 200 with service information and links."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("service"), "Agentic Research Assistant API")
        self.assertEqual(data.get("status"), "online")
        self.assertIn("docs_url", data)
        self.assertIn("health_url", data)

    def test_02_health_endpoint(self):
        """Verify GET /api/health returns 200 with all modules and pipeline metadata."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("version"), "0.1.0")

        # Modules check
        modules = data.get("modules", {})
        self.assertEqual(modules.get("fastapi"), "running")
        self.assertEqual(modules.get("paper_processing"), "ready")
        self.assertEqual(modules.get("rag_engine"), "ready")
        self.assertEqual(modules.get("chromadb"), "connected")
        self.assertEqual(modules.get("bm25"), "synchronized")

        # Pipeline singleton metadata check
        pipeline_info = data.get("pipeline", {})
        self.assertIn("database_path", pipeline_info)
        self.assertEqual(pipeline_info.get("embedding_dimension"), 384)
        self.assertGreaterEqual(pipeline_info.get("active_chunks", 0), 0)
        self.assertGreaterEqual(pipeline_info.get("chroma_records", 0), 0)

    def test_03_swagger_docs(self):
        """Verify /docs Swagger UI is accessible."""
        res = self.client.get("/docs")
        self.assertEqual(res.status_code, 200)
        self.assertIn("swagger-ui", res.text.lower())

    def test_04_openapi_schema(self):
        """Verify /openapi.json schema returns valid spec with title."""
        res = self.client.get("/openapi.json")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("info", {}).get("title"), "Agentic Research Assistant API")

    def test_05_cors_headers(self):
        """Verify CORS preflight / Origin headers for local Vite dev server."""
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        }
        res = self.client.options("/api/health", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("access-control-allow-origin"), "http://localhost:5173")


if __name__ == "__main__":
    unittest.main(verbosity=2)
