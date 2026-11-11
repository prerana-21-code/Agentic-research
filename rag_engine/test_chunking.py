
from chunking import create_chunks

sample_text = """
Artificial Intelligence is transforming healthcare.
Deep learning models are increasingly used for medical
image analysis. CNN models can identify patterns in
X-ray images. These models can help doctors detect
diseases earlier.
"""

chunks = create_chunks(
    text=sample_text,
    paper_id="P001",
    paper_title="AI in Healthcare",
    page_number=1,
    chunk_size=100,
    overlap=20
)

for chunk in chunks:
    print("\nChunk ID:", chunk["chunk_id"])
    print("Paper:", chunk["paper_title"])
    print("Page:", chunk["page_number"])
    print("Text:", chunk["text"])
