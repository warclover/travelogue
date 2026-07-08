"""Dogfood A/B: legacy p2l2 vs screen-editorial-4mix (PRD PR-6)."""

from __future__ import annotations

import copy
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from travelogue.curation.editorial_4mix import (
    LAYOUT_HINT_EDITORIAL_4MIX,
    PATTERN_EDITORIAL_4MIX,
    apply_editorial_4mix_slot_fits,
    build_4mix_slots,
    chess_order_asset_ids,
    chess_window_matches,
)
from travelogue.curation.layout_planner import aspect_kind_for_asset
from travelogue.layout_engine.mosaic.builders import build_screen
from travelogue.layout_engine.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2
from travelogue.layout_engine.mosaic.pattern_catalog import default_registry
from travelogue.render.engine import render_trip
from travelogue.services.validate import asset_map


@dataclass
class Editorial4MixCompareResult:
    trip_dir: Path
    wrapper_html: Path
    legacy_panel: Path
    editorial_panel: Path


def _mixed_four_screen(screen: dict) -> dict | None:
    slots = screen.get("slots") or []
    if len(slots) != 4:
        return None
    pid = str(screen.get("patternId") or "")
    if pid not in (PATTERN_EDITORIAL_4MIX, PATTERN_PORTRAIT_2_LANDSCAPE_2):
        return None
    return screen


def _transform_screen_for_4mix_compare(
    screen: dict,
    *,
    mode: str,
    assets_map: dict[str, dict],
    aspects: dict[str, str],
    trip: dict,
) -> dict:
    src = _mixed_four_screen(screen)
    if not src:
        return copy.deepcopy(screen)

    sc = copy.deepcopy(src)
    asset_ids = [str(s.get("assetId") or "") for s in sc.get("slots") or [] if s.get("assetId")]
    if not chess_window_matches(asset_ids, assets_map, aspects=aspects):  # type: ignore[arg-type]
        return sc

    base = {
        k: v
        for k, v in sc.items()
        if k not in ("patternId", "slots", "layoutHint", "layoutGeometry")
    }

    if mode == "legacy":
        reg = default_registry()
        pattern = reg[PATTERN_PORTRAIT_2_LANDSCAPE_2]
        legacy = build_screen(
            pattern,
            asset_ids,
            assets_map=assets_map,
            screen_id=str(base.get("screenId") or ""),
        )
        legacy.update({k: v for k, v in base.items() if k not in legacy})
        return legacy

    ordered = chess_order_asset_ids(asset_ids, assets_map, aspects=aspects)  # type: ignore[arg-type]
    if not ordered:
        return sc
    out = dict(base)
    out["patternId"] = PATTERN_EDITORIAL_4MIX
    out["layoutHint"] = LAYOUT_HINT_EDITORIAL_4MIX
    out["slots"] = build_4mix_slots(ordered, assets_map)
    out["layoutGeometry"] = {"gridClass": "layout-screen__grid--editorial-4mix"}
    return apply_editorial_4mix_slot_fits(out, assets_map, trip=trip)


def transform_trip_for_4mix_compare(trip: dict, *, mode: str) -> dict:
    """Clone trip with 2L+2P screens shown as p2l2 or editorial-4mix."""
    out = copy.deepcopy(trip)
    out["layoutEngine"] = "screens"
    if mode == "editorial":
        export = out.setdefault("export", {})
        export["editorial4Mix"] = True
    assets_map = asset_map(out)
    aspects = {
        a["id"]: aspect_kind_for_asset(a)
        for a in out.get("assets") or []
        if a.get("id")
    }
    for ch in out.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        screens = ch.get("screens") or []
        ch["screens"] = [
            _transform_screen_for_4mix_compare(
                sc,
                mode=mode,
                assets_map=assets_map,
                aspects=aspects,
                trip=out,
            )
            for sc in screens
            if isinstance(sc, dict)
        ]
    return out


def _write_compare_wrapper(out_dir: Path, *, trip_title: str) -> Path:
    path = out_dir / "index-editorial-4mix-compare.html"
    path.write_text(
        f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<title>{trip_title} · Editorial 4mix A/B</title>
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
  <p>并排对比 legacy <code>portrait-2-landscape-2</code> 与 <code>screen-editorial-4mix</code>（同资产 · screens 引擎）</p>
  <div class="grid">
    <div class="panel">
      <h2>Legacy · screen-portrait-2-landscape-2</h2>
      <iframe src="panel-legacy.html" title="legacy p2l2"></iframe>
    </div>
    <div class="panel">
      <h2>Editorial · screen-editorial-4mix</h2>
      <iframe src="panel-editorial.html" title="editorial 4mix"></iframe>
    </div>
  </div>
</body>
</html>
""",
        encoding="utf-8",
    )
    return path


def _sync_compare_assets(trip_root: Path, compare_dir: Path) -> None:
    """Copy trip assets beside panel HTML so relative src= paths resolve under file://."""
    trip_root = trip_root.resolve()
    compare_dir = compare_dir.resolve()
    if compare_dir == trip_root:
        return
    for name in ("assets", "source"):
        src = trip_root / name
        if src.is_dir():
            shutil.copytree(src, compare_dir / name, dirs_exist_ok=True)


def compare_editorial_4mix(
    trip_path: Path | str,
    *,
    out_dir: Path | str | None = None,
) -> Editorial4MixCompareResult:
    """Render side-by-side dogfood panels for p2l2 vs editorial-4mix."""
    trip_file = Path(trip_path).resolve()
    if not trip_file.is_file():
        raise FileNotFoundError(f"trip.json not found: {trip_file}")
    compare_dir = Path(out_dir).resolve() if out_dir else trip_file.parent / "editorial-4mix-compare"
    compare_dir.mkdir(parents=True, exist_ok=True)

    trip = json.loads(trip_file.read_text(encoding="utf-8"))
    title = str(trip.get("meta", {}).get("title") or trip.get("tripId") or "Trip")

    legacy_trip = transform_trip_for_4mix_compare(trip, mode="legacy")
    editorial_trip = transform_trip_for_4mix_compare(trip, mode="editorial")

    render_trip(
        trip_file,
        compare_dir,
        trip=legacy_trip,
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        reading_profile_override="legacy",
        index_name="panel-legacy.html",
    )
    render_trip(
        trip_file,
        compare_dir,
        trip=editorial_trip,
        validate=False,
        layout_engine="screens",
        export_layout_override="web",
        reading_profile_override="legacy",
        index_name="panel-editorial.html",
    )

    _sync_compare_assets(trip_file.parent, compare_dir)

    wrapper = _write_compare_wrapper(compare_dir, trip_title=title)
    return Editorial4MixCompareResult(
        trip_dir=compare_dir,
        wrapper_html=wrapper,
        legacy_panel=compare_dir / "panel-legacy.html",
        editorial_panel=compare_dir / "panel-editorial.html",
    )
