import os
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_embeddings():
    """Load the embedding model only when a search needs it.

    Creating this object can download/load a large model.  Doing it during
    module import made even ``/health`` unavailable when the model cache or
    its optional dependency was missing.
    """
    # The model is downloaded during environment setup.  Avoid an online Hub
    # metadata check for each new server process, which otherwise leaves local
    # searches waiting when the server has no outbound network access.
    local_files_only = os.getenv(
        "EMBEDDING_LOCAL_FILES_ONLY", "true"
    ).strip().lower() not in {"0", "false", "no"}

    return HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"local_files_only": local_files_only},
    )
