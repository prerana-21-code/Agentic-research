
from rag_engine.embeddings import EmbeddingGenerator

# Sample research-paper chunks
texts = [
    "Deep learning is used for medical image analysis.",
    "CNN models can detect diseases from X-ray images.",
    "Natural language processing helps analyse research papers."
]

# Create the embedding generator
generator = EmbeddingGenerator()

# Generate embeddings
embeddings = generator.generate_embeddings(texts)

# Display results
print("Number of chunks:", len(texts))
print("Embedding shape:", embeddings.shape)

for i, embedding in enumerate(embeddings):
    print(f"\nChunk {i + 1}")
    print("Vector dimensions:", len(embedding))
    print("First five values:", embedding[:5])


import numpy as np

# Take the first two embeddings
vector_a = embeddings[0]
vector_b = embeddings[1]

# Calculate cosine similarity
similarity = np.dot(vector_a, vector_b) / (
    np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
)

print("\nFirst vector dimensions:", len(vector_a))
print("Second vector dimensions:", len(vector_b))

print("Cosine similarity:", round(float(similarity), 4))
