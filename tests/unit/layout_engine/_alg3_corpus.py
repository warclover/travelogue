"""ALG-V3 · AC-20/21 corpus helpers (fixed MCS windows · candidate hot path).

Full-trip ``plan_mosaic_screens`` on atom-fallback buckets rarely calls
``build_screen``; AC-20 needs the candidate loop where B2a skips builds.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tests._golden.helpers import _asset
from travelogue.config import MosaicConfig
from travelogue.config.mosaic import TemplateContractConfig
from travelogue.layout_engine.mosaic.builders import (
    get_build_screen_calls,
    reset_build_screen_calls,
)
from travelogue.layout_engine.mosaic.candidates import (
    generate_window_candidates_with_rejections,
)

CORPUS_ID = "alg3-default-mcs-v1"
AC20_PROBE_ID = "alg3-ac20-mismatch-probe-v1"
_BASELINE_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "acceptance-records"
)
BUILD_SCREEN_BASELINE = _BASELINE_DIR / "alg3-build-screen-calls-baseline.json"
AC21_LAYOUT_BASELINE = _BASELINE_DIR / "alg3-ac21-layout-baseline.json"

# Fixed windows: 2P2L (B2a early-reject) + pure 4-slot (stable winners).
_CORPUS_WINDOWS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("mix-2p2l-a", ("portrait", "portrait", "landscape", "landscape")),
    ("mix-2p2l-b", ("portrait", "landscape", "portrait", "landscape")),
    ("mix-2p2l-c", ("landscape", "portrait", "landscape", "portrait")),
    ("mix-2p2l-d", ("landscape", "landscape", "portrait", "portrait")),
    ("land-4-a", ("landscape",) * 4),
    ("land-4-b", ("landscape",) * 4),
    ("port-4-a", ("portrait",) * 4),
    ("port-4-b", ("portrait",) * 4),
    ("mix-3p1l", ("portrait", "portrait", "portrait", "landscape")),
    ("mix-1p3l", ("portrait", "landscape", "landscape", "landscape")),
)


def _mosaic_cfg() -> MosaicConfig:
    return MosaicConfig(
        enabled=True,
        enabled_window_sizes=(4, 5, 6, 9),
        unified_mode=True,
        scorer_version="p15-s2",
        min_candidate_score=0.0,
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
    )


def _window_assets(
    window_key: str, kinds: tuple[str, ...]
) -> tuple[list[str], dict[str, str], dict[str, dict]]:
    ids: list[str] = []
    aspects: dict[str, str] = {}
    assets_map: dict[str, dict] = {}
    for i, kind in enumerate(kinds):
        aid = f"{window_key}-{i}"
        asset = _asset(
            aid,
            900 if kind == "portrait" else 2000,
            1600 if kind == "portrait" else 1200,
            offset_hours=float(i) * 0.1 + (len(window_key) * 0.01),
            sharpness=0.8,
        )
        assets_map[aid] = asset
        aspects[aid] = asset["aspectKind"]
        ids.append(aid)
    return ids, aspects, assets_map


def _project_winner(candidates: list[Any]) -> dict[str, Any] | None:
    """Best hard_valid candidate → AC-21 projection fields."""
    hard = [c for c in candidates if getattr(c, "hard_valid", False)]
    pool = hard or list(candidates)
    if not pool:
        return None
    best = pool[0]
    screen = getattr(best, "screen", None) or {}
    slots = screen.get("slots") if isinstance(screen, dict) else None
    slot_asset_ids = list(getattr(best, "ordered_asset_ids", None) or [])
    roles: list[Any] = []
    if isinstance(slots, list) and slots:
        slot_asset_ids = [
            sl.get("assetId")
            for sl in slots
            if isinstance(sl, dict) and sl.get("assetId")
        ]
        roles = [
            sl.get("role")
            for sl in slots
            if isinstance(sl, dict) and sl.get("assetId")
        ]
    out: dict[str, Any] = {
        "patternId": getattr(best, "pattern_id", None) or screen.get("patternId"),
        "slotAssetIds": slot_asset_ids,
    }
    if any(r for r in roles):
        out["slotRoles"] = roles
    return out


def run_alg3_corpus(*, precheck_enabled: bool = True) -> dict[str, Any]:
    """Run fixed windows through candidate generation; sum ``buildScreenCalls``.

    When ``precheck_enabled`` is False, ``candidates.pattern_geometry_precheck``
    always returns ``None`` (W0-equivalent).
    """
    import travelogue.layout_engine.mosaic.candidates as cand_mod

    cfg = _mosaic_cfg()
    orig = cand_mod.pattern_geometry_precheck

    def _precheck_off(*_a, **_k):
        return None

    if not precheck_enabled:
        cand_mod.pattern_geometry_precheck = _precheck_off  # type: ignore[assignment]

    windows_out: list[dict[str, Any]] = []
    screens_out: list[dict[str, Any]] = []
    total_calls = 0
    try:
        for window_key, kinds in _CORPUS_WINDOWS:
            ids, aspects, assets_map = _window_assets(window_key, kinds)
            reset_build_screen_calls()
            result = generate_window_candidates_with_rejections(
                ids,
                aspects,  # type: ignore[arg-type]
                assets_map,
                cfg=cfg,
                trip_photo_total=40,
            )
            calls = int(get_build_screen_calls())
            total_calls += calls
            winner = _project_winner(list(result.candidates or []))
            windows_out.append(
                {
                    "windowKey": window_key,
                    "buildScreenCalls": calls,
                    "candidateCount": len(result.candidates or []),
                    "winner": winner,
                }
            )
            screen_proj: dict[str, Any] = {
                "windowKey": window_key,
                "patternId": (winner or {}).get("patternId"),
                "slotAssetIds": list((winner or {}).get("slotAssetIds") or []),
            }
            if winner and "slotRoles" in winner:
                screen_proj["slotRoles"] = winner["slotRoles"]
            screens_out.append(screen_proj)
    finally:
        cand_mod.pattern_geometry_precheck = orig  # type: ignore[assignment]

    return {
        "corpusId": CORPUS_ID,
        "buildScreenCalls": total_calls,
        "windows": windows_out,
        "chapters": [
            {
                "id": "alg3-corpus",
                "patternId": "open",
                "screens": screens_out,
            }
        ],
    }


def run_ac20_mismatch_probe(*, precheck_enabled: bool = True) -> dict[str, Any]:
    """AC-20 stress: mono-portrait window forced onto a landscape-mix auto-flow SKU.

    Production signature routing often collapses try-sets to aspect-matched SKUs,
    so the main corpus never reaches a definite ``pattern_geometry_precheck=False``.
    This probe keeps ordering successful while orientation is statically wrong —
    B2a must skip ``build_screen``; W0-equivalent (precheck forced None) must call it.
    """
    import travelogue.layout_engine.mosaic.candidates as cand_mod
    from travelogue.layout_engine.mosaic.constants import PATTERN_PORTRAIT_2_LANDSCAPE_2
    from travelogue.layout_engine.mosaic.pattern_catalog import AspectProfile, MosaicPattern

    ids, aspects, assets_map = _window_assets(
        "ac20-mismatch", ("portrait", "portrait", "portrait", "portrait")
    )
    reg = {
        PATTERN_PORTRAIT_2_LANDSCAPE_2: MosaicPattern(
            pattern_id=PATTERN_PORTRAIT_2_LANDSCAPE_2,
            slot_count=4,
            grid_class="mixed",
            roles=("a", "b", "c", "d"),
            accepts=AspectProfile(),
        )
    }
    cfg = MosaicConfig(
        enabled=True,
        enabled_window_sizes=(4,),
        unified_mode=True,
        min_candidate_score=0.0,
        template_contract=TemplateContractConfig(enabled=False, shadow_log=False),
    )

    orig_pre = cand_mod.pattern_geometry_precheck
    orig_order = cand_mod.try_order_for_pattern

    def _order(*_a, **_k):
        return list(ids)

    def _precheck_off(*_a, **_k):
        return None

    cand_mod.try_order_for_pattern = _order  # type: ignore[assignment]
    if not precheck_enabled:
        cand_mod.pattern_geometry_precheck = _precheck_off  # type: ignore[assignment]
    reset_build_screen_calls()
    try:
        result = generate_window_candidates_with_rejections(
            ids,
            aspects,  # type: ignore[arg-type]
            assets_map,
            cfg=cfg,
            registry=reg,
            trip_photo_total=40,
            burst_seconds=3600.0,
        )
        calls = int(get_build_screen_calls())
    finally:
        cand_mod.pattern_geometry_precheck = orig_pre  # type: ignore[assignment]
        cand_mod.try_order_for_pattern = orig_order  # type: ignore[assignment]

    static_rejects = [
        r
        for r in (result.rejected or [])
        if r.get("reason") == "geometry_invalid"
        and r.get("detail") == "static_precheck"
    ]
    return {
        "probeId": AC20_PROBE_ID,
        "buildScreenCalls": calls,
        "staticPrecheckRejects": len(static_rejects),
        "candidateCount": len(result.candidates or []),
    }


def ac20_total_build_screen_calls(*, precheck_enabled: bool) -> dict[str, Any]:
    """Main MCS corpus + mismatch probe (AC-20 absolute count)."""
    main = run_alg3_corpus(precheck_enabled=precheck_enabled)
    probe = run_ac20_mismatch_probe(precheck_enabled=precheck_enabled)
    return {
        "corpusId": CORPUS_ID,
        "probeId": AC20_PROBE_ID,
        "mainBuildScreenCalls": int(main["buildScreenCalls"]),
        "probeBuildScreenCalls": int(probe["buildScreenCalls"]),
        "buildScreenCalls": int(main["buildScreenCalls"]) + int(probe["buildScreenCalls"]),
        "probe": probe,
        "chapters": main["chapters"],
    }


def freeze_alg3_baselines(*, frozen_at: str) -> dict[str, Any]:
    """Write W0-equivalent buildScreenCalls baseline + B2a-on AC-21 layout baseline."""
    w0 = ac20_total_build_screen_calls(precheck_enabled=False)
    w1_main = run_alg3_corpus(precheck_enabled=True)
    w1_probe = run_ac20_mismatch_probe(precheck_enabled=True)
    w1_total = int(w1_main["buildScreenCalls"]) + int(w1_probe["buildScreenCalls"])

    build_payload = {
        "schemaVersion": 1,
        "status": "frozen",
        "note": (
            "W0-equivalent: candidates.pattern_geometry_precheck forced None. "
            "AC-20: B2a-on totalBuildScreenCalls must be strictly < this baseline. "
            "Corpus = _CORPUS_WINDOWS + AC20_PROBE_ID mismatch probe "
            "(signature routing alone never hits definite precheck False)."
        ),
        "frozenAt": frozen_at,
        "corpusId": CORPUS_ID,
        "probeId": AC20_PROBE_ID,
        "configNote": (
            "MosaicConfig enabled; window sizes (4,5,6,9); unified; "
            "min_candidate_score=0; template_contract off; scoring/LSE off"
        ),
        "precheckEnabled": False,
        "windows": [
            {"windowKey": w["windowKey"], "buildScreenCalls": w["buildScreenCalls"]}
            for w in run_alg3_corpus(precheck_enabled=False)["windows"]
        ],
        "probeBuildScreenCalls": int(w0["probeBuildScreenCalls"]),
        "totalBuildScreenCalls": int(w0["buildScreenCalls"]),
        "b2aOnBuildScreenCalls": w1_total,
        "b2aOnProbeBuildScreenCalls": int(w1_probe["buildScreenCalls"]),
    }
    BUILD_SCREEN_BASELINE.write_text(
        json.dumps(build_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    layout_payload = {
        "schemaVersion": 1,
        "status": "frozen",
        "note": (
            "AC-21 projection with B2a on. "
            "Fields: patternId + slotAssetIds (+ slotRoles when present). "
            "Empty patternId means no hard_valid winner for that window."
        ),
        "frozenAt": frozen_at,
        "corpusId": CORPUS_ID,
        "projection": "patternId+slotAssetIds(+slotRoles)",
        "stripWhitelistRef": "ACCEPTANCE §2.2",
        "buildScreenCalls": int(w1_main["buildScreenCalls"]),
        "chapters": w1_main["chapters"],
    }
    AC21_LAYOUT_BASELINE.write_text(
        json.dumps(layout_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {"buildScreen": build_payload, "layout": layout_payload}


if __name__ == "__main__":
    result = freeze_alg3_baselines(frozen_at="2026-08-01")
    print("W0 totalBuildScreenCalls:", result["buildScreen"]["totalBuildScreenCalls"])
    print("B2a-on buildScreenCalls:", result["buildScreen"]["b2aOnBuildScreenCalls"])
    print(
        "AC-21 screens:",
        len(result["layout"]["chapters"][0]["screens"]),
    )
