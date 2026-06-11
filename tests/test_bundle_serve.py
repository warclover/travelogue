"""Studio bundle static route helpers."""

from __future__ import annotations

from travelogue.render.bundle_serve import parse_bundle_request, resolve_bundle_file


def test_parse_bundle_request() -> None:
    assert parse_bundle_request("/__travelogue/bundle/visual-journal/breath.js") == (
        "visual-journal",
        "breath.js",
    )
    assert parse_bundle_request("/__travelogue/bundle/") is None
    assert parse_bundle_request("/__studio/foo.js") is None


def test_resolve_bundle_file() -> None:
    path = resolve_bundle_file("visual-journal", "breath.js")
    assert path is not None
    assert path.name == "breath.js"
    assert resolve_bundle_file("visual-journal", "../breath.js") is None
    assert resolve_bundle_file("visual-journal", "journal.css") is None
