"""AA · stratum blend, portrait lite, MLLM integration tests."""

from __future__ import annotations

from dataclasses import replace

from travelogue.config import AestheticConfig, resolve_learned_blend
from travelogue.curation.aesthetic_learned_eval import grid_search_stratum_blend
from travelogue.curation.aesthetic_score import compute_aesthetic
from travelogue.curation.portrait_lite import portrait_lite_subject_clarity_factor
from travelogue.vision.aesthetic_mllm import build_mllm_shortlist, mllm_cache_key


def _asset(aid: str, *, learned: float = 0.8, rules: float = 0.5, face_count: int = 0):
    dims = {
        "composition": rules,
        "exposure": rules,
        "color": rules,
        "lighting": rules,
        "subjectClarity": rules,
    }
    q: dict = {
        "sharpness": 200,
        "aesthetic": {
            "overall": rules,
            "dims": dims,
            "signals": {"learnedAesthetic": learned},
        },
    }
    if face_count:
        q["faceCount"] = face_count
    asset = {"id": aid, "quality": q, "subjectClass": "person" if face_count else "landscape"}
    if face_count > 1:
        asset["faces"] = [{"bbox": [0, 0, 10, 10]} for _ in range(face_count)]
    elif face_count == 1:
        asset["faces"] = [{"bbox": [0, 0, 10, 10]}]
    return asset


def test_resolve_learned_blend_uses_stratum():
    asset = _asset("a1", face_count=3)
    cfg = AestheticConfig(
        ml_calibrate_blend=0.4,
        use_stratum_blend=True,
        stratum_blends={"group": 0.1, "person": 0.5},
    )
    assert resolve_learned_blend(asset, cfg) == 0.1


def test_resolve_learned_blend_uniform_when_disabled():
    asset = _asset("a1")
    cfg = AestheticConfig(ml_calibrate_blend=0.4, use_stratum_blend=False)
    assert resolve_learned_blend(asset, cfg) == 0.4


def test_portrait_lite_boosts_clear_group():
    asset = _asset("g1", face_count=4)
    asset["quality"]["faceRatio"] = 0.08
    asset["quality"]["sharpness"] = 400
    assert portrait_lite_subject_clarity_factor(asset) > 1.0


def test_portrait_lite_neutral_for_landscape():
    asset = _asset("l1")
    assert portrait_lite_subject_clarity_factor(asset) == 1.0


def test_compute_aesthetic_applies_portrait_lite():
    base = {
        "id": "p1",
        "quality": {"sharpness": 400, "faceCount": 4, "faceRatio": 0.08},
        "subjectClass": "person",
    }
    signals = {
        "dynamicRange": 0.5,
        "midtoneCenter": 0.5,
        "colorHarmony": 0.5,
        "lumaGradient": 0.5,
        "contrast": 0.5,
        "balance": 0.5,
        "subjectContrast": 0.5,
    }
    on = compute_aesthetic(base, signals=signals, cfg=AestheticConfig(portrait_lite_enabled=True))
    off = compute_aesthetic(
        base, signals=signals, cfg=AestheticConfig(portrait_lite_enabled=False)
    )
    assert on["dims"]["subjectClarity"] > off["dims"]["subjectClarity"]


def test_grid_search_stratum_blend_improves_on_uniform():
    assets = {}
    labels = []
    for i in range(12):
        aid = f"g{i}"
        hs = (i % 5) + 1
        rules = 0.35
        learned = hs / 5.0
        assets[aid] = _asset(aid, learned=learned, rules=rules)
        labels.append({"assetId": aid, "humanScore": hs, "stratum": "group"})
    for i in range(5):
        aid = f"p{i}"
        hs = i + 3
        rules = 0.4
        learned = hs / 8.0
        assets[aid] = _asset(aid, learned=learned, rules=rules, face_count=1)
        labels.append({"assetId": aid, "humanScore": hs, "stratum": "person"})
    out = grid_search_stratum_blend(
        assets,
        labels,
        blend_min=0.0,
        blend_max=1.0,
        blend_step=0.2,
        min_samples=3,
    )
    full = out["fullCorpus"]["srcc"]
    uniform = out["uniformBlend"]["srcc"]
    assert full is not None and uniform is not None
    assert "group" in out["recommendedBlends"]
    assert out["recommendedBlends"]["group"] is not None


def test_build_mllm_shortlist_respects_cap():
    assets = [_asset(f"a{i}", learned=0.5 + i * 0.01, rules=0.4 + i * 0.01) for i in range(20)]
    cfg = AestheticConfig(
        ml_calibrate=True,
        mllm=replace(
            AestheticConfig().mllm,
            enabled=True,
            shortlist_k=2,
            max_calls_per_trip=3,
            shortlist_purposes=("cover", "hero"),
        ),
    )
    shortlist = build_mllm_shortlist(assets, cfg=cfg)
    assert len(shortlist) <= 3


def test_build_mllm_shortlist_prefers_profile_strata():
    landscape = _asset("L1", learned=0.65, rules=0.65)
    landscape["subjectClass"] = "landscape"
    person = _asset("P1", learned=0.95, rules=0.95, face_count=1)
    cfg = AestheticConfig(
        ml_calibrate=True,
        mllm=replace(
            AestheticConfig().mllm,
            enabled=True,
            shortlist_k=1,
            max_calls_per_trip=1,
            shortlist_purposes=("cover",),
        ),
    )
    profile = {
        "dominantStratum": "landscape",
        "strata": {"landscape": 0.7, "group": 0.2, "person": 0.1},
    }
    baseline = build_mllm_shortlist([person, landscape], cfg=cfg)
    prioritized = build_mllm_shortlist([person, landscape], cfg=cfg, album_profile=profile)
    assert baseline[0][0] == "P1"
    assert prioritized[0][0] == "L1"


def test_build_mllm_shortlist_portrait_preference_overrides_trip():
    landscape = _asset("L1", learned=0.95, rules=0.95)
    landscape["subjectClass"] = "landscape"
    person = _asset("P1", learned=0.65, rules=0.65, face_count=1)
    cfg = AestheticConfig(
        ml_calibrate=True,
        mllm=replace(
            AestheticConfig().mllm,
            enabled=True,
            shortlist_k=1,
            max_calls_per_trip=1,
            shortlist_purposes=("cover",),
        ),
    )
    trip = {
        "assets": [landscape, person],
        "curation": {
            "stratumPreference": "portrait",
            "albumProfile": {
                "dominantStratum": "landscape",
                "strata": {"landscape": 0.9, "person": 0.1},
            },
        },
    }
    shortlist = build_mllm_shortlist([person, landscape], cfg=cfg, trip=trip)
    assert shortlist[0][0] == "P1"


def test_refresh_portrait_lite_overall_updates_subject_clarity():
    from travelogue.curation.aesthetic_score import refresh_portrait_lite_overall

    asset = {
        "id": "p1",
        "quality": {
            "faceCount": 4,
            "faceRatio": 0.08,
            "sharpness": 400,
            "aesthetic": {
                "overall": 0.5,
                "dims": {
                    "composition": 0.5,
                    "exposure": 0.5,
                    "color": 0.5,
                    "lighting": 0.5,
                    "subjectClarity": 0.5,
                },
                "signals": {},
            },
        },
        "subjectClass": "person",
    }
    cfg = AestheticConfig(portrait_lite_enabled=True)
    assert refresh_portrait_lite_overall(asset, cfg=cfg)
    assert asset["quality"]["aesthetic"]["dims"]["subjectClarity"] > 0.5
    assert asset["quality"]["aesthetic"]["signals"]["portraitLiteFactor"] > 1.0


def test_apply_mllm_oracle_from_labels():
    from travelogue.vision.aesthetic_mllm import apply_mllm_oracle_from_labels

    asset = _asset("a1", learned=0.7, rules=0.5)
    cfg = AestheticConfig(
        ml_calibrate=True,
        mllm=replace(
            AestheticConfig().mllm,
            enabled=True,
            shortlist_k=1,
            max_calls_per_trip=5,
            shortlist_purposes=("cover",),
        ),
    )
    rep = apply_mllm_oracle_from_labels(
        [asset],
        [{"assetId": "a1", "humanScore": 5}],
        cfg=cfg,
    )
    assert rep["scored"] == 1
    assert asset["quality"]["aesthetic"]["signals"]["mllmScore"] == 1.0


def test_mllm_cache_key_uses_content_sig():
    asset = {"id": "x", "contentSig": "abc123"}
    assert "sig:abc123" in mllm_cache_key(asset, model="qwen-vl-max", rubric="universal")


def test_purpose_overall_skips_mllm_when_purpose_not_shortlisted():
    from travelogue.curation.aesthetic_score import purpose_overall

    asset = _asset("a1", learned=0.7, rules=0.5)
    asset["quality"]["aesthetic"]["signals"]["mllmScore"] = 1.0
    cfg = AestheticConfig(
        ml_calibrate=True,
        use_purpose_presets=True,
        mllm=replace(AestheticConfig().mllm, enabled=True, blend=0.45, shortlist_purposes=("cover",)),
    )
    cover = purpose_overall(asset, "cover", cfg=cfg)
    hero = purpose_overall(asset, "hero", cfg=cfg)
    assert cover is not None and hero is not None
    assert cover > hero
