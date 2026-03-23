"""
Embedding Provider Abstraction - Protocol + Local/Hosted implementations + factory.

Provides a unified interface for embedding text into fixed-dimension float vectors.
Two implementations:
  - LocalEmbeddingProvider: Bundled ONNX model via fastembed (no external service).
  - HostedEmbeddingProvider: OpenAI-compatible endpoint via openai SDK.

Factory function `create_provider(config)` selects the implementation based on config.
"""

import asyncio
from collections.abc import Generator
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

    @property
    def max_batch_size(self) -> int:
        """Maximum recommended texts per batch call. Provider handles internal chunking."""
        ...

    def embed(self, text: str) -> list[float]:
        """Embed a single text string (sync). Delegates to embed_batch."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple text strings (sync). Used by build pipeline."""
        ...

    async def aembed(self, text: str) -> list[float]:
        """Embed a single text string (async). Used by server runtime."""
        ...

    async def aembed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple text strings (async)."""
        ...


# ---------------------------------------------------------------------------
# Local Provider (FastEmbed / ONNX)
# ---------------------------------------------------------------------------


class LocalEmbeddingProvider:
    """Embedding provider using a bundled ONNX model via fastembed.

    Sync methods call ONNX directly. Async methods offload to a background
    thread via asyncio.to_thread() to avoid blocking the event loop (CPU-bound).
    """

    _max_batch_size: int = 256

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

    @property
    def max_batch_size(self) -> int:
        return self._max_batch_size

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        results = list(self._model.embed(texts, batch_size=self._max_batch_size))
        return [r.tolist() if isinstance(r, np.ndarray) else list(r) for r in results]

    async def aembed(self, text: str) -> list[float]:
        return await asyncio.to_thread(self.embed, text)

    async def aembed_batch(self, texts: list[str]) -> list[list[float]]:
        return await asyncio.to_thread(self.embed_batch, texts)


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
        max_batch_size: int = 256,
    ) -> None:
        self._model = model
        self._dimension = dimension
        self._max_batch_size = max_batch_size
        self._sync_client = OpenAI(base_url=base_url, api_key=api_key)
        self._async_client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        log.info("Hosted embedding provider initialized", base_url=base_url, model=model, dimension=dimension)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def max_batch_size(self) -> int:
        return self._max_batch_size

    def _iter_batches(self, texts: list[str]) -> Generator[list[str]]:
        """Yield successive batches of max_batch_size from texts."""
        for i in range(0, len(texts), self._max_batch_size):
            yield texts[i : i + self._max_batch_size]

    def embed(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for batch in self._iter_batches(texts):
            response = self._sync_client.embeddings.create(
                model=self._model,
                input=batch,
                encoding_format="float",
            )
            all_embeddings.extend(item.embedding for item in response.data)
        return all_embeddings

    async def aembed(self, text: str) -> list[float]:
        results = await self.aembed_batch([text])
        return results[0]

    async def aembed_batch(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []
        for batch in self._iter_batches(texts):
            response = await self._async_client.embeddings.create(
                model=self._model,
                input=batch,
                encoding_format="float",
            )
            all_embeddings.extend(item.embedding for item in response.data)
        return all_embeddings


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_provider(config: ServerConfig, *, model_name_override: str | None = None) -> EmbeddingProvider:
    """Create an embedding provider based on configuration.

    Args:
        config: Server configuration.
        model_name_override: Override the local model name (e.g. for symbol view).
            Only applies when embedding_provider='local'.

    Raises:
        ValueError: If provider dimension doesn't match config.embedding_dimension.
    """
    provider: EmbeddingProvider
    if config.embedding_provider == "local":
        model_name = model_name_override or config.embedding_local_model
        provider = LocalEmbeddingProvider(model_name=model_name)

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
