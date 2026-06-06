"""Process-wide config cache and request-scoped overrides."""

from __future__ import annotations

import threading
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

from travelogue.config.app import AppConfig
from travelogue.config.loader import load_config

_config_ctx: ContextVar[AppConfig | None] = ContextVar("app_config", default=None)
_cached: AppConfig | None = None
_cache_lock = threading.Lock()


@contextmanager
def config_override(cfg: AppConfig) -> Iterator[AppConfig]:
    """Temporarily use *cfg* for ``get_config()`` in this context (thread/async safe)."""
    token = _config_ctx.set(cfg)
    try:
        yield cfg
    finally:
        _config_ctx.reset(token)


@contextmanager
def app_config_scope(cfg: AppConfig | None = None) -> Iterator[AppConfig]:
    """Pin *cfg* (or current ``get_config()``) for a pipeline stage or HTTP request."""
    active = cfg or get_config()
    with config_override(active):
        yield active


def reset_config_cache() -> None:
    """Clear process-wide lazy cache (tests)."""
    global _cached
    with _cache_lock:
        _cached = None


def get_config(*, reload: bool = False, path: Path | None = None) -> AppConfig:
    override = _config_ctx.get()
    if override is not None:
        return override

    global _cached
    from travelogue.env import load_dotenv_files

    load_dotenv_files()
    with _cache_lock:
        if _cached is None or reload:
            _cached = load_config(path)
        return _cached


def default_web_layout_engine(export_layout: str, *, cfg: AppConfig | None = None) -> str:
    """Resolve layoutEngine when not set on trip (config + exportLayout)."""
    if export_layout not in ("web", "auto"):
        return "legacy"
    app = cfg or get_config()
    if app.layout.web_layout_engine == "screens":
        return "screens"
    return "legacy"


def default_screen_plan_scope(*, cfg: AppConfig | None = None) -> str:
    return (cfg or get_config()).layout.screen_plan_scope


def default_mixed_proximity_seconds(*, cfg: AppConfig | None = None) -> float:
    return (cfg or get_config()).layout.mixed_proximity_seconds


def default_enable_food_grid(*, cfg: AppConfig | None = None) -> bool:
    return (cfg or get_config()).curate.enable_food_grid


def default_mundane_grid_buckets(*, cfg: AppConfig | None = None) -> tuple[str, ...]:
    buckets = (cfg or get_config()).curate.mundane_grid_buckets
    return buckets or ("food",)


def reading_profile_defaults(cfg: AppConfig | None = None) -> dict[str, str]:
    """Map AppConfig.render.reading to resolve_reading_payload config_defaults."""
    app = cfg or get_config()
    reading = app.render.reading
    return {
        "draft_web_profile": reading.default_profile,
        "share_zip_profile": reading.share_profile,
        "mobile_profile": reading.mobile_profile,
        "longshot_surface_profile": reading.longshot_surface_profile,
    }
