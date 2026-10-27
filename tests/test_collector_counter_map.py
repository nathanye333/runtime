"""Every canonical Sample field must map on Ampere, Hopper, and Blackwell."""

from __future__ import annotations

from gitm.telemetry.counter_map import (
    COUNTER_MAP,
    GENERATIONS,
    generations_missing,
    required_sample_fields,
    unmapped_sample_fields,
)


def test_every_canonical_sample_field_is_mapped() -> None:
    missing = unmapped_sample_fields()
    assert not missing, f"Sample fields missing from COUNTER_MAP: {sorted(missing)}"


def test_every_mapped_field_covers_all_generations() -> None:
    required = required_sample_fields()
    for field in sorted(required):
        absent = generations_missing(field)
        assert not absent, f"{field} missing generation mapping(s): {sorted(absent)}"


def test_counter_map_has_no_orphan_keys() -> None:
    """Map keys should be Sample fields (or we dropped a field without cleanup)."""
    allowed = required_sample_fields()
    orphans = frozenset(COUNTER_MAP) - allowed
    assert not orphans, f"COUNTER_MAP keys not on Sample: {sorted(orphans)}"


def test_generations_tuple_is_the_pass_set() -> None:
    assert GENERATIONS == ("ampere", "hopper", "blackwell")
