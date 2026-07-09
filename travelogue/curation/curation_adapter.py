"""Curation adapter layer — template-specific structure hints (PRD §5.3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from travelogue.config import AppConfig, get_config
from travelogue.domain.template_ids import DEFAULT_TEMPLATE_ID, EVENT_RECAP_TEMPLATE_ID


@dataclass(frozen=True)
class CurationPlan:
    template_id: str
    layout_engine: str
    min_chapters: int
    max_chapters: int
    prefer_video_highlights: bool
    screen_tone_profile: str


class CurationAdapter(Protocol):
    def plan(self, trip: dict, *, cfg: AppConfig | None) -> CurationPlan: ...


class VisualJournalCurationAdapter:
    def plan(self, trip: dict, *, cfg: AppConfig | None) -> CurationPlan:
        return CurationPlan(
            template_id=DEFAULT_TEMPLATE_ID,
            layout_engine="screens",
            min_chapters=3,
            max_chapters=5,
            prefer_video_highlights=False,
            screen_tone_profile="travel",
        )


class EventRecapCurationAdapter:
    def plan(self, trip: dict, *, cfg: AppConfig | None) -> CurationPlan:
        return CurationPlan(
            template_id=EVENT_RECAP_TEMPLATE_ID,
            layout_engine="screens",
            min_chapters=1,
            max_chapters=5,
            prefer_video_highlights=True,
            screen_tone_profile="event",
        )


_ADAPTERS: dict[str, CurationAdapter] = {
    DEFAULT_TEMPLATE_ID: VisualJournalCurationAdapter(),
    EVENT_RECAP_TEMPLATE_ID: EventRecapCurationAdapter(),
}


def resolve_effective_template(trip: dict) -> str:
    """Authoritative template id for curation hints (mirrors templating.resolver)."""
    sel = trip.get("templateSelection") or {}
    resolved = sel.get("resolvedTemplateId")
    if isinstance(resolved, str) and resolved.strip():
        return resolved.strip()
    legacy = trip.get("templateId")
    if isinstance(legacy, str) and legacy.strip():
        return legacy.strip()
    return DEFAULT_TEMPLATE_ID


def get_curation_adapter(template_id: str) -> CurationAdapter:
    return _ADAPTERS.get(template_id) or _ADAPTERS[DEFAULT_TEMPLATE_ID]


def apply_curation_adapter_hints(trip: dict, *, cfg: AppConfig | None = None) -> CurationPlan:
    """Write template-specific curation hints before run_curate."""
    tid = resolve_effective_template(trip)
    plan = get_curation_adapter(tid).plan(trip, cfg=cfg or get_config())
    hints = trip.setdefault("curation", {}).setdefault("templateHints", {})
    hints.update(
        {
            "templateId": plan.template_id,
            "layoutEngine": plan.layout_engine,
            "minChapters": plan.min_chapters,
            "maxChapters": plan.max_chapters,
            "preferVideoHighlights": plan.prefer_video_highlights,
            "screenToneProfile": plan.screen_tone_profile,
        }
    )
    return plan
