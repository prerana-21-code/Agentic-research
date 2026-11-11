from rag_engine.vector_store import VectorStore
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.semantic_search import SemanticSearch


# Step 1: Connect to existing ChromaDB
store = VectorStore()

# Step 2: Load embedding model
generator = EmbeddingGenerator()

# Step 3: Initialize semantic search
search_engine = SemanticSearch(store, generator)

# Step 4: Ask a research question
query = "What AI techniques are used to detect diseases from medical images?"

# Step 5: Retrieve the top 3 relevant chunks
results = search_engine.search(query, top_k=3)

# Step 6: Display results
print("\nRESEARCH QUESTION:", query)
print("\n----- SEARCH RESULTS -----")

for i in range(len(results["ids"][0])):

    print(f"\nResult {i + 1}")
    print("Chunk ID:", results["ids"][0][i])
    print("Research text:", results["documents"][0][i])
    print("Metadata:", results["metadatas"][0][i])
    print("Distance:", results["distances"][0][i])