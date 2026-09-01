#!/usr/bin/env python3
"""EA-01 · one-shot source-template geometry health check.

Reads only ``travelogue/layout_templates/templates/{screen,page}-*.yaml``.
Never walks ``dist/`` or ``.version_history/``. Policy freezes (slot-count
caps, usage docs) are recorded but do not change the three-state health.

Usage:
  python scripts/ea01_template_geometry_audit.py
  python scripts/ea01_template_geometry_audit.py --json
  python scripts/ea01_template_geometry_audit.py --write-markdown docs/acceptance-records/ea-01-template-geometry-2026-09-01.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Literal

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

Health = Literal["healthy", "suspicious", "broken"]

SOURCE_TEMPLATES_DIR = ROOT / "travelogue" / "layout_templates" / "templates"
KNOWN_ROLES = frozenset({"portrait", "landscape", "main", "tile", "square"})

# Geometry / crop / role. These drive the three-state health.
GEOMETRY_CODES = frozenset(
    {
        "V-P16-01",  # overlap
        "V-P16-02",  # undeclared gap
        "V-P16-03",  # photoCount ≠ slots
        "V-P16-04",  # role ↔ displayAspect
        "V-P16-05",  # CSS grid
        "V-P16-06",  # slot covers no cells
        "V-P16-09",  # mix vs role counts
        "V-P16-10",  # balance policy
        "V-P16-13",  # AR ladder
        "V-P16-14",  # bounds / non-positive tracks
        "V-P16-S01",  # stack geometry
        "EA-01-PARSE",
        "EA-01-SCHEMA",
        "EA-01-INDEX",
        "EA-01-ROLE",
        "EA-01-CROP",
    }
)

# Recorded, ignored for health. EA-01 is geometry, not publish policy.
POLICY_CODES = frozenset(
    {
        "V-LTN-FREEZE",
        "V-P16-12",
        "V-P16-08",
        "V-P16-U01",
        "V-P16-U02",
        "V-P16-U03",
        "V-P16-MAIN-01",
        "V-P16-S03",
        "V-P16-S04",
    }
)

CATEGORY_BY_CODE = {
    "V-P16-01": "overlap",
    "V-P16-02": "gap",
    "V-P16-03": "empty_or_count",
    "V-P16-04": "crop",
    "V-P16-05": "css",
    "V-P16-06": "empty_slot",
    "V-P16-09": "role",
    "V-P16-10": "balance",
    "V-P16-13": "crop",
    "V-P16-14": "bounds",
    "V-P16-S01": "bounds",
    "EA-01-PARSE": "parse",
    "EA-01-SCHEMA": "schema",
    "EA-01-INDEX": "empty_or_count",
    "EA-01-ROLE": "role",
    "EA-01-CROP": "crop",
}


@dataclass
class Issue:
    code: str
    message: str
    level: str
    category: str
    policy: bool = False


@dataclass
class TemplateRow:
    id: str
    path: str
    family: str
    status: str
    health: Health
    slot_count: int
    stage_aspect: str
    issues: list[Issue] = field(default_factory=list)
    policy_notes: list[Issue] = field(default_factory=list)


def is_dist_path(path: Path) -> bool:
    return any(part.lower() == "dist" for part in path.parts)


def iter_source_template_paths(root: Path | None = None) -> list[Path]:
    """Non-recursive ``screen-*.yaml`` / ``page-*.yaml``. Never ``dist/``."""
    base = Path(root) if root is not None else SOURCE_TEMPLATES_DIR
    if is_dist_path(base):
        raise ValueError(f"refusing dist path: {base}")
    files: list[Path] = []
    for path in sorted(base.glob("screen-*.yaml")) + sorted(base.glob("page-*.yaml")):
        if path.name.startswith("_"):
            continue
        if is_dist_path(path):
            continue
        if ".version_history" in path.parts:
            continue
        files.append(path)
    return files


def classify_health(issues: Iterable[Issue]) -> Health:
    geo = [i for i in issues if not i.policy]
    if any(i.level in ("error", "block") for i in geo):
        return "broken"
    if any(i.level == "warn" for i in geo):
        return "suspicious"
    return "healthy"


def _issue(code: str, message: str, *, level: str) -> Issue:
    return Issue(
        code=code,
        message=message,
        level=level,
        category=CATEGORY_BY_CODE.get(code, "other"),
        policy=code in POLICY_CODES,
    )


def _extra_geometry_checks(template: Any) -> list[Issue]:
    extra: list[Issue] = []
    indices = [s.index for s in template.slots]
    if len(indices) != len(set(indices)):
        extra.append(
            _issue("EA-01-INDEX", f"duplicate slot indices {indices}", level="error")
        )
    expected = list(range(len(template.slots)))
    if sorted(indices) != expected:
        extra.append(
            _issue(
                "EA-01-INDEX",
                f"slot indices {indices} are not contiguous 0..{len(template.slots) - 1}",
                level="warn",
            )
        )
    for slot in template.slots:
        role = str(slot.role or "").strip()
        if not role:
            extra.append(
                _issue("EA-01-ROLE", f"slot {slot.index} missing role", level="error")
            )
        elif role not in KNOWN_ROLES:
            extra.append(
                _issue(
                    "EA-01-ROLE",
                    f"slot {slot.index} unknown role {role!r}",
                    level="error",
                )
            )
        c0, c1, r0, r1 = slot.rect
        if c1 < c0 or r1 < r0:
            extra.append(
                _issue(
                    "EA-01-CROP",
                    f"slot {slot.index} rect {slot.rect} has zero/negative span",
                    level="error",
                )
            )
    return extra


def audit_file(path: Path, *, schema_validator: Any | None = None) -> TemplateRow:
    import yaml

    from travelogue.layout_templates.css_gen import template_family
    from travelogue.layout_templates.registry import template_def_from_yaml
    from travelogue.layout_templates.validator import validate_template_def

    rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        issue = _issue("EA-01-PARSE", str(exc), level="error")
        return TemplateRow(
            id=path.stem,
            path=rel,
            family="unknown",
            status="unreadable",
            health="broken",
            slot_count=0,
            stage_aspect="",
            issues=[issue],
        )
    if not isinstance(doc, dict):
        issue = _issue("EA-01-PARSE", "root must be a mapping", level="error")
        return TemplateRow(
            id=path.stem,
            path=rel,
            family="unknown",
            status="unreadable",
            health="broken",
            slot_count=0,
            stage_aspect="",
            issues=[issue],
        )

    issues: list[Issue] = []
    if schema_validator is not None:
        for err in sorted(schema_validator.iter_errors(doc), key=lambda e: list(e.path)):
            loc = ".".join(str(p) for p in err.path) or "(root)"
            issues.append(_issue("EA-01-SCHEMA", f"{loc}: {err.message}", level="error"))

    try:
        template = template_def_from_yaml(doc)
    except Exception as exc:  # noqa: BLE001 — report, do not crash the batch
        issues.append(_issue("EA-01-PARSE", f"model load failed: {exc}", level="error"))
        tid = str(doc.get("id") or path.stem)
        return TemplateRow(
            id=tid,
            path=rel,
            family=template_family(tid),
            status=str(doc.get("status") or "unknown"),
            health=classify_health(issues),
            slot_count=len(doc.get("slots") or []),
            stage_aspect=str((doc.get("stage") or {}).get("aspect") or ""),
            issues=[i for i in issues if not i.policy],
            policy_notes=[],
        )

    report = validate_template_def(template, mode="ci")
    for raw in report.issues:
        issues.append(_issue(raw.code, raw.message, level=raw.level))
    issues.extend(_extra_geometry_checks(template))

    geo = [i for i in issues if i.code in GEOMETRY_CODES or not i.policy]
    geo = [i for i in geo if not i.policy]
    policy = [i for i in issues if i.policy]
    health = classify_health(geo)
    return TemplateRow(
        id=template.id,
        path=rel,
        family=template_family(template.id),
        status=template.status,
        health=health,
        slot_count=len(template.slots),
        stage_aspect=template.stage.aspect,
        issues=geo,
        policy_notes=policy,
    )


def _schema_validator() -> Any:
    import json

    import jsonschema

    from travelogue.layout_templates.registry import schema_path

    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    return jsonschema.Draft202012Validator(schema)


def run_audit(root: Path | None = None) -> dict[str, Any]:
    paths = iter_source_template_paths(root)
    validator = _schema_validator()
    rows = [audit_file(p, schema_validator=validator) for p in paths]
    counts = Counter(r.health for r in rows)
    family_counts: dict[str, Counter[str]] = {"journal": Counter(), "portfolio": Counter()}
    for row in rows:
        family_counts.setdefault(row.family, Counter())[row.health] += 1
    source = Path(root) if root is not None else SOURCE_TEMPLATES_DIR
    try:
        source_dir = source.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        source_dir = source.as_posix()
    return {
        "date": date.today().isoformat(),
        "source_dir": source_dir,
        "excluded": ["dist/", ".version_history/", "_*.yaml"],
        "checked": len(rows),
        "counts": {
            "healthy": counts.get("healthy", 0),
            "suspicious": counts.get("suspicious", 0),
            "broken": counts.get("broken", 0),
        },
        "by_family": {
            name: {
                "healthy": c.get("healthy", 0),
                "suspicious": c.get("suspicious", 0),
                "broken": c.get("broken", 0),
                "total": sum(c.values()),
            }
            for name, c in family_counts.items()
        },
        "templates": [asdict(r) for r in rows],
    }


def _short(text: str, limit: int = 140) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def format_markdown(report: dict[str, Any]) -> str:
    counts = report["counts"]
    lines = [
        "# EA-01 源码模板几何体检",
        "",
        "| 属性 | 内容 |",
        "|------|------|",
        f"| 日期 | {report['date']} |",
        "| 任务 | [收敛任务清单.md](../收敛任务清单.md) `EA-01` |",
        f"| 源目录 | `{report['source_dir']}` |",
        f"| 排除 | {', '.join(f'`{x}`' for x in report['excluded'])} |",
        f"| 检查数 | **{report['checked']}** |",
        "| 三态 | 健康 = 无几何 error/warn；可疑 = 仅几何 warn；破损 = 几何 error/block |",
        "| 不计入三态 | 槽位数量冻结、usage 文档、命名、16:9 main eligibility 等 **政策** 项 |",
        "| 复跑 | `python scripts/ea01_template_geometry_audit.py --write-markdown docs/acceptance-records/ea-01-template-geometry-2026-09-01.md` |",
        "",
        "## 总览",
        "",
        f"- 健康 **{counts['healthy']}**",
        f"- 可疑 **{counts['suspicious']}**",
        f"- 破损 **{counts['broken']}**",
        "",
        "| 族 | 健康 | 可疑 | 破损 | 合计 |",
        "|----|------|------|------|------|",
    ]
    for name, block in report["by_family"].items():
        lines.append(
            f"| {name} | {block['healthy']} | {block['suspicious']} | "
            f"{block['broken']} | {block['total']} |"
        )
    lines += [
        "",
        "## 怎么读这份报告",
        "",
        "1. **破损极少不等于竖版已就绪。** 本检查只看 16:9 源几何能否自洽（空槽、越界、重叠、角色、裁切可行性）。`stage.variants` 仍只声明 aspect，竖版槽位几何尚未存在。",
        "2. **唯一破损 `page-10-grid-port` 是 schema 天花板，不是槽位重叠。** `layout_template.schema.json` 把 `photoCount` / `mix` 上限写成 9、`slots.index` 上限写成 8（游记时代的 9 槽合同）。10 槽页的 YAML 轨道可能仍合法，但合同未放行。`CV-01` 不要拿它当健康基线；它倒适合当难迁移对照。",
        "3. **`screen-*` 可疑偏多，主因是 16:9 舞台上的竖槽必然偏离 AR 阶梯。** 例如三列竖图槽 displayAspect≈0.889，不在 `{2/3, 3/4, 1, 4/3, 3/2, 16/9}` 上。这是舞台比例与角色的结构性张力，不是 YAML 写坏。",
        "4. **`square` 槽被现行校验器按横图推荐区间 `[1.25, 2.2]` 衡量**，所以 1:1 英雄页会进可疑。正方形槽几何成立；这是角色分组问题，不是空槽或重叠。",
        "5. **政策备注（文末）不影响三态**，绝大多数是 `usage.siblings` 未互指。",
        "",
        "## `CV-01` 选样提示（不代替拍板）",
        "",
        "| 角色 | 建议（均须为健康态） | 理由 |",
        "|------|----------------------|------|",
        "| 常用单图 | `page-1-hero-land-right` | 健康、1 槽、作品集高频 |",
        "| 常用混合 | `page-2-1p1l` | 健康、横竖各一 |",
        "| 难迁移 | `page-9-grid-land-wide` | 健康、宽幅九宫，竖屏几乎必然重编 |",
        "| `screen-*` 对照 | `screen-portrait-2-gallery` | 健康、有声明留白 |",
        "",
        "不要从可疑集合里选试点：那会把「AR 阶梯预警」和「竖版迁不了」混在一起。",
        "",
        "## 破损",
        "",
    ]
    broken = [t for t in report["templates"] if t["health"] == "broken"]
    if not broken:
        lines.append("无。")
    else:
        lines += [
            "| id | 族 | status | 槽数 | 原因 |",
            "|----|----|--------|------|------|",
        ]
        for row in broken:
            reasons = "; ".join(
                f"{i['code']} {_short(i['message'])}"
                for i in row["issues"]
                if i["level"] in ("error", "block")
            )
            lines.append(
                f"| `{row['id']}` | {row['family']} | {row['status']} | "
                f"{row['slot_count']} | {reasons} |"
            )
    lines += [
        "",
        "## 可疑",
        "",
    ]
    suspicious = [t for t in report["templates"] if t["health"] == "suspicious"]
    if not suspicious:
        lines.append("无。")
    else:
        lines += [
            "| id | 族 | status | 槽数 | 警告 |",
            "|----|----|--------|------|------|",
        ]
        for row in suspicious:
            reasons = "; ".join(
                f"{i['code']} {_short(i['message'], 100)}" for i in row["issues"]
            )
            lines.append(
                f"| `{row['id']}` | {row['family']} | {row['status']} | "
                f"{row['slot_count']} | {reasons} |"
            )
    lines += [
        "",
        "## 健康（可供 `CV-01` 选样）",
        "",
        "下列全部为 16:9 基线几何健康。`CV-01` 仍须从中挑 1 个预判难迁移件（宽幅/多列/密排）。",
        "",
    ]
    healthy = [t for t in report["templates"] if t["health"] == "healthy"]
    page_h = [t for t in healthy if t["family"] == "portfolio"]
    screen_h = [t for t in healthy if t["family"] == "journal"]
    lines.append(f"`page-*` 健康 {len(page_h)} 个：")
    lines.append("")
    lines.append(", ".join(f"`{t['id']}`" for t in page_h) or "（无）")
    lines.append("")
    lines.append(f"`screen-*` 健康 {len(screen_h)} 个：")
    lines.append("")
    lines.append(", ".join(f"`{t['id']}`" for t in screen_h) or "（无）")
    lines += [
        "",
        "## 政策备注（不影响三态）",
        "",
    ]
    with_policy = [t for t in report["templates"] if t["policy_notes"]]
    if not with_policy:
        lines.append("无。")
    else:
        lines += [
            "| id | 备注 |",
            "|----|------|",
        ]
        for row in with_policy:
            notes = "; ".join(
                f"{i['code']} {_short(i['message'], 80)}" for i in row["policy_notes"]
            )
            lines.append(f"| `{row['id']}` | {notes} |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EA-01 source template geometry audit")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-markdown", type=Path, default=None)
    parser.add_argument(
        "--templates",
        type=Path,
        default=None,
        help="Override source dir (must not contain dist/)",
    )
    args = parser.parse_args(argv)
    report = run_audit(args.templates)
    if args.write_markdown:
        out = args.write_markdown
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(format_markdown(report), encoding="utf-8")
        print(f"wrote {out}")
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        c = report["counts"]
        print(
            f"EA-01 geometry audit: checked={report['checked']} "
            f"healthy={c['healthy']} suspicious={c['suspicious']} broken={c['broken']}"
        )
        for row in report["templates"]:
            if row["health"] == "healthy":
                continue
            print(f"  {row['health'].upper()} {row['id']}")
            for issue in row["issues"]:
                print(f"    [{issue['level']}] {issue['code']} {issue['message']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
