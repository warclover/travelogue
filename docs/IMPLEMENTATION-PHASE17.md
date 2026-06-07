# Travelogue · Phase 17 实施清单（智能排版引擎 LSE · 融合设计 + W0 审计 + 阶段交付）

| 属性 | 内容 |
|------|------|
| **文档** | IMPLEMENTATION-PHASE17 |
| **版本** | v0.1（W0 起草） |
| **配套 PRD** | [PRD-PHASE17-layout-strategy-engine.md](./PRD-PHASE17-layout-strategy-engine.md)（v0.17.6） |
| **分支** | `feature/phase17-lse` |
| **更新日期** | 2026-06-07 |
| **状态** | **W0 已冻结** — 审计+schema+DESIGN+ADR 就绪；**W1 待开工** |

> **本文定位**：把 PRD 的「做什么/为什么」落成「怎么接、改哪里、先干哪些、多久」。PRD 是契约，本文是施工图。**§13.4 W0 阻断交付物之一**。

---

## 0. 三句话总览

1. **融合策略 = 防腐 adapter + 开关 + 受控 parity 护栏**：LSE 旁路包住现有 `screen_planner` 链路；`layout.strategy_engine.enabled` 默认 `false`（行为 = P16 末态），W3a 翻 `true`。
2. **复用而非重造**：生命周期/审批/审计/RBAC 复用 `travelogue/templating/`；decision log 用 sidecar 新 schema + 适配器投影现有 3 套日志；不动 beam/乘性打分本体（NG-P17-07）。
3. **W0 三项审计是开工前提**：现网真实活跃打分链审计、确定性 vs parity 跑法、decision log 包装方案——任一未定，W1 的 parity CI 会建错基线。

---

## 1. 与现有代码的融合设计

### 1.1 旁路并行架构

```
master / P16 末态（持续可跑，行为不变）：
  run_curate → _curate_preflight → attach_screens_to_chapters
            → plan_screens_for_chapter(...15 kwargs...)
            → ChapterScreenPlanner.create().plan()
            → stages（hero/mosaic/mixed/...）→ MCS scorer（乘性）→ screens[]

feature/phase17-lse 引入 LSE（旁路 + 开关）：
  run_curate → _curate_preflight
            → layout_engine/adapter.plan_chapter_screens(ctx, engine)   # 新唯一入口
                ├─ enabled=false → 直接转发现有 plan_screens_for_chapter（零行为变化）
                └─ enabled=true  → 从 StrategyPack 解析 kwargs + profile 注入 → 同一 ChapterScreenPlanner
            → decision_log.emit（sidecar，异步）

回退：layout.strategy_engine.enabled=false（瞬时回到 P16 末态）
```

**关键原则**：W1 的 adapter **`enabled=true` 也必须逻辑等价 P16**（纯收敛、不带 CAP）。CAP-02/03/04 在 W3b 才以特征/权重形式注入，且各自有 capability 开关。

### 1.2 融合点（文件级 · 已核证）

| # | 融合点 | 关键文件（行数） | 摩擦 | 改动要点 |
|---|--------|------------------|------|----------|
| 1 | curate 入口 | `curation/curate.py`（`run_curate` / `_curate_preflight`） | 🟡中 | `_curate_preflight` 内构造 `LayoutStrategyEngine`，传入 adapter；不改 `run_curate` 主签名 |
| 2 | 章组屏入口 | `curation/screen_planner_attach.py`（`attach_screens_to_chapters`,2 处调用 `plan_screens_for_chapter`） | 🔴中高 | adapter 包住这 2 处调用；**15 kwargs 的收束映射**（§3） |
| 3 | God 文件 | `curation/screen_planner.py`（**1007 行**）、`screen_planner_stages.py`（751） | 🔴高 | **不整文件搬家**（ADR-010）；adapter 旁路，stages 渐进迁入 `layout_engine/stages/` |
| 4 | 节奏状态 | `curation/screen_layout_state.py`（158） | 🟡中 | `nine_grid_limits` / `density_profiles` bias 注入；W1 仅"等价复刻"，W3b 才加 beat bias |
| 5 | MCS 打分 | `curation/mosaic/scorer.py`（283，乘性） | 🟡中 | profile 注入 weights/penalties；W3b 加 `salient_crop`；**§4.3 log-domain `contribution` 输出** |
| 6 | 搜索预算 | `curation/search_budget.py`（`time.monotonic` 门控） | 🔴高 | **确定性矛盾点**（§2）；改为确定性上限，wall-clock 仅 telemetry |
| 7 | 决策日志 | `curation/decision_log.py`（24）+ `mosaic/log.py` + `mosaic/telemetry.py` | 🟡中 | 新建统一 sidecar schema；适配器从 3 套投影（§4） |
| 8 | 配置 | `config/layout.py`（dataclass + from_dict，**非 pydantic**） | 🟡中 | 加 `LayoutStrategyEngineConfig`；schema.json 与 dataclass 双真值源 → 加一致性测试 |
| 9 | 渲染绑定 | `render/context.py`（已出 `--focal-x/y`）+ `journal-screens.css`（硬编码 object-position） | 🔴高 | §4.10 渲染落地契约；CAP-02 上线前置 |
| 10 | 治理后台 | `templating/config_governance.py`（硬编码 if-chain）+ `template_admin_handlers.py` | 🟡中 | 扩展 5 个 `layout_strategy_*` patch 键（L0 代码改动）；新增「排版策略」Tab |
| 11 | 隐式反馈 | `curation/feedback.py`（已有 `G1EditRecord` + 去噪） | 🟢低 | 复用 G1 去噪；`layoutFeedback` 投影 + 有效 label 过滤（W4） |

### 1.3 三个必须正视的真相

- **真相 1（现网"活跃参数"≠ PRD 字面）**：`LayoutScoringConfig.enabled` 默认 `False` 且 weights 全 0（`config/layout.py:15-44`）。现网真正生效的是 `mosaic.weights/penalties` + `ScreenLayoutPlannerState` 分档。→ 见 §2 审计 A。
- **真相 2（现网搜索就是挂钟非确定）**：`search_budget.should_stop()` 用 `time.monotonic() >= search_timeout_ms` 截断搜索且**改变产出**（`curate.py:905/936` 注入）。P16 末态在负载下本就不确定。→ 见 §2 审计 B。
- **真相 3（decision log 不是从零）**：已有 3 套日志，结构互不相同；"统一"是聚合/适配而非另起炉灶。→ 见 §2 审计 C / §4。

### 1.4 模块结构（新建 vs 复用）

```
travelogue/layout_engine/              # 新建（R-P17-01）
├── __init__.py
├── registry.py          # YAML 加载、profile 索引、contentHash、list_active_strategies
├── adapter.py           # plan_chapter_screens：curate 唯一入口（防腐层）
├── policy.py            # lse_policy.yaml + runtime merge
├── decision_log.py      # 统一 sidecar schema + emit/query（适配现有 3 套）
├── validator.py         # Strategy Pack 门禁（用 schema.json）+ dataclass 一致性
├── features.py          # LayoutFeatures 统一派生（W4；值域契约 §4.6）
├── slot_assignment.py   # greedy | hungarian（W4，确定性 max_matrix_n）
├── segment_order.py     # 段内序优化（W4，Plus）
├── feedback.py          # layoutFeedback 投影 + 有效 label 过滤（W4，复用 curation/feedback.py）
├── pace.py              # pace_profile（W5）
├── highlight_windows.py # 高光窗（W4，Plus）
├── editorial_hints.py   # breath/folio hint 输出（W4，Plus）
├── cli.py               # validate | probe | sandbox | audit-active-params
├── lse_strategy.schema.json
├── lse_policy.yaml
├── strategies/default.yaml
└── probe/

复用（不新建）：
travelogue/templating/        # lifecycle/roles/audit/config_governance/shadow
travelogue/layout_templates/  # LTE 只读消费
travelogue/curation/feedback.py
travelogue/web/studio_handlers/template_admin_handlers.py

渐进迁入（不一次性搬家，W3+）：
screen_planner_stages.py → layout_engine/stages/
screen_layout_state.py   → layout_engine/rhythm.py
```

---

## 2. W0 三项审计（开工阻断 · 产出模板）

> 三项审计**均须在 W1 开工前产出**并评审，否则 parity CI 建错基线。产出存 `docs/acceptance-records/p17-w0-audit-*.md`。

### 审计 A — 现网真实活跃打分链

**目的**：确定 `scoring_profiles.default` 的真值来源，避免迁入死路径。

| 待查项 | 方法 | 产出 |
|--------|------|------|
| `layout.scoring.enabled` 现网值 | 读 `config.yaml` + `config/layout.py` 默认 | 是否生效结论 |
| 各打分链调用关系 | trace `curate.py` → mosaic vs layout_search 分支 | "哪条链对默认 trip 真正跑" |
| `mosaic.weights/penalties` 现网值 | 读 `config.yaml` + `MosaicConfig` | 迁入默认包的权威数值 |
| `ScreenLayoutPlannerState` 分档常数 | 读 `screen_layout_state.py` | `rhythm.nine_grid_limits` 映射表 |

**验收**：产出一张"现网活跃参数 → StrategyPack 字段"映射表，覆盖 §7.2 全部行，标注每行"活跃/死代码/部分"。

### 审计 B — 确定性 vs parity 跑法

**目的**：定义"受控 parity"（AC-P17-01 已改口径），并评估去除 wall-clock 的回归面。

| 待查项 | 方法 | 产出 |
|--------|------|------|
| `search_budget` 是否影响默认 trip 产出 | 固定大 trip，跑 timeout=∞ vs 2000ms 比对 screens | "现网是否已非确定"结论 |
| 受控跑法定义 | 固定时钟桩 / `max_evaluations` 替代 / 单线程 | 受控 parity runbook |
| 去 wall-clock 的回归面 | 评估改 `search_budget` 后哪些现有测试受影响 | 风险清单 |

**受控 parity runbook（草案）**：
```
PYTHONHASHSEED=0；单线程；search_budget 用 max_evaluations 上限（非 timeout）；
固定 utc_now 桩；冻结 trips/demo-151e7b488c + demo-2025 + 新增人像/风景 golden
→ enabled=false 与 enabled=true（纯收敛）screens[] 逐字段比对（忽略 decisionLog/时间戳）
```

### 审计 C — Decision Log 包装方案

**目的**：定调"适配现有 vs 新建"，冻结统一 schema。

| 现有 | 结构 | 处置 |
|------|------|------|
| `curation/decision_log.py` `LayoutDecisionLog` | `{chapterId, events[]}` 事件型 in-trip | 投影到统一 schema |
| `mosaic/log.py` / `mosaic/telemetry.py` | mosaic 窗级 | 投影 candidates/rejected/picked |
| 统一目标（§4.3） | sidecar `runs/layout-decisions.jsonl` | **新建**，适配器从上述投影 |

**验收**：冻结统一 schema（对齐 PRD §4.3，含 `contribution`），给出 3 套日志 → 统一 schema 的字段映射；trip.json 只存摘要 hash（§14 决议）。

---

## 3. Adapter 参数收束映射（融合核心）

`plan_screens_for_chapter` 的 15 kwargs 须由 StrategyPack 派生。W1 产出此表并在 `adapter.py` 实现：

| plan_screens_for_chapter kwarg | StrategyPack 来源 | 备注 |
|--------------------------------|-------------------|------|
| `max_per_screen` | `planning.stages` | 现常量 |
| `burst_seconds` | 现 ingest 规则 | 不归 LSE |
| `mixed_proximity_seconds` | `planning.mixed_proximity_seconds` | 直映 |
| `layout_state` | `rhythm.nine_grid_limits` → `ScreenLayoutPlannerState` | 等价复刻（W1）/ +bias（W3b） |
| `trip_photo_total` | 运行时 | — |
| `enable_mosaic` | `planning.stages.enabled` 含 mosaic + L3 `overrides.disable_stages` | L3 紧急开关 |
| `enable_portrait_grid8` / `enable_food_grid` | `planning.stages.enabled` | — |
| `preferred_hero_id` / `include_chapter_hero` | curate hero 链 | 不归 LSE（§4.8） |
| `median_sharp` | QualityFeatures（W4）/ 现值（W1） | — |
| `featured_weight` | `scoring_profiles.default` | — |

> **W1 验收**：`enabled=true` 时，adapter 从默认 pack 派生的 kwargs **逐一等于**现网默认值（审计 A 的映射表）→ parity 成立。

---

## 4. Decision Log 统一 schema（落地）

- 写入：`runs/layout-decisions.jsonl`（sidecar，异步，不阻塞主路径，AC-P17-28）；`trip.curation.layoutDecisionLog` 只存摘要 + `weightsHash`。
- schema 对齐 PRD §4.3，**`explain` 字段写 `contribution` 而非裸 weight**（§4.3 log-domain 归因）。
- 截断：`decision_log_max_events: 2000`（config）。
- 渲染隔离：C 端渲染不读此 sidecar（AC-P17-31）。

---

## 5. 阶段任务分解（切引擎与上 CAP 解耦 · R-P17-05）

| 波次 | 任务 | 出口 AC |
|------|------|---------|
| **W0** | 三项审计（§2）+ schema.json + 本文 + DESIGN-PHASE17 + 性能 spike | AC-P17-15 |
| **W1** | `layout_engine/`：registry + policy + **adapter（参数收束）** + decision_log（适配）+ validator + config 接线 + **受控 parity CI** | AC-P17-01～05 |
| **W2** | Studio Inspector（只读，§5.1.1 前端规格）+ L3 `overrides` patch（config_governance 扩 5 键，L0）| AC-P17-06、08、14 |
| **W3a** | **先切引擎**：`enabled=true`（纯收敛）+ 受控 parity + 零步 E2E + quick_share 零 diff，稳定 | AC-P17-01/02/23/27 |
| **W3b** | **再上算法**：CAP-02（§4.10 渲染绑定前置）/03/04 + golden probe + 审批+沙箱 + shadow 双轨 + dogfood | AC-P17-16～18、30、31 |
| **W4** | CAP-01 匈牙利（确定性 `max_matrix_n` + tie-break）+ CAP-08 QualityFeatures；Plus: CAP-05/06/10/14/15 | AC-P17-19、28；Plus 20～26 |
| **W5** | CAP-07/13、Editorial 联动、多包 lifecycle | Plus / P18 |

**关键依赖**：W3b 的 CAP-02 **强依赖** §4.10 渲染绑定（CSS object-position 收敛）——否则人脸完整率在像素上不生效。渲染绑定列为 W3b 前置任务。

---

## 6. 工作量估算（粗略 · 单人）

| 波次 | 估算 | 风险系数 |
|------|------|----------|
| W0 审计 + schema | 0.5–1 人周 | 中（审计可能翻出更多隐藏路径） |
| W1 引擎骨架 + adapter + parity | **2–3 人周** | 高（adapter 包 1007 行 God file + 受控 parity 改 search_budget） |
| W2 Inspector + L3 | 1.5–2 人周 | 中 |
| W3a 切引擎 | 0.5–1 人周 | 中 |
| W3b CAP-02/03/04 + 渲染绑定 + 审批沙箱 | 2.5–3.5 人周 | 高（CSS 收敛 + 乘性 contribution 改造） |
| W4 匈牙利 + QualityFeatures | 2–3 人周 | 中高 |
| **Core 关键路径合计** | **≈ 9–13.5 人周** | — |

> 比 PRD §9 名义周期偏长，主因 W1 adapter + 受控 parity 改造与 W3b 渲染绑定被低估。建议 2–3 人并行，Core 约 5–7 周。

---

## 7. W1 开工清单（Definition of Ready）

W1 开工前必须全部 ✅：

- [x] 审计 A 映射表评审通过（现网活跃参数权威值）
- [x] 审计 B 受控 parity runbook 评审通过 + AC-P17-01 口径确认
- [x] 审计 C 统一 decision log schema 冻结
- [x] `lse_strategy.schema.json` 草案就绪（W0 阻断）
- [x] `DESIGN-PHASE17-layout-strategy-engine.md` 就绪（W0 阻断）
- [x] ADR-013 审批语义对齐（W0 阻断）
- [x] `strategies/default.yaml` + `lse_policy.yaml`（对齐审计 A）
- [ ] 性能 spike 报告（各能力 × trip 规模增量）— **W3 能力开启前**，不阻断 W1
- [ ] golden trip 三类各 ≥2（家庭混排/风景横图/人像竖图）冻结快照 — W1 并行补齐
- [x] 分支 `feature/phase17-lse` 已建

**W1 可开工判定**：上表除性能 spike / golden 扩充外均已 ✅。

---

## 8. 风险登记（实施侧补充 PRD §11）

| 风险 | 触发 | 缓解 |
|------|------|------|
| 受控 parity 改 `search_budget` 引入回归 | 去 wall-clock 改变现有测试 | 审计 B 先评估回归面；改动隔离在开关后 |
| adapter 15 kwargs 收束漏项 | 某 kwarg 未映射 → 行为偏移 | §3 映射表逐一 parity 断言 |
| schema.json 与 dataclass 漂移 | 双真值源 | 加一致性测试（validator 同时校验两者） |
| 乘性 contribution 改造影响 mosaic 打分 | 改 scorer 输出 | contribution 仅"附加输出"，不改 total 计算 |
| CSS object-position 收敛触发 render 快照大面积 diff | §4.10.1 | 先豁免清单 + 截图回归逐 pattern 灰度 |

---

## 10. W1 任务清单（优先级序 · 执行跟踪）

| 优先级 | ID | 任务 | 产出 | AC | 状态 |
|--------|-----|------|------|-----|------|
| P0 | W1-01 | `LayoutStrategyEngineConfig` + `config.yaml.example` 接线 | `config/layout.py` | — | ✅ |
| P0 | W1-02 | `registry.py` 加载 pack + policy + contentHash | `layout_engine/registry.py` | AC-P17-03 | ✅ |
| P0 | W1-03 | `validator.py` schema 门禁 + default.yaml CI | `cli validate` | AC-P17-02 | ✅ |
| P0 | W1-04 | `adapter.py` 防腐层 + §3 十五 kwargs 收束 | `screen_planner_attach.py` 3 处 | AC-P17-01/02 | 🟡 薄包装已接；kwargs 全量映射待补 |
| P0 | W1-05 | `search_budget` 挂钟改 telemetry-only | `search_budget.py` + 测试改写 | 审计 B | ✅ |
| P1 | W1-06 | `decision_log.py` sidecar + mosaic 投影 | `runs/layout-decisions.jsonl` | AC-P17-04/05 | 待办 |
| P1 | W1-07 | 受控 parity CI `test_p17_controlled_parity.py` | golden 快照 | AC-P17-01 | 待办 |
| P1 | W1-08 | `weights_hash` + `strategyId` 写入 trip 摘要 | `curation.layoutStrategy` | AC-P17-04 | 待办 |
| P2 | W1-09 | golden 人像/风景 fixture 各 ≥2 | `tests/fixtures/` | §10.3 | 待办 |
| P2 | W1-10 | `enabled=false` 默认；文档与 Studio 开关说明 | — | AC-P17-01 | 待办 |

**执行顺序**：W1-01 → 02 → 03（可并行 02/03）→ 04 → 05 → 06 → 07 → 08；09/10 与 P0 并行。

**W1 出口**：AC-P17-01～05 通过；`enabled=false` 与 `enabled=true`（纯收敛）受控 parity 绿。

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2 | 2026-06-07 | W0 冻结：DoR 勾选、§10 W1 任务清单、状态更新 |
| v0.1 | 2026-06-07 | W0 起草：融合设计、三项 W0 审计模板、adapter 参数收束、decision log 适配、切引擎/上 CAP 解耦的阶段分解、工作量、W1 DoR |
