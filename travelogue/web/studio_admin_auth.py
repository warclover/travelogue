"""Studio template-admin API access (token + role, Phase 13 hardening)."""

from __future__ import annotations

from travelogue.config import AppConfig
from travelogue.web.studio_auth import studio_post_authorized
from travelogue.web.studio_errors import user_message
from travelogue.web.studio_handlers.protocols import StudioHandlerProtocol


def studio_authenticated(handler: StudioHandlerProtocol) -> bool:
    return studio_post_authorized(
        host=handler.studio_host,
        token=handler.studio_token,
        headers=handler.headers,
        allow_lan=handler.studio_allow_lan,
    )


def admin_api_requires_studio_token(handler: StudioHandlerProtocol, cfg: AppConfig) -> bool:
    return bool(handler.studio_allow_lan or cfg.template_admin.require_token_on_loopback)


def require_admin_api_access(handler: StudioHandlerProtocol, cfg: AppConfig) -> bool:
    """Token gate for template admin JSON API (GET/POST). Returns False after 401 response."""
    if not admin_api_requires_studio_token(handler, cfg):
        return True
    if studio_authenticated(handler):
        return True
    handler._json_response(
        401,
        {
            "ok": False,
            "error": "E_STUDIO_AUTH",
            "message": user_message("E_STUDIO_AUTH"),
        },
    )
    return False
