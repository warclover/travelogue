"""AC-P7-12 · fault injection: interrupted cache writes must not corrupt prior state."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest


def test_save_embedding_cache_keeps_prior_on_replace_failure(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision.cache import load_embedding_cache, save_embedding_cache

    v1 = np.zeros((1, 8), dtype=np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=["a1"],
        vectors=v1,
        source="heuristic",
        model="test",
    )

    def _boom(*_args, **_kwargs) -> None:
        raise OSError("simulated interrupt during atomic replace")

    monkeypatch.setattr("travelogue.vision.cache.os.replace", _boom)
    v2 = np.ones((2, 8), dtype=np.float32)
    with pytest.raises(OSError):
        save_embedding_cache(
            tmp_path,
            asset_ids=["a1", "a2"],
            vectors=v2,
            source="heuristic",
            model="test",
        )

    loaded = load_embedding_cache(tmp_path)
    assert loaded is not None
    assert loaded["asset_ids"] == ["a1"]
    assert float(loaded["vectors"][0, 0]) == 0.0


def test_orphan_tmp_does_not_replace_valid_cache(tmp_path: Path) -> None:
    from travelogue.vision.cache import (
        EMBEDDINGS_FILE,
        EMBEDDINGS_TMP,
        load_embedding_cache,
        save_embedding_cache,
    )

    vectors = np.zeros((1, 8), dtype=np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=["a1"],
        vectors=vectors,
        source="heuristic",
    )
    cache_dir = tmp_path / ".cluster-cache"
    (cache_dir / EMBEDDINGS_TMP).write_bytes(b"partial write")
    assert (cache_dir / EMBEDDINGS_FILE).is_file()
    loaded = load_embedding_cache(tmp_path)
    assert loaded is not None
    assert loaded["asset_ids"] == ["a1"]


def test_embedding_cache_is_corrupt_when_final_file_unreadable(tmp_path: Path, monkeypatch) -> None:
    from travelogue.vision.cache import embedding_cache_is_corrupt, save_embedding_cache

    vectors = np.zeros((1, 8), dtype=np.float32)
    save_embedding_cache(
        tmp_path,
        asset_ids=["a1"],
        vectors=vectors,
        source="heuristic",
    )

    def _bad_load(_trip_dir: Path):
        return None

    monkeypatch.setattr("travelogue.vision.cache.load_embedding_cache", _bad_load)
    assert embedding_cache_is_corrupt(tmp_path) is True
