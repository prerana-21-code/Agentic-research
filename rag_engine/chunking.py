
import re


def create_chunks(
    text,
    paper_id,
    paper_title,
    page_number,
    chunk_size=500,
    overlap=100
):

    # Validate input
    if not isinstance(text, str) or not text.strip():
        raise ValueError("Research text cannot be empty.")

    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive.")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "Overlap must be non-negative and smaller than chunk size."
        )

    # Step 1: Split text into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())

    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    chunks = []
    current_sentences = []
    chunk_number = 1

    # Step 2: Group complete sentences into chunks
    for sentence in sentences:

        candidate = " ".join(current_sentences + [sentence])

        if current_sentences and len(candidate) > chunk_size:

            # Save the current chunk
            chunk_text = " ".join(current_sentences)

            chunks.append({
                "chunk_id": f"{paper_id}_chunk_{chunk_number}",
                "paper_id": paper_id,
                "paper_title": paper_title,
                "page_number": page_number,
                "text": chunk_text
            })

            chunk_number += 1

            # Step 3: Preserve overlapping sentences
            overlap_sentences = []
            overlap_length = 0

            for previous_sentence in reversed(current_sentences):

                required_length = len(previous_sentence)

                if overlap_sentences:
                    required_length += 1

                if overlap_length + required_length <= overlap:
                    overlap_sentences.insert(0, previous_sentence)
                    overlap_length += required_length

                else:
                    break
                
            current_sentences = overlap_sentences

        current_sentences.append(sentence)

    # Step 4: Store the final remaining chunk
    if current_sentences:

        chunk_text = " ".join(current_sentences)

        chunks.append({
            "chunk_id": f"{paper_id}_chunk_{chunk_number}",
            "paper_id": paper_id,
            "paper_title": paper_title,
            "page_number": page_number,
            "text": chunk_text
        })

    return chunks
