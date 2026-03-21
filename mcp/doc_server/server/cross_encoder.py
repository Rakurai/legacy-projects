"""
Cross-Encoder Provider - Async-capable wrapper around fastembed TextCrossEncoder.

Used for reranking search candidates against the original query text.
"""

import asyncio

from fastembed.rerank.cross_encoder import TextCrossEncoder

from server.logging_config import log


class CrossEncoderProvider:
    """Wraps TextCrossEncoder with sync/async rerank methods."""

    def __init__(self, model_name: str) -> None:
        log.info("Initializing cross-encoder model", model=model_name)
        self._reranker = TextCrossEncoder(model_name=model_name)
        self._model_name = model_name
        log.info("Cross-encoder model ready", model=model_name)

    def rerank(self, query: str, documents: list[str], batch_size: int = 64) -> list[float]:
        """Score each document against the query (sync). Returns scores in input order."""
        return list(self._reranker.rerank(query, documents, batch_size=batch_size))

    async def arerank(self, query: str, documents: list[str], batch_size: int = 64) -> list[float]:
        """Score each document against the query (async via thread offload)."""
        return await asyncio.to_thread(self.rerank, query, documents, batch_size)
