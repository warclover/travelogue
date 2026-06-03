"""Template governance lifecycle state machine (PRD §5.5)."""

from __future__ import annotations

from typing import Literal

TemplateLifecycle = Literal["experimental", "beta", "ga", "deprecated", "disabled"]

_ALLOWED_TRANSITIONS: dict[TemplateLifecycle, frozenset[TemplateLifecycle]] = {
    "experimental": frozenset({"beta", "disabled"}),
    "beta": frozenset({"ga", "experimental", "disabled"}),
    "ga": frozenset({"deprecated", "beta"}),
    "deprecated": frozenset({"disabled", "ga"}),
    "disabled": frozenset({"experimental", "beta"}),
}


class LifecycleTransitionError(ValueError):
    code = "E_TEMPLATE_LIFECYCLE"


def can_transition(current: TemplateLifecycle, target: TemplateLifecycle) -> bool:
    return target in _ALLOWED_TRANSITIONS.get(current, frozenset())


def assert_transition(current: TemplateLifecycle, target: TemplateLifecycle) -> None:
    if not can_transition(current, target):
        raise LifecycleTransitionError(
            f"invalid lifecycle transition: {current} -> {target}"
        )
