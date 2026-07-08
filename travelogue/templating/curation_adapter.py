"""Curation adapter layer (templating re-export shim · M-B1)."""

from travelogue.curation.curation_adapter import (  # noqa: F401
    CurationPlan,
    apply_curation_adapter_hints,
    get_curation_adapter,
    resolve_effective_template,
)

__all__ = [
    "CurationPlan",
    "apply_curation_adapter_hints",
    "get_curation_adapter",
    "resolve_effective_template",
]
