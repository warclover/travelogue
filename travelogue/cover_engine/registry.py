"""Cover Style Registry (API-CSE-01..05, 11)."""

from __future__ import annotations

from collections.abc import Iterable
from threading import RLock

from travelogue.cover_engine.types import CoverStyleProfile, CoverStyleRecord, CoverStyleStatus

_DEFAULT_STYLE_ID = "veil-footer"

_lock = RLock()
_records: dict[str, CoverStyleRecord] = {}
_overrides: dict[str, dict] = {}  # style_id -> {status?, sort_order?}
_bootstrapped = False


class CoverStyleRegistry:
    """Process-local style catalog. Callers should use module-level helpers."""

    def list_styles(self, *, status: CoverStyleStatus | None = None) -> list[CoverStyleRecord]:
        return list_styles(status=status)

    def list_assignable(self) -> list[CoverStyleRecord]:
        return list_assignable_styles()

    def get(self, style_id: str) -> CoverStyleRecord | None:
        return get_style(style_id)


def get_registry() -> CoverStyleRegistry:
    _ensure_bootstrapped()
    return CoverStyleRegistry()


def register_style(record: CoverStyleRecord) -> None:
    """Register or replace a style record (startup / tests)."""
    with _lock:
        _records[record.id] = record


def _ensure_bootstrapped() -> None:
    global _bootstrapped
    if _bootstrapped:
        return
    with _lock:
        if _bootstrapped:
            return
        from travelogue.cover_engine.catalog import bootstrap_catalog

        bootstrap_catalog()
        _bootstrapped = True


def _effective(record: CoverStyleRecord) -> CoverStyleRecord:
    ov = _overrides.get(record.id) or {}
    if not ov:
        return record
    status = ov.get("status", record.status)
    sort_order = ov.get("sort_order", record.sort_order)
    if status == record.status and sort_order == record.sort_order:
        return record
    return CoverStyleRecord(
        id=record.id,
        label=record.label,
        status=status,
        sort_order=int(sort_order),
        studio_blurb=record.studio_blurb,
        narrow_fallback=record.narrow_fallback,
        closing_family=record.closing_family,
        css_hook=record.css_hook,
        profile=record.profile,
        preview_fixtures=record.preview_fixtures,
        legacy_aliases=record.legacy_aliases,
        studio_label=record.studio_label,
    )


def list_styles(*, status: CoverStyleStatus | None = None) -> list[CoverStyleRecord]:
    _ensure_bootstrapped()
    with _lock:
        rows = [_effective(r) for r in _records.values()]
    if status is not None:
        rows = [r for r in rows if r.status == status]
    rows.sort(key=lambda r: (r.sort_order, r.id))
    return rows


def list_assignable_styles() -> list[CoverStyleRecord]:
    return list_styles(status="active")


def get_style(style_id: str) -> CoverStyleRecord | None:
    _ensure_bootstrapped()
    raw = (style_id or "").strip()
    if not raw:
        return None
    with _lock:
        rec = _records.get(raw)
        return _effective(rec) if rec else None


def get_profile(style_id: str) -> CoverStyleProfile:
    rec = get_style(style_id)
    if rec is None:
        raise KeyError(f"unknown cover style: {style_id!r}")
    return rec.profile


def get_default_style_id() -> str:
    return _DEFAULT_STYLE_ID


def is_assignable(style_id: str) -> bool:
    rec = get_style(style_id)
    return rec is not None and rec.status == "active"


def set_style_status(style_id: str, status: CoverStyleStatus) -> None:
    if status not in ("draft", "active", "retired"):
        raise ValueError(f"invalid status: {status!r}")
    _ensure_bootstrapped()
    with _lock:
        if style_id not in _records:
            raise KeyError(f"unknown cover style: {style_id!r}")
        _overrides.setdefault(style_id, {})["status"] = status


def set_style_weight(style_id: str, sort_order: int) -> None:
    _ensure_bootstrapped()
    with _lock:
        if style_id not in _records:
            raise KeyError(f"unknown cover style: {style_id!r}")
        _overrides.setdefault(style_id, {})["sort_order"] = int(sort_order)


def reset_registry_for_tests(*, records: Iterable[CoverStyleRecord] | None = None) -> None:
    """Test helper: clear overrides and optionally replace catalog."""
    global _bootstrapped
    with _lock:
        _overrides.clear()
        if records is not None:
            _records.clear()
            for rec in records:
                _records[rec.id] = rec
            _bootstrapped = True
        else:
            _records.clear()
            _bootstrapped = False
