"""Persisted template admin overrides + audit trail (Phase 13 · M50-W3)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from typing import Any

from travelogue.domain.template_admin_state import STATE_PATH as _STATE_PATH
from travelogue.templating.lifecycle import TemplateLifecycle, assert_transition

_LOCK = threading.Lock()
_HIGH_RISK_TARGETS = frozenset({"disabled", "deprecated"})

# mtime-keyed cache for the read-only runtime overrides block. The curate
# scoring hot path calls load_runtime() once per candidate; without this it
# re-reads + re-parses the state JSON from disk on every call.
_RUNTIME_CACHE: tuple[float, dict[str, Any]] | None = None


class AdminRevisionConflict(Exception):
    code = "E_TEMPLATE_REVISION_CONFLICT"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _load_unlocked() -> dict[str, Any]:
    if not _STATE_PATH.is_file():
        return {"revision": 0, "templates": {}, "audit": [], "runtime": {}}
    try:
        data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"revision": 0, "templates": {}, "audit": []}
    if not isinstance(data, dict):
        return {"revision": 0, "templates": {}, "audit": []}
    data.setdefault("revision", 0)
    data.setdefault("templates", {})
    data.setdefault("audit", [])
    data.setdefault("runtime", {})
    return data


def _save_unlocked(data: dict[str, Any]) -> None:
    global _RUNTIME_CACHE
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = _STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(_STATE_PATH)
    _RUNTIME_CACHE = None  # in-process writes invalidate the read cache


def load_runtime() -> dict[str, Any]:
    """Return runtime overrides, cached by state-file mtime (read-only)."""
    global _RUNTIME_CACHE
    with _LOCK:
        try:
            mtime = _STATE_PATH.stat().st_mtime
        except OSError:
            mtime = -1.0
        cache = _RUNTIME_CACHE
        if cache is not None and cache[0] == mtime:
            return dict(cache[1])
        runtime = dict(_load_unlocked().get("runtime") or {})
        _RUNTIME_CACHE = (mtime, runtime)
        return dict(runtime)


def list_audit(*, limit: int = 50) -> list[dict[str, Any]]:
    with _LOCK:
        audit = list(_load_unlocked().get("audit") or [])
    return audit[-max(1, min(limit, 500)) :]


def apply_rollback(
    level: str,
    *,
    template_id: str | None = None,
    operator: str = "studio",
    confirm_high_risk: bool = False,
) -> dict[str, Any]:
    if level in ("L2", "L3") and not confirm_high_risk:
        raise ValueError("E_TEMPLATE_CONFIRM_REQUIRED")

    with _LOCK:
        data = _load_unlocked()
        runtime = dict(data.get("runtime") or {})
        if level == "L1":
            runtime["template_router_enabled"] = False
        elif level == "L2":
            if not template_id:
                raise ValueError("templateId required for L2")
            templates = data.setdefault("templates", {})
            row = dict(templates.get(template_id) or {})
            row["lifecycle"] = "disabled"
            row["updatedAt"] = _utc_now()
            row["updatedBy"] = operator
            templates[template_id] = row
        elif level == "L3":
            runtime["template_router_enabled"] = False
            runtime["allowed_templates"] = ["visual-journal"]
        else:
            raise ValueError(f"unknown rollback level: {level}")

        data["runtime"] = runtime
        data["revision"] = int(data.get("revision") or 0) + 1
        data.setdefault("audit", []).append(
            {
                "at": _utc_now(),
                "action": "rollback",
                "operator": operator,
                "templateId": template_id or "*",
                "detail": {"level": level, "runtime": runtime},
            }
        )
        _save_unlocked(data)
    from travelogue.templating.metrics import record_admin_rollback

    record_admin_rollback(level=level, operator=operator, template_id=template_id)
    return {"revision": data["revision"], "runtime": runtime}


def get_store_revision() -> int:
    with _LOCK:
        return int(_load_unlocked().get("revision") or 0)


def get_template_admin_row(template_id: str) -> dict[str, Any]:
    with _LOCK:
        return dict((_load_unlocked().get("templates") or {}).get(template_id) or {})


def get_effective_lifecycle(template_id: str, *, default: TemplateLifecycle) -> TemplateLifecycle:
    with _LOCK:
        row = (_load_unlocked().get("templates") or {}).get(template_id) or {}
    lc = row.get("lifecycle")
    if lc in ("experimental", "beta", "ga", "deprecated", "disabled"):
        return lc  # type: ignore[return-value]
    return default


def append_audit(action: str, *, operator: str, template_id: str, detail: dict[str, Any]) -> None:
    with _LOCK:
        data = _load_unlocked()
        audit = data.setdefault("audit", [])
        audit.append(
            {
                "at": _utc_now(),
                "action": action,
                "operator": operator,
                "templateId": template_id,
                "detail": detail,
            }
        )
        if len(audit) > 500:
            data["audit"] = audit[-500:]
        _save_unlocked(data)


def update_template_lifecycle(
    template_id: str,
    target: TemplateLifecycle,
    *,
    current: TemplateLifecycle,
    expected_revision: int | None,
    operator: str = "studio",
    confirm_high_risk: bool = False,
) -> dict[str, Any]:
    assert_transition(current, target)
    if target in _HIGH_RISK_TARGETS and not confirm_high_risk:
        raise ValueError("E_TEMPLATE_CONFIRM_REQUIRED")

    with _LOCK:
        data = _load_unlocked()
        rev = int(data.get("revision") or 0)
        if expected_revision is not None and expected_revision != rev:
            raise AdminRevisionConflict(f"revision mismatch: expected {expected_revision}, got {rev}")

        templates = data.setdefault("templates", {})
        row = dict(templates.get(template_id) or {})
        row["lifecycle"] = target
        row["updatedAt"] = _utc_now()
        row["updatedBy"] = operator
        templates[template_id] = row
        data["revision"] = rev + 1
        audit = data.setdefault("audit", [])
        from travelogue.templates.registry import get_registry

        reg = get_registry()
        try:
            rec = reg.get(template_id)
            registry_version = reg.version
            template_version = rec.version
        except Exception:
            registry_version = None
            template_version = None
        audit.append(
            {
                "at": _utc_now(),
                "action": "lifecycle_update",
                "operator": operator,
                "templateId": template_id,
                "detail": {
                    "from": current,
                    "to": target,
                    "registryVersion": registry_version,
                    "templateVersion": template_version,
                },
            }
        )
        if len(audit) > 500:
            data["audit"] = audit[-500:]
        _save_unlocked(data)
    if target in _HIGH_RISK_TARGETS and confirm_high_risk:
        from travelogue.templating.metrics import record_high_risk_action

        record_high_risk_action(
            action="lifecycle_update",
            operator=operator,
            template_id=template_id,
        )
    return {"revision": data["revision"], "template": row}
