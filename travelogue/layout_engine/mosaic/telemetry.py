"""Online mosaic/layout metrics (PRD §7.1 → template-metrics.jsonl)."""

from __future__ import annotations

from collections import Counter
from typing import Any


def _emit_per_template_enabled() -> bool:
    try:
        from travelogue.config import get_config

        te = getattr(get_config().layout, "template_engine", None)
        return te is not None and bool(getattr(te, "emit_per_template", True))
    except Exception:
        return False


def _registry_version_label() -> str:
    try:
        from travelogue.config import get_config

        te = getattr(get_config().layout, "template_engine", None)
        ver = str(getattr(te, "registry_version", "") or "")
        max_len = int(getattr(te, "telemetry_registry_versions_max", 8) or 8)
        return ver[:max_len] if ver else ""
    except Exception:
        return ""


def record_mosaic_layout_metrics(
    *,
    trip_id: str | None,
    layout_metrics: dict[str, Any],
    mosaic_enabled: bool,
) -> None:
    """Append curate-time layout KPIs; never raises."""
    try:
        from travelogue.util.template_metrics import record_template_metric
    except ImportError:
        return

    labels = {"tripId": trip_id, "mosaicEnabled": mosaic_enabled}
    mapping = (
        ("layout.mosaic5.exposure_rate", "layout.mosaic5.exposure_rate"),
        ("layout.mosaic_v2.unified_exposure_rate", "layout.mosaic_v2.unified_exposure_rate"),
        ("layout.mosaic_v2.fallback_rate", "layout.mosaic_v2.fallback_rate"),
        ("layout.mosaic_v2.low_score_fallback_rate", "layout.mosaic_v2.low_score_fallback_rate"),
        ("layout.render.error_rate", "layout.render.error_rate"),
        ("layout.pattern.repeat_rate", "layout.pattern.repeat_rate"),
        ("layout.eligible_to_screen_coverage", "layout.eligible_to_screen_coverage"),
        ("layout.mosaic_v2.drop_rate", "layout.mosaic_v2.drop_rate"),
    )
    for key, metric_name in mapping:
        val = layout_metrics.get(key)
        if val is None:
            continue
        record_template_metric(metric_name, value=val, **labels)

    render_err = layout_metrics.get("layout.render.error_rate")
    if render_err is not None and mosaic_enabled:
        ok = float(render_err) == 0.0
        record_template_metric(
            "layout.mosaic_v2.render_check",
            tripId=trip_id,
            ok=ok,
            errorRate=render_err,
        )


def record_per_template_layout_metrics(
    *,
    trip_id: str | None,
    chapters: list[dict],
    mosaic_logs: list[dict] | None = None,
) -> None:
    """Emit PRD §9.1 per-template counters from curated screens and mosaic window logs."""
    if not _emit_per_template_enabled():
        return
    try:
        from travelogue.util.template_metrics import record_template_metric
    except ImportError:
        return

    reg_ver = _registry_version_label()
    base = {"tripId": trip_id}
    if reg_ver:
        base["templateRegistryVersion"] = reg_ver

    wins = Counter[str]()
    candidates = Counter[str]()
    fallbacks = Counter[str]()
    slot_ar: dict[str, list[float]] = {}
    win_scores: dict[str, list[float]] = {}
    face_crop_hits: Counter[str] = Counter()
    face_crop_wins: Counter[str] = Counter()

    for ch in chapters:
        for screen in ch.get("screens") or []:
            pid = str(screen.get("patternId") or "").strip()
            if not pid:
                continue
            wins[pid] += 1

    for entry in mosaic_logs or []:
        pid = str(entry.get("winnerPatternId") or "").strip()
        if pid:
            candidates[pid] += int(entry.get("candidatesCount") or 1)
            if entry.get("fallbackUsed"):
                fallbacks[pid] += 1
            score = entry.get("slotArMatchScore")
            if score is not None and pid:
                try:
                    slot_ar.setdefault(pid, []).append(float(score))
                except (TypeError, ValueError):
                    pass
            ws = entry.get("winnerScore")
            if ws is not None and pid and not entry.get("fallbackUsed"):
                try:
                    win_scores.setdefault(pid, []).append(float(ws))
                except (TypeError, ValueError):
                    pass
            if pid and not entry.get("fallbackUsed"):
                face_crop_wins[pid] += 1
                if entry.get("faceCropProxy"):
                    face_crop_hits[pid] += 1

    for pid, count in wins.items():
        record_template_metric(
            "layout.template.exposure_count",
            templateId=pid,
            value=count,
            **base,
        )

    total_wins = sum(wins.values()) or 1
    for pid, count in wins.items():
        record_template_metric(
            "layout.template.exposure_share",
            templateId=pid,
            value=round(count / total_wins, 4),
            **base,
        )

    for pid, count in candidates.items():
        record_template_metric(
            "layout.template.candidate_count",
            templateId=pid,
            value=count,
            **base,
        )

    for pid, count in fallbacks.items():
        record_template_metric(
            "layout.template.fallback_rate",
            templateId=pid,
            value=round(count / max(1, wins.get(pid, 1)), 4),
            **base,
        )

    for pid, scores in slot_ar.items():
        scores.sort()
        mid = scores[len(scores) // 2]
        record_template_metric(
            "layout.template.slot_ar_distance_p50",
            templateId=pid,
            value=round(mid, 4),
            **base,
        )

    def _pct(vals: list[float], p: float) -> float:
        vals = sorted(vals)
        idx = min(len(vals) - 1, max(0, int(round(p * (len(vals) - 1)))))
        return round(vals[idx], 4)

    for pid, scores in win_scores.items():
        if not scores:
            continue
        record_template_metric(
            "layout.template.win_score_p50",
            templateId=pid,
            value=_pct(scores, 0.5),
            **base,
        )
        if len(scores) >= 2:
            record_template_metric(
                "layout.template.win_score_p90",
                templateId=pid,
                value=_pct(scores, 0.9),
                **base,
            )

    for pid, win_count in face_crop_wins.items():
        if win_count <= 0:
            continue
        rate = round(face_crop_hits.get(pid, 0) / win_count, 4)
        record_template_metric(
            "layout.template.face_crop_proxy_rate",
            templateId=pid,
            value=rate,
            **base,
        )
