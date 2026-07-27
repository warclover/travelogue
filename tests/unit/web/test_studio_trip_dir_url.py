"""Bare /{tripId}/ must resolve to index.html (not 404)."""

from __future__ import annotations

from travelogue.web.studio_routes import StudioMixin


class _PartsHost(StudioMixin):
    pass


def test_studio_trip_parts_accepts_bare_trip_directory_urls() -> None:
    host = _PartsHost()
    assert host.studio_trip_parts("/demo-2025") == ("demo-2025", "")
    assert host.studio_trip_parts("/demo-2025/") == ("demo-2025", "")
    assert host.studio_trip_parts("/demo-2025/index.html") == (
        "demo-2025",
        "index.html",
    )


def test_studio_trip_parts_rejects_studio_reserved_prefixes() -> None:
    host = _PartsHost()
    assert host.studio_trip_parts("/") is None
    assert host.studio_trip_parts("/__studio/x") is None
    assert host.studio_trip_parts("/_internal/x") is None
