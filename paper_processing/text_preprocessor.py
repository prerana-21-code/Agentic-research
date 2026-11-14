"""
Academic Text Preprocessor
Module 1 — Phase 3: NLP-Based Research Paper Analysis

Provides robust cleaning and academic-aware sentence segmentation for scholarly papers,
resolving PDF artifacts (ligatures, column hyphenation, running headers/footers) while
preserving sentence boundaries around academic abbreviations (e.g., 'et al.', 'i.e.', 'Fig.').
Tracks exact character offsets, page numbers, and provenance.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

# Common PDF ligature mappings to standard ASCII/Unicode equivalents
LIGATURE_MAP: dict[str, str] = {
    "\ufb00": "ff",
    "\ufb01": "fi",
    "\ufb02": "fl",
    "\ufb03": "ffi",
    "\ufb04": "ffl",
    "\ufb05": "ft",
    "\ufb06": "st",
}

# Recognized scholarly abbreviations that must NOT trigger sentence breaks
ACADEMIC_ABBREVIATIONS: tuple[str, ...] = (
    "et al",
    "i.e",
    "e.g",
    "cf",
    "vs",
    "viz",
    "ca",
    "approx",
    "fig",
    "figs",
    "tab",
    "tabs",
    "eq",
    "eqs",
    "sec",
    "secs",
    "ref",
    "refs",
    "vol",
    "vols",
    "no",
    "pp",
    "dept",
    "univ",
    "dr",
    "prof",
    "mr",
    "mrs",
    "ms",
)


class AcademicTextPreprocessor:
    """
    Cleans and segments academic text into sentences with page provenance.
    """

    def __init__(self) -> None:
        # Precompile hyphen un-breaking regex: word-\nword -> wordword
        self._hyphen_wrap_pattern = re.compile(r"(\b[a-zA-Z]+)-\s*\n\s*([a-zA-Z]+\b)")
        # Precompile header/footer patterns like arXiv submission timestamps
        self._arxiv_header_pattern = re.compile(
            r"arXiv:\d{4}\.\d{4,5}(?:v\d+)?\s+\[[a-zA-Z\-]+(?:\.[a-zA-Z\-]+)?\]\s+\d{1,2}\s+[A-Za-z]{3}\s+\d{4}",
            re.IGNORECASE,
        )
        self._page_num_footer_pattern = re.compile(r"^\s*\d{1,4}\s*$", re.MULTILINE)

    def normalize_text(self, text: str) -> str:
        """
        Normalizes raw text extracted from PDF or OpenAlex.

        Steps:
        1. Unicode normalization (NFKD) and ligature replacement.
        2. Un-breaking hyphenated words split across lines.
        3. Stripping recurring arXiv headers and standalone page number footers.
        4. Standardizing intra-sentence whitespace without collapsing line breaks completely.

        Args:
            text: Raw input string.

        Returns:
            Normalized, clean text string.
        """
        if not text or not isinstance(text, str):
            return ""

        # Step 1: Replace ligatures
        clean = text
        for lig, rep in LIGATURE_MAP.items():
            if lig in clean:
                clean = clean.replace(lig, rep)

        # Standard Unicode normalization
        clean = unicodedata.normalize("NFKC", clean)

        # Step 2: Un-break line-wrap hyphens (e.g. "connec-\ntions" -> "connections")
        clean = self._hyphen_wrap_pattern.sub(r"\1\2", clean)

        # Step 3: Remove recurring arXiv stamps
        clean = self._arxiv_header_pattern.sub("", clean)

        # Step 4: Remove isolated line numbers / page footers
        clean = self._page_num_footer_pattern.sub("", clean)

        # Step 5: Normalize carriage returns and multiple blank lines
        clean = clean.replace("\r\n", "\n").replace("\r", "\n")
        clean = re.sub(r"[ \t]+", " ", clean)
        clean = re.sub(r"\n{3,}", "\n\n", clean)

        return clean.strip()

    def split_sentences(
        self,
        text: str,
        page_number: int | None = None,
        provenance: str = "full_text",
    ) -> list[dict[str, Any]]:
        """
        Splits text into complete sentences while preserving academic abbreviations.

        Handles:
        - Standard punctuation boundaries (. ! ?) followed by whitespace and capital letter.
        - Preserves 'et al.', 'i.e.', 'e.g.', 'Fig. 1', 'Eq. (2)', and numeric decimals like '3.57%'.
        - Preserves 1-based page numbers and provenance.

        Args:
            text: Clean or raw text to segment.
            page_number: 1-based page number (None for abstract-only).
            provenance: Descriptive source tag (e.g. 'page_1', 'abstract').

        Returns:
            List of sentence dictionaries:
            {
                "sentence_id": int,
                "text": str,
                "page_number": int | None,
                "provenance": str,
                "char_offset": int
            }
        """
        if not text or not isinstance(text, str):
            return []

        clean_text = self.normalize_text(text)
        if not clean_text:
            return []

        # Replace abbreviations with placeholder dots to avoid false sentence splits
        # e.g., "et al." -> "et al<DOT>"
        placeholder = "<ACAD_DOT>"
        protected_text = clean_text

        # Protect known academic abbreviations followed by a period
        for abbr in ACADEMIC_ABBREVIATIONS:
            # Pattern matches case-insensitive abbreviation followed by a dot
            pattern = re.compile(rf"\b({re.escape(abbr)})\.", re.IGNORECASE)
            protected_text = pattern.sub(rf"\1{placeholder}", protected_text)

        # Protect decimal numbers (e.g., 3.14, 0.05)
        decimal_pattern = re.compile(r"(\d+)\.(\d+)")
        protected_text = decimal_pattern.sub(rf"\1{placeholder}\2", protected_text)

        # Split on sentence terminals (. ! ?) followed by whitespace
        # and an uppercase letter, digit, or opening quote/bracket
        split_pattern = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'\[\(])")
        raw_splits = split_pattern.split(protected_text)

        sentences: list[dict[str, Any]] = []
        sentence_id = 1
        current_offset = 0

        for segment in raw_splits:
            # Restore dot placeholders
            restored = segment.replace(placeholder, ".").strip()
            # Collapse any internal newlines into single spaces for clean sentence presentation
            restored = re.sub(r"\s+", " ", restored)

            if len(restored) < 4:
                # Skip isolated symbols or accidental punctuation crumbs
                continue

            # Calculate approximate character offset in normalized text
            offset = clean_text.find(restored, current_offset)
            if offset == -1:
                offset = current_offset

            sentences.append({
                "sentence_id": sentence_id,
                "text": restored,
                "page_number": page_number,
                "provenance": provenance,
                "char_offset": offset,
            })
            sentence_id += 1
            current_offset = offset + len(restored)

        return sentences

    def process_paper_record(self, paper: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Preprocesses and segments an entire paper record into an ordered sentence stream.

        Supports both:
        - 'open_access_full_text' records with multi-page structures (preserves page_number).
        - 'abstract_only' records with single-passage abstracts (sets page_number=None, provenance='abstract').

        Args:
            paper: Standardized enriched paper record from Phase 1 or Phase 2.

        Returns:
            Unified ordered list of sentence objects with page and provenance metadata.
        """
        if not paper or not isinstance(paper, dict):
            return []

        source_type = paper.get("source_type") or "abstract_only"
        pages = paper.get("pages")
        all_sentences: list[dict[str, Any]] = []
        global_sentence_id = 1

        # Case 1: Full-text record with page-by-page text
        if source_type == "open_access_full_text" and isinstance(pages, list) and len(pages) > 0:
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_num = page.get("page_number")
                page_text = page.get("text") or ""
                if not page_text.strip():
                    continue

                prov = f"page_{page_num}" if page_num is not None else "full_text"
                page_sentences = self.split_sentences(
                    text=page_text,
                    page_number=page_num,
                    provenance=prov,
                )
                for s in page_sentences:
                    s["sentence_id"] = global_sentence_id
                    all_sentences.append(s)
                    global_sentence_id += 1

            if all_sentences:
                return all_sentences

        # Case 2: Full-text string present without granular pages array
        full_text = paper.get("full_text")
        if source_type == "open_access_full_text" and full_text and isinstance(full_text, str) and full_text.strip():
            sentences = self.split_sentences(
                text=full_text,
                page_number=1,
                provenance="full_text",
            )
            return sentences

        # Case 3: Abstract-only fallback (or fallback when full text extraction yielded no pages)
        abstract_text = paper.get("abstract") or ""
        if isinstance(abstract_text, str) and abstract_text.strip():
            abstract_sentences = self.split_sentences(
                text=abstract_text,
                page_number=None,
                provenance="abstract",
            )
            return abstract_sentences

        return []
