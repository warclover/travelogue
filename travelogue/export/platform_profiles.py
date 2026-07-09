"""Platform export profiles for Longshot 2.0 (ADR-016)."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from travelogue.paths import ROOT

PLATFORM_PROFILES_PATH = ROOT / "config" / "platform_profiles.yaml"

DEFAULT_PLATFORM = "wechat_chat"
PLATFORM_SEGMENT_IDS = frozenset({"wechat_moments", "xiaohongshu"})
KNOWN_PLATFORM_IDS = frozenset({"wechat_chat", "wechat_moments", "xiaohongshu"})

# Phase A UI / API gray-list default (config may override)
PHASE_A_PLATFORMS = ("wechat_moments",)


class PlatformProfileError(ValueError):
    """Invalid platform id or slideCount."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class PlatformProfile:
    id: str
    label: str
    segment: str
    capture: str
    allow_p1: bool
    target_pages: int | None = None
    min_pages: int = 1
    max_pages: int = 9
    tiny_photo_max: int = 5
    sparse_photo_hint_below: int = 15
    default_pad_mode: str = "letterbox"
    naming: str = ""
    footer: str = "{i}/{n}"
    publish_guide: str = ""
    output: dict[str, Any] = field(default_factory=dict)
    phase: str | None = None

    @property
    def is_platform_segment(self) -> bool:
        return self.id in PLATFORM_SEGMENT_IDS or self.segment == "content_balanced"


def _coerce_int(value: Any, default: int | None = None) -> int | None:
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _profile_from_raw(pid: str, raw: dict[str, Any]) -> PlatformProfile:
    output = raw.get("output") if isinstance(raw.get("output"), dict) else {}
    return PlatformProfile(
        id=pid,
        label=str(raw.get("label") or pid),
        segment=str(raw.get("segment") or "technical_chapter"),
        capture=str(raw.get("capture") or "chapter_or_full"),
        allow_p1=bool(raw.get("allow_p1", pid == DEFAULT_PLATFORM)),
        target_pages=_coerce_int(raw.get("target_pages")),
        min_pages=int(_coerce_int(raw.get("min_pages"), 1) or 1),
        max_pages=int(_coerce_int(raw.get("max_pages"), 9) or 9),
        tiny_photo_max=int(_coerce_int(raw.get("tiny_photo_max"), 5) or 5),
        sparse_photo_hint_below=int(
            _coerce_int(raw.get("sparse_photo_hint_below"), 15) or 15
        ),
        default_pad_mode=str(raw.get("default_pad_mode") or "letterbox"),
        naming=str(output.get("naming") or ""),
        footer=str(output.get("footer") or "{i}/{n}"),
        publish_guide=str(raw.get("publish_guide") or "").strip(),
        output=dict(output),
        phase=str(raw["phase"]) if raw.get("phase") is not None else None,
    )


@lru_cache(maxsize=4)
def load_platform_profiles(path: str | None = None) -> dict[str, PlatformProfile]:
    profile_path = Path(path) if path else PLATFORM_PROFILES_PATH
    if not profile_path.is_file():
        raise FileNotFoundError(f"platform profiles missing: {profile_path}")
    doc = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    platforms = doc.get("platforms") if isinstance(doc, dict) else None
    if not isinstance(platforms, dict):
        raise ValueError("platform_profiles.yaml missing platforms map")
    out: dict[str, PlatformProfile] = {}
    for pid, raw in platforms.items():
        if not isinstance(raw, dict):
            continue
        out[str(pid)] = _profile_from_raw(str(pid), raw)
    return out


def clear_platform_profiles_cache() -> None:
    load_platform_profiles.cache_clear()


def list_platform_ids(*, path: str | None = None) -> frozenset[str]:
    return frozenset(load_platform_profiles(path).keys())


def get_profile(platform_id: str, *, path: str | None = None) -> PlatformProfile:
    pid = str(platform_id or "").strip() or DEFAULT_PLATFORM
    profiles = load_platform_profiles(path)
    if pid not in profiles:
        raise PlatformProfileError(
            "E_LNG2_INVALID_PLATFORM",
            f"不支持的平台「{pid}」，请更新客户端",
        )
    return profiles[pid]


def normalize_platform_id(raw: Any) -> str:
    if raw is None or raw == "":
        return DEFAULT_PLATFORM
    return str(raw).strip()


def resolve_profile(
    platform: str | None,
    *,
    slide_count: int | None = None,
    pad_mode: str | None = None,
    path: str | None = None,
    longshot2_enabled: bool = True,
    allowed_platforms: list[str] | tuple[str, ...] | None = None,
) -> PlatformProfile:
    """Resolve and validate platform for API/CLI.

    Unknown platform → PlatformProfileError (caller maps to HTTP 400).
    When longshot2 disabled, non-chat platforms are rejected.
    """
    pid = normalize_platform_id(platform)
    profile = get_profile(pid, path=path)

    if pid != DEFAULT_PLATFORM:
        if not longshot2_enabled:
            raise PlatformProfileError(
                "E_LNG2_INVALID_PLATFORM",
                "平台导出未启用，请改用微信群长图",
            )
        if allowed_platforms is not None:
            allow = {str(x).strip() for x in allowed_platforms if str(x).strip()}
            if pid not in allow:
                raise PlatformProfileError(
                    "E_LNG2_INVALID_PLATFORM",
                    f"平台「{pid}」未在灰度列表中开放",
                )

    if slide_count is not None and pid != DEFAULT_PLATFORM:
        try:
            n = int(slide_count)
        except (TypeError, ValueError) as exc:
            raise PlatformProfileError(
                "E_LNG2_INVALID_SLIDE_COUNT",
                "slideCount 须为整数",
            ) from exc
        # moments ignores slideCount (PRD §8.1); xhs validates range
        if pid == "xiaohongshu" and (n < profile.min_pages or n > profile.max_pages):
            raise PlatformProfileError(
                "E_LNG2_INVALID_SLIDE_COUNT",
                f"slideCount 须在 {profile.min_pages}–{profile.max_pages} 之间",
            )

    if pad_mode is not None and pad_mode not in ("", "letterbox", "smart_crop", "auto"):
        raise PlatformProfileError(
            "E_LNG2_INVALID_PAD_MODE",
            "padMode 须为 letterbox 或 smart_crop",
        )

    return profile


def resolve_moments_page_count(
    *,
    photo_count: int,
    max_feasible_segments: int,
    profile: PlatformProfile | None = None,
) -> tuple[int, str]:
    """Return (N, userHint) for wechat_moments (D-LNG2-02/21/22)."""
    profile = profile or get_profile("wechat_moments")
    target = int(profile.target_pages or 9)
    min_pages = int(profile.min_pages or 6)
    max_pages = int(profile.max_pages or 9)
    tiny_max = int(profile.tiny_photo_max or 5)

    feasible = max(1, int(max_feasible_segments))
    photos = max(0, int(photo_count))

    if photos <= tiny_max:
        n = min(feasible, max(1, photos if photos > 0 else 1), max_pages)
        n = max(1, min(n, feasible))
        hint = (
            f"内容较少，已生成 {n} 张朋友圈配图。"
            "建议改用微信群长图以获得更完整阅读体验。"
        )
        return n, hint

    # Prefer target 9 when feasible; else clamp to [min_pages, max_pages] ∩ feasible
    if feasible >= target:
        return target, f"已生成 {target} 张朋友圈配图，按编号 01→{target:02d} 选图发布。"

    if feasible >= min_pages:
        n = min(feasible, max_pages)
        return n, f"内容较少，已生成 {n} 张朋友圈配图（目标 {target} 张）。"

    # Fewer than min_pages legal segments (but photos > tiny): still emit what we can
    n = max(1, min(feasible, max_pages))
    return n, f"内容较少，已生成 {n} 张朋友圈配图（目标 {target} 张）。"


def resolve_xhs_slide_count(
    *,
    photo_count: int,
    slide_count: int | None = None,
    max_feasible_segments: int | None = None,
    profile: PlatformProfile | None = None,
) -> tuple[int, str]:
    """Xiaohongshu page count · D-LNG2-31 / PRD §6.4.3.

    Returns (N, userHint). When ``slide_count`` is set, use it (clamped to profile).
    """
    import math

    profile = profile or get_profile("xiaohongshu")
    min_pages = int(profile.min_pages or 1)
    max_pages = int(profile.max_pages or 18)
    photos = max(0, int(photo_count))
    feasible = (
        max(1, int(max_feasible_segments))
        if max_feasible_segments is not None
        else max_pages
    )

    if slide_count is not None:
        n = max(min_pages, min(int(slide_count), max_pages, feasible))
        hint = f"已生成 {n} 张 3:4 配图 · 更多细节可写在笔记正文"
        return n, hint

    n0 = max(1, int(math.ceil(photos / 4))) if photos else 1
    if photos < 12:
        n = max(3, min(n0, 6))
    else:
        n = max(5, min(n0, 9))
        if photos > 48:
            n = min(n, 10)
    n = max(min_pages, min(n, max_pages, feasible))
    hint = f"已生成 {n} 张 3:4 配图 · 更多细节可写在笔记正文"
    return n, hint


def file_prefix_for_platform(title: str, platform_id: str) -> str:
    """Stem prefix before ``-{nn}.ext`` (e.g. ``林芝-moments``)."""
    from travelogue.export.longshot import _slug_title

    slug = _slug_title(title)
    if platform_id == "wechat_moments":
        return f"{slug}-moments"
    if platform_id == "xiaohongshu":
        return f"{slug}-xhs"
    return f"{slug}-{platform_id}"
