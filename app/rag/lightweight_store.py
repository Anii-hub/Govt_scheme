"""Low-memory scheme retrieval backed by the bundled Chroma SQLite database."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.config import CHROMA_PATH


@dataclass
class SchemeDocument:
    """The small document interface consumed by the RAG pipeline."""

    page_content: str
    metadata: dict[str, object]


def _fts_query(query: str) -> str:
    """Convert user text to a safe SQLite FTS query."""
    tokens = re.findall(r"[^\W_]{2,}", query.lower(), flags=re.UNICODE)
    return " OR ".join(dict.fromkeys(tokens))


def _database_path() -> Path:
    return Path(CHROMA_PATH) / "chroma.sqlite3"


def keyword_search(query: str, k: int = 50) -> list[tuple[SchemeDocument, float]]:
    """Return BM25-ranked scheme documents without loading an ML model.

    The project's Chroma database already contains an SQLite full-text index of
    every scheme. Using it avoids the several-hundred-megabyte PyTorch embedding
    model that exceeds the memory available on Render's small instances.
    """
    fts_query = _fts_query(query)
    database_path = _database_path()
    if not fts_query or not database_path.is_file():
        return []

    with sqlite3.connect(database_path) as connection:
        ranked_ids = connection.execute(
            """
            SELECT rowid, bm25(embedding_fulltext_search) AS score
            FROM embedding_fulltext_search
            WHERE embedding_fulltext_search MATCH ?
            ORDER BY score
            LIMIT ?
            """,
            (fts_query, k),
        ).fetchall()

        if not ranked_ids:
            return []

        ids = [row[0] for row in ranked_ids]
        placeholders = ",".join("?" for _ in ids)
        metadata_rows = connection.execute(
            f"""
            SELECT id, key, string_value, int_value, float_value, bool_value
            FROM embedding_metadata
            WHERE id IN ({placeholders})
            """,
            ids,
        ).fetchall()

    metadata_by_id: dict[int, dict[str, object]] = {item_id: {} for item_id in ids}
    for item_id, key, string_value, int_value, float_value, bool_value in metadata_rows:
        value = next(
            (value for value in (string_value, int_value, float_value, bool_value) if value is not None),
            "",
        )
        metadata_by_id[item_id][key] = value

    results: list[tuple[SchemeDocument, float]] = []
    for item_id, score in ranked_ids:
        metadata = metadata_by_id[item_id]
        content = str(metadata.pop("chroma:document", ""))
        results.append((SchemeDocument(page_content=content, metadata=metadata), float(score)))

    return results
