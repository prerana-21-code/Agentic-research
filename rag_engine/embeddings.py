
from sentence_transformers import SentenceTransformer


class EmbeddingGenerator:

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ):
        """Load the sentence embedding model."""

        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts):
        """Convert multiple text chunks into embeddings."""

        if not texts:
            return []

        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embeddings

    def generate_single_embedding(self, text):
        """Convert one text passage into an embedding."""

        if not isinstance(text, str) or not text.strip():
            raise ValueError("Text cannot be empty.")

        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True
        )

        return embedding
