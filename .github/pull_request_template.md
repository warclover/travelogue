## Summary

<!-- 1–3 句：为何改、影响范围 -->

## Quality gate

- [ ] `python scripts/quality_gate.py` 通过
- [ ] 若改 `trip.json` 结构 → 已更新 `schemas/trip.schema.json`
- [ ] 若改 layout/scoring → 已跑相关 pytest（见 [docs/QUALITY-GATE.md](../docs/QUALITY-GATE.md)）
- [ ] 若新增/改 `travelogue/layout_contract/` → `python scripts/lint_layout_contract_surface.py` 通过（仅层 0 依赖）
- [ ] 生产代码未新增 runtime `assert`（`python scripts/lint_no_runtime_assert.py`；见 [TESTING.md §9](../docs/TESTING.md)）

## Test plan

- [ ] 本地 pytest 子集 / 全量（如适用）
- [ ] 真实 trip 验收：`python scripts/e2e_trip_acceptance.py <tripId>`（如适用）
