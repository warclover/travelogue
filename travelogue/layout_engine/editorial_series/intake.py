"""Accept a promote-ready magazine series YAML into the runtime catalog.

Does not read ``docs/templates/reserve/``. Invalid ``folio-*`` ids are skipped
(atelier prefix). Id / pageCount mismatch is rejected (AS-PFM-03).
"""

from __future__ import annotations

import re
from typing import Any, Mapping

from travelogue.layout_engine.editorial_series.match import photo_span

MAGAZINE_ID_RE = re.compile(r"^magazine-(\d+)-(standard|sparse|dense)$")
_ROLE_DIGIT_RE = re.compile(r"(\d+)")
_ALLOWED_STATUS = frozenset({"", "official", "promote-ready"})


class SeriesIntakeError(ValueError):
    """YAML is not safe to load as a runtime magazine series."""


def slot_band_from_role(role: str, spec: Mapping[str, Any] | None = None) -> int:
    """Derive slot count when the promote YAML omitted ``slotBand``."""
    raw = None if spec is None else spec.get("slotBand")
    if raw is None and spec is not None:
        raw = spec.get("slot_band")
    if raw not in (None, ""):
        try:
            band = int(raw)
            if band > 0:
                return min(band, 10)
        except (TypeError, ValueError):
            pass
    hint = ""
    if spec is not None:
        hint = str(spec.get("faceHint") or spec.get("patternId") or "")
    page_n = re.match(r"page-(\d+)", hint.strip())
    if page_n:
        return min(max(int(page_n.group(1)), 1), 10)
    text = str(role or "").strip().lower()
    if "hero" in text and "grid" not in text and "stack" not in text:
        return 1
    if "pair" in text or "1p1l" in text or "1l1p" in text:
        return 2
    found = _ROLE_DIGIT_RE.search(text)
    if found:
        return min(max(int(found.group(1)), 1), 10)
    return 3


def normalize_series_document(
    data: Mapping[str, Any],
    *,
    source_name: str = "",
) -> dict[str, Any]:
    """Return a matcher-ready series dict or raise ``SeriesIntakeError``."""
    if not isinstance(data, Mapping):
        raise SeriesIntakeError("series document must be a mapping")
    sid = str(data.get("id") or "").strip()
    if not sid:
        raise SeriesIntakeError(f"missing id ({source_name or 'yaml'})")
    if sid.startswith("folio-"):
        raise SeriesIntakeError(f"atelier id not allowed at runtime: {sid}")
    matched = MAGAZINE_ID_RE.match(sid)
    if not matched:
        raise SeriesIntakeError(
            f"runtime id must be magazine-{{pages}}-{{density}}, got {sid!r}"
        )
    id_pages = int(matched.group(1))
    id_density = matched.group(2)
    page_count = int(data.get("pageCount") or data.get("page_count") or 0)
    if page_count != id_pages:
        raise SeriesIntakeError(
            f"{sid} pageCount {page_count} does not match id pages {id_pages}"
        )
    density = str(data.get("density") or id_density).strip().lower() or id_density
    if density != id_density:
        raise SeriesIntakeError(f"{sid} density {density!r} does not match id")
    status = str(data.get("status") or "").strip().lower()
    if status not in _ALLOWED_STATUS:
        raise SeriesIntakeError(f"{sid} status {status!r} is not runtime-ready")
    lo, hi = photo_span(data)
    if lo <= 0 or hi <= 0:
        raise SeriesIntakeError(f"{sid} requires photo_span [lo, hi]")
    sequence = data.get("sequence")
    if not isinstance(sequence, list) or not sequence:
        raise SeriesIntakeError(f"{sid} requires a non-empty sequence")
    if len(sequence) != page_count:
        raise SeriesIntakeError(
            f"{sid} sequence length {len(sequence)} != pageCount {page_count}"
        )
    pages: list[dict[str, Any]] = []
    for i, raw_page in enumerate(sequence, 1):
        if not isinstance(raw_page, Mapping):
            raise SeriesIntakeError(f"{sid} sequence[{i}] is not a mapping")
        role = str(raw_page.get("role") or "").strip()
        program = str(raw_page.get("program") or "").strip()
        if not role or not program:
            raise SeriesIntakeError(f"{sid} sequence[{i}] needs role and program")
        band = slot_band_from_role(role, raw_page)
        pattern = str(
            raw_page.get("patternId")
            or raw_page.get("faceHint")
            or f"page-{role}"
        ).strip()
        page = dict(raw_page)
        page["i"] = int(raw_page.get("i") or i)
        page["role"] = role
        page["program"] = program
        page["slotBand"] = band
        page["patternId"] = pattern
        pages.append(page)
    baked = sum(int(page["slotBand"]) for page in pages)
    raw_cap = data.get("capacity")
    if raw_cap not in (None, ""):
        try:
            capacity = int(raw_cap)
        except (TypeError, ValueError) as exc:
            raise SeriesIntakeError(f"{sid} capacity must be a positive int") from exc
        if capacity != baked:
            raise SeriesIntakeError(
                f"{sid} capacity {capacity} != sum(slotBand) {baked}"
            )
    else:
        capacity = baked
    if capacity <= 0:
        raise SeriesIntakeError(f"{sid} capacity must be > 0")
    out = dict(data)
    out["id"] = sid
    out["kind"] = str(data.get("kind") or "series")
    out["pageCount"] = page_count
    out["density"] = density
    out["photo_span"] = [lo, hi]
    out["capacity"] = capacity
    out["sequence"] = pages
    return out


def accept_series_document(
    data: Mapping[str, Any] | None,
    *,
    source_name: str = "",
) -> dict[str, Any] | None:
    """``None`` = skip (atelier prefix). Otherwise normalize or raise."""
    if not isinstance(data, Mapping):
        return None
    sid = str(data.get("id") or source_name or "").strip()
    if sid.startswith("folio-"):
        return None
    return normalize_series_document(data, source_name=source_name or sid)
