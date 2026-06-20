"""Dogfood A/B: legacy person-triple vs editorial portrait row (PRD PR-5)."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path

from travelogue.curation.editorial_portrait_row import (
    LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL,
    PATTERN_PORTRAIT_3,
    PATTERN_PORTRAIT_3_EDITORIAL,
    apply_editorial_row_slot_fits,
    editorial_row_screen_has_person,
)
from travelogue.render.engine import render_trip
from travelogue.services.validate import asset_map


@dataclass
class EditorialCompareResult:
    trip_dir: Path
    wrapper_html: Path
    legacy_panel: Path
    editorial_panel: Path


def _transform_screen_for_compare(
    screen: dict,
    *,
    mode: str,
    assets_map: dict[str, dict],
    trip: dict,
) -> dict:
    sc = copy.deepcopy(screen)
    pid = str(sc.get("patternId") or "")
    slots = sc.get("slots") or []
    if len(slots) != 3:
        return sc
    if pid not in (PATTERN_PORTRAIT_3, PATTERN_PORTRAIT_3_EDITORIAL):
        return sc

    if mode == "legacy":
        sc["patternId"] = PATTERN_PORTRAIT_3
        if editorial_row_screen_has_person(sc, assets_map):
            sc["layoutHint"] = "person-triple"
        else:
            sc.pop("layoutHint", None)
        return sc

    sc["patternId"] = PATTERN_PORTRAIT_3_EDITORIAL
    sc["layoutHint"] = LAYOUT_HINT_PORTRAIT_ROW_EDITORIAL
    return apply_editorial_row_slot_fits(sc, assets_map, trip=trip)


def transform_trip_for_editorial_compare(trip: dict, *, mode: str) -> dict:
    """Clone trip with portrait triple screens shown as legacy or editorial."""
    out = copy.deepcopy(trip)
    out["layoutEngine"] = "screens"
    assets_map = asset_map(out)
    for ch in out.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        screens = ch.get("screens") or []
        ch["screens"] = [
            _transform_screen_for_compare(
                sc, mode=mode, assets_map=assets_map, trip=out
            )
            for sc in screens
            if isinstance(sc, dict)
        ]
    return out


def _write_compare_wrapper(out_dir: Path, *, trip_title: str) -> Path:
    path = out_dir / "index-editorial-compare.html"
    path.write_text(
        f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>{trip_title} · Editorial Row A/B</title>
<style>
  :root {{ font-family: system-ui, "Segoe UI", sans-serif; background: #1a1a1a; color: #eee; }}
  body {{ margin: 0; padding: 16px 24px 32px; }}
  h1 {{ font-size: 1.1rem; font-weight: 600; margin: 0 0 8px; }}
  p {{ margin: 0 0 16px; color: #aaa; font-size: 0.9rem; }}
  .grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    min-height: calc(100vh - 120px);
  }}
  .panel {{ display: flex; flex-direction: column; min-height: 0; }}
  .panel h2 {{
    font-size: 0.85rem;
    font-weight: 500;
    margin: 0 0 8px;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #ccc;
  }}
  iframe {{
    flex: 1;
    width: 100%;
    min-height: 640px;
    border: 1px solid #444;
    border-radius: 6px;
    background: #f4f1ea;
  }}
  @media (max-width: 1100px) {{
    .grid {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
  <h1>{trip_title}</h1>
  <p>并排对比 legacy <code>person-triple</code> 与 <code>portrait-row-editorial</code>（同资产 · screens 引擎）</p>
  <div class="grid">
    <div class="panel">
      <h2>Legacy · screen-portrait-3 / person-triple</h2>
      <iframe src="panel-legacy.html" title="legacy person-triple"></iframe>
    </div>
    <div class="panel">
      <h2>Editorial · screen-portrait-3-editorial</h2>
      <iframe src="panel-editorial.html" title="editorial portrait row"></iframe>
    </div>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )
    return path


def compare_editorial_portrait_row(
    trip_path: Path | str,
    *,
    out_dir: Path | str | None = None,
) -> EditorialCompareResult:
    """
    Render side-by-side dogfood panels for portrait triple vs editorial row.

    Does not mutate the source trip.json on disk.
    """
    trip_file = Path(trip_path).resolve()
    if not trip_file.is_file():
        raise FileNotFoundError(f"trip.json not found: {trip_file}")
    trip_root = trip_file.parent
    compare_dir = Path(out_dir).resolve() if out_dir else trip_root / "editorial-compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    trip = json.loads(trip_file.read_text(encoding="utf-8"))
    title = str(trip.get("meta", {}).get("title") or trip.get("tripId") or "Trip")

    legacy_trip = transform_trip_for_editorial_compare(trip, mode="legacy")
    editorial_trip = transform_trip_for_editorial_compare(trip, mode="editorial")

    render_trip(
        trip_file,
        compare_dir,
        trip=legacy_trip,
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        index_name="panel-legacy.html",
    )
    render_trip(
        trip_file,
        compare_dir,
        trip=editorial_trip,
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        index_name="panel-editorial.html",
    )

    wrapper = _write_compare_wrapper(compare_dir, trip_title=title)
    return EditorialCompareResult(
        trip_dir=compare_dir,
        wrapper_html=wrapper,
        legacy_panel=compare_dir / "panel-legacy.html",
        editorial_panel=compare_dir / "panel-editorial.html",
    )
