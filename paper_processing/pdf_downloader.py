"""
Safe PDF Downloader
Module 1 — Phase 2: PDF Discovery and Full-Text Extraction

Downloads legitimate, open-access research paper PDFs safely using streaming requests,
validates content types and PDF signatures (%PDF), enforces strict file-size limits,
prevents path traversal attacks, and stores files deterministically.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse
import requests

logger = logging.getLogger(__name__)

# Default storage location
DEFAULT_PAPERS_DIR = Path(__file__).resolve().parent / "data" / "papers"
DEFAULT_MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
DEFAULT_TIMEOUT = 25.0
PDF_MAGIC_BYTES = b"%PDF"


class PDFDownloadError(Exception):
    """Base exception for PDF download errors."""
    pass


class PDFDownloader:
    """
    Downloads and verifies open-access PDF documents.

    Attributes:
        storage_dir: Base directory where validated PDFs are stored.
        max_file_size_bytes: Maximum allowed file size in bytes (default 50MB).
        timeout: HTTP request timeout in seconds.
        session: Custom or shared requests.Session instance.
    """

    def __init__(
        self,
        storage_dir: Path | str | None = None,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE,
        timeout: float = DEFAULT_TIMEOUT,
        session: requests.Session | None = None,
    ) -> None:
        self.storage_dir = Path(storage_dir or DEFAULT_PAPERS_DIR).resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.max_file_size_bytes = int(max_file_size_bytes)
        self.timeout = float(timeout)
        self.session = session or requests.Session()

    def _sanitize_filename(self, paper_id: str) -> str:
        """
        Sanitizes paper_id to prevent directory traversal or unsafe filesystem characters.
        """
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", paper_id.strip())
        if not clean_id:
            clean_id = "unknown_paper"
        return f"{clean_id}.pdf"

    def _is_safe_path(self, target_path: Path) -> bool:
        """Ensures the target file path resides strictly inside storage_dir."""
        try:
            return self.storage_dir in target_path.resolve().parents or target_path.resolve().parent == self.storage_dir
        except Exception:
            return False

    def is_valid_existing_pdf(self, file_path: Path) -> bool:
        """Checks if an existing file on disk is a non-empty, valid PDF."""
        if not file_path.is_file():
            return False
        try:
            if file_path.stat().st_size < 10:
                return False
            with open(file_path, "rb") as f:
                header = f.read(5)
                return header.startswith(PDF_MAGIC_BYTES)
        except Exception:
            return False

    def download(
        self,
        paper_id: str,
        pdf_url: str | None,
        force_redownload: bool = False,
    ) -> dict[str, Any]:
        """
        Safely downloads an open-access PDF file.

        Args:
            paper_id: Unique paper identifier.
            pdf_url: Valid HTTP/HTTPS PDF URL.
            force_redownload: If True, re-downloads even if valid file exists.

        Returns:
            Structured download result dictionary:
            {
                "paper_id": str,
                "download_status": str,  # "success" | "already_exists" | "failed" | "skipped" | "invalid_pdf" | "size_exceeded"
                "file_path": str | None,
                "file_size_bytes": int,
                "pdf_url": str | None,
                "error_message": str | None
            }
        """
        result: dict[str, Any] = {
            "paper_id": paper_id,
            "download_status": "failed",
            "file_path": None,
            "file_size_bytes": 0,
            "pdf_url": pdf_url,
            "error_message": None,
        }

        if not paper_id or not isinstance(paper_id, str):
            result["error_message"] = "Invalid or empty paper_id provided."
            return result

        filename = self._sanitize_filename(paper_id)
        final_path = (self.storage_dir / filename).resolve()

        if not self._is_safe_path(final_path):
            result["error_message"] = f"Path traversal detected: {final_path}"
            return result

        # Check existing valid PDF
        if not force_redownload and self.is_valid_existing_pdf(final_path):
            file_size = final_path.stat().st_size
            logger.info("PDF for '%s' already exists at %s (%d bytes). Skipping download.", paper_id, final_path, file_size)
            result.update({
                "download_status": "already_exists",
                "file_path": str(final_path),
                "file_size_bytes": file_size,
            })
            return result

        if not pdf_url or not isinstance(pdf_url, str):
            result.update({
                "download_status": "skipped",
                "error_message": "No valid PDF URL provided for download.",
            })
            return result

        parsed_url = urlparse(pdf_url.strip())
        if parsed_url.scheme not in ("http", "https") or not parsed_url.netloc:
            result.update({
                "download_status": "failed",
                "error_message": f"Invalid URL scheme or format: {pdf_url}",
            })
            return result

        temp_path = final_path.with_suffix(".pdf.tmp")

        try:
            headers = {
                "User-Agent": "AgenticResearchAssistant/1.0 (PDFDownloader; polite)",
                "Accept": "application/pdf,application/octet-stream,*/*",
            }

            logger.info("Downloading PDF for paper '%s' from %s", paper_id, pdf_url)
            response = self.session.get(
                pdf_url.strip(),
                headers=headers,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
            )

            if response.status_code != 200:
                result.update({
                    "download_status": "failed",
                    "error_message": f"Server returned HTTP status {response.status_code}",
                })
                return result

            # Validate Content-Type header if present
            content_type = response.headers.get("Content-Type", "").lower()
            if "text/html" in content_type or "application/json" in content_type:
                result.update({
                    "download_status": "failed",
                    "error_message": f"Unexpected non-PDF content type: '{content_type}'",
                })
                return result

            # Check Content-Length header against max size
            content_length = response.headers.get("Content-Length")
            if content_length:
                try:
                    expected_size = int(content_length)
                    if expected_size > self.max_file_size_bytes:
                        result.update({
                            "download_status": "size_exceeded",
                            "error_message": f"Content-Length ({expected_size} bytes) exceeds limit ({self.max_file_size_bytes} bytes).",
                        })
                        return result
                except ValueError:
                    pass

            # Stream download to temporary file and inspect magic bytes
            downloaded_bytes = 0
            is_magic_checked = False

            with open(temp_path, "wb") as f_out:
                for chunk in response.iter_content(chunk_size=16384):
                    if not chunk:
                        continue

                    # Verify %PDF magic bytes on first chunk
                    if not is_magic_checked:
                        if not chunk.startswith(PDF_MAGIC_BYTES):
                            result.update({
                                "download_status": "invalid_pdf",
                                "error_message": f"Invalid PDF signature: Header does not start with {PDF_MAGIC_BYTES.decode()}",
                            })
                            f_out.close()
                            if temp_path.exists():
                                temp_path.unlink()
                            return result
                        is_magic_checked = True

                    downloaded_bytes += len(chunk)
                    if downloaded_bytes > self.max_file_size_bytes:
                        result.update({
                            "download_status": "size_exceeded",
                            "error_message": f"Downloaded bytes exceeded maximum allowed size of {self.max_file_size_bytes} bytes.",
                        })
                        f_out.close()
                        if temp_path.exists():
                            temp_path.unlink()
                        return result

                    f_out.write(chunk)

            if downloaded_bytes == 0 or not is_magic_checked:
                result.update({
                    "download_status": "failed",
                    "error_message": "Downloaded file was empty.",
                })
                if temp_path.exists():
                    temp_path.unlink()
                return result

            # Rename temp file to final destination atomically
            if final_path.exists():
                final_path.unlink()
            temp_path.rename(final_path)

            logger.info("Successfully downloaded paper '%s' (%d bytes) to %s", paper_id, downloaded_bytes, final_path)
            result.update({
                "download_status": "success",
                "file_path": str(final_path),
                "file_size_bytes": downloaded_bytes,
                "error_message": None,
            })
            return result

        except requests.exceptions.Timeout as exc:
            logger.error("Timeout downloading PDF for paper '%s': %s", paper_id, exc)
            result.update({
                "download_status": "failed",
                "error_message": f"Download request timed out after {self.timeout}s: {exc}",
            })
            return result
        except requests.exceptions.RequestException as exc:
            logger.error("Network error downloading PDF for paper '%s': %s", paper_id, exc)
            result.update({
                "download_status": "failed",
                "error_message": f"Network transport error: {exc}",
            })
            return result
        except Exception as exc:
            logger.error("Unexpected error downloading PDF for paper '%s': %s", paper_id, exc)
            result.update({
                "download_status": "failed",
                "error_message": f"Unexpected error: {exc}",
            })
            return result
        finally:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass


def download_pdf(
    paper_id: str,
    pdf_url: str | None,
    storage_dir: Path | str | None = None,
    max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Convenience function delegating to PDFDownloader."""
    downloader = PDFDownloader(
        storage_dir=storage_dir,
        max_file_size_bytes=max_file_size_bytes,
        timeout=timeout,
    )
    return downloader.download(paper_id=paper_id, pdf_url=pdf_url)
