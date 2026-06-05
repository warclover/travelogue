"""Phase 7 incremental embed modes: append / delete / replace (P7-G6 · AC-P7-03)."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from travelogue.vision.cache import (
    compute_change_ratio,
    plan_embedding_refresh,
    prepare_scene_embeddings,
    save_embedding_cache,
)
from travelogue.vision.clip_encoder import HEURISTIC_MODEL_V2, HEURISTIC_V2_DIM, ClipEncoder


def _assets(n: int, *, prefix: str = "a") -> list[dict]:
    return [
        {
            "id": f"{prefix}{i:02d}",
            "type": "image",
            "width": 1200,
            "height": 800,
            "sharpness": 0.5 + i * 0.01,
            "subjectBucket": "landscape" if i % 2 == 0 else "food",
        }
        for i in range(n)
    ]


def test_incremental_append_mode(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision import clip_encoder as mod

    monkeypatch.setattr(mod, "clip_torch_available", lambda: False)
    base = _assets(100)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(0).rand(len(ids), HEURISTIC_V2_DIM).astype(np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=ids,
        vectors=vectors,
        source="heuristic",
        model=HEURISTIC_MODEL_V2,
    )

    appended = base + _assets(5, prefix="n")
    new_ids = [a["id"] for a in appended]
    plan = plan_embedding_refresh(tmp_path, new_ids)
    assert plan.mode == "incremental"
    assert len(plan.new_ids) == 5

    enc = ClipEncoder()
    embed, out_plan = prepare_scene_embeddings(tmp_path, appended, enc, deterministic=True)
    assert out_plan.mode == "incremental"
    assert embed.asset_ids == new_ids


def test_incremental_delete_prune_mode(tmp_path: Path) -> None:
    base = _assets(100)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(1).rand(len(ids), HEURISTIC_V2_DIM).astype(np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=ids,
        vectors=vectors,
        source="heuristic",
        model=HEURISTIC_MODEL_V2,
    )

    kept = base[:90]
    kept_ids = [a["id"] for a in kept]
    plan = plan_embedding_refresh(tmp_path, kept_ids)
    assert plan.mode == "prune"
    assert not plan.new_ids
    assert len(plan.removed_ids) == 10

    enc = ClipEncoder()
    embed, out_plan = prepare_scene_embeddings(tmp_path, kept, enc, deterministic=True)
    assert out_plan.mode == "prune"
    assert embed.asset_ids == kept_ids


def test_incremental_replace_triggers_full_when_large_delta(tmp_path: Path) -> None:
    base = _assets(100)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(2).rand(len(ids), 8).astype(np.float32)
    save_embedding_cache(tmp_path, asset_ids=ids, vectors=vectors, source="heuristic", model="h1")

    # Replace 35% of assets → full recluster threshold (30%)
    kept = base[:65]
    replaced = _assets(35, prefix="x")
    mixed = kept + replaced
    mixed_ids = [a["id"] for a in mixed]
    ratio, _, _ = compute_change_ratio(mixed_ids, ids)
    assert ratio >= 0.30
    plan = plan_embedding_refresh(tmp_path, mixed_ids)
    assert plan.mode == "full"
    assert plan.new_ids == mixed_ids


def test_incremental_replace_small_swap_stays_incremental(tmp_path: Path) -> None:
    base = _assets(100)
    ids = [a["id"] for a in base]
    vectors = np.random.RandomState(3).rand(len(ids), HEURISTIC_V2_DIM).astype(np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=ids,
        vectors=vectors,
        source="heuristic",
        model=HEURISTIC_MODEL_V2,
    )

    kept = base[:96]
    swapped = _assets(4, prefix="s")
    mixed = kept + swapped
    mixed_ids = [a["id"] for a in mixed]
    plan = plan_embedding_refresh(tmp_path, mixed_ids)
    assert plan.mode == "incremental"
    assert len(plan.new_ids) == 4
    assert len(plan.removed_ids) == 4
