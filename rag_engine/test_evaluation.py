
from rag_engine.paper_loader import load_papers
from rag_engine.chunking import create_chunks
from rag_engine.embeddings import EmbeddingGenerator
from rag_engine.vector_store import VectorStore
from rag_engine.semantic_search import SemanticSearch
from rag_engine.keyword_search import KeywordSearch
from rag_engine.hybrid_search import HybridSearch

from rag_engine.evaluation import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank
)

# 1. Load papers and generate chunks
papers = load_papers()
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

# 2. Generate embeddings
generator = EmbeddingGenerator()
texts = [chunk["text"] for chunk in all_chunks]
embeddings = generator.generate_embeddings(texts)

# 3. Refresh ChromaDB
store = VectorStore()

store.collection.delete(
    where={
        "paper_id": {
            "$in": [paper["paper_id"] for paper in papers]
        }
    }
)

store.add_documents(all_chunks, embeddings)

# 4. Initialize retrieval systems
semantic_engine = SemanticSearch(store, generator)
keyword_engine = KeywordSearch(all_chunks)

hybrid_engine = HybridSearch(
    semantic_engine,
    keyword_engine
)

# 5. Define evaluation questions and relevant chunks
evaluation_data = [
    {
        "question": "How are CNNs used to detect diseases in MRI images?",
        "relevant_ids": ["paper_001_chunk_1", "paper_003_chunk_1"]
    },
    {
        "question": "How do Vision Transformers analyse medical images?",
        "relevant_ids": ["paper_002_chunk_1", "paper_002_chunk_2"]
    },
    {
        "question": "What techniques are used for brain tumour detection?",
        "relevant_ids": ["paper_003_chunk_1", "paper_003_chunk_2"]
    },
    {
        "question": "Which machine learning algorithms predict disease risk?",
        "relevant_ids": ["paper_004_chunk_1", "paper_004_chunk_2"]
    },
    {
        "question": "How is NLP used to analyse biomedical research papers?",
        "relevant_ids": ["paper_005_chunk_1", "paper_005_chunk_2"]
    }
]

# 6. Evaluate each retrieval method
retrieval_methods = {
    "Semantic Search": semantic_engine,
    "BM25 Search": keyword_engine,
    "Hybrid Search": hybrid_engine
}

k = 3

for method_name, engine in retrieval_methods.items():

    precision_scores = []
    recall_scores = []
    mrr_scores = []

    print("\n" + "=" * 65)
    print("EVALUATION:", method_name)
    print("=" * 65)

    for item in evaluation_data:

        query = item["question"]
        relevant_ids = item["relevant_ids"]

        if method_name == "Semantic Search":
            results = engine.search(query, top_k=k)
            retrieved_ids = results["ids"][0]

        elif method_name == "BM25 Search":
            results = engine.search(query, top_k=k)
            retrieved_ids = [result["chunk_id"] for result in results]

        else:
            results = engine.search(query, top_k=k)
            retrieved_ids = [result["chunk_id"] for result in results]

        precision = precision_at_k(
            retrieved_ids, relevant_ids, k
        )

        recall = recall_at_k(
            retrieved_ids, relevant_ids, k
        )

        mrr = mean_reciprocal_rank(
            retrieved_ids, relevant_ids
        )

        precision_scores.append(precision)
        recall_scores.append(recall)
        mrr_scores.append(mrr)

        print("\nQuestion:", query)
        print("Retrieved:", retrieved_ids)
        print("Precision@3:", round(precision, 4))
        print("Recall@3:", round(recall, 4))
        print("MRR:", round(mrr, 4))

    print("\n----- AVERAGE METRICS -----")
    print("Average Precision@3:",
          round(sum(precision_scores) / len(precision_scores), 4))
    print("Average Recall@3:",
          round(sum(recall_scores) / len(recall_scores), 4))
    print("Average MRR:",
          round(sum(mrr_scores) / len(mrr_scores), 4))
