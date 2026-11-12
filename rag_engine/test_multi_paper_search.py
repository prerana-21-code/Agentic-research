
from rag_engine.vector_store import VectorStore
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.semantic_search import SemanticSearch

store = VectorStore()
generator = EmbeddingGenerator()

search_engine = SemanticSearch(store, generator)

questions = [
    "How are CNNs used to detect diseases in MRI images?",
    "How do Vision Transformers analyse medical images?",
    "What techniques are used for brain tumour detection?",
    "Which machine learning algorithms predict disease risk?",
    "How is NLP used to analyse biomedical research papers?"
]

for query in questions:
    print("\n" + "=" * 65)
    print("RESEARCH QUESTION:", query)
    print("=" * 65)

    results = search_engine.search(query, top_k=3)

    for i in range(len(results["ids"][0])):
        print(f"\nResult {i + 1}")
        print("Chunk ID:", results["ids"][0][i])
        print("Paper:", results["metadatas"][0][i]["paper_title"])
        print("Text:", results["documents"][0][i])
        print("Distance:", round(results["distances"][0][i], 4))
