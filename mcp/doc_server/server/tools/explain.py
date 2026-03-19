"""
Explain Interface Tool - Five-part behavioral contract retrieval.

Composes existing entity fields with entity_usages data into a structured
behavioral contract for spec-creating and auditor agents.
"""

from typing import Annotated

from fastmcp import Context
from pydantic import Field
from sqlalchemy import func
from sqlmodel import select

from server.app import get_ctx, mcp
from server.db_models import Entity, EntityUsage
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

        # Query entity_usages for this callee, ranked by caller fan_in.
        # Subquery: max fan_in per caller signature across all entities.
        # Defaults to 0 for unmatched callers (common sigs like void init() may not match).
        fanin_sq = (
            select(Entity.signature, func.max(Entity.fan_in).label("fan_in")).group_by(Entity.signature).subquery()
        )

        from sqlalchemy import outerjoin

        usage_stmt = (
            select(
                EntityUsage.caller_compound,
                EntityUsage.caller_sig,
                EntityUsage.description,
                func.coalesce(fanin_sq.c.fan_in, 0).label("caller_fan_in"),
            )
            .select_from(
                outerjoin(
                    EntityUsage,
                    fanin_sq,
                    EntityUsage.caller_sig == fanin_sq.c.signature,  # type: ignore[arg-type]
                )
            )
            .where(EntityUsage.callee_id == entity_id)
            .order_by(func.coalesce(fanin_sq.c.fan_in, 0).desc())
            .limit(5)
        )

        result = await session.execute(usage_stmt)
        usage_rows = result.all()

        calling_patterns = [
            CallingPattern(
                caller_compound=row.caller_compound,
                caller_sig=row.caller_sig,
                description=row.description,
            )
            for row in usage_rows
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
