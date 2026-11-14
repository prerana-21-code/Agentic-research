"""
Paper Adapter for RAG Engine Integration
Module 2 — Phase 4: Adapter Layer between Member 1 and Member 2

Translates Member 1's enriched research paper records and structured NLP insights
into standardized, page-aware, section-aware, and separately identifiable chunks
compatible with Member 2's ChromaDB VectorStore and BM25 KeywordSearch.
"""

from __future__ import annotations

import re
from typing import Any

from paper_processing.section_segmenter import SectionSegmenter
from paper_processing.text_preprocessor import AcademicTextPreprocessor
from rag_engine.vector_store import VectorStore


# Known academic dataset aliases mapped to canonical names
DATASET_ALIAS_MAP: dict[str, str] = {
    "coco": "MS COCO",
    "ms coco": "MS COCO",
    "microsoft coco": "MS COCO",
    "imagenet": "ImageNet",
    "ilsvrc": "ImageNet",
    "pascal voc": "PASCAL VOC",
    "pascal": "PASCAL VOC",
    "voc 2007": "PASCAL VOC",
    "voc 2012": "PASCAL VOC",
    "cifar": "CIFAR",
    "cifar-10": "CIFAR-10",
    "cifar-100": "CIFAR-100",
    "mnist": "MNIST",
    "squad": "SQuAD",
    "glue": "GLUE",
}

# Cue patterns for methodology classification
RELATED_WORK_CUES = re.compile(
    r"\b(in\s+\[\d+\]|concurrent\s+with|prior\s+(to|work|art)|earlier\s+work|"
    r"highway\s+networks?|inception|vgg|alexnet|papers?\s+of\s+\[\d+\]|"
    r"practices\s+and\s+theories|previous\s+(work|studies|methods))\b",
    re.IGNORECASE,
)

EXPERIMENTAL_SETUP_CUES = re.compile(
    r"\b(we\s+evaluate|we\s+compare|in\s+the\s+first\s+comparison|baseline|"
    r"batch\s+size|learning\s+rate|weight\s+decay|sgd|iterations|epochs?|"
    r"hyperparameters?|data\s+augmentation|warmup)\b",
    re.IGNORECASE,
)

PROPOSED_METHOD_CUES = re.compile(
    r"\b(we\s+propose|we\s+present|we\s+introduce|we\s+formulate|we\s+adopt|"
    r"in\s+this\s+paper|in\s+our\s+case|our\s+(method|framework|model|architecture|"
    r"approach|network|formulation)|residual\s+learning\s+framework|"
    r"identity\s+shortcut)\b",
    re.IGNORECASE,
)


def normalize_dataset_name(name: str) -> str:
    """
    Normalizes dataset aliases for aggregation without overwriting original names.

    Examples:
        'coco' -> 'MS COCO'
        'MS COCO' -> 'MS COCO'
        'ILSVRC' -> 'ImageNet'
    """
    if not name or not isinstance(name, str):
        return ""
    clean = name.strip()
    key = clean.lower()
    return DATASET_ALIAS_MAP.get(key, clean)


def classify_methodology(item: dict[str, Any]) -> str:
    """
    Classifies an extracted methodology item into one of three categories:
    - 'proposed_method': Novel contribution of the paper.
    - 'related_work_method': Prior work, baseline, or literature comparison.
    - 'experimental_setup': Hyperparameters, training setup, or baseline ablation.

    Preserves all original evidence and metadata without deletion.
    """
    evidence = item.get("evidence", "") or ""
    method = item.get("method", "") or ""
    section = (item.get("section") or "").upper()
    combined_text = f"{method} {evidence}"

    # 1. Check strong proposed cues first
    has_proposed_cue = bool(PROPOSED_METHOD_CUES.search(combined_text))

    # 2. Section: RELATED_WORK
    if section == "RELATED_WORK":
        if has_proposed_cue and not RELATED_WORK_CUES.search(combined_text):
            return "proposed_method"
        return "related_work_method"

    # 3. Related work cues in any section
    if RELATED_WORK_CUES.search(combined_text) and not has_proposed_cue:
        return "related_work_method"

    # 4. Experimental / Evaluation section
    if section in ("EXPERIMENTS", "EVALUATION", "RESULTS"):
        if EXPERIMENTAL_SETUP_CUES.search(combined_text):
            return "experimental_setup"
        if has_proposed_cue:
            return "proposed_method"
        return "experimental_setup"

    # 5. Methodology / Introduction / Abstract default to proposed
    if section in ("METHODOLOGY", "INTRODUCTION", "ABSTRACT", "CONCLUSION"):
        return "proposed_method"

    if has_proposed_cue:
        return "proposed_method"

    return "proposed_method"


class EnhancedVectorStore(VectorStore):
    """
    Non-invasive extension of Member 2's VectorStore.
    Preserves extended metadata (section, chunk_type, dimension, provenance,
    source_type, confidence) in ChromaDB while maintaining 100% backward compatibility.
    """

    def add_documents(self, chunks: list[dict[str, Any]], embeddings: Any) -> None:
        """
        Stores chunks and dense embeddings into ChromaDB with extended metadata.
        """
        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for chunk in chunks:
            ids.append(str(chunk["chunk_id"]))
            documents.append(str(chunk["text"]))

            # ChromaDB requires primitive types (str, int, float, bool)
            raw_page = chunk.get("page_number")
            page_int = int(raw_page) if raw_page is not None and int(raw_page) > 0 else 0

            raw_conf = chunk.get("confidence")
            conf_float = float(raw_conf) if raw_conf is not None else 1.0

            metadatas.append({
                "paper_id": str(chunk["paper_id"]),
                "paper_title": str(chunk.get("paper_title", "")),
                "page_number": page_int,
                "section": str(chunk.get("section", "FULL_TEXT")),
                "chunk_type": str(chunk.get("chunk_type", "body_passage")),
                "dimension": str(chunk.get("dimension", "body")),
                "provenance": str(chunk.get("provenance", "unknown")),
                "source_type": str(chunk.get("source_type", "unknown")),
                "confidence": conf_float,
            })

        # Upsert into ChromaDB collection
        self.collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings,
            metadatas=metadatas,
        )


class PaperIngestionAdapter:
    """
    Adapts Member 1's research paper records and NLP analysis outputs into
    Member 2's chunk format with full page-awareness, section-awareness,
    and structured NLP evidence retention.
    """

    def __init__(self) -> None:
        self.preprocessor = AcademicTextPreprocessor()
        self.segmenter = SectionSegmenter()

    def adapt_paper(
        self,
        paper_record: dict[str, Any],
        nlp_analysis: dict[str, Any] | None = None,
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Main adapter entry point. Converts any Member 1 paper record (full-text or
        abstract-only) and optional NLP analysis into standardized chunks.
        """
        if not paper_record or not isinstance(paper_record, dict):
            raise ValueError("paper_record must be a non-empty dictionary.")

        paper_id = str(paper_record.get("paper_id") or "unknown_paper")
        paper_title = str(paper_record.get("title") or paper_record.get("paper_title") or "Untitled Paper")
        source_type = str(paper_record.get("source_type") or "abstract_only")

        chunks: list[dict[str, Any]] = []

        # 1. Generate Body Chunks
        if source_type in ("open_access_full_text", "open_access_pdf") and paper_record.get("pages"):
            body_chunks = self.create_page_aware_chunks(
                pages=paper_record["pages"],
                paper_id=paper_id,
                paper_title=paper_title,
                source_type=source_type,
                chunk_size=chunk_size,
                overlap=overlap,
            )
            chunks.extend(body_chunks)
        else:
            # Abstract-only fallback
            abstract_text = str(paper_record.get("abstract") or paper_record.get("full_text") or "").strip()
            if abstract_text:
                abstract_chunks = self.create_abstract_chunks(
                    abstract_text=abstract_text,
                    paper_id=paper_id,
                    paper_title=paper_title,
                    source_type="abstract_only",
                    chunk_size=chunk_size,
                    overlap=overlap,
                )
                chunks.extend(abstract_chunks)

        # 2. Generate Separately Identifiable Structured NLP Fact Chunks
        if nlp_analysis and isinstance(nlp_analysis, dict):
            fact_chunks = self.create_nlp_fact_chunks(
                nlp_analysis=nlp_analysis,
                paper_id=paper_id,
                paper_title=paper_title,
                source_type=source_type,
            )
            chunks.extend(fact_chunks)

        return chunks

    def create_page_aware_chunks(
        self,
        pages: list[dict[str, Any]],
        paper_id: str,
        paper_title: str,
        source_type: str = "open_access_full_text",
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Generates page-aware and section-aware body chunks from multi-page records.
        Sentence groupings never cross page boundaries, preserving exact page provenance.
        """
        dummy_record = {"source_type": "open_access_full_text", "pages": pages}
        sentences = self.preprocessor.process_paper_record(dummy_record)
        tagged_sentences = self.segmenter.assign_sections_to_sentences(sentences)

        chunks: list[dict[str, Any]] = []
        if not tagged_sentences:
            return chunks

        # Group sentences by page_number
        current_page = None
        current_page_sentences: list[dict[str, Any]] = []
        pages_groups: list[list[dict[str, Any]]] = []

        for s in tagged_sentences:
            p_num = s.get("page_number")
            if p_num != current_page and current_page_sentences:
                pages_groups.append(current_page_sentences)
                current_page_sentences = []
            current_page = p_num
            current_page_sentences.append(s)
        if current_page_sentences:
            pages_groups.append(current_page_sentences)

        for page_sentences in pages_groups:
            p_num = page_sentences[0].get("page_number")
            page_int = int(p_num) if p_num is not None and int(p_num) > 0 else 1
            prov = page_sentences[0].get("provenance") or f"page_{page_int}"

            current_sentences: list[str] = []
            current_section = page_sentences[0].get("section", "INTRODUCTION")
            chunk_num = 1

            for s in page_sentences:
                sent_text = s.get("text", "").strip()
                if not sent_text:
                    continue

                candidate = " ".join(current_sentences + [sent_text])
                if current_sentences and len(candidate) > chunk_size:
                    chunk_text = " ".join(current_sentences)
                    chunk_id = f"{paper_id}_p{page_int}_c{chunk_num}"
                    chunks.append({
                        "chunk_id": chunk_id,
                        "paper_id": paper_id,
                        "paper_title": paper_title,
                        "page_number": page_int,
                        "section": current_section,
                        "chunk_type": "body_passage",
                        "dimension": "body",
                        "provenance": prov,
                        "source_type": source_type,
                        "confidence": 1.0,
                        "text": chunk_text,
                    })
                    chunk_num += 1

                    # Sliding sentence overlap within the same page
                    overlap_sentences: list[str] = []
                    overlap_len = 0
                    for prev_sent in reversed(current_sentences):
                        req_len = len(prev_sent) + (1 if overlap_sentences else 0)
                        if overlap_len + req_len <= overlap:
                            overlap_sentences.insert(0, prev_sent)
                            overlap_len += req_len
                        else:
                            break
                    current_sentences = overlap_sentences

                current_sentences.append(sent_text)
                if s.get("section"):
                    current_section = s["section"]

            if current_sentences:
                chunk_text = " ".join(current_sentences)
                chunk_id = f"{paper_id}_p{page_int}_c{chunk_num}"
                chunks.append({
                    "chunk_id": chunk_id,
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "page_number": page_int,
                    "section": current_section,
                    "chunk_type": "body_passage",
                    "dimension": "body",
                    "provenance": prov,
                    "source_type": source_type,
                    "confidence": 1.0,
                    "text": chunk_text,
                })

        return chunks

    def create_abstract_chunks(
        self,
        abstract_text: str,
        paper_id: str,
        paper_title: str,
        source_type: str = "abstract_only",
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Generates chunks for abstract-only papers. Uses ChromaDB sentinel 0 for page_number.
        """
        dummy_record = {"source_type": "abstract_only", "abstract": abstract_text}
        sentences = self.preprocessor.process_paper_record(dummy_record)
        tagged_sentences = self.segmenter.assign_sections_to_sentences(sentences)

        chunks: list[dict[str, Any]] = []
        if not tagged_sentences:
            return chunks

        current_sentences: list[str] = []
        chunk_num = 1

        for s in tagged_sentences:
            sent_text = s.get("text", "").strip()
            if not sent_text:
                continue

            candidate = " ".join(current_sentences + [sent_text])
            if current_sentences and len(candidate) > chunk_size:
                chunk_text = " ".join(current_sentences)
                chunks.append({
                    "chunk_id": f"{paper_id}_abstract_c{chunk_num}",
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "page_number": 0,  # Sentinel 0 for abstract
                    "section": "ABSTRACT",
                    "chunk_type": "abstract_passage",
                    "dimension": "abstract",
                    "provenance": "abstract",
                    "source_type": source_type,
                    "confidence": 1.0,
                    "text": chunk_text,
                })
                chunk_num += 1
                current_sentences = []

            current_sentences.append(sent_text)

        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunks.append({
                "chunk_id": f"{paper_id}_abstract_c{chunk_num}",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": 0,
                "section": "ABSTRACT",
                "chunk_type": "abstract_passage",
                "dimension": "abstract",
                "provenance": "abstract",
                "source_type": source_type,
                "confidence": 1.0,
                "text": chunk_text,
            })

        return chunks

    def create_nlp_fact_chunks(
        self,
        nlp_analysis: dict[str, Any],
        paper_id: str,
        paper_title: str,
        source_type: str = "open_access_full_text",
    ) -> list[dict[str, Any]]:
        """
        Transforms Member 1's structured NLP dimensions into separately identifiable
        high-density semantic chunks. Preserves evidence sentences, page provenance,
        section, and confidence scores.
        """
        fact_chunks: list[dict[str, Any]] = []

        # 1. Research Objectives Chunk
        objectives = nlp_analysis.get("research_objectives", [])
        if objectives:
            lines = [f"[RESEARCH OBJECTIVES] Paper: {paper_title}"]
            primary_page = 0
            primary_sec = "INTRODUCTION"
            primary_prov = "full_text"
            for obj in objectives:
                p_num = obj.get("page_number") or 0
                if p_num > 0 and primary_page == 0:
                    primary_page = p_num
                    primary_sec = obj.get("section", "INTRODUCTION")
                    primary_prov = obj.get("provenance", f"page_{p_num}")
                stmt = obj.get("statement", "")
                evid = obj.get("evidence", "")
                conf = obj.get("confidence", 0.8)
                lines.append(f"- Objective: {stmt}")
                lines.append(f"  Evidence: \"{evid}\" [Page {p_num if p_num > 0 else 'Abstract'}, Section: {obj.get('section', 'INTRODUCTION')}, Confidence: {conf}]")

            fact_chunks.append({
                "chunk_id": f"{paper_id}_nlp_objectives",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": primary_page,
                "section": primary_sec,
                "chunk_type": "nlp_fact",
                "dimension": "objectives",
                "provenance": primary_prov,
                "source_type": source_type,
                "confidence": 0.9,
                "text": "\n".join(lines),
            })

        # 2. Research Methodologies Chunk (with attribution classification)
        methodologies = nlp_analysis.get("research_methodologies", [])
        if methodologies:
            proposed_lines = []
            related_lines = []
            setup_lines = []
            primary_page = 0

            for meth in methodologies:
                p_num = meth.get("page_number") or 0
                if p_num > 0 and primary_page == 0:
                    primary_page = p_num

                # Classify attribution while preserving evidence
                attr = classify_methodology(meth)
                meth["attribution"] = attr
                m_text = meth.get("method", "")
                evid = meth.get("evidence", "")
                conf = meth.get("confidence", 0.8)
                sec = meth.get("section", "METHODOLOGY")

                formatted = (
                    f"- Method: {m_text}\n"
                    f"  Evidence: \"{evid}\" [Page {p_num if p_num > 0 else 'Abstract'}, Section: {sec}, Attribution: {attr}, Confidence: {conf}]"
                )

                if attr == "proposed_method":
                    proposed_lines.append(formatted)
                elif attr == "related_work_method":
                    related_lines.append(formatted)
                else:
                    setup_lines.append(formatted)

            lines = [f"[RESEARCH METHODOLOGIES] Paper: {paper_title}"]
            if proposed_lines:
                lines.append("\nProposed Contributions:")
                lines.extend(proposed_lines)
            if related_lines:
                lines.append("\nRelated Work & Prior Literature:")
                lines.extend(related_lines)
            if setup_lines:
                lines.append("\nExperimental Setup & Baselines:")
                lines.extend(setup_lines)

            fact_chunks.append({
                "chunk_id": f"{paper_id}_nlp_methodologies",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": primary_page if primary_page > 0 else 0,
                "section": "METHODOLOGY",
                "chunk_type": "nlp_fact",
                "dimension": "methodologies",
                "provenance": f"page_{primary_page}" if primary_page > 0 else "abstract",
                "source_type": source_type,
                "confidence": 0.85,
                "text": "\n".join(lines),
            })

        # 3. Datasets Chunk (with normalized aliases)
        datasets = nlp_analysis.get("datasets", [])
        if datasets:
            lines = [f"[DATASETS & BENCHMARKS] Paper: {paper_title}"]
            primary_page = 0
            for d in datasets:
                orig_name = d.get("name", "")
                norm_name = normalize_dataset_name(orig_name)
                d["normalized_name"] = norm_name
                p_num = d.get("page_number") or 0
                if p_num > 0 and primary_page == 0:
                    primary_page = p_num
                evid = d.get("evidence", "")
                sec = d.get("section", "EXPERIMENTS")
                conf = d.get("confidence", 0.9)
                lines.append(
                    f"- Dataset: {orig_name} (Normalized: {norm_name})\n"
                    f"  Evidence: \"{evid}\" [Page {p_num if p_num > 0 else 'Abstract'}, Section: {sec}, Confidence: {conf}]"
                )

            fact_chunks.append({
                "chunk_id": f"{paper_id}_nlp_datasets",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": primary_page,
                "section": "DATASETS",
                "chunk_type": "nlp_fact",
                "dimension": "datasets",
                "provenance": f"page_{primary_page}" if primary_page > 0 else "abstract",
                "source_type": source_type,
                "confidence": 0.95,
                "text": "\n".join(lines),
            })

        # 4. Evaluation Metrics Chunk
        metrics = nlp_analysis.get("evaluation_metrics", [])
        if metrics:
            lines = [f"[EVALUATION METRICS & RESULTS] Paper: {paper_title}"]
            primary_page = 0
            for m in metrics:
                m_name = m.get("metric", "")
                val = m.get("value")
                val_str = f", Value: {val}" if val else ""
                p_num = m.get("page_number") or 0
                if p_num > 0 and primary_page == 0:
                    primary_page = p_num
                evid = m.get("evidence", "")
                sec = m.get("section", "RESULTS")
                conf = m.get("confidence", 0.85)
                lines.append(
                    f"- Metric: {m_name}{val_str}\n"
                    f"  Evidence: \"{evid}\" [Page {p_num if p_num > 0 else 'Abstract'}, Section: {sec}, Confidence: {conf}]"
                )

            fact_chunks.append({
                "chunk_id": f"{paper_id}_nlp_metrics",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": primary_page,
                "section": "RESULTS",
                "chunk_type": "nlp_fact",
                "dimension": "evaluation_metrics",
                "provenance": f"page_{primary_page}" if primary_page > 0 else "abstract",
                "source_type": source_type,
                "confidence": 0.9,
                "text": "\n".join(lines),
            })

        # 5. Research Findings Chunk
        findings = nlp_analysis.get("research_findings", [])
        if findings:
            lines = [f"[RESEARCH FINDINGS] Paper: {paper_title}"]
            primary_page = 0
            for f in findings:
                finding_text = f.get("finding", "")
                p_num = f.get("page_number") or 0
                if p_num > 0 and primary_page == 0:
                    primary_page = p_num
                evid = f.get("evidence", "")
                sec = f.get("section", "CONCLUSION")
                conf = f.get("confidence", 0.8)
                lines.append(
                    f"- Finding: {finding_text}\n"
                    f"  Evidence: \"{evid}\" [Page {p_num if p_num > 0 else 'Abstract'}, Section: {sec}, Confidence: {conf}]"
                )

            fact_chunks.append({
                "chunk_id": f"{paper_id}_nlp_findings",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": primary_page,
                "section": "CONCLUSION",
                "chunk_type": "nlp_fact",
                "dimension": "findings",
                "provenance": f"page_{primary_page}" if primary_page > 0 else "abstract",
                "source_type": source_type,
                "confidence": 0.85,
                "text": "\n".join(lines),
            })

        # 6. Research Limitations Chunk
        limitations = nlp_analysis.get("research_limitations", [])
        if limitations:
            lines = [f"[RESEARCH LIMITATIONS] Paper: {paper_title}"]
            primary_page = 0
            for lim in limitations:
                lim_text = lim.get("limitation", "")
                p_num = lim.get("page_number") or 0
                if p_num > 0 and primary_page == 0:
                    primary_page = p_num
                evid = lim.get("evidence", "")
                sec = lim.get("section", "DISCUSSION")
                conf = lim.get("confidence", 0.8)
                lines.append(
                    f"- Limitation: {lim_text}\n"
                    f"  Evidence: \"{evid}\" [Page {p_num if p_num > 0 else 'Abstract'}, Section: {sec}, Confidence: {conf}]"
                )

            fact_chunks.append({
                "chunk_id": f"{paper_id}_nlp_limitations",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": primary_page,
                "section": "DISCUSSION",
                "chunk_type": "nlp_fact",
                "dimension": "limitations",
                "provenance": f"page_{primary_page}" if primary_page > 0 else "abstract",
                "source_type": source_type,
                "confidence": 0.8,
                "text": "\n".join(lines),
            })

        # 7. Keywords and Concepts Chunk
        keywords = nlp_analysis.get("keywords_and_concepts", [])
        if keywords:
            kw_terms = [k.get("term", "") for k in keywords if k.get("term")]
            if kw_terms:
                kw_str = ", ".join(kw_terms)
                fact_chunks.append({
                    "chunk_id": f"{paper_id}_nlp_keywords",
                    "paper_id": paper_id,
                    "paper_title": paper_title,
                    "page_number": 0,
                    "section": "KEYWORDS",
                    "chunk_type": "nlp_fact",
                    "dimension": "keywords",
                    "provenance": "nlp_extraction",
                    "source_type": source_type,
                    "confidence": 0.9,
                    "text": f"[DOMAIN KEYWORDS & CONCEPTS] Paper: {paper_title}\nKeywords: {kw_str}",
                })

        return fact_chunks

    def adapt_legacy_paper(
        self,
        legacy_paper: dict[str, Any],
        chunk_size: int = 500,
        overlap: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Adapts Member 2's sample_data paper dictionary into chunks compatible
        with the unified pipeline, preserving chunk_id format f'{paper_id}_chunk_{N}'
        for backward compatibility with Member 2 tests.
        """
        from rag_engine.chunking import create_chunks

        raw_chunks = create_chunks(
            text=legacy_paper["text"],
            paper_id=legacy_paper["paper_id"],
            paper_title=legacy_paper["paper_title"],
            page_number=1,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        adapted: list[dict[str, Any]] = []
        for c in raw_chunks:
            adapted.append({
                "chunk_id": c["chunk_id"],
                "paper_id": c["paper_id"],
                "paper_title": c["paper_title"],
                "page_number": 1,
                "section": "FULL_TEXT",
                "chunk_type": "body_passage",
                "dimension": "body",
                "provenance": legacy_paper.get("source", "sample_data"),
                "source_type": "legacy_sample",
                "confidence": 1.0,
                "text": c["text"],
            })

        return adapted
