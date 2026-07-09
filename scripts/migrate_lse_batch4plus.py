#!/usr/bin/env python3
"""One-shot LSE import migration (batch 4+)."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "travelogue"


def main() -> None:
    # planner_state shim
    shim_sls = '''"""Trip-level Web screens rhythm state (shim → layout_contract.planner_state)."""

from __future__ import annotations

import importlib

_mod = importlib.import_module("travelogue.layout_contract.planner_state")
__all__ = list(_mod.__all__)
for _name in __all__:
    globals()[_name] = getattr(_mod, _name)
'''
    (ROOT / "curation/screen_layout_state.py").write_text(shim_sls, encoding="utf-8")

    # chapter_items
    ci_src = (ROOT / "curation/chapter_items.py").read_text(encoding="utf-8")
    if "layout_contract.chapter_items" not in ci_src:
        ci_end = ci_src.index("\ndef resolve_chapter_items_for_render")
        kernel = ci_src[ci_src.index("from __future__") : ci_end]
        (ROOT / "layout_contract/chapter_items.py").write_text(
            '"""Compact chapter items helpers (layout kernel)."""\n\n' + kernel,
            encoding="utf-8",
        )
        tail = ci_src[ci_end:]
        (ROOT / "curation/chapter_items.py").write_text(
            '"""Compact chapter items (shim + render resolver)."""\n\n'
            "from travelogue.layout_contract.chapter_items import *  # noqa: F403\n\n"
            + tail.lstrip(),
            encoding="utf-8",
        )

    # aspect_buckets
    ab = (ROOT / "curation/aspect_buckets.py").read_text(encoding="utf-8")
    if "layout_contract" not in ab:
        (ROOT / "layout_contract/aspect_buckets.py").write_text(
            ab.replace(
                '"""Landscape aspect-ratio buckets',
                '"""Landscape aspect-ratio buckets (layout kernel).',
            ),
            encoding="utf-8",
        )
        (ROOT / "curation/aspect_buckets.py").write_text(
            '"""Shim → layout_contract.aspect_buckets."""\n'
            "from travelogue.layout_contract.aspect_buckets import *  # noqa: F403\n",
            encoding="utf-8",
        )

    # burst
    bu_path = ROOT / "curation/burst_utils.py"
    if "layout_contract" not in bu_path.read_text(encoding="utf-8"):
        bu = bu_path.read_text(encoding="utf-8").replace(
            "from travelogue.curation.asset_quality import asset_sharpness",
            "from travelogue.media.quality import asset_sharpness",
        )
        (ROOT / "layout_contract/burst.py").write_text(
            bu.replace('"""Shared burst detection', '"""Shared burst detection (layout kernel).'),
            encoding="utf-8",
        )
        bu_path.write_text(
            '"""Shim → layout_contract.burst."""\n'
            "from travelogue.layout_contract.burst import *  # noqa: F403\n",
            encoding="utf-8",
        )

    # collage_routing
    cr_path = ROOT / "curation/collage_routing.py"
    if "layout_contract" not in cr_path.read_text(encoding="utf-8"):
        cr = cr_path.read_text(encoding="utf-8").replace(
            "from travelogue.curation.media_classify import",
            "from travelogue.media.media_classify import",
        )
        (ROOT / "layout_contract/collage_routing.py").write_text(
            cr.replace('"""Collage asset routing', '"""Collage asset routing (layout kernel).'),
            encoding="utf-8",
        )
        cr_path.write_text(
            '"""Shim → layout_contract.collage_routing."""\n'
            "from travelogue.layout_contract.collage_routing import *  # noqa: F403\n",
            encoding="utf-8",
        )

    # layout_metrics kernel
    lm_kernel = '''"""Layout metrics pure helpers (layout kernel)."""

from __future__ import annotations


def _screen_pattern_ids(chapters: list[dict]) -> list[str]:
    ids: list[str] = []
    for ch in chapters:
        for s in ch.get("screens") or []:
            pid = s.get("patternId")
            if pid:
                ids.append(pid)
    return ids


def pattern_diversity(chapters: list[dict]) -> float:
    pids = _screen_pattern_ids(chapters)
    if not pids:
        return 0.0
    return len(set(pids)) / len(pids)


def chapter_distinct_pattern_counts(chapters: list[dict]) -> list[int]:
    counts: list[int] = []
    for ch in chapters:
        pids = {
            str(s.get("patternId"))
            for s in ch.get("screens") or []
            if s.get("patternId")
        }
        if pids:
            counts.append(len(pids))
    return counts


def pattern_diversity_p50(chapters: list[dict]) -> float:
    counts = chapter_distinct_pattern_counts(chapters)
    if not counts:
        return 0.0
    counts.sort()
    mid = len(counts) // 2
    if len(counts) % 2:
        return float(counts[mid])
    return (counts[mid - 1] + counts[mid]) / 2.0
'''
    (ROOT / "layout_contract/layout_metrics.py").write_text(lm_kernel, encoding="utf-8")

    # scoring helpers
    scoring_path = ROOT / "layout_contract/scoring.py"
    scoring = scoring_path.read_text(encoding="utf-8")
    if "def median_sharpness" not in scoring:
        scoring_path.write_text(
            scoring.rstrip()
            + '''

def median_sharpness(assets: list[dict]) -> float:
    from travelogue.media.quality import asset_sharpness

    values = [asset_sharpness(a) for a in assets if asset_sharpness(a) > 0]
    if not values:
        return 0.0
    values.sort()
    mid = len(values) // 2
    if len(values) % 2:
        return values[mid]
    return (values[mid - 1] + values[mid]) / 2.0


def sort_bucket_asset_ids(bucket: list[str], assets_by_id: dict[str, dict]) -> list[str]:
    from travelogue.media.quality import asset_sharpness

    items = [(aid, assets_by_id.get(aid, {})) for aid in bucket]
    items.sort(key=lambda x: x[1].get("takenAt") or "")
    result: list[str] = []
    i = 0
    while i < len(items):
        aid, a = items[i]
        bg = a.get("burstGroupId")
        if bg:
            group_ids = [aid]
            j = i + 1
            while j < len(items) and items[j][1].get("burstGroupId") == bg:
                group_ids.append(items[j][0])
                j += 1
            group_ids.sort(key=lambda x: -asset_sharpness(assets_by_id.get(x, {})))
            result.extend(group_ids)
            i = j
        else:
            result.append(aid)
            i += 1
    return result
''',
            encoding="utf-8",
        )

    # constraints
    cons_path = ROOT / "layout_contract/constraints.py"
    cons = cons_path.read_text(encoding="utf-8")
    if "plan_violates_consecutive_pattern" not in cons:
        cons_path.write_text(
            cons.rstrip()
            + '''

DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN = 2


def max_consecutive_pattern_streak(screens: list[dict]) -> int:
    streak = 0
    best = 0
    prev: str | None = None
    for screen in screens:
        pid = screen.get("patternId")
        if not pid:
            streak = 0
            prev = None
            continue
        if pid == prev:
            streak += 1
        else:
            streak = 1
            prev = pid
        best = max(best, streak)
    return best


def plan_violates_consecutive_pattern(
    screens: list[dict],
    *,
    max_streak: int = DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN,
) -> bool:
    return max_consecutive_pattern_streak(screens) > max_streak
''',
            encoding="utf-8",
        )

    # feedback
    fb_path = ROOT / "curation/feedback.py"
    if "layout_contract.feedback" not in fb_path.read_text(encoding="utf-8"):
        fb_src = fb_path.read_text(encoding="utf-8")
        fb_cut = fb_src.index("\ndef record_g1_edit")
        (ROOT / "layout_contract/feedback.py").write_text(
            fb_src[:fb_cut].replace(
                '"""G1 edit-distance feedback',
                '"""G1 edit-distance feedback (layout kernel).',
            ),
            encoding="utf-8",
        )
        fb_path.write_text(
            "from travelogue.layout_contract.feedback import *  # noqa: F403\n"
            + fb_src[fb_cut + 1 :],
            encoding="utf-8",
        )

    # beam_scoring
    beam_path = ROOT / "layout_engine/planner/beam_scoring.py"
    if not beam_path.is_file():
        ls = (ROOT / "curation/layout_scoring.py").read_text(encoding="utf-8")
        header_end = ls.index("\ndef _plan_screen_key")
        header = ls[:header_end]
        beam_body = ls[header_end + 1 :]
        beam_header = '''"""Beam / screen-plan scoring (layout_engine)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from travelogue.layout_contract.orientations import AspectKind
from travelogue.layout_contract.scoring import (
    FEATURED_BEAM_BONUS_PER_ASSET,
    FEATURED_HERO_SEPARATION_HALVED,
    IncrementalScoreState,
    ScoreBreakdown,
    ScoringWeights,
    moment_secondary_plan_bonus,
    screen_dominant_tone,
)

'''
        beam_path.write_text(beam_header + beam_body, encoding="utf-8")
        beam_text = beam_path.read_text(encoding="utf-8").replace(
            "from travelogue.curation.burst_utils import ingest_burst_group_id",
            "from travelogue.layout_contract.burst import ingest_burst_group_id",
        )
        beam_path.write_text(beam_text, encoding="utf-8")
        reexports = '''

from travelogue.layout_engine.planner.beam_scoring import (  # noqa: F401
    rank_screens,
    score_screen,
    score_screen_plan,
)

__all__ = [
    "FEATURED_BEAM_BONUS_PER_ASSET",
    "FEATURED_HERO_SEPARATION_HALVED",
    "IncrementalScoreState",
    "PHASE2_WEIGHTS",
    "PHASE3_WEIGHTS",
    "PHASE3B_WEIGHTS",
    "PHASE6_WEIGHTS",
    "ScoreBreakdown",
    "ScoringWeights",
    "moment_secondary_plan_bonus",
    "rank_screens",
    "resolve_scoring_weights",
    "score_screen",
    "score_screen_plan",
    "screen_dominant_tone",
]
'''
        (ROOT / "curation/layout_scoring.py").write_text(header + reexports, encoding="utf-8")

    # evaluator
    eval_dst = ROOT / "layout_engine/usage_rules/evaluator.py"
    if not eval_dst.is_file():
        eval_src = (ROOT / "curation/usage_rules/evaluator.py").read_text(encoding="utf-8")
        eval_src = eval_src.replace(
            "from travelogue.curation.mosaic.main_eligibility import asset_native_ar",
            "from travelogue.layout_engine.mosaic.main_eligibility import asset_native_ar",
        )
        eval_dst.parent.mkdir(parents=True, exist_ok=True)
        (eval_dst.parent / "__init__.py").write_text(
            '"""Usage rule evaluation (layout_engine)."""\n', encoding="utf-8"
        )
        eval_dst.write_text(eval_src, encoding="utf-8")
        (ROOT / "curation/usage_rules/evaluator.py").write_text(
            '"""Shim → layout_engine.usage_rules.evaluator."""\n'
            "from travelogue.layout_engine.usage_rules.evaluator import *  # noqa: F403\n",
            encoding="utf-8",
        )

    # curate_scoring dedupe
    cs_path = ROOT / "curation/curate_scoring.py"
    cs = cs_path.read_text(encoding="utf-8")
    if "from travelogue.layout_contract.scoring import median_sharpness" not in cs:
        cs = cs.replace(
            "from travelogue.curation.asset_quality import asset_sharpness",
            "from travelogue.curation.asset_quality import asset_sharpness\n"
            "from travelogue.layout_contract.scoring import median_sharpness, sort_bucket_asset_ids",
        )
        cs = re.sub(
            r"\ndef median_sharpness\(assets: list\[dict\]\) -> float:.*?"
            r"\n    return \(values\[mid - 1\] \+ values\[mid\]\) / 2\.0\n",
            "\n",
            cs,
            count=1,
            flags=re.S,
        )
        cs = re.sub(
            r"\ndef sort_bucket_asset_ids\(bucket: list\[str\], assets_by_id: dict\[str, dict\]\) -> list\[str\]:.*?"
            r"\n    return result\n",
            "\n",
            cs,
            count=1,
            flags=re.S,
        )
        cs_path.write_text(cs, encoding="utf-8")

    # layout_engine redirects
    repl = [
        ("from travelogue.curation.screen_layout_state import", "from travelogue.layout_contract.planner_state import"),
        ("from travelogue.curation.chapter_items import", "from travelogue.layout_contract.chapter_items import"),
        ("from travelogue.curation.aspect_buckets import", "from travelogue.layout_contract.aspect_buckets import"),
        ("from travelogue.curation.collage_routing import", "from travelogue.layout_contract.collage_routing import"),
        (
            "from travelogue.curation.layout_metrics import pattern_diversity_p50",
            "from travelogue.layout_contract.layout_metrics import pattern_diversity_p50",
        ),
        (
            "from travelogue.curation.layout_scoring import score_screen_plan",
            "from travelogue.layout_engine.planner.beam_scoring import score_screen_plan",
        ),
        (
            "from travelogue.curation.usage_rules.evaluator import",
            "from travelogue.layout_engine.usage_rules.evaluator import",
        ),
        (
            "from travelogue.curation.curate_scoring import sort_bucket_asset_ids",
            "from travelogue.layout_contract.scoring import sort_bucket_asset_ids",
        ),
        ("from travelogue.curation.feedback import", "from travelogue.layout_contract.feedback import"),
        (
            "from travelogue.curation.layout_constraints import plan_violates_consecutive_pattern",
            "from travelogue.layout_contract.constraints import plan_violates_consecutive_pattern",
        ),
        (
            "from travelogue.curation.longshot_filter import BREATH_PATTERN",
            "from travelogue.layout_contract.rhythm import BREATH_PATTERN",
        ),
        ("from travelogue.curation.burst_utils import", "from travelogue.layout_contract.burst import"),
    ]
    for py in (ROOT / "layout_engine").rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        orig = text
        text = re.sub(
            r"from travelogue\.curation\.curate_scoring import effective_hero_score, median_sharpness",
            "from travelogue.curation.curate_scoring import effective_hero_score\n"
            "from travelogue.layout_contract.scoring import median_sharpness",
            text,
        )
        text = re.sub(
            r"from travelogue\.curation\.curate_scoring import median_sharpness",
            "from travelogue.layout_contract.scoring import median_sharpness",
            text,
        )
        for old, new in repl:
            text = text.replace(old, new)
        if text != orig:
            py.write_text(text, encoding="utf-8")

    print("done")


if __name__ == "__main__":
    main()
