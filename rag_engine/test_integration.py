"""
Dedicated Integration Test Suite
Module 2 — Phase 4: Hybrid RAG Engine Integration

Validates end-to-end integration between Member 1 (paper_processing)
and Member 2 (rag_engine) using real research paper data (ResNet)
and Member 2 sample papers.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure repo root is on sys.path
repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from paper_processing.nlp_analyzer import analyze_paper
from paper_processing.pdf_extractor import extract_text_from_pdf
from paper_processing.record_enrichment import enrich_paper_record
from rag_engine.integrated_pipeline import (
    IntegratedRAGPipeline,
    check_paper_index_status,
)
from rag_engine.paper_adapter import (
    PaperIngestionAdapter,
    classify_methodology,
    normalize_dataset_name,
)


class TestMember1Member2Integration(unittest.TestCase):
    """Integration test suite covering all Phase 4 adapter and pipeline requirements."""

    @classmethod
    def setUpClass(cls):
        """Prepare real ResNet paper data and temporary ChromaDB test database."""
        cls.test_dir = tempfile.mkdtemp(prefix="rag_integration_test_")
        cls.db_path = os.path.join(cls.test_dir, "chroma_db")

        # 1. Process real ResNet paper with Member 1
        cls.resnet_pdf_path = str(repo_root / "paper_processing" / "data" / "papers" / "W2949650786.pdf")
        cls.has_resnet_pdf = os.path.exists(cls.resnet_pdf_path)

        if cls.has_resnet_pdf:
            extracted = extract_text_from_pdf("W2949650786", cls.resnet_pdf_path)
            raw_work = {
                "paper_id": "W2949650786",
                "openalex_id": "https://openalex.org/W2949650786",
                "title": "Deep Residual Learning for Image Recognition",
                "authors": ["Kaiming He", "Xiangyu Zhang", "Shaoqing Ren", "Jian Sun"],
                "year": 2016,
                "doi": "https://doi.org/10.1109/cvpr.2016.90",
                "abstract": "Deeper neural networks are more difficult to train.",
                "publication_type": "article",
                "concepts": ["Residual neural network", "Deep learning"],
                "landing_page_url": "https://doi.org/10.1109/cvpr.2016.90",
            }
            discovery_res = {
                "paper_id": "W2949650786",
                "pdf_url": "https://arxiv.org/pdf/1512.03385.pdf",
                "access_type": "open_access_pdf",
                "landing_page_url": "https://doi.org/10.1109/cvpr.2016.90",
                "discovery_source": "arxiv",
            }
            download_res = {
                "paper_id": "W2949650786",
                "status": "downloaded",
                "pdf_path": cls.resnet_pdf_path,
                "file_size_bytes": os.path.getsize(cls.resnet_pdf_path),
            }
            cls.resnet_enriched = enrich_paper_record(
                raw_work,
                discovery_result=discovery_res,
                download_result=download_res,
                extraction_result=extracted,
            )
            cls.resnet_analyzed = analyze_paper(cls.resnet_enriched)
        else:
            cls.resnet_enriched = None
            cls.resnet_analyzed = None

        # 2. Prepare an abstract-only record
        cls.abstract_work = {
            "paper_id": "W_ABSTRACT_001",
            "openalex_id": "https://openalex.org/W_ABSTRACT_001",
            "title": "A Survey on Transformers in Healthcare",
            "authors": ["Alice Smith"],
            "year": 2023,
            "doi": "https://doi.org/10.1000/182",
            "abstract": (
                "In this survey, we evaluate Vision Transformers and CNNs on ImageNet and medical imaging datasets. "
                "We achieve 94.5% top-1 accuracy on MRI disease classification. "
                "However, limited labeled medical datasets remain a major limitation."
            ),
            "publication_type": "article",
            "concepts": ["Vision Transformer", "Medical imaging"],
            "landing_page_url": "https://doi.org/10.1000/182",
        }
        cls.abstract_enriched = enrich_paper_record(cls.abstract_work)
        cls.abstract_analyzed = analyze_paper(cls.abstract_enriched)

        # 3. Initialize Adapter and Pipeline with test DB
        cls.adapter = PaperIngestionAdapter()
        cls.pipeline = IntegratedRAGPipeline(database_path=cls.db_path)

    @classmethod
    def tearDownClass(cls):
        """Clean up temporary test database directory."""
        try:
            shutil.rmtree(cls.test_dir)
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Adapter Unit Tests
    # -------------------------------------------------------------------------

    def test_01_full_text_paper_adaptation(self):
        """Verify full-text paper produces page-aware and section-aware body chunks."""
        if not self.has_resnet_pdf:
            self.skipTest("ResNet PDF not available.")

        chunks = self.adapter.adapt_paper(self.resnet_enriched, self.resnet_analyzed)
        self.assertGreater(len(chunks), 10)

        body_chunks = [c for c in chunks if c["chunk_type"] == "body_passage"]
        self.assertGreater(len(body_chunks), 0)

        # Check page provenance
        page_numbers = {c["page_number"] for c in body_chunks}
        self.assertTrue(all(isinstance(p, int) and p >= 1 for p in page_numbers))
        self.assertIn(1, page_numbers)

        # Check section awareness
        sections = {c["section"] for c in body_chunks}
        self.assertTrue(len(sections) > 1, f"Expected multiple sections, got {sections}")
        self.assertTrue(any(s in ("INTRODUCTION", "RELATED_WORK", "METHODOLOGY") for s in sections))

        # Check deterministic chunk ID format
        for c in body_chunks:
            self.assertTrue(c["chunk_id"].startswith("W2949650786_p"))

    def test_02_abstract_only_adaptation(self):
        """Verify abstract-only record adaptation uses sentinel page_number 0 and preserves provenance."""
        chunks = self.adapter.adapt_paper(self.abstract_enriched, self.abstract_analyzed)
        self.assertGreater(len(chunks), 0)

        abstract_passages = [c for c in chunks if c["chunk_type"] == "abstract_passage"]
        self.assertGreater(len(abstract_passages), 0)

        for c in abstract_passages:
            self.assertEqual(c["page_number"], 0)
            self.assertEqual(c["section"], "ABSTRACT")
            self.assertEqual(c["provenance"], "abstract")
            self.assertEqual(c["source_type"], "abstract_only")
            self.assertTrue(c["chunk_id"].startswith("W_ABSTRACT_001_abstract_c"))

    def test_03_nlp_fact_chunk_generation(self):
        """Verify all 7 NLP dimensions generate distinct, identifiable fact chunks with evidence."""
        if not self.has_resnet_pdf:
            self.skipTest("ResNet PDF not available.")

        chunks = self.adapter.adapt_paper(self.resnet_enriched, self.resnet_analyzed)
        fact_chunks = {c["dimension"]: c for c in chunks if c["chunk_type"] == "nlp_fact"}

        expected_dimensions = [
            "objectives",
            "methodologies",
            "datasets",
            "evaluation_metrics",
            "findings",
            "limitations",
            "keywords",
        ]
        for dim in expected_dimensions:
            self.assertIn(dim, fact_chunks, f"Missing NLP fact chunk for dimension: {dim}")
            chunk = fact_chunks[dim]
            self.assertEqual(chunk["paper_id"], "W2949650786")
            if dim != "keywords":
                self.assertIn("Evidence:", chunk["text"])
            else:
                self.assertIn("Keywords:", chunk["text"])

        # Datasets chunk must mention ImageNet and CIFAR-10
        datasets_text = fact_chunks["datasets"]["text"]
        self.assertIn("ImageNet", datasets_text)
        self.assertIn("CIFAR-10", datasets_text)

        # Metrics chunk must mention error rates
        metrics_text = fact_chunks["evaluation_metrics"]["text"]
        self.assertTrue("error" in metrics_text.lower() or "accuracy" in metrics_text.lower())

    def test_04_methodology_attribution(self):
        """Verify methodology classification distinguishes proposed methods from related work and setup."""
        # 1. Proposed methodology
        prop_item = {
            "method": "deep residual learning framework",
            "evidence": "In this paper, we address the degradation problem by introducing a deep residual learning framework.",
            "section": "INTRODUCTION",
            "page_number": 2,
        }
        self.assertEqual(classify_methodology(prop_item), "proposed_method")

        # 2. Related work methodology
        rel_item = {
            "method": "highway networks",
            "evidence": "Concurrent with our work, highway networks [42] present shortcut connections with gating functions.",
            "section": "RELATED_WORK",
            "page_number": 2,
        }
        self.assertEqual(classify_methodology(rel_item), "related_work_method")

        # 3. Experimental setup
        setup_item = {
            "method": "SGD optimizer",
            "evidence": "We evaluate with SGD using a batch size of 256 and learning rate of 0.1.",
            "section": "EXPERIMENTS",
            "page_number": 4,
        }
        self.assertEqual(classify_methodology(setup_item), "experimental_setup")

    def test_05_dataset_alias_normalization(self):
        """Verify dataset aliases normalize correctly for aggregation while preserving original names."""
        self.assertEqual(normalize_dataset_name("COCO"), "MS COCO")
        self.assertEqual(normalize_dataset_name("ms coco"), "MS COCO")
        self.assertEqual(normalize_dataset_name("ILSVRC"), "ImageNet")
        self.assertEqual(normalize_dataset_name("cifar-10"), "CIFAR-10")
        self.assertEqual(normalize_dataset_name("PASCAL"), "PASCAL VOC")

        # Check in adapted NLP chunk that both original and normalized are preserved
        if self.has_resnet_pdf:
            fact_chunks = self.adapter.create_nlp_fact_chunks(
                self.resnet_analyzed, "W2949650786", "Deep Residual Learning"
            )
            ds_chunk = next(c for c in fact_chunks if c["dimension"] == "datasets")
            self.assertIn("ImageNet", ds_chunk["text"])

    def test_06_legacy_sample_paper_adaptation(self):
        """Verify Member 2's sample papers adapt seamlessly preserving original chunk IDs."""
        sample_dict = {
            "paper_id": "paper_001",
            "paper_title": "Deep Learning Techniques for Medical Image Classification",
            "text": (
                "Paper ID: paper_001\nTitle: Deep Learning Techniques for Medical Image Classification\n\n"
                "Medical image classification is an important application of artificial intelligence. "
                "Convolutional Neural Networks are widely used for analysing X-ray images and MRI scans."
            ),
            "source": "paper_001.txt",
        }
        adapted = self.adapter.adapt_legacy_paper(sample_dict, chunk_size=150, overlap=30)
        self.assertGreater(len(adapted), 0)
        for c in adapted:
            self.assertTrue(c["chunk_id"].startswith("paper_001_chunk_"))
            self.assertEqual(c["paper_id"], "paper_001")
            self.assertEqual(c["source_type"], "legacy_sample")
            self.assertEqual(c["page_number"], 1)

    # -------------------------------------------------------------------------
    # Pipeline Ingestion & Multi-Paper Storage Tests
    # -------------------------------------------------------------------------

    def test_07_ingest_sample_data_and_resnet(self):
        """Verify ingesting Member 2's 5 sample papers and ResNet into the same collection."""
        # 1. Ingest Member 2 sample papers
        sample_results = self.pipeline.ingest_sample_data()
        self.assertEqual(len(sample_results), 5)
        for res in sample_results:
            self.assertIn(res["status"], ("indexed", "already_indexed"))

        # 2. Ingest real ResNet paper
        if self.has_resnet_pdf:
            resnet_res = self.pipeline.ingest_paper(self.resnet_enriched, self.resnet_analyzed)
            self.assertIn(resnet_res["status"], ("indexed", "already_indexed"))
            self.assertEqual(resnet_res["paper_id"], "W2949650786")

        # 3. Ingest abstract-only paper
        abs_res = self.pipeline.ingest_paper(self.abstract_enriched, self.abstract_analyzed)
        self.assertIn(abs_res["status"], ("indexed", "already_indexed"))
        self.assertEqual(abs_res["paper_id"], "W_ABSTRACT_001")

        # 4. Verify ChromaDB contains chunks from ALL papers simultaneously
        stored = self.pipeline.vector_store.collection.get(include=["metadatas"])
        stored_metas = stored.get("metadatas", [])
        stored_papers = {m["paper_id"] for m in stored_metas}

        self.assertIn("paper_001", stored_papers)
        self.assertIn("paper_002", stored_papers)
        self.assertIn("paper_003", stored_papers)
        self.assertIn("paper_004", stored_papers)
        self.assertIn("paper_005", stored_papers)
        self.assertIn("W_ABSTRACT_001", stored_papers)
        if self.has_resnet_pdf:
            self.assertIn("W2949650786", stored_papers)

    def test_08_extended_chromadb_metadata(self):
        """Verify extended metadata (section, chunk_type, dimension, provenance) is stored in ChromaDB."""
        stored = self.pipeline.vector_store.collection.get(include=["metadatas"])
        metas = stored.get("metadatas", [])

        # Check required fields exist on every metadata record
        for m in metas:
            self.assertIn("paper_id", m)
            self.assertIn("paper_title", m)
            self.assertIn("page_number", m)
            self.assertIn("section", m)
            self.assertIn("chunk_type", m)
            self.assertIn("dimension", m)
            self.assertIn("provenance", m)
            self.assertIn("source_type", m)
            self.assertIn("confidence", m)

    def test_09_targeted_reindexing_isolation(self):
        """Verify reindexing one paper (force_reindex=True) never deletes chunks belonging to other papers."""
        # Record chunk count for paper_001 before reindexing
        p1_before = self.pipeline.vector_store.collection.get(
            where={"paper_id": "paper_001"}, include=["metadatas"]
        )
        p1_count_before = len(p1_before.get("ids", []))
        self.assertGreater(p1_count_before, 0)

        # Force reindex abstract paper
        self.pipeline.ingest_paper(self.abstract_enriched, self.abstract_analyzed, force_reindex=True)

        # Verify paper_001 chunks are completely unaffected
        p1_after = self.pipeline.vector_store.collection.get(
            where={"paper_id": "paper_001"}, include=["metadatas"]
        )
        p1_count_after = len(p1_after.get("ids", []))
        self.assertEqual(p1_count_before, p1_count_after)

    def test_10_bm25_synchronization(self):
        """Verify in-memory BM25 index contains all chunks from all papers stored in ChromaDB."""
        total_chroma_count = self.pipeline.vector_store.collection.count()
        self.assertEqual(len(self.pipeline.chunks), total_chroma_count)

        # Search for unique terms from different papers via BM25 keyword search
        kw_mri = self.pipeline.search("MRI scans X-ray images", mode="keyword", top_k=3)
        self.assertGreater(len(kw_mri), 0)
        self.assertEqual(kw_mri[0]["score_type"], "bm25_score")

        if self.has_resnet_pdf:
            kw_resnet = self.pipeline.search("residual learning framework shortcut", mode="keyword", top_k=3)
            self.assertGreater(len(kw_resnet), 0)
            self.assertTrue(any(r["paper_id"] == "W2949650786" for r in kw_resnet))

    # -------------------------------------------------------------------------
    # Hybrid Retrieval & Filtering Tests
    # -------------------------------------------------------------------------

    def test_11_hybrid_search_resnet_metrics(self):
        """Verify hybrid retrieval returns ResNet metric and dataset facts."""
        if not self.has_resnet_pdf:
            self.skipTest("ResNet PDF not available.")

        results = self.pipeline.search(
            "What is the top-5 error of ResNet on ImageNet?",
            mode="hybrid",
            top_k=5,
        )
        self.assertGreater(len(results), 0)

        # Top result or top-3 should include ResNet
        resnet_results = [r for r in results if r["paper_id"] == "W2949650786"]
        self.assertGreater(len(resnet_results), 0)

        # Check score_type is rrf_score
        for r in results:
            self.assertEqual(r["score_type"], "rrf_score")
            self.assertGreater(r["score"], 0)

    def test_12_hybrid_search_medical_sample_papers(self):
        """Verify hybrid retrieval answers Member 2's benchmark query accurately."""
        query = "How are CNNs used to detect diseases in MRI images?"
        results = self.pipeline.search(query, mode="hybrid", top_k=3)
        self.assertGreater(len(results), 0)

        # Member 2's benchmark relevant papers are paper_001 or paper_003
        matched_papers = {r["paper_id"] for r in results}
        self.assertTrue(
            "paper_001" in matched_papers or "paper_003" in matched_papers,
            f"Expected paper_001 or paper_003 in results, got {matched_papers}",
        )

    def test_13_metadata_filtering_section(self):
        """Verify filtering by section restricts both semantic and BM25 results before RRF."""
        results = self.pipeline.search(
            "residual learning framework",
            mode="hybrid",
            top_k=5,
            filters={"section": "METHODOLOGY"},
        )
        for r in results:
            self.assertEqual(r["section"], "METHODOLOGY")

    def test_14_metadata_filtering_chunk_type(self):
        """Verify filtering by chunk_type='nlp_fact' returns only structured NLP fact chunks."""
        results = self.pipeline.search(
            "ImageNet evaluation error accuracy",
            mode="hybrid",
            top_k=5,
            filters={"chunk_type": "nlp_fact"},
        )
        for r in results:
            self.assertEqual(r["chunk_type"], "nlp_fact")

    def test_15_abstract_only_page_number_conversion(self):
        """Verify abstract-only results convert sentinel page_number 0 to None in user-facing output."""
        results = self.pipeline.search(
            "Transformers in Healthcare survey medical imaging",
            mode="hybrid",
            top_k=3,
            filters={"paper_id": "W_ABSTRACT_001"},
        )
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertIsNone(
                r["page_number"],
                f"Expected page_number to be None for abstract-only result, got {r['page_number']}",
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
