"""Same-folder collision: legacy portfolio on the journal slug."""

from __future__ import annotations

import json
from pathlib import Path

from travelogue.util.trip_slug import demo_trip_id_from_album
from travelogue.web.studio_pipeline import peek_existing_album_trip, resolve_studio_trip_dir


def _write_trip(trip_dir: Path, *, title: str, edition: str) -> None:
    trip_dir.mkdir(parents=True)
    (trip_dir / "trip.json").write_text(
        json.dumps({"title": title, "studio": {"edition": edition}}, ensure_ascii=False),
        encoding="utf-8",
    )


def test_peek_and_resolve_reuse_legacy_portfolio_slug(tmp_path: Path) -> None:
    album = tmp_path / "珠海东澳岛一日游"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    trips = tmp_path / "trips"
    title = "珠海东澳岛一日游"
    legacy = demo_trip_id_from_album(album, title=title, place="旅途")
    _write_trip(trips / legacy, title=title, edition="portfolio")

    assert (
        peek_existing_album_trip(
            album, trips_dir=trips, title=title, place="旅途", edition="journal"
        )
        is None
    )
    found = peek_existing_album_trip(
        album, trips_dir=trips, title=title, place="旅途", edition="portfolio"
    )
    assert found is not None
    assert found["tripId"] == legacy
    assert found["edition"] == "portfolio"

    slug, path = resolve_studio_trip_dir(
        album, trips_dir=trips, title=title, place="旅途", edition="portfolio"
    )
    assert slug == legacy
    assert path == trips / legacy


def test_peek_portfolio_does_not_claim_journal(tmp_path: Path) -> None:
    album = tmp_path / "华农油菜花"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    trips = tmp_path / "trips"
    title = "华农油菜花"
    journal = demo_trip_id_from_album(album, title=title, place="旅途")
    _write_trip(trips / journal, title=title, edition="journal")

    found_j = peek_existing_album_trip(
        album, trips_dir=trips, title=title, place="旅途", edition="journal"
    )
    assert found_j is not None
    assert found_j["edition"] == "journal"
    assert (
        peek_existing_album_trip(
            album, trips_dir=trips, title=title, place="旅途", edition="portfolio"
        )
        is None
    )
    slug, _path = resolve_studio_trip_dir(
        album, trips_dir=trips, title=title, place="旅途", edition="portfolio"
    )
    assert slug != journal


def test_peek_journal_stays_when_portfolio_exists(tmp_path: Path) -> None:
    album = tmp_path / "华农油菜花"
    album.mkdir()
    (album / "a.jpg").write_bytes(b"x")
    trips = tmp_path / "trips"
    title = "华农油菜花"
    journal = demo_trip_id_from_album(album, title=title, place="旅途")
    pf_slug, _ = resolve_studio_trip_dir(
        album, trips_dir=trips, title=title, place="旅途", edition="portfolio"
    )
    _write_trip(trips / journal, title=title, edition="journal")
    _write_trip(trips / pf_slug, title=title, edition="portfolio")

    found_j = peek_existing_album_trip(
        album, trips_dir=trips, title=title, place="旅途", edition="journal"
    )
    found_p = peek_existing_album_trip(
        album, trips_dir=trips, title=title, place="旅途", edition="portfolio"
    )
    assert found_j is not None
    assert found_j["edition"] == "journal"
    assert found_j["tripId"] == journal
    assert found_p is not None
    assert found_p["edition"] == "portfolio"
    assert found_p["tripId"] == pf_slug
    assert found_p["tripId"] != journal
