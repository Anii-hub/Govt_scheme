"""
Embedding model factory.

Groq does not provide an embeddings API — it is an LLM inference service only.
For a lightweight, deployment-friendly alternative to sentence-transformers we use
FastEmbed, which runs BAAI/bge-small-en-v1.5 via ONNX Runtime (no PyTorch required).

FastEmbed is ~10x smaller in memory footprint than sentence-transformers and boots
in ~200 ms on CPU, making cold-starts on free tiers (e.g. Render) very fast.
"""

from functools import lru_cache

from langchain_community.embeddings import FastEmbedEmbeddings

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings():
    """Return a cached FastEmbed embedding model instance.

    FastEmbedEmbeddings downloads the ONNX model on first use and caches it
    locally, so subsequent server restarts are near-instant.
    """
    return FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
