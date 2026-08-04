"""Platform export profiles for Longshot 2.0 (ADR-016)."""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from travelogue.paths import resource_root

PLATFORM_PROFILES_PATH = resource_root() / "config" / "platform_profiles.yaml"

DEFAULT_PLATFORM = "wechat_chat"
# Branch B · content-balanced platforms (ADR-016). Studio UI only opens a subset via config.
PLATFORM_SEGMENT_IDS = frozenset(
    {
        "wechat_moments",
        "moments_grid",
        "poster_bric",
        "xiaohongshu",
        "album_spread",
        "instagram",
        "weibo",
        "douyin_cover",
        "custom",
    }
)
KNOWN_PLATFORM_IDS = frozenset({"wechat_chat"} | PLATFORM_SEGMENT_IDS)

# Fixed-canvas collage compose (no Playwright aspect-fit longshot)
COMPOSE_PLATFORM_IDS = frozenset({"poster_bric", "xiaohongshu", "album_spread"})

# Aspect-fit platforms (letterbox / smart_crop to fixed WxH)
ASPECT_FIT_PLATFORM_IDS = frozenset(
    {"instagram", "weibo", "douyin_cover", "custom"}
)

# Studio UI / API allow-list default (config may override). Phase A+B + compose.
PHASE_A_PLATFORMS = (
    "wechat_moments",
    "xiaohongshu",
    "poster_bric",
    "album_spread",
)
# Phase C platforms are CLI/API only — never auto-listed in Studio Popover
PHASE_C_CLI_ONLY = frozenset({"instagram", "weibo", "douyin_cover", "custom"})


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
        return self.id in PLATFORM_SEGMENT_IDS or self.segment in (
            "content_balanced",
            "photo_led",
        )

    @property
    def is_photo_led(self) -> bool:
        return self.segment == "photo_led"


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
        if allowed_platforms is not None and pid not in PHASE_C_CLI_ONLY:
            # Phase C platforms are CLI/API only — skip Studio gray-list gate
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
        # moments ignores slideCount (PRD §8.1); aspect-fit / collage validate range
        if (
            pid in ASPECT_FIT_PLATFORM_IDS or pid in ("xiaohongshu", "album_spread")
        ) and (n < profile.min_pages or n > profile.max_pages):
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


def output_canvas_size(profile: PlatformProfile) -> tuple[int, int] | None:
    """Return (width, height) for aspect-fit platforms; None for moments/chat."""
    out = profile.output or {}
    w = _coerce_int(out.get("width"))
    h = _coerce_int(out.get("height"))
    if w and h and w > 0 and h > 0:
        return int(w), int(h)
    return None


def is_single_file_output(profile: PlatformProfile) -> bool:
    out = profile.output or {}
    return bool(out.get("single_file")) or int(profile.max_pages or 1) == 1


def with_custom_output(
    profile: PlatformProfile,
    *,
    width: int | None = None,
    height: int | None = None,
    pad_mode: str | None = None,
) -> PlatformProfile:
    """Return a custom profile with overridden canvas size (CLI only)."""
    if profile.id != "custom":
        return profile
    out = dict(profile.output or {})
    if width is not None:
        out["width"] = int(width)
    if height is not None:
        out["height"] = int(height)
    w = int(out.get("width") or 1080)
    h = int(out.get("height") or 1440)
    if w < 64 or h < 64 or w > 4096 or h > 8192:
        raise PlatformProfileError(
            "E_LNG2_INVALID_CUSTOM_SIZE",
            "custom 宽高须在 64–4096 × 64–8192 之间",
        )
    out["width"] = w
    out["height"] = h
    out["aspect"] = f"{w}:{h}"
    default_pad = (pad_mode or profile.default_pad_mode or "letterbox").strip().lower()
    if default_pad not in ("letterbox", "smart_crop", "auto", ""):
        raise PlatformProfileError(
            "E_LNG2_INVALID_PAD_MODE",
            "padMode 须为 letterbox 或 smart_crop",
        )
    if default_pad in ("", "auto"):
        default_pad = "letterbox"
    return PlatformProfile(
        id=profile.id,
        label=profile.label,
        segment=profile.segment,
        capture=profile.capture,
        allow_p1=profile.allow_p1,
        target_pages=profile.target_pages,
        min_pages=profile.min_pages,
        max_pages=profile.max_pages,
        tiny_photo_max=profile.tiny_photo_max,
        sparse_photo_hint_below=profile.sparse_photo_hint_below,
        default_pad_mode=default_pad,
        naming=profile.naming,
        footer=profile.footer,
        publish_guide=profile.publish_guide,
        output=out,
        phase=profile.phase,
    )


def resolve_moments_page_count(
    *,
    photo_count: int,
    max_feasible_segments: int,
    profile: PlatformProfile | None = None,
) -> tuple[int, str]:
    """Return (N, userHint) for wechat_moments.

    ``content_balanced`` (default): target 9 contiguous segments; fewer when
    legal cut points are scarce; tiny trips may be 1–N (never pad blank pages).
    ``photo_led``: N = min(photo_count, max_pages) with discrete photo crops.
    """
    profile = profile or get_profile("wechat_moments")
    target = int(profile.target_pages or 9)
    max_pages = int(profile.max_pages or 9)
    tiny_max = int(profile.tiny_photo_max or 5)
    photos = max(0, int(photo_count))
    feasible = max(1, int(max_feasible_segments))

    if profile.is_photo_led:
        n = max(1, min(photos if photos > 0 else 1, max_pages, feasible))
        if photos > max_pages:
            hint = (
                f"已从 {photos} 张照片中选取 {n} 张完整配图（目标 {target} 张），"
                f"按编号 01→{n:02d} 选图发布。"
            )
        elif photos <= tiny_max:
            hint = (
                f"已生成 {n} 张完整照片配图。"
                "照片较少时也可改用微信群长图获得更完整阅读体验。"
            )
        else:
            hint = f"已生成 {n} 张完整照片配图，按编号 01→{n:02d} 选图发布。"
        return n, hint

    # content_balanced · contiguous longshot split (1…9)
    if feasible >= target:
        return (
            min(target, max_pages),
            f"已生成 {min(target, max_pages)} 张朋友圈配图，按编号 "
            f"01→{min(target, max_pages):02d} 选图发布 · 滑动可连读。",
        )

    n = max(1, min(feasible, max_pages))
    if photos <= tiny_max or n == 1:
        hint = (
            f"内容较少，已生成 {n} 张朋友圈配图。"
            "照片少时允许单张；也可改用微信群长图。"
        )
    elif n < target:
        hint = f"内容较少，已生成 {n} 张朋友圈配图（目标 {target} 张）· 滑动可连读。"
    else:
        hint = f"已生成 {n} 张朋友圈配图，按编号 01→{n:02d} 选图发布 · 滑动可连读。"
    return n, hint


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
    return resolve_aspect_slide_count(
        photo_count=photo_count,
        slide_count=slide_count,
        max_feasible_segments=max_feasible_segments,
        profile=profile or get_profile("xiaohongshu"),
        hint_kind="xhs",
    )


def resolve_aspect_slide_count(
    *,
    photo_count: int,
    slide_count: int | None = None,
    max_feasible_segments: int | None = None,
    profile: PlatformProfile | None = None,
    hint_kind: str = "aspect",
) -> tuple[int, str]:
    """Generic page count for aspect-fit platforms (xhs / ins / weibo / custom).

    Uses Guizang-style auto formula when slide_count is None; clamps to profile
    min/max and feasible segments. ``douyin_cover`` always returns 1.
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

    # Single-frame covers (douyin)
    if max_pages == 1 or is_single_file_output(profile):
        return 1, "已生成 1 张竖版封面"

    size = output_canvas_size(profile)
    ratio_label = "配图"
    if size:
        w, h = size
        if (w, h) == (1080, 1440):
            ratio_label = "3:4 配图"
        elif (w, h) == (1080, 1350):
            ratio_label = "4:5 配图"
        else:
            ratio_label = f"{w}×{h} 配图"

    if slide_count is not None:
        n = max(min_pages, min(int(slide_count), max_pages, feasible))
        if hint_kind == "xhs":
            hint = f"已生成 {n} 张 3:4 配图 · 更多细节可写在笔记正文"
        else:
            hint = f"已生成 {n} 张{ratio_label}"
        return n, hint

    # Guizang-calibrated auto (same as xhs §6.4.3); clamp to platform max
    n0 = max(1, int(math.ceil(photos / 4))) if photos else 1
    if photos < 12:
        n = max(min(3, max_pages), min(n0, min(6, max_pages)))
        n = max(min_pages, n)
    else:
        n = max(min(5, max_pages), min(n0, min(9, max_pages)))
        if photos > 48:
            n = min(n, min(10, max_pages))
    n = max(min_pages, min(n, max_pages, feasible))
    if hint_kind == "xhs":
        hint = f"已生成 {n} 张 3:4 配图 · 更多细节可写在笔记正文"
    else:
        hint = f"已生成 {n} 张{ratio_label}"
    return n, hint


def file_prefix_for_platform(title: str, platform_id: str) -> str:
    """Stem prefix before ``-{nn}.ext`` (e.g. ``林芝-moments``).

    ``douyin_cover`` uses ``{slug}-douyin-cover`` (single file, no nn in prefix).
    """
    from travelogue.export.longshot import _slug_title

    slug = _slug_title(title)
    if platform_id == "wechat_moments":
        return f"{slug}-moments"
    if platform_id == "moments_grid":
        return f"{slug}-moments-grid"
    if platform_id == "poster_bric":
        return f"{slug}-poster"
    if platform_id == "xiaohongshu":
        return f"{slug}-xhs"
    if platform_id == "album_spread":
        return f"{slug}-album"
    if platform_id == "instagram":
        return f"{slug}-ins"
    if platform_id == "weibo":
        return f"{slug}-weibo"
    if platform_id == "douyin_cover":
        return f"{slug}-douyin-cover"
    if platform_id == "custom":
        return f"{slug}-custom"
    return f"{slug}-{platform_id}"
