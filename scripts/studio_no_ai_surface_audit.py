#!/usr/bin/env python3
"""NAS · 默认可达面禁词静态审计（FE-NAS-14 / PRD 附录 C）。

用法:
  python scripts/studio_no_ai_surface_audit.py --wave w1
  python scripts/studio_no_ai_surface_audit.py --wave w2
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUDIO = ROOT / "templates" / "studio"

# 附录 C.2（默认可达面核心禁词；dark 包 / nas-allow 另分 job）
BANNED = [
    "AI 文案",
    "写作引擎",
    "配置写作引擎",
    "管理写作引擎",
    "升级 AI",
    "杂志感文案",
    "生成杂志感",
    "按新感觉重写",
    "按新感觉重写这段",
    "重新生成文案",
    "去配置写作引擎",
    "继续生成本机画册",
    "继续生成本机游记",
    "本机文案",
    "以后再升级",
    "更好的文案",
]

# 白名单邻近例外：版式「杂志感」且同行无 AI/文案/升级 — 简化：整行含「杂志感文案」才禁

W1_GLOBS = [
    "studio-home-v2.html",
    "js/ai-surface.js",
    "js/capability-card.js",
    "js/home-stub-banner.js",
    "js/help-onboarding.js",
    "js/errors.js",
    "js/constants.js",
    "homepage-v2/bootstrap.js",
    "homepage-v2/settings-panel.js",
    "homepage-v2/first-success.js",
    "homepage-v2/import-failed.js",
]

W2_EXTRA = [
    "preview-toolbar-v3-sheet.js",
    "preview-toolbar-v3-task-dock.js",
    "preview-toolbar/core.js",
    "preview-toolbar/init-v3.js",
    "preview-toolbar/drawers.js",
    "preview-toolbar/dock.js",
    "homepage-v2/import-run.js",
    "homepage-v2/wait-tips-copy.js",
    "js/llm-settings.js",  # 文件头 nas-allow+dark-only 则整文件跳过
]

# dark-only 整文件（文件头含 nas-allow 则整文件跳过）
FILE_ALLOW_MARK = "nas-allow"


def _strip_nas_allow_blocks(text: str) -> str:
    """移除 /* nas-allow ... */ 与 <!-- nas-allow ... --> 以及 data-nas-allow 元素粗略块。"""
    text = re.sub(r"/\*\s*nas-allow[\s\S]*?\*/", "", text, flags=re.I)
    text = re.sub(r"<!--\s*nas-allow[\s\S]*?-->", "", text, flags=re.I)
    # 带 data-nas-allow 的 details/div：去掉整段（非完美 HTML 解析）
    text = re.sub(
        r"<(details|div)[^>]*data-nas-allow[^>]*>[\s\S]*?</\1>",
        "",
        text,
        flags=re.I,
    )
    return text


def _strip_comments(text: str, path: Path) -> str:
    """默认可达面 = 用户可读串；注释/文档块不计入禁词命中。"""
    suffix = path.suffix.lower()
    if suffix in {".js", ".css"}:
        text = re.sub(r"/\*[\s\S]*?\*/", "", text)
        text = re.sub(r"(?m)//.*?$", "", text)
    if suffix in {".html", ".htm"}:
        text = re.sub(r"<!--[\s\S]*?-->", "", text)
    return text


def _iter_files(wave: str) -> list[Path]:
    rels = list(W1_GLOBS)
    if wave == "w2":
        rels.extend(W2_EXTRA)
    out: list[Path] = []
    for rel in rels:
        p = STUDIO / rel
        if p.is_file():
            out.append(p)
    return out


def audit(wave: str) -> list[str]:
    hits: list[str] = []
    for path in _iter_files(wave):
        raw = path.read_text(encoding="utf-8")
        head = "\n".join(raw.splitlines()[:20]).lower()
        if FILE_ALLOW_MARK in head and "dark-only" in head:
            continue
        body = _strip_comments(_strip_nas_allow_blocks(raw), path)
        for i, line in enumerate(body.splitlines(), 1):
            if "nas-allow" in line.lower():
                continue
            for term in BANNED:
                if term in line:
                    rel = path.relative_to(ROOT).as_posix()
                    hits.append(f"{rel}:{i}: {term!r} :: {line.strip()[:120]}")
                    break
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wave", choices=("w1", "w2"), default="w1")
    args = ap.parse_args()
    hits = audit(args.wave)
    if hits:
        print(f"NAS audit FAIL ({args.wave}): {len(hits)} hit(s)", file=sys.stderr)
        for h in hits:
            print(h, file=sys.stderr)
        return 1
    print(f"NAS audit OK ({args.wave})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
