"""Template routing and admin configuration."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TemplateRouterConfig:
    """Phase 13 template routing (PRD §9)."""

    enabled: bool = True
    default_template: str = "visual-journal"
    confidence_threshold: float = 0.65
    allow_manual_override: bool = True
    allowed_templates: tuple[str, ...] = ("visual-journal", "event-recap")
    beta_allowlist_trip_ids: tuple[str, ...] = ()
    display_order: tuple[str, ...] = ("visual-journal", "event-recap")
    shadow_mode: bool = False
    discovery_sort_mode: str = "recommended"


@dataclass
class TemplateAdminConfig:
    """Template governance admin API (Phase 13)."""

    default_role_loopback: str = "template_admin"
    require_role_on_lan: bool = True
    lan_role: str = "template_operator"
    require_token_on_loopback: bool = False
    trust_client_role_header: bool = True
