"""Ingest-time WebP width selection (worker-safe; no ingest/curation imports)."""

from __future__ import annotations

from travelogue.config import IngestConfig


def effective_ingest_widths(cfg: IngestConfig, *, deferred: bool) -> tuple[int, ...]:
    """Widths written during ingest."""
    full = tuple(int(w) for w in (cfg.webp_widths or (800, 1600)))
    if not deferred:
        return full
    ingest = tuple(int(w) for w in (cfg.webp_ingest_widths or (800, 1600)))
    allowed = set(full)
    filtered = tuple(w for w in sorted(ingest) if w in allowed)
    return filtered or full[: min(2, len(full))]
