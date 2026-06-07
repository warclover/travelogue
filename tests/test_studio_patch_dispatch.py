"""Studio PATCH routing via studio_dispatch_PATCH (R4)."""

from __future__ import annotations

from travelogue.web.studio_handlers.paths import (
    ASSET_MEDIA_SUFFIX,
    CONFIG_PATH,
    INTENT_SUFFIX,
    PIPELINE_SUFFIX,
    TRIPS_PATH,
)
from travelogue.web.studio_routes import StudioMixin


class _PatchProbe(StudioMixin):
    studio_mode = True
    studio_token = "t"
    studio_host = "127.0.0.1"
    studio_port = 8766
    studio_allow_lan = False
    studio_config_path = None
    trips_dir = None
    trip_json_path = None
    app_config = None
    command = "PATCH"
    path = "/"
    headers: dict = {}

    def __init__(self) -> None:
        self.calls: list[str] = []

    def _studio_require_post_auth(self) -> bool:
        return True

    def _json_response(self, code: int, payload: dict) -> None:
        pass

    def _studio_handle_config(self) -> None:
        self.calls.append("config")

    def _studio_handle_patch_intent(self, trip_id: str) -> None:
        self.calls.append(f"intent:{trip_id}")

    def _studio_handle_patch_pipeline(self, trip_id: str) -> None:
        self.calls.append(f"pipeline:{trip_id}")


def test_studio_dispatch_patch_routes(monkeypatch) -> None:
    probe = _PatchProbe()
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.config_handlers.handle_config",
        lambda h: probe.calls.append("config_handler"),
    )
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.trip_handlers.handle_patch_intent",
        lambda h, tid: probe.calls.append(f"intent_handler:{tid}"),
    )
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.trip_handlers.handle_patch_pipeline",
        lambda h, tid: probe.calls.append(f"pipeline_handler:{tid}"),
    )
    monkeypatch.setattr(
        "travelogue.web.studio_handlers.trip_handlers.handle_asset_media_class",
        lambda h, tid: probe.calls.append(f"asset_media_handler:{tid}"),
    )

    assert probe.studio_dispatch_PATCH(CONFIG_PATH) is True
    assert probe.calls == ["config_handler"]

    probe.calls.clear()
    trip = "kyoto-2025"
    assert probe.studio_dispatch_PATCH(f"{TRIPS_PATH}/{trip}{INTENT_SUFFIX}") is True
    assert probe.calls == [f"intent_handler:{trip}"]

    probe.calls.clear()
    assert probe.studio_dispatch_PATCH(f"{TRIPS_PATH}/{trip}{PIPELINE_SUFFIX}") is True
    assert probe.calls == [f"pipeline_handler:{trip}"]

    probe.calls.clear()
    assert probe.studio_dispatch_PATCH(f"{TRIPS_PATH}/{trip}{ASSET_MEDIA_SUFFIX}") is True
    assert probe.calls == [f"asset_media_handler:{trip}"]

    assert probe.studio_dispatch_PATCH("/unknown") is False
