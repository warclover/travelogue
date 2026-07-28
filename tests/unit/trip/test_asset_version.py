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
# Re-bumped 2026-06-17: unify non-homepage UI fonts to Microsoft YaHei stack (folio meta, toasts, modals).
# Re-bumped 2026-06-19: chapter-separator sprocket decoration-only + ticket progress markup.
# Re-bumped 2026-06-19 (b): split-mat narrow panel + vertical title layout (journal/longshot CSS).
# Re-bumped 2026-06-19 (c): Studio default mist + journal accent sync + cover-mat folio ground.
# Re-bumped 2026-07-05: LTE journal-screens.generated.css sync + mosaic template usage docs.
# Re-bumped 2026-07-10: Cover Styles V6 · five opening skins + Studio options.
# Re-bumped 2026-07-10 (b): V6 dock-safe / placeholder badge / §4.7 token wiring.
# Re-bumped 2026-07-10 (c): enlarge cameo aperture circle (58vh / 520px).
# Re-bumped 2026-07-18: TPC W3/gap template YAML + contract gating (rollout percent=0).
# Re-bumped 2026-07-18 (b): restore journal-screens.css curly-quote escape (\201C).
# Re-bumped 2026-07-27: mixed-1l1p + landscape-2 editorial grids in journal-screens.css.
# Re-bumped 2026-07-27 (b): mixed slot AR fix + overlap cornered shrink.
# Re-bumped 2026-07-27 (c): mixed L|P/P|L portrait full-height + landscape remainder.
# Re-bumped 2026-07-27 (d): landscape-2 overlap edge-flush enlarge.
# Re-bumped 2026-07-27 (e): overlap lighter 55×58, keep edge flush.
# Re-bumped 2026-07-27 (f): landscape-3 asym + mixed-1p2l L2|P grids.
# Re-bumped 2026-07-27 (g): LTE sync + CSS-primary overlays (L3E/M1P2L/height).
# Re-bumped 2026-07-27 (h): restore contain-collapse opt-out for mixed-1l1p /
# landscape-3-editorial / person-pair|triple (export --sync-journal regression).
# Re-bumped 2026-07-27 (i): mixed-1l1p both-cols full-height + person-pair
# 100dvh height-adapt; CSS-primary moved into journal-screens-overlays.css SSOT.
# Re-bumped 2026-07-27 (j): restore landscape-2-overlap edge-flush CSS-primary
# (LTE 1×1 stack was full-bleed ghosting after sync wiped absolute slots).
# Re-bumped 2026-07-27 (k): mosaic-5 3P2L portrait-hero quad / lp-stack grids.
# Re-bumped 2026-07-27 (l): 3P2L left rail 11/20 · readable main AR≈0.978.
# Re-bumped 2026-07-28: moment signature label → short paper tag (EXIF contrast).
_EXPECTED_BUNDLE_VERSION = f"{ASSET_VERSION_PREFIX}028080c79510"

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
