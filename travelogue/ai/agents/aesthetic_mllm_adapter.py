"""Aesthetic MLLM scoring adapter · ACP M4 / D-ACP-16.

Pure vision-LLM call path only. Shortlist / blend / oracle live in
``travelogue.curation.aesthetic_mllm_shortlist`` (must not import curation here).
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.ai.budget import budget_for_trip
from travelogue.ai.gate import acp_instrumentation_active, check_gate
from travelogue.ai.telemetry import AgentCallRecord, record_agent_call, timed_call
from travelogue.config import AestheticMllmConfig
from travelogue.llm.client import parse_json_content, resolve_llm_runtime, vision_chat_completion
from travelogue.llm.errors import LlmError

_log = logging.getLogger(__name__)

AGENT = "aesthetic_mllm"
_MLLM_CACHE_FILE = "aesthetic-mllm.json"

_UNIVERSAL_RUBRIC = (
    "你是旅行相册选片助手。按「通用大众审美」评价照片是否适合作为旅行回忆的代表作。"
    "关注：主体是否清晰、情绪/瞬间是否打动人、构图与光线是否舒服、是否值得重点展示。"
    "忽略：过度修图偏好、小众艺术风格偏好。"
)

_PURPOSE_LABELS = {
    "cover": "封面",
    "hero": "主视觉 hero",
    "moment": "决定性瞬间",
}


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def mllm_cache_path(trip_dir: Path) -> Path:
    return trip_dir / "cache" / _MLLM_CACHE_FILE


def mllm_cache_key(asset: dict, *, model: str, rubric: str) -> str:
    sig = str(asset.get("contentSig") or "").strip()
    if sig:
        return f"mllm|sig:{sig}|model:{model}|rubric:{rubric}"
    rel = str(asset.get("displayFile") or asset.get("sourceFile") or asset.get("id") or "")
    return f"mllm|rel:{rel}|model:{model}|rubric:{rubric}"


def _asset_image_path(asset: dict, trip_dir: Path) -> Path | None:
    rel = str(asset.get("displayFile") or asset.get("sourceFile") or "")
    if not rel:
        return None
    path = trip_dir / rel
    return path if path.is_file() else None


def _encode_image_data_url(path: Path, *, max_edge: int) -> str:
    with Image.open(path) as img:
        rgb = img.convert("RGB")
        w, h = rgb.size
        edge = max(w, h, 1)
        if edge > max_edge:
            scale = max_edge / edge
            rgb = rgb.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        rgb.save(buf, format="JPEG", quality=85)
    b64 = base64.standard_b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{b64}"


def _parse_mllm_response(raw: dict[str, Any]) -> tuple[float, str]:
    score_raw = raw.get("score", raw.get("aestheticScore"))
    if score_raw is None:
        raise LlmError("E_MLLM_PARSE", f"missing score in {raw!r}")
    score = float(score_raw)
    if score > 1.0:
        score = score / 10.0 if score <= 10.0 else score / 100.0
    critique = str(raw.get("critique") or raw.get("comment") or "").strip()
    return _clamp01(score), critique


def _trip_id(trip: dict[str, Any] | None) -> str:
    if not isinstance(trip, dict):
        return ""
    return str(trip.get("tripId") or trip.get("id") or "")


def score_image_with_mllm(
    asset: dict,
    *,
    trip_dir: Path,
    purpose: str,
    cfg: AestheticMllmConfig,
    provider: str | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
    trip: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Score one image; returns None on fail-open paths.

    When ``ai_capability.enabled`` is True, enforces ACP gate + trip budget
    (D-ACP-14 / D-ACP-04). Default (disabled) preserves legacy MLLM semantics.
    """
    if not cfg.enabled:
        return None
    path = _asset_image_path(asset, trip_dir)
    if path is None:
        return None
    model = str(cfg.model or "qwen-vl-max")
    rubric = str(cfg.rubric or "universal")
    key = mllm_cache_key(asset, model=model, rubric=rubric)
    if cfg.cache and cache is not None and key in cache:
        hit = cache[key]
        if isinstance(hit, dict) and hit.get("score") is not None:
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT,
                    source="cache",
                    ok=True,
                    latency_ms=0.0,
                    model=model,
                    reason="cache_hit",
                    trip_id=_trip_id(trip),
                ),
            )
            return dict(hit)

    active = acp_instrumentation_active()
    if active:
        decision = check_gate()
        if not decision.allow:
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT,
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=model,
                    reason=decision.reason,
                    trip_id=_trip_id(trip),
                ),
            )
            return None
        if not budget_for_trip(_trip_id(trip)).try_consume(AGENT):
            record_agent_call(
                trip,
                AgentCallRecord(
                    agent=AGENT,
                    source="fallback",
                    ok=False,
                    latency_ms=0.0,
                    model=model,
                    reason="budget_exceeded",
                    trip_id=_trip_id(trip),
                ),
            )
            return None

    try:
        prov = provider or cfg.provider or "dashscope"
        rt = resolve_llm_runtime(prov)
        data_url = _encode_image_data_url(path, max_edge=int(cfg.image_max_edge))
        purpose_label = _PURPOSE_LABELS.get(purpose, purpose)
        system = _UNIVERSAL_RUBRIC + " 只输出 JSON：{\"score\": 0-1, \"critique\": \"一句话\"}。"
        user_text = (
            f"用途：{purpose_label}。请给出 0~1 审美分（越高越适合重点展示）和一句中文点评。"
        )
        with timed_call() as clock:
            content = vision_chat_completion(
                [
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_text},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    },
                ],
                provider=prov,
                model=model or rt.model,
                temperature=float(cfg.temperature),
                runtime=rt,
                json_mode=True,
            )
        parsed = parse_json_content(content)
        score, critique = _parse_mllm_response(parsed)
        out = {
            "score": round(score, 4),
            "critique": critique,
            "model": model,
            "purpose": purpose,
        }
        if cfg.cache and cache is not None:
            cache[key] = out
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="llm",
                ok=True,
                latency_ms=clock.latency_ms,
                model=model,
                reason="ok",
                trip_id=_trip_id(trip),
                started_at=clock.started_at,
                finished_at=clock.finished_at,
            ),
        )
        if not active:
            budget_for_trip(_trip_id(trip)).force_count(1)
        return out
    except LlmError as exc:
        _log.warning("mllm score fail-open for %s: %s", asset.get("id"), exc)
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="llm",
                ok=False,
                latency_ms=0.0,
                model=model,
                reason="llm_error",
                trip_id=_trip_id(trip),
            ),
        )
        return None
    except Exception as exc:
        _log.warning("mllm score unexpected fail-open for %s: %s", asset.get("id"), exc)
        record_agent_call(
            trip,
            AgentCallRecord(
                agent=AGENT,
                source="llm",
                ok=False,
                latency_ms=0.0,
                model=model,
                reason="exception",
                trip_id=_trip_id(trip),
            ),
        )
        return None
