#!/usr/bin/env python3
"""Studio UI Detail · static audit for Studio overlay CSS drift.

Scans templates/studio CSS for:
  - conflicting property values on shared selectors (D-UID-01)
  - font-size / color histograms (D-UID-07)
  - wave2: Settings vs Preview sheet family mismatch (D-UID-08)

Usage:
  python scripts/studio_ui_detail_static_audit.py
  python scripts/studio_ui_detail_static_audit.py --wave modal
  python scripts/studio_ui_detail_static_audit.py --wave settings-sheet
  python scripts/studio_ui_detail_static_audit.py --wave preview-chrome
  python scripts/studio_ui_detail_static_audit.py --wave wait-tips
  python scripts/studio_ui_detail_static_audit.py --wave cap-narrow-lightbox
  python scripts/studio_ui_detail_static_audit.py --wave bench-wizard-carousel
  python scripts/studio_ui_detail_static_audit.py --wave home-tokens
  python scripts/studio_ui_detail_static_audit.py --wave shelf-dev-loading
  python scripts/studio_ui_detail_static_audit.py --wave overlay-toast
  python scripts/studio_ui_detail_static_audit.py --wave wizard-help-closeout
  python scripts/studio_ui_detail_static_audit.py --wave all
  python scripts/studio_ui_detail_static_audit.py --json out/ui-detail-static.json
  python scripts/studio_ui_detail_static_audit.py --strict   # exit 1 if P0 or P1 findings
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from travelogue.paths import ROOT

STUDIO = ROOT / "templates" / "studio"

# Wave1 · modal family (inventory S-MODAL … S-TOAST)
PILOT_CSS = [
    STUDIO / "studio-modal.css",
    STUDIO / "preview-toolbar" / "modal-chrome.css",
    STUDIO / "homepage-v2" / "css" / "overlays.css",
    STUDIO / "homepage-v2" / "css" / "import-wizard.css",
    STUDIO / "help-drawer.css",
]

# Wave2 · Settings popover + Preview sheet
WAVE2_CSS = [
    STUDIO / "homepage-v2" / "css" / "bento.css",  # hosts .v2-settings-*
    STUDIO / "preview-toolbar" / "sheet.css",
]

# Wave3 · remaining preview chrome + help drawer
WAVE3_CSS = [
    STUDIO / "preview-toolbar" / "tokens.css",
    STUDIO / "preview-toolbar" / "shell.css",
    STUDIO / "preview-toolbar" / "longshot.css",
    STUDIO / "preview-toolbar" / "drawers.css",
    STUDIO / "preview-toolbar" / "legacy-bar.css",
    STUDIO / "preview-toolbar" / "cohort.css",
    STUDIO / "preview-toolbar" / "task-dock.css",
    STUDIO / "preview-toolbar" / "v3-bar.css",
    STUDIO / "help-drawer.css",
]

# Wave4 · Importing wait-tips tip-tone (dark glass · gold family only)
WAVE4_CSS = [
    STUDIO / "homepage-v2" / "css" / "overlays.css",
]

# Wave5 · Capability card + narrow-gate + lightbox
WAVE5_CSS = [
    STUDIO / "studio-modal.css",  # panel token source of truth
    STUDIO / "capability-card.css",
    STUDIO / "preview-toolbar" / "shell.css",  # hosts .preview-narrow-gate
    STUDIO / "homepage-v2" / "css" / "chrome.css",  # lightbox
]

# Wave6 · Bench light panels + wizard empty accent + carousel dots
WAVE6_CSS = [
    STUDIO / "homepage-v2" / "css" / "bench.css",
    STUDIO / "homepage-v2" / "css" / "import-wizard.css",
    STUDIO / "homepage-v2" / "css" / "carousel.css",
    STUDIO / "homepage-v2" / "css" / "theme-classic.css",
]

# Wave7 · Homepage token default + theme-aware hardcodes
WAVE7_CSS = [
    STUDIO / "homepage-v2" / "css" / "tokens.css",
    STUDIO / "homepage-v2" / "css" / "bench.css",
    STUDIO / "homepage-v2" / "css" / "bento.css",
    STUDIO / "homepage-v2" / "css" / "carousel.css",
    STUDIO / "homepage-v2" / "css" / "phone.css",
]

# Wave8 · Shelf menu + Dev panel + Loading shimmer
WAVE8_CSS = [
    STUDIO / "homepage-v2" / "css" / "shelf.css",
    STUDIO / "homepage-v2" / "css" / "dev-panel.css",
    STUDIO / "homepage-v2" / "css" / "bento.css",  # .v2-loading
    STUDIO / "homepage-v2" / "css" / "bench.css",  # ready-badge
]

# Wave9 · Unsupported + FirstSuccess/Failure + Toast family
WAVE9_CSS = [
    STUDIO / "homepage-v2" / "css" / "chrome.css",
    STUDIO / "homepage-v2" / "css" / "overlays.css",
    STUDIO / "studio-modal.css",
    STUDIO / "preview-toolbar" / "drawers.css",
]

# Wave10 · Wizard ladder + Help drawer + dock/longshot closeout
WAVE10_CSS = [
    STUDIO / "homepage-v2" / "css" / "import-wizard.css",
    STUDIO / "help-drawer.css",
    STUDIO / "preview-toolbar" / "task-dock.css",
    STUDIO / "preview-toolbar" / "longshot.css",
]

WAVES = {
    "modal": PILOT_CSS,
    "settings-sheet": WAVE2_CSS,
    "preview-chrome": WAVE3_CSS,
    "wait-tips": WAVE4_CSS,
    "cap-narrow-lightbox": WAVE5_CSS,
    "bench-wizard-carousel": WAVE6_CSS,
    "home-tokens": WAVE7_CSS,
    "shelf-dev-loading": WAVE8_CSS,
    "overlay-toast": WAVE9_CSS,
    "wizard-help-closeout": WAVE10_CSS,
    # overlays 已在 modal 波；dict.fromkeys 去重路径
    "all": list(
        dict.fromkeys(
            PILOT_CSS
            + WAVE2_CSS
            + WAVE3_CSS
            + WAVE4_CSS
            + WAVE5_CSS
            + WAVE6_CSS
            + WAVE7_CSS
            + WAVE8_CSS
            + WAVE9_CSS
            + WAVE10_CSS
        )
    ),
}

CONFLICT_SELECTORS = [
    ".studio__modal-backdrop",
    ".studio__modal",
    ".studio__modal h3",
    ".studio__modal p",
    ".studio__btn",
    ".studio__btn--ghost",
    ".studio__btn--primary",
    ".studio__btn--sm",
]

COMPARE_PROPS = {
    "width",
    "padding",
    "border-radius",
    "background",
    "background-color",
    "color",
    "font-size",
    "line-height",
    "font-weight",
    "min-height",
    "box-shadow",
    "z-index",
}

_FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;}+]+)", re.I)
_COLOR_RE = re.compile(
    r"(?<!background-)(?<!border-)(?<!outline-)(?<!text-decoration-)"
    r"(?<!caret-)(?<!column-rule-)(?<!text-emphasis-)"
    r"color\s*:\s*([^;}+]+)",
    re.I,
)
_RULE_RE = re.compile(
    r"([^{}@][^{]*)\{([^{}]*)\}",
    re.M,
)


@dataclass
class Finding:
    id: str
    severity: str
    selector: str
    detail: str
    files: list[str]


def _strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _norm_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().rstrip(";").lower())


def _parse_rules(css: str) -> list[tuple[str, dict[str, str]]]:
    text = _strip_comments(css)
    out: list[tuple[str, dict[str, str]]] = []
    for m in _RULE_RE.finditer(text):
        selectors = [s.strip() for s in m.group(1).split(",") if s.strip()]
        body = m.group(2)
        props: dict[str, str] = {}
        for part in body.split(";"):
            if ":" not in part:
                continue
            key, val = part.split(":", 1)
            key = key.strip().lower()
            if key in COMPARE_PROPS:
                props[key] = _norm_value(val)
        if not props:
            continue
        for sel in selectors:
            out.append((sel, props))
    return out


def find_selector_conflicts(paths: list[Path]) -> list[Finding]:
    # selector -> prop -> [(file, value)]
    store: dict[str, dict[str, list[tuple[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        for sel, props in _parse_rules(path.read_text(encoding="utf-8")):
            if sel not in CONFLICT_SELECTORS:
                continue
            for prop, val in props.items():
                store[sel][prop].append((rel, val))

    findings: list[Finding] = []
    for sel, prop_map in sorted(store.items()):
        for prop, pairs in sorted(prop_map.items()):
            uniq = sorted({v for _, v in pairs})
            if len(uniq) <= 1:
                continue
            files = sorted({f for f, _ in pairs})
            detail_lines = [f"{f}: {prop}={v}" for f, v in pairs]
            findings.append(
                Finding(
                    id="D-UID-01",
                    severity="P0",
                    selector=sel,
                    detail=f"冲突属性 `{prop}` → " + " | ".join(detail_lines),
                    files=files,
                )
            )
    return findings


def histogram_for_files(paths: list[Path]) -> dict[str, object]:
    font_sizes: Counter[str] = Counter()
    colors: Counter[str] = Counter()
    per_file: dict[str, dict[str, object]] = {}
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = _strip_comments(path.read_text(encoding="utf-8"))
        fs = [_norm_value(m.group(1)) for m in _FONT_SIZE_RE.finditer(text)]
        cols: list[str] = []
        for m in _COLOR_RE.finditer(text):
            raw = _norm_value(m.group(1))
            if raw.startswith("var(") or raw in {"inherit", "transparent", "currentcolor"}:
                continue
            cols.append(raw)
        font_sizes.update(fs)
        colors.update(cols)
        per_file[rel] = {
            "fontSizeUnique": sorted(set(fs)),
            "fontSizeCount": len(set(fs)),
            "colorUnique": sorted(set(cols)),
            "colorCount": len(set(cols)),
        }
    return {
        "fontSizeHistogram": dict(font_sizes.most_common()),
        "colorHistogram": dict(colors.most_common()),
        "perFile": per_file,
    }


def build_histogram_findings(hist: dict[str, object]) -> list[Finding]:
    findings: list[Finding] = []
    per_file = hist.get("perFile") or {}
    for rel, info in sorted(per_file.items()):
        fs_count = int(info.get("fontSizeCount") or 0)
        color_count = int(info.get("colorCount") or 0)
        # Overlay / wizard / sheet files with very wide ladders → P2 drift signal
        if fs_count >= 8:
            findings.append(
                Finding(
                    id="D-UID-07",
                    severity="P2",
                    selector=rel,
                    detail=f"字号离散度偏高：{fs_count} 种 → {info.get('fontSizeUnique')}",
                    files=[rel],
                )
            )
        if color_count >= 10:
            findings.append(
                Finding(
                    id="D-UID-07",
                    severity="P2",
                    selector=rel,
                    detail=f"color 声明离散度偏高：{color_count} 种",
                    files=[rel],
                )
            )
    return findings


def _rules_matching(path: Path, needle: str) -> list[tuple[str, dict[str, str]]]:
    if not path.is_file():
        return []
    return [
        (sel, props)
        for sel, props in _parse_rules(path.read_text(encoding="utf-8"))
        if needle in sel
    ]


def find_settings_sheet_family_drift() -> list[Finding]:
    """D-UID-08 · Settings claims to mirror sheet zones but uses a different ink family."""
    bento = STUDIO / "homepage-v2" / "css" / "bento.css"
    sheet = STUDIO / "preview-toolbar" / "sheet.css"
    findings: list[Finding] = []
    set_rules = _rules_matching(bento, "v2-settings")
    sheet_rules = _rules_matching(sheet, "preview-sheet")
    set_fonts = sorted(
        {props["font-size"] for _, props in set_rules if "font-size" in props}
    )
    sheet_fonts = sorted(
        {props["font-size"] for _, props in sheet_rules if "font-size" in props}
    )
    set_colors = sorted(
        {
            props["color"]
            for _, props in set_rules
            if "color" in props and not props["color"].startswith("var(")
        }
    )
    sheet_colors = sorted(
        {
            props["color"]
            for _, props in sheet_rules
            if "color" in props and not props["color"].startswith("var(")
        }
    )
    if len(set_fonts) >= 6:
        findings.append(
            Finding(
                id="D-UID-07",
                severity="P2",
                selector=".v2-settings-*",
                detail=f"Settings 选择器字号 {len(set_fonts)} 种 → {set_fonts}",
                files=["templates/studio/homepage-v2/css/bento.css"],
            )
        )
    if len(sheet_fonts) >= 8:
        findings.append(
            Finding(
                id="D-UID-07",
                severity="P2",
                selector=".preview-sheet*",
                detail=f"Preview sheet 选择器字号 {len(sheet_fonts)} 种 → {sheet_fonts}",
                files=["templates/studio/preview-toolbar/sheet.css"],
            )
        )
    # Family mismatch: legacy slate settings vs blue-gray sheet hardcodes
    set_has_slate = any("0f172a" in c or "475569" in c or "455a64" in c for c in set_colors)
    sheet_has_bluegray = any(
        "546e7a" in c or "607d8b" in c or "78909c" in c for c in sheet_colors
    )
    set_uses_panel = any(
        "studio-panel" in props.get(k, "")
        for _, props in set_rules
        for k in ("color", "font-size", "background", "border")
    ) or any("--v2-set-ink: var(--studio-panel" in str(props) for _, props in set_rules)
    # also detect token wiring on the popover root via raw text
    bento_text = bento.read_text(encoding="utf-8") if bento.is_file() else ""
    sheet_text = sheet.read_text(encoding="utf-8") if sheet.is_file() else ""
    set_uses_panel = "--studio-panel-ink" in bento_text or "studio-panel-ink" in bento_text
    # Sheet may nest via --preview-* then --studio-panel-* (Wave3)
    sheet_uses_panel = "studio-panel-ink" in sheet_text
    if set_has_slate and sheet_has_bluegray:
        findings.append(
            Finding(
                id="D-UID-08",
                severity="P1",
                selector="settings-vs-sheet",
                detail=(
                    "Settings（slate）与 Preview sheet（蓝灰）色族不一致；"
                    f" settingsColors={len(set_colors)} sheetColors={len(sheet_colors)}"
                ),
                files=[
                    "templates/studio/homepage-v2/css/bento.css",
                    "templates/studio/preview-toolbar/sheet.css",
                ],
            )
        )
    elif not (set_uses_panel and sheet_uses_panel):
        findings.append(
            Finding(
                id="D-UID-08",
                severity="P1",
                selector="settings-vs-sheet",
                detail=(
                    "Settings/Sheet 未同时挂到 studio-panel-* token："
                    f" settingsPanel={set_uses_panel} sheetPanel={sheet_uses_panel}"
                ),
                files=[
                    "templates/studio/homepage-v2/css/bento.css",
                    "templates/studio/preview-toolbar/sheet.css",
                ],
            )
        )
    # Title size mismatch signal (normalize CSS var fallbacks)
    def _norm_title(raw: str | None) -> str | None:
        if not raw:
            return None
        if "15px" in raw:
            return "15px"
        if "13px" in raw:
            return "13px"
        return raw

    set_title = _norm_title(
        next((props.get("font-size") for sel, props in set_rules if sel.endswith("__title")), None)
    )
    sheet_title = _norm_title(
        next(
            (
                props.get("font-size")
                for sel, props in sheet_rules
                if sel.rstrip().endswith("preview-sheet__title")
            ),
            None,
        )
    )
    if set_title and sheet_title and set_title != sheet_title:
        findings.append(
            Finding(
                id="D-UID-08",
                severity="P1",
                selector="title-font-size",
                detail=f"面板标题字号 Settings={set_title} vs Sheet={sheet_title}",
                files=[
                    "templates/studio/homepage-v2/css/bento.css",
                    "templates/studio/preview-toolbar/sheet.css",
                ],
            )
        )

    # Sheet mint / orange / forest tip leftovers（原 D-UID-09 整文件豁免 sheet）
    if sheet.is_file():
        sheet_body = _strip_comments(sheet.read_text(encoding="utf-8"))
        stripped = re.sub(r"var\([^)]*\)", "", sheet_body).lower()
        banned_sheet = (
            "#e8f5ef",
            "#ffb74d",
            "#f5fbf8",
            "rgba(26, 47, 40",
            "rgba(47, 107, 85",
        )
        found = [b for b in banned_sheet if b in stripped]
        if found:
            findings.append(
                Finding(
                    id="D-UID-08",
                    severity="P1",
                    selector=".preview-sheet*",
                    detail=(
                        f"Sheet 仍含薄荷/橙/森林硬编码 {found} "
                        f"（激活态应用 accent color-mix；tip 用 cream/gold）"
                    ),
                    files=["templates/studio/preview-toolbar/sheet.css"],
                )
            )
    return findings


def find_preview_chrome_bare_hex(paths: list[Path]) -> list[Finding]:
    """D-UID-09 · bare legacy hex outside var() in preview chrome / help."""
    banned = ("#1a2f28", "#546e7a", "#607d8b", "#0f172a", "#475569")
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        # Token source + inventory gates may keep literal accent-strong
        if path.name in ("sheet.css", "tokens.css", "studio-modal.css"):
            continue
        text = _strip_comments(path.read_text(encoding="utf-8"))
        stripped = re.sub(r"var\([^)]*\)", "", text)
        found = [h for h in banned if h in stripped.lower()]
        if found:
            findings.append(
                Finding(
                    id="D-UID-09",
                    severity="P1",
                    selector=rel,
                    detail=f"仍含裸十六进制文案/UI 色 {found}（应改用 --preview-* / --studio-panel-*）",
                    files=[rel],
                )
            )
    return findings


def find_wait_tips_rainbow_tones(paths: list[Path]) -> list[Finding]:
    """D-UID-10 · wait-tips / import panel must not stack cyan/green/blue/orange tip tones."""
    # Legacy tip-tone + import source cyan (case-insensitive match on stripped CSS)
    banned = (
        "#90e0ef",
        "#9ee7f2",
        "#90caf9",
        "#a5d6a7",
        "#ffcc80",
        "rgba(144, 224, 239",
        "rgba(129, 199, 132",
        "rgba(100, 181, 246",
        "rgba(255, 183, 77",
    )
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = _strip_comments(path.read_text(encoding="utf-8")).lower()
        # Only gate wait-tips / import-panel blocks — skip files without those markers
        chunks: list[str] = []
        for marker in (".v2-wait-tips", ".v2-import-panel"):
            idx = 0
            while True:
                start = text.find(marker, idx)
                if start < 0:
                    break
                end = min(len(text), start + 2400)
                chunks.append(text[start:end])
                idx = start + len(marker)
        if not chunks:
            continue
        hay = "\n".join(chunks)
        found = [b for b in banned if b.lower() in hay]
        if found:
            findings.append(
                Finding(
                    id="D-UID-10",
                    severity="P1",
                    selector=".v2-wait-tips__label / .v2-import-panel",
                    detail=(
                        f"仍含彩虹 tip-tone / cyan source {found} "
                        f"（应收敛到 --wt-gold / cream / white）"
                    ),
                    files=[rel],
                )
            )
    return findings


def find_cap_narrow_lightbox_drift(paths: list[Path]) -> list[Finding]:
    """D-UID-11 · capability / narrow-gate / lightbox must use panel + cream, not forest dual palette."""
    findings: list[Finding] = []
    modal = STUDIO / "studio-modal.css"
    if modal.is_file():
        root = _strip_comments(modal.read_text(encoding="utf-8"))
        if "--studio-panel-ink:" not in root:
            findings.append(
                Finding(
                    id="D-UID-11",
                    severity="P0",
                    selector=":root",
                    detail="studio-modal.css 缺少 --studio-panel-ink 定义（Wave2 token 回潮）",
                    files=["templates/studio/studio-modal.css"],
                )
            )

    cap = STUDIO / "capability-card.css"
    if cap.is_file():
        text = _strip_comments(cap.read_text(encoding="utf-8")).lower()
        banned_cap = ("#2f6b55", "#1a2420", "#4a5c55", "#f7f5f0", "#c5d0ca")
        found = [h for h in banned_cap if h in text]
        if found:
            findings.append(
                Finding(
                    id="D-UID-11",
                    severity="P1",
                    selector=".studio-capability-card",
                    detail=f"能力卡仍含旧森林色 {found}（应挂 --studio-panel-*）",
                    files=["templates/studio/capability-card.css"],
                )
            )
        if "font-size:17px" in text.replace(" ", "") or "font-size: 17px" in text:
            findings.append(
                Finding(
                    id="D-UID-11",
                    severity="P1",
                    selector=".studio-capability-card__title",
                    detail="能力卡标题仍为 17px（应对齐 --studio-panel-title-size 15px）",
                    files=["templates/studio/capability-card.css"],
                )
            )

    cap_js = STUDIO / "js" / "capability-card.js"
    if cap_js.is_file():
        js = cap_js.read_text(encoding="utf-8")
        if "studio-capability-card-style" in js or "#2f6b55" in js:
            findings.append(
                Finding(
                    id="D-UID-11",
                    severity="P1",
                    selector="capability-card.js",
                    detail="能力卡仍内联注入样式/旧 accent（应使用 capability-card.css）",
                    files=["templates/studio/js/capability-card.js"],
                )
            )

    for path in paths:
        if path.name != "shell.css":
            continue
        text = _strip_comments(path.read_text(encoding="utf-8"))
        # Only inspect narrow-gate block
        start = text.find(".preview-narrow-gate")
        if start < 0:
            continue
        chunk = text[start : start + 2200]
        banned_ng = ("#eef6f1", "#f5fbf8", "1.35rem", "0.95rem")
        found = [b for b in banned_ng if b in chunk]
        if found:
            findings.append(
                Finding(
                    id="D-UID-11",
                    severity="P1",
                    selector=".preview-narrow-gate",
                    detail=f"窄屏门面仍含旧薄荷色/rem 字阶 {found}",
                    files=["templates/studio/preview-toolbar/shell.css"],
                )
            )

    for path in paths:
        if path.name != "chrome.css":
            continue
        text = _strip_comments(path.read_text(encoding="utf-8")).lower()
        start = text.find(".v2-lightbox")
        if start < 0:
            continue
        chunk = text[start : start + 1800]
        if "#232b25" in chunk or "#161b17" in chunk:
            findings.append(
                Finding(
                    id="D-UID-11",
                    severity="P1",
                    selector=".v2-lightbox__page-ph",
                    detail="lightbox 占位仍用冷绿渐变（应对齐暖褐 #23201a / #161411）",
                    files=["templates/studio/homepage-v2/css/chrome.css"],
                )
            )
    return findings


def find_bench_wizard_carousel_drift(paths: list[Path]) -> list[Finding]:
    """D-UID-12 · bench light panels / wizard empty / carousel dots leave slate+cyan."""
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = _strip_comments(path.read_text(encoding="utf-8"))
        lower = text.lower()

        if path.name == "bench.css":
            for marker, ban, label in (
                (
                    ".v2-advanced-popover",
                    ("#0f172a", "#475569", "#94a3b8", "#0077b6", "#f1f5f9"),
                    "高级选项浅色面板",
                ),
                (
                    ".v2-preview-combobox__popover",
                    ("#0f172a", "#475569", "#94a3b8", "#0077b6", "#f8fafc"),
                    "预览 combobox 浅色面板",
                ),
            ):
                start = lower.find(marker)
                if start < 0:
                    continue
                chunk = lower[start : start + 2800]
                found = [b for b in ban if b in chunk]
                if found:
                    findings.append(
                        Finding(
                            id="D-UID-12",
                            severity="P1",
                            selector=marker,
                            detail=f"{label}仍含 slate/cyan {found}（应挂 --studio-panel-*）",
                            files=[rel],
                        )
                    )
                if "studio-panel-ink" not in chunk and "--v2-adv-ink: var(--studio-panel" not in chunk and "--v2-combo-ink: var(--studio-panel" not in chunk:
                    # token wiring required at block head
                    if "studio-panel" not in chunk:
                        findings.append(
                            Finding(
                                id="D-UID-12",
                                severity="P1",
                                selector=marker,
                                detail=f"{label}未挂 studio-panel token",
                                files=[rel],
                            )
                        )

        if path.name == "import-wizard.css":
            # Empty/legacy theme must not reintroduce cyan accent
            if "#90e0ef" in lower:
                findings.append(
                    Finding(
                        id="D-UID-12",
                        severity="P1",
                        selector=".v2-wizard",
                        detail="Import Wizard 仍含 cyan #90e0ef（空主题应对齐 classic cream）",
                        files=[rel],
                    )
                )

        if path.name in ("carousel.css", "theme-classic.css"):
            # Gate carousel dots block only
            idx = 0
            while True:
                start = lower.find(".v2-carousel__dots", idx)
                if start < 0:
                    break
                chunk = lower[start : start + 500]
                if "#0f172a" in chunk:
                    findings.append(
                        Finding(
                            id="D-UID-12",
                            severity="P1",
                            selector=".v2-carousel__dots",
                            detail="轮播点边框仍为 slate #0f172a（应对齐 --studio-panel-ink）",
                            files=[rel],
                        )
                    )
                    break
                idx = start + len(".v2-carousel__dots")
    return findings


def find_home_tokens_drift(paths: list[Path]) -> list[Finding]:
    """D-UID-13 · bare :root must not be cyan sky; component CSS must not hardcode sky cyan."""
    findings: list[Finding] = []
    tokens = STUDIO / "homepage-v2" / "css" / "tokens.css"
    if tokens.is_file():
        text = tokens.read_text(encoding="utf-8")
        if ':root[data-v2-theme="sky"]' not in text:
            findings.append(
                Finding(
                    id="D-UID-13",
                    severity="P0",
                    selector=':root[data-v2-theme="sky"]',
                    detail="缺少显式 sky 主题块（cyan 不得再靠无 data-v2-theme）",
                    files=["templates/studio/homepage-v2/css/tokens.css"],
                )
            )
        # First :root { ... } before any [data-v2-theme] must not use sky primary
        m = re.search(r":root\s*\{([^{}]+)\}", text)
        if m:
            bare = m.group(1).lower()
            if "#0077b6" in bare or "#eaf8fb" in bare or "#48cae4" in bare:
                findings.append(
                    Finding(
                        id="D-UID-13",
                        severity="P1",
                        selector=":root",
                        detail="裸 :root 仍是 sky cyan（应对齐 mist 默认）",
                        files=["templates/studio/homepage-v2/css/tokens.css"],
                    )
                )

    boot = STUDIO / "homepage-v2" / "theme-boot.js"
    store = STUDIO / "homepage-v2" / "store.js"
    for path, label in ((boot, "theme-boot.js"), (store, "store.js")):
        if not path.is_file():
            continue
        js = path.read_text(encoding="utf-8")
        if 'removeAttribute("data-v2-theme")' in js or "removeAttribute('data-v2-theme')" in js:
            findings.append(
                Finding(
                    id="D-UID-13",
                    severity="P1",
                    selector=label,
                    detail="仍 removeAttribute(data-v2-theme)（sky 应 setAttribute sky）",
                    files=[str(path.relative_to(ROOT)).replace("\\", "/")],
                )
            )

    banned = ("rgba(72, 202, 228", "#0077b6", "#48cae4")
    for path in paths:
        if path.name == "tokens.css":
            continue
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        lower = _strip_comments(path.read_text(encoding="utf-8")).lower()
        found = [b for b in banned if b.lower() in lower]
        if found:
            findings.append(
                Finding(
                    id="D-UID-13",
                    severity="P1",
                    selector=rel,
                    detail=f"组件 CSS 仍硬编码 sky cyan {found}（应改用 --v2-* token）",
                    files=[rel],
                )
            )
    return findings


def find_shelf_dev_loading_drift(paths: list[Path]) -> list[Finding]:
    """D-UID-14 · shelf menu / dev panel / loading shimmer leave cyan or sub-11px chips."""
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = _strip_comments(path.read_text(encoding="utf-8"))
        lower = text.lower()

        if path.name == "bento.css":
            start = lower.find(".v2-loading__bar")
            if start >= 0:
                chunk = lower[start : start + 900]
                if "189, 230, 240" in chunk or "#bde6f0" in chunk:
                    findings.append(
                        Finding(
                            id="D-UID-14",
                            severity="P1",
                            selector=".v2-loading__bar",
                            detail="Loading shimmer 仍硬编码 sky cyan（应跟 --v2-border / --v2-surface）",
                            files=[rel],
                        )
                    )

        if path.name == "shelf.css":
            if "--v2-shelf-menu-ink: var(--studio-panel-ink" not in lower:
                findings.append(
                    Finding(
                        id="D-UID-14",
                        severity="P1",
                        selector=".v2-shelf__menu",
                        detail="书架菜单未挂 --studio-panel-ink",
                        files=[rel],
                    )
                )

        if path.name == "dev-panel.css":
            if "--dev-ink" not in lower:
                findings.append(
                    Finding(
                        id="D-UID-14",
                        severity="P1",
                        selector=".v2-dev-panel",
                        detail="Dev panel 缺少 --dev-ink cream 暗玻璃 token",
                        files=[rel],
                    )
                )
            if "font-family: system-ui" in lower.replace(" ", ""):
                findings.append(
                    Finding(
                        id="D-UID-14",
                        severity="P2",
                        selector=".v2-dev-panel",
                        detail="Dev panel 仍单独用 system-ui（应对齐 --studio-font-ui）",
                        files=[rel],
                    )
                )

        if path.name == "bench.css":
            start = lower.find(".v2-shelf__ready-badge")
            if start >= 0:
                chunk = lower[start : start + 400]
                if "font-size:9px" in chunk.replace(" ", "") or "font-size: 9px" in chunk:
                    findings.append(
                        Finding(
                            id="D-UID-14",
                            severity="P1",
                            selector=".v2-shelf__ready-badge",
                            detail="ready badge 仍为 9px（应对齐 --studio-panel-chip-size 11px）",
                            files=[rel],
                        )
                    )
    return findings


def find_overlay_toast_drift(paths: list[Path]) -> list[Finding]:
    """D-UID-15 · unsupported / failure / toast leave mint forest or sub-label sizes."""
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = _strip_comments(path.read_text(encoding="utf-8"))
        lower = text.lower()

        if path.name == "chrome.css":
            start = lower.find(".v2-unsupported")
            if start >= 0:
                chunk = lower[start : start + 2200]
                if "--un-ink" not in chunk:
                    findings.append(
                        Finding(
                            id="D-UID-15",
                            severity="P1",
                            selector=".v2-unsupported",
                            detail="Unsupported 缺少 --un-ink cream token",
                            files=[rel],
                        )
                    )
                if "font-size:10px" in chunk.replace(" ", "") or "font-size: 10px" in chunk:
                    findings.append(
                        Finding(
                            id="D-UID-15",
                            severity="P1",
                            selector=".v2-unsupported__brand",
                            detail="Unsupported brand 仍为 10px（应对齐 label 11px）",
                            files=[rel],
                        )
                    )

        if path.name == "overlays.css":
            if "#9ec5b8" in lower or "rgba(120, 160, 150" in lower:
                findings.append(
                    Finding(
                        id="D-UID-15",
                        severity="P1",
                        selector=".v2-failure__panel--auth",
                        detail="Failure auth 仍含薄荷 accent（应对齐 cream muted）",
                        files=[rel],
                    )
                )
            if lower.count("--v2-fs-accent:") > 1:
                findings.append(
                    Finding(
                        id="D-UID-15",
                        severity="P2",
                        selector=".v2-first-success__panel",
                        detail="FirstSuccess 重复定义 --v2-fs-accent",
                        files=[rel],
                    )
                )

        if path.name == "drawers.css":
            start = lower.find(".preview-toolbar__toast")
            if start >= 0:
                chunk = lower[start : start + 1200]
                banned = ("#f5fbf8", "#b8e0d0", "rgba(26, 47, 40", "#1a2f28")
                found = [b for b in banned if b in chunk]
                if found:
                    findings.append(
                        Finding(
                            id="D-UID-15",
                            severity="P1",
                            selector=".preview-toolbar__toast",
                            detail=f"Preview toast 仍含薄荷/森林色 {found}（应对齐 studio__toast cream）",
                            files=[rel],
                        )
                    )
    return findings


def find_wizard_help_closeout_drift(paths: list[Path]) -> list[Finding]:
    """D-UID-16 · wizard sub-11px labels / help forest / dock mint leftovers."""
    findings: list[Finding] = []
    for path in paths:
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        text = _strip_comments(path.read_text(encoding="utf-8"))
        lower = text.lower()

        if path.name == "import-wizard.css":
            if "font-size: 10px" in text or "font-size:10px" in text.replace(" ", ""):
                findings.append(
                    Finding(
                        id="D-UID-16",
                        severity="P1",
                        selector=".v2-wizard",
                        detail="Wizard 仍含 10px 文案（应对齐 label 11px）",
                        files=[rel],
                    )
                )
            forest = ("rgba(47, 107, 85", "#2f6b55", "rgba(120, 190, 160")
            found_forest = [b for b in forest if b in lower]
            if found_forest:
                findings.append(
                    Finding(
                        id="D-UID-16",
                        severity="P1",
                        selector=".v2-wizard__demo",
                        detail=(
                            f"Wizard demo CTA 仍含旧森林色 {found_forest} "
                            f"（应对齐 --v2-sheet-accent cream/gold）"
                        ),
                        files=[rel],
                    )
                )

        if path.name == "help-drawer.css":
            if "rgba(26, 47, 40" in lower or "#f7faf8" in lower:
                findings.append(
                    Finding(
                        id="D-UID-16",
                        severity="P1",
                        selector=".studio-help-drawer",
                        detail="Help 抽屉仍含森林 rgba(26,47,40) / #f7faf8（应挂 --studio-panel-*）",
                        files=[rel],
                    )
                )

        if path.name == "task-dock.css":
            banned = ("#f5fbf8", "#a8dcc8", "rgba(26, 47, 40", "rgba(255, 183, 77")
            found = [b for b in banned if b in lower]
            if found:
                findings.append(
                    Finding(
                        id="D-UID-16",
                        severity="P1",
                        selector=".preview-task-dock",
                        detail=f"Task dock 仍含薄荷/橙 tip {found}（应对齐 cream + gold）",
                        files=[rel],
                    )
                )

        if path.name == "longshot.css":
            banned = ("#81d4fa", "#a8dcc8", "rgba(255, 183, 77", "#ffb74d")
            found = [b for b in banned if b in lower]
            if found:
                findings.append(
                    Finding(
                        id="D-UID-16",
                        severity="P1",
                        selector=".preview-toolbar__export / longshot",
                        detail=f"Longshot 仍含 cyan/mint/橙 tip {found}",
                        files=[rel],
                    )
                )
    return findings


def run_audit(
    paths: list[Path] | None = None,
    *,
    wave: str = "modal",
) -> dict[str, object]:
    if paths is None:
        paths = [p for p in WAVES.get(wave, PILOT_CSS) if p.is_file()]
    conflicts = find_selector_conflicts(paths)
    hist = histogram_for_files(paths)
    hist_findings = build_histogram_findings(hist)
    findings = conflicts + hist_findings
    if wave in ("settings-sheet", "all"):
        findings.extend(find_settings_sheet_family_drift())
    if wave in ("preview-chrome", "all"):
        findings.extend(find_preview_chrome_bare_hex(paths))
    if wave in ("wait-tips", "all"):
        findings.extend(find_wait_tips_rainbow_tones(paths))
    if wave in ("cap-narrow-lightbox", "all"):
        findings.extend(find_cap_narrow_lightbox_drift(paths))
    if wave in ("bench-wizard-carousel", "all"):
        findings.extend(find_bench_wizard_carousel_drift(paths))
    if wave in ("home-tokens", "all"):
        findings.extend(find_home_tokens_drift(paths))
    if wave in ("shelf-dev-loading", "all"):
        findings.extend(find_shelf_dev_loading_drift(paths))
    if wave in ("overlay-toast", "all"):
        findings.extend(find_overlay_toast_drift(paths))
    if wave in ("wizard-help-closeout", "all"):
        findings.extend(find_wizard_help_closeout_drift(paths))
    by_sev = Counter(f.severity for f in findings)
    return {
        "scope": wave,
        "files": [str(p.relative_to(ROOT)).replace("\\", "/") for p in paths],
        "summary": {
            "findings": len(findings),
            "P0": by_sev.get("P0", 0),
            "P1": by_sev.get("P1", 0),
            "P2": by_sev.get("P2", 0),
        },
        "findings": [asdict(f) for f in findings],
        "histograms": hist,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Studio UI detail static audit")
    ap.add_argument(
        "--wave",
        choices=sorted(WAVES),
        default=None,
        help="Which surface wave to audit (default: modal; with --strict ⇒ all)",
    )
    ap.add_argument("--json", type=Path, default=None, help="Write full JSON report")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 when P0 or P1 findings exist (P2 不阻断)；裸 --strict 时 wave=all",
    )
    args = ap.parse_args(argv)
    # QFX D-QFX-11 / AC-08/19：bare --strict ⇒ wave=all
    wave = args.wave
    if wave is None:
        wave = "all" if args.strict else "modal"
    report = run_audit(wave=wave)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    for f in report["findings"]:
        print(f"[{f['severity']}] {f['id']} {f['selector']}: {f['detail']}")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"wrote {args.json}")
    if args.strict and (report["summary"]["P0"] or report["summary"]["P1"]):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
