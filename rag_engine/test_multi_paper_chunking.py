
from rag_engine.paper_loader import load_papers
from rag_engine.chunking import create_chunks

# Load all sample papers
papers = load_papers()

all_chunks = []

# Process every paper
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

# Display results
print("\n----- MULTI-PAPER CHUNKING RESULTS -----")

print("Total papers:", len(papers))
print("Total chunks:", len(all_chunks))

for chunk in all_chunks:
    print("\nChunk ID:", chunk["chunk_id"])
    print("Paper:", chunk["paper_title"])
    print("Text:", chunk["text"])
    print("Character count:", len(chunk["text"]))

# Check chunks per paper
print("\n----- CHUNKS PER PAPER -----")

for paper in papers:
    count = sum(
        1 for chunk in all_chunks
        if chunk["paper_id"] == paper["paper_id"]
    )

    print(paper["paper_id"], ":", count)
