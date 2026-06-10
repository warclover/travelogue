"""Hard constraints for layout search (V2 PRD §5 · Phase 6 M25-B)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class LayoutConstraintViolation:
    code: str
    message: str
    chapter_id: str | None = None
    screen_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "chapterId": self.chapter_id,
            "screenIndex": self.screen_index,
        }


DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN = 2


def _slot_asset_ids(screen: dict) -> list[str]:
    return [s["assetId"] for s in (screen.get("slots") or []) if s.get("assetId")]


def _content_screens(chapters: list[dict]) -> list[tuple[str | None, int, dict]]:
    rows: list[tuple[str | None, int, dict]] = []
    for ch in chapters:
        ch_id = ch.get("id")
        for si, screen in enumerate(ch.get("screens") or []):
            if not any(s.get("assetId") for s in (screen.get("slots") or [])):
                continue
            rows.append((ch_id, si, screen))
    return rows


def max_consecutive_pattern_streak(screens: list[dict]) -> int:
    streak = 0
    best = 0
    prev: str | None = None
    for screen in screens:
        pid = screen.get("patternId")
        if not pid:
            streak = 0
            prev = None
            continue
        if pid == prev:
            streak += 1
        else:
            streak = 1
            prev = pid
        best = max(best, streak)
    return best


def plan_violates_consecutive_pattern(
    screens: list[dict],
    *,
    max_streak: int = DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN,
) -> bool:
    """P6-D3 · rule gate for beam candidates and longshot picks."""
    return max_consecutive_pattern_streak(screens) > max_streak


def check_max_consecutive_same_pattern(
    chapters: list[dict],
    *,
    max_streak: int = DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN,
) -> list[LayoutConstraintViolation]:
    violations: list[LayoutConstraintViolation] = []
    streak = 0
    prev: str | None = None
    for ch_id, si, screen in _content_screens(chapters):
        pid = screen.get("patternId")
        if not pid:
            streak = 0
            prev = None
            continue
        if pid == prev:
            streak += 1
        else:
            streak = 1
            prev = pid
        if streak > max_streak:
            violations.append(
                LayoutConstraintViolation(
                    code="consecutive_same_pattern",
                    message=f"pattern {pid} repeated {streak} times (max {max_streak})",
                    chapter_id=ch_id,
                    screen_index=si,
                )
            )
    return violations


def check_no_duplicate_assets(chapters: list[dict]) -> list[LayoutConstraintViolation]:
    seen: set[str] = set()
    violations: list[LayoutConstraintViolation] = []
    for ch in chapters:
        ch_id = ch.get("id")
        for si, screen in enumerate(ch.get("screens") or []):
            for aid in _slot_asset_ids(screen):
                if aid in seen:
                    violations.append(
                        LayoutConstraintViolation(
                            code="duplicate_asset",
                            message=f"asset {aid} appears more than once",
                            chapter_id=ch_id,
                            screen_index=si,
                        )
                    )
                seen.add(aid)
    return violations


def check_cover_not_in_screens(
    chapters: list[dict],
    cover_asset_id: str | None,
) -> list[LayoutConstraintViolation]:
    if not cover_asset_id:
        return []
    violations: list[LayoutConstraintViolation] = []
    for ch in chapters:
        for si, screen in enumerate(ch.get("screens") or []):
            if cover_asset_id in _slot_asset_ids(screen):
                violations.append(
                    LayoutConstraintViolation(
                        code="cover_in_screen",
                        message=f"cover {cover_asset_id} must not appear in screens",
                        chapter_id=ch.get("id"),
                        screen_index=si,
                    )
                )
    return violations


FOCAL_EDGE_MARGIN = 0.15


def check_focal_not_at_edge(
    chapters: list[dict],
    assets_by_id: dict[str, dict],
    *,
    margin: float = FOCAL_EDGE_MARGIN,
) -> list[LayoutConstraintViolation]:
    """Subject/focal should not sit on screen edge (Phase 3b partial)."""
    violations: list[LayoutConstraintViolation] = []
    for ch in chapters:
        for si, screen in enumerate(ch.get("screens") or []):
            for aid in _slot_asset_ids(screen):
                asset = assets_by_id.get(aid) or {}
                fp = asset.get("focalPoint") or {}
                x = fp.get("x")
                y = fp.get("y")
                if x is None or y is None:
                    continue
                if x < margin or x > 1.0 - margin or y < margin or y > 1.0 - margin:
                    violations.append(
                        LayoutConstraintViolation(
                            code="focal_at_edge",
                            message=f"asset {aid} focal ({x:.2f},{y:.2f}) too close to edge",
                            chapter_id=ch.get("id"),
                            screen_index=si,
                        )
                    )
    return violations


def validate_chapter_layout(
    chapters: list[dict],
    *,
    cover_asset_id: str | None = None,
    assets_by_id: dict[str, dict] | None = None,
    check_focal_edges: bool = False,
    max_consecutive_same_pattern: int = DEFAULT_MAX_CONSECUTIVE_SAME_PATTERN,
) -> list[LayoutConstraintViolation]:
    violations: list[LayoutConstraintViolation] = []
    violations.extend(check_no_duplicate_assets(chapters))
    violations.extend(check_cover_not_in_screens(chapters, cover_asset_id))
    violations.extend(
        check_max_consecutive_same_pattern(
            chapters,
            max_streak=max_consecutive_same_pattern,
        )
    )
    if check_focal_edges and assets_by_id:
        violations.extend(check_focal_not_at_edge(chapters, assets_by_id))
    return violations


def layout_is_valid(chapters: list[dict], **kwargs: Any) -> bool:
    return not validate_chapter_layout(chapters, **kwargs)


# --- 排版规则优化 v0.5 · 节奏 post-check（PRD R-06 / R-08 / V-08 / V-09） ---

MAX_PORTRAIT_PAIR_STREAK = 2  # R-06
MAX_PORTRAIT_ORIENTATION_STREAK = 6  # R-08

_PORTRAIT_PAIR_PATTERNS = frozenset({"screen-portrait-2"})
_FULL_BLEED_PORTRAIT_PATTERNS = frozenset(
    {"screen-portrait-1", "screen-tall-1", "screen-plate"}
)
_PORTRAIT_ORIENTATION_PATTERNS = frozenset(
    {"screen-portrait-1", "screen-portrait-2", "screen-portrait-3", "screen-tall-1"}
)


def is_portrait_pair_pattern(pattern_id: str | None) -> bool:
    """R-06 · 两张竖版并排（含 person-pair 等价 patternId）。"""
    return pattern_id in _PORTRAIT_PAIR_PATTERNS


def is_portrait_orientation_pattern(pattern_id: str | None) -> bool:
    """R-08 · 计入「全竖版屏」朝向 streak 的 patternId。"""
    return pattern_id in _PORTRAIT_ORIENTATION_PATTERNS


def is_full_bleed_portrait_screen(screen: dict) -> bool:
    """V-08/V-09 · 满屏竖图等价类：portrait-1 / tall-1 / 单竖 plate。"""
    pid = str(screen.get("patternId") or "")
    if pid in ("screen-portrait-1", "screen-tall-1"):
        return True
    if pid == "screen-plate":
        # plate 仅当唯一槽位为竖图时计入（sole portrait slot）
        slots = [s for s in (screen.get("slots") or []) if s.get("assetId")]
        return len(slots) == 1
    return False


def _streak_violations(
    chapters: list[dict],
    *,
    code: str,
    label: str,
    max_streak: int,
    pred,
) -> list[LayoutConstraintViolation]:
    """Generic consecutive-streak checker over content screens (R-07: breath 不计入)."""
    violations: list[LayoutConstraintViolation] = []
    streak = 0
    for ch_id, si, screen in _content_screens(chapters):
        if pred(screen):
            streak += 1
        else:
            streak = 0
            continue
        if streak > max_streak:
            violations.append(
                LayoutConstraintViolation(
                    code=code,
                    message=f"{label} streak {streak} > {max_streak}",
                    chapter_id=ch_id,
                    screen_index=si,
                )
            )
    return violations


def check_portrait_pair_streak(
    chapters: list[dict],
    *,
    max_streak: int = MAX_PORTRAIT_PAIR_STREAK,
) -> list[LayoutConstraintViolation]:
    """R-06 · `screen-portrait-2` 连续不得 > max_streak（默认 2）。"""
    return _streak_violations(
        chapters,
        code="portrait_pair_streak",
        label="portrait-2",
        max_streak=max_streak,
        pred=lambda sc: is_portrait_pair_pattern(sc.get("patternId")),
    )


def check_full_bleed_portrait_consecutive(
    chapters: list[dict],
) -> list[LayoutConstraintViolation]:
    """V-08/V-09 · 满屏竖单等价类不得连续（streak > 1）。"""
    return _streak_violations(
        chapters,
        code="full_bleed_portrait_consecutive",
        label="full-bleed-portrait",
        max_streak=1,
        pred=is_full_bleed_portrait_screen,
    )


def check_portrait_orientation_streak(
    chapters: list[dict],
    *,
    max_streak: int = MAX_PORTRAIT_ORIENTATION_STREAK,
) -> list[LayoutConstraintViolation]:
    """R-08 · 连续「全竖版屏」不得 > max_streak（默认 6）。"""
    return _streak_violations(
        chapters,
        code="portrait_orientation_streak",
        label="portrait-orientation",
        max_streak=max_streak,
        pred=lambda sc: is_portrait_orientation_pattern(sc.get("patternId")),
    )


def audit_rhythm_violations(
    chapters: list[dict],
    *,
    max_pair_streak: int = MAX_PORTRAIT_PAIR_STREAK,
    max_orientation_streak: int = MAX_PORTRAIT_ORIENTATION_STREAK,
) -> list[LayoutConstraintViolation]:
    """汇总 v0.5 节奏规则违规（供 telemetry / 灰度 log / 测试）。"""
    violations: list[LayoutConstraintViolation] = []
    violations.extend(check_portrait_pair_streak(chapters, max_streak=max_pair_streak))
    violations.extend(check_full_bleed_portrait_consecutive(chapters))
    violations.extend(
        check_portrait_orientation_streak(chapters, max_streak=max_orientation_streak)
    )
    return violations
