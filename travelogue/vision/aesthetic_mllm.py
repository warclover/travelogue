"""AA · M3 · vision LLM aesthetic scoring for high-value shortlist only."""

from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path
from typing import Any

from PIL import Image

from travelogue.config import AestheticConfig, AestheticMllmConfig
from travelogue.curation.aesthetic_blind_review import review_stratum_for_asset
from travelogue.curation.aesthetic_score import purpose_overall, refresh_aesthetic_ml_blend
from travelogue.curation.album_profile import (
    album_profile_for_trip,
    effective_priority_strata,
    stratum_preference_for_trip,
)
from travelogue.llm.client import parse_json_content, resolve_llm_runtime, vision_chat_completion
from travelogue.llm.errors import LlmError

_log = logging.getLogger(__name__)

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


def _load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _log.debug("mllm cache read skipped for %s", path, exc_info=True)
        return {}
    return raw if isinstance(raw, dict) else {}


def _save_cache(path: Path, cache: dict[str, dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


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


def score_image_with_mllm(
    asset: dict,
    *,
    trip_dir: Path,
    purpose: str,
    cfg: AestheticMllmConfig,
    provider: str | None = None,
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Score one image; returns None on fail-open paths."""
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
            return dict(hit)

    try:
        prov = provider or cfg.provider or "dashscope"
        rt = resolve_llm_runtime(prov)
        data_url = _encode_image_data_url(path, max_edge=int(cfg.image_max_edge))
        purpose_label = _PURPOSE_LABELS.get(purpose, purpose)
        system = _UNIVERSAL_RUBRIC + " 只输出 JSON：{\"score\": 0-1, \"critique\": \"一句话\"}。"
        user_text = (
            f"用途：{purpose_label}。请给出 0~1 审美分（越高越适合重点展示）和一句中文点评。"
        )
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
        return out
    except LlmError as exc:
        _log.warning("mllm score fail-open for %s: %s", asset.get("id"), exc)
        return None
    except Exception as exc:
        _log.warning("mllm score unexpected fail-open for %s: %s", asset.get("id"), exc)
        return None


def _rank_mllm_candidates(
    assets: list[dict],
    purpose: str,
    *,
    cfg: AestheticConfig,
    priority_strata: frozenset[str],
) -> list[tuple[float, dict]]:
    ranked: list[tuple[float, dict]] = []
    for asset in assets:
        if asset.get("type", "image") == "video":
            continue
        aid = str(asset.get("id") or "")
        if not aid:
            continue
        val = purpose_overall(asset, purpose, cfg=cfg)  # type: ignore[arg-type]
        if val is None:
            continue
        ranked.append((float(val), asset))

    def sort_key(t: tuple[float, dict]) -> tuple[int, float, str]:
        score, asset = t
        if priority_strata:
            stratum = review_stratum_for_asset(asset)
            in_priority = 0 if stratum in priority_strata else 1
            return (in_priority, -score, str(asset.get("id") or ""))
        return (0, -score, str(asset.get("id") or ""))

    ranked.sort(key=sort_key)
    return ranked


def build_mllm_shortlist(
    assets: list[dict],
    *,
    cfg: AestheticConfig,
    album_profile: dict | None = None,
    trip: dict | None = None,
) -> list[tuple[str, dict, str]]:
    """Return ``(asset_id, asset, purpose)`` tuples for MLLM scoring."""
    mllm = cfg.mllm
    if not mllm.enabled:
        return []
    if album_profile is None and trip is not None:
        album_profile = album_profile_for_trip(trip)
    preference = stratum_preference_for_trip(trip) if trip is not None else "auto"
    priority_strata = effective_priority_strata(album_profile, preference=preference)
    k = max(1, int(mllm.shortlist_k))
    out: list[tuple[str, dict, str]] = []
    seen: set[str] = set()
    for purpose in mllm.shortlist_purposes:
        ranked = _rank_mllm_candidates(
            assets, purpose, cfg=cfg, priority_strata=priority_strata
        )
        for _, asset in ranked[:k]:
            aid = str(asset["id"])
            if aid in seen:
                continue
            seen.add(aid)
            out.append((aid, asset, purpose))
            if len(out) >= int(mllm.max_calls_per_trip):
                return out
    return out[: int(mllm.max_calls_per_trip)]


def _write_mllm_fields(asset: dict, result: dict[str, Any]) -> None:
    q = asset.setdefault("quality", {})
    ae = q.setdefault("aesthetic", {})
    sig = ae.setdefault("signals", {})
    if isinstance(sig, dict):
        sig["mllmScore"] = float(result["score"])
        sig["mllmModel"] = str(result.get("model") or "")
        sig["mllmShortlist"] = str(result.get("purpose") or "")
    critique = result.get("critique")
    if critique:
        ae["critique"] = str(critique)


def apply_aesthetic_mllm_scores(
    assets: list[dict],
    *,
    trip_dir: Path,
    cfg: AestheticConfig | None = None,
    trip: dict | None = None,
) -> dict[str, Any]:
    """Score shortlist with vision LLM; fail-open when disabled or errors."""
    cfg = cfg or AestheticConfig()
    mllm = cfg.mllm
    report: dict[str, Any] = {
        "enabled": mllm.enabled,
        "scored": 0,
        "cached": 0,
        "failed": 0,
        "skipped": 0,
        "calls": 0,
    }
    if not mllm.enabled:
        return report

    shortlist = build_mllm_shortlist(assets, cfg=cfg, trip=trip)
    if not shortlist:
        return report

    cache_path = mllm_cache_path(trip_dir)
    cache = _load_cache(cache_path) if mllm.cache else {}
    cache_dirty = False
    provider = mllm.provider or "dashscope"

    for aid, asset, purpose in shortlist:
        key = mllm_cache_key(asset, model=str(mllm.model), rubric=str(mllm.rubric))
        if mllm.cache and key in cache:
            hit = cache[key]
            if isinstance(hit, dict) and hit.get("score") is not None:
                _write_mllm_fields(asset, hit)
                refresh_aesthetic_ml_blend(asset, cfg=cfg)
                report["cached"] += 1
                report["scored"] += 1
                continue

        report["calls"] += 1
        result = score_image_with_mllm(
            asset,
            trip_dir=trip_dir,
            purpose=purpose,
            cfg=mllm,
            provider=provider,
            cache=cache if mllm.cache else None,
        )
        if result is None:
            report["failed"] += 1
            continue
        _write_mllm_fields(asset, result)
        refresh_aesthetic_ml_blend(asset, cfg=cfg)
        report["scored"] += 1
        cache_dirty = True

    if cache_dirty and mllm.cache:
        _save_cache(cache_path, cache)
    return report


def apply_mllm_oracle_from_labels(
    assets: list[dict],
    label_rows: list[dict[str, Any]],
    *,
    cfg: AestheticConfig | None = None,
) -> dict[str, Any]:
    """Offline oracle upper-bound: human labels as ``mllmScore`` on shortlist only."""
    from travelogue.curation.aesthetic_blind_review import normalize_human_score

    cfg = cfg or AestheticConfig(mllm=AestheticMllmConfig(enabled=True))
    labels_by_id = {str(r.get("assetId") or ""): r for r in label_rows if r.get("assetId")}
    shortlist = build_mllm_shortlist(assets, cfg=cfg)
    report: dict[str, Any] = {
        "mode": "oracle-human",
        "shortlistCount": len(shortlist),
        "scored": 0,
        "missingLabel": 0,
    }
    for aid, asset, purpose in shortlist:
        row = labels_by_id.get(aid)
        if not row or row.get("humanScore") is None:
            report["missingLabel"] += 1
            continue
        try:
            score = normalize_human_score(row["humanScore"])
        except (TypeError, ValueError):
            report["missingLabel"] += 1
            continue
        _write_mllm_fields(
            asset,
            {
                "score": round(score, 4),
                "critique": "oracle from human label",
                "model": "oracle-human",
                "purpose": purpose,
            },
        )
        refresh_aesthetic_ml_blend(asset, cfg=cfg)
        report["scored"] += 1
    return report
