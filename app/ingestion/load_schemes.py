import os
import shutil
from pathlib import Path
from datasets import load_dataset
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.ingestion.document_builder import create_document
from app.embeddings import get_embeddings
from app.config import CHROMA_PATH, COLLECTION_NAME


DATASET_NAME = "smartduketech/indian-government-schemes-2025"
BATCH_SIZE = 250


def load_schemes(persist_directory=None):
    persist_directory = persist_directory or CHROMA_PATH

    # -------------------------------------------------
    # Step 1: Load dataset from Hugging Face
    # -------------------------------------------------
    print(f"Loading government schemes dataset '{DATASET_NAME}'...")
    dataset = load_dataset(DATASET_NAME, split="train")
    print(f"Dataset loaded: {len(dataset)} schemes found.")

    # -------------------------------------------------
    # Step 2: Convert dataset rows into Documents
    # -------------------------------------------------
    documents = []
    for scheme in dataset:
        doc = create_document(scheme)
        if doc.page_content.strip():
            documents.append(doc)

    print(f"Valid scheme documents created: {len(documents)}")

    # -------------------------------------------------
    # Step 3: Split into chunks
    # -------------------------------------------------
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documents)
    print(f"Total chunks to embed: {len(chunks)}")

    # -------------------------------------------------
    # Step 4: Clear existing Chroma directory
    # -------------------------------------------------
    path = Path(persist_directory)
    if path.exists():
        print(f"Removing old Chroma store at {path}...")
        shutil.rmtree(path)

    # -------------------------------------------------
    # Step 5: Ingest in batches using FastEmbed
    # -------------------------------------------------
    embeddings = get_embeddings()
    print(f"Embedding model ready. Ingesting in batches of {BATCH_SIZE}...")

    vector_store = None
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        print(f"Ingesting batch {i // BATCH_SIZE + 1} / {(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} chunks)...")
        if vector_store is None:
            vector_store = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                persist_directory=persist_directory,
                collection_name=COLLECTION_NAME,
            )
        else:
            vector_store.add_documents(batch)

    print(f"\nAll {len(chunks)} chunks across {len(documents)} schemes successfully ingested into ChromaDB at {persist_directory}!")
    return vector_store


if __name__ == "__main__":
    load_schemes()