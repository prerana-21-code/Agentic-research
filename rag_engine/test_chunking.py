
from rag_engine.chunking import create_chunks


research_text = """
Deep learning is widely used in medical image analysis.
Convolutional neural networks help detect diseases from X-ray images.
Machine learning models can improve disease classification.
Natural language processing helps analyse research papers.
"""


chunks = create_chunks(
    text=research_text,
    paper_id="paper_001",
    paper_title="Deep Learning in Medical Image Analysis",
    page_number=1,
    chunk_size=120,
    overlap=75
)


print("\n----- SENTENCE-AWARE CHUNKING RESULTS -----")

for chunk in chunks:
    print("\nChunk ID:", chunk["chunk_id"])
    print("Text:", chunk["text"])
    print("Character count:", len(chunk["text"]))
    print("Paper ID:", chunk["paper_id"])
