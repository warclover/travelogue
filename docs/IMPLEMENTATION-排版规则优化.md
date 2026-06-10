# Travelogue · 排版规则优化实施清单

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **对应 PRD** | [PRD-排版规则优化.md](./PRD-排版规则优化.md) v0.3 |
| **讨论会** | [WORKSHOP-排版规则优化讨论会.md](./WORKSHOP-排版规则优化讨论会.md) |
| **范围** | web screens 引擎；mobile/legacy 不动 |
| **验收样本** | `trips/demo-2025-2`（竖版墙）+ 正样本 linzhi / demo-2025（防过拟合） |
| **更新日期** | 2026-06-10 |

---

## 1. 冻结决策（启动前）

| 决策 | 取值 | 来源 |
|------|------|------|
| OQ-03 人物连拍触顶排法 | 纯竖版游程内**用 portrait-3 打断**（无横版可插时），即 `2+2+3+…`；有横版时让位换气 | 本实施细化 |
| OQ-04 R-08 全竖版连续上限 | **6** | PRD 默认 |
| OQ-09 上线方式 | 先 **log**（post-check 观测），planner 改造同期但 enforce 走配置 | PRD |

---

## 2. PR 拆解

| PR | 范围 | 风险 | 状态 |
|----|------|------|------|
| **PR-1** | `ScreenLayoutPlannerState` 增 `last_pattern_id` / `pattern_streak` + `portrait_pair` kind + `can_emit_pattern` 支持 R-06 | 低 | ✅ 本次 |
| **PR-2** | `layout_constraints.py` post-check：portrait-2 streak / 满屏竖单 / 朝向 streak（log/审计用） | 低（纯新增） | ✅ 本次 |
| **PR-3** | `screen_planner` flush 路径接入 R-06：纯竖版游程触顶用 triple 打断 | 中 | ✅ 本次 |
| **PR-3b** | AC-RHY-07：`run_rhythm_postcheck` 灰度接入 `run_curate`（mode=log，R-07 breath 透明） | 低（纯观测） | ✅ 本次 |
| **PR-4** | R-08 朝向 streak + 换气（混排上下文插横版） | 中 | ⏳ 次轮 |
| **PR-5** | `force=True` 收窄 + carry/state 同步（V-08/V-10）+ folio plate（V-09/S-02） | 高 | ⏳ 次轮 |
| **PR-6** | LSE `consecutive_bans` 接线 + 阈值配置化 + LAYOUT-PLANNER v0.5 | 低 | ⏳ 次轮 |

---

## 3. 本次交付（PR-1 ~ PR-3）

### 3.1 状态层（PR-1）
- 新增 `last_pattern_id`、`pattern_streak`（按 patternId 连续计数，WS-ALG-01 雏形）
- `layout_kind_from_pattern`：`screen-portrait-2` → `portrait_pair`
- `can_emit_pattern("screen-portrait-2")`：`pattern_streak >= MAX_PORTRAIT_PAIR_STREAK(=2)` 时返回 False（R-06）
- `note_screen`：同步 `last_pattern_id` / `pattern_streak`
- 新增 `current_portrait_pair_streak()` 供批量出屏路径取种子值

### 3.2 校验层（PR-2 · 纯新增，不改默认行为）
- `is_portrait_pair_pattern` / `is_full_bleed_portrait_screen` / `is_portrait_orientation_pattern`
- `check_portrait_pair_streak`（R-06，max=2）
- `check_full_bleed_portrait_consecutive`（V-08/V-09）
- `check_portrait_orientation_streak`（R-08，max=6）
- `audit_rhythm_violations(chapters)` 汇总（供 telemetry / 测试）

### 3.3 规划层（PR-3）
- `_emit_person_portrait_screens` 与 `_flush_portrait_pending` 竖版 while 循环：
  - 维护**局部 pair streak**（种子取自 `layout_state.current_portrait_pair_streak()`）
  - 将出第 3 连 `portrait-2` 前，若剩余 ≥3 且可出 `portrait-3`（非连续 triple），改出 **triple 打断**
  - `force=True` 仍可绕过**单竖**兜底，但**不绕过 R-06**（pair streak）

### 3.4 灰度观测层（PR-3b · AC-RHY-07）
- `layout_constraints.run_rhythm_postcheck(chapters, mode="log", trip_id=...)`：
  - 汇总 `audit_rhythm_violations`，按 code 计数，违规时 `logger.warning` 摘要 + `logger.info` 逐条
  - `mode="log"`（默认，OQ-09=B 灰度）只观测不改规划；`mode="enforce"` 预留硬执行接口
- `run_curate`：screens 引擎 + `apply_layout` 时，breath 插入后调用 post-check，违规计入 `CurateResult.warnings`
- R-07：`_streak_violations` 对 `screen-breath*` / `screen-decor*` **透明**（不计入也不打断 streak）

---

## 4. 受影响测试

| 测试 | 处理 |
|------|------|
| `test_screen_layout_planner.py::test_portrait_heavy_summary`（6 连竖→3×portrait-2） | **更新期望**：6 连竖在 R-06 下 → `portrait-2, portrait-2, portrait-3`（pair-first + triple 打断） |
| 新增 `test_layout_rhythm_rules.py` | R-06 streak、满屏竖单、朝向 streak、validator |

---

## 5. 验收

- ✅ `AC-RHY-01`：全 trip `max_streak(portrait-2) ≤ 2` — demo-2025-2 实跑 max=2
- ✅ demo-2025-2 ch-01 两段 4 连双竖消失（实跑确认，`audit_rhythm_violations`=0）
- ✅ R-08 朝向 streak：demo-2025-2 实跑无违规（横版/全景天然换气，最长全竖版连续≈3）
- ✅ 现有 screens/rhythm 测试通过（除有意更新的 1 项）；新增 `test_layout_rhythm_rules`
- ✅ mosaic/lte 子集 319 passed（含本地 config.yaml 关停解耦 fixture）

### 5.1 demo-2025-2 实跑结果（2026-06-10）

ch-01 内容序：`L,L,L,p2,p2,p3,L,p3,L,p2,p2,p3,full,mosaic5,p2,p2` —— 原「4 连双竖×2 段」已被横版/三列/mosaic 打断，`portrait-2` 最长 2 连。结论：**P0 达到 demo 验收目标**；OQ-03「插横版换气」在本 trip 因时间线天然交错横版而自然满足，无需 P0 内强制 R-08。

---

## 6. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-10 | PR 拆解 + PR-1~PR-3 落地 |
| v0.2 | 2026-06-10 | PR-3b：AC-RHY-07 post-check 灰度 log 接入 curate（R-07 breath 透明） |
