"""SNR · narrate success diff summary (D-SNR-06 / COPY-SNR-D*)."""

from __future__ import annotations

from typing import Any


def summarize_narrate_fields(fields_updated: list[str] | None) -> dict[str, Any]:
    """Turn fields_updated paths into a chrome-facing diff summary.

    Returns ``{slotsLabel, slotTypes, firstAnchor, count}``.
    Empty fields → empty slotsLabel (caller must not show fake diff).
    """
    fields = [str(f).strip() for f in (fields_updated or []) if str(f).strip()]
    if not fields:
        return {
            "slotsLabel": "",
            "slotTypes": [],
            "firstAnchor": "",
            "count": 0,
        }

    has_hook = False
    lead_n = 0
    has_epilogue = False
    caption_n = 0
    title_n = 0
    other_n = 0
    first_anchor = ""

    for f in fields:
        if f == "meta.hook" or f.endswith(".hook"):
            has_hook = True
            if not first_anchor:
                first_anchor = "#cover, .cover-hook, [data-cover-hook], .vj-cover"
            continue
        if ".lead" in f or f.endswith("].lead"):
            lead_n += 1
            if not first_anchor:
                first_anchor = ".chapter-lead, [data-chapter-lead], .vj-chapter-lead"
            continue
        if f == "epilogue" or f.endswith("epilogue"):
            has_epilogue = True
            if not first_anchor:
                first_anchor = ".epilogue, [data-epilogue]"
            continue
        if ".caption" in f:
            caption_n += 1
            continue
        if ".title" in f:
            title_n += 1
            continue
        other_n += 1

    parts: list[str] = []
    slot_types: list[str] = []
    if has_hook:
        parts.append("封面钩子")
        slot_types.append("hook")
    if lead_n:
        parts.append(f"{lead_n} 段章导语" if lead_n > 1 else "章导语")
        slot_types.append("lead")
    if has_epilogue:
        parts.append("辑封一句")
        slot_types.append("epilogue")
    if caption_n:
        parts.append(f"{caption_n} 条图注" if caption_n > 1 else "图注")
        slot_types.append("caption")
    if title_n and not parts:
        parts.append("章名")
        slot_types.append("title")
    if other_n and not parts:
        parts.append("文案")
        slot_types.append("other")

    return {
        "slotsLabel": " · ".join(parts),
        "slotTypes": slot_types,
        "firstAnchor": first_anchor,
        "count": len(fields),
    }
