"""LTN C6 · user-facing mosaicDecisionLog explain («为何没拼»)."""

from __future__ import annotations

from typing import Any

_FALLBACK_LABELS: dict[str, str] = {
    "no_candidates": "这组照片没有可用的拼图模板",
    "low_score": "候选拼图分数偏低，未采用拼图",
    "pattern_disabled": "对应拼图模板当前未启用",
    "window_size_mismatch": "窗口张数与模板要求不一致",
    "mcs_no_winner": "拼图评分未选出胜者，已尝试其他窗宽",
    "mcs_all_sizes_failed": "多种拼图窗宽均未成功，已回落常规排版",
    "mcs_single_hero_rescue": "拼图未成，改以单张主图突出呈现",
}

_REJECT_LABELS: dict[str, str] = {
    "geometry_invalid": "版式几何不合适",
    "main_ar_ineligible": "主图画幅不适合放在主槽",
    "ordering_failed": "照片顺序无法匹配槽位角色",
    "hard_invalid": "硬性条件未通过",
    "pattern_disabled": "模板未启用",
    "contract:infeasible_mix": "横竖混排与模板要求不符",
    "contract:mix_miss": "横竖混排未命中可用模板合同",
    "atom_boundary": "跨场景原子边界，不宜拼在同一窗",
    "shot_group_cross": "跨分镜硬边界，拼在一起会像切条",
    "shot_group_anti_slice": "同分镜过密，该模板易呈切条感",
    "near_scene_clone": "同场景过近/近似连拍，未做成切条拼图",
    "ega_clone_soft": "同场景偏近，等权宫软降权后仍可参与比分",
    "main_ar_mismatch": "主图画幅与主槽不匹配",
    "sidebar_min_short_side": "侧栏短边过窄，版式不成立",
    "mixed_portrait_is_hero": "竖图更适合主图，当前模板已排除",
    "mixed_routing:mixed_portrait_is_hero": "竖图更适合主图，当前模板已排除",
}

_SOURCE_LABELS: dict[str, str] = {
    "exact": "模板合约精确命中",
    "fallback": "模板合约回落",
    "signature": "签名路由直接命中",
    "signature_fallback": "签名未命中，已回落全量模板库",
    "legacy_size": "按窗宽全量模板",
}


def _human_fallback(reason: str | None) -> str:
    if not reason:
        return "本窗未采用拼图"
    if reason in _FALLBACK_LABELS:
        return _FALLBACK_LABELS[reason]
    if reason.startswith("usage_rule:"):
        return f"使用规则拦截（{reason.split(':', 1)[-1]}）"
    return f"未拼原因：{reason}"


def _human_reject(entry: dict[str, Any]) -> str:
    reason = str(entry.get("reason") or "")
    tid = str(entry.get("templateId") or "模板")
    short = tid.removeprefix("screen-")
    if reason in _REJECT_LABELS:
        label = _REJECT_LABELS[reason]
    elif reason.startswith("usage_rule:"):
        label = f"使用规则 {reason.split(':', 1)[-1]}"
    elif reason.startswith("contract:"):
        label = _REJECT_LABELS.get(reason, "模板合同未通过")
    else:
        label = reason or "未通过"
    detail = entry.get("detail")
    if detail:
        return f"{short}：{label}（{detail}）"
    return f"{short}：{label}"


def _is_winner_plan(entry: dict[str, Any]) -> bool:
    """Prefer isWinnerPlan=true; accept missing flag for older trips."""
    if "isWinnerPlan" not in entry:
        return True
    return bool(entry.get("isWinnerPlan"))


def _interesting(entry: dict[str, Any]) -> bool:
    if entry.get("fallbackUsed"):
        return True
    if entry.get("rejectedTemplates"):
        return True
    if entry.get("fallbackReason"):
        return True
    return False


def build_mosaic_explain(curation: dict[str, Any] | None) -> dict[str, Any] | None:
    """Build Studio-facing «为何没拼» block from mosaicDecisionLog (LTN C6 / AC-C-05)."""
    if not curation:
        return None
    logs = curation.get("mosaicDecisionLog")
    if not isinstance(logs, list) or not logs:
        return None

    winners = [e for e in logs if isinstance(e, dict) and _is_winner_plan(e)]
    interesting = [e for e in winners if _interesting(e)]
    mosaic_wins = [
        e
        for e in winners
        if e.get("winnerPatternId")
        and not e.get("fallbackUsed")
        and str(e.get("plannerPath") or "") == "mosaic"
    ]

    details: list[str] = []
    for entry in interesting[:3]:
        seg = str(entry.get("segmentId") or "").strip()
        prefix = f"「{seg}」" if seg else ""
        if entry.get("fallbackUsed") or entry.get("fallbackReason"):
            line = f"{prefix}{_human_fallback(entry.get('fallbackReason'))}".strip()
        else:
            line = f"{prefix}拼图候选被部分否决".strip()
        source = entry.get("candidateSource")
        if source in _SOURCE_LABELS:
            line = f"{line}（{_SOURCE_LABELS[str(source)]}）"
        rejects = [r for r in (entry.get("rejectedTemplates") or []) if isinstance(r, dict)][
            :3
        ]
        if rejects:
            reject_txt = "；".join(_human_reject(r) for r in rejects)
            line = f"{line} — {reject_txt}"
        details.append(line)

    if not details and mosaic_wins:
        sample = str(mosaic_wins[0].get("winnerPatternId") or "").removeprefix("screen-")
        return {
            "mode": "ok",
            "summary": f"本辑有 {len(mosaic_wins)} 处拼图胜出上屏",
            "details": [f"例如 {sample}"] if sample else [],
        }

    if not details:
        return None

    fallback_n = sum(1 for e in winners if e.get("fallbackUsed"))
    if fallback_n:
        summary = f"有 {fallback_n} 处窗口未能拼成，主要原因如下"
    else:
        summary = "拼图候选中有部分模板被否决，主要原因如下"

    return {
        "mode": "fallback" if fallback_n else "rejects",
        "summary": summary,
        "details": details,
    }
