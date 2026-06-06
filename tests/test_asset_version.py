"""assetVersion cache-bust stability (P2-4)."""

from __future__ import annotations

from travelogue.render.context import (
    ASSET_VERSION_HEX_CHARS,
    ASSET_VERSION_PREFIX,
    _longshot_bundle_version,
)


def test_bundle_version_is_content_stable() -> None:
    trip = {"updatedAt": "2026-06-06T12:00:00Z"}
    first = _longshot_bundle_version(trip)
    second = _longshot_bundle_version(trip)
    assert first == second
    assert first.startswith(ASSET_VERSION_PREFIX)
    assert len(first) == len(ASSET_VERSION_PREFIX) + ASSET_VERSION_HEX_CHARS


def test_bundle_version_uses_hash_not_mtime_digits_only() -> None:
    version = _longshot_bundle_version({})
    assert version.startswith(ASSET_VERSION_PREFIX)
    suffix = version[2:]
    assert any(c in "abcdef" for c in suffix)
