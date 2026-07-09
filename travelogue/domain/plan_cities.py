"""City alias normalization and plan/segment matching (M-B1 · domain kernel)."""

from __future__ import annotations

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_ALIASES_PATH = Path(__file__).resolve().parents[1] / "data" / "city_aliases.json"


def normalize_city(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().casefold()


@lru_cache(maxsize=1)
def city_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    try:
        raw = json.loads(_ALIASES_PATH.read_text(encoding="utf-8"))
        for entry in raw.get("cities") or []:
            if not isinstance(entry, dict):
                continue
            canonical = str(entry.get("canonical") or "").strip()
            if not canonical:
                continue
            index[normalize_city(canonical)] = canonical
            for alias in entry.get("aliases") or []:
                alias_text = str(alias).strip()
                if alias_text:
                    index[normalize_city(alias_text)] = canonical
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("city_aliases.json unavailable: %s", exc)
    return index


def cities_match(plan_city: str, place: str) -> bool:
    """City alignment for plan vs geo segment labels (PRD-PHASE4 §4.2)."""
    if not plan_city or not place:
        return False
    plan_norm = normalize_city(plan_city)
    place_norm = normalize_city(place)
    if plan_norm == place_norm:
        return True
    alias_index = city_alias_index()
    plan_canon = alias_index.get(plan_norm, plan_city)
    place_canon = alias_index.get(place_norm, place)
    if normalize_city(plan_canon) == normalize_city(place_canon):
        return True
    plan_canon_norm = normalize_city(plan_canon)
    place_canon_norm = normalize_city(place_canon)
    return plan_canon_norm in place_canon_norm or place_canon_norm in plan_canon_norm
