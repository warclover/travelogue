"""Check LTE template slot counts vs usage text consistency."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = ROOT / "travelogue" / "layout_templates" / "templates"

# Numbers in summary that claim photo/window size (图/张/槽/竖/横 as quantity)
CLAIM_RE = re.compile(
    r"(?:(\d+)\s*(?:张|图|槽|竖|横|图屏|竖图|横图))"
    r"|(?:(\d+)\s*[Pp]\s*\+\s*(\d+)\s*[Ll])"
    r"|(?:(\d+)×(\d+))"
)


def load_templates() -> list[tuple[Path, dict]]:
    rows: list[tuple[Path, dict]] = []
    for path in sorted(TEMPLATES_DIR.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(doc, dict):
            rows.append((path, doc))
    return rows


def slot_info(doc: dict) -> tuple[int, int, int, int, int]:
    mix = doc.get("mix") or {}
    p = int(mix.get("portrait") or 0)
    l = int(mix.get("landscape") or 0)
    n = len(doc.get("slots") or [])
    pc = doc.get("photoCount") or {}
    return n, p, l, int(pc["min"]), int(pc["max"])


def grid_product(text: str) -> int | None:
    m = re.search(r"(\d+)×(\d+)", text)
    if m:
        return int(m.group(1)) * int(m.group(2))
    return None


def check_summary_counts(tid: str, n: int, p: int, l: int, summary: str) -> list[str]:
    issues: list[str] = []
    # Explicit "N 图/张/槽" in summary must match n (when N is 1-9)
    for m in CLAIM_RE.finditer(summary):
        if m.group(1):
            claimed = int(m.group(1))
            if 1 <= claimed <= 9 and claimed != n:
                issues.append(
                    f"summary 写 {claimed} 图/张/槽，实际 slots={n} photoCount={n}"
                )
        elif m.group(2) and m.group(3):
            cp, cl = int(m.group(2)), int(m.group(3))
            if (p or l) and (cp != p or cl != l):
                issues.append(f"summary 写 {cp}P+{cl}L，实际 mix={p}P+{l}L")
        elif m.group(4) and m.group(5):
            grid_n = int(m.group(4)) * int(m.group(5))
            if grid_n != n:
                issues.append(f"summary 写 {m.group(4)}×{m.group(5)}={grid_n} 格，实际 slots={n}")

    # Common shorthand: "六图" "九竖" etc — skip, CLAIM_RE handles digits

    # Special: id says 5 but photoCount 6
    if "mosaic-5-main-hero-plus-4" in tid and n == 6:
        if "6" not in summary and "5-main" in summary and "6 图" not in summary:
            if "6" not in summary.split("id")[0]:
                pass  # usage already warns about id vs photoCount

    return issues


def main() -> int:
    templates = load_templates()
    missing: list[str] = []
    internal: list[tuple[str, str]] = []
    mismatches: list[tuple[str, list[str]]] = []

    print("templateId                                    slots  mix     usage  photoCount")
    print("-" * 78)

    for path, doc in templates:
        tid = str(doc["id"])
        n, p, l, pc_min, pc_max = slot_info(doc)
        mix = f"{p}P+{l}L" if (p or l) else "—"
        usage = doc.get("usage")
        has_u = "Y" if isinstance(usage, dict) and usage.get("summary") else "N"
        print(f"{tid:<45} {n:>5}  {mix:>6}  {has_u:>5}  {pc_min}-{pc_max}")

        if pc_min != n or pc_max != n:
            internal.append((tid, f"photoCount {pc_min}-{pc_max} != len(slots)={n}"))

        if not isinstance(usage, dict) or not str(usage.get("summary") or "").strip():
            missing.append(tid)
            continue

        issues = check_summary_counts(tid, n, p, l, str(usage.get("summary") or ""))
        if issues:
            mismatches.append((tid, issues))

    print()
    print(f"模板总数: {len(templates)}")
    print(f"有 usage.summary: {len(templates) - len(missing)}")
    print(f"缺 usage: {len(missing)}")
    if missing:
        for t in missing:
            print(f"  MISSING: {t}")

    print()
    print(f"YAML 内部不一致 (photoCount vs slots): {len(internal)}")
    for tid, msg in internal:
        print(f"  {tid}: {msg}")

    print()
    print(f"summary 与槽位数量不一致: {len(mismatches)}")
    if mismatches:
        for tid, issues in mismatches:
            print(f"  {tid}:")
            for i in issues:
                print(f"    - {i}")
    else:
        print("  (无)")

    # Sibling id validity
    known = {doc["id"] for _, doc in templates}
    broken_siblings: list[tuple[str, str]] = []
    for _, doc in templates:
        usage = doc.get("usage") or {}
        for s in usage.get("siblings") or []:
            if isinstance(s, dict):
                sid = str(s.get("id") or "")
                if sid and sid not in known:
                    broken_siblings.append((doc["id"], sid))
    print()
    print(f"siblings 断链: {len(broken_siblings)}")
    for tid, sid in broken_siblings:
        print(f"  {tid} -> {sid!r}")

    ok = not missing and not internal and not mismatches and not broken_siblings
    print()
    print("结论:", "一致 ✓" if ok else "存在不一致，见上")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
