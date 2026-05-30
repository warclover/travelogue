## Summary

<!-- 1–3 句：为何改、影响范围 -->

## Quality gate

- [ ] `python scripts/quality_gate.py` 通过
- [ ] 若改 `trip.json` 结构 → 已更新 `schemas/trip.schema.json`
- [ ] 若改 layout/scoring → 已跑相关 pytest（见 [docs/QUALITY-GATE.md](../docs/QUALITY-GATE.md)）

## Test plan

- [ ] 本地 pytest 子集 / 全量（如适用）
- [ ] 真实 trip 验收：`python scripts/e2e_trip_acceptance.py <tripId>`（如适用）
