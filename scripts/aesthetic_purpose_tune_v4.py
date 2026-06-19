"""v4 purpose tune · replay frozen pairwise judgments · re-export v4-p2."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from dataclasses import replace
from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import get_config  # noqa: E402
from travelogue.config.aesthetic import AestheticConfig  # noqa: E402
from travelogue.config.aesthetic_stratified import (  # noqa: E402
    apply_stratum_preference_overlay,
    config_summary,
    landscape_pilot_config,
)
from travelogue.curation.aesthetic_purpose_blind import (  # noqa: E402
    PurposeKey,
    build_purpose_pairwise_html,
    export_purpose_pick_pairs,
    rank_assets_for_purpose,
    score_purpose_pairwise_export,
)
from travelogue.curation.aesthetic_purpose_calibrate import weights_with_dim_emphasis  # noqa: E402
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment  # noqa: E402

CAL_V4 = ROOT / "docs/acceptance-records/aesthetic-stratum-calibration.merged.v4.json"
RECORDS = ROOT / "docs/acceptance-records"

TRIPS: list[dict[str, str]] = [
    {
        "tripId": "demo-1506104ebf",
        "tripDir": "trips/demo-1506104ebf",
        "title": "川藏线 cover/hero A/B",
        "preference": "landscape",
        "role": "calibration",
    },
    {
        "tripId": "demo-ef0cef1d1d",
        "tripDir": "trips/demo-ef0cef1d1d",
        "title": "云南自驾 cover/hero A/B",
        "preference": "portrait",
        "role": "calibration",
    },
    {
        "tripId": "demo-b388794e0a",
        "tripDir": "trips/demo-b388794e0a",
        "title": "王丹精选2 cover/hero A/B",
        "preference": "portrait",
        "role": "calibration",
    },
    {
        "tripId": "demo-ecc41072d7",
        "tripDir": "trips/demo-ecc41072d7",
        "title": "广西之游 cover/hero A/B",
        "preference": "portrait",
        "role": "calibration",
    },
    {
        "tripId": "demo-1d4f92d534",
        "tripDir": "trips/demo-1d4f92d534",
        "title": "仙本那精选2 cover/hero A/B",
        "preference": "portrait",
        "role": "calibration",
    },
    {
        "tripId": "demo-enshi-v4",
        "tripDir": "trips/demo-enshi-v4",
        "title": "恩施 hold-out cover/hero A/B",
        "preference": "portrait",
        "role": "hold_out",
    },
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def rules_cfg() -> AestheticConfig:
    app = get_config()
    return replace(app.aesthetic, ml_calibrate=False, use_album_relative=False, source="rules")


def build_aligned_cfg(
    *,
    cover_subject_clarity: float,
    hero_composition: float,
    preference: str,
    hero_strata: tuple[str, ...],
    cover_strata: tuple[str, ...] | None = None,
) -> AestheticConfig:
    app = get_config()
    base = landscape_pilot_config(
        CAL_V4,
        use_album_relative=True,
        stratum_blend_only=("landscape", "person", "group"),
    )
    base = apply_stratum_preference_overlay(base, preference)
    by_purpose = dict(base.stratum_blend_only_by_purpose or {})
    by_purpose["hero"] = hero_strata
    if cover_strata is not None:
        by_purpose["cover"] = cover_strata
    cover_w = weights_with_dim_emphasis(
        base.presets.cover, dim="subjectClarity", emphasis=cover_subject_clarity
    )
    hero_w = weights_with_dim_emphasis(
        base.presets.hero, dim="composition", emphasis=hero_composition
    )
    presets = replace(base.presets, cover=cover_w, hero=hero_w)
    return replace(
        base,
        presets=presets,
        stratum_blend_only_by_purpose=by_purpose,
        mllm=app.aesthetic.mllm,
        portrait_lite_enabled=app.aesthetic.portrait_lite_enabled,
    )


def _score_map(
    assets: list[dict],
    purpose: PurposeKey,
    cfg: AestheticConfig,
    *,
    album_relative: bool,
) -> dict[str, float]:
    ranked = rank_assets_for_purpose(
        assets,
        purpose,
        cfg=cfg,
        album_relative=album_relative,
    )
    return {str(r["assetId"]): float(r["score"]) for r in ranked}


def replay_user_agreement(
    assets: list[dict],
    scored_doc: dict[str, Any],
    aligned: AestheticConfig,
) -> dict[str, Any]:
    """User picked asset vs aligned purpose score on frozen pairs."""
    wins = 0
    comparable = 0
    ties = 0
    by_purpose: dict[str, dict[str, int]] = {}
    score_cache: dict[PurposeKey, dict[str, float]] = {}

    def aligned_score(aid: str, purpose: PurposeKey) -> float:
        if purpose not in score_cache:
            score_cache[purpose] = _score_map(assets, purpose, aligned, album_relative=True)
        return score_cache[purpose].get(aid, float("-inf"))

    for pair in scored_doc.get("pairs") or []:
        purpose = str(pair.get("purpose") or "cover")
        pkey: PurposeKey = purpose  # type: ignore[assignment]
        verdict = pair.get("judgeVerdict")
        block = by_purpose.setdefault(purpose, {"comparable": 0, "alignedWins": 0, "ties": 0})
        if not verdict:
            continue
        if verdict == "tie":
            block["ties"] += 1
            ties += 1
            continue
        left_id = str(pair["optionLeft"]["assetId"])
        right_id = str(pair["optionRight"]["assetId"])
        picked = left_id if verdict == "left" else right_id
        other = right_id if picked == left_id else left_id
        s_pick = aligned_score(picked, pkey)
        s_other = aligned_score(other, pkey)
        block["comparable"] += 1
        comparable += 1
        if s_pick > s_other:
            block["alignedWins"] += 1
            wins += 1

    wr = round(100.0 * wins / comparable, 2) if comparable else None
    return {
        "comparable": comparable,
        "alignedWins": wins,
        "ties": ties,
        "alignedWinratePct": wr,
        "passed": wr is not None and wr >= 60.0,
        "byPurpose": by_purpose,
    }


def tune_trip(
    spec: dict[str, str],
    scored_doc: dict[str, Any],
    assets: list[dict],
) -> dict[str, Any]:
    pref_default = spec.get("preference") or "portrait"
    cover_grid = (0.30, 0.40, 0.45, 0.50, 0.55)
    hero_comp_grid = (0.28, 0.35, 0.42, 0.48)
    hero_strata_grid = (("landscape",), ("landscape", "person"))
    cover_strata_grid: tuple[tuple[str, ...] | None, ...] = (None, ("landscape", "person"))
    pref_grid = (pref_default, "auto", "landscape") if pref_default != "landscape" else ("landscape",)

    best: dict[str, Any] | None = None
    for pref, cover_sc, hero_comp, hero_strata, cover_strata in product(
        pref_grid, cover_grid, hero_comp_grid, hero_strata_grid, cover_strata_grid
    ):
        aligned = build_aligned_cfg(
            cover_subject_clarity=cover_sc,
            hero_composition=hero_comp,
            preference=pref,
            hero_strata=hero_strata,
            cover_strata=cover_strata,
        )
        metrics = replay_user_agreement(assets, scored_doc, aligned)
        candidate = {
            "preference": pref,
            "coverSubjectClarity": cover_sc,
            "heroComposition": hero_comp,
            "heroStrata": list(hero_strata),
            "coverStrata": list(cover_strata) if cover_strata else None,
            **metrics,
        }
        if best is None:
            best = candidate
            continue
        b_wr = best.get("alignedWinratePct") or 0
        c_wr = metrics.get("alignedWinratePct") or 0
        if c_wr > b_wr:
            best = candidate

    assert best is not None
    return best


def export_tuned(
    spec: dict[str, str],
    assets: list[dict],
    tuned: dict[str, Any],
    *,
    suffix: str,
    seed: int,
    min_score_gap: float,
) -> dict[str, Any]:
    aligned = build_aligned_cfg(
        cover_subject_clarity=float(tuned["coverSubjectClarity"]),
        hero_composition=float(tuned["heroComposition"]),
        preference=str(tuned["preference"]),
        hero_strata=tuple(tuned["heroStrata"]),
        cover_strata=tuple(tuned["coverStrata"]) if tuned.get("coverStrata") else None,
    )
    rules = rules_cfg()
    cover_sc = float(tuned["coverSubjectClarity"])
    cover = replace(rules.presets.cover, subject_clarity=cover_sc)
    rules = replace(rules, presets=replace(rules.presets, cover=cover))

    export = export_purpose_pick_pairs(
        assets,
        rules_cfg=rules,
        aligned_cfg=aligned,
        trip_id=spec["tripId"],
        purposes=("cover", "hero"),
        pairs_per_purpose=6,
        seed=seed,
        album_relative=True,
        min_score_gap=min_score_gap,
    )
    export["exportedAt"] = datetime.now(UTC).isoformat()
    export["pilotConfig"] = config_summary(aligned)
    export["tune"] = {k: v for k, v in tuned.items() if k not in ("byPurpose",)}
    export["notes"] = f"v4 purpose tune · export suffix {suffix}"
    return export


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="v4 purpose tune + re-export")
    parser.add_argument("--suffix", type=str, default="v4-p2")
    parser.add_argument("--seed", type=int, default=44)
    parser.add_argument("--min-score-gap", type=float, default=0.012)
    parser.add_argument(
        "--write-report",
        type=Path,
        default=RECORDS / "aesthetic-purpose-tune.v4.json",
    )
    args = parser.parse_args(argv)

    report: dict[str, Any] = {
        "version": "1",
        "recordedAt": datetime.now(UTC).isoformat(),
        "calibrationSource": str(CAL_V4.relative_to(ROOT)).replace("\\", "/"),
        "judgedSourceSuffix": "v4",
        "exportSuffix": args.suffix,
        "seed": args.seed,
        "minScoreGap": args.min_score_gap,
        "trips": {},
    }

    calibration: dict[str, Any] = {}
    for spec in TRIPS:
        trip_id = spec["tripId"]
        trip_dir = ROOT / spec["tripDir"]
        scored_path = RECORDS / f"purpose-pairwise-scored.{trip_id}.v4.json"
        scored_doc = _load_json(scored_path)
        trip = _load_json(trip_dir / "trip.json")
        assets = copy.deepcopy(list(trip.get("assets") or []))
        app_cfg = get_config()
        if app_cfg.aesthetic.enabled:
            apply_aesthetic_alignment(assets, trip_dir=trip_dir, cfg=app_cfg, trip=trip)

        before_role = score_purpose_pairwise_export(scored_doc)
        before_asset = replay_user_agreement(assets, scored_doc, build_aligned_cfg(
            cover_subject_clarity=0.45,
            hero_composition=0.35,
            preference=spec.get("preference") or "portrait",
            hero_strata=("landscape",),
        ))
        tuned = tune_trip(spec, scored_doc, assets)
        after_asset = replay_user_agreement(
            assets,
            scored_doc,
            build_aligned_cfg(
                cover_subject_clarity=float(tuned["coverSubjectClarity"]),
                hero_composition=float(tuned["heroComposition"]),
                preference=str(tuned["preference"]),
                hero_strata=tuple(tuned["heroStrata"]),
                cover_strata=tuple(tuned["coverStrata"]) if tuned.get("coverStrata") else None,
            ),
        )

        export = export_tuned(
            spec,
            assets,
            tuned,
            suffix=args.suffix,
            seed=args.seed,
            min_score_gap=args.min_score_gap,
        )
        stem = f"purpose-pairwise.{trip_id}.{args.suffix}"
        json_path = RECORDS / f"{stem}.json"
        html_path = RECORDS / f"{stem}.html"
        _save_json(json_path, export)
        html_path.write_text(
            build_purpose_pairwise_html(export, image_base_url="", title=spec["title"]),
            encoding="utf-8",
        )

        entry = {
            "tripId": trip_id,
            "role": spec["role"],
            "beforeRoleWinratePct": before_role.get("alignedWinratePct"),
            "beforeAssetReplayPct": before_asset.get("alignedWinratePct"),
            "afterAssetReplayPct": after_asset.get("alignedWinratePct"),
            "tune": {k: v for k, v in tuned.items() if k != "byPurpose"},
            "afterByPurpose": after_asset.get("byPurpose"),
            "exportJson": str(json_path.relative_to(ROOT)).replace("\\", "/"),
            "exportHtml": str(html_path.relative_to(ROOT)).replace("\\", "/"),
            "pairCount": export.get("pairCount"),
        }
        report["trips"][trip_id] = entry
        if spec["role"] == "calibration":
            calibration[trip_id] = entry

        print(
            f"{trip_id}: role={before_role.get('alignedWinratePct')}% "
            f"replay {before_asset.get('alignedWinratePct')}% -> {after_asset.get('alignedWinratePct')}% "
            f"pairs={export.get('pairCount')}"
        )

    passed = sum(1 for e in calibration.values() if (e.get("afterAssetReplayPct") or 0) >= 60.0)
    report["summary"] = {
        "calibrationPassedReplay": f"{passed}/{len(calibration)}",
        "note": "Asset-based replay on frozen v4 pairs; re-export for optional human recheck",
    }
    out = args.write_report if args.write_report.is_absolute() else ROOT / args.write_report
    _save_json(out, report)
    print("report", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
