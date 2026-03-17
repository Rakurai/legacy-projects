# Research: Local FastEmbed Provider

**Feature**: 004-local-fastembed-provider  
**Date**: 2026-03-15

## R1: FastEmbed Library Integration

**Decision**: Use `fastembed` Python library with `TextEmbedding` class for local ONNX-based embedding.

**Rationale**: FastEmbed is a lightweight, ONNX Runtime-based embedding library from Qdrant. It requires no GPU, no external service, and downloads model weights on first use (~130 MB for bge-base). The API is synchronous (`model.embed(texts)` returns an iterator of numpy arrays), which is ideal for the build pipeline and can be wrapped in `asyncio.to_thread()` for the async server path. It is the most commonly used Python library for local embedding without a full ML framework.

**Alternatives considered**:
- `sentence-transformers`: Heavier dependency (pulls PyTorch), more functionality than needed, larger install footprint (~2 GB).
- `onnxruntime` directly: Would require manual tokenization and model loading. FastEmbed handles both.
- `llama-cpp-python` with embedding models: More complex setup, designed for LLM inference not just embeddings.

## R2: Model Selection — BAAI/bge-base-en-v1.5

**Decision**: Use `BAAI/bge-base-en-v1.5` (768-dim, ~130 MB ONNX).

**Rationale**: bge-base is the mid-tier BGE model, well-suited for retrieval over structured technical text. At 768 dimensions it offers notably better retrieval quality than bge-small (384-dim) while remaining fast on CPU (~5-20ms per single text, ~2 minutes for 5,300 texts). The 768-dim vectors produce ~32 MB of stored embeddings for the full entity set, well within pgvector's comfort zone. This model is widely benchmarked and is FastEmbed's documented default tier.

**Alternatives considered**:
- `BAAI/bge-small-en-v1.5` (384-dim, ~33 MB): Faster and smaller but measurably worse on retrieval benchmarks. The 768→384 quality loss is not worth the marginal speed gain for an offline build step and <100ms query budget.
- `BAAI/bge-large-en-v1.5` (1024-dim, ~320 MB): Diminishing returns over base for this domain. Larger vectors increase pgvector index size without proportional benefit for ~5K entities.

## R3: Async Integration Pattern for Local Provider

**Decision**: Use `asyncio.to_thread()` to offload synchronous FastEmbed calls in the async server, and call synchronously in the build script.

**Rationale**: FastEmbed's `TextEmbedding.embed()` is a blocking CPU-bound call. In the MCP server (which is async via FastMCP), blocking the event loop would stall all concurrent tool calls. `asyncio.to_thread()` moves the call to a thread pool worker, which is the standard Python pattern for CPU-bound work in async contexts. Single-query embedding takes 5-20ms, so the thread pool overhead is negligible. The build script runs synchronously already (`asyncio.run(main())` wrapping the pipeline), so no threading is needed there.

**Alternatives considered**:
- `run_in_executor` with custom thread pool: Unnecessary complexity — the default executor is sufficient for single-query embedding payloads.
- Process pool: Overkill for a 5-20ms CPU operation. Process spawn overhead would dominate.

## R4: Dynamic Vector Column Dimension

**Decision**: Read `EMBEDDING_DIMENSION` from environment at module import time and pass to `Vector(dim)` in the SQLModel column definition.

**Rationale**: The `Vector(N)` declaration in pgvector/SQLAlchemy requires a compile-time integer. Since Python module-level code runs at import time, reading `os.environ.get("EMBEDDING_DIMENSION", "768")` at the top of `db_models.py` is the simplest approach. This works because:
1. The schema is dropped and recreated on every build (`drop_and_create_schema`).
2. Build and server both import `db_models.py` and both read the same `.env` file.
3. No migration is ever needed — the dimension is baked into the schema at table creation time.

**Alternatives considered**:
- Untyped vector column (pgvector supports `vector` without dimension): Loses HNSW index, which requires a fixed dimension. Unacceptable for search performance.
- Runtime schema alteration: Unnecessary complexity given the drop-and-recreate pattern.

## R5: Embedding Provider Abstraction Design

**Decision**: Define an `EmbeddingProvider` Protocol with `embed_query(text) -> list[float]` (async), `embed_documents(texts) -> list[list[float]]` (async), sync variants of both, and a `dimension` property. Two implementations: `LocalEmbeddingProvider` and `HostedEmbeddingProvider`. A `create_provider(config)` factory function selects the implementation.

**Rationale**: The current codebase passes `embedding_client: AsyncOpenAI | None` and `embedding_model: str` through 5 files (lifespan → tools → search/resolver). Replacing this with a single `EmbeddingProvider | None` simplifies the call chain. The Protocol pattern (structural typing) avoids requiring an abstract base class while still providing IDE/mypy support. Both implementations are simple wrappers (~20 lines each) around their respective libraries' APIs.

**Alternatives considered**:
- Keep `AsyncOpenAI` API as the universal interface and make FastEmbed conform to it: Would require faking the OpenAI response shape, which is fragile and misleading.
- Abstract base class (ABC): Works but Protocol is more Pythonic for this simple interface and doesn't require inheritance.
- No abstraction (just `if/else` in search.py): Scatters provider logic across multiple files, makes testing harder.

## R6: Artifact Naming Convention

**Decision**: `embed_cache_{model_slug}_{dim}.pkl` where `model_slug` is the model name with `/` replaced by `-`. Example: `embed_cache_BAAI-bge-base-en-v1.5_768.pkl`.

**Rationale**: Including both model name and dimension in the filename ensures:
1. Artifacts for different models coexist without collision.
2. A config change triggers regeneration (new filename doesn't exist).
3. Developers can visually identify what's cached.
The slug transformation (`/` → `-`) avoids filesystem path issues. Pickle format is retained because it's already the project standard and handles Python `list[float]` natively.

**Alternatives considered**:
- Hash-based naming (e.g., `embed_cache_{sha256(config)}.pkl`): Opaque, hard to reason about which artifact belongs to which config.
- JSON format: Much larger file size (~3x) for float arrays. numpy `.npy` would be optimal for size but adds a numpy dependency to the loader.

## R7: Embed Text Construction

**Decision**: Port the `Document.to_doxygen()` method from the original `doc_db.py` into a new `build_helpers/embed_text.py` module as `build_embed_text(merged: MergedEntity) -> str`. This function reconstructs the same Doxygen-formatted docstring from the server's `MergedEntity` and `Document` dataclass fields.

**Rationale**: The original embeddings were generated by calling `doc.to_doxygen()` on each document, producing structured text with `@fn`, `@brief`, `@details`, `@param`, `@return`, `@note`, `@rationale` tags. The server's `Document` dataclass (in `artifact_models.py`) has the same fields (`brief`, `details`, `params`, `returns`, `notes`, `rationale`, `definition`, `argsstring`). The `MergedEntity` provides `entity.kind` and `entity.name` for the tag line. By replicating the same text format, embeddings generated by the new system are semantically comparable to what the original pipeline would produce (modulo model differences).

**Alternatives considered**:
- Embed raw concatenated fields: Loses the structured format that was used for the original vectors. Would produce different embedding geometry.
- Import the original `doc_db.py` directly: Creates a cross-package dependency between the MCP server and the gen_docs pipeline. The server deliberately uses lightweight `artifact_models.py` to avoid this.

## R8: Build Pipeline: Hosted Generation At Build Time

**Decision**: The hosted provider's `embed_documents_sync` method will use the synchronous OpenAI SDK (`openai.OpenAI`) for batch embedding at build time, mirroring how the local provider uses `TextEmbedding.embed()`.

**Rationale**: The existing `regen_embeddings.py` already uses the synchronous OpenAI SDK for batch embedding. The build script runs `asyncio.run(main())` but the embedding generation step is naturally synchronous (iterate entities → batch embed → collect results). Using the sync SDK avoids mixing async OpenAI calls into the build's existing sync flow. The async variant (`AsyncOpenAI`) is used only at server runtime for query embedding.

**Alternatives considered**:
- Use async OpenAI client in the build: Would require restructuring the build pipeline's embedding stage to be async-first. Adds complexity for no benefit since the build is inherently sequential.
