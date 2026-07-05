"""YAML → grid CSS strings (R-P16-14). W2 full generation + depth validation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from travelogue.layout_templates.models import TemplateDef, TemplateSlot, TemplateStage
from travelogue.paths import JOURNAL_SCREENS_CSS


def _format_weighted_track(weight: float) -> str:
    w = int(weight) if weight == int(weight) else weight
    return f"minmax(0, {w}fr)"


def _format_uniform_track(weight: float) -> str:
    if weight == 1.0:
        return "1fr"
    return _format_weighted_track(weight)


def grid_template_columns(stage: TemplateStage) -> str:
    if stage.cols:
        weights = stage.cols
        if len(weights) > 1 and len(set(weights)) > 1:
            return " ".join(_format_weighted_track(w) for w in weights)
        if all(w == weights[0] for w in weights):
            return f"repeat({len(weights)}, 1fr)"
        return " ".join(_format_uniform_track(w) for w in weights)
    if stage.grid:
        n = stage.grid[0]
        return f"repeat({n}, 1fr)"
    return "1fr"


def grid_template_rows(stage: TemplateStage) -> str:
    if stage.rows:
        weights = stage.rows
        if len(weights) > 1 and len(set(weights)) > 1:
            return " ".join(_format_weighted_track(w) for w in weights)
        if all(w == weights[0] for w in weights):
            return f"repeat({len(weights)}, 1fr)"
        return " ".join(_format_uniform_track(w) for w in weights)
    if stage.grid and len(stage.grid) > 1:
        n = stage.grid[1]
        return f"repeat({n}, 1fr)"
    return "1fr"


def grid_templates_for(template: TemplateDef) -> tuple[str, str]:
    return grid_template_columns(template.stage), grid_template_rows(template.stage)


def normalize_grid_template(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


_JOURNAL_CSS_CACHE: tuple[str, float, str] | None = None


def _read_journal_css() -> str:
    """Read journal-screens.css with an mtime-keyed cache.

    validate_css_bundle is called once per template during a full CLI validate;
    without caching this re-reads the same large stylesheet N times.
    """
    global _JOURNAL_CSS_CACHE
    path = Path(JOURNAL_SCREENS_CSS)
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return path.read_text(encoding="utf-8")
    key = str(path)
    cache = _JOURNAL_CSS_CACHE
    if cache is not None and cache[0] == key and cache[1] == mtime:
        return cache[2]
    text = path.read_text(encoding="utf-8")
    _JOURNAL_CSS_CACHE = (key, mtime, text)
    return text


def _track_dims(stage: TemplateStage) -> tuple[int, int]:
    if stage.cols and stage.rows:
        return len(stage.cols), len(stage.rows)
    if stage.grid:
        return stage.grid[0], stage.grid[1]
    return 1, 1


def slot_cells(stage: TemplateStage, rect: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    """Track cells (1-based) covered by a slot rect."""
    c0, c1, r0, r1 = rect
    cols, rows = _track_dims(stage)
    if c0 < 1 or r0 < 1 or c1 < c0 or r1 < r0:
        return set()
    if c1 > cols or r1 > rows:
        return set()
    return {(c, r) for c in range(c0, c1 + 1) for r in range(r0, r1 + 1)}


def slot_placement_decl(slot: TemplateSlot) -> tuple[str, str]:
    """Canonical grid-column / grid-row declarations from rect."""
    c0, c1, r0, r1 = slot.rect
    col_span = c1 - c0 + 1
    row_span = r1 - r0 + 1
    if col_span == 1:
        col = str(c0)
    else:
        col = f"{c0} / span {col_span}"
    if row_span == 1:
        row = str(r0)
    else:
        row = f"{r0} / span {row_span}"
    return col, row


def generate_slot_css(template: TemplateDef, slot: TemplateSlot) -> str:
    cls = template.render_grid_class
    col, row = slot_placement_decl(slot)
    sel = (
        f"html[data-layout=\"web\"] .{cls} .layout-slot[data-slot=\"{slot.index}\"], "
        f"html[data-layout=\"auto\"] .{cls} .layout-slot[data-slot=\"{slot.index}\"]"
    )
    return f"{sel} {{\n  grid-column: {col};\n  grid-row: {row};\n}}"


def generate_grid_css(template: TemplateDef) -> str:
    if template.kind == "stack":
        cols = grid_template_columns(template.stage)
        return (
            f"html[data-layout=\"web\"] .{template.render_grid_class},\n"
            f"html[data-layout=\"auto\"] .{template.render_grid_class} {{\n"
            f"  grid-template-columns: {cols};\n"
            f"  grid-auto-rows: auto;\n"
            f"  align-items: stretch;\n"
            f"}}"
        )
    cols, rows = grid_templates_for(template)
    cls = template.render_grid_class
    header = (
        f"html[data-layout=\"web\"] .{cls},\n"
        f"html[data-layout=\"auto\"] .{cls}"
    )
    block = (
        f"{header} {{\n"
        f"  grid-template-columns: {cols};\n"
        f"  grid-template-rows: {rows};\n"
    )
    if template.stage.gap:
        block += f"  gap: {template.stage.gap};\n"
    block += "  align-items: stretch;\n}"
    if template.kind == "primitive" and template.slots and len(template.slots) <= 1:
        return block
    slot_blocks = [generate_slot_css(template, s) for s in template.slots]
    return block + "\n\n" + "\n\n".join(slot_blocks)


def generate_bundle_css(templates: dict[str, TemplateDef]) -> str:
    parts = [
        "/* Phase 16 LTE generated grid CSS — do not edit by hand */",
        "",
    ]
    for tid in sorted(templates):
        parts.append(f"/* {tid} */")
        parts.append(generate_grid_css(templates[tid]))
        parts.append("")
    return "\n".join(parts)


def _parse_journal_grid_css(css_text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    blocks = re.findall(
        r"(\.layout-screen__grid--[a-z0-9-]+)\s*\{([^}]+)\}",
        css_text,
        flags=re.IGNORECASE,
    )
    for selector, body in blocks:
        cls = selector.lstrip(".")
        cols_m = re.search(r"grid-template-columns:\s*([^;]+);", body)
        rows_m = re.search(r"grid-template-rows:\s*([^;]+);", body)
        if not cols_m and not rows_m:
            continue
        out.setdefault(cls, {})
        if cols_m:
            out[cls]["gridTemplateColumns"] = normalize_grid_template(cols_m.group(1))
        if rows_m:
            out[cls]["gridTemplateRows"] = normalize_grid_template(rows_m.group(1))
    return out


def _marker_block_region(css_text: str) -> str:
    """Authoritative LTE-generated region only.

    Parity must compare YAML output against the generated marker block, not the
    pattern-specific overlays (data-pattern/data-layout-hint), which legitimately
    redefine the same grid class with variant tracks and would otherwise clobber
    the canonical value (e.g. screen-portrait-2's person-pair overlay).
    """
    start = css_text.find(LTE_MARKER_START)
    end = css_text.find(LTE_MARKER_END)
    if start == -1 or end == -1 or end <= start:
        return css_text
    return css_text[start : end + len(LTE_MARKER_END)]


def validate_css_bundle(template: TemplateDef, *, journal_css_text: str | None = None) -> list[str]:
    """V-P16-05/06: generated grid-template matches stage; optional journal CSS parity."""
    issues: list[str] = []
    if template.kind == "stack":
        return issues
    cols, rows = grid_templates_for(template)
    if template.kind == "composite" or (template.kind == "primitive" and len(template.slots) > 1):
        covered: set[tuple[int, int]] = set()
        for slot in template.slots:
            cells = slot_cells(template.stage, slot.rect)
            if not cells:
                issues.append(f"slot {slot.index} rect {slot.rect} covers no cells (V-P16-06)")
            overlap = covered & cells
            if overlap:
                issues.append(f"slot {slot.index} placement overlaps {sorted(overlap)} (V-P16-06)")
            covered |= cells
    css_text = journal_css_text or _read_journal_css()
    parsed = _parse_journal_grid_css(_marker_block_region(css_text))
    expected = parsed.get(template.render_grid_class)
    if expected:
        if "gridTemplateColumns" in expected and normalize_grid_template(cols) != expected["gridTemplateColumns"]:
            issues.append(
                f"grid-template-columns {cols!r} != journal {expected['gridTemplateColumns']!r}"
            )
        if "gridTemplateRows" in expected and normalize_grid_template(rows) != expected["gridTemplateRows"]:
            issues.append(
                f"grid-template-rows {rows!r} != journal {expected['gridTemplateRows']!r}"
            )
    return issues


def write_generated_css(
    templates: dict[str, TemplateDef],
    path: Path,
) -> None:
    path.write_text(generate_bundle_css(templates), encoding="utf-8")


LTE_MARKER_START = (
    "/* @lte-generated:start — YAML→CSS authority; "
    "run: python -m travelogue.layout_templates.cli export --sync-journal */"
)
LTE_MARKER_END = "/* @lte-generated:end */"
JOURNAL_SCREENS_OVERLAYS = Path(JOURNAL_SCREENS_CSS).parent / "journal-screens-overlays.css"
OVERLAYS_MARKER_START = "/* @journal-overlays:start */"
OVERLAYS_MARKER_END = "/* @journal-overlays:end */"


_CSS_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_TRAILING_SELECTOR_RE = re.compile(r"([^{}]+)\{")


def _is_blank_or_comment_only(css_text: str) -> bool:
    """True if css_text has no CSS content once comments/whitespace are stripped."""
    return _CSS_COMMENT_RE.sub("", css_text).strip() == ""


def _trailing_legacy_selector_preview(css_text: str, *, max_selectors: int = 5) -> list[str]:
    """Best-effort selector list for a trailing CSS blob, for stderr/error reporting."""
    stripped = _CSS_COMMENT_RE.sub("", css_text)
    selectors = [s.strip().replace("\n", " ") for s in _TRAILING_SELECTOR_RE.findall(stripped)]
    selectors = [re.sub(r"\s+", " ", s) for s in selectors if s]
    return selectors[:max_selectors]


class TrailingLegacyCssError(RuntimeError):
    """Raised (T-LRG-12 / AC-LRG-12) when hand-written CSS survives after
    @journal-overlays:end and would otherwise be silently truncated by export.
    """

    def __init__(self, preview: list[str]) -> None:
        self.preview = preview
        listing = "\n".join(f"  - {sel}" for sel in preview) or "  (selector preview unavailable)"
        super().__init__(
            "export --sync-journal: hand-written CSS found after @journal-overlays:end; "
            "it would be silently truncated (T-LRG-12). Truncated selector preview:\n"
            f"{listing}\n"
            "Move these rules into templates/visual-journal/journal-screens-overlays.css "
            "before the marker (only file allowed to hold hand-written reader-visible "
            "overlay CSS), or pass --warn-trailing-legacy for a warn-only migration bypass."
        )


def _truncate_trailing_legacy_after_overlays(
    journal_text: str,
    *,
    on_trailing_legacy: str = "strict",
) -> str:
    """Drop hand-written grid CSS after overlay marker (LTE is authoritative).

    Universal slot/img containment lives in the preamble *before* LTE_MARKER_START;
    do not move it into the truncated tail or export will drop mosaic image sizing.

    Before truncating, detect non-blank/non-comment CSS in the region being dropped
    (T-LRG-12 / AC-LRG-12):
      - on_trailing_legacy="strict" (default): raise TrailingLegacyCssError.
      - on_trailing_legacy="warn": print a WARNING to stderr, still truncate.
    """
    oend = journal_text.find(OVERLAYS_MARKER_END)
    if oend == -1:
        return journal_text
    end_pos = oend + len(OVERLAYS_MARKER_END)
    trailing = journal_text[end_pos:]
    if not _is_blank_or_comment_only(trailing):
        preview = _trailing_legacy_selector_preview(trailing)
        if on_trailing_legacy == "warn":
            listing = "; ".join(preview) or "(selector preview unavailable)"
            print(
                "WARNING: hand-written CSS found after @journal-overlays:end; "
                f"truncating (T-LRG-12 warn-only bypass): {listing}",
                file=sys.stderr,
            )
        else:
            raise TrailingLegacyCssError(preview)
    return journal_text[:end_pos].rstrip() + "\n"


def sync_journal_screens_css(
    templates: dict[str, TemplateDef],
    *,
    journal_path: Path | None = None,
    on_trailing_legacy: str = "strict",
) -> Path:
    """Inject/replace LTE generated grid CSS in journal-screens.css (R-P16-14).

    on_trailing_legacy: forwarded to _truncate_trailing_legacy_after_overlays
    (T-LRG-12); "strict" (default) raises TrailingLegacyCssError on marker-external
    hand-written CSS, "warn" logs to stderr and still truncates.
    """
    path = journal_path or Path(JOURNAL_SCREENS_CSS)
    text = path.read_text(encoding="utf-8")
    generated = generate_bundle_css(templates)
    block = f"{LTE_MARKER_START}\n{generated}\n{LTE_MARKER_END}"
    pattern = re.compile(
        re.escape(LTE_MARKER_START) + r".*?" + re.escape(LTE_MARKER_END),
        re.DOTALL,
    )
    if pattern.search(text):
        new_text = pattern.sub(block, text)
    else:
        anchor = (
            "html[data-layout=\"web\"] .layout-screen__grid--1col,\n"
            "html[data-layout=\"auto\"] .layout-screen__grid--1col {"
        )
        idx = text.find(anchor)
        if idx == -1:
            raise ValueError(f"anchor not found in {path}")
        end = text.find("}", idx)
        if end == -1:
            raise ValueError(f"anchor block incomplete in {path}")
        insert_at = end + 1
        new_text = text[:insert_at] + "\n\n" + block + text[insert_at:]
    new_text = prune_lte_duplicate_blocks_outside_marker(new_text)
    new_text = sync_journal_overlays(new_text)
    new_text = _truncate_trailing_legacy_after_overlays(new_text, on_trailing_legacy=on_trailing_legacy)
    path.write_text(new_text, encoding="utf-8")
    return path


def _journal_text_without_overlay_block(journal_text: str) -> str:
    ostart = journal_text.find(OVERLAYS_MARKER_START)
    oend = journal_text.find(OVERLAYS_MARKER_END)
    if ostart == -1 or oend == -1 or oend < ostart:
        return journal_text
    return journal_text[:ostart] + journal_text[oend + len(OVERLAYS_MARKER_END) :]


def sync_journal_overlays(
    journal_text: str,
    *,
    overlays_path: Path | None = None,
) -> str:
    """Inject pattern-specific overlay CSS (data-pattern / data-layout-hint rules)."""
    path = overlays_path or JOURNAL_SCREENS_OVERLAYS
    if not path.is_file():
        return journal_text
    overlays = path.read_text(encoding="utf-8").strip()
    if not overlays:
        return journal_text
    block = f"\n\n{OVERLAYS_MARKER_START}\n{overlays}\n{OVERLAYS_MARKER_END}\n"
    pattern = re.compile(
        re.escape(OVERLAYS_MARKER_START) + r".*?" + re.escape(OVERLAYS_MARKER_END),
        re.DOTALL,
    )
    if pattern.search(journal_text):
        return pattern.sub(block.strip() + "\n", journal_text)
    lte_end = journal_text.find(LTE_MARKER_END)
    if lte_end == -1:
        return journal_text.rstrip() + block
    insert_at = lte_end + len(LTE_MARKER_END)
    return journal_text[:insert_at] + block + journal_text[insert_at:]


def lte_grid_classes_outside_marker(journal_text: str) -> list[str]:
    """Return LTE grid class names duplicated outside the generated marker block."""
    journal_text = _journal_text_without_overlay_block(journal_text)
    start = journal_text.find(LTE_MARKER_START)
    end = journal_text.find(LTE_MARKER_END)
    if start == -1 or end == -1:
        return []
    outside = journal_text[:start] + journal_text[end + len(LTE_MARKER_END) :]
    inside = journal_text[start:end]
    inside_classes = set(re.findall(r"\.(layout-screen__grid--[a-z0-9-]+)", inside))
    dupes: list[str] = []
    for cls in sorted(inside_classes):
        if re.search(rf"\.{re.escape(cls)}\s*[,{{]", outside):
            dupes.append(cls)
    return dupes


_GRID_CLASS_IN_SELECTOR = re.compile(r"layout-screen__grid--[a-z0-9-]+")
_CSS_RULE_BLOCK = re.compile(r"([^{}/]+?\{[^{}]*\})", re.MULTILINE)


def _grid_classes_in_selector(selector: str) -> set[str]:
    return set(_GRID_CLASS_IN_SELECTOR.findall(selector))


def _is_pattern_overlay_selector(selector: str) -> bool:
    """Pattern-specific overrides must survive LTE grid dedupe."""
    return "data-pattern=" in selector or "data-layout-hint=" in selector


def _should_prune_rule(selector: str, dupe_classes: set[str]) -> bool:
    if "@" in selector:
        # Never touch at-rule preludes (@media/@supports/...); the flat regex
        # scanner cannot model their nested blocks safely.
        return False
    if _is_pattern_overlay_selector(selector):
        return False
    classes = _grid_classes_in_selector(selector)
    if not classes:
        return False
    return classes <= dupe_classes


def _rewrite_rule_strip_dupe_selectors(full_rule: str, dupe_classes: set[str]) -> str | None:
    """Drop selector lines that only reference duplicated LTE grid classes."""
    brace = full_rule.find("{")
    if brace == -1:
        return full_rule
    selector_part = full_rule[:brace]
    body = full_rule[brace:]
    selectors = [s.strip() for s in selector_part.split(",") if s.strip()]
    kept = [
        sel
        for sel in selectors
        if _is_pattern_overlay_selector(sel) or not _should_prune_rule(sel, dupe_classes)
    ]
    if not kept:
        return None
    if len(kept) == len(selectors):
        return full_rule
    return ",\n".join(kept) + " " + body.lstrip()


def _prune_css_section(text: str, dupe_classes: set[str]) -> str:
    if not dupe_classes or not text.strip():
        return text
    out: list[str] = []
    pos = 0
    for match in _CSS_RULE_BLOCK.finditer(text):
        out.append(text[pos : match.start()])
        rule = match.group(0)
        if _should_prune_rule(rule.split("{", 1)[0], dupe_classes):
            pos = match.end()
            continue
        rewritten = _rewrite_rule_strip_dupe_selectors(rule, dupe_classes)
        if rewritten is None:
            pos = match.end()
            continue
        out.append(rewritten)
        pos = match.end()
    out.append(text[pos:])
    cleaned = re.sub(r"\n{3,}", "\n\n", "".join(out))
    return cleaned.rstrip() + ("\n" if cleaned else "")


def prune_lte_duplicate_blocks_outside_marker(journal_text: str) -> str:
    """Remove hand-written grid rules outside the marker when LTE already generates them."""
    dupes = set(lte_grid_classes_outside_marker(journal_text))
    if not dupes:
        return journal_text
    start = journal_text.find(LTE_MARKER_START)
    end = journal_text.find(LTE_MARKER_END)
    if start == -1 or end == -1:
        return journal_text
    marker_end = end + len(LTE_MARKER_END)
    before = _prune_css_section(journal_text[:start], dupes)
    marker = journal_text[start:marker_end]
    after = journal_text[marker_end:]
    ostart = after.find(OVERLAYS_MARKER_START)
    oend = after.find(OVERLAYS_MARKER_END)
    if ostart != -1 and oend != -1 and oend > ostart:
        mid = _prune_css_section(after[:ostart], dupes)
        overlay = after[ostart : oend + len(OVERLAYS_MARKER_END)]
        tail = _prune_css_section(after[oend + len(OVERLAYS_MARKER_END) :], dupes)
        return before + marker + mid + overlay + tail
    after = _prune_css_section(after, dupes)
    return before + marker + after
