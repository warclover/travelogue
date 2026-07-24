# Travelogue · 美食角色策略验收（Food Role Policy · FRP）

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-FOOD-ROLE-POLICY-V1.md](./PRD-FOOD-ROLE-POLICY-V1.md) v0.1.0 |
| **特性代号** | FRP |
| **状态** | Implemented · 自动化 + Fixture Dogfood 绿；真人目视待签 |
| **Fixture 基线** | [acceptance-records/food-role-policy.fixture.json](./acceptance-records/food-role-policy.fixture.json) |
| **Dogfood 清单** | [acceptance-records/food-role-policy-dogfood-CHECKLIST.md](./acceptance-records/food-role-policy-dogfood-CHECKLIST.md) |
| **更新日期** | 2026-07-24 |

---

## 1. 自动化验收

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-FRP-01** | 混合相册：非美食 + 高分横幅美食 → 默认封面 ≠ food | `tests/unit/curation/test_food_role_policy.py` |
| **AC-FRP-02** | 候选几乎全 food → 允许 food 封面 + fallback 标记 | 同上 |
| **AC-FRP-03** | opening lock + `sync_trip_covers(web)` 后 food 封面保留，`foodPolicy.cover=override` | 同上 |
| **AC-FRP-04** | 混合相册封底 ≠ food，且 `curation.foodPolicy.closing` 落库 | 同上（含 lock→override） |
| **AC-FRP-05** | 章内存在横幅美食与非美食 landscape → 章首 hero ≠ food | 同上 |
| **AC-FRP-06** | 单张 food + 多张风景 → food ∉ `momentPoolIds` | 同上 |
| **AC-FRP-07** | Studio 指定 food 为 moment → 允许并注入池 | 同上 |
| **AC-FRP-08** | 2 张连续 food → 1 个 food-grid（非 2 全幅） | `tests/unit/curation/test_food_grid.py` |
| **AC-FRP-09** | 3 张 food + 中间 1 风景且时间差 < 60min → 仍 1 grid | 同上 |
| **AC-FRP-10** | 1 张孤立 food → 非 grid / 非封面 / 非 moment 池 | 同上 |
| **AC-FRP-08b** | food-grid 成功时写入 `foodPolicy.grids[]` | 同上 |
| **AC-FRP-06b** | `peak_moment_score` 对 food 乘 `moment_multiplier` | 同上 |
| **AC-FRP-11** | `cover_policy=off` 且 `grid_min_items=3` → 近似 FRP 前 | 同上 |
| **AC-FRP-12** | 无 vision、仅 tags=`food` → demote / 组屏仍生效 | 同上 |
| **AC-FRP-R1** | Phase 10 既有组屏回归（≥3 / disable / multi-bucket） | `pytest tests/unit/curation/test_food_grid.py -q` |
| **AC-FRP-R2** | subject bridge + 关键 planner 无回归 | `pytest tests/unit/curation/test_food_role_policy.py tests/unit/curation/test_food_grid.py -q` |

### 一键命令

```powershell
python -m pytest tests/unit/curation/test_food_role_policy.py tests/unit/curation/test_food_grid.py -q
python scripts/food_role_policy_acceptance.py --write-fixture --write docs/acceptance-records/food-role-policy.fixture.json
```

---

## 2. Dogfood / 人工

| ID | 条件 | 状态 | 说明 |
|----|------|------|------|
| **AC-FRP-D1** | 混拍对比：封面 / 单张美食屏 / grid | ✅ Fixture | [food-role-policy.fixture.json](./acceptance-records/food-role-policy.fixture.json)；真人 trip 可选补 `food-role-policy.<trip-id>.json` |
| **AC-FRP-D2** | 封面目视：地方/人/氛围，不是菜单 | ☐ 产品 | [dogfood CHECKLIST](./acceptance-records/food-role-policy-dogfood-CHECKLIST.md) |
| **AC-FRP-D3** | 同桌菜以拼图出现 | ☐ 产品 | 同上 |

---

## 3. PRD 用例对照

| 场景 | 预期 | AC |
|------|------|----|
| 高分横幅菜 + 普通风景 | 封面 = 风景（或非 food） | AC-FRP-01 |
| 全美食相册 | 封面可为 food；`foodPolicy.cover=fallback` | AC-FRP-02 |
| Opening locked 为 food | re-sync 不改封面 | AC-FRP-03 |
| 封底候选含风景与菜 | 封底 ≠ food | AC-FRP-04 |
| 章首可选 landscape 非美食 | hero ≠ food | AC-FRP-05 |
| 孤立 1 张菜 | 不进高光池 | AC-FRP-06 / 10 |
| Studio 把菜设为签名时刻 | 成功；池内含该 id | AC-FRP-07 |
| 2 张连续菜 | `layoutHint=food-grid`，pattern square-4，2 slots | AC-FRP-08 |
| 同餐段被 1 张风景打断 | 仍聚成 grid | AC-FRP-09 |
| `food_role.cover_policy=off` + `grid_min_items=3` | 2 张不组屏；封面可上菜 | AC-FRP-11 |

---

## 4. 配置默认（合入后）

```yaml
curate:
  food_role:
    cover_policy: demote
    cover_multiplier: 0.15
    closing_policy: demote
    closing_multiplier: 0.15
    hero_policy: skip
    allow_food_in_moment: false
    moment_multiplier: 0.05
    grid_min_items: 2
    cluster_window_seconds: 3600
    grid_max_interruptions: 2
```

| 回退 | 做法 |
|------|------|
| 关闭封面美食策略 | `cover_policy: off` |
| 恢复 Phase 10 组屏门槛 | `grid_min_items: 3`（并可把 `grid_max_interruptions` 调回 1） |
| 允许美食进高光池 | `allow_food_in_moment: true` |

---

## 5. 签字栏

| 角色 | 结果 | 日期 | 备注 |
|------|------|------|------|
| 工程 | ✅ AC-FRP 单测 + fixture dogfood | 2026-07-24 | `food_role_policy_acceptance.py` status=passed；legacy 封面=`f_hero` → FRP=`l3` |
| 产品 | ☐ AC-FRP-D2–D3 真人目视 | | |
| 合并 | ☐ | | |
