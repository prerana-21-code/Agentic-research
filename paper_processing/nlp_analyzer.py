"""
NLP Research Paper Analyzer Facade
Module 1 — Phase 3: NLP-Based Research Paper Analysis

Main orchestrator facade that integrates:
- AcademicTextPreprocessor (Text cleaning and sentence segmentation)
- SectionSegmenter (IMRAD structural context tagging)
- KeywordExtractor (TF-ISF intra-document keyphrases + OpenAlex concept blending)
- InformationExtractor (Evidence-grounded research dimensions extraction)

Produces a standardized, JSON-serializable dictionary capturing:
1. Research Objectives
2. Research Methodologies
3. Keywords and Important Concepts
4. Datasets
5. Evaluation Metrics
6. Research Findings
7. Research Limitations

Guarantees:
- Evidence sentences, page numbers, and detected section names are preserved.
- For abstract-only records, page_number is None and provenance is 'abstract'.
- The original abstract is preserved intact without modification.
- Zero-hallucination: dimensions with no text support are returned as empty lists [].
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from paper_processing.text_preprocessor import AcademicTextPreprocessor
from paper_processing.section_segmenter import SectionSegmenter
from paper_processing.keyword_extractor import KeywordExtractor
from paper_processing.information_extractor import InformationExtractor

logger = logging.getLogger(__name__)


class NLPResearchAnalyzer:
    """
    Analyzes standardized scholarly paper records to extract structured research dimensions.
    """

    def __init__(
        self,
        max_keywords: int = 15,
    ) -> None:
        self.preprocessor = AcademicTextPreprocessor()
        self.segmenter = SectionSegmenter()
        self.keyword_extractor = KeywordExtractor(max_keywords=max_keywords)
        self.info_extractor = InformationExtractor()

    def analyze(self, paper: dict[str, Any]) -> dict[str, Any]:
        """
        Executes full NLP analysis on a standardized paper record.

        Args:
            paper: Enriched paper record dictionary from Phase 1 or Phase 2.

        Returns:
            Structured, JSON-serializable analysis result dictionary.
        """
        if not paper or not isinstance(paper, dict):
            return self._empty_result("", "", "abstract_only")

        paper_id = str(paper.get("paper_id") or "")
        paper_title = str(paper.get("title") or "")
        source_type = str(paper.get("source_type") or "abstract_only")
        total_pages = paper.get("total_pages") or 0

        # 1. Preprocess and segment sentences with page provenance
        raw_sentences = self.preprocessor.process_paper_record(paper)

        # 2. Assign section contexts to sentences
        tagged_sentences = self.segmenter.assign_sections_to_sentences(raw_sentences)

        # 3. Extract technical keywords and blend with OpenAlex concepts
        openalex_concepts = paper.get("concepts") or []
        keywords = self.keyword_extractor.extract_keywords(
            sentences=tagged_sentences,
            openalex_concepts=openalex_concepts,
        )

        # 4. Extract research dimensions with exact evidence sentences
        extracted_dims = self.info_extractor.extract_all(tagged_sentences)

        # 5. Compile metadata summary
        total_characters = sum(len(s.get("text", "")) for s in tagged_sentences)
        scope = "full_text" if source_type == "open_access_full_text" else "abstract_only"

        # Unique page numbers represented in sentences
        distinct_pages = {
            s["page_number"] for s in tagged_sentences if s.get("page_number") is not None
        }

        # For abstract-only records, analyzed_pages must be strictly 0 (not a PDF page),
        # while analyzed_passages reflects the textual passage analyzed.
        if scope == "abstract_only":
            analyzed_pages = 0
            analyzed_passages = 1 if len(tagged_sentences) > 0 else 0
        else:
            analyzed_pages = len(distinct_pages) if distinct_pages else total_pages
            analyzed_passages = len(distinct_pages) if distinct_pages else (1 if len(tagged_sentences) > 0 else 0)

        analysis_metadata = {
            "analyzed_pages": analyzed_pages,
            "analyzed_passages": analyzed_passages,
            "total_sentences": len(tagged_sentences),
            "character_count": total_characters,
            "scope": scope,
            "provenance_summary": "pages_1_to_end" if distinct_pages else "abstract",
        }

        # 6. Compile extraction summary counts
        extraction_summary = {
            "objectives_count": len(extracted_dims["research_objectives"]),
            "methodologies_count": len(extracted_dims["research_methodologies"]),
            "keywords_count": len(keywords),
            "datasets_count": len(extracted_dims["datasets"]),
            "metrics_count": len(extracted_dims["evaluation_metrics"]),
            "findings_count": len(extracted_dims["research_findings"]),
            "limitations_count": len(extracted_dims["research_limitations"]),
        }

        return {
            "paper_id": paper_id,
            "paper_title": paper_title,
            "source_type": source_type,
            "analysis_metadata": analysis_metadata,
            "research_objectives": extracted_dims["research_objectives"],
            "research_methodologies": extracted_dims["research_methodologies"],
            "keywords_and_concepts": keywords,
            "datasets": extracted_dims["datasets"],
            "evaluation_metrics": extracted_dims["evaluation_metrics"],
            "research_findings": extracted_dims["research_findings"],
            "research_limitations": extracted_dims["research_limitations"],
            "extraction_summary": extraction_summary,
        }

    def _empty_result(self, paper_id: str, title: str, source_type: str) -> dict[str, Any]:
        """Returns safe default structure when input is empty or invalid."""
        return {
            "paper_id": paper_id,
            "paper_title": title,
            "source_type": source_type,
            "analysis_metadata": {
                "analyzed_pages": 0,
                "analyzed_passages": 0,
                "total_sentences": 0,
                "character_count": 0,
                "scope": "empty",
                "provenance_summary": "none",
            },
            "research_objectives": [],
            "research_methodologies": [],
            "keywords_and_concepts": [],
            "datasets": [],
            "evaluation_metrics": [],
            "research_findings": [],
            "research_limitations": [],
            "extraction_summary": {
                "objectives_count": 0,
                "methodologies_count": 0,
                "keywords_count": 0,
                "datasets_count": 0,
                "metrics_count": 0,
                "findings_count": 0,
                "limitations_count": 0,
            },
        }


def analyze_paper(paper: dict[str, Any], max_keywords: int = 15) -> dict[str, Any]:
    """Convenience function delegating to NLPResearchAnalyzer."""
    analyzer = NLPResearchAnalyzer(max_keywords=max_keywords)
    return analyzer.analyze(paper)
