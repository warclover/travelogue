"""Template discovery: metadata, sort, recommend (PRD §5.7)."""

from __future__ import annotations

from datetime import UTC
from typing import Any

from travelogue.templates.registry import TemplateRecord


def discovery_row(rec: TemplateRecord, *, lifecycle: str) -> dict[str, Any]:
    meta = getattr(rec, "discovery", None) or {}
    return {
        "templateId": rec.template_id,
        "category": meta.get("category", "general"),
        "tags": list(meta.get("tags") or ()),
        "style": meta.get("style"),
        "complexity": meta.get("complexity"),
        "bestFor": list(meta.get("bestFor") or ()),
        "lifecycle": lifecycle,
        "version": rec.version,
    }


def _popular_rank() -> dict[str, int]:
    """Lower rank = more popular (from discovery select metrics)."""

    from travelogue.templating.metrics import metrics_path

    scores: dict[str, int] = {}
    path = metrics_path()
    if not path.is_file():
        return scores
    import json
    from datetime import datetime, timedelta

    cutoff = datetime.now(UTC) - timedelta(hours=24 * 30)
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("name")) != "template.discovery.select_count":
                continue
            at_raw = row.get("at")
            if at_raw:
                at = datetime.fromisoformat(str(at_raw).replace("Z", "+00:00"))
                if at.tzinfo is None:
                    at = at.replace(tzinfo=UTC)
                if at < cutoff:
                    continue
            tid = str(row.get("templateId") or "")
            if tid:
                scores[tid] = scores.get(tid, 0) + 1
    except OSError:
        pass
    ranked = sorted(scores.items(), key=lambda x: (-x[1], x[0]))
    return {tid: i for i, (tid, _) in enumerate(ranked)}


def sort_consumer_templates(
    items: list[dict[str, Any]],
    *,
    display_order: tuple[str, ...],
    recommended: tuple[str, ...],
    sort_mode: str = "recommended",
    team_templates: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    rec_rank = {tid: i for i, tid in enumerate(recommended)} if recommended else {}
    order_rank = {tid: i for i, tid in enumerate(display_order)}
    popular_rank = _popular_rank()
    team_set = frozenset(team_templates or recommended or ())

    def key(row: dict[str, Any]) -> tuple:
        tid = str(row.get("templateId") or "")
        if sort_mode == "alphabetical":
            return (tid,)
        if sort_mode == "category":
            return (str(row.get("category") or "general"), rec_rank.get(tid, 999), tid)
        if sort_mode == "latest":
            rev = row.get("revision")
            try:
                rev_n = -int(rev)
            except (TypeError, ValueError):
                rev_n = 0
            return (rev_n, tid)
        if sort_mode == "popular":
            return (popular_rank.get(tid, 999), tid)
        if sort_mode == "team":
            in_team = 0 if tid in team_set else 1
            return (in_team, rec_rank.get(tid, 999), tid)
        return (rec_rank.get(tid, 999), order_rank.get(tid, 999), tid)

    return sorted(items, key=key)


def filter_admin_templates(
    rows: list[dict[str, Any]],
    *,
    lifecycle: str | None = None,
    category: str | None = None,
    query: str | None = None,
) -> list[dict[str, Any]]:
    out = rows
    if lifecycle:
        out = [r for r in out if str(r.get("lifecycle") or "") == lifecycle]
    if category:
        out = [r for r in out if str(r.get("category") or "general") == category]
    if query:
        q = query.strip().lower()
        out = [
            r
            for r in out
            if q in str(r.get("templateId") or "").lower()
            or q in str(r.get("category") or "").lower()
            or any(q in str(t).lower() for t in (r.get("tags") or []))
        ]
    return out
