
from rag_engine.paper_loader import load_papers

papers = load_papers()

print("\n----- PAPER LOADING RESULTS -----")
print("Total papers loaded:", len(papers))

for paper in papers:
    print("\nPaper ID:", paper["paper_id"])
    print("Title:", paper["paper_title"])
    print("Source:", paper["source"])
    print("Text length:", len(paper["text"]))
