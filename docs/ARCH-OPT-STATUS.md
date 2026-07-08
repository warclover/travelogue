# 架构优化 · 里程碑状态追踪

> 配套 [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) v1.1 · 执行提示词见 [PROMPTS-ARCH-OPTIMIZATION.md](./PROMPTS-ARCH-OPTIMIZATION.md)

**当前分支**: `arch/optimization-ws1`  
**最后更新**: 2026-07-08（M-C6 命名消歧 done）

## 里程碑总表

| 里程碑 ID | 状态 | 完成日期 | 证据摘要 | 遗留项 |
|-----------|------|----------|----------|--------|
| M-A0 | done | 2026-07-08 | `python scripts/_m_a0_config_equivalence_check.py` 全绿；无重复顶层键；load_config 与合并前后段生效值一致 | — |
| M-A1a | done | 2026-07-08 | `pytest tests/test_trip_service_update.py` 7 passed | — |
| M-A1b | done | 2026-07-08 | handlers 14 处 + serve.py 2 处改 svc.update；409 E_TRIP_CONFLICT + http.js 重试；`pytest tests/test_studio_handlers_trip.py` 等 41 passed | — |
| M-A1c | done | 2026-07-08 | studio_pipeline 5 处 + studio_narrate 1 处改 update；`tests/test_trip_cross_process_update.py` spawn 集成测试通过 | 文件锁补强（.trip.lock）跳过 |
| M-A1d | done | 2026-07-08 | render/engine.py + orchestrator/run.py + CLI/export 收口 persist_trip_snapshot | — |
| M-A1e | done | 2026-07-08 | `scripts/lint_trip_save_calls.py` + CI；AC-ARC-01/02 测试；`test_trip_concurrent_save.py` 改写 | — |
| M-A2 | done | 2026-07-08 | 重复键 ConfigError（含行号）；未知键单条 warning / strict 报错；`pytest tests/test_config_fail_loud.py` 5 passed；example 零告警回归 | — |
| M-A3 | done | 2026-07-08 | `.gitignore` 增加 registry.cache.json / trips/.cache/；registry.cache 移出索引；import-wizard.js 索引无正反斜杠重复 | — |
| M-B5 | done | 2026-07-08 | `scripts/lint_trip_json.py` + CI validate/lint；`e2e_trip_acceptance` 接入；13 fixtures + `pytest tests/test_lint_trip_json.py` 6 passed | — |
| M-B0 | done | 2026-07-08 | `scripts/arch_equivalence_check.py` 自反性冒烟；`lint-imports` 基线 26 豁免；CI lint+validate；TECH-ARCH §18 | M-B1 已收紧至 11 豁免 |
| ADR-015 | accepted | 2026-07-08 | ADR 已批准；cross-import 51→44（B4a 后） | LSE 互引 109 见下表 |
| M-B4a | done | 2026-07-08 | kernel→layout_contract；adapter 收敛；mosaic ContextVar；render_fingerprint；equivalence 全绿 | LSE cross-import 109（非 import-linter） |
| M-B4b | done | 2026-07-08 | planner+mosaic→layout_engine/；weekly dual-run；消费方收敛 | PRD cross-import ≤10 未达标（109）；待 adapter/shim 退役 |
| M-B1 | done | 2026-07-08 | PRD §5.3.2 违例表清零；import-linter 26→**11** 豁免；`lint-imports` 全绿；domain/kernel 下沉见 §M-B1 交付 | 11 条 intentional 豁免（§import-linter）；LSE 互引 109 不归 M-B1 |
| M-B2 | done | 2026-07-08 | S1 `ARCH-ORCH-DIFF-MATRIX.md`；S2 StudioProfile/Hooks + clustering stage；Go（G-WIP-01 用户授权） | — |
| M-B3 | done | 2026-07-08 | `pipeline.orchestration` unified 默认；legacy 保留；`orchestration_dual_run.py`；weekly CI | legacy 开关 4 周 DoD 至 2026-08-05 |
| M-C4 | done | 2026-07-08 | 三视图 + lint + 单测；curate/orchestrator/render/cli/export 改引 pipeline_view | media/ingest/sandbox 直赋属 ingest 域 |
| M-B6 | done | 2026-07-08 | `trip_migration` 兼容窗口 + 模块 doc；`lint_trip_json` version 窗；超窗单测 | 多 minor 迁移链待 schema bump 时补 |
| M-C6 | done | 2026-07-08 | gate `v3`→`classic` + telemetry/LCP 同步；GLOSSARY + holdback docs；Import Wizard §16 AC-IW-DS-01～08 e2e 全覆盖 | legacy telemetry `variant=v3` 聚合归一化为 classic |
| M-C1 | todo | — | — | 触发：新增 Studio API |
| **M-C2** | done | 2026-07-08 | 全量 **423** 文件分层；baseline **1**（`test_ingest.py` shim）；collect **2714**；14 个 `tests/unit/*` 目录 | — |
| M-C3 | done | 2026-07-08 | `gen_scripts_registry.py` + `scripts/README.md`（168 脚本）+ 7 个 phase 脚本已 `git mv` 至 `scripts/archive/` + docs 索引 | — |
| M-C5 | in-progress | 2026-07-08 | **Phase 1** AC-ARC-14a-d · **Phase 2** `preview-toolbar/{dock,share,inline-edit,longshot}.js` | core/shell 拆分 · tsc · CSS（G-WIP-02） |
| M-D1 | todo | — | — | 开关满 4 周 DoD |

## M-B1 交付摘要（PRD §5.3.2）

| 清偿项 | 处置 |
|--------|------|
| `media/ingest` → curation quality/classify | `media/quality.py` + `media/media_classify.py` |
| `media/ingest_report` → layout_planner | `layout_contract/orientations.py` |
| `render/assemble` → curate cover | `domain/cover_view.py` |
| `templating/roles` → web auth | `util/net.py` |
| `layout_engine/sandbox` → web preview | `preview_url_for` 参数注入 |
| `cover_opening_style` → web telemetry | `services/studio_homepage_telemetry.py` |
| `bucket_planning` / curate → copy_subject | `domain/copy_subject.py` |
| `bucket_planning` → manifest_limits | `manifest_limits.py`（第 0 层） |
| `curate` → templating.curation_adapter | `curation/curation_adapter.py` |
| `chapter_explain` → intent_plan | `domain/plan_cities.py` |
| `moment_scoring` → render.cover_closing | `domain/closing_view.py` |

证据：`python -m importlinter.cli lint-imports` 全绿；相关 pytest（ingest / cover / sandbox / intent / closing）通过；分支 `51964a3` 起可复现。

## import-linter 豁免余量（M-B1 后 · 11 条）

> M-B0 基线 26 条 → M-B1 后 **11 条**（`pyproject.toml` `[tool.importlinter.contracts]`）。均属 PRD 表外或 R-15 实验路径，**不阻塞 M-B1 收口**。

| # | 违例 | 性质 / 后续 |
|---|------|-------------|
| 1–2 | `config.app/loader` → `desktop.bundle` | 桌面 bundle 路径；config 层待独立 ADR |
| 3 | `config.loader` → `llm.presets` | 配置加载可选预设 |
| 4–5 | `curation.mosaic.*` → `templating.*` | R-15 实验路径；随 mosaic shim 退役 |
| 6–8 | `layout_templates.*` → `templating.*` | 同层 layout 管理 |
| 9–10 | `templating.admission` → `render.*` | 准入 golden 回归 |
| 11 | `paths` → `templates.registry` | manifest 路径解析 |

## LSE ↔ curation cross-import 基线（ADR-015）

> **与 import-linter 分层违例不同维度**：仅统计 `layout_engine` ↔ `curation` 包间 AST 边。  
> 刷新：`python scripts/lse_cross_import_stats.py` → `docs/acceptance-records/lse-cross-import-baseline.json`

| 指标 | M-B0 参考 | **2026-07-08（M-B4b + M-B1 后）** | PRD / ADR 目标 |
|------|-----------|-----------------------------------|----------------|
| layout_engine → curation | — | **100** | — |
| curation → layout_engine | — | **9** | — |
| **合计** | 51（B4a 前）→ 44（B4a 后） | **109** | PRD ≤10 ❌ · ADR 20%≈22 ❌ |
| Top importer | — | `layout_engine.planner.screen_planner` (12) | adapter 白名单收敛 |
| Top imported | — | `curation.layout_planner` (16) · `screen_layout_state` (14) | kernel/shim 共享待续 |

**说明**：B4b 物理迁移后 LSE 模块仍大量 lazy-import curation（评分、mosaic shim、curate 实验路径），边数上升属预期；**≤10 目标归属 M-B4 后续**（adapter 薄化 + curation shim 删除 + 白名单边审计），非 M-B1 范围。

## 开关台账

| 开关 | 上线日期 | 4 周 DoD 到期 | 备注 |
|------|----------|---------------|------|
| `pipeline.orchestration` | 2026-07-08 | 2026-08-05 | M-B3 默认 unified；legacy weekly dual-run |
| `layout.planner_impl` | 2026-07-08 | 2026-08-05 | M-B4b 默认 layout_engine |

## 发现问题

（范围外问题仅记录，不在当前里程碑修复）

---

## WS1 执行顺序

P-00 ✓ → … → P-17 (M-B6) ✓ · **P-13 (M-C4) ✓** · **P-19 (M-C2) ✓** · **P-12 (M-C3) ✓** · **P-22 (M-C6) ✓** · **AC-ARC-14a-d ✓**

## 下一步（2026-07-08 更新 · 不合并 PR，优先编码/文档）

| 优先级 | 任务 | 触发 / 门禁 | 目标 |
|--------|------|-------------|------|
| P0 | 开关观察：`pipeline.orchestration` · `layout.planner_impl` weekly dual-run | §3.3 DoD ①–④ | 至 **2026-08-05** |
| P1 | **AC-ARC-14a-d** Playwright（M-C5 前置） | `tests/e2e/test_preview_toolbar_arc14_playwright.py` | **done** · 4 passed |
| P1 | **M-D1 / P-23** 删 legacy + TECH-ARCH 全量 | 开关 DoD 全满足 | **2026-08-05** 后 |
| P1 | **LSE cross-import 收敛**（109→≤10） | ADR-015 后续 | 独立 PR 链 |
| P2 | **M-C5 / P-21 Phase 2 续** · core/shell ESM + tsc + CSS | core 模块 · **G-WIP-02**（CSS） | longshot 已拆 |
| P2 | **M-C1 / P-18** 路由表化 | 新增 Studio API | 机会主义 |
| 背景 | 全量 `pytest --fast` 预存失败 (~25) | 非 M-C6 | 分批 issue |
