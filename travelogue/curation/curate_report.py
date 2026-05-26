"""Human-readable curate summaries for CLI."""

from __future__ import annotations


def format_curate_report(result, trip: dict | None = None) -> str:
    lines: list[str] = []
    lines.append(
        f"策展 {getattr(result, 'chapter_count', '?')} 章 · "
        f"封面 {getattr(result, 'cover_asset_id', '-')}"
    )
    if getattr(result, "day_groups", None):
        lines.append(f"  日桶 {result.day_groups} → 章 {result.chapter_count}")

    if trip:
        curation = trip.get("curation") or {}
        segs = curation.get("segments") or []
        if segs:
            lines.append(f"  时间段 {len(segs)} 段")
        excluded = curation.get("excludedLowResAssetIds") or []
        if excluded:
            lines.append(f"  低分辨率剔除 {len(excluded)} 张")
        plan = curation.get("chapterPlan") or []
        for entry in plan[:6]:
            idx = entry.get("chapterIndex", "?")
            n = entry.get("assetCount", 0)
            pat = entry.get("patternHint") or entry.get("patternId") or "?"
            title = ""
            for ch in trip.get("chapters") or []:
                if ch.get("index") == idx:
                    title = ch.get("title", "")
                    break
            lines.append(f"    [{idx}] {title or '—'} · {n} 张 · {pat}")
        if len(plan) > 6:
            lines.append(f"    …共 {len(plan)} 章")

    for w in getattr(result, "warnings", None) or []:
        lines.append(f"  WARN: {w}")
    return "\n".join(lines)
