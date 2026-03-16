"""
Embedding helper — wraps an OpenAI-compatible endpoint with batching and
L2 normalisation.

Currently configured for **Qwen3-Embedding-8B** running locally in LM Studio.
Change BASE_URL / MODEL to switch providers.

Provides:
    embed_texts(texts)           → np.ndarray  (N, dim)
    embed_single(text)           → np.ndarray  (dim,)
"""
from __future__ import annotations

import os
import time
from typing import Sequence

import numpy as np
from openai import OpenAI

# ── Model configuration ──────────────────────────────────────────────
BASE_URL = os.environ.get("EMBEDDING_BASE_URL", "http://localhost:4000/v1")
API_KEY  = os.environ.get("EMBEDDING_API_KEY", "lm-studio")   # LM Studio ignores this
MODEL    = os.environ.get("EMBEDDING_MODEL", "text-embedding-qwen3-embedding-8b")
DIMENSIONS: int | None = None   # None = use model's native dim (set after first call)
MAX_BATCH = 64                  # small batches for local inference (large docs)
REQUEST_TIMEOUT = 120           # seconds per batch

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=REQUEST_TIMEOUT)
    return _client


def _normalize(vecs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(vecs, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return vecs / norms


def embed_texts(
    texts: Sequence[str],
    *,
    model: str = MODEL,
    batch_size: int = MAX_BATCH,
    show_progress: bool = False,
) -> np.ndarray:
    """Embed a list of texts, returning an (N, dim) float32 array (L2-normalised)."""
    global DIMENSIONS
    client = _get_client()
    all_vecs: list[np.ndarray] = []

    n = len(texts)
    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        batch = list(texts[start:end])
        if show_progress:
            print(f"  embedding batch {start}–{end} / {n} …")
        for attempt in range(3):
            try:
                resp = client.embeddings.create(input=batch, model=model)
                break
            except Exception as e:
                if attempt < 2:
                    wait = 5 * (attempt + 1)
                    print(f"    retry {attempt+1}/2 after error: {e!r} (wait {wait}s)")
                    time.sleep(wait)
                else:
                    raise
        # Response embeddings are returned in order
        vecs = np.array([d.embedding for d in resp.data], dtype=np.float32)
        all_vecs.append(vecs)

    result = np.concatenate(all_vecs, axis=0)
    result = _normalize(result)

    # Auto-detect dimensionality on first call
    if DIMENSIONS is None:
        DIMENSIONS = result.shape[1]

    return result


def embed_single(text: str, *, model: str = MODEL) -> np.ndarray:
    """Embed a single text, returning a 1-D float32 vector (L2-normalised)."""
    return embed_texts([text], model=model)[0]
