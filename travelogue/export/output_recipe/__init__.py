"""Output Recipe V1 · Band × Intent → 导出配方（PRD-OUTPUT-RECIPE-V1 Phase A）."""

from __future__ import annotations

from travelogue.export.output_recipe.kept_n import count_kept_n
from travelogue.export.output_recipe.resolve import (
    ambiguous_intent_options,
    classify_band,
    resolve_output_recipe,
)
from travelogue.export.output_recipe.types import (
    INTENT_TO_PLATFORM,
    PHASE_A_INTENTS,
    PLATFORM_TO_INTENT,
    BandThresholds,
    OutputRecipe,
    OutputRecipeError,
)

__all__ = [
    "BandThresholds",
    "INTENT_TO_PLATFORM",
    "OutputRecipe",
    "OutputRecipeError",
    "PHASE_A_INTENTS",
    "PLATFORM_TO_INTENT",
    "ambiguous_intent_options",
    "classify_band",
    "count_kept_n",
    "resolve_output_recipe",
]
