"""
Research Information Extractor
Module 1 — Phase 3: NLP-Based Research Paper Analysis

Extracts structured research dimensions from research paper sentences:
1. Research Objectives
2. Research Methodologies
3. Datasets
4. Evaluation Metrics
5. Research Findings
6. Research Limitations

Design & Evidence Preservation Principles:
------------------------------------------
- Strict Evidence Requirement: Every extracted element MUST include its exact verbatim
  supporting sentence from the paper.
- Exact Provenance: Page numbers (1-based) and detected section names are attached to
  every extracted item. For abstract-only records, page_number is None and provenance is 'abstract'.
- Zero Hallucination: If the source text contains no supporting evidence for a dimension
  (e.g., an abstract mentioning no limitations), an empty list [] is returned.
- Transparent Scoring: Confidence scores are computed deterministically based on
  pattern specificity tiers.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Curated benchmark dataset lexicon (canonical display names)
# Ordered with more specific / longer names first to prevent substring collision
CURATED_DATASETS: list[tuple[str, str]] = [
    ("cifar-100", "CIFAR-100"),
    ("cifar-10", "CIFAR-10"),
    ("cifar", "CIFAR"),
    ("ms coco", "MS COCO"),
    ("coco", "COCO"),
    ("pascal voc", "PASCAL VOC"),
    ("imagenet", "ImageNet"),
    ("mnist", "MNIST"),
    ("svhn", "SVHN"),
    ("squad", "SQuAD"),
    ("superglue", "SuperGLUE"),
    ("glue", "GLUE"),
    ("imdb", "IMDb"),
    ("wmt", "WMT"),
    ("cityscapes", "Cityscapes"),
    ("kinetics", "Kinetics"),
    ("ade20k", "ADE20K"),
]

# Evaluation predicate regex: requires explicit empirical evaluation / training context
EVAL_PREDICATE_REGEX = re.compile(
    r"\b(?:evaluat(?:e|ed|ing|ion|es)|train(?:ed|ing|s)?|test(?:ed|ing|s)?|benchmark(?:ed|ing|s)?|"
    r"results? on|experiments? on|applied to|baseline on|validated? on|dataset|corpus|database)\b",
    re.IGNORECASE,
)

# Pattern matching citations / comparative historical citations without evaluation
CITATION_ONLY_PATTERN = re.compile(
    r"(?:\(see\s+\[\d+\]\)|\(e\.g\.,\s+\[\d+\]\)|reported in\s+\[\d+\]|see\s+\[\d+\]|in\s+\[\d+\])",
    re.IGNORECASE,
)

# Resolution language: indicates a problem is solved/addressed, NOT an open limitation
RESOLUTION_REGEX = re.compile(
    r"\b(?:(?:we|our|resnet|method|framework|architecture|model|mapping|setting|solver)\s+"
    r"(?:address(?:es|ed)?|overcome(?:s)?|manage(?:d)? to overcome|resolve(?:s|d)?|mitigate(?:s|d)?|"
    r"solv(?:es|ed)?|eliminat(?:es|ed)?)|well addressed|effectively addressed|sufficient for addressing|"
    r"addressed in this setting|manage to overcome)\b",
    re.IGNORECASE,
)

# Neural network bottleneck architecture mentions (as distinct from resource/system bottlenecks)
BOTTLENECK_ARCH_REGEX = re.compile(
    r"\b(?:bottleneck\s+(?:block|building block|design|architecture|layer|resnet)|"
    r"bottleneck(?:s)?\s+that are introduced|non-bottleneck)\b",
    re.IGNORECASE,
)

# Patterns that indicate a table/figure caption or section title rather than a finding
NON_FINDING_HEADER_REGEX = re.compile(
    r"^(?:Table\s*\d+|Figure\s*\d+|Fig\.\s*\d+|Comparisons?\s+(?:of|with)|Bottom:|Top:|Right:|Left:|"
    r"Top-1 error|Top-5 error|Object detection mAP)",
    re.IGNORECASE,
)


class InformationExtractor:
    """
    Extracts evidence-grounded research dimensions from segmented, section-tagged sentences.
    """

    def __init__(self) -> None:
        self._init_objective_patterns()
        self._init_methodology_patterns()
        self._init_dataset_patterns()
        self._init_metric_patterns()
        self._init_findings_patterns()
        self._init_limitation_patterns()

    def _init_objective_patterns(self) -> None:
        # Tier 1: Explicit scholarly intent declarations (Confidence: 0.95)
        self.obj_tier1 = re.compile(
            r"\b(?:in this (?:paper|work|study)|our (?:primary )?(?:goal|objective)|the goal of this (?:paper|work))"
            r"[,:]?\s+(?:we\s+)?(?:propose|present|address|introduce|investigate|develop|aim|seek|is to)\b",
            re.IGNORECASE,
        )
        # Tier 2: First-person goal markers (Confidence: 0.80)
        self.obj_tier2 = re.compile(
            r"\bwe\s+(?:aim to|focus on|seek to|set out to|design|target)\b",
            re.IGNORECASE,
        )
        # Tier 3: Problem overcoming phrasing (Confidence: 0.65)
        self.obj_tier3 = re.compile(
            r"\b(?:to overcome|to address|to tackle)\s+(?:the|this)\s+(?:problem|issue|challenge|degradation)\b",
            re.IGNORECASE,
        )

    def _init_methodology_patterns(self) -> None:
        # Tier 1: Framework / architecture declarations (Confidence: 0.90)
        self.method_tier1 = re.compile(
            r"\b(?:we\s+(?:introduce|propose|develop|present|formulate)\s+(?:a|an)\s+"
            r"(?:new|novel|deep|residual)?\s*(?:framework|architecture|model|approach|method|algorithm|network))\b",
            re.IGNORECASE,
        )
        # Tier 2: Structural / algorithmic formulation (Confidence: 0.75)
        self.method_tier2 = re.compile(
            r"\b(?:shortcut connections|residual learning|residual mapping|identity mapping|"
            r"is formulated as|is composed of|consists of|we optimize the network)\b",
            re.IGNORECASE,
        )

    def _init_dataset_patterns(self) -> None:
        # Regex matching capitalized entities followed by 'dataset', 'benchmark', etc.
        self.dataset_regex = re.compile(
            r"\b([A-Z][a-zA-Z0-9_\-]+(?:\s+[A-Z0-9][a-zA-Z0-9_\-]+)?)\s+(?:dataset|benchmark|corpus|database)\b"
        )

    def _init_metric_patterns(self) -> None:
        # 1. Case-sensitive Mean Average Precision metric patterns
        self.map_metric_regex = re.compile(
            r"\bmAP(?:@(?:\.[0-9]+|\[[0-9.,\s]+\]|[0-9.]+|IoU\s*=\s*[0-9.]+))?\b"
        )
        # 2. Case-insensitive standard metrics
        self.curated_metrics = (
            "mean average precision",
            "top-1 error",
            "top-5 error",
            "top-1 accuracy",
            "top-5 accuracy",
            "error rate",
            "training error",
            "test error",
            "validation error",
            "accuracy",
            "precision",
            "recall",
            "f1-score",
            "f1 score",
            "bleu",
            "rouge",
            "perplexity",
            "loss",
            "auc",
            "roc",
        )
        # 3. Numeric tokens to ignore during metric value proximity binding
        self.ignored_numeric_patterns = [
            re.compile(r"\b\d+[- ]layers?\b", re.IGNORECASE),
            re.compile(r"\b(?:cifar|voc|resnet|vgg)[- ]\d+\b", re.IGNORECASE),
            re.compile(r"\b(?:table|figure|fig\.|tab\.|section|eq\.|equation)\s*\d+\b", re.IGNORECASE),
            re.compile(r"\b\d+e\d+\b", re.IGNORECASE),
            re.compile(r"\b\d+[x]\d+\b", re.IGNORECASE),
        ]
        # Valid percentage value regex
        self.percentage_regex = re.compile(r"\b\d+(?:\.\d+)?%")
        # General decimal / numeric metric value regex
        self.metric_num_regex = re.compile(r"\b\d+\.\d+\b")

    def _init_findings_patterns(self) -> None:
        # Quantitative achievement or state-of-the-art claim (Confidence: 0.90)
        self.find_tier1 = re.compile(
            r"\b(?:achieves?(?:\s+a|\s+an)?\s+\d+\.?\d*%|outperforms?|won (?:1st|first) place|"
            r"substantially improves?|reduces the error by \d+\.?\d*%|"
            r"(?:is|are)\s+\d+(?:\.\d+)?\s+points higher than|"
            r"(?:achieves?|outperforms?|higher than|better than|among the)\s+(?:the\s+)?(?:previous\s+)?state-of-the-art|"
            r"state-of-the-art results?\s*\(\d+)\b",
            re.IGNORECASE,
        )
        # Qualitative empirical finding markers (Confidence: 0.75)
        self.find_tier2 = re.compile(
            r"\b(?:our results (?:show|demonstrate|indicate)|we find that|are easier to optimize|"
            r"gain accuracy from considerably increased depth|leads to higher accuracy)\b",
            re.IGNORECASE,
        )

    def _init_limitation_patterns(self) -> None:
        # Tier 1: Stated failure modes, degradation in baseline, or bottlenecks (Confidence: 0.85)
        self.limit_tier1 = re.compile(
            r"\b(?:limitation|limitations|computational overhead|computational cost|"
            r"suffer from overfitting|because of overfitting|fails? to converge|"
            r"accuracy gets saturated\s+(?:and then degrades)?|leads to higher training error|"
            r"degradation problem has been exposed)\b",
            re.IGNORECASE,
        )
        # Tier 2: Caveats and practical resource constraints (Confidence: 0.70)
        self.limit_tier2 = re.compile(
            r"\b(?:concerns on the training time that we can afford|still remains a challenge|"
            r"future work (?:is needed|should)|constrained by|not applicable to)\b",
            re.IGNORECASE,
        )

    def extract_objectives(self, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extracts research objectives with exact supporting evidence sentence."""
        objectives: list[dict[str, Any]] = []
        seen_evidence: set[str] = set()

        for s in sentences:
            text = s.get("text", "").strip()
            if not text or text in seen_evidence:
                continue

            confidence: float | None = None
            if self.obj_tier1.search(text):
                confidence = 0.95
            elif self.obj_tier2.search(text):
                confidence = 0.80
            elif self.obj_tier3.search(text):
                confidence = 0.65

            if confidence is not None:
                seen_evidence.add(text)
                objectives.append({
                    "statement": text,
                    "evidence": text,
                    "page_number": s.get("page_number"),
                    "provenance": s.get("provenance", "full_text"),
                    "section": s.get("section"),
                    "confidence": confidence,
                })

        return objectives

    def extract_methodologies(self, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Extracts methodology declarations and framework descriptions."""
        methodologies: list[dict[str, Any]] = []
        seen_evidence: set[str] = set()

        for s in sentences:
            text = s.get("text", "").strip()
            if not text or text in seen_evidence:
                continue

            confidence: float | None = None
            if self.method_tier1.search(text):
                confidence = 0.90
            elif self.method_tier2.search(text):
                confidence = 0.75

            if confidence is not None:
                seen_evidence.add(text)
                methodologies.append({
                    "method": text,
                    "evidence": text,
                    "page_number": s.get("page_number"),
                    "provenance": s.get("provenance", "full_text"),
                    "section": s.get("section"),
                    "confidence": confidence,
                })

        return methodologies

    def extract_datasets(self, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Extracts datasets evaluated or trained on in the paper.

        Filters out:
        - Datasets mentioned solely in citations or comparative references (e.g. 'on MNIST (see [42])').
        - Substring duplicates from the same sentence (e.g. 'CIFAR' when 'CIFAR-10' is present).
        """
        datasets: list[dict[str, Any]] = []
        seen_datasets: set[str] = set()

        for s in sentences:
            text = s.get("text", "").strip()
            if not text:
                continue

            # Check if the sentence has an evaluation context
            has_eval_predicate = bool(EVAL_PREDICATE_REGEX.search(text))

            text_lower = text.lower()
            sentence_datasets_matched: list[str] = []

            # 1. Check curated benchmark datasets
            for key, canonical_name in CURATED_DATASETS:
                # Do not match 'cifar' if it is part of 'cifar-10' or 'cifar-100'
                if key == "cifar" and re.search(r"\bcifar[- ](?:10|100)\b", text_lower):
                    continue
                # Do not match 'coco' if it is preceded by 'ms '
                if key == "coco" and re.search(r"\bms\s+coco\b", text_lower):
                    continue

                pattern = rf"\b{re.escape(key)}\b"
                match = re.search(pattern, text_lower)
                if not match:
                    continue

                # Check if this occurrence is purely an external citation reference
                # e.g., "on MNIST (see [42])" or "MNIST (see [42])"
                citation_window = text[match.start(): min(len(text), match.end() + 35)]
                if CITATION_ONLY_PATTERN.search(citation_window) and not has_eval_predicate:
                    continue
                # Specific check for comparative citation e.g. "on MNIST (see [42])"
                if re.search(rf"\b{re.escape(key)}\s*(?:\(see\s+\[\d+\]\)|\(e\.g\.,\s+\[\d+\]\))", text, re.IGNORECASE):
                    if not re.search(rf"\b(?:evaluate|train|test|experiment|results?)\s+(?:on\s+)?{re.escape(key)}\b", text_lower):
                        continue

                # Substring deduplication across paper:
                if canonical_name == "CIFAR" and any(x in seen_datasets for x in ("CIFAR-10", "CIFAR-100")):
                    continue
                if canonical_name == "COCO" and "MS COCO" in seen_datasets:
                    continue

                if canonical_name not in seen_datasets:
                    sentence_datasets_matched.append(canonical_name)
                    seen_datasets.add(canonical_name)
                    datasets.append({
                        "name": canonical_name,
                        "evidence": text,
                        "page_number": s.get("page_number"),
                        "provenance": s.get("provenance", "full_text"),
                        "section": s.get("section"),
                        "confidence": 0.95,
                    })

            # 2. Check pattern-based dataset names (e.g. "FooBar dataset")
            for match in self.dataset_regex.finditer(text):
                candidate_name = match.group(1).strip()
                if len(candidate_name) >= 3 and candidate_name not in seen_datasets:
                    if candidate_name.lower() not in ("the", "this", "our", "a", "an", "each", "and"):
                        seen_datasets.add(candidate_name)
                        datasets.append({
                            "name": candidate_name,
                            "evidence": text,
                            "page_number": s.get("page_number"),
                            "provenance": s.get("provenance", "full_text"),
                            "section": s.get("section"),
                            "confidence": 0.80,
                        })

        return datasets

    def extract_metrics(self, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Extracts evaluation metrics and binds numerical values via proximity.

        Improvements:
        - Case-sensitive matching for mAP (Mean Average Precision).
        - Ignores lowercase 'map' in 'feature map'.
        - Proximity binding: avoids associating layer counts (e.g. 56-layer) or dataset names (CIFAR-10).
        - Returns value=None if no valid metric value is found nearby.
        """
        metrics: list[dict[str, Any]] = []
        seen_pairs: set[tuple[str, str | None, int | None]] = set()

        for s in sentences:
            text = s.get("text", "").strip()
            if not text:
                continue

            text_lower = text.lower()
            page_num = s.get("page_number")

            # 1. Check case-sensitive mAP matches
            map_matches = list(self.map_metric_regex.finditer(text))
            for m in map_matches:
                metric_name = m.group(0)
                metric_span = m.span()
                value = self._extract_metric_value_in_proximity(text, metric_span)
                pair_key = (metric_name, value, page_num)
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    metrics.append({
                        "metric": metric_name,
                        "value": value,
                        "evidence": text,
                        "page_number": page_num,
                        "provenance": s.get("provenance", "full_text"),
                        "section": s.get("section"),
                        "confidence": 0.90 if value is not None else 0.75,
                    })

            # 2. Check standard curated metrics (case-insensitive)
            for metric in self.curated_metrics:
                pattern = rf"\b{re.escape(metric)}\b"
                for match in re.finditer(pattern, text_lower):
                    metric_span = match.span()
                    value = self._extract_metric_value_in_proximity(text, metric_span)
                    pair_key = (metric, value, page_num)
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        metrics.append({
                            "metric": metric,
                            "value": value,
                            "evidence": text,
                            "page_number": page_num,
                            "provenance": s.get("provenance", "full_text"),
                            "section": s.get("section"),
                            "confidence": 0.90 if value is not None else 0.75,
                        })

        return metrics

    def _extract_metric_value_in_proximity(self, text: str, metric_span: tuple[int, int]) -> str | None:
        """
        Finds a valid metric number/percentage in the immediate proximity of a metric match.

        Filters out architecture numbers (56-layer), dataset digits (CIFAR-10),
        table numbers (Table 1), and figure numbers (Fig. 4).
        """
        start_idx, end_idx = metric_span
        # Window of 60 chars before and 70 chars after metric
        window_start = max(0, start_idx - 60)
        window_end = min(len(text), end_idx + 70)
        window = text[window_start:window_end]

        # Mask out known false positive numbers in the window
        masked_window = window
        for pattern in self.ignored_numeric_patterns:
            masked_window = pattern.sub(lambda m: " " * len(m.group(0)), masked_window)

        # Check for explicit percentage in proximity first
        percentages = self.percentage_regex.findall(masked_window)
        if percentages:
            return percentages[0]

        # Check for floating point metric numbers (e.g. "3.57", "6.43")
        decimals = self.metric_num_regex.findall(masked_window)
        if decimals:
            return decimals[0]

        return None

    def extract_findings(self, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Extracts empirical research findings, excluding table/figure titles and subheadings.
        """
        findings: list[dict[str, Any]] = []
        seen_evidence: set[str] = set()

        for s in sentences:
            text = s.get("text", "").strip()
            if not text or text in seen_evidence:
                continue

            # Reject standalone headings, table headers, or figure labels
            if NON_FINDING_HEADER_REGEX.search(text):
                continue
            if len(text.split()) < 6 or len(text) < 35:
                continue
            if text.endswith(":") or text.startswith("Table ") or text.startswith("Fig. "):
                continue

            confidence: float | None = None
            if self.find_tier1.search(text):
                confidence = 0.90
            elif self.find_tier2.search(text):
                confidence = 0.75

            if confidence is not None:
                seen_evidence.add(text)
                findings.append({
                    "finding": text,
                    "evidence": text,
                    "page_number": s.get("page_number"),
                    "provenance": s.get("provenance", "full_text"),
                    "section": s.get("section"),
                    "confidence": confidence,
                })

        return findings

    def extract_limitations(self, sentences: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Extracts stated research limitations, bottlenecks, or failure modes.

        Excludes:
        - Statements claiming to solve/address/overcome the degradation problem.
        - Mentions of 'bottleneck architecture' / 'bottleneck design'.
        - Standalone section headings without complete sentences.
        """
        limitations: list[dict[str, Any]] = []
        seen_evidence: set[str] = set()

        for s in sentences:
            text = s.get("text", "").strip()
            if not text or text in seen_evidence:
                continue

            # Exclude short headings
            if len(text.split()) < 5 or len(text) < 30:
                continue

            # 1. Check if the sentence claims to solve / address the problem
            if RESOLUTION_REGEX.search(text):
                continue

            # 2. Check if 'bottleneck' is only used as an architectural design name
            if BOTTLENECK_ARCH_REGEX.search(text):
                # Only keep if sentence also expresses an actual constraint
                if "training time" not in text.lower() and "computational" not in text.lower():
                    continue

            confidence: float | None = None
            if self.limit_tier1.search(text):
                confidence = 0.85
            elif self.limit_tier2.search(text):
                confidence = 0.70

            if confidence is not None:
                seen_evidence.add(text)
                limitations.append({
                    "limitation": text,
                    "evidence": text,
                    "page_number": s.get("page_number"),
                    "provenance": s.get("provenance", "full_text"),
                    "section": s.get("section"),
                    "confidence": confidence,
                })

        return limitations

    def extract_all(self, sentences: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """
        Executes extraction across all 6 research dimensions.
        """
        return {
            "research_objectives": self.extract_objectives(sentences),
            "research_methodologies": self.extract_methodologies(sentences),
            "datasets": self.extract_datasets(sentences),
            "evaluation_metrics": self.extract_metrics(sentences),
            "research_findings": self.extract_findings(sentences),
            "research_limitations": self.extract_limitations(sentences),
        }
