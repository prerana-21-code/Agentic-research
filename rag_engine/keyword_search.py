from rank_bm25 import BM25Okapi


class KeywordSearch:

    def __init__(self, chunks):

        self.chunks = chunks

        # Extract text from each chunk
        self.documents = [
            chunk["text"] for chunk in chunks
        ]

        # Convert documents into tokens
        self.tokenized_documents = [
            document.lower().split()
            for document in self.documents
        ]

        # Create BM25 index
        self.bm25 = BM25Okapi(self.tokenized_documents)

    def search(self, query, top_k=3):

        # Tokenize research question
        tokenized_query = query.lower().split()

        # Calculate BM25 scores
        scores = self.bm25.get_scores(tokenized_query)

        # Sort documents by score
        ranked_indices = scores.argsort()[::-1][:top_k]

        results = []

        for index in ranked_indices:

            results.append({
                "chunk_id": self.chunks[index]["chunk_id"],
                "text": self.chunks[index]["text"],
                "metadata": self.chunks[index],
                "score": float(scores[index])
            })

        return results