"""Hard constraints for layout search (V2 PRD §5)."""

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


def _slot_asset_ids(screen: dict) -> list[str]:
    return [s["assetId"] for s in (screen.get("slots") or []) if s.get("assetId")]


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
) -> list[LayoutConstraintViolation]:
    violations: list[LayoutConstraintViolation] = []
    violations.extend(check_no_duplicate_assets(chapters))
    violations.extend(check_cover_not_in_screens(chapters, cover_asset_id))
    if check_focal_edges and assets_by_id:
        violations.extend(check_focal_not_at_edge(chapters, assets_by_id))
    return violations


def layout_is_valid(chapters: list[dict], **kwargs: Any) -> bool:
    return not validate_chapter_layout(chapters, **kwargs)
