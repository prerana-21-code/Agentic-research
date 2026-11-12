
from rag_engine.paper_loader import load_papers
from rag_engine.chunking import create_chunks
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore

# 1. Load all five papers
papers = load_papers()

# 2. Generate chunks from every paper
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

print("Total papers:", len(papers))
print("Total chunks:", len(all_chunks))

# 3. Generate embeddings for all chunks
generator = EmbeddingGenerator()

texts = [chunk["text"] for chunk in all_chunks]

embeddings = generator.generate_embeddings(texts)

print("\nEmbedding shape:", embeddings.shape)

# 4. Connect to ChromaDB
store = VectorStore()

# Remove old sample records for these five papers
store.collection.delete(
    where={
        "paper_id": {
            "$in": [paper["paper_id"] for paper in papers]
        }
    }
)

# 5. Store the new chunks and embeddings
store.add_documents(all_chunks, embeddings)

print("\n----- MULTI-PAPER STORAGE RESULTS -----")
print("Total records in ChromaDB:", store.collection.count())
