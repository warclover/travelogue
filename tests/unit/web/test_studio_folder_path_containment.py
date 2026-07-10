"""Featured/material folder paths must stay inside the album directory."""

from __future__ import annotations

from pathlib import Path

import pytest

from travelogue.demo.build import DemoError
from travelogue.web.studio_pipeline import _path_within_album, _resolve_ingest_folder_paths


def test_path_within_album_accepts_relative_subdir(tmp_path: Path) -> None:
    album = tmp_path / "album"
    featured = album / "精选"
    featured.mkdir(parents=True)
    resolved = _path_within_album("精选", album)
    assert resolved == featured.resolve()


def test_path_within_album_rejects_parent_traversal(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    outside = tmp_path / "secret"
    outside.mkdir()
    with pytest.raises(DemoError) as exc:
        _path_within_album("../secret", album)
    assert exc.value.code == "E_STUDIO_ALBUM_DENIED"


def test_path_within_album_rejects_absolute_outside(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    with pytest.raises(DemoError) as exc:
        _path_within_album(str(outside), album)
    assert exc.value.code == "E_STUDIO_ALBUM_DENIED"


def test_resolve_ingest_folder_paths_keeps_both_inside(tmp_path: Path) -> None:
    album = tmp_path / "album"
    (album / "featured").mkdir(parents=True)
    (album / "material").mkdir(parents=True)
    featured, material = _resolve_ingest_folder_paths(
        album,
        {"featuredDir": "featured", "materialDir": "material"},
    )
    assert featured is not None
    assert material is not None
    assert featured.relative_to(album.resolve())
    assert material.relative_to(album.resolve())


def test_resolve_ingest_folder_paths_rejects_escape(tmp_path: Path) -> None:
    album = tmp_path / "album"
    album.mkdir()
    with pytest.raises(DemoError) as exc:
        _resolve_ingest_folder_paths(album, {"featuredDir": "../../etc"})
    assert exc.value.code == "E_STUDIO_ALBUM_DENIED"
