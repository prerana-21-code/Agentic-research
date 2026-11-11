from rag_engine.chunking import create_chunks
from rag_engine.keyword_search import KeywordSearch


# Step 1: Sample research paper text
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


# Step 3: Initialize BM25 search
keyword_engine = KeywordSearch(chunks)


# Step 4: Enter research question
query = "CNN models detect diseases"


# Step 5: Search using BM25
results = keyword_engine.search(query, top_k=3)


# Step 6: Display results
print("\nRESEARCH QUESTION:", query)
print("\n----- BM25 SEARCH RESULTS -----")

for i, result in enumerate(results):

    print(f"\nResult {i + 1}")
    print("Chunk ID:", result["chunk_id"])
    print("Research text:", result["text"])
    print("BM25 Score:", result["score"])