"""
Embedding Provider Abstraction - Protocol + Local/Hosted implementations + factory.

Provides a unified interface for embedding text into fixed-dimension float vectors.
Two implementations:
  - LocalEmbeddingProvider: Bundled ONNX model via fastembed (no external service).
  - HostedEmbeddingProvider: OpenAI-compatible endpoint via openai SDK.

Factory function `create_provider(config)` selects the implementation based on config.
"""

from __future__ import annotations

import asyncio
from typing import Protocol, runtime_checkable

import numpy as np
from fastembed import TextEmbedding
from openai import AsyncOpenAI, OpenAI

from server.config import ServerConfig
from server.logging_config import log

# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------

@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding text into fixed-dimension float vectors."""

    @property
    def dimension(self) -> int:
        """Number of dimensions in the output vector."""
        ...

    async def embed_query(self, text: str) -> list[float]:
        """Embed a single query string (async, non-blocking)."""
        ...

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple document strings (async)."""
        ...

    def embed_query_sync(self, text: str) -> list[float]:
        """Embed a single query string (synchronous, for build pipeline)."""
        ...

    def embed_documents_sync(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple document strings (synchronous, for build pipeline)."""
        ...


# ---------------------------------------------------------------------------
# Local Provider (FastEmbed / ONNX)
# ---------------------------------------------------------------------------

class LocalEmbeddingProvider:
    """Embedding provider using a bundled ONNX model via fastembed.

    Sync methods call ONNX directly. Async methods offload to a background
    thread via asyncio.to_thread() to avoid blocking the event loop (FR-012).
    """

    def __init__(self, model_name: str = "BAAI/bge-base-en-v1.5") -> None:
        log.info("Initializing local embedding model", model=model_name)
        self._model = TextEmbedding(model_name=model_name)
        self._model_name = model_name
        # Probe dimension by embedding a tiny string
        probe = list(self._model.embed(["dimension probe"]))
        self._dimension = len(probe[0])
        log.info("Local embedding model ready", model=model_name, dimension=self._dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_query_sync(self, text: str) -> list[float]:
        results = list(self._model.embed([text]))
        return results[0].tolist() if isinstance(results[0], np.ndarray) else list(results[0])

    def embed_documents_sync(self, texts: list[str]) -> list[list[float]]:
        results = list(self._model.embed(texts))
        return [r.tolist() if isinstance(r, np.ndarray) else list(r) for r in results]

    async def embed_query(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed_query_sync, text)

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_documents_sync, texts)


# ---------------------------------------------------------------------------
# Hosted Provider (OpenAI-compatible)
# ---------------------------------------------------------------------------

class HostedEmbeddingProvider:
    """Embedding provider using an OpenAI-compatible hosted endpoint.

    Uses sync `OpenAI` client for build-time batch operations and
    async `AsyncOpenAI` client for server runtime query embedding.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimension: int,
    ) -> None:
        self._model = model
        self._dimension = dimension
        self._sync_client = OpenAI(base_url=base_url, api_key=api_key)
        self._async_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        log.info("Hosted embedding provider initialized", base_url=base_url, model=model, dimension=dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    def _extract_vectors(self, data: list) -> list[list[float]]:
        """Extract embedding vectors from OpenAI response data objects."""
        return [item.embedding for item in data]

    def embed_query_sync(self, text: str) -> list[float]:
        response = self._sync_client.embeddings.create(
            model=self._model,
            input=text,
            encoding_format="float",
        )
        return response.data[0].embedding

    def embed_documents_sync(self, texts: list[str]) -> list[list[float]]:
        # Process in batches of 32 to stay within typical API limits
        all_embeddings: list[list[float]] = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = self._sync_client.embeddings.create(
                model=self._model,
                input=batch,
                encoding_format="float",
            )
            all_embeddings.extend(self._extract_vectors(response.data))
        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        response = await self._async_client.embeddings.create(
            model=self._model,
            input=text,
            encoding_format="float",
        )
        return response.data[0].embedding

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self._async_client.embeddings.create(
                model=self._model,
                input=batch,
                encoding_format="float",
            )
            all_embeddings.extend(self._extract_vectors(response.data))
        return all_embeddings


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_provider(config: ServerConfig) -> EmbeddingProvider | None:
    """Create an embedding provider based on configuration.

    Returns:
        LocalEmbeddingProvider, HostedEmbeddingProvider, or None.

    Raises:
        ValueError: If provider dimension doesn't match config.embedding_dimension.
    """
    if config.embedding_provider is None:
        log.info("No embedding provider configured; semantic search disabled")
        return None

    if config.embedding_provider == "local":
        provider = LocalEmbeddingProvider(model_name=config.embedding_local_model)

    elif config.embedding_provider == "hosted":
        if not config.embedding_base_url:
            raise ValueError("EMBEDDING_BASE_URL is required when EMBEDDING_PROVIDER=hosted")
        if not config.embedding_model:
            raise ValueError("EMBEDDING_MODEL is required when EMBEDDING_PROVIDER=hosted")

        provider = HostedEmbeddingProvider(
            base_url=config.embedding_base_url,
            api_key=config.embedding_api_key or "default",
            model=config.embedding_model,
            dimension=config.embedding_dimension,
        )
    else:
        raise ValueError(f"Unknown embedding provider: {config.embedding_provider!r}")

    # Validate dimension matches config (FR-011)
    if provider.dimension != config.embedding_dimension:
        raise ValueError(
            f"Embedding dimension mismatch: provider outputs {provider.dimension}-dim vectors "
            f"but config specifies EMBEDDING_DIMENSION={config.embedding_dimension}"
        )

    log.info(
        "Embedding provider created",
        provider=config.embedding_provider,
        dimension=provider.dimension,
    )
    return provider
