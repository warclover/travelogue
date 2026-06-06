# Travelogue · Phase 11 实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PHASE11-copy-optimization.md](./PRD-PHASE11-copy-optimization.md) v0.11.0 |
| **验收** | [ACCEPTANCE-PHASE11.md](./ACCEPTANCE-PHASE11.md) |
| **里程碑** | M11 · Lite Copy |
| **状态** | **W1/W2 Done · W3 部分**（盲评 AC-P11-04 待人工） |
| **更新** | 2026-06-06 |

---

## 波次总览

| 波次 | 目标 | 出口 |
|------|------|------|
| **M11-W1** | 章级单句 `decorLine`（<=30 字）基础链路 | §2 任务全绿 + AC-P11-01/02/03/06 |
| **M11-W2** | 最小意图注入（mood/focus/note）+ 重排加权 | §3 任务全绿 + AC-P11-07 |
| **M11-W3** | 灰度与观测完善 | §4 任务全绿 + 线上灰度记录 |

---

## M11-W1 · 基础链路（P0）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M11-1a | `trip.schema` 新增 `chapters[].decorLine` | `schemas/trip.schema.json` | ☑ |
| M11-1b | `NarrativeConfig` 新增 `decor_line_*` 配置 | `travelogue/config.py` `config.yaml.example` | ☑ |
| M11-1c | brief 组装：新增 `build_chapter_decor_brief()` | `travelogue/services/narrative_brief.py` | ☑ |
| M11-1d | 生成链路：候选生成与写入 | `travelogue/services/decor_line.py` · `narrate.py` | ☑ |
| M11-1e | 校验规则：长度<=30、禁套话、重复惩罚 | `travelogue/services/decor_line.py` · `narrative_validate.py` | ☑ |
| M11-1f | 渲染上下文透传 `decorLine` | `travelogue/render/chapters.py` | ☑ |
| M11-1g | 模板渲染 `decorLine`（轻层级） | `templates/visual-journal/partials/chapter.hbs` · `journal.css` | ☑ |
| M11-1h | 一键隐藏/纯照片无回归 | `copy-display.css` · `test_phase11_copy_toggle_regression.py` | ☑ |
| M11-1i | 单测：长度/空输出/edited 保护 | `tests/test_phase11_decor_line.py` | ☑ |
| M11-1j | 回归：narrate/render/schema | `tests/test_narrate.py` `tests/test_validate.py` | ☑ |

---

## M11-W2 · 最小意图注入（P0/P1）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M11-2a | schema 新增 `chapters[].curation.copyIntent` | `schemas/trip.schema.json` | ☑ |
| M11-2b | 配置新增 `decor_line_intent_*` | `travelogue/config.py` `config.yaml.example` | ☑ |
| M11-2c | brief 注入意图锚点（mood/focus/note） | `travelogue/services/narrative_brief.py` | ☑ |
| M11-2d | 重排新增 `intent_fit` 权重 | `travelogue/services/decor_line.py` | ☑ |
| M11-2e | Studio handler 透传 copyIntent（可选） | `travelogue/web/studio_handlers/*` · `preview-toolbar.js` | ☑ |
| M11-2f | 校验：枚举合法性与 note 长度（<=30） | `travelogue/services/decor_line.py` · `narrative_validate.py` | ☑ |
| M11-2g | 单测：有锚点 vs 无锚点评分对比 | `tests/test_phase11_decor_line.py` | ☑ |
| M11-2h | 集成：UI 输入 -> narrate -> render 闭环 | `preview-toolbar.js` · `test_phase11_decor_line.py` | ☑ |

---

## M11-W3 · 灰度与运营（P1）

| ID | 任务 | 文件 | 状态 |
|----|------|------|------|
| M11-3a | 指标落盘：fill/hide/intent_adoption/lift | `travelogue/services/pipeline_state.py` 等 | ☐ |
| M11-3b | 验收脚本：离线批量评测 | `scripts/phase11_copy_acceptance.py` | ☑ |
| M11-3c | 验收记录模板 | `docs/acceptance-records/phase11-copy.json` | ☑ |
| M11-3d | 灰度开关与回滚 runbook | `config.yaml.example` · PRD §9 | ☑ |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.11.1 | 2026-06-06 | W1/W2 合入：`decor_line.py` 规则链 + 渲染 + 单测 |
| v0.11.0 | 2026-06-02 | 初稿：M11-W1/W2/W3 任务拆解 |
