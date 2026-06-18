"""GAP-08 · MLLM cover shortlist tie-break in cover logit."""

from __future__ import annotations

from travelogue.curation.cover_scoring_v2 import cover_logit_v2


def _landscape(aid: str, *, aesthetic: float, mllm: float | None = None) -> dict:
    sig: dict = {}
    if mllm is not None:
        sig["mllmScore"] = mllm
        sig["mllmShortlist"] = "cover"
    return {
        "id": aid,
        "type": "image",
        "width": 3200,
        "height": 1800,
        "aspectKind": "landscape",
        "quality": {
            "sharpness": 200.0,
            "meanLuma": 0.5,
            "aesthetic": {
                "overall": aesthetic,
                "dims": {"composition": aesthetic, "subjectClarity": aesthetic},
                "signals": sig,
            },
        },
        "dominantTone": "#4488cc",
    }


def test_mllm_cover_shortlist_boosts_logit():
    plain = _landscape("plain", aesthetic=0.55)
    boosted = _landscape("boosted", aesthetic=0.55, mllm=0.92)
    pool = [plain, boosted]
    plain_logit = cover_logit_v2(plain, "web", pool, aesthetic_enabled=True)
    boosted_logit = cover_logit_v2(boosted, "web", pool, aesthetic_enabled=True)
    assert boosted_logit > plain_logit


def test_mllm_boost_only_for_cover_shortlist():
    asset = _landscape("x", aesthetic=0.6)
    asset["quality"]["aesthetic"]["signals"] = {"mllmScore": 0.95, "mllmShortlist": "hero"}
    pool = [asset]
    with_hero = cover_logit_v2(asset, "web", pool, aesthetic_enabled=True)
    asset["quality"]["aesthetic"]["signals"]["mllmShortlist"] = "cover"
    with_cover = cover_logit_v2(asset, "web", pool, aesthetic_enabled=True)
    assert with_cover > with_hero
