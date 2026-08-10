"""Phase 4 M16 · preview toolbar backend (title, intent PATCH, promote defer, rerender)."""

from __future__ import annotations

import json
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import error, request

import pytest

from tests.studio_test_helpers import chromium_safe_free_port
from travelogue.services.trip import TripService, apply_intent
from travelogue.web.copy_patch import apply_copy_patches
from travelogue.web.serve import TripPreviewHandler
from travelogue.web.studio_entry import build_intent_brief_ui, build_intent_summary

pytestmark = pytest.mark.e2e


def _patch_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="PATCH",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def _post_json(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body) if body else {}


def _free_port() -> int:
    return chromium_safe_free_port()


def _start_studio(trips_dir: Path, port: int) -> ThreadingHTTPServer:
    handler = partial(
        TripPreviewHandler,
        directory=str(trips_dir),
        trip_json=trips_dir / ".placeholder" / "trip.json",
        studio_mode=True,
        trips_dir=trips_dir,
        studio_host="127.0.0.1",
        studio_port=port,
        auto_rerender=False,
    )
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _minimal_trip(trip_id: str = "demo-m16") -> dict:
    return {
        "meta": {"title": "旧杂志名"},
        "assets": [
            {"id": "a1", "userTier": "normal"},
            {"id": "a2", "userTier": "normal"},
        ],
        "chapters": [],
    }


def test_meta_title_copy_patch_dual_writes_intent() -> None:
    trip = _minimal_trip()
    apply_copy_patches(trip, [{"path": "meta.title", "value": "雨后京都"}])
    assert trip["meta"]["title"] == "雨后京都"
    assert trip["intent"]["title"] == "雨后京都"


def test_memory_anchors_copy_patch() -> None:
    trip = {
        "chapters": [{"id": "ch-01", "title": "京都", "items": []}],
    }
    apply_copy_patches(
        trip,
        [{"path": "chapters.ch-01.curation.memoryAnchors", "value": "寺, 雨, 慢走"}],
    )
    assert trip["chapters"][0]["curation"]["memoryAnchors"] == ["寺", "雨", "慢走"]


def test_intent_summary_includes_user_notes_text() -> None:
    trip = _minimal_trip()
    apply_intent(trip, user_notes="带娃慢走")
    summary = build_intent_summary(trip)
    assert summary["hasUserNotes"] is True
    assert summary["userNotes"] == "带娃慢走"


def test_intent_brief_ui_user_facing_labels() -> None:
    trip = _minimal_trip()
    empty = build_intent_brief_ui(trip)
    assert empty["ready"] is False
    assert empty["statusLabel"] == "尚未解析"
    trip.setdefault("intent", {})["intentBrief"] = {
        "source": "cache",
        "tone": "quiet documentary",
        "titleHint": "慢走大理",
        "clusterHints": {"preferFewerChapters": True},
    }
    ui = build_intent_brief_ui(trip)
    assert ui["ready"] is True
    assert "已就绪" in ui["statusLabel"]
    assert "偏少章" in ui["statusLabel"]
    assert "Intent" not in ui["statusLabel"]
    assert "intent_brief" not in (ui["detail"] or "")


def test_patch_intent_updates_user_notes(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_id = "demo-m16"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    trip = _minimal_trip(trip_id)
    TripService(root=tmp_path).save(trip, trip_dir / "trip.json")

    port = _free_port()
    server = _start_studio(trips_dir, port)
    try:
        status, body = _patch_json(
            f"http://127.0.0.1:{port}/__travelogue/trips/{trip_id}/intent",
            {"userNotes": "想表达静谧"},
        )
        assert status == 200
        assert body["ok"] is True
        assert body["intent"]["userNotes"] == "想表达静谧"

        saved = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        assert saved["userNotes"] == "想表达静谧"
        assert saved["intent"]["userNotes"] == "想表达静谧"
    finally:
        server.shutdown()


def test_promote_tier_defer_rerender(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_id = "demo-m16"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    trip = _minimal_trip(trip_id)
    TripService(root=tmp_path).save(trip, trip_dir / "trip.json")

    port = _free_port()
    server = _start_studio(trips_dir, port)
    try:
        status, body = _post_json(
            f"http://127.0.0.1:{port}/{trip_id}/__travelogue/promote-tier",
            {"assetIds": ["a1"], "rerender": False},
        )
        assert status == 200
        assert body["ok"] is True
        assert body["promoted"] == ["a1"]
        assert body["rendered"] == []

        saved = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        tiers = {a["id"]: a.get("userTier") for a in saved["assets"]}
        assert tiers["a1"] == "featured"

        status2, body2 = _post_json(
            f"http://127.0.0.1:{port}/{trip_id}/__travelogue/promote-tier",
            {"assetIds": ["a1"], "tier": "material", "rerender": False},
        )
        assert status2 == 200
        assert body2["ok"] is True
        assert body2["demoted"] == ["a1"]
        saved2 = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
        tiers2 = {a["id"]: a.get("userTier") for a in saved2["assets"]}
        assert tiers2["a1"] == "material"
    finally:
        server.shutdown()


def test_rerender_endpoint_ok_without_crash(tmp_path: Path) -> None:
    trips_dir = tmp_path / "trips"
    trip_id = "demo-m16"
    trip_dir = trips_dir / trip_id
    trip_dir.mkdir(parents=True)
    trip = _minimal_trip(trip_id)
    TripService(root=tmp_path).save(trip, trip_dir / "trip.json")

    port = _free_port()
    server = _start_studio(trips_dir, port)
    try:
        status, body = _post_json(
            f"http://127.0.0.1:{port}/{trip_id}/__travelogue/rerender",
            {},
        )
        assert status == 200
        assert body["ok"] is True
        assert isinstance(body["rendered"], list)
    finally:
        server.shutdown()
