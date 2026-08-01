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


def _tests_subpath(item: pytest.Item) -> list[str]:
    nodeid = item.nodeid.replace("\\", "/")
    parts = nodeid.split("/")
    if "tests" not in parts:
        return []
    idx = parts.index("tests")
    return parts[idx + 1 :]


def _apply_auto_markers(item: pytest.Item) -> None:
    """Ensure Playwright / browser tests are tagged for CI tier selection."""
    # Playwright tagging must run before the path-bucket early returns: e2e
    # serialization (`playwright_serial` ordering + torch contention fixture)
    # depends on the marker even when the module lives in tests/e2e/.
    names = {m.name for m in item.iter_markers()}
    basename = _module_basename(item)
    if "playwright_serial" in names or "playwright" in basename:
        if "e2e" not in names:
            item.add_marker(pytest.mark.e2e)
        if "playwright_serial" not in names:
            item.add_marker(pytest.mark.playwright_serial)
        return
    if item.get_closest_marker("unit"):
        return
    subpath = _tests_subpath(item)
    if subpath:
        bucket = subpath[0]
        if bucket == "unit":
            item.add_marker(pytest.mark.unit)
            return
        if bucket == "integration":
            if not item.get_closest_marker("integration"):
                item.add_marker(pytest.mark.integration)
            return
        if bucket == "e2e":
            if not item.get_closest_marker("e2e"):
                item.add_marker(pytest.mark.e2e)
            return
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
def _trust_local_album_in_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Opt in to local album paths for Studio import tests.

    Production defaults ``TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0``. Tests that
    assert the deny path should ``monkeypatch.setenv(..., \"0\")`` or
    ``delenv`` explicitly.
    """
    monkeypatch.setenv("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")


@pytest.fixture(autouse=True)
def _forbid_implicit_nima_torch_in_unit(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch
):
    """T-M5-02 / QH-17 · unit 默认禁止隐式拉起 NIMA/pyiqa 评分。

    Opt-in：``@pytest.mark.vision``，或测试内自行 monkeypatch ``pyiqa_available``。
    e2e / integration / playwright_serial 不受影响。
    """
    node = request.node
    if node.get_closest_marker("vision") is not None:
        yield
        return
    if any(
        node.get_closest_marker(name) is not None
        for name in ("e2e", "integration", "playwright_serial")
    ):
        yield
        return
    subpath = _tests_subpath(node)
    is_unit = node.get_closest_marker("unit") is not None or (
        bool(subpath) and subpath[0] == "unit"
    )
    if not is_unit:
        yield
        return
    monkeypatch.setattr(
        "travelogue.curation.photo_cull_ml.pyiqa_available",
        lambda: False,
    )
    yield


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
    """Five-slot mosaics opt-in via @pytest.mark.mosaic.

    Start from ``AppConfig()`` defaults so a local dogfood ``config.yaml``
    (near_scene_clone_gate / template_experiments / slot_adaptation) cannot
    poison MCS unit tests that call ``get_config()``.
    """
    if request.node.get_closest_marker("mosaic") is None:
        yield
        return
    from travelogue import config as config_mod
    from travelogue.config.app import AppConfig
    from travelogue.config.runtime import config_override

    base = AppConfig()
    sizes = tuple(sorted(set(base.mosaic.enabled_window_sizes) | {5}))
    patched = replace(
        base,
        mosaic=replace(base.mosaic, enabled=True, enabled_window_sizes=sizes),
    )
    monkeypatch.setattr(config_mod, "get_config", lambda: patched)
    with config_override(patched):
        yield


@pytest.fixture
def lte_pattern_enabled(monkeypatch):
    """Re-enable retired flagship for intrinsic geometry / MCS tests only.

    Force ``template_contract`` off: TPC no longer unlocks experimental rails
    (MTSO), and deprecated equal is injected on the size-path only.
    """
    from tests._golden.helpers import intrinsic_2p3l_mcs_enabled
    from travelogue.config.mosaic import TemplateContractConfig
    from travelogue.config.runtime import config_override, get_config

    base = get_config()
    te = base.layout.template_engine
    clean = replace(
        base,
        layout=replace(base.layout, template_engine=replace(te, overrides_disable=())),
        mosaic=replace(
            base.mosaic,
            template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
        ),
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
