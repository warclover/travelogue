"""SSG M2 · look boundary metrics (AC-SSG-11)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence


def look_boundary_f1(
    ordered_ids: Sequence[str],
    gold_group_of: Mapping[str, str],
    pred_group_of: Mapping[str, str],
) -> dict[str, float]:
    """Pairwise consecutive-boundary F1 on a time-ordered look track.

    A boundary exists between adjacent ids when their group ids differ.
    """
    if len(ordered_ids) < 2:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0, "tp": 0, "fp": 0, "fn": 0}

    tp = fp = fn = 0
    for a, b in zip(ordered_ids, ordered_ids[1:]):
        gold_b = gold_group_of.get(a) != gold_group_of.get(b)
        pred_b = pred_group_of.get(a) != pred_group_of.get(b)
        if gold_b and pred_b:
            tp += 1
        elif pred_b and not gold_b:
            fp += 1
        elif gold_b and not pred_b:
            fn += 1

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0.0
    )
    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "tp": float(tp),
        "fp": float(fp),
        "fn": float(fn),
    }
