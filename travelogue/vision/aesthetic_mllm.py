"""AA · MLLM scoring shim (ACP W1b / D-ACP-16).

Scoring lives in ``travelogue.ai.agents.aesthetic_mllm_adapter``.
Shortlist / blend / oracle live in ``travelogue.curation.aesthetic_mllm_shortlist``.

This module re-exports scoring helpers only (no curation imports) so the
historical ``vision.aesthetic_mllm → curation.*`` reverse edges can be removed.
Call ``apply_aesthetic_mllm_scores`` / ``build_mllm_shortlist`` from curation.
"""

from __future__ import annotations

from travelogue.ai.agents.aesthetic_mllm_adapter import (
    mllm_cache_key,
    mllm_cache_path,
    score_image_with_mllm,
)

__all__ = [
    "mllm_cache_key",
    "mllm_cache_path",
    "score_image_with_mllm",
]
