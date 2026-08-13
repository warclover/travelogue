"""Album / EDC shared editorialRole rules (AEL L2 · AC-AEL-10/22/27).

Pure functions. Enum matches EDC: vista | portrait | detail | sequence | unused.
Group is a flag on portrait, not a sixth token (D-AEL-12 / D-AEL-28).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal

from travelogue.layout_contract.subject_tagging import is_food_asset

EditorialRole = Literal["vista", "portrait", "detail", "sequence", "unused"]

EDITORIAL_ROLES: frozenset[str] = frozenset(
    {"vista", "portrait", "detail", "sequence", "unused"}
)

# p33 中文槽标签 → 照片角色 / 槽角色（D-AEL-31）。不新增 small / main-photo。
P33_LABEL_TO_PHOTO_ROLE: dict[str, EditorialRole] = {
    "主图": "vista",
    "竖图": "portrait",
    "横图": "vista",
    "细节": "detail",
    "小图": "detail",
}
P33_LABEL_TO_SLOT_ROLE: dict[str, str] = {
    "主图": "main",
    "竖图": "portrait",
    "横图": "landscape",
    # 较小非 main；CardSlot.role 无 support token（D-AEL-31）
    "细节": "portrait",
    "小图": "portrait",
}

_GROUP_FACE_MIN = 3
_PORTRAIT_AR_MAX = 1.05
_VISTA_AR_MIN = 1.2


def _as_mapping(raw: Any) -> Mapping[str, Any] | None:
    return raw if isinstance(raw, Mapping) else None


def face_count_for_asset(asset: Mapping[str, Any] | None) -> int:
    """D-AEL-28: max(quality.faceCount, len(faces)). Both 0 → not a group."""
    if not asset:
        return 0
    n_faces = 0
    raw_faces = asset.get("faces")
    if isinstance(raw_faces, (list, tuple)):
        n_faces = len(raw_faces)
    qn = 0
    quality = _as_mapping(asset.get("quality"))
    if quality is not None:
        try:
            qn = int(quality.get("faceCount") or 0)
        except (TypeError, ValueError):
            qn = 0
    return max(qn, n_faces)


def _asset_ar(asset: Mapping[str, Any]) -> float | None:
    try:
        w = float(asset.get("nativeWidth") or asset.get("width") or 0)
        h = float(asset.get("nativeHeight") or asset.get("height") or 0)
    except (TypeError, ValueError):
        return None
    if w <= 0 or h <= 0:
        return None
    return w / h


def _has_protect(asset: Mapping[str, Any]) -> bool:
    box = _as_mapping(asset.get("protectBox"))
    if box is None:
        return False
    try:
        return float(box.get("w") or 0) > 0 and float(box.get("h") or 0) > 0
    except (TypeError, ValueError):
        return False


def translate_p33_label(label: str) -> tuple[EditorialRole, str]:
    """Map a p33 Chinese slot label. Unknown labels raise KeyError (fail-loud)."""
    key = str(label or "").strip()
    if key not in P33_LABEL_TO_PHOTO_ROLE:
        raise KeyError(f"unknown p33 label: {label!r}")
    return P33_LABEL_TO_PHOTO_ROLE[key], P33_LABEL_TO_SLOT_ROLE[key]


def editorial_role_for_asset(
    asset: Mapping[str, Any] | None,
    *,
    group_face_min: int = _GROUP_FACE_MIN,
) -> tuple[EditorialRole, bool]:
    """Return ``(editorialRole, group)``.

    Food never becomes vista (D-AEL-29). Uncertain food does not demote
    a person/vista signal — only definite food is forced to detail.
    """
    if not asset:
        return "unused", False
    quality = _as_mapping(asset.get("quality")) or {}
    if quality.get("rejected") is True or asset.get("unused") is True:
        return "unused", False

    n_faces = face_count_for_asset(asset)
    group = n_faces >= max(1, int(group_face_min))
    ar = _asset_ar(asset)
    has_person = n_faces > 0 or _has_protect(asset)
    food = is_food_asset(dict(asset))

    if food and not has_person:
        return "detail", False

    if has_person and (ar is None or ar <= _PORTRAIT_AR_MAX):
        return "portrait", group
    if has_person and group:
        return "portrait", True
    if has_person:
        return "portrait", False

    shot = str(asset.get("shotGroupId") or "").strip()
    if shot and str(asset.get("editorialHint") or "") == "sequence":
        return "sequence", False

    if ar is not None and ar >= _VISTA_AR_MIN:
        return "vista", False
    return "detail", False
