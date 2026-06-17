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
# Bumped for Phase 16: LTE-generated grid CSS in journal-screens.css + restored
# PRD-EXPERIENCE E2/E7 reading-experience overlay (clobbered by d51b144 sync).
# Re-bumped 2026-06-07: journal-screens.css collage sync (0ff0303) + screen-portrait-3
# intrinsic row height (4fabb39) changed the shipped bundle without updating this golden.
# Re-bumped 2026-06-08: lse-flags-admin.html + first-success.js i18n in studio bundle.
# Re-bumped 2026-06-09: Lite Copy v1.1 + Web cover-opening/closing breath bundle
# (breath.js/breath-gsap.js/journal.css + copy-toggle/inline-edit) changed shipped bytes.
# Re-bumped 2026-06-10: portrait-4 (2×2) contain collapse overlay in
# journal-screens.css removed the forced 9:16 stage box / bottom blank.
# Re-bumped 2026-06-10 (b): screen-square-1 fill (742f0fb) shipped without a
# golden bump, then AC-P17-30 focal binding restored on screen-portrait-grid-8/
# portrait-1/panorama-1 cover rules (clobbered by fc61396) re-changed the bundle.
# Re-bumped 2026-06-10 (c): screen-plate portrait contain shares portrait-1 stage
# collapse (folio lite chapter opener blank bands regression).
# Re-bumped 2026-06-15: Cover optimization V4 · web cover-opening title card
# (journal.css right-bottom solid panel + line-clamp + meta inline).
# Re-bumped 2026-06-15 (b): title card width max-content + min-width floor.
# Re-bumped 2026-06-15 (c): cover title card plan A — hide trip-meta (dates), place only.
# Re-bumped 2026-06-15 (d): cover title card strict 1.6× scale (width, height, type, padding).
# Re-bumped 2026-06-15 (e): remove decorative cover-opening__enter scroll hint.
# Re-bumped 2026-06-15 (f): cover title + hook use --font-legacy-brush (handwriting).
# Re-bumped 2026-06-15 (g): cover title uses Studio HetangYuese handwriting stack.
# Re-bumped 2026-06-15 (h): expanded hetangyuese.woff2 subset (cover titles incl. 林芝).
# Re-bumped 2026-06-16: cover title uses --font-ui (Microsoft YaHei); remove HetangYuese.
_EXPECTED_BUNDLE_VERSION = f"{ASSET_VERSION_PREFIX}33886043758f"

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
