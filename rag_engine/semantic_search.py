class SemanticSearch:

    def __init__(self, vector_store, embedding_generator):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator

    def search(self, query, top_k=3):

        # Convert the research question into an embedding
        query_embedding = self.embedding_generator.generate_single_embedding(
            query
        )

        # Search ChromaDB
        results = self.vector_store.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        return results