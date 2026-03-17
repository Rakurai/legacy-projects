"""Unit tests for the deterministic entity ID generator."""

import re

import pytest

from build_helpers.entity_ids import build_id_map, compute_entity_id, kind_to_prefix

_ID_RE = re.compile(r"^[a-z]+:[0-9a-f]{7}$")


# -- kind_to_prefix ----------------------------------------------------------


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("function", "fn"),
        ("define", "fn"),
        ("variable", "var"),
        ("class", "cls"),
        ("struct", "cls"),
        ("file", "file"),
        ("enum", "sym"),
        ("typedef", "sym"),
        ("unknown", "sym"),
    ],
)
def test_kind_to_prefix(kind: str, expected: str) -> None:
    assert kind_to_prefix(kind) == expected


# -- compute_entity_id -------------------------------------------------------


def test_compute_entity_id_format() -> None:
    eid = compute_entity_id("function", "fight_8cc", "void fight(CHAR_DATA*)")
    assert _ID_RE.match(eid), f"ID {eid!r} does not match {{prefix}}:{{7 hex}}"
    assert eid.startswith("fn:")


def test_compute_entity_id_determinism() -> None:
    a = compute_entity_id("function", "fight_8cc", "void fight(CHAR_DATA*)")
    b = compute_entity_id("function", "fight_8cc", "void fight(CHAR_DATA*)")
    assert a == b


def test_compute_entity_id_different_kinds_different_prefix() -> None:
    fn_id = compute_entity_id("function", "foo_c", "void foo()")
    var_id = compute_entity_id("variable", "foo_c", "int foo")
    assert fn_id.startswith("fn:")
    assert var_id.startswith("var:")
    assert fn_id != var_id


def test_compute_entity_id_different_inputs_different_hash() -> None:
    a = compute_entity_id("function", "a_c", "void a()")
    b = compute_entity_id("function", "b_c", "void b()")
    assert a != b


# -- build_id_map -------------------------------------------------------------


def _make_sig_map_and_entities(
    entries: list[tuple[str, str, str, str]],
) -> tuple[dict[str, str], dict[str, dict]]:
    """Build signature_map_data and code_graph_entities from a list of tuples.

    Each tuple: (compound_id, second_element, old_entity_id, kind)
    """
    sig_map: dict[str, str] = {}
    entities: dict[str, dict] = {}
    for compound_id, second_element, old_id, kind in entries:
        key_str = repr((compound_id, second_element))
        sig_map[key_str] = old_id
        entities[old_id] = {"kind": kind}
    return sig_map, entities


def test_build_id_map_basic() -> None:
    sig_map, entities = _make_sig_map_and_entities([
        ("fight_8cc", "void fight(CHAR_DATA*)", "fight_8cc_abc123", "function"),
        ("save_8cc", "void save()", "save_8cc_def456", "function"),
    ])
    result = build_id_map(sig_map, entities)
    assert len(result) == 2
    for old_id, new_id in result.items():
        assert _ID_RE.match(new_id), f"{new_id!r} does not match format"
        assert new_id.startswith("fn:")


def test_build_id_map_skips_missing_entities() -> None:
    sig_map = {repr(("foo_c", "void foo()")): "old_foo"}
    entities: dict[str, dict] = {}  # empty — no matching entity
    result = build_id_map(sig_map, entities)
    assert len(result) == 0


def test_build_id_map_collision_raises() -> None:
    """Synthetic collision: force two different keys to map to the same new ID.

    We monkey-patch compute_entity_id to always return the same value.
    """
    import build_helpers.entity_ids as mod

    original = mod.compute_entity_id

    def always_collide(kind: str, compound_id: str, second_element: str) -> str:
        return "fn:0000000"

    mod.compute_entity_id = always_collide  # type: ignore[assignment]
    try:
        sig_map, entities = _make_sig_map_and_entities([
            ("a_c", "void a()", "old_a", "function"),
            ("b_c", "void b()", "old_b", "function"),
        ])
        with pytest.raises(RuntimeError, match="Hash collision"):
            build_id_map(sig_map, entities)
    finally:
        mod.compute_entity_id = original  # type: ignore[assignment]


def test_build_id_map_determinism() -> None:
    sig_map, entities = _make_sig_map_and_entities([
        ("fight_8cc", "void fight(CHAR_DATA*)", "old_fight", "function"),
        ("save_8cc", "void save()", "old_save", "function"),
        ("player_h", "class Player", "old_player", "class"),
    ])
    r1 = build_id_map(sig_map, entities)
    r2 = build_id_map(sig_map, entities)
    assert r1 == r2
