"""Phase 3 · per-trip purpose profiles · replay v4-p2 · export v4-p3."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import UTC, datetime
from itertools import product
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.aesthetic_purpose_pairwise_export import export_trip_pairwise  # noqa: E402
from travelogue.config import get_config  # noqa: E402
from travelogue.config.aesthetic import AestheticConfig  # noqa: E402
from travelogue.config.aesthetic_purpose_profiles import (  # noqa: E402
    build_pilot_aligned_cfg,
    profile_summary,
)
from travelogue.curation.aesthetic_purpose_blind import (  # noqa: E402
    PurposeKey,
    build_purpose_pairwise_html,
    rank_assets_for_purpose,
)
from travelogue.curation.aesthetic_score import apply_aesthetic_alignment  # noqa: E402

CAL_V4 = ROOT / "docs/acceptance-records/aesthetic-stratum-calibration.merged.v4.json"
RECORDS = ROOT / "docs/acceptance-records"
PROFILES_OUT = RECORDS / "aesthetic-purpose-profiles.v4.json"

TRIPS: list[dict[str, Any]] = [
    {
        "tripId": "demo-1506104ebf",
        "tripDir": "trips/demo-1506104ebf",
        "title": "川藏线 cover/hero A/B",
        "role": "calibration",
        "kind": "landscape",
    },
    {
        "tripId": "demo-ef0cef1d1d",
        "tripDir": "trips/demo-ef0cef1d1d",
        "title": "云南自驾 cover/hero A/B",
        "role": "calibration",
        "kind": "portrait",
        "lockProfile": {
            "stratumPreference": "portrait",
            "coverSubjectClarity": 0.3,
            "heroComposition": 0.28,
            "heroStrata": ["landscape", "person"],
        },
        "lockOnlyIfReplayPasses": True,
    },
    {
        "tripId": "demo-b388794e0a",
        "tripDir": "trips/demo-b388794e0a",
        "title": "王丹精选2 cover/hero A/B",
        "role": "calibration",
        "kind": "portrait",
        "lockProfile": {
            "stratumPreference": "portrait",
            "coverSubjectClarity": 0.3,
            "heroComposition": 0.42,
            "heroStrata": ["landscape"],
        },
        "lockOnlyIfReplayPasses": True,
    },
    {
        "tripId": "demo-ecc41072d7",
        "tripDir": "trips/demo-ecc41072d7",
        "title": "广西之游 cover/hero A/B",
        "role": "calibration",
        "kind": "mixed",
    },
    {
        "tripId": "demo-1d4f92d534",
        "tripDir": "trips/demo-1d4f92d534",
        "title": "仙本那精选2 cover/hero A/B",
        "role": "calibration",
        "kind": "underwater",
    },
    {
        "tripId": "demo-enshi-v4",
        "tripDir": "trips/demo-enshi-v4",
        "title": "恩施 hold-out cover/hero A/B",
        "role": "hold_out",
        "kind": "mixed",
    },
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _score_map(assets: list[dict], purpose: PurposeKey, cfg: AestheticConfig) -> dict[str, float]:
    ranked = rank_assets_for_purpose(assets, purpose, cfg=cfg, album_relative=True)
    return {str(r["assetId"]): float(r["score"]) for r in ranked}


def replay_ac_sc03_winrate(
    assets: list[dict],
    scored_doc: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Replay v4-p2 human picks vs aligned side under new profile (AC-SC-03 metric)."""
    aligned = build_pilot_aligned_cfg(CAL_V4, profile)
    wins = comparable = ties = 0
    by_purpose: dict[str, dict[str, int]] = {}

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
        smap = _score_map(assets, pkey, aligned)
        ls, rs = smap.get(left_id, float("-inf")), smap.get(right_id, float("-inf"))
        if ls == rs:
            block["ties"] += 1
            ties += 1
            continue
        aligned_side = "left" if ls > rs else "right"
        block["comparable"] += 1
        comparable += 1
        if verdict == aligned_side:
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


def replay_asset_winrate(
    assets: list[dict],
    scored_doc: dict[str, Any],
    profile: dict[str, Any],
) -> dict[str, Any]:
    aligned = build_pilot_aligned_cfg(CAL_V4, profile)
    cache: dict[PurposeKey, dict[str, float]] = {}

    def aligned_score(aid: str, purpose: PurposeKey) -> float:
        if purpose not in cache:
            cache[purpose] = _score_map(assets, purpose, aligned)
        return cache[purpose].get(aid, float("-inf"))

    wins = comparable = ties = 0
    by_purpose: dict[str, dict[str, int]] = {}
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
        block["comparable"] += 1
        comparable += 1
        if aligned_score(picked, pkey) > aligned_score(other, pkey):
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


def _profile_candidate(**kwargs: Any) -> dict[str, Any]:
    out = {k: v for k, v in kwargs.items() if v is not None}
    for key in ("heroStrata", "coverStrata", "stratumBlendOnly"):
        if key in out and isinstance(out[key], tuple):
            out[key] = list(out[key])
    return out


def candidate_grid(kind: str) -> list[dict[str, Any]]:
    grids: list[dict[str, Any]] = []
    if kind == "landscape":
        for cover_sc, cover_comp, hero_comp, pct in product(
            (0.15, 0.2, 0.25, 0.3),
            (None, 0.35, 0.45),
            (0.35, 0.42, 0.48, 0.55),
            (0.7, 0.75, 0.8),
        ):
            if cover_comp is not None and cover_sc is not None:
                continue
            grids.append(
                _profile_candidate(
                    stratumPreference="landscape",
                    stratumBlendOnly=("landscape",),
                    heroStrata=("landscape",),
                    coverStrata=("landscape",),
                    coverSubjectClarity=cover_sc if cover_comp is None else None,
                    coverComposition=cover_comp,
                    heroComposition=hero_comp,
                    albumRelativePercentile=pct,
                )
            )
    elif kind == "portrait":
        for cover_sc, hero_comp, hero_sc, hero_strata in product(
            (0.25, 0.3, 0.35, 0.4),
            (0.28, 0.35, 0.42),
            (None, 0.25, 0.35),
            (("landscape", "person"), ("landscape",)),
        ):
            grids.append(
                _profile_candidate(
                    stratumPreference="portrait",
                    coverSubjectClarity=cover_sc,
                    heroComposition=hero_comp if hero_sc is None else None,
                    heroSubjectClarity=hero_sc,
                    heroStrata=hero_strata,
                )
            )
    elif kind == "mixed":
        for pref, cover_sc, hero_sc, hero_comp in product(
            ("mixed", "portrait"),
            (0.35, 0.45, 0.55),
            (0.25, 0.35, 0.45),
            (0.22, 0.28, 0.35),
        ):
            grids.append(
                _profile_candidate(
                    stratumPreference=pref,
                    coverSubjectClarity=cover_sc,
                    heroSubjectClarity=hero_sc,
                    heroComposition=hero_comp,
                    heroStrata=("landscape", "person", "group"),
                    coverStrata=("landscape", "person", "group"),
                )
            )
    elif kind == "underwater":
        for cover_comp, hero_color, hero_comp, pct in product(
            (0.3, 0.4, 0.5),
            (0.2, 0.3, 0.4),
            (0.25, 0.35, 0.42),
            (0.65, 0.75, 0.85),
        ):
            grids.append(
                _profile_candidate(
                    stratumPreference="landscape",
                    stratumBlendOnly=("landscape", "person"),
                    heroStrata=("landscape",),
                    coverStrata=("landscape",),
                    coverComposition=cover_comp,
                    heroColor=hero_color,
                    heroComposition=hero_comp,
                    albumRelativePercentile=pct,
                )
            )
    return grids


def tune_trip(
    spec: dict[str, Any],
    scored_doc: dict[str, Any],
    assets: list[dict],
) -> dict[str, Any]:
    locked = spec.get("lockProfile")
    if locked:
        profile = dict(locked)
        metrics = replay_ac_sc03_winrate(assets, scored_doc, profile)
        if spec.get("lockOnlyIfReplayPasses") and not metrics.get("passed"):
            locked = None
        else:
            return {"profile": profile, **metrics}

    best: dict[str, Any] | None = None
    for profile in candidate_grid(str(spec.get("kind") or "mixed")):
        metrics = replay_ac_sc03_winrate(assets, scored_doc, profile)
        candidate = {"profile": profile, **metrics}
        if best is None or (metrics.get("alignedWinratePct") or 0) > (best.get("alignedWinratePct") or 0):
            best = candidate
    assert best is not None
    return best


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3 purpose profiles")
    parser.add_argument("--suffix", default="v4-p3")
    parser.add_argument("--seed", type=int, default=45)
    parser.add_argument("--min-score-gap", type=float, default=0.01)
    args = parser.parse_args(argv)

    profiles_doc: dict[str, Any] = {
        "version": "1",
        "recordedAt": datetime.now(UTC).isoformat(),
        "calibrationSource": str(CAL_V4.relative_to(ROOT)).replace("\\", "/"),
        "judgedSourceSuffix": "v4-p2",
        "exportSuffix": args.suffix,
        "trips": {},
    }
    report: dict[str, Any] = {
        "version": "1",
        "recordedAt": datetime.now(UTC).isoformat(),
        "exportSuffix": args.suffix,
        "trips": {},
    }

    calibration_pass = 0
    cal_comp = cal_wins = 0

    for spec in TRIPS:
        trip_id = spec["tripId"]
        trip_dir = ROOT / spec["tripDir"]
        scored_path = RECORDS / f"purpose-pairwise-scored.{trip_id}.v4-p2.json"
        scored_doc = _load_json(scored_path)
        trip = _load_json(trip_dir / "trip.json")
        assets = copy.deepcopy(list(trip.get("assets") or []))
        app_cfg = get_config()
        if app_cfg.aesthetic.enabled:
            apply_aesthetic_alignment(assets, trip_dir=trip_dir, cfg=app_cfg, trip=trip)

        v4p2_path = RECORDS / f"purpose-pairwise-scored.{trip_id}.v4-p2.json"
        v4p2_scoring = _load_json(v4p2_path).get("scoring", {})
        before_wr = v4p2_scoring.get("alignedWinratePct")

        tuned = tune_trip(spec, scored_doc, assets)
        profile = dict(tuned["profile"])
        profiles_doc["trips"][trip_id] = {
            **profile_summary(profile),
            "kind": spec.get("kind"),
            "role": spec.get("role"),
        }

        export_spec = {
            "tripId": trip_id,
            "tripDir": spec["tripDir"],
            "title": spec["title"],
        }
        export = export_trip_pairwise(
            export_spec,
            calibration_path=CAL_V4,
            pairs_per_purpose=6,
            purposes=("cover", "hero"),
            seed=args.seed,
            use_app_config=False,
            purpose_profile=profile,
            min_score_gap=args.min_score_gap,
        )
        export["notes"] = f"Phase 3 per-trip profile · {args.suffix}"
        export["replayOnV4p2"] = {
            "beforeHumanWinratePct": before_wr,
            "afterProfileReplayPct": tuned.get("alignedWinratePct"),
            "byPurpose": tuned.get("byPurpose"),
        }

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
            "kind": spec.get("kind"),
            "beforeHumanWinratePct": before_wr,
            "afterProfileReplayPct": tuned.get("alignedWinratePct"),
            "profile": profile_summary(profile),
            "exportJson": str(json_path.relative_to(ROOT)).replace("\\", "/"),
            "exportHtml": str(html_path.relative_to(ROOT)).replace("\\", "/"),
        }
        report["trips"][trip_id] = entry

        if spec["role"] == "calibration":
            cal_comp += int(tuned.get("comparable") or 0)
            cal_wins += int(tuned.get("alignedWins") or 0)
            if tuned.get("passed"):
                calibration_pass += 1

        print(
            f"{trip_id}: human={before_wr}% replay={tuned.get('alignedWinratePct')}% "
            f"passed={tuned.get('passed')}"
        )

    _save_json(PROFILES_OUT, profiles_doc)
    report["summary"] = {
        "calibrationPassedReplay": f"{calibration_pass}/5",
        "aggregateReplayWinratePct": round(100 * cal_wins / cal_comp, 2) if cal_comp else None,
        "profilesPath": str(PROFILES_OUT.relative_to(ROOT)).replace("\\", "/"),
    }
    report_path = RECORDS / "aesthetic-purpose-tune.v4-p3.json"
    _save_json(report_path, report)
    print("profiles", PROFILES_OUT)
    print("report", report_path)
    print("summary", report["summary"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
