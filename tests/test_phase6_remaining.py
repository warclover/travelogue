"""Phase 6 remaining module tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from travelogue.curation.breath_pauses import arc_breath_interval, insert_breath_screens_in_chapters
from travelogue.curation.geo_events import GeoSegment
from travelogue.curation.phase6_rollout import (
    p5_rollback_patch,
    phase6_feature_snapshot,
    phase6_in_rollout_cohort,
    rollout_bucket,
)
from travelogue.curation.scene_subsegments import apply_scene_subsegments
from travelogue.config import AppConfig, Phase6ObservabilityConfig, Phase6RolloutConfig
from travelogue.vision.cache import plan_embedding_refresh, prepare_scene_embeddings, save_embedding_cache
from travelogue.vision.clip_encoder import ClipEncoder


def test_apply_scene_subsegments_splits_by_cluster() -> None:
    segment = GeoSegment(
        id="evt-01",
        name="东京",
        start_date=__import__("datetime").date(2025, 5, 1),
        end_date=__import__("datetime").date(2025, 5, 1),
        location="东京",
        asset_ids=["a1", "a2", "a3", "a4", "a5", "a6"],
    )
    assets_by_id = {
        "a1": {"id": "a1", "sceneClusterId": 0, "takenAt": "2025-05-01T09:00:00Z", "place": {"city": "东京"}},
        "a2": {"id": "a2", "sceneClusterId": 0, "takenAt": "2025-05-01T10:00:00Z", "place": {"city": "东京"}},
        "a3": {"id": "a3", "sceneClusterId": 0, "takenAt": "2025-05-01T11:00:00Z", "place": {"city": "东京"}},
        "a4": {"id": "a4", "sceneClusterId": 1, "takenAt": "2025-05-01T12:00:00Z", "place": {"city": "东京"}},
        "a5": {"id": "a5", "sceneClusterId": 1, "takenAt": "2025-05-01T13:00:00Z", "place": {"city": "东京"}},
        "a6": {"id": "a6", "sceneClusterId": 1, "takenAt": "2025-05-01T14:00:00Z", "place": {"city": "东京"}},
    }
    refined, meta = apply_scene_subsegments([segment], assets_by_id, min_photos_per_sub=3)
    assert len(refined) == 2
    assert meta["parentSplitCount"] == 1
    assert meta["breakpoints"]


def test_plan_prune_on_delete_only(tmp_path: Path) -> None:
    from travelogue.vision.clip_encoder import HEURISTIC_MODEL_V2, HEURISTIC_V2_DIM

    ids = [f"a{i:02d}" for i in range(10)]
    vectors = np.random.RandomState(0).rand(len(ids), HEURISTIC_V2_DIM).astype(np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=ids,
        vectors=vectors,
        source="heuristic",
        model=HEURISTIC_MODEL_V2,
    )
    kept = ids[:8]
    plan = plan_embedding_refresh(tmp_path, kept)
    assert plan.mode == "prune"
    assert not plan.new_ids
    assert len(plan.removed_ids) == 2


def test_prepare_scene_embeddings_prune_without_reembed(tmp_path: Path, monkeypatch) -> None:
    base_assets = [
        {
            "id": f"a{i:02d}",
            "type": "image",
            "width": 1200,
            "height": 800,
            "sharpness": 0.5,
            "subjectBucket": "landscape",
        }
        for i in range(6)
    ]
    ids = [a["id"] for a in base_assets]
    from travelogue.vision.clip_encoder import HEURISTIC_MODEL_V2, HEURISTIC_V2_DIM

    vectors = np.random.RandomState(1).rand(len(ids), HEURISTIC_V2_DIM).astype(np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=ids,
        vectors=vectors,
        source="heuristic",
        model=HEURISTIC_MODEL_V2,
    )

    calls = {"n": 0}
    real_embed = ClipEncoder.embed_assets

    def _spy(self, assets, **kwargs):
        calls["n"] += 1
        return real_embed(self, assets, **kwargs)

    monkeypatch.setattr(ClipEncoder, "embed_assets", _spy)
    kept_assets = base_assets[:4]
    embed, plan = prepare_scene_embeddings(tmp_path, kept_assets, ClipEncoder(), deterministic=True)
    assert plan.mode == "prune"
    assert calls["n"] == 0
    assert embed.asset_ids == [a["id"] for a in kept_assets]


def test_arc_breath_interval_peak_shorter() -> None:
    assert arc_breath_interval("peak") < arc_breath_interval("setup")


def test_arc_driven_breath_inserts_with_peak_label() -> None:
    chapters = [
        {
            "id": "ch-1",
            "screens": [
                {"screenId": "s1", "patternId": "screen-portrait-1", "arcSegment": "peak", "slots": [{"assetId": "a1"}]},
                {"screenId": "s2", "patternId": "screen-portrait-1", "arcSegment": "peak", "slots": [{"assetId": "a2"}]},
                {"screenId": "s3", "patternId": "screen-portrait-1", "arcSegment": "peak", "slots": [{"assetId": "a3"}]},
            ],
        }
    ]
    n = insert_breath_screens_in_chapters(chapters, arc_driven=True)
    assert n >= 1
    breath = [sc for sc in chapters[0]["screens"] if sc.get("patternId") == "screen-breath-pause"]
    assert breath
    assert breath[0].get("breathLabel") == "—"


def test_p5_rollback_patch_keys() -> None:
    patch = p5_rollback_patch()
    assert patch["clustering"]["scene"]["algorithm"] == "dbscan"
    assert patch["curate"]["layout"]["enable_mmr_diversity"] is False


def test_phase6_feature_snapshot() -> None:
    snap = phase6_feature_snapshot(AppConfig())
    assert "sceneAlgorithm" in snap
    assert snap["enableGravityBalance"] is True


def test_rollout_bucket_stable() -> None:
    a = rollout_bucket("kyoto-2025", cohort_salt="salt", traffic_percent=10.0)
    b = rollout_bucket("kyoto-2025", cohort_salt="salt", traffic_percent=10.0)
    assert a == b
    assert 0 <= a <= 99


def test_phase6_in_rollout_cohort_off_means_full_p6() -> None:
    cfg = AppConfig(
        phase6=Phase6ObservabilityConfig(
            rollout=Phase6RolloutConfig(stage="off", traffic_percent=0.0),
        )
    )
    assert phase6_in_rollout_cohort("trip-a", cfg) is True
    assert phase6_in_rollout_cohort("", cfg) is False
    assert phase6_in_rollout_cohort("  ", cfg) is False


def test_phase6_in_rollout_cohort_allowlist_and_bucket() -> None:
    cfg = AppConfig(
        phase6=Phase6ObservabilityConfig(
            rollout=Phase6RolloutConfig(
                stage="G1",
                traffic_percent=10.0,
                cohort_salt="test-salt",
                allowlist_trip_ids=("always-p6",),
                blocklist_trip_ids=("never-p6",),
            )
        )
    )
    assert phase6_in_rollout_cohort("always-p6", cfg) is True
    assert phase6_in_rollout_cohort("never-p6", cfg) is False
    in_count = sum(
        1
        for i in range(200)
        if phase6_in_rollout_cohort(f"trip-{i}", cfg)
    )
    assert 10 <= in_count <= 30
