"""
Academic Keyword and Keyphrase Extractor
Module 1 — Phase 3: NLP-Based Research Paper Analysis

Extracts domain-relevant keywords, technical n-grams (unigrams, bigrams, trigrams),
and integrates OpenAlex scholarly concepts.

Methodology & Scoring Documentation:
-------------------------------------
1. Single-Document TF-ISF (Term Frequency - Inverse Sentence Frequency):
   Standard corpus-level TF-IDF assumes a collection of thousands of documents where
   IDF distinguishes rare domain terms from ubiquitous words across the corpus.
   When analyzing an individual paper, treating single-document TF-IDF as corpus-level
   importance is statistically invalid because the document collection size is 1.

   To provide meaningful statistical term weighting without an external corpus, we treat
   the paper's constituent sentences {s_1, ..., s_N} as an intra-document micro-corpus.
   We compute the Term Frequency - Inverse Sentence Frequency (TF-ISF):
       TF-ISF(t) = (1 + log(tf(t))) * log(1 + N / (1 + sf(t)))
   where:
       tf(t) = total occurrences of candidate n-gram t in the paper
       sf(t) = number of distinct sentences in the paper containing candidate t
       N     = total number of sentences in the paper
   This highlights terms that appear repeatedly across focused sections rather than
   omnipresent filler words or isolated one-off typos.

2. Candidate N-Gram Generation & Filtering:
   - Evaluates unigrams, bigrams, and trigrams (1 <= n <= 3).
   - Filters out English stopwords and academic filler terms (e.g., 'paper', 'method',
     'proposed', 'approach', 'results', 'table', 'figure', 'et al').
   - Filters purely numeric tokens, symbols, and generic fragments like 'set', 'rate', 'size'.
   - Deduplicates singular and plural variants (e.g. 'layer' vs 'layers', 'network' vs 'networks').

3. OpenAlex Concept Blending:
   OpenAlex concepts carry pre-computed global scholarly relevance scores (from OpenAlex's
   global graph). When a concept matches the paper's text or title:
   - Hybrid Score = 0.5 * normalized_salience + 0.5 * concept_score
   - Concept is labeled as source='hybrid' or source='openalex_concept'.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

# Domain-specific academic noise words and generic fragments to filter
ACADEMIC_STOPWORDS: set[str] = {
    "paper",
    "papers",
    "propose",
    "proposes",
    "proposed",
    "proposing",
    "approach",
    "approaches",
    "method",
    "methods",
    "methodology",
    "model",
    "models",
    "result",
    "results",
    "show",
    "shows",
    "shown",
    "showing",
    "table",
    "figure",
    "fig",
    "using",
    "used",
    "based",
    "study",
    "et",
    "al",
    "author",
    "authors",
    "work",
    "works",
    "present",
    "presents",
    "presented",
    "demonstrate",
    "demonstrates",
    "demonstrated",
    "evaluate",
    "evaluates",
    "evaluated",
    "analysis",
    "performance",
    "comparative",
    "various",
    "different",
    "state",
    "art",
    "section",
    "experiments",
    "conclusion",
    "introduction",
    "discussion",
    # Generic dataset, measurement, and syntactic fragments
    "set",
    "sets",
    "rate",
    "rates",
    "case",
    "cases",
    "level",
    "levels",
    "size",
    "sizes",
    "type",
    "types",
    "order",
    "orders",
    "point",
    "points",
    "number",
    "numbers",
    "value",
    "values",
    "example",
    "examples",
    "form",
    "forms",
    "term",
    "terms",
    "way",
    "ways",
    "map",
    "maps",
}


class KeywordExtractor:
    """
    Extracts and ranks technical keyphrases from research papers,
    blending statistical intra-document salience with OpenAlex concepts.
    """

    def __init__(self, max_keywords: int = 15) -> None:
        self.max_keywords = max(1, int(max_keywords))

    def _is_valid_candidate(self, term: str) -> bool:
        """
        Validates whether an extracted n-gram qualifies as a technical keyword.
        """
        clean = term.strip().lower()
        if len(clean) < 3 or len(clean) > 50:
            return False

        # Reject purely numeric or symbol tokens
        if re.match(r"^[\d\W]+$", clean):
            return False

        # Split tokens
        tokens = clean.split()
        if not tokens:
            return False

        # Reject if all tokens are stopwords
        non_stop = [t for t in tokens if t not in ACADEMIC_STOPWORDS and len(t) > 2]
        if not non_stop:
            return False

        # Reject if candidate starts or ends with an academic stopword
        if tokens[0] in ACADEMIC_STOPWORDS or tokens[-1] in ACADEMIC_STOPWORDS:
            return False

        return True

    def _singularize_token(self, token: str) -> str:
        """Helper to get base form of an English token for inflection deduplication."""
        t = token.lower().strip()
        if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
            if t.endswith("ies") and len(t) > 4:
                return t[:-3] + "y"
            if t.endswith("es") and len(t) > 4 and t[-3] in ("s", "x", "z", "c", "h"):
                return t[:-2]
            return t[:-1]
        return t

    def _get_base_key(self, term: str) -> str:
        """Computes singularized base key for an n-gram (e.g. 'layers' -> 'layer')."""
        return " ".join(self._singularize_token(w) for w in term.lower().strip().split())

    def extract_keywords(
        self,
        sentences: list[dict[str, Any]] | str,
        openalex_concepts: list[Any] | None = None,
        top_k: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Extracts top technical keywords and keyphrases from text or segmented sentences.

        Args:
            sentences: Either a list of sentence dictionaries or a single string.
            openalex_concepts: Optional list of concepts from OpenAlex metadata.
            top_k: Maximum number of keywords to return (defaults to self.max_keywords).

        Returns:
            List of structured keyword dictionaries with singular/plural variants deduplicated:
            {
                "term": str,
                "salience_score": float,  # Normalized 0.0 - 1.0
                "source": str,            # "text_ngram" | "openalex_concept" | "hybrid"
                "ngram_type": str,        # "unigram" | "bigram" | "trigram" | "concept"
                "frequency": int
            }
        """
        k = top_k or self.max_keywords

        # 1. Prepare sentence text collection
        sentence_texts: list[str] = []
        if isinstance(sentences, list):
            for s in sentences:
                if isinstance(s, dict) and s.get("text"):
                    sentence_texts.append(s["text"].strip())
                elif isinstance(s, str) and s.strip():
                    sentence_texts.append(s.strip())
        elif isinstance(sentences, str) and sentences.strip():
            sentence_texts = [line.strip() for line in sentences.split("\n") if line.strip()]

        if not sentence_texts:
            return self._format_concepts_only(openalex_concepts, k)

        full_doc_text = " ".join(sentence_texts).lower()

        # 2. Extract n-grams using TfidfVectorizer across the sentence collection
        ngram_scores: dict[str, float] = {}
        ngram_frequencies: dict[str, int] = {}

        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                stop_words="english",
                max_features=250,
                sublinear_tf=True,
                token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z0-9_\-]{2,}\b",
            )
            tfidf_matrix = vectorizer.fit_transform(sentence_texts)
            feature_names = vectorizer.get_feature_names_out()

            mean_scores = tfidf_matrix.mean(axis=0).A1
            for idx, feature in enumerate(feature_names):
                term = str(feature).strip()
                if self._is_valid_candidate(term):
                    freq = len(re.findall(rf"\b{re.escape(term)}\b", full_doc_text))
                    if freq > 0:
                        ngram_scores[term] = float(mean_scores[idx])
                        ngram_frequencies[term] = freq
        except Exception as exc:
            logger.warning("TF-IDF vectorizer fallback on simple regex tokenization: %s", exc)
            words = re.findall(r"\b[a-zA-Z]{3,}\b", full_doc_text)
            for w in set(words):
                if self._is_valid_candidate(w):
                    freq = words.count(w)
                    ngram_scores[w] = freq * 0.1
                    ngram_frequencies[w] = freq

        # 3. Normalize statistical n-gram scores to [0.0, 1.0]
        max_score = max(ngram_scores.values()) if ngram_scores else 1.0
        normalized_ngrams: dict[str, float] = {
            t: round(s / max_score, 4) for t, s in ngram_scores.items()
        }

        # 4. Integrate OpenAlex Concepts
        concept_dict: dict[str, float] = {}
        if openalex_concepts and isinstance(openalex_concepts, list):
            for item in openalex_concepts:
                name: str | None = None
                score: float = 0.5
                if isinstance(item, str):
                    name = item.strip()
                elif isinstance(item, dict):
                    name = item.get("display_name") or item.get("name")
                    raw_score = item.get("score")
                    if isinstance(raw_score, (int, float)):
                        score = float(raw_score)
                if name and len(name) >= 3:
                    concept_dict[name.strip()] = score

        # 5. Blend n-grams and concepts
        candidate_items: list[dict[str, Any]] = []

        # Add concepts
        for c_name, c_score in concept_dict.items():
            c_lower = c_name.lower()
            freq = len(re.findall(rf"\b{re.escape(c_lower)}\b", full_doc_text))
            if c_lower in normalized_ngrams:
                salience = round(0.5 * normalized_ngrams[c_lower] + 0.5 * c_score, 4)
                candidate_items.append({
                    "term": c_name,
                    "salience_score": salience,
                    "source": "hybrid",
                    "ngram_type": self._determine_ngram_type(c_lower),
                    "frequency": freq or 1,
                })
            else:
                candidate_items.append({
                    "term": c_name,
                    "salience_score": round(c_score * 0.8, 4),
                    "source": "openalex_concept",
                    "ngram_type": "concept",
                    "frequency": freq,
                })

        # Add remaining statistical n-grams
        concept_lowers = {c.lower() for c in concept_dict}
        for term, salience in normalized_ngrams.items():
            if term not in concept_lowers:
                candidate_items.append({
                    "term": term,
                    "salience_score": salience,
                    "source": "text_ngram",
                    "ngram_type": self._determine_ngram_type(term),
                    "frequency": ngram_frequencies.get(term, 1),
                })

        # 6. Singular / Plural Deduplication
        # Group candidates by base singular form (e.g., 'layer' and 'layers' -> group 'layer')
        base_groups: dict[str, list[dict[str, Any]]] = {}
        for item in candidate_items:
            base_key = self._get_base_key(item["term"])
            base_groups.setdefault(base_key, []).append(item)

        deduplicated: list[dict[str, Any]] = []
        for base_key, group in base_groups.items():
            if len(group) == 1:
                deduplicated.append(group[0])
            else:
                # Merge group items:
                # Choose representation with highest frequency or plural form
                best_item = max(group, key=lambda x: (x["frequency"], len(x["term"])))
                max_salience = max(x["salience_score"] for x in group)
                total_freq = sum(x["frequency"] for x in group)
                # Keep hybrid source if any member was hybrid
                best_source = "hybrid" if any(x["source"] == "hybrid" for x in group) else best_item["source"]

                deduplicated.append({
                    "term": best_item["term"],
                    "salience_score": max_salience,
                    "source": best_source,
                    "ngram_type": best_item["ngram_type"],
                    "frequency": total_freq,
                })

        # Sort by salience_score descending, then frequency descending
        sorted_results = sorted(
            deduplicated,
            key=lambda x: (x["salience_score"], x["frequency"]),
            reverse=True,
        )

        return sorted_results[:k]

    def _determine_ngram_type(self, term: str) -> str:
        """Determines whether a candidate is unigram, bigram, or trigram."""
        words = term.strip().split()
        if len(words) == 1:
            return "unigram"
        elif len(words) == 2:
            return "bigram"
        return "trigram"

    def _format_concepts_only(
        self,
        concepts: list[Any] | None,
        top_k: int,
    ) -> list[dict[str, Any]]:
        """Fallback when text is empty but OpenAlex concepts are available."""
        if not concepts or not isinstance(concepts, list):
            return []

        results: list[dict[str, Any]] = []
        for item in concepts[:top_k]:
            name = item.get("display_name") if isinstance(item, dict) else str(item)
            if name:
                results.append({
                    "term": name.strip(),
                    "salience_score": 0.5,
                    "source": "openalex_concept",
                    "ngram_type": "concept",
                    "frequency": 0,
                })
        return results
