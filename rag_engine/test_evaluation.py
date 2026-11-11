from rag_engine.evaluation import (
    precision_at_k,
    recall_at_k,
    mean_reciprocal_rank
)

# Simulated retrieval results
retrieved_ids = [
    "chunk_001",
    "chunk_002",
    "chunk_003",
    "chunk_004",
    "chunk_005"
]

# Chunks we know are relevant to the research question
relevant_ids = [
    "chunk_002",
    "chunk_004",
    "chunk_006"
]

k = 3

precision = precision_at_k(retrieved_ids, relevant_ids, k)
recall = recall_at_k(retrieved_ids, relevant_ids, k)
mrr = mean_reciprocal_rank(retrieved_ids, relevant_ids)

print("\n----- RETRIEVAL EVALUATION -----")
print("Precision@3:", round(precision, 4))
print("Recall@3:", round(recall, 4))
print("MRR:", round(mrr, 4))