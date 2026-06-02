#!/usr/bin/env python3
"""Phase 10 · Food Grid acceptance helper (AC-P10-01/02 auto + AC-P10-03 fixture spec)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from travelogue.curation.screen_planner import FOOD_GRID_LAYOUT_HINT, plan_screens_for_chapter


def _build_assets(
    ids: list[str],
    *,
    food_ids: set[str],
    clip_ids: set[str] | None = None,
    tag_value: str = "food",
) -> tuple[dict[str, dict], dict[str, str]]:
    clip_ids = clip_ids or set()
    base = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    assets: dict[str, dict] = {}
    aspects: dict[str, str] = {}
    for idx, aid in enumerate(ids):
        asset: dict = {
            "id": aid,
            "type": "image",
            "takenAt": (base + timedelta(seconds=idx)).isoformat().replace("+00:00", "Z"),
        }
        if aid in food_ids:
            if aid in clip_ids:
                asset["subjectClass"] = "food"
                asset["subjectConfidence"] = 0.92
            else:
                asset["tags"] = [tag_value]
        assets[aid] = asset
        if aid.startswith("p"):
            aspects[aid] = "portrait"
        elif aid.startswith("l"):
            aspects[aid] = "landscape"
        else:
            aspects[aid] = "square"
    return assets, aspects


def _food_screens(screens: list[dict]) -> list[dict]:
    return [sc for sc in screens if sc.get("layoutHint") == FOOD_GRID_LAYOUT_HINT]


def _bucket_screens(screens: list[dict], hint: str) -> list[dict]:
    return [sc for sc in screens if sc.get("layoutHint") == hint]


def run_acceptance(
    *,
    include_phase101: bool = False,
    include_demo_verify: bool = False,
    mundane_grid_buckets: tuple[str, ...] = ("food",),
) -> dict:
    checks: list[dict] = []

    ids = ["f1", "f2", "f3"]
    assets, aspects = _build_assets(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=mundane_grid_buckets,
    )
    food = _food_screens(screens)
    checks.append(
        {
            "id": "ac-p10-auto-01",
            "name": "3 food -> square-4 food-grid",
            "passed": len(food) == 1 and food[0].get("patternId") == "screen-square-4",
            "actualPatterns": [sc.get("patternId") for sc in screens],
            "foodGridCount": len(food),
        }
    )

    ids = [f"f{i}" for i in range(6)]
    assets, aspects = _build_assets(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=mundane_grid_buckets,
    )
    food = _food_screens(screens)
    checks.append(
        {
            "id": "ac-p10-auto-02",
            "name": "6 food -> square-6",
            "passed": len(food) == 1 and food[0].get("patternId") == "screen-square-6",
            "actualPatterns": [sc.get("patternId") for sc in screens],
            "foodGridCount": len(food),
        }
    )

    ids = [f"f{i}" for i in range(12)]
    assets, aspects = _build_assets(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        mundane_grid_buckets=mundane_grid_buckets,
    )
    food = _food_screens(screens)
    checks.append(
        {
            "id": "ac-p10-auto-03",
            "name": "9+ food -> split multiple food grids",
            "passed": len(food) >= 2
            and food[0].get("patternId") == "screen-square-9"
            and food[1].get("patternId") == "screen-square-4",
            "actualPatterns": [sc.get("patternId") for sc in food],
            "foodGridCount": len(food),
        }
    )

    ids = ["f1", "f2", "f3", "f4"]
    assets, aspects = _build_assets(ids, food_ids=set(ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        enable_food_grid=False,
        mundane_grid_buckets=mundane_grid_buckets,
    )
    checks.append(
        {
            "id": "ac-p10-auto-04",
            "name": "enable_food_grid=false fallback",
            "passed": len(_food_screens(screens)) == 0,
            "actualPatterns": [sc.get("patternId") for sc in screens],
            "foodGridCount": len(_food_screens(screens)),
        }
    )

    portrait_ids = [f"p{i}" for i in range(8)]
    food_ids = ["f1", "f2", "f3"]
    ids = portrait_ids + food_ids
    assets, aspects = _build_assets(ids, food_ids=set(food_ids))
    screens = plan_screens_for_chapter(
        ids,
        aspects,
        assets=assets,
        include_chapter_hero=False,
        burst_seconds=10.0,
        trip_photo_total=80,
        orientation_summary={"portrait": 50, "landscape": 20},
        mundane_grid_buckets=mundane_grid_buckets,
    )
    patterns = [sc.get("patternId") for sc in screens]
    checks.append(
        {
            "id": "ac-p10-auto-05",
            "name": "portrait-grid + food-grid coexist",
            "passed": "screen-portrait-grid-8" in patterns and bool(_food_screens(screens)),
            "actualPatterns": patterns,
            "foodGridCount": len(_food_screens(screens)),
        }
    )

    if include_phase101:
        ids = ["s1", "s2", "s3"]
        assets, aspects = _build_assets(ids, food_ids=set())
        for aid in ids:
            assets[aid]["tags"] = ["sign"]
        screens = plan_screens_for_chapter(
            ids,
            aspects,
            assets=assets,
            include_chapter_hero=False,
            mundane_grid_buckets=mundane_grid_buckets,
        )
        checks.append(
            {
                "id": "ac-p10-1-auto-sign-01",
                "name": "3 sign -> sign-grid when bucket enabled",
                "passed": bool(_bucket_screens(screens, "sign-grid")),
                "actualPatterns": [sc.get("patternId") for sc in screens],
            }
        )

        ids = ["t1", "t2", "t3"]
        assets, aspects = _build_assets(ids, food_ids=set())
        for aid in ids:
            assets[aid]["tags"] = ["ticket"]
        screens = plan_screens_for_chapter(
            ids,
            aspects,
            assets=assets,
            include_chapter_hero=False,
            mundane_grid_buckets=mundane_grid_buckets,
        )
        checks.append(
            {
                "id": "ac-p10-1-auto-ticket-01",
                "name": "3 ticket -> ticket-grid when bucket enabled",
                "passed": bool(_bucket_screens(screens, "ticket-grid")),
                "actualPatterns": [sc.get("patternId") for sc in screens],
            }
        )

        ids = ["h1", "h2", "h3"]
        assets, aspects = _build_assets(ids, food_ids=set())
        for aid in ids:
            assets[aid]["tags"] = ["shop"]
        screens = plan_screens_for_chapter(
            ids,
            aspects,
            assets=assets,
            include_chapter_hero=False,
            mundane_grid_buckets=mundane_grid_buckets,
        )
        checks.append(
            {
                "id": "ac-p10-1-auto-shop-01",
                "name": "3 shop -> shop-grid when bucket enabled",
                "passed": bool(_bucket_screens(screens, "shop-grid")),
                "actualPatterns": [sc.get("patternId") for sc in screens],
            }
        )

    if include_demo_verify:
        cmd = [sys.executable, "-m", "travelogue", "demo", "verify"]
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        checks.append(
            {
                "id": "ac-p10-auto-06",
                "name": "demo verify no regression",
                "passed": proc.returncode == 0,
                "command": " ".join(cmd),
                "returnCode": proc.returncode,
            }
        )

    manual_fixture = {
        "tripId": "phase10-food-grid-manual-fixture",
        "fixturePath": "schemas/fixtures/trip.phase10_food_grid.json",
        "description": "用于 AC-P10-03 人工抽检（章内 >=3 food，含 portrait run 共存）",
        "orderedAssetIds": [f"p{i}" for i in range(8)] + ["f1", "f2", "l1", "f3", "f4", "f5"],
        "expected": {
            "mustContainLayoutHint": FOOD_GRID_LAYOUT_HINT,
            "mustContainPatterns": ["screen-portrait-grid-8", "screen-square-4"],
        },
    }
    passed = all(bool(c["passed"]) for c in checks)
    return {
        "schemaVersion": "1",
        "phase": "P10-FoodGrid",
        "recordedAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "passed" if passed else "failed",
        "checks": checks,
        "manualFixtureSpec": manual_fixture,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 10 food grid acceptance helper")
    parser.add_argument(
        "--write",
        type=Path,
        default=ROOT / "docs" / "acceptance-records" / "phase10-food-grid.json",
        help="write acceptance record json",
    )
    parser.add_argument(
        "--include-phase101",
        action="store_true",
        help="include optional phase10.1 sign/ticket/shop checks",
    )
    parser.add_argument(
        "--include-demo-verify",
        action="store_true",
        help="run `python -m travelogue demo verify` and append check result",
    )
    parser.add_argument(
        "--mundane-buckets",
        type=str,
        default="food",
        help="comma-separated mundane buckets (e.g. food,sign,ticket,shop)",
    )
    args = parser.parse_args()

    buckets = tuple(x.strip().lower() for x in args.mundane_buckets.split(",") if x.strip())
    record = run_acceptance(
        include_phase101=args.include_phase101,
        include_demo_verify=args.include_demo_verify,
        mundane_grid_buckets=buckets or ("food",),
    )
    text = json.dumps(record, ensure_ascii=False, indent=2)
    print(text)
    args.write.parent.mkdir(parents=True, exist_ok=True)
    args.write.write_text(text + "\n", encoding="utf-8")
    print(f"Wrote {args.write}", file=sys.stderr)
    return 0 if record.get("status") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
