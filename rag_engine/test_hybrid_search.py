from rag_engine.chunking import create_chunks
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore
from rag_engine.semantic_search import SemanticSearch
from rag_engine.keyword_search import KeywordSearch
from rag_engine.hybrid_search import HybridSearch


# Step 1: Sample research paper
research_text = """
Deep learning is widely used in medical image analysis.
Convolutional neural networks help detect diseases
from X-ray images and MRI scans.
Machine learning models can improve disease classification.
"""


# Step 2: Create chunks
chunks = create_chunks(
    text=research_text,
    paper_id="paper_001",
    paper_title="Deep Learning in Medical Image Analysis",
    page_number=1,
    chunk_size=100,
    overlap=20
)


# Step 3: Initialize embedding generator
generator = EmbeddingGenerator()


# Step 4: Initialize ChromaDB
store = VectorStore()


# Step 5: Initialize semantic search
semantic_engine = SemanticSearch(store, generator)


# Step 6: Initialize BM25 search
keyword_engine = KeywordSearch(chunks)


# Step 7: Combine both search engines
hybrid_engine = HybridSearch(
    semantic_engine,
    keyword_engine
)


# Step 8: Research question
query = "What AI techniques are used to detect diseases from medical images?"


# Step 9: Perform hybrid search
results = hybrid_engine.search(query, top_k=3)


# Step 10: Display final results
print("\nRESEARCH QUESTION:", query)
print("\n----- HYBRID SEARCH RESULTS -----")

for i, result in enumerate(results):

    print(f"\nResult {i + 1}")
    print("Chunk ID:", result["chunk_id"])
    print("Research text:", result["text"])
    print("RRF Score:", round(result["rrf_score"], 6))
    print("Metadata:", result["metadata"])