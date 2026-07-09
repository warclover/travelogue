"""Hard constraints for layout search (V2 PRD §5 · Phase 6 M25-B)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from travelogue.layout_contract.constraints import FOCAL_EDGE_MARGIN
from travelogue.layout_contract.rhythm import (
    MAX_PORTRAIT_ORIENTATION_STREAK,
    MAX_PORTRAIT_PAIR_STREAK,
    PORTRAIT_SINGLE_PATTERNS,
    is_portrait_orientation_pattern,
    is_portrait_pair_pattern,
)

_log = logging.getLogger(__name__)


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
# 常量与 pattern 判定的单一来源在 screen_layout_state（与规划期硬约束同源），
# 此处仅做事后审计，禁止再复制阈值。


def is_full_bleed_portrait_screen(screen: dict) -> bool:
    """V-08/V-09 · 满屏竖图等价类：portrait-1 / tall-1 / 单竖 plate。"""
    pid = str(screen.get("patternId") or "")
    if pid in PORTRAIT_SINGLE_PATTERNS:
        return True
    if pid == "screen-plate":
        # plate 仅当唯一槽位为竖图时计入（sole portrait slot）
        slots = [s for s in (screen.get("slots") or []) if s.get("assetId")]
        return len(slots) == 1
    return False


def _is_rhythm_transparent(screen: dict) -> bool:
    """R-07 · 呼吸屏 / 章分隔 / decor 不计入也不打断 streak。"""
    pid = str(screen.get("patternId") or "")
    return pid.startswith("screen-breath") or pid.startswith("screen-decor")


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
        if _is_rhythm_transparent(screen):
            # R-07: transparent — neither count nor break the streak.
            continue
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


RHYTHM_POSTCHECK_CODES = (
    "portrait_pair_streak",
    "full_bleed_portrait_consecutive",
    "portrait_orientation_streak",
)


def run_rhythm_postcheck(
    chapters: list[dict],
    *,
    mode: str = "log",
    trip_id: str | None = None,
    max_pair_streak: int = MAX_PORTRAIT_PAIR_STREAK,
    max_orientation_streak: int = MAX_PORTRAIT_ORIENTATION_STREAK,
) -> tuple[dict[str, int], list[LayoutConstraintViolation]]:
    """灰度 post-check（AC-RHY-07 · OQ-09=B）：审计 R-06 / R-08 / V-09 违规。

    - ``mode="log"``（默认）：仅记录日志并返回摘要，不改变规划结果（灰度观测期）。
    - ``mode="enforce"``：返回违规供上层处理（当前与 log 行为一致，预留硬执行接口）。
    """
    violations = audit_rhythm_violations(
        chapters,
        max_pair_streak=max_pair_streak,
        max_orientation_streak=max_orientation_streak,
    )
    summary: dict[str, int] = {code: 0 for code in RHYTHM_POSTCHECK_CODES}
    for v in violations:
        summary[v.code] = summary.get(v.code, 0) + 1
    if violations:
        _log.warning(
            "layout rhythm post-check (mode=%s) trip=%s violations=%s",
            mode,
            trip_id or "?",
            summary,
        )
        for v in violations:
            _log.info(
                "  rhythm violation: %s ch=%s screen=%s · %s",
                v.code,
                v.chapter_id,
                v.screen_index,
                v.message,
            )
    return summary, violations
