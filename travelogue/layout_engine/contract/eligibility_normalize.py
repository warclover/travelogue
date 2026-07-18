"""Single-source eligibility spec normalization (AC-TPC-18).

Eligibility specs arrive from YAML in either camelCase (``maxHeroAreaAtRef``) or
snake_case (``max_hero_area_at_ref``). Historically every reader accepted both
spellings inline, which duplicated the key knowledge across evaluator/validator.
``normalize_eligibility_spec`` is the one place that canonicalizes to camelCase
(recursively, so nested ``photoCountScale`` is normalized too) — downstream code
reads a single spelling.
"""

from __future__ import annotations

from typing import Any


def _camelize_key(key: str) -> str:
    """snake_case → camelCase; already-camel keys pass through unchanged."""
    if "_" not in key:
        return key
    head, *rest = key.split("_")
    return head + "".join(word[:1].upper() + word[1:] for word in rest)


def normalize_eligibility_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Return a camelCase copy of ``spec`` (recursing into nested dicts).

    Non-dict input yields an empty dict so callers can treat the result as a
    plain mapping without extra guards.
    """
    if not isinstance(spec, dict):
        return {}
    out: dict[str, Any] = {}
    for raw_key, value in spec.items():
        key = _camelize_key(str(raw_key))
        if isinstance(value, dict):
            out[key] = normalize_eligibility_spec(value)
        else:
            out[key] = value
    return out
