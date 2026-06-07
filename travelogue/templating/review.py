"""Template human review workflow (PRD §5.9 · AC-P13-13)."""

from __future__ import annotations

from typing import Any, Literal

from travelogue.templating.admin_store import (
    _LOCK,
    _load_unlocked,
    _save_unlocked,
    _utc_now,
    append_audit,
)
from travelogue.templating.admission import run_admission_check

ReviewStatus = Literal["none", "pending", "approved", "rejected"]


def get_review_status(template_id: str) -> dict[str, Any]:
    with _LOCK:
        row = dict((_load_unlocked().get("templates") or {}).get(template_id) or {})
    review = dict(row.get("review") or {})
    return {
        "templateId": template_id,
        "status": str(review.get("status") or "none"),
        "submittedAt": review.get("submittedAt"),
        "submittedBy": review.get("submittedBy"),
        "reviewedAt": review.get("reviewedAt"),
        "reviewedBy": review.get("reviewedBy"),
        "note": review.get("note"),
    }


def _admission_for_review(template_id: str) -> dict[str, Any]:
    from travelogue.layout_templates.layout_admin import is_layout_template_id

    if is_layout_template_id(template_id):
        from travelogue.layout_templates.admission import run_layout_template_admission

        return run_layout_template_admission(template_id, target="beta")
    return run_admission_check(template_id)


def submit_for_review(template_id: str, *, operator: str = "studio") -> dict[str, Any]:
    admission = _admission_for_review(template_id)
    if not admission.get("ok"):
        raise ValueError("E_TEMPLATE_ADMISSION_FAILED")
    with _LOCK:
        data = _load_unlocked()
        templates = data.setdefault("templates", {})
        row = dict(templates.get(template_id) or {})
        row["review"] = {
            "status": "pending",
            "submittedAt": _utc_now(),
            "submittedBy": operator,
            "admissionOk": True,
        }
        templates[template_id] = row
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(data)
    append_audit("review_submit", operator=operator, template_id=template_id, detail={"status": "pending"})
    from travelogue.templating.metrics import record_review_event

    record_review_event(template_id=template_id, outcome="submitted")
    return get_review_status(template_id)


def approve_review(template_id: str, *, reviewer: str, note: str = "") -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        templates = data.setdefault("templates", {})
        row = dict(templates.get(template_id) or {})
        review = dict(row.get("review") or {})
        if review.get("status") != "pending":
            raise ValueError("E_TEMPLATE_REVIEW_NOT_PENDING")
        review.update(
            {
                "status": "approved",
                "reviewedAt": _utc_now(),
                "reviewedBy": reviewer,
                "note": (note or "").strip() or None,
            }
        )
        row["review"] = review
        templates[template_id] = row
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(data)
    append_audit("review_approve", operator=reviewer, template_id=template_id, detail=review)
    from travelogue.templating.metrics import record_review_event

    record_review_event(template_id=template_id, outcome="approved")
    return get_review_status(template_id)


def reject_review(template_id: str, *, reviewer: str, reason: str = "") -> dict[str, Any]:
    with _LOCK:
        data = _load_unlocked()
        templates = data.setdefault("templates", {})
        row = dict(templates.get(template_id) or {})
        review = dict(row.get("review") or {})
        if review.get("status") != "pending":
            raise ValueError("E_TEMPLATE_REVIEW_NOT_PENDING")
        review.update(
            {
                "status": "rejected",
                "reviewedAt": _utc_now(),
                "reviewedBy": reviewer,
                "note": (reason or "").strip() or None,
            }
        )
        row["review"] = review
        templates[template_id] = row
        data["revision"] = int(data.get("revision") or 0) + 1
        _save_unlocked(data)
    append_audit("review_reject", operator=reviewer, template_id=template_id, detail=review)
    from travelogue.templating.metrics import record_review_event

    record_review_event(template_id=template_id, outcome="rejected")
    return get_review_status(template_id)


def require_review_approved_for_ga(template_id: str) -> None:
    status = get_review_status(template_id).get("status")
    if status != "approved":
        raise ValueError("E_TEMPLATE_REVIEW_REQUIRED")
