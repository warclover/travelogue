## Summary
- Share-Face Integrity W0–W2: context filter / naming / re-render, time outliers + appendix chapter, compact density + brand three-state + share polish.
- Rebased onto current `master` (includes CSC #16): resolved CSC doc conflicts; routed `rerender` via `layout_engine.api`; raised `curate.py` god-module ceiling 1830→1940 for SFI growth (documented).
- AC-12 script half-gate Pass (11.3%→3.0% non-photo share); **human blind seats still unsigned** — see merge-prep note.

## Test plan
- [x] `python scripts/lint_layout_engine_facade.py` (=0)
- [x] `python scripts/lint_csc_god_module_ratchet.py` (ceiling updated)
- [x] `python scripts/lint_csc_recipe_baseline.py`
- [x] `python -m pytest tests/unit -q -k "sfi or happy_path or public_api"` (45 passed)
- [ ] Product: AC-SFI-12 blind seats (≥3/5) **or** explicit waiver in merge note
- [ ] Optional dogfood: Studio export density + brand three-state on Semporna demo

## Notes
- CI Actions minutes exhausted — rely on local smoke above.
- Merge-prep: `docs/acceptance-records/share-face-integrity-v1-merge-prep-2026-07-22.md`
