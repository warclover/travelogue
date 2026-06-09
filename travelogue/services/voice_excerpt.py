"""Trim ASR / voice transcripts for short copy slots (decorLine, caption)."""

from __future__ import annotations

import re

_FILLER_RE = re.compile(r"^(那个|嗯|啊|呃|就是|然后)+[，,]?")
_SENTENCE_SPLIT = re.compile(r"[。！？!?…]+")


def trim_voice_for_copy(text: str, *, max_chars: int = 30) -> str:
    """First meaningful clause, trimmed to max_chars (Chinese travelogue tone)."""
    raw = (text or "").strip()
    if not raw:
        return ""
    raw = _FILLER_RE.sub("", raw).strip()
    clause = _SENTENCE_SPLIT.split(raw, maxsplit=1)[0].strip()
    if not clause:
        clause = raw
    if len(clause) <= max_chars:
        out = clause
    else:
        out = _truncate_clauses(clause, max_chars)
    out = out.rstrip("，,、 ")
    if not out:
        return ""
    if len(out) < max_chars and not out.endswith(("。", "！", "？")):
        if len(out) + 1 <= max_chars:
            out += "。"
    return out[:max_chars]


def _truncate_clauses(text: str, max_chars: int) -> str:
    for sep in ("，", "、", ",", "；", ";", " "):
        parts = [p.strip() for p in text.split(sep) if p.strip()]
        if len(parts) < 2:
            continue
        acc = parts[0]
        for part in parts[1:]:
            candidate = f"{acc}，{part}"
            if len(candidate) <= max_chars:
                acc = candidate
            else:
                break
        if acc:
            return acc[:max_chars]
    return text[:max_chars]
