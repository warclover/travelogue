"""Studio handler routing helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config import get_config
from travelogue.runtime import AppContext
from travelogue.services.trip_factory import create_trip
from travelogue.web.studio_handlers.common import (
    match_bento_preview,
    match_entry,
    match_trip_curate,
    match_trip_delete,
    match_trip_intent,
    match_trip_pipeline,
    match_trip_suffix,
    resolve_trip_dir,
)
from travelogue.web.studio_handlers.paths import (
    CURATE_SUFFIX,
    INTENT_SUFFIX,
    PIPELINE_SUFFIX,
    TRIPS_PATH,
)

pytestmark = pytest.mark.unit


def test_match_trip_suffix_extracts_trip_id() -> None:
    path = f"{TRIPS_PATH}/my-trip{INTENT_SUFFIX}"
    assert match_trip_suffix(path, INTENT_SUFFIX) == "my-trip"


def test_match_trip_suffix_rejects_nested_trip_id() -> None:
    path = f"{TRIPS_PATH}/a/b{INTENT_SUFFIX}"
    assert match_trip_suffix(path, INTENT_SUFFIX) is None


def test_match_wrappers_align_with_suffix() -> None:
    tid = "demo-01"
    assert match_entry(f"{TRIPS_PATH}/{tid}/entry") == tid
    assert match_bento_preview(f"{TRIPS_PATH}/{tid}/bento-preview") == tid
    assert match_trip_intent(f"{TRIPS_PATH}/{tid}{INTENT_SUFFIX}") == tid
    assert match_trip_pipeline(f"{TRIPS_PATH}/{tid}{PIPELINE_SUFFIX}") == tid
    assert match_trip_curate(f"{TRIPS_PATH}/{tid}{CURATE_SUFFIX}") == tid
    assert match_trip_delete(f"{TRIPS_PATH}/{tid}") == tid


def test_resolve_trip_dir_rejects_invalid_id(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    ctx = AppContext(cfg=get_config(), trips_root=trips_dir)
    assert resolve_trip_dir(ctx, "../evil") is None
    assert resolve_trip_dir(ctx, "bad/id") is None


def test_resolve_trip_dir_requires_trip_json(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    (trips_dir / "empty-trip").mkdir(parents=True)
    ctx = AppContext(cfg=get_config(), trips_root=trips_dir)
    assert resolve_trip_dir(ctx, "empty-trip") is None


def test_resolve_trip_dir_finds_existing_trip(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    create_trip("demo-01", trips_dir)
    ctx = AppContext(cfg=get_config(), trips_root=trips_dir)
    trip_dir = resolve_trip_dir(ctx, "demo-01")
    assert trip_dir is not None
    assert (trip_dir / "trip.json").is_file()


def test_ac_aad_03_studio_rejects_absolute_escape(tmp_path: Path) -> None:
    """AC-AAD-03: Studio never resolves absolute paths outside trips_root."""
    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "trip.json").write_text("{}", encoding="utf-8")
    ctx = AppContext(cfg=get_config(), trips_root=trips_dir)
    assert resolve_trip_dir(ctx, str(outside)) is None
    assert resolve_trip_dir(ctx, str(outside.resolve())) is None
    assert resolve_trip_dir(ctx, "../outside") is None
