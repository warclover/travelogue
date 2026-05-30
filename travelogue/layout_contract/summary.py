"""Layout plan version and human-readable summaries."""

from __future__ import annotations

LAYOUT_PLAN_VERSION = "0.2.0"
VALID_EXPORT_LAYOUTS = frozenset({"auto", "mobile", "web"})


def format_layout_summary(summary: dict, chapters: list[dict]) -> str:
    """Human-readable summary for CLI / G1."""
    parts = [
        f"共 {summary.get('total', 0)} 张",
        f"横 {summary.get('landscape', 0)}",
        f"竖 {summary.get('portrait', 0)}",
    ]
    if summary.get("square"):
        parts.append(f"方 {summary['square']}")
    if summary.get("panorama"):
        parts.append(f"全景 {summary['panorama']}")
    if summary.get("tall"):
        parts.append(f"超长 {summary['tall']}")
    engine = None
    row_counts: dict[str, int] = {}
    slots: dict[str, int] = {}
    screen_counts: dict[str, int] = {}
    screen_total = 0
    for ch in chapters:
        if ch.get("screens"):
            engine = engine or "screens"
            for sc in ch.get("screens") or []:
                screen_total += 1
                pid = sc.get("patternId") or "screen"
                screen_counts[pid] = screen_counts.get(pid, 0) + 1
        for it in ch.get("items", []):
            rl = it.get("rowLayout")
            if rl:
                row_counts[rl] = row_counts.get(rl, 0) + 1
            if it.get("type") == "media-card":
                slot = (it.get("layout") or {}).get("slot")
                if slot:
                    slots[slot] = slots.get(slot, 0) + 1

    hints: list[str] = []
    if row_counts.get("landscape-triple"):
        hints.append(f"{row_counts['landscape-triple']} 组横图三联")
    if row_counts.get("portrait-triple"):
        hints.append(f"{row_counts['portrait-triple']} 组竖图三联")
    if row_counts.get("portrait-pair"):
        hints.append(f"{row_counts['portrait-pair']} 组竖图双列")
    if row_counts.get("square-triple"):
        hints.append(f"{row_counts['square-triple']} 组方图三宫格")
    if row_counts.get("square-pair"):
        hints.append(f"{row_counts['square-pair']} 组方图双列")
    if slots.get("panorama"):
        hints.append(f"{slots['panorama']} 条全景宽条")

    if engine == "screens" and screen_total:
        parts.append("引擎 screens")
        parts.append(f"{screen_total} 屏")
        for pid, n in sorted(screen_counts.items(), key=lambda x: (-x[1], x[0])):
            short = pid.replace("screen-", "").replace("landscape", "横").replace("portrait", "竖")
            short = short.replace("square", "方").replace("panorama", "全景")
            if pid.endswith("-3"):
                hints.append(f"{n}×{short}三联")
            elif pid.endswith("-4"):
                hints.append(f"{n}×{short}四宫格")
            elif pid.endswith("-9"):
                hints.append(f"{n}×{short}九宫格")
            elif pid.endswith("-1"):
                hints.append(f"{n}×{short}单张")
            else:
                hints.append(f"{n}×{short}")

    parts.append(f"版式 {summary.get('export_layout', 'mobile')}")

    line1 = " · ".join(parts)
    if hints:
        return f"{line1}；{'、'.join(hints)}"
    return line1
