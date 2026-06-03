"""Template decision summary for Studio API responses (Phase 13)."""

from __future__ import annotations

from typing import Any

from travelogue.templating.resolver import is_template_locked, resolve_effective_template
from travelogue.templating.router import template_user_feedback

_SOURCE_LABELS = {
    "smart": "智能匹配",
    "manual": "手动指定",
    "fallback": "回退默认",
    "legacy": "默认模板",
}


def template_source_kind(trip: dict) -> str:
    sel = trip.get("templateSelection") or {}
    if not sel:
        return "legacy"
    if sel.get("fallbackUsed"):
        return "fallback"
    mode = sel.get("mode")
    if mode == "manual":
        return "manual"
    if mode == "smart":
        return "smart"
    return "legacy"


def build_template_summary(trip: dict) -> dict[str, Any]:
    sel = trip.get("templateSelection") or {}
    tid = resolve_effective_template(trip)
    kind = template_source_kind(trip)
    feedback = template_user_feedback(sel) if sel else {
        "kind": "legacy",
        "message": "视觉游记（历史项目）",
        "templateId": tid,
    }
    return {
        "resolvedTemplateId": tid,
        "source": kind,
        "sourceLabel": _SOURCE_LABELS.get(kind, kind),
        "locked": is_template_locked(trip),
        "mode": sel.get("mode"),
        "fallbackUsed": bool(sel.get("fallbackUsed")),
        "confidence": sel.get("confidence"),
        "reasonCodes": list(sel.get("reasonCodes") or []),
        "decisionHash": sel.get("decisionHash"),
        "feedbackMessage": feedback.get("message", ""),
    }
