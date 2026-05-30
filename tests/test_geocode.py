"""Reverse geocode cache and Nominatim parsing."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from travelogue.media.geocode import _cache_key, reverse_geocode_city


def test_cache_key_rounds_coordinates() -> None:
    assert _cache_key(29.123456, 94.987654) == "29.1235,94.9877"


def test_reverse_geocode_disabled_returns_none(tmp_path) -> None:
    cache = tmp_path / "geo.json"
    assert reverse_geocode_city(30.0, 94.0, cache_path=cache, enabled=False) is None
    assert not cache.is_file()


def test_reverse_geocode_uses_disk_cache(tmp_path) -> None:
    cache = tmp_path / "geo.json"
    key = _cache_key(29.654, 94.362)
    cache.write_text(json.dumps({key: "林芝"}, ensure_ascii=False), encoding="utf-8")
    with patch("travelogue.media.geocode.urllib.request.urlopen") as urlopen:
        assert reverse_geocode_city(29.654, 94.362, cache_path=cache, enabled=True) == "林芝"
        urlopen.assert_not_called()


def test_reverse_geocode_fetches_and_caches_city(tmp_path) -> None:
    cache = tmp_path / "geo.json"
    payload = json.dumps({"address": {"city": "拉萨"}}).encode("utf-8")
    resp = MagicMock()
    resp.read.return_value = payload
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    with patch("travelogue.media.geocode.urllib.request.urlopen", return_value=resp):
        city = reverse_geocode_city(29.654, 91.117, cache_path=cache, enabled=True)
    assert city == "拉萨"
    saved = json.loads(cache.read_text(encoding="utf-8"))
    assert saved[_cache_key(29.654, 91.117)] == "拉萨"


def test_reverse_geocode_network_failure_returns_none(tmp_path) -> None:
    cache = tmp_path / "geo.json"
    import urllib.error

    with patch(
        "travelogue.media.geocode.urllib.request.urlopen",
        side_effect=urllib.error.URLError("offline"),
    ):
        assert reverse_geocode_city(1.0, 2.0, cache_path=cache, enabled=True) is None
    saved = json.loads(cache.read_text(encoding="utf-8"))
    assert saved[_cache_key(1.0, 2.0)] == ""
