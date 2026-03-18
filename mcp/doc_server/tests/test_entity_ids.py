"""Unit tests for the deterministic entity ID generator."""

import re

import pytest

from build_helpers.entity_ids import compute_entity_id, kind_to_prefix

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
