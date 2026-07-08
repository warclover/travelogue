"""Shared pytest fixtures and resource hygiene for the test suite."""

from __future__ import annotations

import gc
import json
import logging
import shutil
import threading
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

_playwright_gate = threading.Lock()
_log = logging.getLogger(__name__)

from tests.studio_test_helpers import IngestedTripWorkspace, make_test_album
from travelogue.media.ingest import ingest_into_trip
from travelogue.services.trip_factory import create_trip

_FAST_SKIP_MARKERS = frozenset(
    {"e2e", "playwright_serial", "integration", "vision", "legacy_homepage"}
)
_TIER_MARKERS = frozenset(_FAST_SKIP_MARKERS | {"unit", "mosaic"})


def _module_basename(item: pytest.Item) -> str:
    nodeid = item.nodeid.replace("\\", "/")
    return nodeid.split("/")[-1].split("::")[0]


def _apply_auto_markers(item: pytest.Item) -> None:
    """Ensure Playwright / browser tests are tagged for CI tier selection."""
    if item.get_closest_marker("unit"):
        return
    names = {m.name for m in item.iter_markers()}
    if "playwright_serial" in names and "e2e" not in names:
        item.add_marker(pytest.mark.e2e)
        names.add("e2e")
    basename = _module_basename(item)
    if "playwright" in basename:
        if "e2e" not in names:
            item.add_marker(pytest.mark.e2e)
        if "playwright_serial" not in names:
            item.add_marker(pytest.mark.playwright_serial)
        names = {m.name for m in item.iter_markers()}
    if not names.intersection(_TIER_MARKERS):
        item.add_marker(pytest.mark.unit)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--stress-iterations",
        action="store",
        default=200,
        type=int,
        help="AC-ARC-01 concurrent update iterations per thread (default: 200).",
    )
    parser.addoption(
        "--fast",
        action="store_true",
        default=False,
        help=(
            "Skip e2e, playwright_serial, integration, vision, and legacy_homepage "
            "(same tiers as CI test-pr fast job)."
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "mosaic: planner tests that require mosaic.enabled (Phase 15 MCS)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-mark browser tests; optional --fast; run Studio UI Playwright last."""
    if config.getoption("--fast"):
        deselected: list[pytest.Item] = []
        selected: list[pytest.Item] = []
        for item in items:
            if any(item.get_closest_marker(name) for name in _FAST_SKIP_MARKERS):
                deselected.append(item)
            else:
                selected.append(item)
        if deselected:
            config.hook.pytest_deselected(items=deselected)
        items[:] = selected

    for item in items:
        _apply_auto_markers(item)

    serial: list[pytest.Item] = []
    other: list[pytest.Item] = []
    for item in items:
        if item.get_closest_marker("playwright_serial"):
            serial.append(item)
        else:
            other.append(item)
    items[:] = other + serial


@pytest.fixture(autouse=True)
def _release_resources_before_playwright(request: pytest.FixtureRequest):
    """Reduce open_clip/torch ↔ Playwright contention for longshot capture."""
    if request.node.get_closest_marker("playwright_serial") is None:
        yield
        return

    with _playwright_gate:
        try:
            from travelogue.export.longshot import reset_browser_pool_for_tests

            reset_browser_pool_for_tests()
        except Exception as exc:
            _log.debug("playwright pool reset (setup) failed: %s", exc, exc_info=True)
        gc.collect()

        try:
            import torch  # type: ignore

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as exc:
            _log.debug("torch cuda cache clear (setup) failed: %s", exc, exc_info=True)

        gc.collect()
        yield
        gc.collect()
        try:
            from travelogue.export.longshot import reset_browser_pool_for_tests

            reset_browser_pool_for_tests()
        except Exception as exc:
            _log.debug("playwright pool reset (teardown) failed: %s", exc, exc_info=True)


@pytest.fixture(autouse=True)
def _enable_five_slot_for_mosaic_marked_tests(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Five-slot mosaics are off by default in app config; @pytest.mark.mosaic tests opt in."""
    if request.node.get_closest_marker("mosaic") is None:
        yield
        return
    from travelogue import config as config_mod

    base = config_mod.get_config()
    sizes = tuple(sorted(set(base.mosaic.enabled_window_sizes) | {5}))
    patched = replace(base, mosaic=replace(base.mosaic, enabled_window_sizes=sizes))
    monkeypatch.setattr(config_mod, "get_config", lambda: patched)
    yield


@pytest.fixture
def lte_pattern_enabled(monkeypatch):
    """Re-enable retired flagship for intrinsic geometry / MCS tests only."""
    from tests._golden.helpers import intrinsic_2p3l_mcs_enabled
    from travelogue.config.runtime import config_override, get_config

    base = get_config()
    te = base.layout.template_engine
    clean = replace(
        base,
        layout=replace(base.layout, template_engine=replace(te, overrides_disable=())),
    )
    with intrinsic_2p3l_mcs_enabled(), config_override(clean):
        yield clean


@pytest.fixture(autouse=True)
def _reset_clip_encoder_singleton() -> None:
    """Avoid CLIP singleton state leaking between vision/clustering tests."""
    yield
    try:
        from travelogue.vision.clip_encoder import reset_clip_encoder_singleton

        reset_clip_encoder_singleton()
    except Exception as exc:
        _log.debug("clip encoder singleton reset failed: %s", exc, exc_info=True)


@pytest.fixture(autouse=True)
def _clear_homepage_gate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Each test starts without holdback env so GET / defaults to v2 (mode=on)."""
    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2", raising=False)
    monkeypatch.delenv("TRAVELOGUE_STUDIO_HOMEPAGE_V2_PERCENT", raising=False)


@pytest.fixture(autouse=True)
def _reset_mosaic_and_config_process_state() -> None:
    """Prevent mosaic override / get_config() cache leaking across tests."""
    yield
    try:
        from travelogue.layout_engine.mosaic.runtime import reset_mosaic_config_override

        reset_mosaic_config_override()
    except Exception as exc:
        _log.debug("mosaic config override reset failed: %s", exc, exc_info=True)
    try:
        from travelogue.config import reset_config_cache

        reset_config_cache()
    except Exception as exc:
        _log.debug("config cache reset failed: %s", exc, exc_info=True)


@pytest.fixture(scope="session")
def session_ingested_trip(tmp_path_factory: pytest.TempPathFactory) -> IngestedTripWorkspace:
    """One ingest per session — copy into per-test tmp dirs to skip re-ingest."""
    root = tmp_path_factory.mktemp("session-pipeline")
    album = make_test_album(root, 8)
    trips_dir = root / "trips"
    trip_json = create_trip("session-ingest", trips_dir, title="Session", place="京都")
    trip_dir = trips_dir / "session-ingest"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    ingest_into_trip(trip, trip_dir, from_dir=album, dedupe=False)
    trip_json.write_text(json.dumps(trip, ensure_ascii=False, indent=2), encoding="utf-8")
    return IngestedTripWorkspace(
        trips_dir=trips_dir,
        trip_id="session-ingest",
        trip_dir=trip_dir,
        trip_json=trip_json,
    )


@pytest.fixture
def ingested_trip(
    session_ingested_trip: IngestedTripWorkspace, tmp_path: Path
) -> tuple[IngestedTripWorkspace, dict]:
    """Mutable trip workspace + trip dict cloned from session ingest."""
    trips_dir = tmp_path / "trips"
    trip_dir = trips_dir / session_ingested_trip.trip_id
    shutil.copytree(session_ingested_trip.trip_dir, trip_dir)
    trip_json = trip_dir / "trip.json"
    trip = json.loads(trip_json.read_text(encoding="utf-8"))
    workspace = IngestedTripWorkspace(
        trips_dir=trips_dir,
        trip_id=session_ingested_trip.trip_id,
        trip_dir=trip_dir,
        trip_json=trip_json,
    )
    return workspace, deepcopy(trip)
