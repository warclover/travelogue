"""Config change dual-approval (PRD §9.1)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from travelogue.templating.admin_store import _LOCK, _load_unlocked, _save_unlocked, append_audit


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def propose_router_change(
    patch: dict[str, Any],
    *,
    operator: str,
    reason: str = "",
) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        pending = data.setdefault("runtime", {}).setdefault("pendingConfigChanges", [])
        req = {
            "id": f"cfg-{len(pending) + 1}",
            "at": _utc_now(),
            "operator": operator,
            "patch": patch,
            "reason": reason,
            "approvals": [],
            "status": "pending",
        }
        pending.append(req)
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(data)
    append_audit("config_propose", operator=operator, template_id="*", detail=req)
    return req


def approve_router_change(
    change_id: str,
    *,
    approver: str,
) -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        runtime = data.setdefault("runtime", {})
        pending = list(runtime.get("pendingConfigChanges") or [])
        target = None
        for item in pending:
            if item.get("id") == change_id:
                target = item
                break
        if target is None:
            raise ValueError("E_CONFIG_CHANGE_NOT_FOUND")
        if approver == str(target.get("operator") or "").strip():
            raise ValueError("E_CONFIG_APPROVER_SAME_AS_OPERATOR")
        approvals = list(target.get("approvals") or [])
        if approver in approvals:
            raise ValueError("E_CONFIG_APPROVER_DUPLICATE")
        approvals.append(approver)
        target["approvals"] = approvals
        if len(approvals) >= 2:
            target["status"] = "approved"
            runtime.setdefault("configHistory", []).append(
                {"at": _utc_now(), "patch": target.get("patch"), "approvers": approvals}
            )
            patch = target.get("patch") or {}
            if "template_router_enabled" in patch:
                runtime["template_router_enabled"] = patch["template_router_enabled"]
            if "allowed_templates" in patch:
                runtime["allowed_templates"] = patch["allowed_templates"]
            if "traffic_percent" in patch:
                runtime["traffic_percent"] = patch["traffic_percent"]
            if "recommended_templates" in patch:
                runtime["recommended_templates"] = patch["recommended_templates"]
            pending = [p for p in pending if p.get("id") != change_id]
        runtime["pendingConfigChanges"] = pending
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(data)
    append_audit(
        "config_approve",
        operator=approver,
        template_id="*",
        detail={"changeId": change_id, "status": target.get("status")},
    )
    return target
