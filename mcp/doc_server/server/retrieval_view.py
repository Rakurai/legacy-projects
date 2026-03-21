"""
RetrievalView - Per-view search configuration abstraction.

Each view (doc, symbol) encapsulates its embedding column, tsvector column,
cross-encoder instance, calibration values, and embed-text reconstruction function.
Instantiated at server startup and passed through the search pipeline.
"""

from collections.abc import Callable
from dataclasses import dataclass

from server.cross_encoder import CrossEncoderProvider
from server.db_models import Entity


@dataclass(frozen=True)
class RetrievalView:
    """Immutable per-view search configuration."""

    name: str
    embedding_column: str
    tsvector_column: str
    tsvector_dictionary: str
    cross_encoder: CrossEncoderProvider
    ts_rank_ceiling: float
    floor_thresholds: dict[str, float]
    assemble_embed_text: Callable[[Entity], str]
