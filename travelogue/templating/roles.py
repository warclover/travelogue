"""Template admin role checks (Phase 13 · M50-3e)."""

from __future__ import annotations

from typing import Literal

from travelogue.config import AppConfig, get_config
from travelogue.web.studio_auth import is_loopback_host

TemplateRole = Literal["viewer", "template_operator", "template_admin"]

_ROLE_RANK = {"viewer": 0, "template_operator": 1, "template_admin": 2}


def _role_from_config_value(raw: str) -> TemplateRole | None:
    role = (raw or "").strip().lower()
    if role in _ROLE_RANK:
        return role  # type: ignore[return-value]
    return None


def resolve_template_role(
    headers,
    *,
    host: str,
    allow_lan: bool,
    cfg: AppConfig | None = None,
    studio_authenticated: bool = False,
) -> TemplateRole:
    app = cfg or get_config()
    admin_cfg = app.template_admin

    if allow_lan or admin_cfg.require_role_on_lan:
        if not studio_authenticated:
            return "viewer"
        role = _role_from_config_value(admin_cfg.lan_role)
        return role if role is not None else "template_operator"  # type: ignore[return-value]

    if admin_cfg.require_token_on_loopback and not studio_authenticated:
        return "viewer"

    if admin_cfg.trust_client_role_header:
        header_role = (
            headers.get("X-Template-Role")
            or headers.get("x-template-role")
            or ""
        ).strip().lower()
        if header_role in _ROLE_RANK:
            return header_role  # type: ignore[return-value]

    if is_loopback_host(host):
        role = _role_from_config_value(admin_cfg.default_role_loopback)
        return role if role is not None else "template_admin"  # type: ignore[return-value]
    return "viewer"


def require_template_role(
    headers,
    *,
    host: str,
    allow_lan: bool,
    minimum: TemplateRole,
    cfg: AppConfig | None = None,
    studio_authenticated: bool = False,
) -> tuple[bool, TemplateRole, str | None]:
    role = resolve_template_role(
        headers,
        host=host,
        allow_lan=allow_lan,
        cfg=cfg,
        studio_authenticated=studio_authenticated,
    )
    if _ROLE_RANK[role] >= _ROLE_RANK[minimum]:
        return True, role, None
    from travelogue.templating.metrics import record_permission_denied

    record_permission_denied(minimum=minimum, role=role)
    return False, role, "E_TEMPLATE_PERMISSION_DENIED"
