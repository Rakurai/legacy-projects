"""
MCP Prompts - Canned conversation starters for common analysis workflows.

Prompts:
- explain_entity: Comprehensive entity explanation workflow
- analyze_behavior: Behavioral analysis of a function
- compare_entry_points: Compare multiple entry points
- explore_capability: Explore a capability group
"""

from server.logging_config import log


def explain_entity_prompt(entity_name: str) -> list[dict[str, str]]:
    """
    Generate prompt messages for comprehensive entity explanation.

    Workflow: search → get_entity → get_callers → get_callees → get_capability_detail

    Args:
        entity_name: Entity name or signature to explain

    Returns:
        List of conversation messages (user + assistant)
    """
    log.info("Generating explain_entity prompt", entity_name=entity_name)

    return [
        {
            "role": "user",
            "content": (
                f"I need to understand the function/class/entity: {entity_name}. "
                "Please provide a comprehensive explanation including:\n\n"
                "1. What it does (brief summary)\n"
                "2. How it works (detailed implementation notes)\n"
                "3. Where it's used (callers and usage context)\n"
                "4. What it depends on (callees and dependencies)\n"
                "5. Its role in the architecture (capability membership, metrics)"
            ),
        },
        {
            "role": "assistant",
            "content": (
                f"I'll analyze {entity_name} using the Legacy documentation server. "
                "Let me gather information:\n\n"
                "1. First, I'll search for the entity to get its ID\n"
                "2. Then I'll fetch full details with get_entity\n"
                "3. Next, I'll examine callers and callees\n"
                "4. Finally, I'll check its capability membership and architectural role\n\n"
                "Starting with a search..."
            ),
        },
    ]


def analyze_behavior_prompt(
    entity_name: str,
    max_depth: int = 5,
) -> list[dict[str, str]]:
    """
    Generate prompt messages for behavioral analysis.

    Workflow: search → get_behavior_slice → get_state_touches

    Args:
        entity_name: Entity name or signature to analyze
        max_depth: Maximum call cone depth

    Returns:
        List of conversation messages (user + assistant)
    """
    log.info("Generating analyze_behavior prompt", entity_name=entity_name, max_depth=max_depth)

    return [
        {
            "role": "user",
            "content": (
                f"I need to understand the behavioral footprint of {entity_name}. "
                "Please analyze:\n\n"
                "1. What it transitively calls (full call cone)\n"
                "2. Which capability groups it exercises\n"
                "3. What global state it touches\n"
                "4. What side effects it produces\n"
                "5. Complexity and risk assessment"
            ),
        },
        {
            "role": "assistant",
            "content": (
                f"I'll perform a behavioral analysis of {entity_name} using call cone "
                "traversal and side-effect detection. This will reveal its transitive "
                "dependencies and architectural impact.\n\n"
                "Starting analysis..."
            ),
        },
    ]


def compare_entry_points_prompt(
    entry_point_names: list[str],
) -> list[dict[str, str]]:
    """
    Generate prompt messages for entry point comparison.

    Workflow: For each entry point → search → get_behavior_slice → get_entry_point_info
              Then compute intersection and differences.

    Args:
        entry_point_names: 2+ entry point names to compare

    Returns:
        List of conversation messages (user + assistant)
    """
    names_str = ", ".join(entry_point_names)
    log.info("Generating compare_entry_points prompt", entry_points=names_str)

    return [
        {
            "role": "user",
            "content": (
                f"I want to compare these entry points: {names_str}. "
                "Please identify:\n\n"
                "1. Shared dependencies (functions both call)\n"
                "2. Unique dependencies (functions only one calls)\n"
                "3. Capability overlap (which capabilities each exercises)\n"
                "4. Potential for code reuse or refactoring"
            ),
        },
        {
            "role": "assistant",
            "content": (
                f"I'll compare {names_str} by analyzing their call cones and "
                "capability footprints. This will reveal opportunities for "
                "consolidation or highlight their distinct roles.\n\n"
                "Gathering data..."
            ),
        },
    ]


def explore_capability_prompt(capability_name: str) -> list[dict[str, str]]:
    """
    Generate prompt messages for capability exploration.

    Workflow: get_capability_detail → list_entry_points → search (fan_in filter) →
              compare_capabilities

    Args:
        capability_name: Capability group name to explore

    Returns:
        List of conversation messages (user + assistant)
    """
    log.info("Generating explore_capability prompt", capability_name=capability_name)

    return [
        {
            "role": "user",
            "content": (
                f"I want to understand the {capability_name} capability group. "
                "Please explain:\n\n"
                "1. What it does (purpose and scope)\n"
                "2. Its functions and organization\n"
                "3. What it depends on (other capabilities)\n"
                "4. What depends on it (reverse dependencies)\n"
                "5. Entry points and user-facing features\n"
                "6. Hotspots and complexity"
            ),
        },
        {
            "role": "assistant",
            "content": (
                f"I'll analyze the {capability_name} capability using the "
                "documentation server. This will reveal its architectural role, "
                "dependencies, and complexity.\n\n"
                "Gathering capability data..."
            ),
        },
    ]
