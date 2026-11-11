import chromadb
import os


class VectorStore:

    def __init__(self, database_path=None):

        if database_path is None:
            database_path = os.path.join(
                os.path.expanduser("~"),
                "rag_research_database"
            )

        os.makedirs(database_path, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=database_path
        )

        self.collection = self.client.get_or_create_collection(
            name="research_papers"
        )

    def add_documents(self, chunks, embeddings):

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:

            ids.append(chunk["chunk_id"])
            documents.append(chunk["text"])

            metadatas.append({
                "paper_id": chunk["paper_id"],
                "paper_title": chunk["paper_title"],
                "page_number": chunk["page_number"]
            })

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas
        )

        print(f"Successfully stored {len(ids)} chunks in ChromaDB!")