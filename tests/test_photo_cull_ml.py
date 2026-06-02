"""Phase 9 · pyiqa / cull.mode resolution (M30-W2)."""

from __future__ import annotations

from travelogue.config import CullConfig
from travelogue.curation.photo_cull import run_photo_cull
from travelogue.curation.photo_cull_ml import pyiqa_available, resolve_effective_mode


def test_resolve_mode_rules_default() -> None:
    cfg = CullConfig(mode="rules")
    assert resolve_effective_mode(cfg) == "rules"


def test_resolve_mode_auto_without_pyiqa_falls_back() -> None:
    cfg = CullConfig(mode="auto", allow_cpu_ml=False)
    if pyiqa_available():
        return
    assert resolve_effective_mode(cfg) == "rules"


def test_run_cull_ml_mode_without_pyiqa_uses_rules() -> None:
    cfg = CullConfig(mode="ml", min_keep=1, keep_ratio_floor=0.0)
    assets = [
        {
            "id": "a1",
            "type": "image",
            "mediaClass": "photo",
            "quality": {"sharpness": 100.0},
            "layoutEligible": True,
        }
    ]
    summary = run_photo_cull(assets, cfg=cfg)
    if pyiqa_available():
        return
    assert summary["mode"] == "rules"


def test_cull_score_prefers_aesthetic_when_ml() -> None:
    from travelogue.curation.photo_cull import _cull_score

    low = {"quality": {"sharpness": 200.0, "aestheticScore": 0.1}, "mediaClass": "photo"}
    high = {"quality": {"sharpness": 50.0, "aestheticScore": 0.95}, "mediaClass": "photo"}
    assert _cull_score(high, sharp_lo=0.0, sharp_hi=300.0, use_ml=True) > _cull_score(
        low, sharp_lo=0.0, sharp_hi=300.0, use_ml=True
    )
