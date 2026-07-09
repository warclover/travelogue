"""PRD Sprint-2 gates: Kendall tau, delta coverId, burst, explain (A-M1/M4/M7, B-M5)."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.curation.cover_scoring_v2 import build_cover_explain_v2, cover_logit_v2
from travelogue.curation.curate_scoring import pick_cover_asset_id, sort_bucket_asset_ids

_KENDALL_FIXTURE = (
    Path(__file__).resolve().parents[2] / "fixtures" / "cover_v2_kendall_albums.json"
)


def _kendall_tau(rank_a: list[str], rank_b: list[str]) -> float:
    common = [x for x in rank_a if x in rank_b]
    n = len(common)
    if n < 2:
        return 1.0
    pos_a = {aid: i for i, aid in enumerate(rank_a)}
    pos_b = {aid: i for i, aid in enumerate(rank_b)}
    concordant = discordant = 0
    for i in range(n):
        for j in range(i + 1, n):
            da = pos_a[common[i]] - pos_a[common[j]]
            db = pos_b[common[i]] - pos_b[common[j]]
            if da * db > 0:
                concordant += 1
            elif da * db < 0:
                discordant += 1
    denom = concordant + discordant
    return 1.0 if denom == 0 else (concordant - discordant) / denom


def _rank_cover_ids(assets: list[dict], *, export_layout: str, version: str) -> list[str]:
    from travelogue.curation.curate_scoring import score_ranked_cover_ids

    rows = score_ranked_cover_ids(
        assets,
        export_layout=export_layout,
        scoring_version=version,
        limit=len(assets),
    )
    return [str(row["assetId"]) for row in rows]


def _asset(aid: str, **extra) -> dict:
    base = {
        "id": aid,
        "type": "image",
        "width": 1200,
        "height": 1800,
        "quality": {"sharpness": 100.0},
        "mediaClass": "photo",
        "dateConfidence": "high",
        "takenAt": "2025-04-01T10:00:00Z",
    }
    base.update(extra)
    return base


def test_b_m5_burst_group_picks_sharpest_frame() -> None:
    assets_by_id = {
        "b1": _asset("b1", quality={"sharpness": 50}, burstGroupId="g1", takenAt="2025-04-01T10:00:00Z"),
        "b2": _asset("b2", quality={"sharpness": 500}, burstGroupId="g1", takenAt="2025-04-01T10:01:00Z"),
        "solo": _asset("solo", takenAt="2025-04-01T11:00:00Z"),
    }
    ordered = sort_bucket_asset_ids(["b1", "b2", "solo"], assets_by_id)
    assert ordered.index("b2") < ordered.index("b1")
    assert ordered == ["b2", "b1", "solo"]


def test_b_m5_burst_winner_stable_when_sharpness_order_preserved() -> None:
    """Rank order unchanged → same burst representative (v1/v2 ingest may rescale values)."""
    frames = [
        _asset("f1", quality={"sharpness": 80}, burstGroupId="burst-a"),
        _asset("f2", quality={"sharpness": 200}, burstGroupId="burst-a"),
        _asset("f3", quality={"sharpness": 120}, burstGroupId="burst-a"),
    ]
    scaled = []
    for f in frames:
        s = float(f["quality"]["sharpness"])
        scaled.append(
            {
                **f,
                "quality": {
                    **f["quality"],
                    "sharpness": s * 0.4,
                    "sharpnessLegacy": s,
                    "sharpnessVersion": "v2",
                },
            }
        )
    by_id_orig = {a["id"]: a for a in frames}
    by_id_scaled = {a["id"]: a for a in scaled}
    ids = [f["id"] for f in frames]
    orig = sort_bucket_asset_ids(ids, by_id_orig)
    after = sort_bucket_asset_ids(ids, by_id_scaled)
    assert orig == after


def test_a_m4_explain_top4_reconstructs_logit() -> None:
    pool = [
        _asset("top", quality={"sharpness": 400}, dominantTone="#4488cc", meanLuma=0.55, focalPoint={"x": 0.33, "y": 0.33}),
        _asset("mid", quality={"sharpness": 200}, dominantTone="#888888", meanLuma=0.4),
        _asset("low", quality={"sharpness": 80}),
    ]
    asset = pool[0]
    logit = cover_logit_v2(asset, "mobile", pool)
    assert logit > 0
    explain = build_cover_explain_v2(asset, "mobile", pool, limit=4)
    contrib_sum = sum(abs(float(row["contribution"])) for row in explain)
    assert contrib_sum >= 0.65 * logit, (contrib_sum, logit, explain)


def test_a_m1_kendall_tau_on_synthetic_albums() -> None:
    data = json.loads(_KENDALL_FIXTURE.read_text(encoding="utf-8"))
    taus: list[float] = []
    for album in data["albums"]:
        assets = album["assets"]
        layout = album.get("exportLayout", "mobile")
        v1 = _rank_cover_ids(assets, export_layout=layout, version="v1")
        v2 = _rank_cover_ids(assets, export_layout=layout, version="v2")
        taus.append(_kendall_tau(v1, v2))
    assert taus, "no kendall albums"
    mean_tau = sum(taus) / len(taus)
    assert mean_tau >= 0.85, {"mean": mean_tau, "per_album": taus}


def test_v2_demotes_low_date_confidence_vs_v1() -> None:
    """Expected v1/v2 divergence: CV2-04 behavior (not counted toward Kendall mean)."""
    assets = [
        _asset("good", quality={"sharpness": 250}, dateConfidence="high"),
        _asset("lowd", quality={"sharpness": 400}, dateConfidence="low"),
    ]
    v1_top = _rank_cover_ids(assets, export_layout="mobile", version="v1")[0]
    v2_top = _rank_cover_ids(assets, export_layout="mobile", version="v2")[0]
    assert v1_top == "lowd"
    assert v2_top == "good"


def test_a_m7_delta_cover_id_at_most_three_per_ten() -> None:
    data = json.loads(_KENDALL_FIXTURE.read_text(encoding="utf-8"))
    albums = data["albums"]
    assert len(albums) >= 10
    changes = 0
    for album in albums[:10]:
        assets = album["assets"]
        layout = album.get("exportLayout", "mobile")
        v1_id = pick_cover_asset_id(assets, export_layout=layout, scoring_version="v1")
        v2_id = pick_cover_asset_id(assets, export_layout=layout, scoring_version="v2")
        if v1_id != v2_id:
            changes += 1
    assert changes <= 3, f"cover changed in {changes}/10 albums"
