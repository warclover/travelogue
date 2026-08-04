"""Load Output Recipe bands / presets YAML."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from travelogue.export.output_recipe.types import BandThresholds, OutputRecipeError
from travelogue.paths import resource_root

BANDS_PATH = resource_root() / "config" / "output_recipe_bands.yaml"
PRESETS_PATH = resource_root() / "config" / "output_recipe_presets.yaml"


def clear_output_recipe_config_cache() -> None:
    load_band_thresholds.cache_clear()
    load_presets_and_copy.cache_clear()


@lru_cache(maxsize=1)
def load_band_thresholds() -> BandThresholds:
    data = _load_yaml(BANDS_PATH)
    bands = data.get("bands") if isinstance(data.get("bands"), dict) else {}
    return BandThresholds(
        sparse_max=int(bands.get("sparse_max", 9)),
        ambiguous_max=int(bands.get("ambiguous_max", 30)),
        narrative_chapter_hint_at=int(bands.get("narrative_chapter_hint_at", 50)),
    )


@lru_cache(maxsize=1)
def load_presets_and_copy() -> tuple[dict[str, dict[str, Any]], dict[str, str]]:
    data = _load_yaml(PRESETS_PATH)
    presets_raw = data.get("presets") if isinstance(data.get("presets"), dict) else {}
    copy_raw = data.get("copy") if isinstance(data.get("copy"), dict) else {}
    presets = {str(k): dict(v) for k, v in presets_raw.items() if isinstance(v, dict)}
    copy = {str(k): str(v) for k, v in copy_raw.items()}
    return presets, copy


def get_preset(preset_id: str) -> dict[str, Any]:
    presets, _ = load_presets_and_copy()
    preset = presets.get(preset_id)
    if not preset:
        raise OutputRecipeError("E_OR_UNKNOWN_PRESET", f"未知配方 preset: {preset_id}")
    return preset


def copy_text(key: str, *, default: str = "", **fmt: Any) -> str:
    _, copy = load_presets_and_copy()
    text = copy.get(key, default or key)
    if fmt:
        try:
            return text.format(**fmt)
        except (KeyError, ValueError):
            return text
    return text


def preset_id_for_intent(intent: str, *, layout: str | None = None) -> str:
    """Map intent (+ optional layout) → preset_id."""
    if intent == "chat_longshot":
        if layout == "single":
            return "preset.chat_longshot_single"
        return "preset.chat_longshot_chapter"
    if intent == "moments_scroll":
        return "preset.moments_scroll"
    if intent == "moments_grid":
        return "preset.moments_grid"
    if intent == "xiaohongshu":
        return "preset.xiaohongshu"
    if intent == "instagram_carousel":
        return "preset.instagram_carousel"
    if intent == "poster_bric":
        return "preset.poster_bric"
    if intent == "album_spread":
        return "preset.album_spread"
    raise OutputRecipeError("E_OR_INVALID_INTENT", f"未知意图: {intent}")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        with path.open(encoding="utf-8") as f:
            loaded = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise OutputRecipeError(
            "E_OR_CONFIG_INVALID",
            f"Output Recipe YAML 损坏: {path.name}",
        ) from exc
    return loaded if isinstance(loaded, dict) else {}
