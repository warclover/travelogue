"""Load Studio stage hints from studio_stages.yaml."""

from __future__ import annotations

import logging
from functools import lru_cache

from travelogue.paths import STUDIO_TEMPLATE_DIR

_log = logging.getLogger(__name__)

_DEFAULT_STAGES = {
    "curate": "约 30 秒",
    "narrate": "约 10 秒",
    "render": "约 30 秒",
    "longshot": "约 20–40 秒",
    "llm_narrate": "约 30–60 秒",
}

_DEFAULT_INGEST = (
    (50, "约 30 秒"),
    (100, "约 1 分钟"),
    (250, "约 2 分钟"),
)

_DEFAULT_PIPELINE_ESTIMATES = (
    (50, "约 3–5 分钟"),
    (100, "约 5–8 分钟"),
    (200, "约 8–15 分钟"),
    (999999, "约 12–25 分钟"),
)


@lru_cache(maxsize=1)
def _load_stages_file() -> dict:
    path = STUDIO_TEMPLATE_DIR / "studio_stages.yaml"
    if not path.is_file():
        return {}
    try:
        import yaml

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception:
        _log.debug("failed to load studio stages from %s", path, exc_info=True)
        return {}


def stage_hint(stage: str, fallback: str = "") -> str:
    data = _load_stages_file()
    stages = data.get("stages") or {}
    return str(stages.get(stage) or _DEFAULT_STAGES.get(stage) or fallback)


def ingest_stage_hint(photo_count: int) -> str:
    data = _load_stages_file()
    tiers = data.get("ingest") or []
    if isinstance(tiers, list):
        for row in tiers:
            if not isinstance(row, dict):
                continue
            limit = int(row.get("max_photos") or 0)
            hint = str(row.get("hint") or "").strip()
            if limit and photo_count <= limit and hint:
                return hint
    for limit, hint in _DEFAULT_INGEST:
        if photo_count <= limit:
            return hint
    return _DEFAULT_INGEST[-1][1]


def pipeline_estimate_hint(photo_count: int) -> str:
    """P5-I2 · full import pipeline duration hint from photo count."""
    data = _load_stages_file()
    tiers = data.get("pipeline_estimates") or []
    if isinstance(tiers, list):
        for row in tiers:
            if not isinstance(row, dict):
                continue
            limit = int(row.get("max_photos") or 0)
            hint = str(row.get("hint") or "").strip()
            if limit and photo_count <= limit and hint:
                return hint
    for limit, hint in _DEFAULT_PIPELINE_ESTIMATES:
        if photo_count <= limit:
            return hint
    return _DEFAULT_PIPELINE_ESTIMATES[-1][1]


def pipeline_estimate_tiers() -> list[dict[str, int | str]]:
    data = _load_stages_file()
    tiers = data.get("pipeline_estimates") or []
    rows: list[dict[str, int | str]] = []
    if isinstance(tiers, list):
        for row in tiers:
            if not isinstance(row, dict):
                continue
            limit = int(row.get("max_photos") or 0)
            hint = str(row.get("hint") or "").strip()
            if limit and hint:
                rows.append({"maxPhotos": limit, "hint": hint})
    if rows:
        return rows
    return [{"maxPhotos": limit, "hint": hint} for limit, hint in _DEFAULT_PIPELINE_ESTIMATES]


def all_stage_hints() -> dict[str, str]:
    data = _load_stages_file()
    stages = dict(_DEFAULT_STAGES)
    raw = data.get("stages") or {}
    if isinstance(raw, dict):
        for key, val in raw.items():
            if val:
                stages[str(key)] = str(val)
    return stages
