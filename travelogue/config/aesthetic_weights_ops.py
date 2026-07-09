"""Pure operations on aesthetic config weights."""

from __future__ import annotations

from travelogue.config.aesthetic import AestheticWeights

_DIM_KEYS = ("composition", "exposure", "color", "lighting", "subjectClarity")


def weights_with_dim_emphasis(
    base: AestheticWeights,
    *,
    dim: str,
    emphasis: float,
) -> AestheticWeights:
    """Set one dim to *emphasis* and scale the rest to sum to 1."""
    key = dim if dim != "subject_clarity" else "subjectClarity"
    if key not in _DIM_KEYS:
        raise ValueError(f"unknown dim {dim!r}")
    m = base.as_dim_map()
    emphasis = max(0.05, min(0.85, float(emphasis)))
    others = [k for k in _DIM_KEYS if k != key]
    rest = 1.0 - emphasis
    others_sum = sum(float(m[k]) for k in others) or 1.0
    scaled = {key: emphasis}
    for k in others:
        scaled[k] = rest * float(m[k]) / others_sum
    return AestheticWeights(
        composition=scaled["composition"],
        exposure=scaled["exposure"],
        color=scaled["color"],
        lighting=scaled["lighting"],
        subject_clarity=scaled["subjectClarity"],
    )
