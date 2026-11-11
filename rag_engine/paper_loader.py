
from pathlib import Path


def load_papers(folder_path=None):
    if folder_path is None:
        folder_path = Path(__file__).parent / "sample_data"
    else:
        folder_path = Path(folder_path)

    papers = []

    for file_path in sorted(folder_path.glob("paper_*.txt")):
        content = file_path.read_text(encoding="utf-8")

        if not content.strip():
            print(f"Skipping empty file: {file_path.name}")
            continue

        lines = content.splitlines()

        paper_id = None
        paper_title = None

        for line in lines:
            if line.startswith("Paper ID:"):
                paper_id = line.split(":", 1)[1].strip()

            elif line.startswith("Title:"):
                paper_title = line.split(":", 1)[1].strip()

        if not paper_id or not paper_title:
            print(f"Skipping file with missing metadata: {file_path.name}")
            continue

        papers.append({
            "paper_id": paper_id,
            "paper_title": paper_title,
            "text": content,
            "source": file_path.name
        })

    return papers
