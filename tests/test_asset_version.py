"""assetVersion cache-bust stability (P2-4)."""

from __future__ import annotations

import re

from travelogue.render.context import (
    ASSET_VERSION_HEX_CHARS,
    ASSET_VERSION_PREFIX,
    _longshot_bundle_version,
    build_render_context,
)
from travelogue.render.golden_regression import load_golden_trip

# Bump only when templates/visual-journal bundle bytes change (same inputs as render).
_EXPECTED_BUNDLE_VERSION = f"{ASSET_VERSION_PREFIX}1f0eb73b9935"

_ASSET_VERSION_RE = re.compile(
    rf"^{re.escape(ASSET_VERSION_PREFIX)}[0-9a-f]{{{ASSET_VERSION_HEX_CHARS}}}$"
)


def test_bundle_version_is_content_stable() -> None:
    trip = {"updatedAt": "2026-06-06T12:00:00Z"}
    first = _longshot_bundle_version(trip)
    second = _longshot_bundle_version(trip)
    assert first == second
    assert _ASSET_VERSION_RE.fullmatch(first)


def test_bundle_version_golden_for_template_bundle() -> None:
    assert _longshot_bundle_version({}) == _EXPECTED_BUNDLE_VERSION


def test_build_render_context_uses_bundle_version() -> None:
    trip = load_golden_trip()
    ctx = build_render_context(trip, export_mode="draft")
    assert ctx["assetVersion"] == _longshot_bundle_version(trip)
    assert ctx["assetVersion"] == _EXPECTED_BUNDLE_VERSION
