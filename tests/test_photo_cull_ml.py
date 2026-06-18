"""Phase 9 · pyiqa / cull.mode resolution (M30-W2)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from travelogue.config import CullConfig
from travelogue.curation.photo_cull import run_photo_cull
from travelogue.curation.photo_cull_ml import (
    apply_aesthetic_scores,
    pyiqa_available,
    resolve_effective_mode,
    _norm_aesthetic,
)


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


def test_ac_p9_ml_02_keep_ratio_within_rules_delta() -> None:
    """AC-P9-ML-02 · ML 保留率 ≥ rules − 2%（需 pyiqa + ml 模式）。"""
    if not pyiqa_available() or resolve_effective_mode(CullConfig(mode="ml")) != "ml":
        pytest.skip("pyiqa/GPU ml path unavailable")

    n = 100
    rules_cfg = CullConfig(mode="rules", min_keep=15, keep_ratio_floor=0.80)
    ml_cfg = CullConfig(mode="ml", min_keep=15, keep_ratio_floor=0.80)

    def _ratio(assets: list[dict], cfg: CullConfig) -> float:
        run_photo_cull(assets, cfg=cfg)
        eligible = sum(1 for a in assets if a.get("layoutEligible", True))
        return eligible / len(assets)

    base = [
        {
            "id": f"a{i:03d}",
            "type": "image",
            "mediaClass": "photo",
            "quality": {"sharpness": 40.0 + float(i)},
            "layoutEligible": True,
        }
        for i in range(n)
    ]
    rules_ratio = _ratio([dict(a) for a in base], rules_cfg)
    ml_ratio = _ratio([dict(a) for a in base], ml_cfg)
    assert ml_ratio >= rules_ratio - 0.02


def test_cull_score_prefers_aesthetic_when_ml() -> None:
    from travelogue.curation.photo_cull import _cull_score

    cfg = CullConfig(mode="ml")
    low = {"quality": {"sharpness": 200.0, "aestheticScore": 0.1}, "mediaClass": "photo"}
    high = {"quality": {"sharpness": 50.0, "aestheticScore": 0.95}, "mediaClass": "photo"}
    assert _cull_score(high, sharp_lo=0.0, sharp_hi=300.0, use_ml=True, cfg=cfg) > _cull_score(
        low, sharp_lo=0.0, sharp_hi=300.0, use_ml=True, cfg=cfg
    )


def test_apply_aesthetic_scores_uses_persistent_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    img_rel = "assets/a1-w800.webp"
    img_path = tmp_path / img_rel
    img_path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), (120, 120, 120)).save(img_path)
    asset = {
        "id": "a1",
        "type": "image",
        "displayFile": img_rel,
        "contentSig": "sig-a1",
        "quality": {},
    }
    cfg = CullConfig(mode="ml", allow_cpu_ml=True)
    calls = {"n": 0}

    class _FakeOut:
        def __init__(self, values):
            self._values = values

        def detach(self):
            return self

        def flatten(self):
            return self

        def tolist(self):
            return self._values

    class _FakeMetric:
        def __call__(self, tensor):  # noqa: ANN001
            calls["n"] += 1
            batch = int(getattr(tensor, "shape", [1])[0])
            return _FakeOut([0.66] * batch)

    monkeypatch.setattr(
        "travelogue.curation.photo_cull_ml.resolve_effective_mode",
        lambda _cfg: "ml",
    )
    monkeypatch.setattr("travelogue.curation.photo_cull_ml.pyiqa_available", lambda: True)
    monkeypatch.setattr(
        "travelogue.curation.photo_cull_ml._get_metric",
        lambda _cfg: _FakeMetric(),
    )
    ok1 = apply_aesthetic_scores([asset], trip_dir=tmp_path, cfg=cfg)
    assert ok1
    assert calls["n"] == 1
    assert asset.get("quality", {}).get("aestheticScore") == pytest.approx(0.66, abs=1e-4)
    sig = asset["quality"]["aesthetic"]["signals"]
    assert sig["learnedAesthetic"] == pytest.approx(0.66, abs=1e-4)
    assert sig["learnedMetric"] == cfg.aesthetic_metric

    asset2 = {
        "id": "a1",
        "type": "image",
        "displayFile": img_rel,
        "contentSig": "sig-a1",
        "quality": {},
    }
    ok2 = apply_aesthetic_scores([asset2], trip_dir=tmp_path, cfg=cfg)
    assert ok2
    assert calls["n"] == 1
    assert asset2.get("quality", {}).get("aestheticScore") == pytest.approx(0.66, abs=1e-4)


def test_norm_aesthetic_nima_maps_ten_point_scale() -> None:
    assert _norm_aesthetic(2.0, metric_name="nima") == pytest.approx(1.0 / 9.0, abs=1e-6)
    assert _norm_aesthetic(10.0, metric_name="nima") == pytest.approx(1.0, abs=1e-6)
    assert _norm_aesthetic(5.5, metric_name="nima") == pytest.approx(0.5, abs=1e-6)
    assert _norm_aesthetic(0.72, metric_name="nima") == pytest.approx(0.72, abs=1e-6)
