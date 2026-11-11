def precision_at_k(retrieved_ids, relevant_ids, k):
    if k <= 0:
        raise ValueError("k must be positive.")

    if not relevant_ids:
        raise ValueError("Relevant IDs cannot be empty.")

    top_k = retrieved_ids[:k]

    relevant_count = sum(
        1 for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_count / k


def recall_at_k(retrieved_ids, relevant_ids, k):
    if k <= 0:
        raise ValueError("k must be positive.")

    if not relevant_ids:
        raise ValueError("Relevant IDs cannot be empty.")

    top_k = retrieved_ids[:k]

    relevant_count = sum(
        1 for chunk_id in top_k
        if chunk_id in relevant_ids
    )

    return relevant_count / len(relevant_ids)


def mean_reciprocal_rank(retrieved_ids, relevant_ids):
    if not relevant_ids:
        raise ValueError("Relevant IDs cannot be empty.")

    for rank, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in relevant_ids:
            return 1 / rank

    return 0.0