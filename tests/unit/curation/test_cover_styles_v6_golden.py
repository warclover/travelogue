"""Cover Styles V6 · §6.3.1 golden fit fixtures (≥2 boost + ≥2 penalty per style)."""

from __future__ import annotations

import pytest

from travelogue.cover_engine.fit import (
    net_style_fit,
    style_avoid_penalty,
    style_fit_below_threshold,
    style_fit_score,
)
from travelogue.cover_engine.registry import get_profile

# (style_id, kind, fx, fy, extra_asset_fields)
# kind: boost | penalty
_GOLDEN: list[tuple[str, str, float, float, dict]] = [
    # veil-footer · prefer focal_y_max; avoid subject_bottom
    ("veil-footer", "boost", 0.5, 0.28, {}),
    ("veil-footer", "boost", 0.42, 0.40, {}),
    ("veil-footer", "penalty", 0.5, 0.82, {}),
    ("veil-footer", "penalty", 0.55, 0.90, {}),
    # folio-overlap · prefer right_weighted; avoid subject_left_30
    ("folio-overlap", "boost", 0.72, 0.45, {}),
    ("folio-overlap", "boost", 0.65, 0.50, {}),
    ("folio-overlap", "penalty", 0.12, 0.45, {}),
    ("folio-overlap", "penalty", 0.18, 0.55, {}),
    # band-cut · prefer upper/horizon; avoid band_safe_zone
    ("band-cut", "boost", 0.5, 0.32, {}),
    ("band-cut", "boost", 0.48, 0.40, {}),
    ("band-cut", "penalty", 0.5, 0.63, {}),
    ("band-cut", "penalty", 0.55, 0.68, {}),
    # cameo-aperture · prefer tight center (trusted focal); avoid edge
    ("cameo-aperture", "boost", 0.51, 0.44, {"faceCount": 1}),
    ("cameo-aperture", "boost", 0.48, 0.42, {"faceCount": 1}),
    ("cameo-aperture", "penalty", 0.08, 0.20, {}),
    ("cameo-aperture", "penalty", 0.92, 0.85, {}),
    # type-monument · prefer texture_mood; avoid face_must_read / very_light_bg
    ("type-monument", "boost", 0.35, 0.55, {"aesthetic": {"overall": 0.72}}),
    ("type-monument", "boost", 0.6, 0.6, {"aesthetic": {"overall": 0.65}}),
    # face_must_read: slightly off sentinel so focal is trusted
    ("type-monument", "penalty", 0.52, 0.42, {"aesthetic": {"overall": 0.3}, "faceCount": 1}),
    ("type-monument", "penalty", 0.55, 0.50, {"avgLuma": 0.85, "aesthetic": {"overall": 0.2}}),
]


def _asset(fx: float, fy: float, extra: dict | None = None) -> dict:
    out = {
        "id": f"g-{fx}-{fy}",
        "type": "image",
        "width": 1600,
        "height": 1200,
        "focalPoint": {"x": fx, "y": fy},
    }
    if extra:
        out.update(extra)
    return out


@pytest.mark.parametrize("style_id,kind,fx,fy,extra", _GOLDEN)
def test_golden_fixture_direction(
    style_id: str, kind: str, fx: float, fy: float, extra: dict
) -> None:
    profile = get_profile(style_id)
    asset = _asset(fx, fy, extra)
    net = net_style_fit(asset, profile)
    if kind == "boost":
        assert style_fit_score(asset, profile) > 0 or style_avoid_penalty(asset, profile) == 0
        assert net >= 0.0, (style_id, kind, net, asset)
    else:
        assert style_avoid_penalty(asset, profile) > 0 or net < 0.15
        assert net < style_fit_score(asset, profile) or net < 0.15, (style_id, kind, net)


@pytest.mark.parametrize(
    "style_id",
    [
        "veil-footer",
        "folio-overlap",
        "band-cut",
        "cameo-aperture",
        "type-monument",
    ],
)
def test_golden_boost_beats_penalty(style_id: str) -> None:
    """Each style: best boost net > worst penalty net."""
    boosts = [r for r in _GOLDEN if r[0] == style_id and r[1] == "boost"]
    penalties = [r for r in _GOLDEN if r[0] == style_id and r[1] == "penalty"]
    assert len(boosts) >= 2 and len(penalties) >= 2
    profile = get_profile(style_id)
    best = max(net_style_fit(_asset(fx, fy, extra), profile) for _, _, fx, fy, extra in boosts)
    worst = min(
        net_style_fit(_asset(fx, fy, extra), profile) for _, _, fx, fy, extra in penalties
    )
    assert best > worst, (style_id, best, worst)


def test_style_fit_below_threshold_flags_bad_pair() -> None:
    bad = _asset(0.5, 0.63)
    good = _asset(0.5, 0.32)
    assert style_fit_below_threshold(bad, "band-cut") is True
    assert style_fit_below_threshold(good, "band-cut") is False
