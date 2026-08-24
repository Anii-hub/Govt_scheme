import shutil
from pathlib import Path

from langchain_chroma import Chroma

from app.embeddings import get_embeddings
from app.config import CHROMA_PATH, COLLECTION_NAME


# =========================================================
# Create Vector Store
# =========================================================

def create_vector_store(
    documents,
    persist_directory=CHROMA_PATH
):
    print(f"Creating ChromaDB in {persist_directory}...")

    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
        collection_name=COLLECTION_NAME,
    )

    batch_size = 250
    total = len(documents)
    for i in range(0, total, batch_size):
        batch = documents[i : i + batch_size]
        vector_store.add_documents(batch)
        print(f"Indexed {min(i + batch_size, total)}/{total} documents...")

    print("ChromaDB created successfully.")
    print("Stored documents:", total)

    return vector_store


# =========================================================
# Rebuild Vector Store
# =========================================================

def rebuild_vector_store(
    documents,
    persist_directory=CHROMA_PATH
):
    """
    Completely rebuild the government-schemes vector database.
    Removes the previous Chroma data directory first, or resets the collection if locked.
    """

    path = Path(persist_directory)

    if path.exists():
        try:
            print(f"Removing old ChromaDB directory: {path}")
            shutil.rmtree(path)
        except PermissionError:
            print(f"Directory {path} is open by another process. Resetting collection via Chroma API...")
            try:
                temp_vs = Chroma(
                    persist_directory=persist_directory,
                    embedding_function=get_embeddings(),
                    collection_name=COLLECTION_NAME,
                )
                temp_vs.delete_collection()
            except Exception as exc:
                print(f"Collection reset notice: {exc}")

    return create_vector_store(
        documents,
        persist_directory=persist_directory,
    )


# =========================================================
# Load Vector Store
# =========================================================

def load_vector_store(
    persist_directory=CHROMA_PATH
):
    return Chroma(
        persist_directory=persist_directory,
        embedding_function=get_embeddings(),
        collection_name=COLLECTION_NAME,
    )
