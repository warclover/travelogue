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
| M-B1 | done | 2026-07-08 | import-linter **26→0** 豁免；PRD §5.3.2 违例清零 | — |
| M-B2 | done | 2026-07-08 | S1 `ARCH-ORCH-DIFF-MATRIX.md`；S2 StudioProfile/Hooks + clustering stage；Go（G-WIP-01 用户授权） | — |
| M-B3 | done | 2026-07-08 | unified `run_trip` 编排；legacy 已于 M-D1 删除 | — |
| M-C4 | done | 2026-07-08 | 三视图 + lint + 单测；curate/orchestrator/render/cli/export 改引 pipeline_view | media/ingest/sandbox 直赋属 ingest 域 |
| M-B6 | done | 2026-07-08 | `trip_migration` 兼容窗口 + 模块 doc；`lint_trip_json` version 窗；超窗单测 | 多 minor 迁移链待 schema bump 时补 |
| M-C6 | done | 2026-07-08 | gate `v3`→`classic` + telemetry/LCP 同步；GLOSSARY + holdback docs；Import Wizard §16 AC-IW-DS-01～08 e2e 全覆盖 | legacy telemetry `variant=v3` 聚合归一化为 classic |
| M-C1 | todo | — | — | 触发：新增 Studio API |
| **M-C2** | done | 2026-07-08 | 全量 **423** 文件分层；baseline **1**（`test_ingest.py` shim）；collect **2714**；14 个 `tests/unit/*` 目录 | — |
| M-C3 | done | 2026-07-08 | `gen_scripts_registry.py` + `scripts/README.md`（168 脚本）+ 7 个 phase 脚本已 `git mv` 至 `scripts/archive/` + docs 索引 | — |
| M-C5 | done | 2026-07-08 | ESM 10 模块 + tsc + preview-toolbar CSS + **studio-home-v2.css** 13 partials | — |
| M-D1 | done | 2026-07-08 | 删 legacy 开关；LSE batch-1～6（108→**7**） | PRD ≤10 ✅ · 余 7 边为 curate→adapter 白名单 |

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

## import-linter（M-B1 后 · 0 豁免）

> M-B0 基线 26 条 → M-B1 初版 11 条 → **2026-07-08 清零 0 条**（domain/util 下沉 + admission hook 注册）。

| 批次 | 清偿项 | 处置 |
|------|--------|------|
| batch-6a | config→desktop/llm | `paths` 平台路径 + `util/llm_presets` |
| batch-6a | paths→templates.registry | 直接 `TEMPLATES_ROOT / id` |
| batch-6b | layout_engine→templating | `domain/template_admin_state` · `util/template_metrics` |
| batch-6b | layout_templates↔templating | review 读 domain；HTML admission 上移至 web handler |
| batch-6b | templating→render | `domain/admission_hooks` + `render/admission_golden` 注册 |

证据：`python -m importlinter.cli lint-imports` 全绿（`ignore_imports = []`）。

## LSE ↔ curation cross-import 基线（ADR-015）

> **与 import-linter 分层违例不同维度**：仅统计 `layout_engine` ↔ `curation` 包间 AST 边。  
> 刷新：`python scripts/lse_cross_import_stats.py` → `docs/acceptance-records/lse-cross-import-baseline.json`

| 指标 | M-B0 参考 | **2026-07-08（batch-6 后）** | PRD / ADR 目标 |
|------|-----------|------------------------------|----------------|
| layout_engine → curation | — | **0** | — |
| curation → layout_engine | — | **7**（curate→adapter 白名单） | adapter 单向入口 |
| **合计** | 51（B4a 前）→ 44（B4a 后） | **7**（batch-1～6：108→7） | PRD ≤10 ✅ |
| Top importer | — | `curation.curate` (7) | 符合 §5.3.1 白名单 |
| Top imported | — | `layout_engine.adapter` 等 7 模块 | intentional |

**说明**：B4b 物理迁移后 LSE 模块仍大量 lazy-import curation（评分、mosaic shim、curate 实验路径），边数上升属预期；**≤10 目标归属 M-B4 后续**（adapter 薄化 + curation shim 删除 + 白名单边审计），非 M-B1 范围。

## 开关台账（M-D1 后）

> 双路径开关已于 **2026-07-08** 删除（用户授权提前执行）。残留 config 键仅触发 `UserWarning`，不阻断启动。

| 原开关 | 删除日期 | 现行路径 |
|--------|----------|----------|
| `pipeline.orchestration` | 2026-07-08 | unified `run_trip`（唯一） |
| `layout.planner_impl` | 2026-07-08 | `layout_engine.planner`（唯一） |

## 发现问题

（范围外问题仅记录，不在当前里程碑修复）

---

## WS1 执行顺序

P-00 ✓ → … → P-17 (M-B6) ✓ · **P-13 (M-C4) ✓** · **P-19 (M-C2) ✓** · **P-12 (M-C3) ✓** · **P-22 (M-C6) ✓** · **AC-ARC-14a-d ✓**

## 下一步（2026-07-08 更新 · 不合并 PR，优先编码/文档）

| 优先级 | 任务 | 触发 / 门禁 | 目标 |
|--------|------|-------------|------|
| P2 | **M-C1 路由表化** | 新增 Studio API | AC-ARC-13 |
| 背景 | G-ARC-06 CacheRegistry 立项 | 未追踪 | — |
| 背景 | 全量 `pytest --fast` 预存失败 (~25) | 非 M-C6 | 分批 issue |
