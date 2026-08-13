"""Album Editorial Lab (AEL) feature flag — PRD-ALBUM-EDITORIAL-LAB-V1 L0.

Default all-off. Parent ``enabled=false`` makes nested knobs ineffective
(``effective_ael``). Unknown keys fail-loud. ``crop.face_hard_gate`` cannot
be turned off from config.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from travelogue.config.errors import ConfigError
from travelogue.config_helpers import cfg_bool, cfg_float, cfg_get, cfg_int

_ALBUM_PLATFORM = "album_spread"

_ROOT_KNOWN = frozenset({"enabled", "crop", "roles", "probes"})
_CROP_KNOWN = frozenset(
    {
        "enabled",
        "face_hard_gate",
        "faceHardGate",
        "group_face_min",
        "groupFaceMin",
        "contain_on_fail",
        "containOnFail",
        "max_solve_ms",
        "maxSolveMs",
    }
)
_ROLES_KNOWN = frozenset({"enabled", "cluster_soft", "clusterSoft"})
_PROBES_KNOWN = frozenset(
    {
        "enabled",
        "max_per_spread",
        "maxPerSpread",
        "max_share",
        "maxShare",
        "allowlist",
    }
)


def _reject_unknown(raw: dict[str, Any], known: frozenset[str], *, path: str) -> None:
    extra = sorted(str(k) for k in raw if str(k) not in known)
    if extra:
        raise ConfigError(f"{path} unknown keys (fail-loud): " + ", ".join(extra))


def _as_id_tuple(raw: Any) -> tuple[str, ...]:
    if raw is None:
        return ()
    if isinstance(raw, str):
        token = raw.strip()
        return (token,) if token else ()
    if isinstance(raw, (list, tuple)):
        return tuple(str(x).strip() for x in raw if str(x).strip())
    raise ConfigError("album_editorial_lab.probes.allowlist must be a list of template ids")


@dataclass
class AlbumEditorialCropConfig:
    enabled: bool = False
    face_hard_gate: bool = True
    group_face_min: int = 3
    contain_on_fail: bool = True
    max_solve_ms: int = 8000


@dataclass
class AlbumEditorialRolesConfig:
    enabled: bool = False
    cluster_soft: bool = True


@dataclass
class AlbumEditorialProbesConfig:
    enabled: bool = False
    max_per_spread: int = 1
    max_share: float = 0.20
    allowlist: tuple[str, ...] = ()


@dataclass
class AlbumEditorialLabConfig:
    enabled: bool = False
    crop: AlbumEditorialCropConfig = field(default_factory=AlbumEditorialCropConfig)
    roles: AlbumEditorialRolesConfig = field(default_factory=AlbumEditorialRolesConfig)
    probes: AlbumEditorialProbesConfig = field(default_factory=AlbumEditorialProbesConfig)


@dataclass(frozen=True)
class EffectiveAel:
    """Resolved AEL knobs for one export call. Non-album and parent-off → all false."""

    enabled: bool = False
    crop: bool = False
    roles: bool = False
    probes: bool = False
    contain_on_fail: bool = True
    group_face_min: int = 3
    max_solve_ms: int = 8000
    face_hard_gate: bool = True
    cluster_soft: bool = True
    max_per_spread: int = 1
    max_share: float = 0.20
    allowlist: tuple[str, ...] = ()


def _crop_from_dict(raw: dict[str, Any]) -> AlbumEditorialCropConfig:
    _reject_unknown(raw, _CROP_KNOWN, path="album_editorial_lab.crop")
    if "face_hard_gate" in raw or "faceHardGate" in raw:
        if not cfg_bool(raw, "face_hard_gate", "faceHardGate", True):
            raise ConfigError(
                "album_editorial_lab.crop.face_hard_gate cannot be false (D-AEL-17)"
            )
    group_face_min = max(1, cfg_int(raw, "group_face_min", "groupFaceMin", 3))
    max_solve_ms = max(0, cfg_int(raw, "max_solve_ms", "maxSolveMs", 8000))
    return AlbumEditorialCropConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        face_hard_gate=True,
        group_face_min=group_face_min,
        contain_on_fail=cfg_bool(raw, "contain_on_fail", "containOnFail", True),
        max_solve_ms=max_solve_ms,
    )


def _roles_from_dict(raw: dict[str, Any]) -> AlbumEditorialRolesConfig:
    _reject_unknown(raw, _ROLES_KNOWN, path="album_editorial_lab.roles")
    return AlbumEditorialRolesConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        cluster_soft=cfg_bool(raw, "cluster_soft", "clusterSoft", True),
    )


def _probes_from_dict(raw: dict[str, Any]) -> AlbumEditorialProbesConfig:
    _reject_unknown(raw, _PROBES_KNOWN, path="album_editorial_lab.probes")
    max_share = cfg_float(raw, "max_share", "maxShare", 0.20)
    if max_share < 0.0 or max_share > 1.0:
        raise ConfigError("album_editorial_lab.probes.max_share must be in [0, 1]")
    return AlbumEditorialProbesConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        max_per_spread=max(0, cfg_int(raw, "max_per_spread", "maxPerSpread", 1)),
        max_share=max_share,
        allowlist=_as_id_tuple(cfg_get(raw, "allowlist", "allowlist", ())),
    )


def album_editorial_lab_from_dict(raw: dict[str, Any] | None) -> AlbumEditorialLabConfig:
    raw = raw or {}
    _reject_unknown(raw, _ROOT_KNOWN, path="album_editorial_lab")
    crop_raw = raw.get("crop") if isinstance(raw.get("crop"), dict) else {}
    roles_raw = raw.get("roles") if isinstance(raw.get("roles"), dict) else {}
    probes_raw = raw.get("probes") if isinstance(raw.get("probes"), dict) else {}
    return AlbumEditorialLabConfig(
        enabled=cfg_bool(raw, "enabled", "enabled", False),
        crop=_crop_from_dict(crop_raw),
        roles=_roles_from_dict(roles_raw),
        probes=_probes_from_dict(probes_raw),
    )


def _lab_from(cfg: Any) -> AlbumEditorialLabConfig | None:
    if cfg is None:
        return None
    if isinstance(cfg, AlbumEditorialLabConfig):
        return cfg
    lab = getattr(cfg, "album_editorial_lab", None)
    return lab if isinstance(lab, AlbumEditorialLabConfig) else None


def effective_ael(cfg: Any | None, platform: str) -> EffectiveAel:
    """Resolve AEL for one platform. L0: callers must not change plan/render."""
    off = EffectiveAel()
    if str(platform or "").strip() != _ALBUM_PLATFORM:
        return off
    lab = _lab_from(cfg)
    if lab is None or not lab.enabled:
        return off
    return EffectiveAel(
        enabled=True,
        crop=bool(lab.crop.enabled),
        roles=bool(lab.roles.enabled),
        probes=bool(lab.probes.enabled),
        contain_on_fail=bool(lab.crop.contain_on_fail),
        group_face_min=int(lab.crop.group_face_min),
        max_solve_ms=int(lab.crop.max_solve_ms),
        face_hard_gate=True,
        cluster_soft=bool(lab.roles.cluster_soft),
        max_per_spread=int(lab.probes.max_per_spread),
        max_share=float(lab.probes.max_share),
        allowlist=tuple(lab.probes.allowlist),
    )
