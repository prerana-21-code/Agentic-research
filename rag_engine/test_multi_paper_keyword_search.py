
from rag_engine.paper_loader import load_papers
from rag_engine.chunking import create_chunks
from rag_engine.keyword_search import KeywordSearch

# Load all five papers
papers = load_papers()

# Generate chunks from all papers
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

# Initialize BM25 using all chunks
keyword_engine = KeywordSearch(all_chunks)

# Research questions
questions = [
    "CNN disease detection MRI images",
    "Vision Transformers medical image analysis",
    "Brain tumour detection MRI",
    "Machine learning algorithms disease prediction",
    "NLP biomedical research"
]

# Search across all papers
for query in questions:
    print("\n" + "=" * 60)
    print("RESEARCH QUESTION:", query)
    print("=" * 60)

    results = keyword_engine.search(query, top_k=3)

    for rank, result in enumerate(results, start=1):
        print(f"\nResult {rank}")
        print("Chunk ID:", result["chunk_id"])
        print("Paper:", result["metadata"]["paper_title"])
        print("BM25 Score:", round(result["score"], 4))
        print("Text:", result["text"])
