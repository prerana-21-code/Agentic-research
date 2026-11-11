from rag_engine.chunking import create_chunks
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore


# Step 1: Sample research paper text
research_text = """
Deep learning is widely used in medical image analysis.
Convolutional neural networks help detect diseases
from X-ray images and MRI scans.
Machine learning models can improve disease classification.
"""


# Step 2: Split the text into chunks
chunks = create_chunks(
    text=research_text,
    paper_id="paper_001",
    paper_title="Deep Learning in Medical Image Analysis",
    page_number=1,
    chunk_size=100,
    overlap=20
)


# Step 3: Generate embeddings
generator = EmbeddingGenerator()

texts = [chunk["text"] for chunk in chunks]

embeddings = generator.generate_embeddings(texts)


# Step 4: Connect to ChromaDB
store = VectorStore()

store.collection.delete(
    where={"paper_id": "paper_001"}
)

# Step 5: Store chunks and embeddings
store.add_documents(chunks, embeddings)


# Step 6: Verify stored records
print("\nTotal records in ChromaDB:",
      store.collection.count())