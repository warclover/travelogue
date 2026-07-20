"""LTN D3 · rhythmSignOff — typography gate for L0/L1/L2 token changes.

Changing ``--rhythm-l*`` in preamble/overlays requires bumping this record
(signedBy / signedAt / note). Unit tests parse CSS and fail on silent drift.
"""

from __future__ import annotations

import re
from typing import Any

# Authoritative signed band (summit D-06 / PRD §8.1). JND may revise in-band
# only with a new sign-off row.
RHYTHM_SIGNOFF: dict[str, Any] = {
    "id": "ltn-d1-rhythm-v1",
    "signedBy": "typography",
    "signedAt": "2026-07-20",
    "note": (
        "L0≈3px; L1=clamp(10px,1.6vh,20px); L2=clamp(36px,6vh,64px); "
        "ratio ≈1:4:16. Tokens live in preamble/overlays only."
    ),
    "tokens": {
        "L0": {"cssVar": "--rhythm-l0-gap", "declared": "3px"},
        "L1": {
            "cssVar": "--rhythm-l1-gap",
            "declared": "clamp(10px, 1.6vh, 20px)",
        },
        "L2": {
            "cssVar": "--rhythm-l2-gap",
            "declared": "clamp(36px, 6vh, 64px)",
        },
    },
}

_TOKEN_RE = re.compile(
    r"(--rhythm-l[012]-gap)\s*:\s*([^;]+);",
    re.IGNORECASE,
)


def _norm_css_value(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip()).lower()


def extract_rhythm_token_decls(css_text: str) -> dict[str, str]:
    """First declaration wins per cssVar (preamble + overlays usually match)."""
    found: dict[str, str] = {}
    for m in _TOKEN_RE.finditer(css_text or ""):
        var = m.group(1).strip().lower()
        if var not in found:
            found[var] = m.group(2).strip()
    return found


def verify_rhythm_signoff(
    css_text: str,
    *,
    signoff: dict[str, Any] | None = None,
) -> list[str]:
    """Return human-readable mismatch messages (empty = OK)."""
    so = signoff or RHYTHM_SIGNOFF
    errors: list[str] = []
    if not str(so.get("signedBy") or "").strip():
        errors.append("rhythmSignOff.signedBy missing")
    if not str(so.get("signedAt") or "").strip():
        errors.append("rhythmSignOff.signedAt missing")
    decls = extract_rhythm_token_decls(css_text)
    tokens = so.get("tokens") if isinstance(so.get("tokens"), dict) else {}
    for _level, meta in tokens.items():
        if not isinstance(meta, dict):
            continue
        var = str(meta.get("cssVar") or "").strip().lower()
        expected = str(meta.get("declared") or "").strip()
        if not var or not expected:
            errors.append(f"rhythmSignOff token incomplete: {_level}")
            continue
        actual = decls.get(var)
        if actual is None:
            errors.append(f"CSS missing {var} (signoff {_level})")
            continue
        if _norm_css_value(actual) != _norm_css_value(expected):
            errors.append(
                f"{var} drifted: css={actual!r} signoff={expected!r} "
                f"(bump RHYTHM_SIGNOFF id/signedAt after typography review)"
            )
    return errors


def rhythm_signoff_ok(css_text: str, *, signoff: dict[str, Any] | None = None) -> bool:
    return not verify_rhythm_signoff(css_text, signoff=signoff)
