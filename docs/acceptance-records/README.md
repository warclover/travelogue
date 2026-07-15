# 验收记录索引

| 属性 | 内容 |
|------|------|
| **权威入口** | [ACCEPTANCE.md](../ACCEPTANCE.md)（单轨） |
| **更新日期** | 2026-06-06 |

> JSON / Markdown 记录供 Phase 验收签字与脚本写入；**发布闸门以各 Phase ACCEPTANCE 文档为准**。

---

## Algorithm V2（封面/heuristic 评分）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [algorithm-v2-signoff.json](./algorithm-v2-signoff.json) | A-M1/A-M7 自动化 + R0' 盲评模板 | `python scripts/algorithm_v2_signoff.py --score-automated --write --extended` |
| [algorithm-v2-prd-review-2026-06-05.md](./algorithm-v2-prd-review-2026-06-05.md) | PRD 评审纪要 | — |

门禁：`python scripts/algorithm_v2_signoff.py --from-json docs/acceptance-records/algorithm-v2-signoff.json` · A-M4 权威单测 `tests/test_cover_scoring_v2_gates.py` · Kendall 报告 [`../reports/algorithm-v2-kendall.md`](../reports/algorithm-v2-kendall.md)

---

## Phase 15（Mosaic v2 · S1）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase15-curate-replay.json](./phase15-curate-replay.json) | curate 回放记录（fixture trip） | `python scripts/phase15_curate_replay.py golden-mixed-scenes --fixture --write …` |
| [phase15-replay-scenarios.json](./phase15-replay-scenarios.json) | 多场景 MCS 回放 | `python scripts/phase15_replay_scenarios.py --write …` |
| [phase15-mosaic-eval.json](./phase15-mosaic-eval.json) | mosaic5 A/B 曝光 | `python scripts/phase15_mosaic_eval.py --write …` |

门禁：`python scripts/phase15_unified_gate.py` · bundle：`python scripts/phase15_acceptance_bundle.py --skip-pytest`

文档入口：[IMPLEMENTATION-PHASE15.md](../IMPLEMENTATION-PHASE15.md) · [ACCEPTANCE-PHASE15.md](../ACCEPTANCE-PHASE15.md)

---

## Phase 13（模板系统化 · P13.1）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase13-gate-signoff.json](./phase13-gate-signoff.json) | G1–G9 开发环境 Smoke 汇总（`go` 字段） | `python scripts/phase13_gate_signoff.py --write docs/acceptance-records/phase13-gate-signoff.json` |
| [phase13-route-eval.json](./phase13-route-eval.json) | 注册表健康 + 回放快照字段 | `python scripts/phase13_template_route_eval.py --check-registry-health --trip-json schemas/fixtures/trip.render_golden.json --seed-selection --write …` |
| [phase13-admin-audit.json](./phase13-admin-audit.json) | 审计覆盖检查 | `python scripts/phase13_admin_audit_check.py --write …` |
| [phase13-rollback-drill.json](./phase13-rollback-drill.json) | 回滚演练记录（R1–R6） | `python scripts/phase13_rollback_drill.py --write …` |
| [phase13-metrics-24h.json](./phase13-metrics-24h.json) | G6 24h 指标窗口（可 `--dev-relaxed`） | `python scripts/phase13_metrics_window.py --hours 24 --write …` |
| [phase13-metrics-72h.json](./phase13-metrics-72h.json) | G6 GA 前置 72h（生产勿 `--dev-relaxed`） | `python scripts/phase13_metrics_window.py --hours 72 --write …` |
| [phase13-metrics-72h-gate-template.json](./phase13-metrics-72h-gate-template.json) | 72h 字段归档模板（`--empty-window`，非生产数据） | `… --hours 72 --empty-window --write …` |
| [phase13-g8-signoff.json](./phase13-g8-signoff.json) | G8 走查 + 自动化 prereq（**dev-only**，非生产签字） | `python scripts/phase13_g8_walkthrough_automated.py --playwright --sign-if-pass --write …` |
| [phase13-release-day-gate-section5.json](./phase13-release-day-gate-section5.json) | REL-03 发布日 Gate §5 | `python scripts/phase13_release_day_gate_section5.py --write …` |
| [phase13-rollback-drill-prod-staging.json](./phase13-rollback-drill-prod-staging.json) | REL-15 预发 state 演练 | `phase13_rollback_drill.py --use-project-state --write …` |
| [phase13-release-day-checklist.json](./phase13-release-day-checklist.json) | P0 汇总 | `python scripts/phase13_p0_release_finalize.py` |
| [phase13-rollback-drill-staging.json](./phase13-rollback-drill-staging.json) | 预发演练（可选） | `phase13_rollback_drill.py --use-project-state --write …` |

文档入口：[ACCEPTANCE-PHASE13.md](../ACCEPTANCE-PHASE13.md) · [phase13-pilot-retro.md](../reports/phase13-pilot-retro.md) · [phase13-template-dashboard.md](../reports/phase13-template-dashboard.md)

---

## Phase 12（静默自治选片增强 · 指标链路）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase9-golden-cull-signoff.json](./phase9-golden-cull-signoff.json) | golden 运行记录（单 trip 级）：含 `mlFallbackRateL1`、`branchFallbackRateL2`、`branchFallbackByReasonL2`、`failOpenRateL3`、分支覆盖率、`cpuMs` | `python scripts/phase9_golden_cull_signoff.py --all --write docs/acceptance-records/phase9-golden-cull-signoff.json` |
| [phase9-eval-baseline.json](./phase9-eval-baseline.json) | 离线汇总基线（跨 trip 聚合）：含 `l1_ml_fallback_rate`、`l2_branch_fallback_rate`、`l2_branch_fallback_by_reason`、`l3_fail_open_rate` | `python scripts/phase9_eval_baseline.py --golden docs/acceptance-records/phase9-golden-cull-signoff.json --quality docs/acceptance-records/phase9-quality-gate.json --write docs/acceptance-records/phase9-eval-baseline.json` |
| [phase12-eval-baseline.json](./phase12-eval-baseline.json) | P12 合成 cull + `category_coherence` 门禁 | `python scripts/phase12_eval_baseline.py --write docs/acceptance-records/phase12-eval-baseline.json` |
| [phase12-latency.json](./phase12-latency.json) | rules cull CPU 时延 P50/P95 | `python scripts/phase12_latency_profile.py --write docs/acceptance-records/phase12-latency.json` |
| [phase9-ml-acceptance.json](./phase9-ml-acceptance.json) | P9 W2 ML 验收（pyiqa/GPU；无依赖时 skipped） | `python scripts/phase9_ml_acceptance.py --write docs/acceptance-records/phase9-ml-acceptance.json` |

字段对照入口：

- 运行时字段：[`../ACCEPTANCE-PHASE9.md` §5.1](../ACCEPTANCE-PHASE9.md)
- 实施口径：[`../IMPLEMENTATION-PHASE12.md`](../IMPLEMENTATION-PHASE12.md)
- PRD 口径：[`../PRD-PHASE12.md`](../PRD-PHASE12.md)

---

## Phase 10（Food Grid）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase10-food-grid.json](./phase10-food-grid.json) | AC-P10 自动验收 + AC-P10-03 人工 fixture 规格（可附带 demo verify） | `python scripts/phase10_food_grid_acceptance.py --write docs/acceptance-records/phase10-food-grid.json`（可加 `--include-demo-verify`） |

---

## Phase 7（性能专项 · 开发准备）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase7-perf-eval.json](./phase7-perf-eval.json) | AC-P7 分阶段性能 + NR-P7 | `python scripts/phase7_pipeline_perf.py --write` |
| [phase7-rollout-log.json](./phase7-rollout-log.json) | G0-G3 灰度与回滚 | 手动记录 + 发布值班更新 |

---

## Studio 首页 v2（M20）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [studio-homepage-v2-rollout-log.json](./studio-homepage-v2-rollout-log.json) | G0–G2 holdback / 切主站 | [SIGNOFF-M20J.md](../studio-homepage-v2/SIGNOFF-M20J.md) |
| — | M21 dogfood 自动化 | `python scripts/m21_dogfood_gate.py --skip-e2e`（CI validate）；全量含 rollback |
| — | M21 发布后路由 smoke | `python scripts/m21_deploy_smoke.py --base http://HOST:8766` |
| [studio-homepage-v2-visual/](./studio-homepage-v2-visual/) | 视觉 sign-off PNG（gitignore 生成物） | `python scripts/studio_ac_visual_capture.py` |
| `studio-homepage-v2-rollback-drill.json` | 回滚演练报告（按需生成） | `python scripts/studio_homepage_rollback_drill.py --out …` |

---

## Phase 6（开发准备）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase6-quality-eval.json](./phase6-quality-eval.json) | AC-P6 / BR-P6 指标记录 | `python scripts/phase6_metrics_baseline.py --summary --write` |
| [phase6-rollout-log.json](./phase6-rollout-log.json) | G0-G3 灰度与回滚日志 | 手动记录 + 发布值班更新 |

---

## Phase 5（当前生产闸门）

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase5-zero-edit.json](./phase5-zero-edit.json) | UX-P5-80-01 零编辑计时 | 手测填写 |
| [phase5-scroll-qualitative.json](./phase5-scroll-qualitative.json) | UX-P5-SCROLL-01 卷轴定性 | 3–5 人手测 |
| [phase5-layout-sprint.json](./phase5-layout-sprint.json) | P5-QS-01 排版冲刺（模板） | `python scripts/phase5_layout_sprint.py --record …` 写入 `phase5-layout-sprint.local.json`（gitignore） |
| [phase5-peval.json](./phase5-peval.json) | P5-8.1 排版盲评 | `python scripts/phase5_blind_review.py <tripId>` |
| [phase5-webview-manual.json](./phase5-webview-manual.json) | P5-MP-2 本地 web-view 手测 | 见 [API-MINIAPP.md](../API-MINIAPP.md) §11 |

---

## Phase 4

| 文件 | 用途 | 命令 / 说明 |
|------|------|-------------|
| [phase4-intent.json](./phase4-intent.json) | P-EVAL · intent 盲评 + 关键词覆盖 | 人工填写 |
| — | AC-P4-02/05 · A11Y 静态守卫 | `python scripts/phase4_acceptance_gate.py --skip-integration` |
| — | AC-P4-02 FirstSuccess e2e | `pytest tests/test_studio_intent_ac_p4_playwright.py -m e2e`（CI `test-e2e` job） |

---

## Phase 3

| 文件 | 用途 |
|------|------|
| [phase3-m12-0-spike.json](./phase3-m12-0-spike.json) | 聚类算法 Spike |
| [phase3-m12-5-cache.json](./phase3-m12-5-cache.json) | 增量 ingest cache |
| [phase3-m13-bench.json](./phase3-m13-bench.json) | P3-Full 性能 |
| [phase3-m13-ig2.json](./phase3-m13-ig2.json) | I-G2 排版质量 |
| [phase3-layout-acceptance.json](./phase3-layout-acceptance.json) | legacy vs beam 客观对比 |
| [phase3-blind-review.json](./phase3-blind-review.json) | Phase 3 盲评包索引 |
| [phase3-weight-experiment.json](./phase3-weight-experiment.json) | 权重实验 |

---

## Phase 2 / Phase 1

| 文件 | 用途 |
|------|------|
| [phase2-layout-compare.json](./phase2-layout-compare.json) | Phase 2 beam 对比 |
| [phase1-layout-equivalence.json](./phase1-layout-equivalence.json) | scoring 等价护栏 |

---

## 真实 trip 手测笔记

| 文件 | trip |
|------|------|
| [linzhi.md](./linzhi.md) | linzhi |
| [mao.md](./mao.md) | mao |
| [maomi.md](./maomi.md) | maomi |

---

## 稳定期质量硬化（Stable-QH）

| 文件 | 用途 |
|------|------|
| [stable-qh-prd-review-2026-07-15.md](./stable-qh-prd-review-2026-07-15.md) | PRD v1.1 六席评审纪要 |
| [stable-qh-2026-07-15.md](./stable-qh-2026-07-15.md) | M1–M5 落地验收记录 |

门禁命令见 [QUALITY-GATE.md · 稳定期质量硬化](../QUALITY-GATE.md)。
