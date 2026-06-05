"""PA-T04 / PA-T05 · Layer 1 aesthetic synthesiser unit tests."""

from __future__ import annotations

from PIL import Image

from travelogue.config import AestheticConfig
from travelogue.curation.aesthetic_score import (
    AESTHETIC_VERSION,
    build_aesthetic_explain,
    compute_aesthetic,
    compute_aesthetic_signals,
    load_signal_cache,
    normalize_sharpness,
    save_signal_cache,
)


def _full_signals() -> dict[str, float]:
    return {
        "dynamicRange": 0.7,
        "clipHighRatio": 0.02,
        "clipLowRatio": 0.01,
        "midtoneCenter": 0.9,
        "colorHarmony": 0.8,
        "lumaGradient": 0.5,
        "contrast": 0.5,
        "balance": 0.8,
        "subjectContrast": 0.6,
    }


def _asset(**overrides) -> dict:
    base = {
        "id": "asset-001",
        "dominantTone": "#3f7fbf",
        "salientBox": {"x": 0.3, "y": 0.3, "w": 0.25, "h": 0.25},
        "quality": {"sharpness": 300.0, "meanLuma": 0.5},
    }
    base.update(overrides)
    return base


def test_normalize_sharpness_monotonic():
    assert normalize_sharpness(0.0) == 0.0
    assert normalize_sharpness(150.0) == 0.5
    assert normalize_sharpness(900.0) > normalize_sharpness(150.0)
    assert 0.0 <= normalize_sharpness(1e9) <= 1.0


def test_compute_aesthetic_dims_in_range():
    block = compute_aesthetic(_asset(), signals=_full_signals())
    assert block["version"] == AESTHETIC_VERSION
    assert block["source"] == "rules"
    for value in block["dims"].values():
        assert 0.0 <= value <= 1.0
    assert 0.0 <= block["overall"] <= 1.0
    assert 0.0 <= block["confidence"] <= 1.0
    assert block["critique"] is None


def test_overall_matches_weighted_dims():
    cfg = AestheticConfig()
    block = compute_aesthetic(_asset(), signals=_full_signals(), cfg=cfg)
    weights = cfg.weights.as_dim_map()
    dims = block["dims"]
    expected = sum(weights[k] * dims[k] for k in dims) / sum(weights.values())
    assert abs(block["overall"] - round(expected, 4)) < 1e-6


def test_fail_open_without_signals():
    block = compute_aesthetic(_asset(), signals=None)
    for value in block["dims"].values():
        assert 0.0 <= value <= 1.0
    # No image signals → confidence is heavily discounted but never crashes.
    assert block["confidence"] < 0.6


def test_confidence_full_signals_higher_than_empty():
    full = compute_aesthetic(_asset(), signals=_full_signals())
    empty = compute_aesthetic(_asset(), signals=None)
    assert full["confidence"] > empty["confidence"]


def test_screenshot_media_class_lowers_confidence():
    normal = compute_aesthetic(_asset(), signals=_full_signals())
    shot = compute_aesthetic(
        _asset(mediaClass="screenshot"), signals=_full_signals()
    )
    assert shot["confidence"] < normal["confidence"]


def test_extreme_exposure_lowers_confidence():
    blown = dict(_full_signals())
    blown["clipHighRatio"] = 0.6
    blown["clipLowRatio"] = 0.1
    block = compute_aesthetic(_asset(), signals=blown)
    normal = compute_aesthetic(_asset(), signals=_full_signals())
    assert block["confidence"] < normal["confidence"]


def test_build_explain_top_dims_sorted():
    asset = _asset()
    asset.setdefault("quality", {})["aesthetic"] = compute_aesthetic(
        asset, signals=_full_signals()
    )
    explain = build_aesthetic_explain(asset, limit=3)
    assert len(explain) == 3
    scores = [item["score"] for item in explain]
    assert scores == sorted(scores, reverse=True)


def test_signals_from_real_image_have_keys():
    img = Image.new("RGB", (64, 64), (90, 140, 60))
    signals = compute_aesthetic_signals(img, _asset())
    for key in ("dynamicRange", "midtoneCenter", "lumaGradient", "contrast", "balance", "colorHarmony"):
        assert key in signals
        assert 0.0 <= float(signals[key]) <= 1.0


def test_pipeline_deterministic():
    img = Image.new("RGB", (64, 64), (90, 140, 60))
    asset = _asset()
    a = compute_aesthetic(asset, signals=compute_aesthetic_signals(img, asset))
    b = compute_aesthetic(asset, signals=compute_aesthetic_signals(img, asset))
    assert a == b


def test_signal_cache_round_trip(tmp_path):
    cache = {"sig:abc": {"version": AESTHETIC_VERSION, "signals": _full_signals()}}
    save_signal_cache(tmp_path, cache)
    loaded = load_signal_cache(tmp_path)
    assert loaded == cache


def test_mean_luma_compat_reading():
    # quality.meanLuma takes precedence; color.meanLuma is the documented fallback.
    img = Image.new("RGB", (32, 32), (10, 10, 10))
    asset = {"id": "a", "color": {"meanLuma": 0.5}}
    signals = compute_aesthetic_signals(img, asset)
    # midtoneCenter computed from the fallback meanLuma=0.5 → fully centred.
    assert signals["midtoneCenter"] == 1.0
