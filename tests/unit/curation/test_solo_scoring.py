"""PA-T09 · U-SOLO solo scoring unit tests."""

from __future__ import annotations

from travelogue.layout_engine.scoring.solo import (
    build_solo_explain,
    duplicate_penalty,
    pick_solo_asset_id,
    solo_score,
    sort_ids_by_solo_score,
    tone_uniqueness,
)


def _asset(
    aid: str,
    *,
    overall: float = 0.6,
    lighting: float = 0.6,
    negative_space: float = 0.5,
    tone: str = "#808080",
    burst: str | None = None,
) -> dict:
    entry: dict = {
        "id": aid,
        "dominantTone": tone,
        "quality": {
            "aesthetic": {
                "overall": overall,
                "dims": {"lighting": lighting, "composition": 0.6},
                "signals": {"negativeSpace": negative_space},
            }
        },
    }
    if burst:
        entry["burstGroupId"] = burst
    return entry


def test_tone_uniqueness_monochrome_peers_low() -> None:
    a = _asset("a", tone="#ff0000")
    peers = [_asset("b", tone="#ff1010"), _asset("c", tone="#fe0000")]
    assert tone_uniqueness(a, peers) < 0.4


def test_tone_uniqueness_complementary_higher() -> None:
    a = _asset("a", tone="#ff0000")
    peers = [_asset("b", tone="#00ffff")]
    assert tone_uniqueness(a, peers) > tone_uniqueness(a, [_asset("b", tone="#ff2020")])


def test_duplicate_penalty_excludes_cover_and_hero() -> None:
    asset = _asset("cover", overall=0.9)
    assert duplicate_penalty(asset, exclude_ids={"cover"}) == 1.0


def test_solo_score_zero_for_excluded() -> None:
    assert solo_score(_asset("x"), exclude_ids={"x"}, aesthetic_enabled=True) == 0.0


def test_solo_score_higher_with_lighting_and_space() -> None:
    weak = _asset("w", overall=0.6, lighting=0.2, negative_space=0.2)
    strong = _asset("s", overall=0.6, lighting=0.9, negative_space=0.8)
    assert solo_score(strong, aesthetic_enabled=True) > solo_score(weak, aesthetic_enabled=True)


def test_pick_solo_prefers_high_overall() -> None:
    assets = {
        "low": _asset("low", overall=0.35),
        "high": _asset("high", overall=0.85),
    }
    assert pick_solo_asset_id(["low", "high"], assets, aesthetic_enabled=True) == "high"


def test_pick_solo_skips_excluded_ids() -> None:
    assets = {
        "hero": _asset("hero", overall=0.95),
        "alt": _asset("alt", overall=0.55),
    }
    picked = pick_solo_asset_id(
        ["hero", "alt"], assets, exclude={"hero"}, aesthetic_enabled=True
    )
    assert picked == "alt"


def test_sort_ids_by_solo_score_orders_descending() -> None:
    assets = {
        "a": _asset("a", overall=0.4),
        "b": _asset("b", overall=0.8),
        "c": _asset("c", overall=0.6),
    }
    ordered = sort_ids_by_solo_score(["a", "b", "c"], assets, aesthetic_enabled=True)
    assert ordered[0] == "b"


def test_build_solo_explain_nonempty_for_strong_candidate() -> None:
    asset = _asset("s", overall=0.85, lighting=0.9, negative_space=0.7, tone="#112233")
    peers = [_asset("p", tone="#ffee00")]
    explain = build_solo_explain(asset, peer_assets=peers, aesthetic_enabled=True)
    assert explain
    assert all("label" in row and "reason" in row for row in explain)


def test_burst_duplicate_penalty_reduces_score() -> None:
    used = {"used-1"}
    assets = {
        "used-1": _asset("used-1", burst="burst-a"),
        "dup": _asset("dup", burst="burst-a", overall=0.8),
        "fresh": _asset("fresh", burst="burst-b", overall=0.8),
    }
    assert solo_score(
        assets["dup"],
        used_asset_ids=used,
        assets_by_id=assets,
        aesthetic_enabled=True,
    ) < solo_score(
        assets["fresh"],
        used_asset_ids=used,
        assets_by_id=assets,
        aesthetic_enabled=True,
    )
