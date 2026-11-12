
from rag_engine.paper_loader import load_papers
from rag_engine.chunking import create_chunks
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore
from rag_engine.semantic_search import SemanticSearch
from rag_engine.keyword_search import KeywordSearch
from rag_engine.hybrid_search import HybridSearch

# 1. Load all papers
papers = load_papers()

# 2. Generate chunks
all_chunks = []

for paper in papers:
    chunks = create_chunks(
        text=paper["text"],
        paper_id=paper["paper_id"],
        paper_title=paper["paper_title"],
        page_number=1,
        chunk_size=500,
        overlap=100
    )
    all_chunks.extend(chunks)

# 3. Prepare embeddings
generator = EmbeddingGenerator()
texts = [chunk["text"] for chunk in all_chunks]
embeddings = generator.generate_embeddings(texts)

# 4. Refresh the sample paper records in ChromaDB
store = VectorStore()

store.collection.delete(
    where={
        "paper_id": {
            "$in": [paper["paper_id"] for paper in papers]
        }
    }
)

store.add_documents(all_chunks, embeddings)

# 5. Initialize both retrieval systems
semantic_engine = SemanticSearch(store, generator)
keyword_engine = KeywordSearch(all_chunks)

# 6. Initialize hybrid search
hybrid_engine = HybridSearch(
    semantic_engine,
    keyword_engine
)

# 7. Research questions
questions = [
    "How are CNNs used to detect diseases in MRI images?",
    "How do Vision Transformers analyse medical images?",
    "What techniques are used for brain tumour detection?",
    "Which machine learning algorithms predict disease risk?",
    "How is NLP used to analyse biomedical research papers?"
]

# 8. Perform hybrid retrieval
for query in questions:
    print("\n" + "=" * 65)
    print("RESEARCH QUESTION:", query)
    print("=" * 65)

    results = hybrid_engine.search(query, top_k=3)

    for rank, result in enumerate(results, start=1):
        print(f"\nResult {rank}")
        print("Chunk ID:", result["chunk_id"])
        print("Paper:", result["metadata"]["paper_title"])
        print("RRF Score:", round(result["rrf_score"], 6))
        print("Text:", result["text"])
