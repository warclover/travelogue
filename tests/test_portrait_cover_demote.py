"""P3-3 · portrait closed-eye penalty in cover scoring."""

from __future__ import annotations

from travelogue.curation.cover_scoring_v2 import cover_logit_v2, extract_cover_features


def _person_asset(**extra) -> dict:
    base = {
        "id": "p1",
        "type": "image",
        "width": 1200,
        "height": 1800,
        "tags": ["person", "face"],
        "quality": {
            "sharpness": 300.0,
            "portrait": {
                "version": "pc-v1",
                "eyesOpenScore": 0.9,
                "faceSharpness": 800.0,
                "confidence": 0.7,
            },
        },
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    base.update(extra)
    return base


def test_portrait_closed_eyes_lowers_cover_person_feature():
    open_eyes = _person_asset(id="open")
    closed = _person_asset(
        id="closed",
        quality={
            "sharpness": 300.0,
            "portrait": {
                "version": "pc-v1",
                "eyesOpenScore": 0.12,
                "faceSharpness": 800.0,
                "confidence": 0.7,
            },
        },
    )
    pool = [open_eyes, closed]
    open_feat = extract_cover_features(open_eyes, "mobile", pool)["person"]
    closed_feat = extract_cover_features(closed, "mobile", pool)["person"]
    assert closed_feat < open_feat
    assert cover_logit_v2(open_eyes, "mobile", pool) > cover_logit_v2(closed, "mobile", pool)


def test_no_portrait_signal_keeps_person_feature_unchanged():
    plain = _person_asset(id="plain", quality={"sharpness": 300.0})
    pool = [plain]
    assert extract_cover_features(plain, "mobile", pool)["person"] > 0.7


def test_portrait_blur_face_lowers_cover_person_feature():
    sharp = _person_asset(id="sharp")
    blurry = _person_asset(
        id="blurry",
        quality={
            "sharpness": 300.0,
            "portrait": {
                "version": "pc-v1",
                "eyesOpenScore": 0.9,
                "faceSharpness": 40.0,
                "confidence": 0.7,
            },
        },
    )
    pool = [sharp, blurry]
    sharp_feat = extract_cover_features(sharp, "mobile", pool)["person"]
    blur_feat = extract_cover_features(blurry, "mobile", pool)["person"]
    assert blur_feat < sharp_feat


def test_hero_logit_penalizes_group_closed_eyes():
    from travelogue.curation.cover_scoring_v2 import hero_logit_v2

    group_ok = {
        "id": "g1",
        "type": "image",
        "width": 3200,
        "height": 2133,
        "tags": ["person", "face"],
        "faces": [{"bbox": [0, 0, 10, 10]}, {"bbox": [20, 0, 10, 10]}],
        "quality": {
            "sharpness": 400.0,
            "portrait": {
                "eyesOpenScore": 0.85,
                "faceSharpness": 900.0,
                "confidence": 0.7,
            },
        },
        "mediaClass": "photo",
        "dateConfidence": "high",
    }
    group_bad = dict(group_ok)
    group_bad["id"] = "g2"
    group_bad["quality"] = {
        "sharpness": 400.0,
        "portrait": {
            "eyesOpenScore": 0.1,
            "faceSharpness": 900.0,
            "confidence": 0.7,
        },
    }
    pool = [group_ok, group_bad]
    assert hero_logit_v2(group_ok, pool) > hero_logit_v2(group_bad, pool)
