"""
Unit tests for Phase 2: PDF Discovery, Downloader, Extractor, and Record Enrichment.
Tests all discovery rules, safe download limits, PyMuPDF extraction states,
and record enrichment using mocks and temporary files without live network dependencies.
"""

import tempfile
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch
import requests

from paper_processing.pdf_discovery import PDFDiscoveryService, discover_pdf
from paper_processing.pdf_downloader import PDFDownloader, download_pdf
from paper_processing.pdf_extractor import PDFExtractor, extract_text_from_pdf
from paper_processing.record_enrichment import enrich_paper_record


class TestPDFDiscovery(unittest.TestCase):
    """Tests for PDF discovery logic and open-access URL extraction."""

    def setUp(self):
        self.service = PDFDiscoveryService()
        self.base_paper = {
            "paper_id": "W12345",
            "title": "A Sample Paper",
            "landing_page_url": "https://example.com/paper/12345",
            "doi": "https://doi.org/10.1000/182",
        }

    def test_discover_from_openalex_best_oa_location(self):
        """Test discovering OA PDF URL from OpenAlex best_oa_location."""
        openalex_work = {
            "id": "https://openalex.org/W12345",
            "best_oa_location": {
                "is_oa": True,
                "pdf_url": "https://repository.edu/papers/w12345.pdf",
                "landing_page_url": "https://repository.edu/handle/12345",
                "license": "cc-by",
            },
        }
        result = self.service.discover(self.base_paper, openalex_work)
        self.assertEqual(result["status"], "found")
        self.assertTrue(result["pdf_available"])
        self.assertEqual(result["pdf_url"], "https://repository.edu/papers/w12345.pdf")
        self.assertEqual(result["access_type"], "open_access_pdf")
        self.assertEqual(result["discovery_method"], "openalex_best_oa_location")
        self.assertEqual(result["license"], "cc-by")

    def test_discover_from_arxiv_landing_page(self):
        """Test resolving arXiv landing page into canonical arXiv PDF URL."""
        paper = {
            "paper_id": "W200",
            "landing_page_url": "https://arxiv.org/abs/2103.12345",
        }
        result = self.service.discover(paper)
        self.assertEqual(result["status"], "found")
        self.assertTrue(result["pdf_available"])
        self.assertEqual(result["pdf_url"], "https://arxiv.org/pdf/2103.12345.pdf")
        self.assertEqual(result["access_type"], "open_access_pdf")
        self.assertEqual(result["discovery_method"], "arxiv_open_access")

    def test_discover_direct_pdf_landing_page(self):
        """Test discovering direct PDF link when landing_page_url ends with .pdf."""
        paper = {
            "paper_id": "W300",
            "landing_page_url": "https://univ.edu/faculty/research/paper_001.pdf",
        }
        result = self.service.discover(paper)
        self.assertEqual(result["status"], "found")
        self.assertEqual(result["pdf_url"], "https://univ.edu/faculty/research/paper_001.pdf")
        self.assertEqual(result["discovery_method"], "direct_pdf_url")

    def test_discover_no_pdf_available(self):
        """Test when paper has no open-access PDF available."""
        paper = {
            "paper_id": "W400",
            "landing_page_url": "https://publisher.com/article/abstract-only",
        }
        openalex_work = {
            "id": "https://openalex.org/W400",
            "open_access": {"is_oa": False, "oa_status": "closed"},
        }
        result = self.service.discover(paper, openalex_work)
        self.assertFalse(result["pdf_available"])
        self.assertIsNone(result["pdf_url"])
        self.assertEqual(result["access_type"], "abstract_only")
        self.assertEqual(result["status"], "restricted")

    def test_discover_invalid_pdf_url(self):
        """Test rejecting malformed or invalid URLs."""
        openalex_work = {
            "id": "https://openalex.org/W500",
            "best_oa_location": {
                "is_oa": True,
                "pdf_url": "not-a-valid-url",
            },
        }
        result = self.service.discover(self.base_paper, openalex_work)
        self.assertFalse(result["pdf_available"])
        self.assertEqual(result["status"], "invalid_url")


class TestPDFDownloader(unittest.TestCase):
    """Tests for safe streaming PDF download and validation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self.temp_dir.name)
        self.mock_session = MagicMock(spec=requests.Session)
        self.downloader = PDFDownloader(
            storage_dir=self.storage_dir,
            max_file_size_bytes=1024 * 1024,  # 1 MB limit for test
            timeout=5.0,
            session=self.mock_session,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_download_success(self):
        """Test successful download with valid %PDF magic bytes and Content-Type."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/pdf", "Content-Length": "2048"}
        mock_response.iter_content.return_value = [b"%PDF-1.4\n", b"Sample PDF body content here..."]
        self.mock_session.get.return_value = mock_response

        result = self.downloader.download(
            paper_id="paper_001",
            pdf_url="https://example.org/paper.pdf",
        )

        self.assertEqual(result["download_status"], "success")
        self.assertIsNotNone(result["file_path"])
        self.assertGreater(result["file_size_bytes"], 0)
        self.assertTrue(Path(result["file_path"]).exists())

    def test_download_invalid_content_type(self):
        """Test rejection when server returns HTML instead of PDF."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
        self.mock_session.get.return_value = mock_response

        result = self.downloader.download(
            paper_id="paper_002",
            pdf_url="https://example.org/login_paywall",
        )
        self.assertEqual(result["download_status"], "failed")
        self.assertIn("non-PDF content type", result["error_message"])

    def test_download_invalid_pdf_signature(self):
        """Test rejection when downloaded file does not start with %PDF."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.iter_content.return_value = [b"NOT_A_PDF_BINARY_DATA"]
        self.mock_session.get.return_value = mock_response

        result = self.downloader.download(
            paper_id="paper_003",
            pdf_url="https://example.org/bad_file.bin",
        )
        self.assertEqual(result["download_status"], "invalid_pdf")
        self.assertIn("Invalid PDF signature", result["error_message"])

    def test_download_file_size_limit_exceeded(self):
        """Test rejection when Content-Length exceeds max allowed bytes."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {
            "Content-Type": "application/pdf",
            "Content-Length": "500000000",  # ~500 MB (exceeds 1MB limit)
        }
        self.mock_session.get.return_value = mock_response

        result = self.downloader.download(
            paper_id="paper_004",
            pdf_url="https://example.org/giant_paper.pdf",
        )
        self.assertEqual(result["download_status"], "size_exceeded")

    def test_download_network_timeout(self):
        """Test handling network timeout during download."""
        self.mock_session.get.side_effect = requests.exceptions.Timeout("Connection timed out")

        result = self.downloader.download(
            paper_id="paper_005",
            pdf_url="https://example.org/slow.pdf",
        )
        self.assertEqual(result["download_status"], "failed")
        self.assertIn("timed out", result["error_message"])

    def test_download_already_exists(self):
        """Test avoiding duplicate download when valid PDF already exists on disk."""
        target_path = self.storage_dir / "paper_existing.pdf"
        target_path.write_bytes(b"%PDF-1.4\nExisting valid PDF file data")

        result = self.downloader.download(
            paper_id="paper_existing",
            pdf_url="https://example.org/paper_existing.pdf",
        )
        self.assertEqual(result["download_status"], "already_exists")
        self.assertEqual(result["file_path"], str(target_path))
        self.mock_session.get.assert_not_called()

    def test_download_path_traversal_sanitization(self):
        """Test sanitizing dangerous characters in paper_id to prevent directory traversal."""
        mock_response = MagicMock(spec=requests.Response)
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/pdf"}
        mock_response.iter_content.return_value = [b"%PDF-1.4\nValid file"]
        self.mock_session.get.return_value = mock_response

        result = self.downloader.download(
            paper_id="../../etc/passwd",
            pdf_url="https://example.org/evil.pdf",
        )
        self.assertEqual(result["download_status"], "success")
        saved_path = Path(result["file_path"])
        self.assertEqual(saved_path.parent, self.storage_dir)
        self.assertNotIn("..", saved_path.name)


class TestPDFExtractor(unittest.TestCase):
    """Tests for PDF text extraction and error handling."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_pdf_path = Path(self.temp_dir.name) / "test.pdf"
        self.test_pdf_path.write_bytes(b"%PDF-1.4\nDummy PDF content")
        self.extractor = PDFExtractor()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_nonexistent_file(self):
        """Test error handling when file does not exist."""
        result = self.extractor.extract("paper_missing", "nonexistent/path/paper.pdf")
        self.assertEqual(result["extraction_status"], "invalid_pdf")

    @patch("paper_processing.pdf_extractor.pymupdf")
    def test_extract_multi_page_success(self, mock_pymupdf):
        """Test multi-page text extraction preserving page numbers."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.is_encrypted = False

        # Page 1
        page1 = MagicMock()
        page1.get_text.return_value = "Introduction to neural networks."

        # Page 2
        page2 = MagicMock()
        page2.get_text.return_value = "Methodology and benchmark results."

        mock_doc.load_page.side_effect = [page1, page2]
        mock_pymupdf.open.return_value = mock_doc

        result = self.extractor.extract("paper_001", self.test_pdf_path)

        self.assertEqual(result["extraction_status"], "success")
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(result["pages_with_text"], 2)
        self.assertEqual(len(result["pages"]), 2)
        self.assertEqual(result["pages"][0]["page_number"], 1)
        self.assertEqual(result["pages"][0]["text"], "Introduction to neural networks.")
        self.assertEqual(result["pages"][1]["page_number"], 2)
        self.assertEqual(result["pages"][1]["text"], "Methodology and benchmark results.")
        self.assertIn("Introduction to neural networks.", result["full_text"])
        self.assertIn("Methodology and benchmark results.", result["full_text"])
        mock_doc.close.assert_called_once()

    @patch("paper_processing.pdf_extractor.pymupdf")
    def test_extract_empty_or_image_only_pages(self, mock_pymupdf):
        """Test handling of scanned or image-only PDF with zero extractable text."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.is_encrypted = False

        page1 = MagicMock()
        page1.get_text.return_value = ""  # Image only
        page2 = MagicMock()
        page2.get_text.return_value = "   "  # Whitespace only

        mock_doc.load_page.side_effect = [page1, page2]
        mock_pymupdf.open.return_value = mock_doc

        result = self.extractor.extract("paper_scanned", self.test_pdf_path)

        self.assertEqual(result["extraction_status"], "no_text")
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(result["pages_with_text"], 0)
        self.assertEqual(result["full_text"], "")

    @patch("paper_processing.pdf_extractor.pymupdf")
    def test_extract_partial_pages(self, mock_pymupdf):
        """Test extraction when some pages have text and others are blank/images."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 2
        mock_doc.is_encrypted = False

        page1 = MagicMock()
        page1.get_text.return_value = "Title and abstract text."
        page2 = MagicMock()
        page2.get_text.return_value = ""  # Figure page

        mock_doc.load_page.side_effect = [page1, page2]
        mock_pymupdf.open.return_value = mock_doc

        result = self.extractor.extract("paper_partial", self.test_pdf_path)

        self.assertEqual(result["extraction_status"], "partial")
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(result["pages_with_text"], 1)
        self.assertEqual(result["full_text"], "Title and abstract text.")

    @patch("paper_processing.pdf_extractor.pymupdf")
    def test_extract_encrypted_pdf(self, mock_pymupdf):
        """Test handling of password-protected encrypted PDF."""
        mock_doc = MagicMock()
        mock_doc.__len__.return_value = 5
        mock_doc.is_encrypted = True
        mock_pymupdf.open.return_value = mock_doc

        result = self.extractor.extract("paper_locked", self.test_pdf_path)

        self.assertEqual(result["extraction_status"], "encrypted")
        self.assertEqual(result["total_pages"], 5)
        self.assertEqual(result["full_text"], "")
        mock_doc.close.assert_called_once()

    @patch("paper_processing.pdf_extractor.pymupdf")
    def test_extract_corrupted_pdf(self, mock_pymupdf):
        """Test handling when fitz/pymupdf fails to open corrupted file."""
        mock_pymupdf.open.side_effect = Exception("FormatError: Corrupted xref table")

        result = self.extractor.extract("paper_corrupt", self.test_pdf_path)
        self.assertEqual(result["extraction_status"], "invalid_pdf")


class TestRecordEnrichment(unittest.TestCase):
    """Tests for record enrichment and schema contract preservation."""

    def setUp(self):
        self.base_paper = {
            "paper_id": "W12345",
            "openalex_id": "https://openalex.org/W12345",
            "title": "Machine Learning in Medicine",
            "authors": ["Alice Smith", "Bob Jones"],
            "year": 2023,
            "doi": "https://doi.org/10.1000/123",
            "abstract": "Original abstract about clinical AI models.",
            "publication_type": "journal-article",
            "concepts": ["Machine learning", "Medicine"],
            "landing_page_url": "https://example.org/paper",
            "source_type": "abstract_only",
            "full_text": None,
        }

    def test_enrichment_full_text_success(self):
        """Test successful full-text promotion preserving original abstract."""
        discovery = {
            "pdf_url": "https://example.org/paper.pdf",
            "access_type": "open_access_pdf",
        }
        download = {
            "file_path": "/local/data/papers/W12345.pdf",
            "pdf_url": "https://example.org/paper.pdf",
        }
        extraction = {
            "extraction_status": "success",
            "total_pages": 4,
            "pages_with_text": 4,
            "pages": [{"page_number": 1, "text": "Page 1 content"}],
            "full_text": "Complete multi-page extracted full text...",
        }

        enriched = enrich_paper_record(self.base_paper, discovery, download, extraction)

        self.assertEqual(enriched["source_type"], "open_access_full_text")
        self.assertEqual(enriched["full_text"], "Complete multi-page extracted full text...")
        self.assertEqual(enriched["pdf_url"], "https://example.org/paper.pdf")
        self.assertEqual(enriched["pdf_path"], "/local/data/papers/W12345.pdf")
        self.assertEqual(enriched["access_type"], "open_access_pdf")
        self.assertEqual(enriched["extraction_status"], "success")
        self.assertEqual(enriched["total_pages"], 4)
        # Verify invariant fields
        self.assertEqual(enriched["paper_id"], "W12345")
        self.assertEqual(enriched["abstract"], "Original abstract about clinical AI models.")

    def test_enrichment_abstract_only_fallback(self):
        """Test remaining abstract_only when no PDF is found or extraction has no text."""
        discovery = {
            "pdf_url": None,
            "access_type": "abstract_only",
        }
        extraction = {
            "extraction_status": "no_text",
            "total_pages": 2,
            "pages_with_text": 0,
            "pages": [],
            "full_text": "",
        }

        enriched = enrich_paper_record(self.base_paper, discovery, None, extraction)

        self.assertEqual(enriched["source_type"], "abstract_only")
        self.assertIsNone(enriched["full_text"])
        self.assertEqual(enriched["abstract"], "Original abstract about clinical AI models.")
        self.assertEqual(enriched["extraction_status"], "no_text")


if __name__ == "__main__":
    unittest.main()
