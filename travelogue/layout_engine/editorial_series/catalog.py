"""Official series catalog. Engine never scans ``docs/templates/reserve/``."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from travelogue.paths import ROOT

# Runtime series live next to this package — empty until TSU / AS-PFM-01 ships.
SERIES_DIR = Path(__file__).resolve().parent / "series"


def official_series_dir() -> Path:
    return SERIES_DIR


def load_official_series(*, series_dir: Path | None = None) -> list[dict[str, Any]]:
    """Load ``*.yaml`` from the official series directory.

    Skips files whose id starts with ``folio-`` (atelier trial prefix).
    """
    root = series_dir or official_series_dir()
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
        sid = str(data.get("id") or path.stem).strip()
        if sid.startswith("folio-"):
            continue
        data.setdefault("id", sid)
        out.append(data)
    return out


def assert_not_reserve_path(path: Path) -> None:
    """ISO-05 · refuse any path under the atelier tree."""
    reserve = (ROOT / "docs" / "templates" / "reserve").resolve()
    try:
        path.resolve().relative_to(reserve)
    except ValueError:
        return
    raise ValueError("editorial_series must not read docs/templates/reserve/")
