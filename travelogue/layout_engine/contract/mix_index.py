"""Bag-of-mix inverted index (TPC D-TPC-02 / D-TPC-06).

W1: build + shadow only. Candidate entry switch requires AC-TPC-12 sign-off.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Mapping

from travelogue.layout_contract.orientations import AspectKind

if TYPE_CHECKING:
    from travelogue.layout_templates.models import TemplateDef

MixKey = tuple[int, int, int]  # (L, P, S)


def aspect_to_letter(kind: AspectKind | str | None) -> str | None:
    """Map aspectKind → L/P/S (panorama→L, tall→P; unknown → None)."""
    if kind in ("landscape", "panorama"):
        return "L"
    if kind in ("portrait", "tall"):
        return "P"
    if kind == "square":
        return "S"
    return None


def mix_key_from_counts(*, landscape: int, portrait: int, square: int = 0) -> MixKey:
    return (int(landscape), int(portrait), int(square))


def mix_key_from_aspects(
    asset_ids: list[str],
    aspects: Mapping[str, AspectKind],
) -> MixKey:
    l = p = s = 0
    for aid in asset_ids:
        letter = aspect_to_letter(aspects.get(aid))
        if letter == "L":
            l += 1
        elif letter == "P":
            p += 1
        elif letter == "S":
            s += 1
    return (l, p, s)


def mix_key_from_template(template: TemplateDef) -> MixKey | None:
    """Derive bag-of-mix from template YAML mix / slot roles.

    Returns None when neither mix fields nor roles yield a usable bag.
    """
    raw_mix = (template.raw or {}).get("mix") or {}
    if isinstance(raw_mix, dict) and (
        raw_mix.get("portrait") is not None
        or raw_mix.get("landscape") is not None
        or raw_mix.get("square") is not None
    ):
        return (
            int(raw_mix.get("landscape") or 0),
            int(raw_mix.get("portrait") or 0),
            int(raw_mix.get("square") or 0),
        )
    if template.mix_landscape is not None or template.mix_portrait is not None:
        return (
            int(template.mix_landscape or 0),
            int(template.mix_portrait or 0),
            0,
        )
    # Fallback: count unambiguous slot roles (skip main/any)
    l = p = s = 0
    for slot in template.slots:
        role = str(slot.role or "").lower()
        if role in ("landscape", "panorama"):
            l += 1
        elif role in ("portrait", "tall"):
            p += 1
        elif role == "square":
            s += 1
    if l + p + s == 0:
        return None
    return (l, p, s)


def format_mix_key(key: MixKey) -> str:
    l, p, s = key
    return f"L{l}P{p}S{s}"


def build_mix_inverted_index(
    templates: Mapping[str, TemplateDef],
    *,
    statuses: frozenset[str] | None = None,
) -> dict[MixKey, list[str]]:
    """Build mix → pattern_id list (stable: pattern_id lexicographic order).

    ``statuses`` defaults to active-ish templates (excludes deprecated/retired).
    """
    allow = statuses or frozenset({"ga", "beta", "experimental"})
    buckets: dict[MixKey, list[str]] = defaultdict(list)
    for tid, tmpl in templates.items():
        status = str(tmpl.status or "").lower()
        if status not in allow:
            continue
        key = mix_key_from_template(tmpl)
        if key is None:
            continue
        buckets[key].append(str(tid))
    return {k: sorted(v) for k, v in sorted(buckets.items())}
