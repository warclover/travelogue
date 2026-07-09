# ADR-015 · LSE 与 Screen Planner 两步渐进迁移

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted**（2026-07-08 批准；M-B4b 可启动，须 M-B4a 完成 + golden 门禁） |
| **日期** | 2026-07-08 |
| **决策者** | 技术负责人（**待签字**） |
| **影响范围** | `travelogue/layout_engine/`、`travelogue/curation/`（`screen_planner*`、`mosaic/`、`layout_search.py`）、`travelogue/layout_contract/` |
| **关联** | [PRD-ARCH-OPTIMIZATION.md](../PRD-ARCH-OPTIMIZATION.md) §5.2 · [PRD-PHASE17-layout-strategy-engine.md](../PRD-PHASE17-layout-strategy-engine.md) R-P17-04 · [ADR-010](./010-tech-debt-sprint.md) D5 · [TECH-ARCHITECTURE.md](../TECH-ARCHITECTURE.md) §18 |

---

## 背景

1. Phase 17 引入 **Layout Strategy Engine（LSE）** 后，`layout_engine/` 与 `curation/screen_planner*` 形成 **双向 cross-import**（adapter 入口 + mosaic scorer 回指 LSE 特征），与目标分层 DAG（PRD §5.3.1：同层互访仅经 `layout_contract` DTO 与 adapter）冲突。
2. Phase 17 **R-P17-04** 裁定 MCS 作为 LSE 子模块 **保留在 `curation/mosaic/`**，经 `layout_engine/adapter.py` 统一入口。
3. **ADR-010 D5** 裁定屏规划采用 **阶段模块 + 单入口薄包装**，`screen_planner.py` 留在 `curation/`，不整文件迁移。
4. 架构优化 PRD v1.1（评审 B-03/B-04）将路线修订为 **两步渐进**：M-B4a kernel 抽取 + adapter 收敛（**无需本 ADR 批准即可启动**）；M-B4b planner/MCS **物理迁移**（**必须本 ADR 批准**）。
5. 2026-07-08 基线实测：`layout_engine ↔ curation` 共有 **51** 条 direct cross-import 边（见 §量化判据）；M-B4a 后须复测，若仍无法降至基线的 ≤20%，则 **关闭 M-B4b**，维持 adapter 方案。

---

## 待决问题

1. 本 ADR 对 **R-P17-04**、**ADR-010 D5** 的 supersede 边界是否可接受？
2. M-B4b 物理迁移是否在 **cross-import 下降 ≥80%** 的前提下启动？
3. **`compose_trip`** 与 **`layout_search.py`** 是否随 planner/MCS 同迁至 `layout_engine/`（PRD Q-06）？
4. 回退开关 **`layout.planner_impl`** 的默认值与删除 DoD（§3.3）是否认可？

---

## Supersede 声明

### 对 R-P17-04（MCS 留 curation）— **部分 supersede**

| 保留 | 修订 |
|------|------|
| MCS 仍是 LSE **子模块**，不是第三套排版引擎 | **物理路径**由 `curation/mosaic/` 迁至 `layout_engine/mosaic/`（M-B4b） |
| 对外仍经 **`layout_engine/adapter.py` 单一入口** | `curation/mosaic/` 仅保留 **shim re-export** + `DeprecationWarning`，直至 §3.3 DoD |
| `compose_trip` 语义不变（trip 级 beam 编排） | 实现文件随 MCS 同包迁移（见 §归属裁定） |

**不 supersede**：MCS 与 LSE 的 **从属关系**（子模块，非独立引擎）。

### 对 ADR-010 D5（渐进 + adapter 薄包装）— **部分 supersede**

| 保留 | 修订 |
|------|------|
| M-B4a 仍做 **阶段模块边界**（`screen_planner_stages` 三文件结构不变） | 不再承诺「`screen_planner.py` **永久**留在 curation」 |
| adapter **薄包装** 在 M-B4a 收敛为 **唯一规划入口** | M-B4b 将三文件 + MCS **物理迁入** `layout_engine/planner/`、`layout_engine/mosaic/` |
| 回归：`plan_screens_for_chapter` 等公开符号经 shim 兼容 | shim 列表 = 现有 `screen_planner.py` L24-35 re-export **全量** |

**不 supersede**：ADR-010 D1–D4、D6–D7（handlers、AppContext、render 分层等）。

---

## 决策

### D1 · 两步路线

#### 第一步 M-B4a（kernel + adapter，**已授权，无需本 ADR 签字**）

| 项 | 内容 |
|----|------|
| kernel | `AspectKind`、`layout_constraints`、`screen_layout_state` 等共享原语抽入 `layout_contract/` |
| adapter | `ChapterPlanRequest` 扩为完整规划参数面；`screen_planner_attach ↔ adapter` 三角依赖改单向 |
| mosaic | `_mosaic_cfg_override` / `_disabled_pattern_ids` → `ContextVar`（与 `mosaic/hook.py` 对齐） |
| 改名 | `render_contract.py` → `render_fingerprint.py`（不并入 layout_contract） |

#### 第二步 M-B4b（物理迁移，**仅 ADR 批准后**）

| 迁移对象 | 目标路径 |
|----------|----------|
| `screen_planner.py` / `screen_planner_stages.py` / `screen_planner_attach.py` | `layout_engine/planner/`（**保持三文件边界**） |
| `curation/mosaic/` 包 | `layout_engine/mosaic/` |
| `curation/layout_search.py` | `layout_engine/planner/layout_search.py`（见 D3） |
| `curation/mosaic/trip.py::compose_trip` | `layout_engine/mosaic/trip.py`（见 D3） |

**约束**：**算法语义不变**——允许破环 import 重排（含 E402 lazy import）；**禁止**改常量表顺序、`sorted` key 顺序、float 累加顺序。

**shim**：原 `curation.*` 路径保留 re-export + `DeprecationWarning`；删除时机 = PRD §3.3 开关 DoD（4 周 + 双跑 diff 全空）。

### D2 · 量化判据（Go/No-Go for M-B4b）

**采集方式**：

```bash
python scripts/lse_cross_import_stats.py
# → docs/acceptance-records/lse-cross-import-baseline.json
```

**2026-07-08 基线（AST，含函数内 import）**：

| 指标 | 值 |
|------|-----|
| `layout_engine → curation` 边数 | **32** |
| `curation → layout_engine` 边数 | **19** |
| **合计 cross-import 边** | **51** |
| M-B4b 目标（下降 ≥80%） | **≤ 10** 条 |

**流程**：

1. M-B4a 完成后 **必须** 重跑 `lse_cross_import_stats.py` 并附 JSON。
2. 若 post-B4a 边数 **仍 > 10**（即降幅 <80%），**No-Go**：关闭 M-B4b，维持 adapter + shim，本 ADR 标记 **Partially Accepted（仅 B4a）**。
3. M-B4b 完成后边数 **≤ 10**，且 golden 三重门禁全绿（`layout_snapshot` · `phase17_golden_metrics.py` · mosaic decision log 签名）。

**高频边（迁移重点）**：`curate`↔`adapter`（7+4 边）、`mosaic.scorer`↔LSE features（5 边）、`metrics`/`sandbox` 内嵌 curate 管线（实验路径，M-B4a 标注后不扩散）。

### D3 · `compose_trip` 与 `layout_search.py` 归属（PRD Q-06）

**建议裁定：随 planner/MCS 同迁 `layout_engine/`**。

| 模块 | 理由 |
|------|------|
| `mosaic/trip.py::compose_trip` | Trip 级 MCS beam 入口；与 `mosaic/search.py` 同域；留 `curation/` 会保留第三条边界（评审 I-05 禁止） |
| `layout_search.py` | Beam wrapper 紧耦合 `mosaic.search.replan_day_buckets_beam` 与 `layout_planner.AspectKind`；与 screen planner 同生命周期 |
| shim | `curation.mosaic.compose_trip`、`curation.layout_search` re-export 至删除 DoD |

**不采纳**：将 `compose_trip` 留在 `curation/` 而只迁 screen planner——会在 `curate.py` 保留对 curation 内 beam 编排的硬依赖，cross-import 无法达标。

### D4 · 回退路径

| 开关 | 值 | 行为 |
|------|-----|------|
| `layout.planner_impl` | `layout_engine`（默认，M-B4b 上线后） | 经 `layout_engine/planner` + adapter |
| | `curation` | 回退 shim 路径（`curation.screen_planner` re-export） |

- CI：**默认只跑 `layout_engine` 路径**；legacy `curation` 路径每周定时 job 双跑（PRD §3.3）。
- 删除 shim：开关满 4 周 + 双跑 diff 全空 + 无 dogfood 回退需求（M-D1）。

### D5 · 验收（AC-ARC-08v2）

1. `curation/` **不再持有** screen 规划实现（shim 除外）。
2. cross-import 边数 ≤ ADR 判据（§D2）。
3. `arch_equivalence_check` · `phase17_golden_metrics.py` · mosaic decision log 签名一致。

---

## 后果

### 正面

- 消除 planner/LSE 双向依赖主因，import-linter 同层契约可逐步收紧（M-B1）。
- MCS 与 LSE 代码邻接，adapter 真正「薄」；评审 R-15 实验路径（sandbox/metrics）可标注隔离。

### 负面

- M-B4b 为 **大规模 `git mv`**，与 M-C2（tests 分层）**不得同期**（PRD R-04）。
- shim 期 import 路径翻倍，阅读成本上升（与 ADR-010 后果类似）。
- 若 B4a 后 cross-import 降幅不足，团队需接受 **B4b 永久搁置** 的架构债。

---

## 验证计划

- [x] 基线 cross-import 统计脚本 `scripts/lse_cross_import_stats.py`
- [x] 基线 JSON `docs/acceptance-records/lse-cross-import-baseline.json`（51 边）
- [x] **决策者批准**本 ADR（Proposed → Accepted · 2026-07-08）
- [x] M-B4a / M-B4b / batch-6 后复测：合计 **7** 边（curate→adapter 白名单）
- [x] 2026-07-09 合并闸门 hotfix 后基线校正为 **8**（+1 `layout_engine.scoring.hero` → `curation.curate_scoring`；aesthetic adapter 已下沉 `layout_contract`，不再计边）
- [x] M-B4b 完成后 AC-ARC-08v2：边数 ≤10 ✅；shim 退役仍属后续 DoD

### 附录 · post-hotfix 边数（2026-07-09）

| 方向 | 边数 | 说明 |
|------|------|------|
| curation → layout_engine | 7 | intentional adapter 白名单 |
| layout_engine → curation | 1 | hero scoring adapter（正确性热修；待内核下沉） |
| **合计** | **8** | 仍满足 ADR D2 ≤10 |

刷新命令：`python scripts/lint_lse_cross_import.py --update-baseline`（只降不升棘轮）。

---

## 参考

- [PRD-ARCH-OPTIMIZATION.md](../PRD-ARCH-OPTIMIZATION.md) §5.2.0–§5.2.2 · §3.3 · Q-06
- [PRD-PHASE17-layout-strategy-engine.md](../PRD-PHASE17-layout-strategy-engine.md) R-P17-04
- [ADR-010](./010-tech-debt-sprint.md) D5
- `scripts/lse_cross_import_stats.py` · `docs/acceptance-records/lse-cross-import-baseline.json`
