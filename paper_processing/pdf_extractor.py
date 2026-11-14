"""
PDF Text Extractor
Module 1 — Phase 2: PDF Discovery and Full-Text Extraction

Extracts clean, page-level text from PDF documents using PyMuPDF (pymupdf),
preserving page numbers, identifying unextractable or image-only pages,
and handling encrypted or corrupted PDF files safely.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None

# Backward compatibility alias
fitz = pymupdf


class PDFExtractionError(Exception):
    """Base exception for PDF text extraction failures."""
    pass


class PDFExtractor:
    """
    Extracts structured page-level text from PDF files using PyMuPDF.
    """

    def __init__(self) -> None:
        pass

    def extract(self, paper_id: str, file_path: Path | str) -> dict[str, Any]:
        """
        Extracts text from a local PDF file page by page.

        Args:
            paper_id: Unique paper identifier.
            file_path: Absolute or relative path to the PDF file.

        Returns:
            Structured extraction result dictionary:
            {
                "paper_id": str,
                "extraction_status": str,  # "success" | "partial" | "no_text" | "encrypted" | "invalid_pdf" | "error"
                "total_pages": int,
                "pages_with_text": int,
                "pages": [
                    {
                        "page_number": int,
                        "text": str
                    }
                ],
                "full_text": str,
                "character_count": int,
                "extraction_method": "pymupdf"
            }
        """
        result: dict[str, Any] = {
            "paper_id": paper_id,
            "extraction_status": "error",
            "total_pages": 0,
            "pages_with_text": 0,
            "pages": [],
            "full_text": "",
            "character_count": 0,
            "extraction_method": "pymupdf",
        }

        path_obj = Path(file_path).resolve()
        if not path_obj.is_file():
            logger.error("PDF file not found at path: %s", path_obj)
            result["extraction_status"] = "invalid_pdf"
            return result

        if pymupdf is None:
            logger.error("PyMuPDF (pymupdf) is not installed in the Python environment.")
            result["extraction_status"] = "error"
            return result

        doc = None
        try:
            try:
                doc = pymupdf.open(str(path_obj))
            except Exception as exc:
                logger.error("Could not open PDF file '%s': %s", path_obj, exc)
                result["extraction_status"] = "invalid_pdf"
                return result

            # Check for encryption
            if getattr(doc, "is_encrypted", False):
                logger.warning("PDF document is password-encrypted: %s", path_obj)
                result["extraction_status"] = "encrypted"
                result["total_pages"] = len(doc)
                return result

            total_pages = len(doc)
            result["total_pages"] = total_pages

            if total_pages == 0:
                result["extraction_status"] = "no_text"
                return result

            pages_list: list[dict[str, Any]] = []
            pages_with_text = 0
            full_text_parts: list[str] = []

            for page_idx in range(total_pages):
                page = doc.load_page(page_idx)
                raw_text = page.get_text("text") or ""
                clean_text = raw_text.strip()

                page_number = page_idx + 1
                if clean_text:
                    pages_with_text += 1
                    full_text_parts.append(clean_text)

                pages_list.append({
                    "page_number": page_number,
                    "text": clean_text,
                })

            assembled_full_text = "\n\n".join(full_text_parts).strip()
            total_chars = len(assembled_full_text)

            # Determine extraction status
            if pages_with_text == 0:
                extraction_status = "no_text"
            elif pages_with_text < total_pages:
                extraction_status = "partial"
            else:
                extraction_status = "success"

            result.update({
                "extraction_status": extraction_status,
                "pages_with_text": pages_with_text,
                "pages": pages_list,
                "full_text": assembled_full_text,
                "character_count": total_chars,
            })
            return result

        except Exception as exc:
            logger.error("Unexpected error during PDF text extraction for '%s': %s", paper_id, exc)
            result["extraction_status"] = "error"
            return result

        finally:
            if doc is not None:
                try:
                    doc.close()
                except Exception:
                    pass


def extract_text_from_pdf(paper_id: str, file_path: Path | str) -> dict[str, Any]:
    """Convenience function delegating to PDFExtractor."""
    extractor = PDFExtractor()
    return extractor.extract(paper_id=paper_id, file_path=file_path)
