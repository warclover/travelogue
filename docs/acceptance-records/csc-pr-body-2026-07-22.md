## Summary
- Land CSC W0–W3: Happy Path Recipe snapshot (`studio_default`), L0/L1 budget, settings tier UI + help H0, `layout_engine` public facade (deep imports = 0), god-module / debt / recipe baseline CI ratchets.
- Split user vs research config examples; DOC-STATUS + ACCEPTANCE contract; grandfather clauses and DIFF empty table.
- Pre-merge smoke Pass (H0, preview→longshot, zero admin hits); see `docs/acceptance-records/csc-pre-merge-smoke-2026-07-22.md`.

## Test plan
- [x] `python scripts/lint_layout_engine_facade.py`
- [x] `python scripts/lint_csc_god_module_ratchet.py`
- [x] `python scripts/lint_csc_debt_table.py`
- [x] `python scripts/lint_csc_recipe_baseline.py`
- [x] `python -m pytest tests/unit/orchestrator/test_happy_path_recipe.py -q`
- [x] Studio smoke: `?help=H0` + settings link; preview→longshot without experimental options; no admin URLs
- [ ] CI lint job: new CSC steps green on this PR

## Notes
- Parking (not in this PR): shim deletion batches, AAD curate split, pipeline opportunistic extract, full 33-bool tier human review.
- SFI branch remains separate until AC-12 closes.
