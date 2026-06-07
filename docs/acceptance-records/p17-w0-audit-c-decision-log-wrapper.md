# P17 W0 审计 C — Decision Log 包装方案

| 属性 | 内容 |
|------|------|
| **审计 ID** | P17-W0-C |
| **日期** | 2026-06-07 |
| **分支** | `feature/phase17-lse` |
| **状态** | 待评审 |
| **配套** | PRD §4.3、§14；IMPLEMENTATION-PHASE17 §4 |

---

## 1. 结论摘要

| 问题 | 结论 |
|------|------|
| 统一 schema 策略？ | **新建 sidecar** + **适配器投影**现有 3 套；不替换 MCS/beam 内部写日志 |
| trip.json 存什么？ | **摘要 only**：`strategyId` + `weightsHash` + `decisionLogDigest`（sha256 前 16 位） |
| 全量日志存哪？ | `runs/layout-decisions.jsonl`（异步 append） |
| `explain` 口径？ | **log-domain `contribution`**（W3b 实现）；W1 可先写空 `explain`，占位 schema |
| 渲染隔离？ | C 端不读 sidecar / digest（AC-P17-31） |

---

## 2. 现有三套日志盘点

### 2.1 `LayoutDecisionLog`（`curation/decision_log.py`）

**触发**：`mosaic/search.py` beam replan（仅 `layout.scoring.enabled=true`）

**存储**：`trip.curation.layoutDecisionLog` — `list[dict]`，每元素一章/日桶

**结构**：

```json
{
  "chapterId": "day-bucket-1",
  "startedAt": "2026-06-07T12:00:00Z",
  "events": [
    {
      "type": "beam_pick",
      "at": "2026-06-07T12:00:01Z",
      "variant": "with_hero",
      "candidateCount": 4,
      "score": { "total": 0.82, "layout_rhythm": 0.9, "diversity": 0.7 },
      "legacyScore": { "total": 0.75 },
      "changed": true,
      "arcProfile": "dynamic",
      "fallbackUsed": false,
      "fallbackReason": null,
      "plannerPath": "beam"
    }
  ]
}
```

**现网默认**：`layout.scoring.enabled=false` → **通常为空**

### 2.2 `MosaicWindowLog`（`mosaic/log.py` + `compose.py`）

**触发**：MCS 窗级 `pick_best_window`（**默认路径活跃**）

**存储**：`trip.curation.mosaicDecisionLog` — `list[dict]`（经 `format_log_entry` 按 `mosaic.log_level` 裁剪）

**log_level=window`（默认）结构**：

```json
{
  "routerVersion": "p15-mcs-1",
  "segmentId": "seg-03",
  "windowSize": 5,
  "windowStart": 12,
  "candidatesCount": 8,
  "winnerPatternId": "screen-mosaic-5-main-hero-plus-4",
  "winnerScore": 0.7241,
  "winnerReasonCodes": ["R_TIME_COHESION", "R_RHYTHM_OK"],
  "fallbackUsed": false,
  "fallbackReason": null,
  "selfHealApplied": false,
  "plannerPath": "mosaic",
  "scorerVersion": "p15-s2",
  "weightsHash": "sha256:abc123…",
  "geometryRejectedTemplates": [{ "templateId": "…", "reason": "geometry_invalid" }]
}
```

**debug 模式**：`mosaic.log_level=debug` 时含 `top3Patterns`/`top3Scores`/`rejectedTemplates`；可 merge 入 `layoutDecisionLog`（`curate.py:978-983`）

### 2.3 `mosaic/telemetry.py`（聚合层 · 非 trip 字段）

**触发**：curate 后 `record_mosaic_layout_metrics` / `record_per_template_layout_metrics`

**存储**：`template-metrics.jsonl`（Studio templating 指标管道）

**性质**：由 `mosaicDecisionLog` **派生**的 KPI（exposure_share、face_crop_proxy_rate 等），**不是**决策原始记录

**处置**：LSE Inspector 可读；**不投影**到统一 window schema（保持 telemetry 分层）

---

## 3. 冻结统一 Sidecar Schema（PRD §4.3 对齐）

**文件**：`{trip_dir}/runs/layout-decisions.jsonl`（每行一条 JSON）

```json
{
  "schemaVersion": 1,
  "strategyId": "lse-default-2026-06",
  "strategyRevision": 0,
  "weightsHash": "sha256:…",
  "algorithmVersion": "p15-s2",
  "chapterId": "ch-03",
  "segmentId": "seg-12",
  "window": { "start": 12, "size": 5 },
  "candidates": [
    {
      "patternId": "screen-mosaic-5-hero-3-2-plus-4",
      "score": 0.72,
      "reasons": ["R_TIME_COHESION"]
    }
  ],
  "rejected": [
    { "patternId": "screen-portrait-5", "reason": "slot_geometry" }
  ],
  "picked": { "patternId": "screen-mosaic-5-hero-3-2-plus-4", "score": 0.72 },
  "layoutState": {
    "nine_used": 2,
    "nine_max": 5,
    "last_kind": "triple",
    "layout_density": "balanced"
  },
  "explain": {
    "topFactors": [
      { "name": "temporal_coherence", "contribution": 0.12, "value": 0.85 }
    ],
    "penalties": [
      { "name": "face_crop", "contribution": -0.08, "risk": 0.85 }
    ]
  },
  "meta": {
    "source": "mosaic_window",
    "plannerPath": "mosaic",
    "fallbackReason": null,
    "emittedAt": "2026-06-07T12:00:00Z"
  }
}
```

### 3.1 字段约束（W0 冻结）

| 字段 | 约束 |
|------|------|
| `explain.topFactors[].contribution` | log-domain 加性分解；**禁止**裸 `weight` |
| `explain.penalties[].contribution` | ≤ 0；乘性惩罚 `log(1 - p·risk)` |
| `candidates` | Top-K（默认 K=3）；完整列表仅 `meta.source=beam` debug |
| `layoutState` | `ScreenLayoutPlannerState` 快照（pick 后） |
| `meta.source` | `mosaic_window` \| `beam_bucket` \| `stage_reject` |
| 截断 | `decision_log_max_events: 2000`；超限丢最旧 + telemetry 计数 |

### 3.2 trip.json 摘要（FR-P17-TRACE）

```json
{
  "curation": {
    "layoutStrategy": {
      "strategyId": "lse-default-2026-06",
      "strategyRevision": 0,
      "weightsHash": "sha256:…",
      "decisionLogDigest": "sha256:…",
      "decisionLogPath": "runs/layout-decisions.jsonl",
      "eventCount": 42
    }
  }
}
```

**不写入**（AC-P17-31）：全量 `candidates`/`explain` 不进 trip.json

---

## 4. 三套日志 → 统一 Schema 字段映射

### 4.1 `MosaicWindowLog` → 统一 schema（主路径 · W1 必做）

| 统一字段 | MosaicWindowLog 来源 | 变换 |
|----------|---------------------|------|
| `chapterId` | — | 由 hook 上下文注入（W1 adapter 补） |
| `segmentId` | `segmentId` | 直映 |
| `window.start` | `windowStart` | 直映 |
| `window.size` | `windowSize` | 直映 |
| `candidates[].patternId` | `top3Patterns[]` | debug 有全量；window 级仅 top3 |
| `candidates[].score` | `top3Scores[]` | 与 pattern  zip |
| `candidates[].reasons` | — | W3b 从 `score_candidate` 补 |
| `rejected[]` | `geometryRejectedTemplates` / `rejectedTemplates` | `{patternId, reason}` |
| `picked.patternId` | `winnerPatternId` | 直映 |
| `picked.score` | `winnerScore` | 直映 |
| `layoutState` | hook 上下文 `layout_state` | pick 后快照 |
| `explain` | — | W3b：`log(contribution)` 从 `MosaicScoreResult` |
| `meta.source` | 常量 | `"mosaic_window"` |
| `meta.plannerPath` | `plannerPath` | `mosaic` \| `legacy` |
| `meta.fallbackReason` | `fallbackReason` | 直映 |
| `weightsHash` | `weightsHash` | 直映 |
| `algorithmVersion` | `scorerVersion` | 直映 |

### 4.2 `LayoutDecisionLog`（beam）→ 统一 schema

| 统一字段 | beam `events[]` 来源 | 变换 |
|----------|---------------------|------|
| `chapterId` | `chapterId` | `day-bucket-N` → 映射真实章 ID（W1） |
| `segmentId` | — | 可用 `day-bucket-{N}` |
| `window` | — | beam 为日桶级；`size=len(bucket)` |
| `candidates` | `candidateCount` + 无明细 | W1 仅计数；W2+ 补候选列表 |
| `picked` | `score.total` + `variant` | `variant` → meta |
| `rejected` | — | 空 |
| `layoutState` | — | beam 后 `_apply_winning_plan_to_state` 快照 |
| `explain.topFactors` | `score` breakdown 字段 | W3b：各因子 `contribution`（加性链） |
| `meta.source` | 常量 | `"beam_bucket"` |
| `meta.plannerPath` | `plannerPath` | `beam` \| `legacy` |
| `meta.fallbackReason` | `fallbackReason` | `BUDGET_EXHAUSTED` / `search_timeout` |

### 4.3 `mosaic/telemetry` → 统一 schema

| 结论 | 说明 |
|------|------|
| **不映射** | telemetry 为聚合 KPI，无 window 级候选细节 |
| **关联** | Inspector 用 `tripId` + `templateId` join sidecar 与 metrics |

### 4.4 Stage 级 reject（W2+ 占位）

`ChapterScreenPlanner` 分支 reject（如 rhythm block）当前**无结构化日志**。

| 统一字段 | 来源（待 W2 插桩） |
|----------|-------------------|
| `meta.source` | `"stage_reject"` |
| `rejected[].reason` | `rhythm_block` \| `quota_exhausted` \| `pattern_disabled` |
| `picked` | null |

---

## 5. 适配器架构（W1 落地）

```
layout_engine/decision_log.py
  ├─ emit_unified(event: LayoutDecisionEvent)  → append jsonl（异步队列）
  ├─ project_mosaic_window(log: MosaicWindowLog, ctx) → LayoutDecisionEvent
  ├─ project_beam_bucket(log: LayoutDecisionLog, ctx) → LayoutDecisionEvent
  ├─ finalize_trip_digest(trip_dir) → decisionLogDigest
  └─ query(filters) → Inspector API（W2）

挂接点（不改 MCS/beam 内部逻辑）：
  mosaic/hook.py drain_mosaic_logs() 之后 → project_* 批量 emit
  curate.py replan_meta.decisionLogs 之后 → project_beam_* emit
```

**W1 最小实现**：

1. schema + `emit` + mosaic 投影（`explain` 空对象）
2. trip 摘要 `layoutStrategy.weightsHash`（从 `mosaic.scorer.weights_hash`）
3. 保留现有 `mosaicDecisionLog` / `layoutDecisionLog` **双写**（兼容期 W1–W2）

**W2 退役**：Studio 改读 sidecar；trip 内旧字段标记 deprecated

**W3b**：`scorer.py` 附加 `contributions: dict` → 填满 `explain`

---

## 6. log-domain contribution 计算备忘（W3b · PRD §4.3）

```text
# 加性 base（score_screen_plan）
contribution_i = w_i_normalized * f_i

# 乘性惩罚（score_candidate）
contribution_j = log(1 - penalty_weight_j * risk_j)   # ≤ 0

# topFactors = 按 contribution 降序 Top-3（正向）
# penalties  = contribution < 0 的项
```

**约束**：`contribution` 仅附加输出，**不改变** `MosaicScoreResult.total` 计算（NG-P17-07）。

---

## 7. 与现有测试的兼容

| 测试 | 影响 | 策略 |
|------|------|------|
| `test_chapter_explain.py` | 读 `layoutDecisionLog` | W1 保留旧字段；explain 仍可用 |
| `test_lte_p3_gaps.py` | debug merge | 双写期不变 |
| `test_phase5_peval.py` | beam_pick events | 不变 |

---

## 8. 签收

| 角色 | 签名 | 日期 |
|------|------|------|
| 开发负责人 | （待评审） | |
| 架构 | （待评审） | |
| 前端/Inspector | （待评审） | |
