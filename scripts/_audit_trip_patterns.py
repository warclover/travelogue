#!/usr/bin/env python3
"""Audit screen pattern usage for a trip (one-off analysis)."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PATTERN_CN = {
    "screen-landscape-9": "九宫格（9张横版）",
    "screen-landscape-6": "六宫格（6张横版）",
    "screen-landscape-4": "四宫格（4张横版）",
    "screen-landscape-3": "三横叠放",
    "screen-landscape-1": "单张横版",
    "screen-portrait-9": "九宫格（9张竖版）",
    "screen-portrait-6": "六宫格（6张竖版）",
    "screen-portrait-4": "四宫格（4张竖版）",
    "screen-portrait-3": "三竖并列",
    "screen-portrait-2": "两张竖版",
    "screen-portrait-1": "单张竖版",
    "screen-portrait-grid-8": "竖版八宫格（2×4）",
    "screen-portrait-1-landscape-2": "1竖+2横",
    "screen-portrait-2-landscape-2": "2竖+2横",
    "screen-mosaic-5-main-portrait-3land": "5窗马赛克（主竖+3横）",
    "screen-mosaic-5-3portrait-2land-balanced": "5窗马赛克（3竖+2横）",
    "screen-mosaic-5-2portrait-3land-balanced": "5窗马赛克（2竖+3横，已退役）",
    "screen-mosaic-5-main-landscape-2portrait-2land": "5窗马赛克（主横+2竖2横，已退役）",
    "screen-mosaic-6-main-hero-plus-5": "6窗主图+5格",
    "screen-square-1": "单张方图",
    "screen-square-4": "四方格",
    "screen-breath-pause": "呼吸留白屏",
    "screen-tall-1": "超高单图",
}

ALL_PATTERNS = list(PATTERN_CN.keys())


def aspect_kind(asset: dict) -> str:
    w, h = asset.get("width") or 1, asset.get("height") or 1
    r = w / h
    if r < 0.85:
        return "portrait"
    if r > 2.5:
        return "panorama"
    if r > 1.2:
        return "landscape"
    return "square"


def analyze(trip_id: str) -> str:
    trip = json.loads((ROOT / "trips" / trip_id / "trip.json").read_text(encoding="utf-8"))
    meta = trip.get("meta") or {}
    curation = trip.get("curation") or {}
    ori = curation.get("orientationSummary") or {}
    amap = {a["id"]: a for a in trip.get("assets") or []}

    screens: list[dict] = []
    for ci, ch in enumerate(trip.get("chapters") or []):
        for si, sc in enumerate(ch.get("screens") or []):
            pid = sc.get("patternId") or "(none)"
            slots = sc.get("slots") or []
            aids = [s.get("assetId") for s in slots if s.get("assetId")]
            kinds = Counter(aspect_kind(amap.get(aid, {})) for aid in aids)
            screens.append(
                {
                    "chapter": ci + 1,
                    "ch_title": ch.get("title") or f"ch{ci + 1}",
                    "idx": si + 1,
                    "pattern": pid,
                    "hint": sc.get("layoutHint"),
                    "n": len(aids),
                    "kinds": dict(kinds),
                }
            )

    pat_counts = Counter(s["pattern"] for s in screens)
    total_layout = int(ori.get("total") or len(trip.get("assets") or []))

    from travelogue.curation.screen_layout_state import (
        nine_grid_limits_for_trip,
        portrait_grid8_max_for_trip,
    )

    nine_lo, nine_hi = nine_grid_limits_for_trip(total_layout)
    p8_max = portrait_grid8_max_for_trip(total_layout)
    lm = curation.get("layoutMetrics") or {}

    lines: list[str] = []
    title = meta.get("title") or trip_id
    lines.append(f"# 模板调用统计 · {title}")
    lines.append("")
    lines.append(f"- **tripId**: `{trip_id}`")
    lines.append(f"- **照片总数**: {len(trip.get('assets') or [])}")
    lines.append(f"- **参与排版**: {ori}")
    lines.append(f"- **屏总数**: {len(screens)}（内容屏 {len(screens) - pat_counts.get('screen-breath-pause', 0)}）")
    lines.append(f"- **九宫格配额**: min={nine_lo}, max={nine_hi}；实际横版九宫 **{pat_counts.get('screen-landscape-9', 0)}** 次")
    lines.append(f"- **竖版八宫格配额上限**: {p8_max}")
    if lm:
        lines.append(
            f"- **layoutMetrics**: repeat_rate={lm.get('patternRepeatRate')}, "
            f"diversity={lm.get('patternDiversity')}"
        )
    lines.append("")

    lines.append("## 已调用模板（按次数）")
    lines.append("")
    lines.append("| 次数 | 中文名 | patternId | layoutHint |")
    lines.append("|------|--------|-----------|------------|")
    for pid, cnt in pat_counts.most_common():
        hints = sorted({s["hint"] for s in screens if s["pattern"] == pid and s["hint"]})
        hint_s = ", ".join(hints) if hints else "—"
        lines.append(f"| {cnt} | {PATTERN_CN.get(pid, pid)} | `{pid}` | {hint_s} |")

    lines.append("")
    lines.append("## 复合模板明细（除单横版/呼吸屏外）")
    lines.append("")
    for s in screens:
        if s["pattern"] in ("screen-landscape-1", "screen-breath-pause"):
            continue
        hint = f" · hint=`{s['hint']}`" if s["hint"] else ""
        lines.append(
            f"- 章{s['chapter']}「{s['ch_title']}」第{s['idx']}屏 · "
            f"**{PATTERN_CN.get(s['pattern'], s['pattern'])}** · "
            f"{s['n']}张 · 构成 {s['kinds']}{hint}"
        )

    used = set(pat_counts)
    unused = [p for p in ALL_PATTERNS if p not in used]

    lines.append("")
    lines.append("## 已调用原因（要点）")
    lines.append("")
    reasons_used = {
        "screen-landscape-9": (
            f"横版连续 run≥9 且 `can_use_nine()`；206 张相册配额允许最多 {nine_hi} 次，"
            f"实际 {pat_counts.get('screen-landscape-9', 0)} 次（在配额内）。"
            "同一 geo bucket 内凑满 9 张横图时优先吃满九宫。"
        ),
        "screen-landscape-4": (
            "横版 run≥4 但未走九宫（配额/连续禁忌/桶内不足 9 张）时，"
            "burst 或密度规则下选 4 宫格。"
        ),
        "screen-portrait-2": (
            "竖版连续 2 张；本 trip 仅 1 次，带 `person-pair` hint，"
            "人物成对竖图专用。"
        ),
        "screen-landscape-1": (
            f"横版 run≤3 直接单屏；或九/四宫消费后剩余单张；"
            f"全景 pano 也映射到此（共 {pat_counts.get('screen-landscape-1', 0)} 次，占主导）。"
        ),
        "screen-portrait-1": "竖版单张或短 run 被拆开后的单屏。",
        "screen-square-1": "方图单张展示。",
        "screen-breath-pause": "章节节奏留白（非照片屏）。",
    }
    for pid, cnt in pat_counts.most_common():
        if pid in reasons_used:
            lines.append(f"- **{PATTERN_CN.get(pid, pid)}** ×{cnt}：{reasons_used[pid]}")

    lines.append("")
    lines.append("## 未调用模板及原因")
    lines.append("")
    lines.append(
        f"相册取向极度偏横：横 {ori.get('landscape', 0)} · 竖 {ori.get('portrait', 0)} · "
        f"方 {ori.get('square', 0)} · 全景 {ori.get('panorama', 0)}。"
        "多数 MCS/竖版模板因「窗口内凑不齐竖版张数」或「已在代码中退役」而未出现。"
    )
    lines.append("")

    reasons_unused = {
        "screen-portrait-9": "竖版仅 12 张，无法形成 9 连竖 run；九宫配额也优先横版。",
        "screen-portrait-6": "6 连竖 run 不存在。",
        "screen-portrait-4": "4 连竖 run 不足。",
        "screen-portrait-3": "竖版 run 太短，被拆成 portrait-1。",
        "screen-portrait-grid-8": f"需 >50 张且竖版主导；竖版 {ori.get('portrait', 0)} 张，配额 {p8_max}。",
        "screen-portrait-1-landscape-2": "需连续 1P+2L 三窗；横版主导流里混合段少。",
        "screen-portrait-2-landscape-2": "需 2P+2L 四窗；竖版稀缺。",
        "screen-mosaic-5-main-portrait-3land": "MCS 5 窗需 1P+4L；横版段被 landscape-9/4/1 先消费。",
        "screen-mosaic-5-3portrait-2land-balanced": "需 3P+2L 五窗；竖版仅 12 张。",
        "screen-mosaic-5-2portrait-3land-balanced": "已从 MOSAIC_5 候选退役（5e97d46）。",
        "screen-mosaic-5-main-landscape-2portrait-2land": "已从 MOSAIC_5 候选退役。",
        "screen-mosaic-6-main-hero-plus-5": "六宫 MCS 需特定 hero 窗；横版 run 多被 nine/4 切走。",
        "screen-landscape-6": "横版 run 切完 nine/4 后常剩 ≤1 张；六宫受连续/配额限制。",
        "screen-landscape-3": "横 run≤3 时规则直接 landscape-1，不组三横。",
        "screen-square-4": f"方图 {ori.get('square', 0)} 张，未触发 food/sign 等 mundane grid。",
        "screen-tall-1": "无 tall 资产。",
    }
    for p in unused:
        lines.append(f"- `{p}`（{PATTERN_CN.get(p, p)}）：{reasons_unused.get(p, '窗口构成不匹配')}")

    logs = curation.get("mosaicDecisionLog") or []
    lines.append("")
    lines.append("## mosaicDecisionLog")
    lines.append("")
    if logs:
        lines.append(f"共 {len(logs)} 条（可查 winner/fallback 细因）。")
    else:
        lines.append(
            "本 trip **无** `mosaicDecisionLog` 记录（可能为渲染前产物或未写入决策日志）。"
            "上表原因来自 `trip.json` 屏 pattern + 相册取向统计 + 规划器规则推断。"
        )

    return "\n".join(lines)


def main() -> int:
    trip_id = sys.argv[1] if len(sys.argv) > 1 else "demo-1506104ebf"
    report = analyze(trip_id)
    out = ROOT / "docs" / "reports" / f"pattern-audit-{trip_id}.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\n--- written {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
