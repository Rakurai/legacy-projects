"""
Explain Interface Tool - Five-part behavioral contract retrieval.

Composes existing entity fields with entity_usages data into a structured
behavioral contract for spec-creating and auditor agents.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from server.app import get_ctx, mcp
from server.db_models import Entity
from server.errors import EntityNotFoundError
from server.logging_config import log
from server.models import (
    CallingPattern,
    ContractMetadata,
    ContractSection,
    ExplainInterfaceResponse,
    MechanismSection,
    PreconditionsSection,
)
from server.util import fetch_top_callers


@mcp.tool()
async def explain_interface(
    ctx: Context,
    entity_id: Annotated[str, Field(description="Entity ID (from search or get_entity)")],
) -> ExplainInterfaceResponse:
    """
    Return a five-part behavioral contract for a code entity.

    Contract sections:
    1. **Signature** - Full signature and definition text
    2. **Mechanism** - What the entity does (brief + details)
    3. **Contract** - Caller-derived behavioral contract (rationale); null if no rationale
    4. **Preconditions** - Implementation notes and quirks; null if no notes
    5. **Calling patterns** - Top 5 usage patterns from callers, ranked by caller fan-in

    All data is derived from existing documentation fields — no LLM inference.
    """
    lc = get_ctx(ctx)

    log.info("explain_interface", entity_id=entity_id)

    async with lc["db_manager"].session() as session:
        entity = await session.get(Entity, entity_id)

        if not entity:
            raise EntityNotFoundError(entity_id)

        top_callers = await fetch_top_callers(session, entity_id, limit=5)
        calling_patterns = [
            CallingPattern(
                caller_compound=u.caller_compound,
                caller_sig=u.caller_sig,
                description=u.description,
            )
            for u in top_callers
        ]

    # Compose signature block
    signature_block = entity.signature if entity.signature else None

    return ExplainInterfaceResponse(
        signature_block=signature_block,
        mechanism=MechanismSection(
            brief=entity.brief,
            details=entity.details,
        ),
        contract=ContractSection(rationale=entity.rationale) if entity.rationale else None,
        preconditions=PreconditionsSection(notes=entity.notes) if entity.notes else None,
        calling_patterns=calling_patterns,
        metadata=ContractMetadata(
            doc_state=entity.doc_state,
            is_contract_seed=entity.is_contract_seed,
            rationale_specificity=entity.rationale_specificity,
            fan_in=entity.fan_in,
            fan_out=entity.fan_out,
            capability=entity.capability,
        ),
    )
