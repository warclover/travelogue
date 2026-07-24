#!/usr/bin/env python3
"""FRP · Food Role Policy acceptance helper (AC-FRP auto + fixture dogfood delta)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.config import config_override, get_config
from travelogue.config.moment import MomentConfig
from travelogue.cover_engine.closing.pick import pick_closing_with_meta
from travelogue.curation.curate_scoring import pick_cover_asset_id_with_meta
from travelogue.curation.food_policy import is_food_asset
from travelogue.curation.moment_scoring import build_moment_pool
from travelogue.layout_engine.planner.screen_planner import (
    FOOD_GRID_LAYOUT_HINT,
    plan_screens_for_chapter,
)

FIXTURE_PATH = ROOT / "schemas" / "fixtures" / "trip.frp_mixed_travel_food.json"


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _with_role(**kwargs) -> object:
    cfg = get_config()
    role = replace(cfg.curate.food_role, **kwargs)
    return replace(cfg, curate=replace(cfg.curate, food_role=role))


def _legacy_role() -> object:
    return _with_role(
        cover_policy="off",
        closing_policy="off",
        hero_policy="allow",
        allow_food_in_moment=True,
        moment_multiplier=1.0,
        grid_min_items=3,
        grid_max_interruptions=1,
        cluster_window_seconds=0.0,
    )


def _asset(
    aid: str,
    *,
    food: bool,
    taken_offset_min: int,
    sharp: float,
    w: int = 1600,
    h: int = 900,
) -> dict:
    base = datetime(2025, 6, 1, 12, 0, 0, tzinfo=UTC)
    asset: dict = {
        "id": aid,
        "type": "image",
        "layoutEligible": True,
        "width": w,
        "height": h,
        "mediaClass": "photo",
        "userTier": "material",
        "quality": {"sharpness": sharp, "overall": 0.8},
        "takenAt": (base + timedelta(minutes=taken_offset_min))
        .isoformat()
        .replace("+00:00", "Z"),
    }
    if food:
        asset["tags"] = ["food"]
        asset["subjectClass"] = "food"
        asset["subjectConfidence"] = 0.92
    else:
        asset["tags"] = ["landscape"]
        asset["subjectClass"] = "landscape"
        asset["subjectConfidence"] = 0.9
    return asset


def _build_mixed_trip() -> dict:
    """Travel + food mix: scenery + high-score food + same-meal cluster."""
    assets = [
        _asset("l0", food=False, taken_offset_min=0, sharp=220.0),
        _asset("l1", food=False, taken_offset_min=5, sharp=240.0),
        _asset("f_hero", food=True, taken_offset_min=40, sharp=980.0, w=2000, h=1125),
        _asset("f1", food=True, taken_offset_min=70, sharp=300.0, w=1200, h=1200),
        _asset("l2", food=False, taken_offset_min=75, sharp=210.0),
        _asset("f2", food=True, taken_offset_min=80, sharp=310.0, w=1200, h=1200),
        _asset("f3", food=True, taken_offset_min=85, sharp=320.0, w=1200, h=1200),
        _asset("l3", food=False, taken_offset_min=120, sharp=260.0),
        _asset("f_solo", food=True, taken_offset_min=200, sharp=280.0, w=1200, h=1200),
    ]
    # Pad moment pool eligibility
    for i in range(12):
        assets.append(
            _asset(f"l_pad{i}", food=False, taken_offset_min=210 + i * 3, sharp=180.0 + i)
        )
    return {
        "tripId": "frp-mixed-travel-food-fixture",
        "version": "0.2",
        "exportLayout": "web",
        "meta": {
            "title": "FRP Mixed Travel+Food",
            "subtitle": "dogfood fixture",
            "dateStart": "2025-06-01",
            "dateEnd": "2025-06-01",
        },
        "assets": assets,
        "curation": {},
        "chapters": [
            {
                "chapterId": "ch-01",
                "screens": [
                    {"slots": [{"assetId": a["id"]} for a in assets[:3]]},
                    {"slots": [{"assetId": a["id"]} for a in assets[3:6]]},
                    {"slots": [{"assetId": a["id"]} for a in assets[6:9]]},
                ],
            }
        ],
    }


def _aspects_for(assets: list[dict]) -> dict[str, str]:
    out: dict[str, str] = {}
    for a in assets:
        aid = str(a["id"])
        w = int(a.get("width") or 1)
        h = int(a.get("height") or 1)
        if abs(w - h) < 40:
            out[aid] = "square"
        elif w > h:
            out[aid] = "landscape"
        else:
            out[aid] = "portrait"
    return out


def _solo_food_screen_count(screens: list[dict], assets_map: dict[str, dict]) -> int:
    count = 0
    for sc in screens:
        slots = sc.get("slots") or []
        if len(slots) != 1:
            continue
        aid = str((slots[0] or {}).get("assetId") or "")
        if aid and is_food_asset(assets_map.get(aid) or {}):
            if sc.get("layoutHint") != FOOD_GRID_LAYOUT_HINT:
                count += 1
    return count


def _run_variant(label: str, cfg) -> dict:
    trip = _build_mixed_trip()
    assets = list(trip["assets"])
    assets_map = {str(a["id"]): a for a in assets}
    aspects = _aspects_for(assets)
    ordered = [str(a["id"]) for a in assets]

    with config_override(cfg):
        cover_id, cover_meta = pick_cover_asset_id_with_meta(assets, export_layout="web")
        closing = pick_closing_with_meta(trip, prefer_landscape=True, require_hard=False)
        moment_cfg = MomentConfig(auto_disable_small_trip=False, min_score=0.0)
        pool = build_moment_pool(trip, assets, cfg=moment_cfg)
        screens = plan_screens_for_chapter(
            ordered,
            aspects,
            assets=assets_map,
            include_chapter_hero=True,
            trip=trip,
            app_config=cfg,
        )

    food_grids = [sc for sc in screens if sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT]
    food_ids = {aid for aid, a in assets_map.items() if is_food_asset(a)}
    return {
        "label": label,
        "coverAssetId": cover_id,
        "coverIsFood": cover_id in food_ids,
        "coverFoodPolicy": (cover_meta.get("foodPolicy") or {}).get("cover"),
        "closingAssetId": closing.get("closing_asset_id"),
        "closingIsFood": bool(
            closing.get("closing_asset_id")
            and closing.get("closing_asset_id") in food_ids
        ),
        "closingFoodPolicy": (trip.get("curation") or {})
        .get("foodPolicy", {})
        .get("closing"),
        "momentPoolIds": pool,
        "momentContainsFood": any(aid in food_ids for aid in pool),
        "foodGridCount": len(food_grids),
        "foodGridSlotCounts": [len(sc.get("slots") or []) for sc in food_grids],
        "soloFoodScreenCount": _solo_food_screen_count(screens, assets_map),
        "foodPolicyGrids": (trip.get("curation") or {})
        .get("foodPolicy", {})
        .get("grids"),
        "patterns": [sc.get("patternId") for sc in screens],
    }


def run_acceptance(*, include_pytest: bool = True, include_demo_verify: bool = False) -> dict:
    checks: list[dict] = []

    frp = _run_variant("frp_default", _with_role())
    legacy = _run_variant("legacy_phase10", _legacy_role())

    checks.append(
        {
            "id": "ac-frp-d1-cover",
            "name": "FRP cover is not food when landscape exists",
            "passed": frp["coverIsFood"] is False,
            "frp": frp["coverAssetId"],
            "legacy": legacy["coverAssetId"],
            "legacyCoverIsFood": legacy["coverIsFood"],
        }
    )
    checks.append(
        {
            "id": "ac-frp-d1-closing",
            "name": "FRP closing is not food when landscape exists",
            "passed": frp["closingIsFood"] is False,
            "frp": frp["closingAssetId"],
            "legacy": legacy["closingAssetId"],
        }
    )
    checks.append(
        {
            "id": "ac-frp-d1-moment",
            "name": "FRP moment pool excludes food",
            "passed": frp["momentContainsFood"] is False,
            "frpPool": frp["momentPoolIds"],
            "legacyContainsFood": legacy["momentContainsFood"],
        }
    )
    checks.append(
        {
            "id": "ac-frp-d1-grid",
            "name": "FRP forms food-grid; solo food screens decrease vs legacy",
            "passed": (
                frp["foodGridCount"] >= 1
                and frp["soloFoodScreenCount"] < legacy["soloFoodScreenCount"]
            ),
            "frpFoodGridCount": frp["foodGridCount"],
            "frpSoloFood": frp["soloFoodScreenCount"],
            "legacyFoodGridCount": legacy["foodGridCount"],
            "legacySoloFood": legacy["soloFoodScreenCount"],
            "frpSlotCounts": frp["foodGridSlotCounts"],
        }
    )
    checks.append(
        {
            "id": "ac-frp-d1-grids-log",
            "name": "FRP writes foodPolicy.grids[]",
            "passed": bool(frp.get("foodPolicyGrids")),
            "grids": frp.get("foodPolicyGrids"),
        }
    )

    # 2-food threshold
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=UTC)
    two = {
        f"f{i}": {
            **_asset(f"f{i}", food=True, taken_offset_min=i, sharp=200.0, w=1200, h=1200),
            "takenAt": (base + timedelta(seconds=i)).isoformat().replace("+00:00", "Z"),
        }
        for i in range(2)
    }
    with config_override(_with_role()):
        screens = plan_screens_for_chapter(
            list(two.keys()),
            {k: "square" for k in two},
            assets=two,
            include_chapter_hero=False,
        )
    food = [sc for sc in screens if sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT]
    checks.append(
        {
            "id": "ac-frp-08",
            "name": "2 food -> food-grid",
            "passed": len(food) == 1 and len(food[0].get("slots") or []) == 2,
        }
    )

    if include_pytest:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/curation/test_food_role_policy.py",
            "tests/unit/curation/test_food_grid.py",
            "-q",
        ]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
        checks.append(
            {
                "id": "ac-frp-pytest",
                "name": "unit suite green",
                "passed": proc.returncode == 0,
                "returnCode": proc.returncode,
                "stdoutTail": (proc.stdout or "")[-400:],
            }
        )

    if include_demo_verify:
        cmd = [sys.executable, "-m", "travelogue", "demo", "verify"]
        proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
        checks.append(
            {
                "id": "ac-frp-demo-verify",
                "name": "demo verify no regression",
                "passed": proc.returncode == 0,
                "returnCode": proc.returncode,
            }
        )

    passed = all(bool(c.get("passed")) for c in checks)
    return {
        "schemaVersion": "1",
        "phase": "FRP-FoodRolePolicy",
        "recordedAt": _now(),
        "status": "passed" if passed else "failed",
        "variants": {"frp": frp, "legacy": legacy},
        "checks": checks,
        "manualDogfood": {
            "status": "pending_product",
            "checklist": "docs/acceptance-records/food-role-policy-dogfood-CHECKLIST.md",
            "fixturePath": str(FIXTURE_PATH.relative_to(ROOT)).replace("\\", "/"),
            "note": "仓库无真实混拍 trip；本记录为 fixture 量化对比。AC-FRP-D2/D3 需产品目视签字。",
        },
        "decisions": {
            "Q1_cover_policy": "demote@0.15",
            "Q2_two_food_pattern": "screen-square-4",
            "Q3_cluster_window_seconds": 3600,
            "Q4_food_grid_as_moment": False,
            "Q5_sign_ticket_cover_demote": False,
        },
    }


def write_fixture(path: Path) -> None:
    trip = _build_mixed_trip()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trip, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="FRP food role policy acceptance")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "food-role-policy.fixture.json",
    )
    parser.add_argument("--write-fixture", action="store_true", help="also write schemas fixture")
    parser.add_argument("--skip-pytest", action="store_true")
    parser.add_argument("--include-demo-verify", action="store_true")
    args = parser.parse_args()

    if args.write_fixture:
        write_fixture(FIXTURE_PATH)
        print(f"Wrote {FIXTURE_PATH}", file=sys.stderr)

    record = run_acceptance(
        include_pytest=not args.skip_pytest,
        include_demo_verify=args.include_demo_verify,
    )
    text = json.dumps(record, ensure_ascii=False, indent=2)
    print(text)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {args.write}", file=sys.stderr)
    return 0 if record.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
