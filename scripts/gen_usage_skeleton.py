"""Generate `usage` skeleton blocks for LTE templates that lack them.

Facts (photo count, mix, slot aspects, main slot) are derived from geometry so
humans only fill in judgment content (whenToUse / whenNotToUse / differences).

Usage:
    python scripts/gen_usage_skeleton.py                 # print skeletons
    python scripts/gen_usage_skeleton.py --only mosaic-5 # filter by id substring
    python scripts/gen_usage_skeleton.py --apply         # append blocks to YAML files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台默认 GBK

from travelogue.layout_templates.geometry import slot_aspect_table  # noqa: E402
from travelogue.layout_templates.models import TemplateDef  # noqa: E402
from travelogue.layout_templates.registry import (  # noqa: E402
    DEFAULT_TEMPLATES_DIR,
    LayoutTemplateEngine,
)


def _mix_label(t: TemplateDef) -> str:
    p = t.mix_portrait or 0
    la = t.mix_landscape or 0
    if p and la:
        return f"{p} 竖 + {la} 横"
    if p:
        return f"{p} 竖"
    return f"{la} 横"


def _density_label(t: TemplateDef) -> str:
    n = len(t.slots)
    if n <= 2:
        return "airy"
    if n <= 4:
        return "balanced"
    return "dense"


def _facts_line(t: TemplateDef) -> str:
    rows = slot_aspect_table(t)
    parts = [f"{len(t.slots)} 槽（{_mix_label(t)}）", f"密度 {_density_label(t)}"]
    mains = [r for r in rows if r.role == "main"]
    if mains:
        parts.append(f"主槽 AR≈{mains[0].display_aspect:.2f}")
    ars = sorted({round(r.display_aspect, 2) for r in rows})
    parts.append("槽位 AR " + "/".join(f"{a:.2f}" for a in ars))
    return " · ".join(parts)


def _sibling_candidates(t: TemplateDef, all_templates: dict[str, TemplateDef]) -> list[str]:
    """Same photo count & kind, ranked: same mix first, then same id prefix."""

    def _score(o: TemplateDef) -> tuple[int, int]:
        same_mix = int(
            o.mix_portrait == t.mix_portrait and o.mix_landscape == t.mix_landscape
        )
        shared_prefix = len(
            [a for a, b in zip(t.id.split("-"), o.id.split("-")) if a == b]
        )
        return (same_mix, shared_prefix)

    candidates = [
        o
        for o in all_templates.values()
        if o.id != t.id
        and o.kind == t.kind
        and not (
            o.photo_count_max < t.photo_count_min or o.photo_count_min > t.photo_count_max
        )
    ]
    candidates.sort(key=_score, reverse=True)
    return [o.id for o in candidates[:3]]


def skeleton_for(t: TemplateDef, all_templates: dict[str, TemplateDef]) -> str:
    lines = [
        "usage:",
        f"  # 几何事实：{_facts_line(t)}（自动生成，仅供撰写参考，可删）",
        "  summary: TODO 一句话定位（判断性内容，勿复述几何事实）",
    ]
    if t.status == "deprecated":
        lines += [
            "  whenNotToUse: |",
            "    - 已退役：新 trip 不再候选，仅保留渲染历史 screens[]。",
            "    - TODO 退役原因 / 后继模板。",
        ]
    else:
        lines += [
            "  whenToUse: |",
            "    - TODO 适用时机 1",
            "    - TODO 适用时机 2",
            "  whenNotToUse: |",
            "    - TODO 失败模式 1（从真实排版案例反推）",
            "    - TODO 失败模式 2",
            "  designIntent: TODO 设计意图（可删）",
        ]
    sibs = _sibling_candidates(t, all_templates)
    if sibs:
        lines.append("  siblings:")
        for sid in sibs:
            lines += [
                f"    - id: {sid}",
                "      difference: TODO 与其区别一句话（≤80 字）",
            ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="Filter template ids by substring")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Append skeleton to YAML files missing usage (instead of printing)",
    )
    args = parser.parse_args()

    engine = LayoutTemplateEngine.load()
    all_templates = engine._templates
    missing = [
        t
        for t in all_templates.values()
        if not isinstance(t.raw.get("usage"), dict)
        and (not args.only or args.only in t.id)
    ]
    if not missing:
        print("all matched templates already have usage blocks")
        return 0

    for t in sorted(missing, key=lambda x: x.id):
        block = skeleton_for(t, all_templates)
        if args.apply:
            path = DEFAULT_TEMPLATES_DIR / f"{t.id}.yaml"
            if not path.is_file():
                print(f"SKIP {t.id}: yaml file not found", file=sys.stderr)
                continue
            text = path.read_text(encoding="utf-8")
            if not text.endswith("\n"):
                text += "\n"
            path.write_text(text + block, encoding="utf-8")
            print(f"appended usage skeleton → {path.name}")
        else:
            print(f"# ── {t.id} ({t.status}) " + "─" * 20)
            print(block)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
