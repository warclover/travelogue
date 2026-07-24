# Travelogue · Phase 10 验收标准

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) v0.10.0 |
| **关联实施** | [IMPLEMENTATION-PHASE10.md](./IMPLEMENTATION-PHASE10.md) |
| **更新日期** | 2026-06-02 |

---

## 1. 自动化验收

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P10-01** | `tests/test_food_grid.py` 全绿 | `pytest tests/test_food_grid.py -v` |
| **AC-P10-02** | demo verify 无回归（PRD 原文） | `python -m travelogue demo verify` |
| **AC-P10-02a** | 关键回归（subject bridge + screen planner）全绿 | `pytest tests/test_subject_tagging_bridge.py tests/test_screen_layout_planner.py -v` |
| **AC-P10-02b** | 一键自动验收记录（含 food-grid 关键场景） | `python scripts/phase10_food_grid_acceptance.py --write docs/acceptance-records/phase10-food-grid.json` |
| **AC-P10-02d（可选）** | 自动验收时附带 demo verify 检查 | `python scripts/phase10_food_grid_acceptance.py --include-demo-verify --write docs/acceptance-records/phase10-food-grid.json` |
| **AC-P10-02c（可选 10.1）** | 多桶检查（sign/ticket/shop） | `python scripts/phase10_food_grid_acceptance.py --include-phase101 --mundane-buckets food,sign,ticket,shop --write docs/acceptance-records/phase10-food-grid.json` |

---

## 2. 人工验收

| ID | 条件 | 说明 |
|----|------|------|
| **AC-P10-03** | 含 ≥3 food 的 trip 在章内出现 `layoutHint=food-grid` 的 square grid 屏 | 优先使用 `schemas/fixtures/trip.phase10_food_grid.json` 在 Studio/导出产物抽检 |

---

## 3. PRD §6 用例对照

| 用例 | 预期 |
|------|------|
| 3 food | 生成 `screen-square-4`，`layoutHint=food-grid` |
| 2 food | **FRP 后触发** food-grid（square-4 · 2 slots）；Phase 10 原文「不触发」已由 [ACCEPTANCE-FOOD-ROLE-POLICY.md](./ACCEPTANCE-FOOD-ROLE-POLICY.md) AC-FRP-08 取代；回退：`food_role.grid_min_items: 3` |
| food + 1 干扰（tolerance=1） | 仍可触发 food grid（FRP 默认 interruptions≤2） |
| `enable_food_grid=false` | 完全回退，food grid 不出现 |
| portrait run + food run | 两类 grid 共存 |
| 6 food | 生成 `screen-square-6` |
| 9+ food | 优先 `screen-square-9`，超出部分继续拆屏 |
| CLIP `subjectClass=food`（无 tags） | 可触发 |
| 仅 tags `meal`（无 CLIP） | 可触发 |
| 章末剩余 ≥3 food | 触发章末 flush |
