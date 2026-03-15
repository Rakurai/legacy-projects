"""
Unit tests for MCP prompt templates.

Tests that prompt generators return well-formed conversation messages.
"""

from server.prompts import (
    explain_entity_prompt,
    analyze_behavior_prompt,
    compare_entry_points_prompt,
    explore_capability_prompt,
)


def test_explain_entity_prompt():
    """Returns user+assistant messages mentioning the entity."""
    msgs = explain_entity_prompt("damage")

    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert "damage" in msgs[0]["content"]
    assert "damage" in msgs[1]["content"]


def test_analyze_behavior_prompt():
    """Returns messages for behavioral analysis workflow."""
    msgs = analyze_behavior_prompt("do_kill", max_depth=5)

    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert "do_kill" in msgs[0]["content"]


def test_compare_entry_points_prompt():
    """Returns messages mentioning all entry points."""
    msgs = compare_entry_points_prompt(["do_look", "do_examine"])

    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert "do_look" in msgs[0]["content"]
    assert "do_examine" in msgs[0]["content"]


def test_explore_capability_prompt():
    """Returns messages for capability exploration."""
    msgs = explore_capability_prompt("combat")

    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"
    assert "combat" in msgs[0]["content"]
