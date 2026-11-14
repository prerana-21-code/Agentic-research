"""
Unit Tests for Phase 3: NLP-Based Research Paper Analysis
Covers:
- AcademicTextPreprocessor
- SectionSegmenter
- KeywordExtractor
- InformationExtractor
- NLPResearchAnalyzer & analyze_paper
"""

from __future__ import annotations

import json
import unittest
from typing import Any

from paper_processing.text_preprocessor import AcademicTextPreprocessor
from paper_processing.section_segmenter import SectionSegmenter
from paper_processing.keyword_extractor import KeywordExtractor
from paper_processing.information_extractor import InformationExtractor
from paper_processing.nlp_analyzer import NLPResearchAnalyzer, analyze_paper


class TestAcademicTextPreprocessor(unittest.TestCase):
    """Tests for academic text normalization and sentence segmentation."""

    def setUp(self) -> None:
        self.preprocessor = AcademicTextPreprocessor()

    def test_ligature_normalization(self) -> None:
        """Test replacement of PDF ligatures with standard ASCII equivalents."""
        raw_text = "The de\ufb01nition of \ufb02exibility in e\ufb03cient architectures."
        normalized = self.preprocessor.normalize_text(raw_text)
        self.assertIn("definition", normalized)
        self.assertIn("flexibility", normalized)
        self.assertIn("efficient", normalized)

    def test_hyphen_wrap_repair(self) -> None:
        """Test un-breaking words split across line breaks with hyphens."""
        raw_text = "Deep residual learning eases the train-\ning of deeper net-\nworks."
        normalized = self.preprocessor.normalize_text(raw_text)
        self.assertIn("training of deeper networks", normalized)
        self.assertNotIn("train-", normalized)
        self.assertNotIn("net-", normalized)

    def test_header_footer_removal(self) -> None:
        """Test removing arXiv submission headers and standalone page numbers."""
        raw_text = "arXiv:1512.03385v1 [cs.CV] 10 Dec 2015\n\nDeep neural networks are effective.\n\n12\n"
        normalized = self.preprocessor.normalize_text(raw_text)
        self.assertNotIn("arXiv:1512.03385v1", normalized)
        self.assertIn("Deep neural networks are effective.", normalized)
        # Standalone page number '12' stripped
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]
        self.assertNotIn("12", lines)

    def test_sentence_splitting_with_abbreviations(self) -> None:
        """Test that academic abbreviations (et al., i.e., e.g., Fig. 1) do not cause false sentence splits."""
        text = (
            "He et al. introduced deep residual learning (i.e., ResNet) for vision tasks. "
            "As shown in Fig. 1, identity shortcut connections avoid degradation. "
            "Our model achieved a 3.57% top-5 error on the test set."
        )
        sentences = self.preprocessor.split_sentences(text, page_number=1, provenance="page_1")
        self.assertEqual(len(sentences), 3)

        self.assertIn("He et al.", sentences[0]["text"])
        self.assertIn("i.e., ResNet", sentences[0]["text"])
        self.assertEqual(sentences[0]["page_number"], 1)
        self.assertEqual(sentences[0]["provenance"], "page_1")

        self.assertIn("Fig. 1", sentences[1]["text"])
        self.assertIn("3.57%", sentences[2]["text"])

    def test_empty_or_invalid_input(self) -> None:
        """Test graceful handling of empty or None inputs."""
        self.assertEqual(self.preprocessor.normalize_text(""), "")
        self.assertEqual(self.preprocessor.split_sentences(""), [])
        self.assertEqual(self.preprocessor.process_paper_record({}), [])

    def test_process_paper_record_full_text(self) -> None:
        """Test preprocessing full-text records with page-by-page structures."""
        paper = {
            "source_type": "open_access_full_text",
            "pages": [
                {"page_number": 1, "text": "First page text. Another sentence."},
                {"page_number": 2, "text": "Second page text."},
            ],
        }
        sentences = self.preprocessor.process_paper_record(paper)
        self.assertEqual(len(sentences), 3)
        self.assertEqual(sentences[0]["page_number"], 1)
        self.assertEqual(sentences[0]["provenance"], "page_1")
        self.assertEqual(sentences[2]["page_number"], 2)
        self.assertEqual(sentences[2]["provenance"], "page_2")

    def test_process_paper_record_abstract_only(self) -> None:
        """Test fallback for abstract_only records setting page_number=None and provenance='abstract'."""
        paper = {
            "source_type": "abstract_only",
            "abstract": "Deeper neural networks are more difficult to train. We present a residual learning framework.",
            "pages": [],
            "full_text": None,
        }
        sentences = self.preprocessor.process_paper_record(paper)
        self.assertEqual(len(sentences), 2)
        self.assertIsNone(sentences[0]["page_number"])
        self.assertEqual(sentences[0]["provenance"], "abstract")
        self.assertIsNone(sentences[1]["page_number"])
        self.assertEqual(sentences[1]["provenance"], "abstract")


class TestSectionSegmenter(unittest.TestCase):
    """Tests for academic section boundary identification and sentence tagging."""

    def setUp(self) -> None:
        self.segmenter = SectionSegmenter()

    def test_identify_heading_patterns(self) -> None:
        """Test recognition of standard heading variations."""
        self.assertEqual(self.segmenter.identify_heading("1. Introduction"), "INTRODUCTION")
        self.assertEqual(self.segmenter.identify_heading("ABSTRACT"), "ABSTRACT")
        self.assertEqual(self.segmenter.identify_heading("III. Proposed Method"), "METHODOLOGY")
        self.assertEqual(self.segmenter.identify_heading("4. Experimental Results"), "EXPERIMENTS")
        self.assertEqual(self.segmenter.identify_heading("Conclusion"), "CONCLUSION")
        self.assertEqual(self.segmenter.identify_heading("Limitations and Future Work"), "LIMITATIONS")

    def test_non_heading_lines(self) -> None:
        """Test that regular sentences are not classified as headings."""
        self.assertIsNone(self.segmenter.identify_heading("In this paper, we propose a new neural network."))
        self.assertIsNone(self.segmenter.identify_heading("The results in Table 1 show substantial improvement."))

    def test_assign_sections_abstract_only(self) -> None:
        """Test that all abstract sentences are assigned section='ABSTRACT'."""
        sentences = [
            {"sentence_id": 1, "text": "Sentence one.", "provenance": "abstract"},
            {"sentence_id": 2, "text": "Sentence two.", "provenance": "abstract"},
        ]
        tagged = self.segmenter.assign_sections_to_sentences(sentences)
        self.assertEqual(tagged[0]["section"], "ABSTRACT")
        self.assertEqual(tagged[1]["section"], "ABSTRACT")

    def test_assign_sections_full_text_progression(self) -> None:
        """Test section transition progression across full text sentences."""
        sentences = [
            {"sentence_id": 1, "text": "1. Introduction In this paper we introduce residual learning.", "provenance": "page_1"},
            {"sentence_id": 2, "text": "Deeper networks are difficult to optimize.", "provenance": "page_1"},
            {"sentence_id": 3, "text": "3. Approach We formulate the residual mapping.", "provenance": "page_2"},
            {"sentence_id": 4, "text": "4. Experiments We evaluate on ImageNet.", "provenance": "page_3"},
            {"sentence_id": 5, "text": "5. Conclusion We have presented residual networks.", "provenance": "page_4"},
        ]
        tagged = self.segmenter.assign_sections_to_sentences(sentences)
        self.assertEqual(tagged[0]["section"], "INTRODUCTION")
        self.assertEqual(tagged[1]["section"], "INTRODUCTION")
        self.assertEqual(tagged[2]["section"], "METHODOLOGY")
        self.assertEqual(tagged[3]["section"], "EXPERIMENTS")
        self.assertEqual(tagged[4]["section"], "CONCLUSION")


class TestKeywordExtractor(unittest.TestCase):
    """Tests for technical keyphrase extraction and OpenAlex concept blending."""

    def setUp(self) -> None:
        self.extractor = KeywordExtractor(max_keywords=10)

    def test_extract_ngrams_and_stopword_filtering(self) -> None:
        """Test n-gram extraction and verification that generic academic stopwords are excluded."""
        text = (
            "Residual learning and shortcut connections improve deep neural networks. "
            "The degradation problem is addressed using identity mapping. "
            "Our residual networks achieve high accuracy on image recognition."
        )
        keywords = self.extractor.extract_keywords(text)
        terms = [k["term"].lower() for k in keywords]

        # Domain terms should be captured
        self.assertTrue(any("residual" in t for t in terms))

        # Academic filler words should NOT be standalone keywords
        self.assertNotIn("paper", terms)
        self.assertNotIn("method", terms)
        self.assertNotIn("results", terms)
        self.assertNotIn("using", terms)

    def test_openalex_concept_blending(self) -> None:
        """Test combining statistical n-grams with OpenAlex concepts."""
        text = "Deep convolutional networks for computer vision."
        concepts = [
            {"display_name": "Convolutional neural network", "score": 0.95},
            {"display_name": "Computer vision", "score": 0.88},
        ]
        keywords = self.extractor.extract_keywords(text, openalex_concepts=concepts)
        terms = [k["term"].lower() for k in keywords]
        sources = [k["source"] for k in keywords]

        self.assertIn("computer vision", terms)
        self.assertTrue("hybrid" in sources or "openalex_concept" in sources)

    def test_salience_score_bounds(self) -> None:
        """Test that within-document salience scores are strictly within [0.0, 1.0]."""
        text = "Deep residual learning eases the training of neural networks."
        keywords = self.extractor.extract_keywords(text)
        for k in keywords:
            self.assertGreaterEqual(k["salience_score"], 0.0)
            self.assertLessEqual(k["salience_score"], 1.0)
            self.assertIn(k["ngram_type"], ("unigram", "bigram", "trigram", "concept"))

    def test_empty_text_with_concepts(self) -> None:
        """Test fallback when text is empty but concepts are provided."""
        concepts = ["Machine learning", "Artificial intelligence"]
        keywords = self.extractor.extract_keywords("", openalex_concepts=concepts)
        self.assertEqual(len(keywords), 2)
        self.assertEqual(keywords[0]["source"], "openalex_concept")


class TestInformationExtractor(unittest.TestCase):
    """Tests for evidence-grounded research dimension extraction."""

    def setUp(self) -> None:
        self.extractor = InformationExtractor()

    def test_extract_objectives_with_evidence(self) -> None:
        """Test extraction of objectives with exact supporting evidence sentence."""
        sentences = [
            {
                "text": "In this paper, we propose a residual learning framework to ease training of deep networks.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            },
            {
                "text": "Deeper networks are known to suffer from degradation.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            },
        ]
        objs = self.extractor.extract_objectives(sentences)
        self.assertEqual(len(objs), 1)
        self.assertIn("propose a residual learning framework", objs[0]["statement"])
        self.assertEqual(objs[0]["evidence"], sentences[0]["text"])
        self.assertEqual(objs[0]["page_number"], 1)
        self.assertEqual(objs[0]["section"], "INTRODUCTION")
        self.assertGreaterEqual(objs[0]["confidence"], 0.8)

    def test_extract_methodologies_with_evidence(self) -> None:
        """Test extraction of methodologies with exact supporting evidence sentence."""
        sentences = [
            {
                "text": "We introduce a deep residual learning framework utilizing shortcut connections.",
                "page_number": 2,
                "provenance": "page_2",
                "section": "METHODOLOGY",
            }
        ]
        methods = self.extractor.extract_methodologies(sentences)
        self.assertEqual(len(methods), 1)
        self.assertEqual(methods[0]["evidence"], sentences[0]["text"])
        self.assertEqual(methods[0]["page_number"], 2)
        self.assertEqual(methods[0]["section"], "METHODOLOGY")

    def test_extract_datasets(self) -> None:
        """Test dataset recognition from curated lexicon and patterns."""
        sentences = [
            {
                "text": "We evaluate our models on the ImageNet 2012 classification dataset and CIFAR-10.",
                "page_number": 3,
                "provenance": "page_3",
                "section": "EXPERIMENTS",
            }
        ]
        datasets = self.extractor.extract_datasets(sentences)
        names = [d["name"] for d in datasets]
        self.assertIn("ImageNet", names)
        self.assertIn("CIFAR-10", names)
        self.assertEqual(datasets[0]["page_number"], 3)
        self.assertEqual(datasets[0]["evidence"], sentences[0]["text"])

    def test_extract_evaluation_metrics(self) -> None:
        """Test metrics extraction with associated numerical values."""
        sentences = [
            {
                "text": "Our 152-layer ResNet achieves a 3.57% top-5 error on the ImageNet test set.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            }
        ]
        metrics = self.extractor.extract_metrics(sentences)
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0]["metric"], "top-5 error")
        self.assertEqual(metrics[0]["value"], "3.57%")
        self.assertEqual(metrics[0]["page_number"], 1)

    def test_extract_findings(self) -> None:
        """Test extraction of empirical research findings."""
        sentences = [
            {
                "text": "Our ensemble outperforms all previous systems and won 1st place in ILSVRC 2015.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            }
        ]
        findings = self.extractor.extract_findings(sentences)
        self.assertEqual(len(findings), 1)
        self.assertIn("won 1st place", findings[0]["finding"])
        self.assertEqual(findings[0]["page_number"], 1)

    def test_extract_limitations(self) -> None:
        """Test extraction of stated research limitations or bottlenecks."""
        sentences = [
            {
                "text": "We note that 1202-layer networks suffer from overfitting on small datasets like CIFAR-10.",
                "page_number": 8,
                "provenance": "page_8",
                "section": "EXPERIMENTS",
            }
        ]
        limits = self.extractor.extract_limitations(sentences)
        self.assertEqual(len(limits), 1)
        self.assertIn("overfitting", limits[0]["limitation"])
        self.assertEqual(limits[0]["page_number"], 8)

    def test_zero_hallucination_empty_results(self) -> None:
        """Test that missing dimensions return empty lists, never fabricated facts."""
        sentences = [
            {
                "text": "A simple discussion on general topics.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "DISCUSSION",
            }
        ]
        extracted = self.extractor.extract_all(sentences)
        self.assertEqual(extracted["research_objectives"], [])
        self.assertEqual(extracted["research_methodologies"], [])
        self.assertEqual(extracted["datasets"], [])
        self.assertEqual(extracted["evaluation_metrics"], [])
        self.assertEqual(extracted["research_findings"], [])
        self.assertEqual(extracted["research_limitations"], [])


class TestNLPResearchAnalyzer(unittest.TestCase):
    """Tests for the high-level NLPResearchAnalyzer orchestrator."""

    def setUp(self) -> None:
        self.analyzer = NLPResearchAnalyzer()

    def test_full_text_paper_analysis(self) -> None:
        """Test full-text paper record analysis with preserved page provenance."""
        paper = {
            "paper_id": "W2949650786",
            "title": "Deep Residual Learning for Image Recognition",
            "source_type": "open_access_full_text",
            "total_pages": 2,
            "abstract": "Deeper neural networks are more difficult to train.",
            "concepts": ["Residual neural network", "ImageNet"],
            "pages": [
                {
                    "page_number": 1,
                    "text": (
                        "1. Introduction\n"
                        "In this paper, we propose a deep residual learning framework to ease network training. "
                        "Our 152-layer ResNet achieves 3.57% top-5 error on the ImageNet test set. "
                        "The model won 1st place in the ILSVRC 2015 classification task."
                    ),
                },
                {
                    "page_number": 2,
                    "text": (
                        "4. Experiments\n"
                        "We evaluate on the CIFAR-10 dataset. "
                        "However, extremely deep models may suffer from overfitting when data is scarce."
                    ),
                },
            ],
        }

        result = self.analyzer.analyze(paper)

        self.assertEqual(result["paper_id"], "W2949650786")
        self.assertEqual(result["paper_title"], "Deep Residual Learning for Image Recognition")
        self.assertEqual(result["source_type"], "open_access_full_text")
        self.assertEqual(result["analysis_metadata"]["scope"], "full_text")

        # Verify Objectives
        self.assertGreaterEqual(len(result["research_objectives"]), 1)
        self.assertEqual(result["research_objectives"][0]["page_number"], 1)

        # Verify Datasets
        dataset_names = [d["name"] for d in result["datasets"]]
        self.assertIn("ImageNet", dataset_names)
        self.assertIn("CIFAR-10", dataset_names)

        # Verify Metrics
        self.assertGreaterEqual(len(result["evaluation_metrics"]), 1)
        self.assertEqual(result["evaluation_metrics"][0]["metric"], "top-5 error")
        self.assertEqual(result["evaluation_metrics"][0]["value"], "3.57%")

        # Verify Findings
        self.assertGreaterEqual(len(result["research_findings"]), 1)

        # Verify Limitations
        self.assertGreaterEqual(len(result["research_limitations"]), 1)
        self.assertEqual(result["research_limitations"][0]["page_number"], 2)

        # Verify JSON serializability
        serialized = json.dumps(result)
        self.assertIsInstance(serialized, str)

    def test_abstract_only_paper_analysis(self) -> None:
        """Test abstract-only record analysis setting page_number=None and provenance='abstract'."""
        original_abstract = (
            "Deeper neural networks are more difficult to train. "
            "In this paper, we propose a residual learning framework. "
            "We evaluate our networks on ImageNet and achieve high accuracy."
        )
        paper = {
            "paper_id": "W2194775991",
            "title": "Deep Residual Learning for Image Recognition",
            "source_type": "abstract_only",
            "total_pages": 0,
            "abstract": original_abstract,
            "concepts": ["Residual neural network"],
            "pages": [],
            "full_text": None,
        }

        result = self.analyzer.analyze(paper)

        self.assertEqual(result["source_type"], "abstract_only")
        self.assertEqual(result["analysis_metadata"]["scope"], "abstract_only")

        # Verify page_number is None and provenance is 'abstract'
        for obj in result["research_objectives"]:
            self.assertIsNone(obj["page_number"])
            self.assertEqual(obj["provenance"], "abstract")

        for ds in result["datasets"]:
            self.assertIsNone(ds["page_number"])
            self.assertEqual(ds["provenance"], "abstract")

        # Invariant check: original abstract unchanged
        self.assertEqual(paper["abstract"], original_abstract)

    def test_empty_paper_handling(self) -> None:
        """Test handling of empty or None paper dictionary."""
        result = self.analyzer.analyze({})
        self.assertEqual(result["paper_id"], "")
        self.assertEqual(result["research_objectives"], [])
        self.assertEqual(result["extraction_summary"]["objectives_count"], 0)


class TestTargetedNLPQualityRegression(unittest.TestCase):
    """
    Regression tests addressing the specific false positives and extraction
    inaccuracies identified during the ResNet quality audit.
    """

    def setUp(self) -> None:
        self.extractor = InformationExtractor()
        self.keyword_extractor = KeywordExtractor(max_keywords=15)
        self.analyzer = NLPResearchAnalyzer()

    def test_mnist_citation_not_extracted_as_dataset(self) -> None:
        """1. MNIST mentioned in a citation is not extracted as an evaluated dataset."""
        sentences = [
            {
                "text": "This phenomenon is similar to that on ImageNet (Fig. 4, left) and on MNIST (see [42]), suggesting that such an optimization difficulty is a fundamental problem.",
                "page_number": 7,
                "provenance": "page_7",
                "section": "METHODOLOGY",
            }
        ]
        datasets = self.extractor.extract_datasets(sentences)
        names = [d["name"] for d in datasets]
        self.assertIn("ImageNet", names)
        self.assertNotIn("MNIST", names)

    def test_cifar10_not_duplicated_as_cifar(self) -> None:
        """2. CIFAR-10 is not duplicated as CIFAR from the same sentence."""
        sentences = [
            {
                "text": "We also present analysis on CIFAR-10 with 100 and 1000 layers.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            }
        ]
        datasets = self.extractor.extract_datasets(sentences)
        names = [d["name"] for d in datasets]
        self.assertIn("CIFAR-10", names)
        self.assertNotIn("CIFAR", names)

    def test_feature_map_not_extracted_as_map(self) -> None:
        """3. 'Feature map' is not extracted as mAP."""
        sentences = [
            {
                "text": "The convolutional layers mostly have 3x3 filters and follow two simple rules for the output feature map.",
                "page_number": 3,
                "provenance": "page_3",
                "section": "EXPERIMENTS",
            }
        ]
        metrics = self.extractor.extract_metrics(sentences)
        self.assertEqual(len(metrics), 0)

    def test_genuine_map_values_extracted_correctly(self) -> None:
        """4. Genuine mAP values are extracted correctly."""
        sentences = [
            {
                "text": "Under this setting, the results are an mAP@.5 of 55.7% and an mAP@[.5, .95] of 34.9% (Table 9).",
                "page_number": 11,
                "provenance": "page_11",
                "section": "DISCUSSION",
            }
        ]
        metrics = self.extractor.extract_metrics(sentences)
        self.assertGreaterEqual(len(metrics), 1)
        map_metrics = {m["metric"]: m["value"] for m in metrics}
        self.assertIn("55.7%", list(map_metrics.values()))

    def test_network_depth_not_extracted_as_test_error(self) -> None:
        """5. Network depth 56 is not extracted as test error."""
        sentences = [
            {
                "text": "(1e4) test error (%) 56-layer 20-layer 56-layer 20-layer Figure 1.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            }
        ]
        metrics = self.extractor.extract_metrics(sentences)
        for m in metrics:
            if m["metric"] == "test error":
                self.assertNotEqual(m["value"], "56")
                self.assertIsNone(m["value"])

    def test_dataset_number_not_extracted_as_training_error(self) -> None:
        """6. Dataset number 10 is not extracted as training error."""
        sentences = [
            {
                "text": "Training error (left) and test error (right) on CIFAR-10 with 20-layer and 56-layer 'plain' networks.",
                "page_number": 1,
                "provenance": "page_1",
                "section": "INTRODUCTION",
            }
        ]
        metrics = self.extractor.extract_metrics(sentences)
        for m in metrics:
            self.assertNotEqual(m["value"], "10")
            self.assertNotEqual(m["value"], "20")
            self.assertNotEqual(m["value"], "56")
            self.assertIsNone(m["value"])

    def test_we_address_degradation_not_a_limitation(self) -> None:
        """7. 'We address the degradation problem' is not extracted as a limitation."""
        sentences = [
            {
                "text": "In this paper, we address the degradation problem by introducing a deep residual learning framework.",
                "page_number": 2,
                "provenance": "page_2",
                "section": "INTRODUCTION",
            }
        ]
        limitations = self.extractor.extract_limitations(sentences)
        self.assertEqual(len(limitations), 0)

    def test_degradation_well_addressed_not_a_limitation(self) -> None:
        """8. 'The degradation problem is well addressed' is not extracted as a limitation."""
        sentences = [
            {
                "text": "This indicates that the degradation problem is well addressed in this setting and we manage to obtain accuracy gains from increased depth.",
                "page_number": 5,
                "provenance": "page_5",
                "section": "EXPERIMENTS",
            }
        ]
        limitations = self.extractor.extract_limitations(sentences)
        self.assertEqual(len(limitations), 0)

    def test_bottleneck_architecture_not_classified_as_limitation(self) -> None:
        """9. 'Bottleneck architecture' is not classified as a limitation."""
        sentences = [
            {
                "text": "Right: a 'bottleneck' building block for ResNet-50/101/152. Deeper Bottleneck Architectures.",
                "page_number": 6,
                "provenance": "page_6",
                "section": "METHODOLOGY",
            }
        ]
        limitations = self.extractor.extract_limitations(sentences)
        self.assertEqual(len(limitations), 0)

    def test_genuine_resource_constraints_and_failure_modes_extracted(self) -> None:
        """10. Genuine resource constraints and experimental failure modes remain extractable."""
        sentences = [
            {
                "text": "Because of concerns on the training time that we can afford, we modify the building block as a bottleneck design.",
                "page_number": 6,
                "provenance": "page_6",
                "section": "METHODOLOGY",
            },
            {
                "text": "We note that 1202-layer networks suffer from overfitting on small datasets like CIFAR-10.",
                "page_number": 8,
                "provenance": "page_8",
                "section": "EXPERIMENTS",
            },
        ]
        limitations = self.extractor.extract_limitations(sentences)
        self.assertEqual(len(limitations), 2)

    def test_table_and_subsection_headings_not_findings(self) -> None:
        """11. Table and subsection headings are not extracted as findings."""
        sentences = [
            {
                "text": "Comparisons with State-of-the-art Methods.",
                "page_number": 7,
                "provenance": "page_7",
                "section": "METHODOLOGY",
            },
            {
                "text": "Comparisons of localization error (%) on the ImageNet dataset with state-of-the-art methods.",
                "page_number": 12,
                "provenance": "page_12",
                "section": "DISCUSSION",
            },
        ]
        findings = self.extractor.extract_findings(sentences)
        self.assertEqual(len(findings), 0)

    def test_singular_plural_keyword_duplicates_reduced(self) -> None:
        """12. Singular/plural keyword duplicates are reduced."""
        text = "Residual layers and each layer in deep networks. The layers have identity mapping."
        keywords = self.keyword_extractor.extract_keywords(text)
        terms = [k["term"].lower() for k in keywords]
        # Should not contain BOTH 'layer' AND 'layers'
        self.assertFalse("layer" in terms and "layers" in terms)

    def test_abstract_only_reports_zero_analyzed_pages(self) -> None:
        """13. Abstract-only records report zero analyzed PDF pages."""
        paper = {
            "paper_id": "W_ABSTRACT_PAGES_TEST",
            "title": "Abstract Test Paper",
            "source_type": "abstract_only",
            "abstract": "In this paper we propose a new framework for deep vision.",
            "pages": [],
            "total_pages": 0,
            "full_text": None,
        }
        result = self.analyzer.analyze(paper)
        self.assertEqual(result["analysis_metadata"]["analyzed_pages"], 0)
        self.assertEqual(result["analysis_metadata"]["analyzed_passages"], 1)
        self.assertEqual(result["analysis_metadata"]["scope"], "abstract_only")


if __name__ == "__main__":
    unittest.main()
