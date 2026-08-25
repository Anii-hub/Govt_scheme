from datasets import load_dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.ingestion.document_builder import create_document
from app.rag.vector_store import rebuild_vector_store


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

    documents = []

    for scheme in dataset:

        document = create_document(scheme)

        documents.append(document)

    print("\nDocuments created:", len(documents))

    # -------------------------------------------------
    # Step 3: Check for empty documents
    # -------------------------------------------------

    empty_documents = [
        document
        for document in documents
        if not document.page_content.strip()
    ]

    print("Empty documents:", len(empty_documents))

    # -------------------------------------------------
    # Step 4: Split documents into chunks
    # -------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
    )
    chunks = splitter.split_documents(documents)

    print("Original documents:", len(documents))
    print("Total chunks:", len(chunks))

    # -------------------------------------------------
    # Step 5: Display first chunk
    # -------------------------------------------------

    print("\n--- FIRST CHUNK ---")

    print(
        chunks[0].page_content
    )

    print("\n--- FIRST CHUNK METADATA ---")

    print(
        chunks[0].metadata
    )

    # -------------------------------------------------
    # Step 6: Create the real ChromaDB
    # -------------------------------------------------

    print(
        "\nLoading all chunks into ChromaDB:",
        len(chunks)
    )

    vector_store = rebuild_vector_store(
        chunks,
        persist_directory="data/chroma"
    )

    print(
        "\nVector database created successfully."
    )

    return chunks


if __name__ == "__main__":
    load_schemes()