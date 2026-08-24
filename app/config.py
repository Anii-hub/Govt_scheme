import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


# Keep data paths stable when Uvicorn is started outside the repository root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

_chroma_path = Path(os.getenv("CHROMA_PATH", "data/chroma"))
CHROMA_PATH = str(
    _chroma_path if _chroma_path.is_absolute() else PROJECT_ROOT / _chroma_path
)

COLLECTION_NAME = os.getenv(
    "COLLECTION_NAME",
    "government_schemes"
)
