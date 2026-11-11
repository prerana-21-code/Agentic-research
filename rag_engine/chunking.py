
def create_chunks(
    text,
    paper_id,
    paper_title,
    page_number,
    chunk_size=500,
    overlap=100
):
    """
    Divide research-paper text into smaller chunks.
    Preserve information about the original paper.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("Research text cannot be empty.")

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    chunks = []
    start = 0
    chunk_number = 1

    while start < len(text):

        end = start + chunk_size

        chunk_text = text[start:end]

        chunk = {
            "chunk_id": f"{paper_id}_chunk_{chunk_number}",
            "paper_id": paper_id,
            "paper_title": paper_title,
            "page_number": page_number,
            "text": chunk_text
        }

        chunks.append(chunk)

        chunk_number += 1
        start += chunk_size - overlap

    return chunks
