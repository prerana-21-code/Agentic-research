"""
Unit tests for OpenAlexClient.
Tests all paper retrieval, abstract reconstruction, pagination, error handling,
and schema normalization using mocked HTTP responses without live API access.
"""

import unittest
from unittest.mock import MagicMock, patch
import requests

from paper_processing.openalex_client import (
    OpenAlexClient,
    OpenAlexError,
    OpenAlexAPIError,
    OpenAlexNetworkError,
    OpenAlexTimeoutError,
)


class TestOpenAlexClient(unittest.TestCase):
    """Unit tests for the OpenAlexClient implementation."""

    def setUp(self):
        """Set up client instance with a mock session."""
        self.mock_session = MagicMock(spec=requests.Session)
        self.client = OpenAlexClient(
            api_key=None,
            email="researcher@example.edu",
            timeout=10.0,
            session=self.mock_session,
        )

    # -------------------------------------------------------------------------
    # Abstract Reconstruction Tests
    # -------------------------------------------------------------------------

    def test_reconstruct_abstract_success(self):
        """Test accurate reconstruction of inverted index into plain text."""
        inverted_index = {
            "Deep": [0],
            "learning": [1],
            "is": [2],
            "effective": [3],
            "for": [4],
            "medical": [5],
            "imaging": [6],
            "tasks.": [7],
        }
        abstract = OpenAlexClient.reconstruct_abstract(inverted_index)
        expected = "Deep learning is effective for medical imaging tasks."
        self.assertEqual(abstract, expected)

    def test_reconstruct_abstract_unordered_positions(self):
        """Test reconstruction when dictionary keys and position tokens are unordered."""
        inverted_index = {
            "networks": [2],
            "Neural": [0],
            "support": [3],
            "diagnostics": [4],
            "recurrent": [1],
        }
        abstract = OpenAlexClient.reconstruct_abstract(inverted_index)
        expected = "Neural recurrent networks support diagnostics"
        self.assertEqual(abstract, expected)

    def test_reconstruct_abstract_missing_or_empty(self):
        """Test graceful handling of missing, empty, or None inverted indexes."""
        self.assertEqual(OpenAlexClient.reconstruct_abstract(None), "")
        self.assertEqual(OpenAlexClient.reconstruct_abstract({}), "")
        self.assertEqual(OpenAlexClient.reconstruct_abstract("not a dict"), "")

    def test_reconstruct_abstract_malformed_entries(self):
        """Test skipping malformed positions or non-integer indices."""
        inverted_index = {
            "Valid": [0],
            "Bad": ["not-an-int", None],
            "Text": [1],
        }
        abstract = OpenAlexClient.reconstruct_abstract(inverted_index)
        self.assertEqual(abstract, "Valid Text")

    # -------------------------------------------------------------------------
    # Successful Retrieval & Normalization Tests
    # -------------------------------------------------------------------------

    def test_search_papers_successful_single_result(self):
        """Test single paper retrieval with all fields present and standardized schema."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"count": 1, "next_cursor": None},
            "results": [
                {
                    "id": "https://openalex.org/W2741809807",
                    "title": "Deep Residual Learning for Image Recognition",
                    "publication_year": 2016,
                    "doi": "https://doi.org/10.1109/cvpr.2016.90",
                    "type": "journal-article",
                    "authorships": [
                        {"author": {"display_name": "Kaiming He"}},
                        {"author": {"display_name": "Xiangyu Zhang"}},
                    ],
                    "concepts": [
                        {"display_name": "Computer vision"},
                        {"display_name": "Artificial intelligence"},
                    ],
                    "abstract_inverted_index": {
                        "Deeper": [0],
                        "neural": [1],
                        "networks": [2],
                        "are": [3],
                        "harder": [4],
                        "to": [5],
                        "train.": [6],
                    },
                    "primary_location": {
                        "landing_page_url": "https://ieeexplore.ieee.org/document/7780459"
                    },
                }
            ],
        }
        self.mock_session.get.return_value = mock_response

        papers = self.client.search_papers(topic="residual networks", max_results=1)

        self.assertEqual(len(papers), 1)
        paper = papers[0]

        # Verify standardized schema
        self.assertEqual(paper["paper_id"], "W2741809807")
        self.assertEqual(paper["openalex_id"], "https://openalex.org/W2741809807")
        self.assertEqual(paper["title"], "Deep Residual Learning for Image Recognition")
        self.assertEqual(paper["authors"], ["Kaiming He", "Xiangyu Zhang"])
        self.assertEqual(paper["year"], 2016)
        self.assertEqual(paper["doi"], "https://doi.org/10.1109/cvpr.2016.90")
        self.assertEqual(paper["abstract"], "Deeper neural networks are harder to train.")
        self.assertEqual(paper["publication_type"], "journal-article")
        self.assertEqual(paper["concepts"], ["Computer vision", "Artificial intelligence"])
        self.assertEqual(paper["landing_page_url"], "https://ieeexplore.ieee.org/document/7780459")
        self.assertEqual(paper["source_type"], "abstract_only")
        self.assertIsNone(paper["full_text"])

    def test_search_papers_multiple_results(self):
        """Test retrieving multiple papers within max_results limit."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"count": 3, "next_cursor": None},
            "results": [
                {"id": "https://openalex.org/W1", "title": "Paper 1"},
                {"id": "https://openalex.org/W2", "title": "Paper 2"},
                {"id": "https://openalex.org/W3", "title": "Paper 3"},
            ],
        }
        self.mock_session.get.return_value = mock_response

        papers = self.client.search_papers(topic="machine learning", max_results=2)

        self.assertEqual(len(papers), 2)
        self.assertEqual(papers[0]["paper_id"], "W1")
        self.assertEqual(papers[1]["paper_id"], "W2")

    def test_search_papers_missing_metadata(self):
        """Test normalization when metadata fields (authors, doi, concepts) are missing."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"count": 1, "next_cursor": None},
            "results": [
                {
                    "id": "https://openalex.org/W999",
                    "title": None,
                    "publication_year": None,
                    "doi": None,
                    "type": None,
                    "authorships": None,
                    "concepts": None,
                    "primary_location": None,
                    "abstract_inverted_index": None,
                }
            ],
        }
        self.mock_session.get.return_value = mock_response

        papers = self.client.search_papers(topic="sparse data", max_results=1)

        self.assertEqual(len(papers), 1)
        paper = papers[0]
        self.assertEqual(paper["paper_id"], "W999")
        self.assertEqual(paper["openalex_id"], "https://openalex.org/W999")
        self.assertEqual(paper["title"], "")
        self.assertEqual(paper["authors"], [])
        self.assertIsNone(paper["year"])
        self.assertIsNone(paper["doi"])
        self.assertEqual(paper["abstract"], "")
        self.assertEqual(paper["publication_type"], "")
        self.assertEqual(paper["concepts"], [])
        self.assertEqual(paper["landing_page_url"], "https://openalex.org/W999")
        self.assertEqual(paper["source_type"], "abstract_only")
        self.assertIsNone(paper["full_text"])

    def test_search_papers_empty_results(self):
        """Test when API returns zero results for an unknown topic."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"count": 0, "next_cursor": None},
            "results": [],
        }
        self.mock_session.get.return_value = mock_response

        papers = self.client.search_papers(topic="nonexistenttopicxyz12345", max_results=10)
        self.assertEqual(papers, [])

    def test_search_papers_deduplication(self):
        """Test that duplicate work records in results are ignored."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"count": 3, "next_cursor": None},
            "results": [
                {"id": "https://openalex.org/W100", "title": "Duplicate Work"},
                {"id": "https://openalex.org/W100", "title": "Duplicate Work"},
                {"id": "https://openalex.org/W101", "title": "Unique Work"},
            ],
        }
        self.mock_session.get.return_value = mock_response

        papers = self.client.search_papers(topic="test dedup", max_results=5)
        self.assertEqual(len(papers), 2)
        self.assertEqual([p["paper_id"] for p in papers], ["W100", "W101"])

    # -------------------------------------------------------------------------
    # Pagination Tests
    # -------------------------------------------------------------------------

    def test_search_papers_pagination_cursor(self):
        """Test cursor-based pagination retrieving results across multiple pages."""
        # Page 1 response
        page1_response = MagicMock(spec=requests.Response)
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "meta": {"count": 4, "next_cursor": "cursor_page_2"},
            "results": [
                {"id": "https://openalex.org/W1", "title": "Paper 1"},
                {"id": "https://openalex.org/W2", "title": "Paper 2"},
            ],
        }

        # Page 2 response
        page2_response = MagicMock(spec=requests.Response)
        page2_response.status_code = 200
        page2_response.json.return_value = {
            "meta": {"count": 4, "next_cursor": None},
            "results": [
                {"id": "https://openalex.org/W3", "title": "Paper 3"},
                {"id": "https://openalex.org/W4", "title": "Paper 4"},
            ],
        }

        self.mock_session.get.side_effect = [page1_response, page2_response]

        papers = self.client.search_papers(topic="transformers", max_results=4, per_page=2)

        self.assertEqual(len(papers), 4)
        self.assertEqual([p["paper_id"] for p in papers], ["W1", "W2", "W3", "W4"])
        self.assertEqual(self.mock_session.get.call_count, 2)

    # -------------------------------------------------------------------------
    # Error Handling Tests
    # -------------------------------------------------------------------------

    def test_search_papers_http_error_404(self):
        """Test handling of HTTP 404 client error."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(OpenAlexAPIError) as ctx:
            self.client.search_papers(topic="test error", max_results=5)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_search_papers_http_error_500(self):
        """Test handling of HTTP 500 internal server error."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(OpenAlexAPIError) as ctx:
            self.client.search_papers(topic="server fail", max_results=5)
        self.assertEqual(ctx.exception.status_code, 500)

    def test_search_papers_network_timeout(self):
        """Test handling of request timeout exception."""
        self.mock_session.get.side_effect = requests.exceptions.Timeout("Connection timed out")

        with self.assertRaises(OpenAlexTimeoutError):
            self.client.search_papers(topic="timeout test", max_results=5)

    def test_search_papers_network_connection_error(self):
        """Test handling of network transport failures."""
        self.mock_session.get.side_effect = requests.exceptions.ConnectionError("DNS failure")

        with self.assertRaises(OpenAlexNetworkError):
            self.client.search_papers(topic="network fail", max_results=5)

    def test_search_papers_invalid_json_payload(self):
        """Test handling of invalid non-JSON response."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.text = "<html>502 Bad Gateway</html>"
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(OpenAlexAPIError):
            self.client.search_papers(topic="json fail", max_results=5)

    def test_search_papers_missing_results_key(self):
        """Test handling when response JSON does not contain 'results'."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "rate limit reached"}
        self.mock_session.get.return_value = mock_response

        with self.assertRaises(OpenAlexAPIError):
            self.client.search_papers(topic="malformed response", max_results=5)

    def test_search_papers_validation_empty_topic(self):
        """Test validation error on empty or whitespace topic."""
        with self.assertRaises(ValueError):
            self.client.search_papers(topic="", max_results=5)
        with self.assertRaises(ValueError):
            self.client.search_papers(topic="   ", max_results=5)

    def test_search_papers_validation_invalid_max_results(self):
        """Test validation error on non-positive max_results."""
        with self.assertRaises(ValueError):
            self.client.search_papers(topic="test", max_results=0)
        with self.assertRaises(ValueError):
            self.client.search_papers(topic="test", max_results=-5)


if __name__ == "__main__":
    unittest.main()
