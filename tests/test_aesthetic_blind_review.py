"""AA · aesthetic blind review sampling + SRCC."""

from __future__ import annotations

from travelogue.curation.aesthetic_blind_review import (
    build_review_row,
    init_labels_from_export,
    normalize_human_score,
    review_stratum_for_asset,
    sample_assets_for_review,
    shuffle_blind_rows,
    srcc_report,
)


def _asset(
    aid: str,
    *,
    subject_class: str = "landscape",
    face_count: int = 0,
    faces: list | None = None,
    width: int = 3200,
    height: int = 2133,
    overall: float = 0.5,
):
    q: dict = {
        "sharpness": 100,
        "aesthetic": {
            "overall": overall,
            "dims": {
                "composition": overall,
                "exposure": overall,
                "color": overall,
                "lighting": overall,
                "subjectClarity": overall,
            },
        },
    }
    if face_count and not faces:
        q["faceCount"] = face_count
    entry: dict = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": width,
        "height": height,
        "aspectKind": "landscape" if width > height else "portrait",
        "subjectClass": subject_class,
        "quality": q,
    }
    if faces is not None:
        entry["faces"] = faces
    return entry


def test_review_stratum_person_vs_group():
    one = _asset("a", subject_class="person", faces=[{"w": 0.1, "h": 0.1}])
    many = _asset(
        "b",
        subject_class="person",
        faces=[{"w": 0.1, "h": 0.1}, {"w": 0.1, "h": 0.1}],
    )
    assert review_stratum_for_asset(one) == "person"
    assert review_stratum_for_asset(many) == "group"


def test_review_stratum_ignores_stale_quality_face_count_on_landscape():
    """Safari/scenery false-positive faceCount must not force group."""
    stale = _asset("safari", subject_class="general", face_count=12, width=3200, height=2133)
    assert review_stratum_for_asset(stale) == "landscape"


def test_sample_respects_target_and_strata():
    assets = []
    for i in range(30):
        assets.append(
            _asset(
                f"p{i}",
                subject_class="person",
                faces=[{"w": 0.1, "h": 0.1}],
                width=900,
                height=1600,
            )
        )
    for i in range(30):
        assets.append(_asset(f"l{i}", subject_class="landscape"))
    for i in range(20):
        assets.append(_asset(f"f{i}", subject_class="food", width=900, height=900))
    picked = sample_assets_for_review(
        assets,
        target_n=40,
        strata_quotas={"person": 15, "landscape": 15, "food": 10},
        seed=7,
    )
    assert len(picked) == 40
    strata = {review_stratum_for_asset(a) for a in picked}
    assert "person" in strata
    assert "landscape" in strata


def test_shuffle_blind_rows_changes_display_order():
    rows = [{"assetId": "a", "displayOrder": 1}, {"assetId": "b", "displayOrder": 2}]
    shuffled = shuffle_blind_rows(rows, seed=99)
    orders = [r["displayOrder"] for r in shuffled]
    assert orders == [1, 2]
    ids = [r["assetId"] for r in shuffled]
    assert set(ids) == {"a", "b"}


def test_normalize_human_score_likert():
    assert normalize_human_score(5) == 1.0
    assert normalize_human_score(1) == 0.0
    assert normalize_human_score(3) == 0.5
    assert normalize_human_score(0.6) == 0.6
    assert normalize_human_score(1.0) == 1.0  # merged v3 [0,1] · not Likert 1


def test_srcc_report_by_stratum():
    rows = [
        {"humanScore": 1, "predictedOverall": 0.2, "stratum": "person"},
        {"humanScore": 3, "predictedOverall": 0.5, "stratum": "person"},
        {"humanScore": 5, "predictedOverall": 0.9, "stratum": "person"},
        {"humanScore": 2, "predictedOverall": 0.3, "stratum": "landscape"},
        {"humanScore": 4, "predictedOverall": 0.7, "stratum": "landscape"},
        {"humanScore": 5, "predictedOverall": 0.85, "stratum": "landscape"},
    ]
    rep = srcc_report(rows, by_stratum=True)
    assert rep["sampleCount"] == 6
    assert rep["srcc"] is not None
    assert rep["srcc"] > 0.95
    assert "person" in rep["byStratum"]
    assert rep["byStratum"]["person"]["sampleCount"] == 3


def test_init_labels_from_export():
    export = {
        "exportedAt": "2026-01-01T00:00:00+00:00",
        "rows": [
            {
                "assetId": "x",
                "predictedOverall": 0.7,
                "stratum": "person",
                "defectTags": ["closed_eyes"],
            }
        ],
    }
    labels = init_labels_from_export(export)
    assert labels["rows"][0]["assetId"] == "x"
    assert labels["rows"][0]["humanScore"] is None
    assert labels["rows"][0]["defectTags"] == ["closed_eyes"]
    assert labels["frozen"] is False


def test_build_blind_review_html_contains_rows():
    from travelogue.curation.aesthetic_blind_review import build_blind_review_html

    export = {
        "exportedAt": "t",
        "sampleCount": 1,
        "seed": 1,
        "rows": [
            {
                "displayOrder": 1,
                "assetId": "a1",
                "tripId": "demo",
                "displayFile": "assets/a.webp",
                "stratum": "person",
                "predictedOverall": 0.5,
            }
        ],
    }
    html = build_blind_review_html(export, title="test")
    assert "a1" in html
    assert "assets/a.webp" in html
    assert "defectPick" in html
    assert "closed_eyes" in html
    assert "predictedOverall" not in html.split("<body>")[1].split("review-data")[0]


def test_build_review_row_includes_defect_tags_default():
    asset = _asset("p1", subject_class="person", faces=[{"w": 0.1, "h": 0.1}])
    row = build_review_row(asset, trip_id="demo", trip_dir="trips/demo", display_order=1)
    assert row["defectTags"] == []


def test_build_review_row_stratum_override():
    asset = _asset("f1", subject_class="landscape", width=4000, height=3000)
    row = build_review_row(
        asset,
        trip_id="demo-food",
        trip_dir="trips/demo-food",
        display_order=1,
        stratum_override="food",
    )
    assert row["stratum"] == "food"
    assert row["stratumAuto"] == "landscape"
