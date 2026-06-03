"""Per-trip template decision log (PRD §5.6 · AC-P13-07)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# re-export for admin aggregate
__all__ = ["append_decision", "list_decisions", "list_recent_decisions", "log_path"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def log_path(trip_dir: Path) -> Path:
    return trip_dir / "runs" / "template_decisions.jsonl"


def append_decision(
    trip_dir: Path,
    *,
    trip_id: str,
    action: str,
    selection: dict[str, Any],
    extra: dict[str, Any] | None = None,
) -> None:
    """Append one JSON line; never raises on I/O failure."""
    try:
        path = log_path(trip_dir)
        path.parent.mkdir(parents=True, exist_ok=True)
        entry: dict[str, Any] = {
            "at": _utc_now(),
            "tripId": trip_id,
            "action": action,
            "mode": selection.get("mode"),
            "requestedTemplateId": selection.get("requestedTemplateId"),
            "resolvedTemplateId": selection.get("resolvedTemplateId"),
            "confidence": selection.get("confidence"),
            "reasonCodes": selection.get("reasonCodes"),
            "fallbackUsed": selection.get("fallbackUsed"),
            "decisionHash": selection.get("decisionHash"),
            "routerVersion": selection.get("routerVersion"),
        }
        if extra:
            entry.update(extra)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def list_decisions(trip_dir: Path, *, limit: int = 20) -> list[dict[str, Any]]:
    path = log_path(trip_dir)
    if not path.is_file():
        return []
    cap = max(1, min(limit, 200))
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    out: list[dict[str, Any]] = []
    for line in lines[-cap:]:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def list_recent_decisions(
    trips_root: Path,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Aggregate recent decisions across trips (admin §4.4)."""
    cap = max(1, min(limit, 200))
    rows: list[dict[str, Any]] = []
    if not trips_root.is_dir():
        return rows
    for trip_dir in sorted(trips_root.iterdir(), key=lambda p: p.stat().st_mtime if p.is_dir() else 0, reverse=True):
        if not trip_dir.is_dir() or not (trip_dir / "trip.json").is_file():
            continue
        for entry in list_decisions(trip_dir, limit=10):
            rows.append(entry)
        if len(rows) >= cap * 2:
            break
    rows.sort(key=lambda r: str(r.get("at") or ""), reverse=True)
    return rows[:cap]
