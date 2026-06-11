"""Studio shared template bundle URLs (R-P2-04 · A-14)."""

from __future__ import annotations

from pathlib import Path

from travelogue.paths import template_dir_for
from travelogue.templates.registry import get_registry

BUNDLE_ASSET_PREFIX = "/__travelogue/bundle/"

# Same-name assets as templates/visual-journal/ (not trip-local journal.css).
SHARED_BUNDLE_REL_PATHS = frozenset(
    {
        "longshot.js",
        "share.js",
        "longshot.css",
        "copy-toggle.js",
        "copy-display.css",
        "screenplay-hash.js",
        "screenplay-bookmarks.js",
        "screenplay.js",
        "screenplay.css",
        "longshot-bridge.js",
        "inline-edit.js",
        "inline-edit.css",
        "breath.js",
        "breath.css",
        "breath-lenis.js",
        "breath-gsap.js",
        "breath-highlight.js",
        "breath-image.js",
        "scroll-nav.js",
        "vendor/html2canvas.min.js",
    }
)


def bundle_source_template_id(template_id: str) -> str:
    rec = get_registry().get(template_id)
    return rec.shared_assets_from or template_id


def bundle_asset_root(template_id: str) -> str:
    tid = bundle_source_template_id(template_id)
    return f"{BUNDLE_ASSET_PREFIX}{tid}/"


def resolve_bundle_file(template_id: str, rel_path: str) -> Path | None:
    rel = rel_path.replace("\\", "/").lstrip("/")
    if rel not in SHARED_BUNDLE_REL_PATHS:
        return None
    root = template_dir_for(bundle_source_template_id(template_id)).resolve()
    target = (root / rel).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target if target.is_file() else None


def parse_bundle_request(path: str) -> tuple[str, str] | None:
    prefix = BUNDLE_ASSET_PREFIX
    if not path.startswith(prefix):
        return None
    rest = path[len(prefix) :].lstrip("/")
    if not rest or "/" not in rest:
        return None
    template_id, rel = rest.split("/", 1)
    if not template_id or not rel or ".." in rel:
        return None
    return template_id, rel
