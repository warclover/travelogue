"""Rule-based travel plan parsing for Studio import (Phase 4 M18)."""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from travelogue.services.trip import apply_intent

logger = logging.getLogger(__name__)

MAX_PLAN_BYTES = 32 * 1024
MAX_CITIES = 10
MAX_SUMMARY = 200

_SKIP_CITY_TOKENS = frozenset(
    {
        "回程",
        "返程",
        "回家",
        "返回",
        "返程日",
        "departure",
        "return",
        "home",
    }
)

_DAY_LINE = re.compile(
    r"^(?:D\s*\d+|Day\s*\d+|第\s*\d+\s*天)\b",
    re.IGNORECASE,
)
_ISO_DATE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")
_LIST_ITEM = re.compile(r"^[\-*•·]\s+")

_ALIASES_PATH = Path(__file__).resolve().parent.parent / "data" / "city_aliases.json"
_ALIAS_INDEX: dict[str, str] | None = None


@dataclass(frozen=True)
class PlanParseResult:
    ok: bool
    warn: str | None = None
    cities: tuple[str, ...] = ()
    summary: str | None = None
    plan_format: str = "text"
    filename: str = "plan.txt"


def _load_alias_index() -> dict[str, str]:
    global _ALIAS_INDEX
    if _ALIAS_INDEX is not None:
        return _ALIAS_INDEX
    index: dict[str, str] = {}
    try:
        raw = json.loads(_ALIASES_PATH.read_text(encoding="utf-8"))
        for entry in raw.get("cities") or []:
            if not isinstance(entry, dict):
                continue
            canonical = str(entry.get("canonical") or "").strip()
            if not canonical:
                continue
            index[_normalize(canonical)] = canonical
            for alias in entry.get("aliases") or []:
                alias_text = str(alias).strip()
                if alias_text:
                    index[_normalize(alias_text)] = canonical
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("city_aliases.json unavailable: %s", exc)
    _ALIAS_INDEX = index
    return index


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFKC", text).strip().casefold()


def _is_garbage(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    printable = sum(1 for ch in stripped if ch.isprintable() or ch in "\n\r\t")
    return printable / max(len(stripped), 1) < 0.5


def _detect_format(filename: str) -> str:
    lower = filename.lower()
    return "markdown" if lower.endswith(".md") else "text"


def _find_city_in_line(
    line: str, *, alias_index: dict[str, str], allow_heuristic: bool = True
) -> str | None:
    normalized_line = _normalize(line)
    if not normalized_line:
        return None
    for token in _SKIP_CITY_TOKENS:
        if _normalize(token) in normalized_line:
            return None

    # Longest alias first to prefer "京都市" over "京都" when both match.
    for alias_norm, canonical in sorted(
        alias_index.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if alias_norm and alias_norm in normalized_line:
            return canonical

    if not allow_heuristic:
        return None

    # Heuristic: CJK place token after date / day marker.
    tail = re.sub(r"^[\-*•·\d\sDday第天]+", "", line, flags=re.IGNORECASE).strip()
    tail = _ISO_DATE.sub("", tail).strip(" ：:→>-—·")
    if 2 <= len(tail) <= 12 and re.search(r"[\u4e00-\u9fff]", tail):
        if _normalize(tail) not in {_normalize(t) for t in _SKIP_CITY_TOKENS}:
            return tail[:12]
    return None


def _extract_cities(lines: list[str], *, alias_index: dict[str, str]) -> list[str]:
    cities: list[str] = []
    seen: set[str] = set()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        is_day = bool(_DAY_LINE.match(stripped) or _ISO_DATE.search(stripped))
        is_list = bool(_LIST_ITEM.match(stripped))
        if is_list:
            city = _find_city_in_line(
                stripped, alias_index=alias_index, allow_heuristic=False
            )
        elif is_day:
            city = _find_city_in_line(
                stripped, alias_index=alias_index, allow_heuristic=True
            )
        elif any(alias in _normalize(stripped) for alias in alias_index):
            city = _find_city_in_line(
                stripped, alias_index=alias_index, allow_heuristic=False
            )
        else:
            continue
        if not city:
            continue
        key = _normalize(city)
        if key in seen:
            continue
        seen.add(key)
        cities.append(city)
        if len(cities) >= MAX_CITIES:
            break
    return cities


def _build_summary(lines: list[str], cities: list[str]) -> str | None:
    if cities:
        parts = [f"D{i + 1} {city}" for i, city in enumerate(cities[:5])]
        summary = " → ".join(parts)
        if len(cities) > 5:
            summary += " …"
        return summary[:MAX_SUMMARY]
    body = " ".join(line.strip() for line in lines if line.strip())
    if not body:
        return None
    return body[:MAX_SUMMARY]


def parse_plan_bytes(data: bytes, *, filename: str = "plan.txt") -> PlanParseResult:
    if len(data) > MAX_PLAN_BYTES:
        logger.warning("travel plan exceeds %d bytes; ignoring cities", MAX_PLAN_BYTES)
        return PlanParseResult(ok=False, warn="plan_too_large", filename=filename)

    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        logger.warning("travel plan is not valid UTF-8; ignoring cities")
        return PlanParseResult(ok=False, warn="plan_decode_error", filename=filename)

    return parse_plan_text(text, filename=filename)


def parse_plan_text(text: str, *, filename: str = "plan.txt") -> PlanParseResult:
    plan_format = _detect_format(filename)
    if _is_garbage(text):
        logger.warning("travel plan empty or unreadable; ignoring cities")
        return PlanParseResult(
            ok=False, warn="plan_unreadable", plan_format=plan_format, filename=filename
        )

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    alias_index = _load_alias_index()
    cities = _extract_cities(lines, alias_index=alias_index)
    summary = _build_summary(lines, cities)
    if not cities and not summary:
        logger.warning("travel plan parsed with no cities; ignoring city hints")
        return PlanParseResult(
            ok=False, warn="plan_no_cities", plan_format=plan_format, filename=filename
        )
    return PlanParseResult(
        ok=True,
        cities=tuple(cities),
        summary=summary,
        plan_format=plan_format,
        filename=filename,
    )


def normalize_city(text: str) -> str:
    return _normalize(text)


def cities_match(plan_city: str, place: str) -> bool:
    """City alignment for plan vs geo segment labels (PRD-PHASE4 §4.2)."""
    if not plan_city or not place:
        return False
    plan_norm = _normalize(plan_city)
    place_norm = _normalize(place)
    if plan_norm == place_norm:
        return True
    alias_index = _load_alias_index()
    plan_canon = alias_index.get(plan_norm, plan_city)
    place_canon = alias_index.get(place_norm, place)
    if _normalize(plan_canon) == _normalize(place_canon):
        return True
    plan_canon_norm = _normalize(plan_canon)
    place_canon_norm = _normalize(place_canon)
    return plan_canon_norm in place_canon_norm or place_canon_norm in plan_canon_norm


def save_plan_file(trip_dir: Path, data: bytes) -> Path:
    intent_dir = trip_dir / "source" / "intent"
    intent_dir.mkdir(parents=True, exist_ok=True)
    dest = intent_dir / "plan.txt"
    dest.write_bytes(data)
    return dest


def apply_plan_parse(trip: dict, result: PlanParseResult) -> None:
    """Write intent.travelPlan and curation.intentHints from a parse result."""
    curation = trip.setdefault("curation", {})
    hints: dict[str, Any] = dict(curation.get("intentHints") or {})

    if not result.ok:
        hints.pop("planCities", None)
        curation["intentHints"] = hints or None
        if not hints:
            curation.pop("intentHints", None)
        return

    travel_plan: dict[str, Any] = {
        "format": result.plan_format,
        "filename": "plan.txt",
    }
    if result.summary:
        travel_plan["summary"] = result.summary[:MAX_SUMMARY]
    if result.cities:
        travel_plan["cities"] = list(result.cities)[:MAX_CITIES]
        hints["planCities"] = list(result.cities)[:MAX_CITIES]
    else:
        hints.pop("planCities", None)

    apply_intent(trip, travel_plan=travel_plan)
    if hints:
        curation["intentHints"] = hints
    else:
        curation.pop("intentHints", None)


def ingest_travel_plan(
    trip: dict,
    trip_dir: Path,
    *,
    raw_bytes: bytes | None = None,
    raw_text: str | None = None,
    filename: str = "plan.txt",
) -> PlanParseResult:
    if raw_bytes is None and raw_text is not None:
        raw_bytes = raw_text.encode("utf-8")
    if raw_bytes is None:
        return PlanParseResult(ok=False, warn="plan_missing")
    save_plan_file(trip_dir, raw_bytes)
    result = parse_plan_bytes(raw_bytes, filename=filename)
    apply_plan_parse(trip, result)
    return result
