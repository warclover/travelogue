"""ALS W0 · isolation: seventh exit must not change the existing six."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.config.studio import (
    DEFAULT_LONGSHOT2_PLATFORMS,
    AlbumLandscapeConfig,
    studio_config_expose,
)
from travelogue.export.platform_profiles import (
    COMPOSE_PLATFORM_IDS,
    KNOWN_PLATFORM_IDS,
    PHASE_A_PLATFORMS,
    SCREEN_CAPTURE_PLATFORM_IDS,
    clear_platform_profiles_cache,
    file_prefix_for_platform,
    get_profile,
)
from travelogue.services.trip_factory import create_trip
from tests.studio_test_helpers import MockStudioHandler

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _clear_profiles() -> None:
    clear_platform_profiles_cache()
    yield
    clear_platform_profiles_cache()


def test_compose_and_default_tuples_unchanged() -> None:
    assert COMPOSE_PLATFORM_IDS == frozenset(
        {"poster_bric", "xiaohongshu", "wechat_official", "album_spread"}
    )
    assert DEFAULT_LONGSHOT2_PLATFORMS == (
        "wechat_moments",
        "xiaohongshu",
        "wechat_official",
        "poster_bric",
        "album_spread",
    )
    assert PHASE_A_PLATFORMS == DEFAULT_LONGSHOT2_PLATFORMS
    assert "album_landscape" not in COMPOSE_PLATFORM_IDS
    assert "album_landscape" not in DEFAULT_LONGSHOT2_PLATFORMS
    assert "album_landscape" not in PHASE_A_PLATFORMS


def test_screen_capture_set_and_known_ids() -> None:
    assert SCREEN_CAPTURE_PLATFORM_IDS == frozenset({"album_landscape"})
    assert "album_landscape" in KNOWN_PLATFORM_IDS
    profile = get_profile("album_landscape")
    assert profile.label == "横版画册"
    assert (profile.output or {}).get("aspect") == "16:9"
    assert file_prefix_for_platform("林芝", "album_landscape") == "林芝-landscape"
    assert file_prefix_for_platform("林芝", "album_spread") == "林芝-album"


def test_studio_config_expose_album_landscape_flag() -> None:
    from travelogue.config import AppConfig

    exposed = studio_config_expose(AppConfig())
    assert exposed["studio"]["albumLandscape"]["enabled"] is True

    cfg = AppConfig()
    cfg.studio.album_landscape = AlbumLandscapeConfig(enabled=False)
    exposed_off = studio_config_expose(cfg)
    assert exposed_off["studio"]["albumLandscape"]["enabled"] is False


def test_album_landscape_module_does_not_import_private_pool() -> None:
    src = Path("travelogue/export/album_landscape.py").read_text(encoding="utf-8")
    assert "import _BROWSER_POOL" not in src
    assert "import _PlaywrightBrowserPool" not in src
    assert "sync_playwright" not in src
    assert "acquire_browser" in src
    assert "release_browser" in src
    from travelogue.export.longshot import acquire_browser, release_browser

    assert callable(acquire_browser)
    assert callable(release_browser)


def test_flag_off_single_api_disabled(tmp_path: Path) -> None:
    from travelogue.web.studio_handlers.export_handlers import handle_longshot

    trips = tmp_path / "trips"
    create_trip("als-off", trips, title="als-off")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "als-off",
            "platform": "album_landscape",
            "allowMissingSource": True,
        },
    )
    handler.app_config.studio.album_landscape = AlbumLandscapeConfig(enabled=False)
    handle_longshot(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_ALS_DISABLED"


def test_batch_containing_album_landscape_forbidden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from travelogue.web.studio_handlers.export_handlers import handle_longshot

    called: list[str] = []

    def _boom(*_a, **_k):
        called.append("export")
        raise AssertionError("batch must not start capture")

    monkeypatch.setattr("travelogue.export.longshot.export_trip_longshot", _boom)
    monkeypatch.setattr(
        "travelogue.export.longshot_batch.export_trip_longshot_batch", _boom
    )

    trips = tmp_path / "trips"
    create_trip("als-batch", trips, title="als-batch")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "als-batch",
            "platforms": [
                {"platform": "xiaohongshu"},
                {"platform": "album_landscape"},
            ],
            "allowMissingSource": True,
        },
    )
    handle_longshot(handler)
    assert handler.response is not None
    status, body = handler.response
    assert status == 400
    assert body["error"] == "E_ALS_BATCH_FORBIDDEN"
    assert called == []


def test_album_landscape_bypasses_output_recipe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """D-ALS-12 · Recipe 开启 + 残留 intent 也不得 400 E_OR_UNKNOWN_PLATFORM。"""
    from travelogue.config.studio import OutputRecipeConfig
    from travelogue.web.studio_handlers.export_handlers import handle_longshot

    monkeypatch.setattr(
        "travelogue.export.longshot.playwright_longshot_available",
        lambda: False,
    )
    trips = tmp_path / "trips"
    create_trip("als-or", trips, title="als-or")
    handler = MockStudioHandler(
        trips,
        json_body={
            "tripId": "als-or",
            "platform": "album_landscape",
            "intent": "xiaohongshu",
            "allowMissingSource": True,
        },
    )
    handler.app_config.studio.output_recipe = OutputRecipeConfig(enabled=True)
    handle_longshot(handler)
    assert handler.response is not None
    status, body = handler.response
    assert body.get("error") != "E_OR_UNKNOWN_PLATFORM"
    assert status == 400
    assert body["error"] == "E_LNG_PLAYWRIGHT"


def test_export_trip_longshot_routes_to_album_landscape(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from travelogue.export.longshot import LongshotExportResult, export_trip_longshot

    called: list[str] = []

    def _stub(*_a, **_k):
        called.append("als")
        return LongshotExportResult(platform="album_landscape", capture_method="album_landscape")

    monkeypatch.setattr(
        "travelogue.export.album_landscape.export_album_landscape", _stub
    )
    trip = tmp_path / "t"
    trip.mkdir()
    (trip / "index.html").write_text("<html></html>", encoding="utf-8")
    result = export_trip_longshot(trip, platform="album_landscape")
    assert called == ["als"]
    assert result.platform == "album_landscape"
