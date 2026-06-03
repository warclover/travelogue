"""Template admin role checks (Phase 13 · M50-3e)."""

from __future__ import annotations

from typing import Literal

from travelogue.config import AppConfig, get_config
from travelogue.web.studio_auth import is_loopback_host

TemplateRole = Literal["viewer", "template_operator", "template_admin"]

_ROLE_RANK = {"viewer": 0, "template_operator": 1, "template_admin": 2}


def resolve_template_role(
    headers,
    *,
    host: str,
    allow_lan: bool,
    cfg: AppConfig | None = None,
) -> TemplateRole:
    app = cfg or get_config()
    admin_cfg = app.template_admin
    header_role = (
        headers.get("X-Template-Role")
        or headers.get("x-template-role")
        or ""
    ).strip().lower()
    if header_role in _ROLE_RANK:
        return header_role  # type: ignore[return-value]
    if is_loopback_host(host) and not allow_lan:
        return admin_cfg.default_role_loopback  # type: ignore[return-value]
    return "viewer"


def require_template_role(
    headers,
    *,
    host: str,
    allow_lan: bool,
    minimum: TemplateRole,
    cfg: AppConfig | None = None,
) -> tuple[bool, TemplateRole, str | None]:
    role = resolve_template_role(headers, host=host, allow_lan=allow_lan, cfg=cfg)
    if _ROLE_RANK[role] >= _ROLE_RANK[minimum]:
        return True, role, None
    from travelogue.templating.metrics import record_permission_denied

    record_permission_denied(minimum=minimum, role=role)
    return False, role, "E_TEMPLATE_PERMISSION_DENIED"
