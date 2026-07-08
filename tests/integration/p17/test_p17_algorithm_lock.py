"""AC-P17-13 · algorithm_version bump policy."""

from __future__ import annotations

from dataclasses import replace

from travelogue.layout_engine.algorithm_lock import validate_pack_against_lock
from travelogue.layout_engine.registry import get_strategy_pack, strategy_pack_from_yaml


def test_default_pack_matches_algorithm_lock() -> None:
    pack = get_strategy_pack("lse-default-2026-06")
    ok, reason = validate_pack_against_lock(pack)
    assert ok, reason


def test_content_hash_change_requires_bump() -> None:
    pack = get_strategy_pack("lse-default-2026-06")
    mutated = replace(pack, content_hash="sha256:deadbeef", raw=dict(pack.raw))
    ok, reason = validate_pack_against_lock(mutated)
    assert not ok
    assert reason


def test_content_hash_change_passes_when_version_bumped() -> None:
    pack = get_strategy_pack("lse-default-2026-06")
    bumped = strategy_pack_from_yaml(
        pack.path,
        {
            **pack.raw,
            "version": int(pack.version) + 1,
            "algorithm_version": "p15-s3",
        },
    )
    bumped = replace(bumped, content_hash="sha256:deadbeef")
    ok, reason = validate_pack_against_lock(bumped)
    assert ok, reason
