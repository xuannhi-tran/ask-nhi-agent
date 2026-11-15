"""Search Nhi's portfolio chunks in Supabase pgvector (the same index Ask Nhi uses)."""

import json
from dataclasses import dataclass
from functools import lru_cache

from . import config


@dataclass
class Chunk:
    id: str
    source: str  # project id, e.g. "jobcompass"
    heading: str
    text: str
    score: float


@lru_cache
def _voyage():
    import voyageai

    return voyageai.Client(max_retries=4)  # reads VOYAGE_API_KEY; retries rate-limit errors


@lru_cache
def _supabase():
    from supabase import create_client

    return create_client(config.SUPABASE_URL, config.SUPABASE_SECRET_KEY)


@lru_cache(maxsize=256)
def embed_query(text: str) -> tuple[float, ...]:
    """Cached, so repeated searches for the same text don't spend an API call."""
    result = _voyage().embed([text], model=config.VOYAGE_MODEL, input_type="query")
    return tuple(result.embeddings[0])


def search(query: str, k: int = config.TOP_K) -> list[Chunk]:
    # match_chunks is defined in portfolio-v3/supabase/rag.sql; pgvector takes the vector as text.
    rows = (
        _supabase()
        .rpc("match_chunks", {"query_embedding": json.dumps(list(embed_query(query))), "match_count": k})
        .execute()
        .data
    )
    return [
        Chunk(
            id=r["id"],
            source=r["source"],
            heading=r.get("heading", ""),
            text=r["text"],
            score=float(r.get("similarity", 0.0)),
        )
        for r in rows
        if float(r.get("similarity", 0.0)) >= config.MIN_SIMILARITY
    ]
