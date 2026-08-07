"""Minimal placement_score (PRD §6.2 · D-CAL-13).

不假设现网已有 ``textSafe``/``typeTheme`` API；自建最小信号集：
留白代理（局部亮度方差）、人脸 IoU 惩罚（无检测器可用则跳过该项）、
遮挡主体显著区比例（阈值 35%）。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image, ImageStat

from travelogue.cover_engine.title_art.whitelist import PlacementPreset

_OVERLAP_THRESHOLD = 0.35
_VARIANCE_NORM = 60.0
_FACE_PENALTY_WEIGHT = 0.6

DetectFacesFn = Callable[[Image.Image], list[tuple[int, int, int, int]]]


@dataclass(frozen=True)
class PlacementCandidate:
    box: tuple[int, int, int, int]  # x, y, w, h 像素坐标
    score: float
    explain: list[str]
    #: 命中的候选来源（D-CAL-20 优先顺位⑤ 多候选打分）。调用方（engine.py）
    #: 需要知道具体是哪一个 preset 赢了打分，才能读取它自己的
    #: ``assume_dark_veil``/``conditional_occupant`` 等每候选独立的字段——
    #: 不能假设永远是列表里的第一个。
    preset: PlacementPreset


def _brightness_variance(img: Image.Image, box: tuple[int, int, int, int]) -> float:
    x, y, w, h = box
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(img.width, x + w), min(img.height, y + h)
    if x1 <= x0 or y1 <= y0:
        return 0.0
    crop = img.convert("L").crop((x0, y0, x1, y1))
    stat = ImageStat.Stat(crop)
    return float(stat.stddev[0]) if stat.stddev else 0.0


def _iou(box: tuple[int, int, int, int], other: tuple[int, int, int, int]) -> float:
    bx, by, bw, bh = box
    ox, oy, ow, oh = other
    ix1, iy1 = max(bx, ox), max(by, oy)
    ix2, iy2 = min(bx + bw, ox + ow), min(by + bh, oy + oh)
    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0
    inter = (ix2 - ix1) * (iy2 - iy1)
    union = bw * bh + ow * oh - inter
    return inter / union if union > 0 else 0.0


def score_candidate(
    img: Image.Image,
    preset: PlacementPreset,
    *,
    faces: list[tuple[int, int, int, int]] | None = None,
) -> PlacementCandidate:
    w, h = img.size
    box = (
        int(preset.rect["x"] * w),
        int(preset.rect["y"] * h),
        int(preset.rect["w"] * w),
        int(preset.rect["h"] * h),
    )
    explain: list[str] = [f"{preset.opening_style_id} 白名单 · {preset.label}"]

    variance = _brightness_variance(img, box)
    openness = max(0.0, 1.0 - min(variance, _VARIANCE_NORM) / _VARIANCE_NORM)

    penalty = 0.0
    if faces:
        best_iou = max((_iou(box, f) for f in faces), default=0.0)
        if best_iou > 0:
            penalty += best_iou * _FACE_PENALTY_WEIGHT
            explain.append(f"人脸重叠惩罚 {best_iou:.2f}")
    else:
        explain.append("未检测到人脸 · 跳过该项")

    overlap_ratio = (box[2] * box[3]) / max(1, w * h)
    if overlap_ratio > _OVERLAP_THRESHOLD:
        penalty += overlap_ratio - _OVERLAP_THRESHOLD
        explain.append(f"遮挡显著区比例 {overlap_ratio:.2f} 超阈值 {_OVERLAP_THRESHOLD}")

    score = max(0.0, openness - penalty)
    return PlacementCandidate(box=box, score=score, explain=explain, preset=preset)


def focal_conflict(asset: dict, rect: dict[str, float]) -> bool:
    """镜头焦点是否落在 ``rect``（真正用于渲染贴纸的候选框）内。

    D-CAL-20 优先顺位④ / OQ-CAL-08：``score_candidate`` 的人脸重叠惩罚依赖
    运行时人脸检测器（可能不可用/成本高），这里补一层更轻量、确定性的信号
    ——复用选图环节已经算好的 ``asset.focalPoint``（`travelogue.cover_engine
    .fit.focal_is_trusted`，同一套"是否为可信焦点"判定，跟 `opening
    /title_safe.py::mark_title_safe` 一致）。

    注意：``rect`` 传的是该风格 **实际用来渲染贴纸** 的 ``PlacementPreset.
    rect``，不是 registry 原始 ``text_safe_regions``——两者对 veil-footer
    并不相同（registry 唯一候选在雾带底部，跟自身面板 DOM 占位冲突，v0.5
    视觉验收后改用手工收窄过的雾带上方矩形；这层冲突是布局占位问题，
    focal 校验管不着，见 PRD OQ-CAL-08 结论修正）。这里要检查的是「实际
    贴纸框」有没有正好压在镜头主体上，跟 registry 原始候选是两件事。
    """
    from travelogue.cover_engine.fit import focal_is_trusted

    if not focal_is_trusted(asset):
        return False
    fp = asset.get("focalPoint") or {}
    try:
        fx = float(fp.get("x", 0.5))
        fy = float(fp.get("y", 0.45))
    except (TypeError, ValueError):
        return False
    x = float(rect.get("x", 0.0))
    y = float(rect.get("y", 0.0))
    w = float(rect.get("w", 0.0))
    h = float(rect.get("h", 0.0))
    return x <= fx <= x + w and y <= fy <= y + h


def best_placement(
    img: Image.Image,
    presets: list[PlacementPreset],
    *,
    detect_faces: DetectFacesFn | None = None,
) -> PlacementCandidate | None:
    """取最高分候选；全员不达标（分数为 0）时仍返回候选，由调用方决定是否 fail-open。"""
    faces: list[tuple[int, int, int, int]] = []
    if detect_faces is not None:
        try:
            faces = list(detect_faces(img) or [])
        except Exception:
            faces = []
    candidates = [score_candidate(img, p, faces=faces) for p in presets]
    if not candidates:
        return None
    return max(candidates, key=lambda c: c.score)
