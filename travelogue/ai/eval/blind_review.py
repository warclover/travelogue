"""Unified blind-review framework · ACP W4 / §5.7.

Methodology aligns with ``pa_acceptance.spearman_srcc`` and CAL AC-CAL-BLIND
export → human score → SRCC. Implemented inside ``ai/eval`` so agents stay
free of upward imports into ``curation`` (D-ACP-01).
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

SUPPORTED_AGENTS = (
    "narrate",
    "layout_critic",
    "intent_brief",
    "title_art_route_c",
    "aesthetic_mllm",
    "mosaic_judge",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _rank_data(values: list[float]) -> list[float]:
    """Average ranks for ties (Spearman) — mirrors pa_acceptance."""
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman_srcc(human: list[float], predicted: list[float]) -> float | None:
    if len(human) != len(predicted) or len(human) < 3:
        return None
    pairs = [(float(h), float(p)) for h, p in zip(human, predicted, strict=True)]
    if len({h for h, _ in pairs}) < 2 or len({p for _, p in pairs}) < 2:
        return None
    hr = _rank_data([h for h, _ in pairs])
    pr = _rank_data([p for _, p in pairs])
    n = float(len(pairs))
    mean_h = sum(hr) / n
    mean_p = sum(pr) / n
    num = sum((h - mean_h) * (p - mean_p) for h, p in zip(hr, pr, strict=True))
    den_h = sum((h - mean_h) ** 2 for h in hr) ** 0.5
    den_p = sum((p - mean_p) ** 2 for p in pr) ** 0.5
    if den_h <= 0 or den_p <= 0:
        return None
    return num / (den_h * den_p)


def sample_items(
    pool: list[dict[str, Any]],
    *,
    sample_rate: float = 0.1,
    seed: int = 42,
    max_items: int = 40,
) -> list[dict[str, Any]]:
    """Deterministic subsample for blind export."""
    if not pool:
        return []
    rate = max(0.0, min(1.0, float(sample_rate)))
    if rate <= 0:
        return []
    rng = random.Random(int(seed))
    indexed = list(enumerate(pool))
    rng.shuffle(indexed)
    target = max(1, min(max_items, int(round(len(pool) * rate))))
    if rate >= 1.0:
        target = min(max_items, len(pool))
    picked = sorted(indexed[:target], key=lambda x: x[0])
    return [dict(item) for _, item in picked]


@dataclass
class BlindReviewPack:
    agent: str
    prompt_version: str
    items: list[dict[str, Any]] = field(default_factory=list)
    sample_rate: float = 0.1
    seed: int = 42
    exported_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "promptVersion": self.prompt_version,
            "sampleRate": self.sample_rate,
            "seed": self.seed,
            "exportedAt": self.exported_at or _utc_now_iso(),
            "itemCount": len(self.items),
            "items": list(self.items),
            "labelSchema": {
                "humanScore": "1-5 integer preference / quality",
                "predictedOverall": "model or heuristic score 0-1 or 1-5",
                "notes": "optional free text (no PII / no pixels)",
            },
        }


def _item_id(agent: str, payload: dict[str, Any], index: int) -> str:
    raw = f"{agent}|{index}|{sorted(payload.items())}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def export_blind_review_pack(
    agent: str,
    pool: list[dict[str, Any]],
    *,
    sample_rate: float = 0.1,
    seed: int = 42,
    prompt_version: str = "v1",
    max_items: int = 40,
) -> BlindReviewPack:
    """Export anonymized review rows for one agent.

    Each pool item should already be pixel-free (text / ids / scores only).
    """
    if agent not in SUPPORTED_AGENTS:
        raise ValueError(f"unsupported blind-review agent: {agent}")
    sampled = sample_items(pool, sample_rate=sample_rate, seed=seed, max_items=max_items)
    items: list[dict[str, Any]] = []
    for i, row in enumerate(sampled):
        predicted = row.get("predictedOverall", row.get("score", row.get("confidence")))
        try:
            predicted_f = float(predicted) if predicted is not None else None
        except (TypeError, ValueError):
            predicted_f = None
        display = str(row.get("display") or row.get("text") or row.get("suggestion") or "")[
            :200
        ]
        items.append(
            {
                "id": str(row.get("id") or _item_id(agent, row, i)),
                "display": display,
                "predictedOverall": predicted_f,
                "humanScore": None,
                "meta": {
                    k: row[k]
                    for k in ("chapterId", "tripId", "windowId", "patternId")
                    if k in row and row[k] is not None
                },
            }
        )
    return BlindReviewPack(
        agent=agent,
        prompt_version=prompt_version,
        items=items,
        sample_rate=sample_rate,
        seed=seed,
        exported_at=_utc_now_iso(),
    )


def score_blind_labels(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute Spearman SRCC from labeled rows (humanScore + predictedOverall)."""
    human: list[float] = []
    predicted: list[float] = []
    for row in rows:
        try:
            h = float(row["humanScore"])
            p = float(row.get("predictedOverall", row.get("overall")))
        except (KeyError, TypeError, ValueError):
            continue
        human.append(h)
        predicted.append(p)
    srcc = spearman_srcc(human, predicted)
    return {
        "sampleCount": len(human),
        "srcc": None if srcc is None else round(srcc, 4),
        "method": "spearman",
    }


def format_blind_report(
    agent: str,
    scores: dict[str, Any],
    *,
    pack: BlindReviewPack | None = None,
) -> str:
    """Markdown report template per agent."""
    lines = [
        f"# ACP 盲评报告 · {agent}",
        "",
        f"- 生成时间：{_utc_now_iso()}",
        f"- 样本数：{scores.get('sampleCount')}",
        f"- Spearman SRCC：{scores.get('srcc')}",
        f"- 方法：{scores.get('method') or 'spearman'}",
    ]
    if pack is not None:
        lines.extend(
            [
                f"- promptVersion：{pack.prompt_version}",
                f"- sampleRate：{pack.sample_rate}",
                f"- seed：{pack.seed}",
                f"- 导出条目：{len(pack.items)}",
            ]
        )
    lines.extend(
        [
            "",
            "## 用法",
            "",
            "1. `export_blind_review_pack` 导出 JSON（无像素）",
            "2. 人工填写 `humanScore`（1–5）",
            "3. `score_blind_labels` 计算 SRCC，贴回本模板",
            "",
            "> 对齐 PA `pa_acceptance` / CAL AC-CAL-BLIND；不做跨 trip 学习。",
            "",
        ]
    )
    return "\n".join(lines)


def pack_from_layout_suggestions(
    suggestions: list[dict[str, Any]],
    *,
    sample_rate: float = 0.1,
    seed: int = 42,
) -> BlindReviewPack:
    pool = []
    for s in suggestions:
        if not isinstance(s, dict):
            continue
        pool.append(
            {
                "display": str(s.get("suggestion") or ""),
                "predictedOverall": s.get("confidence"),
                "chapterId": s.get("chapterId"),
                "patternId": s.get("suggestedPatternId"),
            }
        )
    return export_blind_review_pack(
        "layout_critic",
        pool,
        sample_rate=sample_rate,
        seed=seed,
        prompt_version="layout-critic-v1",
    )
