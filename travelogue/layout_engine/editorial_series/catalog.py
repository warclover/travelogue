"""Official series catalog. Engine never scans ``docs/templates/reserve/``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.layout_engine.editorial_series.intake import (
    SeriesIntakeError,
    accept_series_document,
)
from travelogue.layout_engine.editorial_series.match import photo_span, series_capacity
from travelogue.paths import ROOT

# Runtime series live next to this package (P0: magazine-16-standard).
SERIES_DIR = Path(__file__).resolve().parent / "series"


def official_series_dir() -> Path:
    return SERIES_DIR


def load_official_series(*, series_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load ``*.yaml`` from the official series directory.

    Atelier ``folio-*`` files are skipped. Other invalid magazine YAML is
    skipped so one bad drop-in cannot poison a valid neighbor.
    """
    root = series_dir or official_series_dir()
    assert_not_reserve_path(root)
    if not root.is_dir():
        return []
    try:
        import yaml
    except ImportError:  # pragma: no cover
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        if not isinstance(data, dict):
            continue
        data.setdefault("id", path.stem)
        try:
            accepted = accept_series_document(data, source_name=path.name)
        except SeriesIntakeError:
            continue
        if accepted is None:
            continue
        out.append(accepted)
    return out


def min_photo_span_lo(catalog: list[dict[str, Any]] | None = None) -> int | None:
    """Smallest ``photo_span`` lower bound in *catalog* (advisory copy only)."""
    rows = catalog if catalog is not None else load_official_series()
    lows: list[int] = []
    for row in rows:
        lo, _hi = photo_span(row)
        if lo > 0:
            lows.append(lo)
    return min(lows) if lows else None


def min_capacity(catalog: list[dict[str, Any]] | None = None) -> int | None:
    """Smallest baked ``capacity`` (BLK-MSP-05 · wizard grey-out)."""
    rows = catalog if catalog is not None else load_official_series()
    caps = [series_capacity(row) for row in rows]
    caps = [n for n in caps if n > 0]
    return min(caps) if caps else None


def assert_not_reserve_path(path: Path) -> None:
    """ISO-05 · refuse any path under the atelier tree."""
    reserve = (ROOT / "docs" / "templates" / "reserve").resolve()
    try:
        path.resolve().relative_to(reserve)
    except ValueError:
        return
    raise ValueError("editorial_series must not read docs/templates/reserve/")
