"""CQA M2 · longshot upload whitelist + magic (AC-13/14)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelogue.export.longshot import LongshotExportError, write_longshot_upload
from travelogue.web.studio_handlers import export_handlers


PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"payload"


def _trip_with_json(tmp_path: Path) -> Path:
    trip = tmp_path / "t-upload"
    trip.mkdir()
    (trip / "trip.json").write_text(
        json.dumps({"meta": {"title": "白名单册"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    (trip / "index.html").write_text("<html></html>", encoding="utf-8")
    return trip


def test_write_longshot_upload_ignores_client_filename(tmp_path: Path) -> None:
    trip = _trip_with_json(tmp_path)
    out = write_longshot_upload(
        trip,
        PNG_MAGIC,
        fmt="png",
        filename="not-a-shell-name.png",
    )
    assert out.name == "白名单册-长图.png"
    assert not (trip / "not-a-shell-name.png").exists()
    assert (trip / "trip.json").read_text(encoding="utf-8")


def test_handle_longshot_upload_rejects_html_js_css_filename(
    monkeypatch, tmp_path: Path
) -> None:
    trip = _trip_with_json(tmp_path)
    before = (trip / "index.html").read_text(encoding="utf-8")
    responses: list[tuple[int, dict]] = []

    class H:
        def _read_json_body(self):
            import base64

            return {
                "tripId": trip.name,
                "format": "png",
                "filename": "evil.html",
                "data": base64.b64encode(PNG_MAGIC).decode("ascii"),
            }

        def _json_response(self, status, body):
            responses.append((status, body))

    monkeypatch.setattr(
        export_handlers,
        "resolve_trip_dir",
        lambda _ctx, _tid: trip,
    )
    monkeypatch.setattr(export_handlers, "studio_ctx", lambda _h: object())
    export_handlers.handle_longshot_upload(H())  # type: ignore[arg-type]
    assert responses and responses[0][0] == 400
    assert (trip / "index.html").read_text(encoding="utf-8") == before
    assert list(trip.glob("*-长图*")) == []


def test_write_longshot_upload_rejects_bad_magic(tmp_path: Path) -> None:
    trip = _trip_with_json(tmp_path)
    before = (trip / "trip.json").read_text(encoding="utf-8")
    with pytest.raises(LongshotExportError) as ei:
        write_longshot_upload(trip, b"not-an-image", fmt="png")
    assert ei.value.code == "E_LNG_CAPTURE_FAILED"
    assert (trip / "trip.json").read_text(encoding="utf-8") == before
    assert list(trip.glob("*-长图*")) == []


def test_handle_longshot_upload_rejects_reserved_filename(monkeypatch, tmp_path: Path) -> None:
    trip = _trip_with_json(tmp_path)
    before = (trip / "trip.json").read_text(encoding="utf-8")
    responses: list[tuple[int, dict]] = []

    class H:
        def _read_json_body(self):
            import base64

            return {
                "tripId": trip.name,
                "format": "png",
                "filename": "trip.json",
                "data": base64.b64encode(PNG_MAGIC).decode("ascii"),
            }

        def _json_response(self, status, body):
            responses.append((status, body))

    monkeypatch.setattr(
        export_handlers,
        "resolve_trip_dir",
        lambda _ctx, _tid: trip,
    )
    monkeypatch.setattr(export_handlers, "studio_ctx", lambda _h: object())
    export_handlers.handle_longshot_upload(H())  # type: ignore[arg-type]
    assert responses and responses[0][0] == 400
    assert responses[0][1].get("ok") is False
    assert (trip / "trip.json").read_text(encoding="utf-8") == before
