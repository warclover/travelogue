"""Share-Face Integrity · Xiaohongshu copy pack (D-SFI-14 / FE-SFI-12)."""

from __future__ import annotations


def build_share_copy_pack(
    trip: dict | None,
    *,
    llm_available: bool,
) -> dict[str, str]:
    """Title + optional body + topics.

    OQ-2 · 无 Key：仅标题 + 话题模板，不造正文。
    有 Key：正文复用 meta.hook（开头一句）；空 hook 则无正文段。
    """
    from travelogue.domain.title_humanize import resolve_display_title

    meta = (trip or {}).get("meta") if isinstance(trip, dict) else None
    meta = meta if isinstance(meta, dict) else {}
    title = resolve_display_title(meta) or str(meta.get("title") or "").strip()
    hook = str(meta.get("hook") or "").strip()
    places = meta.get("places") if isinstance(meta.get("places"), list) else []
    tags: list[str] = ["#旅行日记"]
    for p in places[:2]:
        label = str(p or "").strip()
        if label:
            tags.append("#" + label.replace(" ", ""))
    return {
        "title": title,
        "body": hook if llm_available else "",
        "topics": " ".join(tags),
    }
