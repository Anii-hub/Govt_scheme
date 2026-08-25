import shutil
from pathlib import Path

from langchain_chroma import Chroma

from app.embeddings import get_embeddings
from app.config import CHROMA_PATH, COLLECTION_NAME


def create_vector_store(
    documents,
    persist_directory=None,
):
    persist_directory = persist_directory or CHROMA_PATH
    print("Creating ChromaDB...")

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name=COLLECTION_NAME,
    )

    print("ChromaDB created successfully.")
    print("Stored documents:", len(documents))

    return vector_store


def rebuild_vector_store(
    documents,
    persist_directory=None,
):
    """Completely rebuild the government-schemes vector database.

    Removes the previous Chroma data directory first.
    """
    persist_directory = persist_directory or CHROMA_PATH
    path = Path(persist_directory)

    if path.exists():
        print(f"Removing old ChromaDB: {path}")
        shutil.rmtree(path)

    return create_vector_store(
        documents,
        persist_directory=persist_directory,
    )


def load_vector_store(
    persist_directory=None,
):
    persist_directory = persist_directory or CHROMA_PATH
    embeddings = get_embeddings()

    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME,
    )

    return vector_store