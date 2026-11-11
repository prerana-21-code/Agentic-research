class HybridSearch:

    def __init__(self, semantic_search, keyword_search):
        self.semantic_search = semantic_search
        self.keyword_search = keyword_search

    def search(self, query, top_k=3, k=60):

        # Step 1: Get semantic search results
        semantic_results = self.semantic_search.search(
            query, top_k=top_k
        )

        # Step 2: Get BM25 search results
        keyword_results = self.keyword_search.search(
            query, top_k=top_k
        )

        # Step 3: Store combined scores
        fused_results = {}

        # Step 4: Process semantic rankings
        for rank, chunk_id in enumerate(
            semantic_results["ids"][0], start=1
        ):

            fused_results[chunk_id] = {
                "chunk_id": chunk_id,
                "text": semantic_results["documents"][0][rank - 1],
                "metadata": semantic_results["metadatas"][0][rank - 1],
                "rrf_score": 1 / (k + rank)
            }

        # Step 5: Add BM25 ranking contributions
        for rank, result in enumerate(keyword_results, start=1):

            chunk_id = result["chunk_id"]

            if chunk_id not in fused_results:
                fused_results[chunk_id] = {
                    "chunk_id": chunk_id,
                    "text": result["text"],
                    "metadata": result["metadata"],
                    "rrf_score": 0
                }

            fused_results[chunk_id]["rrf_score"] += 1 / (k + rank)

        # Step 6: Sort by combined RRF score
        ranked_results = sorted(
            fused_results.values(),
            key=lambda item: item["rrf_score"],
            reverse=True
        )

        return ranked_results[:top_k]