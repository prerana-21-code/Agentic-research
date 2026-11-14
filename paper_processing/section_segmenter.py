"""
Academic Section Segmenter
Module 1 — Phase 3: NLP-Based Research Paper Analysis

Identifies structural section boundaries in academic papers (IMRAD format:
Abstract, Introduction, Related Work, Methodology, Experiments, Conclusion, Limitations)
and maps sentences to their semantic section context.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Canonical section category definitions and their heading aliases
SECTION_DEFINITIONS: dict[str, tuple[str, ...]] = {
    "ABSTRACT": (
        "abstract",
        "summary",
    ),
    "INTRODUCTION": (
        "introduction",
        "intro",
        "background",
        "overview",
        "motivation",
    ),
    "RELATED_WORK": (
        "related work",
        "prior work",
        "literature review",
        "previous work",
        "related works",
    ),
    "METHODOLOGY": (
        "method",
        "methods",
        "methodology",
        "approach",
        "proposed method",
        "proposed approach",
        "model",
        "architecture",
        "network architecture",
        "system architecture",
        "formulation",
        "framework",
        "system design",
        "implementation",
        "algorithm",
    ),
    "EXPERIMENTS": (
        "experiments",
        "experiment",
        "experimental results",
        "experimental setup",
        "experimental evaluation",
        "evaluation",
        "results",
        "empirical results",
        "empirical evaluation",
        "ablation study",
        "ablation experiments",
        "benchmarking",
        "performance",
        "analysis and results",
    ),
    "DISCUSSION": (
        "discussion",
        "analysis",
        "insights",
        "broader impact",
    ),
    "CONCLUSION": (
        "conclusion",
        "conclusions",
        "concluding remarks",
        "conclusions and future work",
        "summary and conclusion",
        "future work",
    ),
    "LIMITATIONS": (
        "limitations",
        "limitation",
        "limitations and future work",
        "limitations & future work",
        "threats to validity",
        "failure modes",
        "ethical considerations",
    ),
}


class SectionSegmenter:
    """
    Detects section boundaries and maps sentences to their containing academic section.
    """

    def __init__(self) -> None:
        # Precompile heading detection patterns
        # 1. Numbered headings (e.g. "1. Introduction", "3.2 Approach", "III. Experiments")
        # Roman numerals require a period to avoid collision with words like 'Conclusion' or 'Model'
        self._numbered_prefix = re.compile(
            r"^\s*(?:[0-9]{1,2}(?:\.[0-9]{1,2})*|[IVXLCDM]{1,6}\.)\s*[-:.)]?\s*"
        )

    def identify_heading(self, text: str) -> str | None:
        """
        Determines whether a line or sentence prefix represents a recognized section heading.

        Args:
            text: Text line or prefix to inspect.

        Returns:
            Canonical section name (e.g., 'INTRODUCTION', 'METHODOLOGY') if matched, else None.
        """
        if not text or not isinstance(text, str):
            return None

        clean = text.strip()
        if not clean or len(clean) > 80:
            # Section titles are concise; longer lines are body text
            return None

        # Strip leading numbers or Roman numerals (e.g. "1. Introduction" -> "Introduction")
        normalized = self._numbered_prefix.sub("", clean).strip().lower()

        # Check against canonical section definitions
        for canonical, aliases in SECTION_DEFINITIONS.items():
            for alias in aliases:
                # Exact match or colon-separated header (e.g. "Experiments: ImageNet")
                if normalized == alias or normalized.startswith(f"{alias}:") or normalized.startswith(f"{alias} -"):
                    return canonical

        return None

    def assign_sections_to_sentences(
        self,
        sentences: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Traverses a sequence of sentences and tags each with its containing section.

        Special cases:
        - Abstract-only sentences (provenance='abstract') are all assigned 'ABSTRACT'.
        - Full-text sentences start in 'INTRODUCTION' (or 'ABSTRACT' if first) and transition
          when section headings are encountered.

        Args:
            sentences: List of sentence dictionaries from AcademicTextPreprocessor.

        Returns:
            New list of sentence dictionaries with 'section' field populated.
        """
        if not sentences:
            return []

        tagged_sentences: list[dict[str, Any]] = []

        # If all sentences are from an abstract, assign ABSTRACT directly
        if all(s.get("provenance") == "abstract" for s in sentences):
            for s in sentences:
                s_copy = dict(s)
                s_copy["section"] = "ABSTRACT"
                tagged_sentences.append(s_copy)
            return tagged_sentences

        current_section = "INTRODUCTION"

        for s in sentences:
            s_copy = dict(s)
            text = s.get("text", "").strip()

            # Check if this sentence starts with or is an exact section heading
            heading = self.identify_heading(text)
            if heading:
                current_section = heading
                # If the sentence is JUST the heading, we still record it with the section
                s_copy["section"] = current_section
                tagged_sentences.append(s_copy)
                continue

            # Check if the first words of the sentence contain an embedded heading
            # e.g., "1. Introduction In this paper..." or "Experiments We evaluate..."
            words = text.split()
            if len(words) >= 2:
                for candidate_len in (1, 2, 3, 4):
                    if candidate_len <= len(words):
                        candidate_prefix = " ".join(words[:candidate_len])
                        detected = self.identify_heading(candidate_prefix)
                        if detected:
                            current_section = detected
                            break

            s_copy["section"] = current_section
            tagged_sentences.append(s_copy)

        return tagged_sentences
