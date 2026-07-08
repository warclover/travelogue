#!/usr/bin/env python3
"""LSE batch-5: editorial + scoring adapter layer → layout_engine."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "travelogue"


def _git_show(rel: str) -> str:
    p = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        capture_output=True,
        check=True,
        cwd=ROOT.parent,
    )
    return p.stdout.decode("utf-8")


def _write(rel: Path, text: str) -> None:
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_text(text, encoding="utf-8")


def _shim(module: str, target: str) -> str:
    return (
        f'"""Shim → {target}."""\n\n'
        f"from {target} import *  # noqa: F403\n"
    )


def main() -> None:
    # --- scoring adapters ---
    hero = '''"""Hero score adapter (layout_engine · delegates to curation kernel)."""

from __future__ import annotations

from typing import Any

from travelogue.layout_contract.scoring import median_sharpness as median_sharpness  # noqa: F401


def effective_hero_score(
    asset: dict,
    *,
    median_sharp: float = 0.0,
    aesthetic_enabled: bool | None = None,
    featured_weight: float = 1.35,
    memory_anchors: list[str] | None = None,
    meta_places: list[str] | None = None,
    cover_scoring_v2: Any = None,
    scoring_version: str | None = None,
    pool: list[dict] | None = None,
) -> float:
    from travelogue.curation.curate_scoring import effective_hero_score as _score

    return _score(
        asset,
        median_sharp=median_sharp,
        aesthetic_enabled=aesthetic_enabled,
        featured_weight=featured_weight,
        memory_anchors=memory_anchors,
        meta_places=meta_places,
        cover_scoring_v2=cover_scoring_v2,
        scoring_version=scoring_version,
        pool=pool,
    )
'''
    _write(ROOT / "layout_engine/scoring/__init__.py", '"""Layout scoring adapters."""\n')
    _write(ROOT / "layout_engine/scoring/hero.py", hero)

    aesthetic = '''"""Aesthetic score adapter."""

from __future__ import annotations


def aesthetic_overall(asset: dict) -> float | None:
    from travelogue.curation.aesthetic_score import aesthetic_overall as _fn

    return _fn(asset)
'''
    _write(ROOT / "layout_engine/scoring/aesthetic.py", aesthetic)

    # solo_scoring → layout_engine/scoring/solo.py
    solo_src = _git_show("travelogue/curation/solo_scoring.py")
    solo_src = solo_src.replace(
        "from travelogue.curation.asset_quality import asset_sharpness",
        "from travelogue.media.quality import asset_sharpness",
    )
    _write(ROOT / "layout_engine/scoring/solo.py", solo_src)
    _write(
        ROOT / "curation/solo_scoring.py",
        _shim("solo_scoring", "travelogue.layout_engine.scoring.solo"),
    )

    # editorial_portrait_row
    epr_src = _git_show("travelogue/curation/editorial_portrait_row.py")
    epr_src = epr_src.replace(
        "from travelogue.curation.asset_subject import asset_has_person",
        "from travelogue.layout_contract.subject import asset_has_person",
    )
    _write(ROOT / "layout_engine/editorial/__init__.py", '"""Editorial layout hooks."""\n')
    _write(ROOT / "layout_engine/editorial/portrait_row.py", epr_src)
    _write(
        ROOT / "curation/editorial_portrait_row.py",
        _shim("editorial_portrait_row", "travelogue.layout_engine.editorial.portrait_row"),
    )

    # editorial_4mix
    e4_src = _git_show("travelogue/curation/editorial_4mix.py")
    e4_src = e4_src.replace(
        "from travelogue.curation.asset_subject import asset_has_person",
        "from travelogue.layout_contract.subject import asset_has_person",
    )
    e4_src = e4_src.replace(
        "from travelogue.curation.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2",
        "from travelogue.layout_engine.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2",
    )
    e4_src = e4_src.replace(
        "    from travelogue.curation.layout_planner import AspectKind\n",
        "    from travelogue.layout_contract.orientations import AspectKind\n",
    )
    e4_src = e4_src.replace(
        "    from travelogue.curation.layout_planner import aspect_kind_for_asset\n",
        "    from travelogue.layout_contract.orientations import aspect_kind_for_asset\n",
    )
    e4_src = e4_src.replace(
        "    from travelogue.curation.curate_scoring import effective_hero_score, median_sharpness\n",
        "    from travelogue.layout_engine.scoring.hero import effective_hero_score\n"
        "    from travelogue.layout_contract.scoring import median_sharpness\n",
    )
    e4_src = e4_src.replace(
        "    from travelogue.curation.screen_planner import (\n"
        "        _is_landscape_id,\n"
        "        _is_std_portrait_id,\n"
        "    )\n"
        "    from travelogue.curation.mosaic.builders import _sort_asset_ids_by_taken\n",
        "    from travelogue.layout_engine.planner.screen_planner import (\n"
        "        _is_landscape_id,\n"
        "        _is_std_portrait_id,\n"
        "    )\n"
        "    from travelogue.layout_engine.mosaic.builders import _sort_asset_ids_by_taken\n",
    )
    e4_src = re.sub(
        r"from travelogue\.curation\.layout_planner import AspectKind",
        "from travelogue.layout_contract.orientations import AspectKind",
        e4_src,
    )
    _write(ROOT / "layout_engine/editorial/four_mix.py", e4_src)
    _write(
        ROOT / "curation/editorial_4mix.py",
        _shim("editorial_4mix", "travelogue.layout_engine.editorial.four_mix"),
    )

    # Redirect layout_engine importers
    replacements = [
        (
            "from travelogue.curation.curate_scoring import effective_hero_score",
            "from travelogue.layout_engine.scoring.hero import effective_hero_score",
        ),
        (
            "from travelogue.curation.solo_scoring import",
            "from travelogue.layout_engine.scoring.solo import",
        ),
        (
            "from travelogue.curation.editorial_portrait_row import",
            "from travelogue.layout_engine.editorial.portrait_row import",
        ),
        (
            "from travelogue.curation.editorial_4mix import",
            "from travelogue.layout_engine.editorial.four_mix import",
        ),
        (
            "from travelogue.curation.aesthetic_score import aesthetic_overall",
            "from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall",
        ),
    ]
    targets = list((ROOT / "layout_engine").rglob("*.py"))
    targets.append(ROOT / "layout_contract/planner_state.py")
    for path in targets:
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in replacements:
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")

    print("batch-5 migration done")


if __name__ == "__main__":
    main()
