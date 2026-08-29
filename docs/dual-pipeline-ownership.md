# 双管线所有权（DPI）

权威副本。实施以 [PRD-DUAL-PIPELINE-ISOLATION-V1.md](./PRD-DUAL-PIPELINE-ISOLATION-V1.md) v0.2.1 为准。机器门：`python scripts/lint_dual_pipeline_ownership.py`。

## 入口

| 管线 | 装配 | 版式 | 读者面 builder | 读者面 CSS |
|------|------|------|----------------|-----------|
| 游记 | `compose_trip` · `layout_engine/mosaic/**` | `screen-*.yaml` | `render/journal_chapters.py`（`chapters.py` 仅 re-export） | `journal-screens.css` |
| 作品集 | `compose_portfolio_trip` · `editorial_series/**` | `page-*.yaml` | `render/portfolio_chapters.py` | `portfolio-pages.css` |

共用壳：`journal.css`（变量）· Studio · 预览服务器 · ingest / cull / cluster / 开章 / 封面。

反查：`python scripts/lint_dual_pipeline_ownership.py --explain travelogue/render/chapters.py`

## 窄缝（上限 14 · 现 12）

| ID | 文件 | 允许的分支 |
|----|------|-----------|
| S-01 / S-02 | `travelogue/curation/curate.py` | 装配分叉 · 呼吸屏门 |
| S-03 | `travelogue/curation/moment_scoring.py` | 高光早退 |
| S-04 | `travelogue/render/assemble.py` | **唯一**渲染分发 + `data-edition` 戳记 |
| S-05 | `travelogue/render/reading_profile.py` | 默认 magazine |
| S-06 | `travelogue/render/context.py` | `is_page_face` 舞台（本波只参数化） |
| S-07 | `travelogue/export/dispatch.py` | 按 `(platform, edition)` 选 Writer |
| S-08 | `travelogue/services/validate.py` | patternId 语义放行 |
| S-09 | `templates/studio/preview-toolbar/dock.js` | `data-edition` 挂载 + `journalDockLogic` / `portfolioDockLogic` 分发 |
| S-10 | `layout_templates/css_gen.py` · `validator.py` | 按前缀取族参数 |
| S-11 | `travelogue/render/engine.py` | 按身份拷贝 / 重写 `@import`（只改拷贝后的 `journal.css`） |
| S-12 | `travelogue/export/packager.py` | zip 按身份打包族 CSS |

**OLT（DOC-OLT-02 · 2026-08-26）**：成品账本 / 四段指纹 / 票根副券 **零新增窄缝**，额度仍 **12 / 14**。`export/output_ledger.py` 与 `domain/output_fingerprint.py` 无 `is_portfolio` 分支；`export/dispatch.py`（S-07）只在成功后写账本，`edition` 仅作字符串快照。

## 允许清单（不占窄缝额度）

`config/edition.py` · `export/portfolio_*.py` · `layout_engine/editorial_series/**` · `web/studio*` · `cli/render_cmds.py`

RCL 阶段模块不占窄缝：`render/assemble_cover.py` · `render/assemble_copy.py` · `render/journal_folio.py` · `render/journal_screens.py`（零身份 `if`）。

## 夹具

| 独占 | 路径 |
|------|------|
| 游记 | `tests/fixtures/phase16-dogfood/**` |
| 作品集 | `tests/unit/layout_engine/fixtures/editorial_series/**` |
| **共享** | `schemas/fixtures/trip.render_golden.json`（克隆再注入 `edition` 合法） |

## W0 棘轮

现网历史命中在 `docs/acceptance-records/dpi-seam-baseline.json`。只拦**新增**边。W2 已从 grandfather 删掉 `chapters.py` / `surface.py` / `longshot.py` / `context_types.py`；剩下 `export/output_recipe/resolve.py`。W1 起 `lte_journal_css_audit.py --fail-on-prefix-leak` 拦 `journal-screens.css` 里的 `page-` 与 `portfolio-pages.css` 里的 `screen-`。
