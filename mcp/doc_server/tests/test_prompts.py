"""
Unit tests for MCP prompt templates.

Tests that prompt generators return well-formed conversation messages.
"""

import pytest

from server.prompts import (
    explain_entity_prompt,
    analyze_behavior_prompt,
    compare_entry_points_prompt,
    explore_capability_prompt,
)


@pytest.mark.parametrize(
    "factory,args,expected_mentions",
    [
        (explain_entity_prompt, ("damage",), ["damage"]),
        (analyze_behavior_prompt, ("do_kill", 5), ["do_kill"]),
        (compare_entry_points_prompt, (["do_look", "do_examine"],), ["do_look", "do_examine"]),
        (explore_capability_prompt, ("combat",), ["combat"]),
    ],
    ids=["explain_entity", "analyze_behavior", "compare_entry_points", "explore_capability"],
)
def test_prompt_structure(factory, args, expected_mentions):
    """All prompt generators return user+assistant messages mentioning key terms."""
    msgs = factory(*args)

    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    for term in expected_mentions:
        assert term in msgs[0]["content"]
