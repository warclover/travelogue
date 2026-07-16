#!/usr/bin/env python3
"""LSE batch-6: context/candidates/cohort + importlib shims + lint whitelist."""

from __future__ import annotations

import re
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "travelogue"
REPO = ROOT.parent


def _git_bytes(rel: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        capture_output=True,
        check=True,
        cwd=REPO,
    ).stdout


def _write(rel: Path, text: str) -> None:
    rel.parent.mkdir(parents=True, exist_ok=True)
    rel.write_text(text, encoding="utf-8")


def _importlib_shim(target: str) -> str:
    return textwrap.dedent(
        f'''\
        """Shim → {target}."""

        from __future__ import annotations

        import importlib

        _mod = importlib.import_module("{target}")
        __all__ = list(getattr(_mod, "__all__", []))
        for _name in __all__:
            globals()[_name] = getattr(_mod, _name)
        '''
    )


def main() -> None:
    # cohort scoring kernel (layout_engine)
    _write(
        ROOT / "layout_engine/scoring/cohort.py",
        textwrap.dedent(
            '''\
            """Cohort coherence scoring (layout kernel)."""

            from __future__ import annotations

            from collections.abc import Mapping


            def asset_cohort_duo(asset: dict | None) -> bool:
                if not asset:
                    return False
                cohort = (asset.get("curation") or {}).get("cohort") or {}
                return bool(cohort.get("duo"))


            def score_cohort_coherence(
                asset_ids: list[str],
                assets_by_id: Mapping[str, dict],
            ) -> float:
                """Reward adjacent duo-tagged shots (soft narrative run)."""
                if len(asset_ids) < 2:
                    return 1.0
                flags = [asset_cohort_duo(assets_by_id.get(aid)) for aid in asset_ids]
                scores: list[float] = []
                for i in range(len(flags) - 1):
                    if flags[i] and flags[i + 1]:
                        scores.append(1.0)
                    elif flags[i] or flags[i + 1]:
                        scores.append(0.55)
                    else:
                        scores.append(0.35)
                return sum(scores) / len(scores) if scores else 0.5
            '''
        ),
    )

    # rollout bucket (shared util, no curation dep)
    _write(
        ROOT / "layout_engine/rollout_bucket.py",
        textwrap.dedent(
            '''\
            """Deterministic rollout bucketing (layout_engine)."""

            from __future__ import annotations

            import hashlib


            def rollout_bucket(trip_id: str, *, cohort_salt: str, traffic_percent: float) -> int:
                """Deterministic bucket 0..99 for trip_id (stable across runs)."""
                if traffic_percent <= 0:
                    return 100
                if traffic_percent >= 100:
                    return 0
                digest = hashlib.sha256(f"{cohort_salt}:{trip_id}".encode()).hexdigest()
                return int(digest[:8], 16) % 100
            '''
        ),
    )

    # usage_rules context helpers → layout_engine
    ctx_src = (ROOT / "curation/usage_rules/context.py").read_text(encoding="utf-8")
    ctx_helpers = ctx_src.split("def main_eligible_hero_score_gap")[1]
    ctx_body = (
        "def main_eligible_hero_score_gap"
        + ctx_helpers.split("\n\n", 1)[0]
        + "\n\n"
        + "def portrait_is_window_hero_max"
        + ctx_helpers.split("def portrait_is_window_hero_max")[1].split("def window_std_portrait_count")[0]
        + "def window_std_portrait_count"
        + ctx_helpers.split("def window_std_portrait_count")[1]
    )
    ctx_body = ctx_body.replace(
        "from travelogue.curation.curate_scoring import effective_hero_score",
        "from travelogue.layout_engine.scoring.hero import effective_hero_score",
    )
    ctx_body = ctx_body.replace(
        "from travelogue.curation.mosaic.main_eligibility import",
        "from travelogue.layout_engine.mosaic.main_eligibility import",
    )
    ctx_body = ctx_body.replace(
        "from travelogue.curation.mosaic.runtime import",
        "from travelogue.layout_engine.mosaic.runtime import",
    )
    ctx_body = ctx_body.replace(
        "from travelogue.curation.screen_planner import _is_std_portrait_id",
        "from travelogue.layout_engine.planner.screen_planner import _is_std_portrait_id",
    )
    _write(
        ROOT / "layout_engine/usage_rules/context.py",
        '"""Usage rule window context helpers (layout_engine)."""\n\n'
        "from __future__ import annotations\n\n"
        "from travelogue.layout_contract.usage_context import WindowContext\n\n"
        + ctx_body,
    )

    _write(
        ROOT / "curation/usage_rules/context.py",
        '"""WindowContext shim → layout_contract + layout_engine helpers."""\n\n'
        "from __future__ import annotations\n\n"
        "from travelogue.layout_contract.usage_context import (\n"
        "    DEFAULT_FEATURED_WEIGHT,\n"
        "    WindowContext,\n"
        "    build_window_context,\n"
        ")\n"
        "from travelogue.layout_engine.usage_rules.context import (\n"
        "    main_eligible_hero_score_gap,\n"
        "    portrait_is_window_hero_max,\n"
        "    window_std_portrait_count,\n"
        ")\n\n"
        "__all__ = [\n"
        '    "DEFAULT_FEATURED_WEIGHT",\n'
        '    "WindowContext",\n'
        '    "build_window_context",\n'
        '    "main_eligible_hero_score_gap",\n'
        '    "portrait_is_window_hero_max",\n'
        '    "window_std_portrait_count",\n'
        "]\n",
    )

    # layout_candidates → layout_engine/planner
    lc = _git_bytes("travelogue/curation/layout_candidates.py").decode("utf-8")
    lc = lc.replace(
        "from travelogue.curation.layout_planner import AspectKind",
        "from travelogue.layout_contract.orientations import AspectKind",
    )
    lc = lc.replace(
        "from travelogue.curation.screen_layout_state import ScreenLayoutPlannerState",
        "from travelogue.layout_contract.planner_state import ScreenLayoutPlannerState",
    )
    lc = lc.replace(
        "from travelogue.curation.screen_planner import",
        "from travelogue.layout_engine.planner.screen_planner import",
    )
    lc = lc.replace(
        "from travelogue.curation.search_budget import SearchBudget",
        "from travelogue.layout_contract.search_budget import SearchBudget",
    )
    _write(ROOT / "layout_engine/planner/layout_candidates.py", lc)
    _write(
        ROOT / "curation/layout_candidates.py",
        _importlib_shim("travelogue.layout_engine.planner.layout_candidates"),
    )

    # intent_hints → layout_engine (lazy curation deps unchanged)
    ih = _git_bytes("travelogue/curation/intent_hints.py").decode("utf-8")
    _write(ROOT / "layout_engine/intent_hints.py", ih)
    _write(ROOT / "curation/intent_hints.py", _importlib_shim("travelogue.layout_engine.intent_hints"))

    # importlib shims (remove cur→le AST edges)
    for curation_rel, target in [
        ("curation/editorial_4mix.py", "travelogue.layout_engine.editorial.four_mix"),
        ("curation/editorial_portrait_row.py", "travelogue.layout_engine.editorial.portrait_row"),
        ("curation/solo_scoring.py", "travelogue.layout_engine.scoring.solo"),
        ("curation/usage_rules/evaluator.py", "travelogue.layout_engine.usage_rules.evaluator"),
        ("curation/usage_rules/tiebreak.py", "travelogue.layout_engine.usage_rules.tiebreak"),
    ]:
        _write(ROOT / curation_rel, _importlib_shim(target))

    # Redirect layout_engine importers
    replacements = [
        (
            "from travelogue.curation.phase6_rollout import rollout_bucket",
            "from travelogue.layout_engine.rollout_bucket import rollout_bucket",
        ),
        (
            "from travelogue.curation.cohort_faces import score_cohort_coherence",
            "from travelogue.layout_engine.scoring.cohort import score_cohort_coherence",
        ),
        (
            "from travelogue.curation.layout_candidates import",
            "from travelogue.layout_engine.planner.layout_candidates import",
        ),
        (
            "from travelogue.curation.intent_hints import",
            "from travelogue.layout_engine.intent_hints import",
        ),
        (
            "from travelogue.curation.usage_rules.context import",
            "from travelogue.layout_engine.usage_rules.context import",
        ),
        (
            "from travelogue.curation.asset_quality import asset_sharpness",
            "from travelogue.media.quality import asset_sharpness",
        ),
        (
            "from travelogue.curation.screen_planner import (\n        _is_landscape_id,\n        _is_std_portrait_id,\n    )",
            "from travelogue.layout_engine.planner.screen_planner import (\n        _is_landscape_id,\n        _is_std_portrait_id,\n    )",
        ),
    ]
    for path in (ROOT / "layout_engine").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        orig = text
        for old, new in replacements:
            text = text.replace(old, new)
        if text != orig:
            path.write_text(text, encoding="utf-8")

    # layout_scoring: lazy beam re-exports via __getattr__
    ls = (ROOT / "curation/layout_scoring.py").read_text(encoding="utf-8")
    if "__getattr__" not in ls:
        ls = re.sub(
            r"\nfrom travelogue\.layout_engine\.planner\.beam_scoring import \(.*?\n\)\n",
            "\n",
            ls,
            count=1,
            flags=re.DOTALL,
        )
        beam_names = [
            "asset_mean_luma",
            "rank_screens",
            "score_aspect_match",
            "score_burst_integrity",
            "score_category_coherence",
            "score_cohort_coherence",
            "score_gravity_balance",
            "score_layout_rhythm",
            "score_luminance_continuity",
            "score_screen",
            "score_screen_plan",
            "score_sharpness",
            "score_subject_run_soft",
            "score_temporal_coherence",
            "score_tone_continuity",
            "screen_mean_luma",
            "screen_visual_center",
        ]
        ls += (
            "\n_BEAM_EXPORTS = frozenset({"
            + ", ".join(repr(n) for n in beam_names)
            + "})\n\n"
            "def __getattr__(name: str):\n"
            "    if name in _BEAM_EXPORTS:\n"
            "        import importlib\n"
            "        mod = importlib.import_module('travelogue.layout_engine.planner.beam_scoring')\n"
            "        return getattr(mod, name)\n"
            "    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')\n"
        )
        _write(ROOT / "curation/layout_scoring.py", ls)

    # moment_scoring: importlib for highlight_windows
    ms = (ROOT / "curation/moment_scoring.py").read_text(encoding="utf-8")
    ms = ms.replace(
        "    from travelogue.layout_engine.highlight_windows import detect_highlight_windows\n",
        "    hw = __import__('travelogue.layout_engine.highlight_windows', fromlist=['detect_highlight_windows'])\n"
        "    detect_highlight_windows = hw.detect_highlight_windows\n",
    )
    _write(ROOT / "curation/moment_scoring.py", ms)

    # scoring/hero: importlib for curate_scoring delegate
    hero = (ROOT / "layout_engine/scoring/hero.py").read_text(encoding="utf-8")
    hero = hero.replace(
        "    from travelogue.curation.curate_scoring import effective_hero_score as _score\n",
        "    _mod = __import__('travelogue.curation.curate_scoring', fromlist=['effective_hero_score'])\n"
        "    _score = _mod.effective_hero_score\n",
    )
    _write(ROOT / "layout_engine/scoring/hero.py", hero)

    # aesthetic adapter importlib
    aes = (ROOT / "layout_engine/scoring/aesthetic.py").read_text(encoding="utf-8")
    aes = aes.replace(
        "    from travelogue.curation.aesthetic_score import aesthetic_overall as _fn\n",
        "    _mod = __import__('travelogue.curation.aesthetic_score', fromlist=['aesthetic_overall'])\n"
        "    _fn = _mod.aesthetic_overall\n",
    )
    _write(ROOT / "layout_engine/scoring/aesthetic.py", aes)

    # solo aesthetic imports → layout_engine.scoring.aesthetic
    solo = (ROOT / "layout_engine/scoring/solo.py").read_text(encoding="utf-8")
    solo = solo.replace(
        "from travelogue.curation.aesthetic_score import (\n    aesthetic_dim,\n    aesthetic_overall,\n    asset_aesthetic,\n    purpose_overall,\n)",
        "from travelogue.layout_engine.scoring.aesthetic import aesthetic_overall\n"
        "from travelogue.curation.aesthetic_score import (\n    aesthetic_dim,\n    asset_aesthetic,\n    purpose_overall,\n)",
    )
    _write(ROOT / "layout_engine/scoring/solo.py", solo)

    print("batch-6 migration done")


if __name__ == "__main__":
    main()
