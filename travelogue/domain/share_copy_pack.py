"""Share-Face Integrity · Xiaohongshu copy pack (D-SFI-14 / FE-SFI-12).

SNR D-SNR-10 · L0 标题话题 / L1 规则拼装正文（非新 LLM 调用）。
"""

from __future__ import annotations

from travelogue.domain.share_face_copy import sanitize_share_copy


def _clip_lead(text: str, *, max_len: int = 72) -> str:
    t = (text or "").strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1].rstrip() + "…"


def _place_date_line(trip: dict, *, title: str | None) -> str:
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    places = meta.get("places") if isinstance(meta.get("places"), list) else []
    place = ""
    for p in places[:1]:
        label = str(p or "").strip()
        if label:
            place = label
            break
    start = str(meta.get("dateStart") or "")[:10]
    date_label = ""
    if len(start) >= 10 and start[4] == "-" and start[7] == "-":
        try:
            m = int(start[5:7])
            d = int(start[8:10])
            date_label = f"{m}月{d}日"
        except ValueError:
            date_label = ""
    line = " · ".join(x for x in (place, date_label) if x)
    return sanitize_share_copy(line, title=title, kind="caption") or ""


def build_l1_body(trip: dict | None) -> str:
    """L1 body：hook → 最多 3 条非空章 lead → 可选地点/日期一行。"""
    trip = trip if isinstance(trip, dict) else None
    if not trip:
        return ""
    meta = trip.get("meta") if isinstance(trip.get("meta"), dict) else {}
    title = str(meta.get("displayTitle") or meta.get("title") or "").strip() or None
    parts: list[str] = []
    hook = sanitize_share_copy(meta.get("hook"), title=title, kind="lead")
    if hook:
        parts.append(_clip_lead(hook, max_len=80))
    leads: list[str] = []
    for ch in trip.get("chapters") or []:
        if not isinstance(ch, dict):
            continue
        if (ch.get("curation") or {}).get("isAppendix"):
            continue
        lead = sanitize_share_copy(
            ch.get("lead") or ch.get("intro"), title=title, kind="lead"
        )
        if lead:
            leads.append(_clip_lead(lead))
        if len(leads) >= 3:
            break
    parts.extend(leads)
    if not parts:
        return ""
    extra = _place_date_line(trip, title=title)
    if extra and extra not in parts:
        parts.append(extra)
    return "\n".join(parts)


def build_share_copy_pack(
    trip: dict | None,
    *,
    llm_available: bool = False,
) -> dict[str, str]:
    """Title + optional body + topics.

    SNR D-SNR-10：
    - L1：成册已有合格 hook/lead → 规则拼装 body（不依赖 Key）
    - L0：无叙事 → body 空；UI 用 COPY-SNR-X01
    ``llm_available`` 保留兼容；不再作为 body 开关。
    """
    del llm_available  # SNR · body 由版心叙事决定，非 Key 门控
    from travelogue.domain.narrative_posture import has_reader_narrative
    from travelogue.domain.title_humanize import resolve_display_title

    meta = (trip or {}).get("meta") if isinstance(trip, dict) else None
    meta = meta if isinstance(meta, dict) else {}
    title = resolve_display_title(meta) or str(meta.get("title") or "").strip()
    places = meta.get("places") if isinstance(meta.get("places"), list) else []
    tags: list[str] = ["#旅行日记"]
    for p in places[:2]:
        label = str(p or "").strip()
        if label:
            tags.append("#" + label.replace(" ", ""))

    level = "L0"
    body = ""
    hint = "标题和话题已备好 · 正文可粘贴后自填"  # COPY-SNR-X01
    if isinstance(trip, dict) and has_reader_narrative(trip):
        body = build_l1_body(trip)
        if body:
            level = "L1"
            hint = "已带入杂志文案摘要 · 可粘贴后微调"  # COPY-SNR-X02

    return {
        "title": title,
        "body": body,
        "topics": " ".join(tags),
        "level": level,
        "hint": hint,
    }
