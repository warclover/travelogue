"""AA · stratum relabel audit (compare label stratum vs review_stratum_for_asset)."""

from __future__ import annotations

import copy
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset


def merged_asset_key(trip_id: str, asset_id: str) -> str:
    return f"{trip_id}::{asset_id}"


def load_trip_assets_by_id(trip_dir: Path) -> dict[str, dict]:
    trip = json.loads((trip_dir / "trip.json").read_text(encoding="utf-8"))
    return {str(a["id"]): a for a in (trip.get("assets") or []) if a.get("id")}


def audit_label_strata(
    *,
    trip_dir: Path,
    label_rows: list[dict[str, Any]],
    trip_id: str | None = None,
) -> dict[str, Any]:
    """Compare stored ``stratum`` on label rows vs current ``review_stratum_for_asset``."""
    assets = load_trip_assets_by_id(trip_dir)
    tid = trip_id or json.loads((trip_dir / "trip.json").read_text(encoding="utf-8")).get("tripId")
    changes: list[dict[str, Any]] = []
    old_counts: Counter[str] = Counter()
    new_counts: Counter[str] = Counter()
    matrix: Counter[tuple[str | None, str | None]] = Counter()

    for row in label_rows:
        if row.get("humanScore") is None:
            continue
        aid = str(row.get("assetId") or "")
        old = row.get("stratum")
        asset = assets.get(aid)
        new = review_stratum_for_asset(asset) if asset else None
        old_counts[str(old)] += 1
        new_counts[str(new)] += 1
        if old != new:
            changes.append(
                {
                    "assetId": aid,
                    "tripId": tid,
                    "oldStratum": old,
                    "newStratum": new,
                    "displayFile": row.get("displayFile"),
                }
            )
            matrix[(str(old) if old is not None else None, str(new) if new is not None else None)] += 1

    labeled = sum(1 for r in label_rows if r.get("humanScore") is not None)
    return {
        "tripId": tid,
        "tripDir": str(trip_dir),
        "labeledCount": labeled,
        "changeCount": len(changes),
        "changeRatio": round(len(changes) / labeled, 4) if labeled else None,
        "oldStrata": dict(old_counts),
        "newStrata": dict(new_counts),
        "changeMatrix": {f"{o}->{n}": c for (o, n), c in sorted(matrix.items())},
        "changes": changes,
    }


def apply_stratum_audit(
    labels_doc: dict[str, Any],
    audit: dict[str, Any],
    *,
    audit_note: str,
) -> dict[str, Any]:
    """Rewrite label rows: ``stratumAuto`` <- old stratum, ``stratum`` <- audited value."""
    change_by_id = {c["assetId"]: c for c in (audit.get("changes") or [])}
    out = copy.deepcopy(labels_doc)
    rows = list(out.get("rows") or [])
    applied = 0
    for row in rows:
        aid = str(row.get("assetId") or "")
        ch = change_by_id.get(aid)
        if not ch:
            if "stratumAuto" not in row and row.get("stratum") is not None:
                row["stratumAuto"] = row["stratum"]
            continue
        if "stratumAuto" not in row:
            row["stratumAuto"] = row.get("stratum")
        row["stratum"] = ch["newStratum"]
        applied += 1
    out["rows"] = rows
    out["stratumAudit"] = {
        "auditedAt": datetime.now(timezone.utc).isoformat(),
        "changeCount": applied,
        "changeRatio": audit.get("changeRatio"),
        "oldStrata": audit.get("oldStrata"),
        "newStrata": audit.get("newStrata"),
        "changeMatrix": audit.get("changeMatrix"),
        "notes": audit_note,
    }
    return out


def remap_rows_for_merged(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefix assetId with tripId so pooled grids work across trips."""
    remapped: list[dict[str, Any]] = []
    for row in label_rows:
        r = dict(row)
        tid = str(row.get("tripId") or "")
        aid = str(row.get("assetId") or "")
        r["_originalTripId"] = tid
        r["_originalAssetId"] = aid
        r["assetId"] = merged_asset_key(tid, aid)
        remapped.append(r)
    return remapped
