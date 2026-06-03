"""Read quantity limits from visual-journal manifest.json (single source with validate)."""

from __future__ import annotations

import json
from functools import lru_cache

from travelogue.paths import MANIFEST_PATH, manifest_path_for
from travelogue.templates.registry import DEFAULT_TEMPLATE_ID

_DEFAULT_MIN_CHAPTERS = 3
_DEFAULT_MAX_CHAPTERS = 5


@lru_cache(maxsize=8)
def manifest_limits(template_id: str = DEFAULT_TEMPLATE_ID) -> dict:
    path = manifest_path_for(template_id) if template_id != DEFAULT_TEMPLATE_ID else MANIFEST_PATH
    if not path.is_file():
        return {
            "minChapters": _DEFAULT_MIN_CHAPTERS,
            "maxChapters": _DEFAULT_MAX_CHAPTERS,
        }
    data = json.loads(path.read_text(encoding="utf-8"))
    lim = data.get("limits") or {}
    return {
        "minChapters": int(lim.get("minChapters", _DEFAULT_MIN_CHAPTERS)),
        "maxChapters": int(lim.get("maxChapters", _DEFAULT_MAX_CHAPTERS)),
    }


def chapter_limits() -> tuple[int, int]:
    lim = manifest_limits()
    return int(lim["minChapters"]), int(lim["maxChapters"])
