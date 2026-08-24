# app/ingestion/load_schemes.py

from datasets import load_dataset

from app.ingestion.document_builder import create_document
from app.rag.vector_store import rebuild_vector_store
from app.config import CHROMA_PATH


DATASET_NAME = "smartduketech/indian-government-schemes-2025"


def load_schemes():

    # -------------------------------------------------
    # Step 1: Load dataset
    # -------------------------------------------------

    print("Loading government schemes dataset...")

    dataset = load_dataset(
        DATASET_NAME,
        split="train"
    )

    print("Dataset loaded successfully.")
    print("Number of schemes:", len(dataset))

    # -------------------------------------------------
    # Step 2: Convert dataset rows into Documents
    # -------------------------------------------------

    documents = [
        create_document(scheme)
        for scheme in dataset
    ]

    print("\nDocuments created:", len(documents))

    # -------------------------------------------------
    # Step 3: Check for empty documents
    # -------------------------------------------------

    empty_count = sum(
        1
        for doc in documents
        if not doc.page_content.strip()
    )

    print("Empty documents:", empty_count)

    # -------------------------------------------------
    # Step 4: Load all documents into ChromaDB
    # -------------------------------------------------

    print(f"\nLoading all {len(documents)} documents into ChromaDB...")

    rebuild_vector_store(
        documents,
        persist_directory=CHROMA_PATH,
    )

    print("\nVector database created successfully.")

    return documents


if __name__ == "__main__":
    load_schemes()