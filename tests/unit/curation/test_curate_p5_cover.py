"""P5-C2/C3 cover and small-album curation tests."""

from __future__ import annotations

from travelogue.curation.bucket_planning import normalize_bucket_counts
from travelogue.curation.curate_scoring import cover_score


def _asset(aid: str, *, w: int = 1200, h: int = 1600, **extra) -> dict:
    a = {
        "id": aid,
        "type": "image",
        "width": w,
        "height": h,
        "quality": {"sharpness": 100.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    a.update(extra)
    return a


def test_face_tag_lowers_mobile_cover_score() -> None:
    """Non portrait-dominant pool (1/5 tagged) — person demote applies under v2."""
    landscape = [_asset(f"land{i}", w=2400, h=1350, tags=["landscape"]) for i in range(4)]
    portrait_clean = _asset("clean", w=1200, h=1800)
    portrait_face = _asset("face", w=1200, h=1800, tags=["face", "person"])
    pool = landscape + [portrait_clean, portrait_face]
    assert cover_score(portrait_clean, "mobile", pool=pool) > cover_score(
        portrait_face, "mobile", pool=pool
    )


def test_dominant_tone_saturation_boosts_cover() -> None:
    vivid = _asset("vivid", w=1200, h=1800, dominantTone="#4488cc")
    dull = _asset("dull", w=1200, h=1800, dominantTone="#888888")
    assert cover_score(vivid, "mobile") > cover_score(dull, "mobile")


def test_small_album_normalizes_max_chapters() -> None:
    buckets = [["a1", "a2"], ["a3", "a4"], ["a5", "a6"], ["a7", "a8"]]
    norm = normalize_bucket_counts(buckets, None, max_chapters=3, min_bucket_size=2)
    assert len(norm.buckets) <= 3
