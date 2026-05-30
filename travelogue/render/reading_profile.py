"""Resolve export.reading profile for render surfaces (PRD-EXPERIENCE E1)."""

from __future__ import annotations

import json
import threading
from typing import Any

from travelogue.paths import ROOT

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

EXPORT_LAYOUT_LONGSHOT = "longshot"
SURFACE_WEB = "index.html"
SURFACE_MOBILE = "index-mobile.html"
SURFACE_PRESENT_PREVIEW = "index-present.html"
SURFACE_LONGSHOT = "index-longshot.html"

VALID_PROFILES = frozenset({"legacy", "performance", "default_hybrid", "magazine"})

_MATRIX_PATH = ROOT / "docs" / "experience-matrix.yaml"

# Minimal fallback when YAML unavailable (matches experience-matrix.yaml v0.1).
_FALLBACK_MATRIX: dict[str, Any] = {
    "profiles": {
        "legacy": {
            "scroll": {"snap": "off", "breath": "off", "folio": "off"},
            "present": {
                "dwell_ms": 2000,
                "featured_only": False,
                "sync_scroll_on_exit": False,
                "auto_advance": True,
                "manual_controls": True,
                "tap_zone_nav": True,
                "click_stage": "pause",
                "loop": False,
            },
            "longshot": {"breath": "off", "folio": "off"},
        },
        "performance": {
            "scroll": {"snap": "off", "breath": "off", "folio": "off"},
            "present": {
                "dwell_ms": 2000,
                "featured_only": False,
                "sync_scroll_on_exit": True,
                "auto_advance": True,
                "manual_controls": True,
                "tap_zone_nav": True,
                "click_stage": "pause",
                "loop": False,
            },
            "longshot": {"breath": "off", "folio": "off"},
        },
        "default_hybrid": {
            "scroll": {
                "snap": "proximity",
                "breath": "soft",
                "folio": "lite",
                "keyboard_nav": True,
            },
            "present": {
                "dwell_ms": 2000,
                "featured_only": False,
                "sync_scroll_on_exit": True,
                "auto_advance": True,
                "manual_controls": True,
                "tap_zone_nav": True,
                "click_stage": "pause",
                "loop": False,
            },
            "longshot": {"breath": "off", "folio": "off"},
        },
        "magazine": {
            "scroll": {"snap": "proximity", "breath": "flow", "folio": "full"},
            "present": {
                "dwell_ms": 2500,
                "featured_only": False,
                "sync_scroll_on_exit": True,
                "auto_advance": True,
                "manual_controls": True,
                "tap_zone_nav": True,
                "click_stage": "pause",
                "loop": False,
            },
            "longshot": {"breath": "off", "folio": "off"},
        },
    },
    "defaults": {
        "draft_web_profile": "default_hybrid",
        "share_zip_profile": "performance",
        "mobile_profile": "legacy",
        "longshot_surface_profile": "performance",
    },
}


_matrix_cache: dict[str, Any] | None = None
_matrix_cache_mtime: float | None = None
_matrix_cache_lock = threading.Lock()


def load_experience_matrix() -> dict[str, Any]:
    global _matrix_cache, _matrix_cache_mtime
    with _matrix_cache_lock:
        try:
            mtime = _MATRIX_PATH.stat().st_mtime if _MATRIX_PATH.is_file() else None
        except OSError:
            mtime = None
        if _matrix_cache is not None and _matrix_cache_mtime == mtime:
            return _matrix_cache
        if yaml is None or not _MATRIX_PATH.is_file():
            loaded = _FALLBACK_MATRIX
        else:
            raw = yaml.safe_load(_MATRIX_PATH.read_text(encoding="utf-8"))
            loaded = raw if isinstance(raw, dict) else _FALLBACK_MATRIX
        _matrix_cache = loaded
        _matrix_cache_mtime = mtime
        return loaded


def reset_experience_matrix_cache() -> None:
    """Clear cached experience-matrix.yaml (tests)."""
    global _matrix_cache, _matrix_cache_mtime
    with _matrix_cache_lock:
        _matrix_cache = None
        _matrix_cache_mtime = None


def resolve_surface_name(
    *,
    index_name: str = SURFACE_WEB,
    export_layout_override: str | None = None,
) -> str:
    if index_name == SURFACE_LONGSHOT or export_layout_override == EXPORT_LAYOUT_LONGSHOT:
        return SURFACE_LONGSHOT
    if index_name == SURFACE_PRESENT_PREVIEW:
        return SURFACE_PRESENT_PREVIEW
    if index_name == SURFACE_MOBILE or export_layout_override == "mobile":
        return SURFACE_MOBILE
    return SURFACE_WEB


def _matrix_defaults() -> dict[str, str]:
    defaults = load_experience_matrix().get("defaults") or {}
    return {
        "draft_web_profile": str(defaults.get("draft_web_profile", "default_hybrid")),
        "share_zip_profile": str(defaults.get("share_zip_profile", "performance")),
        "mobile_profile": str(defaults.get("mobile_profile", "legacy")),
        "longshot_surface_profile": str(defaults.get("longshot_surface_profile", "performance")),
    }


def default_profile_for_surface(
    surface: str,
    *,
    export_mode: str = "draft",
    config_defaults: dict[str, str] | None = None,
) -> str:
    cfg = config_defaults or _matrix_defaults()
    if surface == SURFACE_MOBILE:
        return cfg["mobile_profile"]
    if surface == SURFACE_LONGSHOT:
        return cfg["longshot_surface_profile"]
    if export_mode in ("share", "present-preview"):
        return cfg["share_zip_profile"]
    return cfg["draft_web_profile"]


def _profile_preset(name: str) -> dict[str, Any]:
    profiles = load_experience_matrix().get("profiles") or {}
    preset = profiles.get(name)
    if not isinstance(preset, dict):
        preset = _FALLBACK_MATRIX["profiles"].get(name, {})
    return json.loads(json.dumps(preset))


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _enum_str(val: Any, default: str = "off") -> str:
    """Normalize YAML booleans (off/on) and string enums for JS payload."""
    if val is False or val is None:
        return default if default != "on" else "off"
    if val is True:
        return "on"
    text = str(val).strip()
    if text.lower() in ("false", "none", ""):
        return default if default != "on" else "off"
    if text.lower() == "true":
        return "on"
    return text


def _present_to_js(raw: dict[str, Any]) -> dict[str, Any]:
    deep_link = raw.get("deep_link", raw.get("deepLink", True))
    click_stage = str(raw.get("click_stage", raw.get("clickStage", "pause"))).strip().lower()
    if click_stage not in ("pause", "stop", "none"):
        click_stage = "pause"
    return {
        "dwellMs": int(raw.get("dwell_ms", raw.get("dwellMs", 2000))),
        "featuredOnly": bool(raw.get("featured_only", raw.get("featuredOnly", False))),
        "syncScrollOnExit": bool(
            raw.get("sync_scroll_on_exit", raw.get("syncScrollOnExit", False))
        ),
        "skipAuxBlocks": bool(raw.get("skip_aux_blocks", raw.get("skipAuxBlocks", False))),
        "deepLink": bool(deep_link),
        "autoAdvance": bool(raw.get("auto_advance", raw.get("autoAdvance", True))),
        "loop": bool(raw.get("loop", False)),
        "manualControls": bool(raw.get("manual_controls", raw.get("manualControls", True))),
        "tapZoneNav": bool(raw.get("tap_zone_nav", raw.get("tapZoneNav", True))),
        "clickStage": click_stage,
    }


def _scroll_to_js(raw: dict[str, Any]) -> dict[str, Any]:
    engine = raw.get("breath_engine", raw.get("breathEngine", "native"))
    engine_text = str(engine).strip().lower() if engine is not None else "native"
    if engine_text not in ("native", "gsap"):
        engine_text = "native"
    return {
        "snap": _enum_str(raw.get("snap"), "off"),
        "breath": _enum_str(raw.get("breath"), "off"),
        "folio": _enum_str(raw.get("folio"), "off"),
        "breathEngine": engine_text,
        "keyboardNav": bool(raw.get("keyboard_nav", raw.get("keyboardNav", False))),
    }


def _longshot_to_js(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "breath": _enum_str(raw.get("breath"), "off"),
        "folio": _enum_str(raw.get("folio"), "off"),
    }


def count_trip_photos(trip: dict) -> int:
    """Count image assets for P5-S1 auto breath."""
    n = 0
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        atype = str(asset.get("type") or "").strip().lower()
        if atype == "image":
            n += 1
            continue
        # Legacy tests / fixtures may use kind=photo without type.
        kind = str(asset.get("kind") or "").strip().lower()
        if not atype and kind in ("photo", "image"):
            n += 1
    return n


def auto_breath_for_trip(trip: dict) -> str:
    """P5-S1 / D18: <20 soft · 20–50 flow · >50 cinematic."""
    n = count_trip_photos(trip)
    if n < 20:
        return "soft"
    if n <= 50:
        return "flow"
    return "cinematic"


def featured_asset_ids(trip: dict) -> list[str]:
    out: list[str] = []
    for asset in trip.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        if asset.get("userTier") == "featured":
            aid = str(asset.get("id") or "").strip()
            if aid:
                out.append(aid)
    return out


def _normalize_export_reading(trip: dict) -> dict[str, Any]:
    """Merge export.reading with deprecated export.breathMode / export.folioMode aliases."""
    export = trip.get("export") or {}
    if not isinstance(export, dict):
        export = {}
    raw_reading = export.get("reading") or {}
    reading: dict[str, Any] = dict(raw_reading) if isinstance(raw_reading, dict) else {}

    scroll_raw = reading.get("scroll")
    scroll: dict[str, Any] = dict(scroll_raw) if isinstance(scroll_raw, dict) else {}

    breath_alias = export.get("breathMode")
    if breath_alias is not None and scroll.get("breath") in (None, ""):
        scroll["breath"] = breath_alias

    folio_alias = export.get("folioMode")
    if folio_alias is not None and scroll.get("folio") in (None, ""):
        scroll["folio"] = folio_alias

    if scroll:
        reading["scroll"] = scroll
    return reading


def resolve_reading_payload(
    trip: dict,
    *,
    export_mode: str = "draft",
    export_layout_override: str | None = None,
    index_name: str = SURFACE_WEB,
    reading_profile_override: str | None = None,
    config_defaults: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build camelCase payload for window.__TRAVELOGUE_READING__."""
    surface = resolve_surface_name(
        index_name=index_name,
        export_layout_override=export_layout_override,
    )
    export_reading = _normalize_export_reading(trip)
    raw_export = trip.get("export") if isinstance(trip.get("export"), dict) else {}
    reading_raw = raw_export.get("reading") if isinstance(raw_export.get("reading"), dict) else {}
    normalized_scroll = export_reading.get("scroll") if isinstance(export_reading.get("scroll"), dict) else {}
    scroll_explicit = normalized_scroll.get("breath") not in (None, "")
    profile_explicit = export_reading.get("profile") not in (None, "")

    profile_name = reading_profile_override or export_reading.get("profile")
    if profile_name:
        profile_name = str(profile_name).strip()
    if not profile_name or profile_name not in VALID_PROFILES:
        profile_name = default_profile_for_surface(
            surface,
            export_mode=export_mode,
            config_defaults=config_defaults,
        )

    mobile_profile_override = export_reading.get("mobileProfile") or export_reading.get(
        "mobile_profile"
    )
    if mobile_profile_override is not None:
        mobile_profile_override = str(mobile_profile_override).strip()

    expanded = _profile_preset(profile_name)
    merged = _deep_merge(expanded, export_reading)
    merged.pop("profile", None)
    merged.pop("mobileProfile", None)
    merged.pop("mobile_profile", None)

    present_raw = merged.get("present") if isinstance(merged.get("present"), dict) else {}
    scroll_raw = merged.get("scroll") if isinstance(merged.get("scroll"), dict) else {}
    longshot_raw = merged.get("longshot") if isinstance(merged.get("longshot"), dict) else {}

    scroll = _scroll_to_js(scroll_raw)
    present = _present_to_js(present_raw)
    longshot = _longshot_to_js(longshot_raw)

    # P5-S1: auto breath on web draft when user has not set scroll.breath.
    if (
        surface == SURFACE_WEB
        and export_mode == "draft"
        and not scroll_explicit
        and not profile_explicit
        and reading_profile_override is None
    ):
        auto_breath = auto_breath_for_trip(trip)
        scroll["breath"] = auto_breath
        if auto_breath == "cinematic":
            scroll["breathEngine"] = "gsap"

    # Surface hard constraints (experience-matrix.yaml surfaces + conflicts).
    if surface == SURFACE_LONGSHOT:
        scroll = {"snap": "off", "breath": "off", "folio": "off", "breathEngine": "native"}
        longshot = {"breath": "off", "folio": "off"}
    elif surface == SURFACE_MOBILE:
        if mobile_profile_override and mobile_profile_override in VALID_PROFILES:
            profile_name = mobile_profile_override
            mobile_expanded = _profile_preset(mobile_profile_override)
            mobile_merged = _deep_merge(mobile_expanded, export_reading)
            mobile_merged.pop("profile", None)
            mobile_merged.pop("mobileProfile", None)
            mobile_merged.pop("mobile_profile", None)
            mobile_scroll = mobile_merged.get("scroll")
            mobile_present = mobile_merged.get("present")
            if isinstance(mobile_scroll, dict):
                scroll = _scroll_to_js(mobile_scroll)
            if isinstance(mobile_present, dict):
                present = _present_to_js(mobile_present)
        else:
            scroll = {"snap": "off", "breath": "off", "folio": "off", "breathEngine": "native"}

    return {
        "profile": profile_name,
        "scroll": scroll,
        "present": present,
        "longshot": longshot,
        "featuredAssetIds": featured_asset_ids(trip),
    }


def reading_html_attrs(payload: dict[str, Any]) -> list[str]:
    """data-* attributes derived from resolved reading payload."""
    attrs = [f'data-reading-profile="{payload["profile"]}"']
    scroll = payload.get("scroll") or {}
    snap = scroll.get("snap", "off")
    breath = scroll.get("breath", "off")
    folio = scroll.get("folio", "off")
    if snap and snap != "off":
        attrs.append(f'data-snap="{snap}"')
    if breath and breath != "off":
        attrs.append(f'data-breath="{breath}"')
    if folio and folio != "off":
        attrs.append(f'data-folio="{folio}"')
    if scroll.get("keyboardNav") is True:
        attrs.append('data-keyboard-nav="on"')
    return attrs


def reading_json_for_html(payload: dict[str, Any]) -> str:
    """Safe JSON for embedding in <script> (no </script> breakout)."""
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace(">", "\\u003e")
