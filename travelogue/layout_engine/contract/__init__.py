"""TPC · unified template contract (PRD-TEMPLATE-CONTRACT-V1)."""

from travelogue.layout_engine.contract.evaluator import (
    contract_pattern_ids_for_window,
    evaluate_contract_eligibility,
    patterns_for_contract_window,
    resolve_eligibility_spec,
)
from travelogue.layout_engine.contract.mix_index import (
    MixKey,
    build_mix_inverted_index,
    mix_key_from_aspects,
    mix_key_from_template,
)

__all__ = [
    "MixKey",
    "build_mix_inverted_index",
    "contract_pattern_ids_for_window",
    "evaluate_contract_eligibility",
    "mix_key_from_aspects",
    "mix_key_from_template",
    "patterns_for_contract_window",
    "resolve_eligibility_spec",
]
