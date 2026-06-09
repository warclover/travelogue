# Travelogue · 文案优化实施任务清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-COPY-OPTIMIZATION.md](./PRD-COPY-OPTIMIZATION.md) v1.1.0 |
| **验收** | [ACCEPTANCE-COPY-OPTIMIZATION.md](./ACCEPTANCE-COPY-OPTIMIZATION.md) |
| **前置** | [IMPLEMENTATION-PHASE11.md](./IMPLEMENTATION-PHASE11.md)（W1/W2 已合入） |
| **里程碑** | COPY-OPT · Lite Copy v1.1 |
| **状态** | **P0–P4 Done · 盲评 AC-COPY-17 待人工** |
| **更新** | 2026-06-09 |

> **出口定义：** P0 全绿 → 可内测「少而准 + 可改可藏」；P1 全绿 → decorLine 走心管线闭环；P2 → UX/意图完善；P3 → 质量灰度。

---

## 波次总览

| 波次 | 优先级 | 目标 | 出口 AC |
|------|--------|------|---------|
| **COPY-P0** | P0 | 策略收敛 + 编辑闭环 + fact skip | AC-COPY-01/03/04/05/06 |
| **COPY-P1** | P1 | voice 直通 + decorLine LLM + 主开关 UX | AC-COPY-02/07/08 |
| **COPY-P2** | P2 | 被动 copyIntent + lead 互斥 + 编辑提示 | AC-COPY-08/09 |
| **COPY-P3** | P3 | prompt/禁用词/VLM 试点 + 灰度指标 | AC-COPY-10 + 盲评 |

---

## COPY-P0 · 策略收敛与编辑闭环

| ID | 任务 | 文件 / 模块 | 依赖 | 状态 |
|----|------|-------------|------|------|
| **COPY-0a** | 确认 `narrative.scope` 默认 `frame` | `config.yaml.example` · `travelogue/config.py` | — | ☑ |
| **COPY-0b** | scope=frame 下 narrate 不生成 lead/caption | `narrative_scope.py` · `llm_narrate.py` · `narrate.py` | 0a | ☑ |
| **COPY-0c** | `extract_chapter_facts`：voice/anchors 优先于 tags；输出事件型 fact | `decor_line.py` | — | ☑ |
| **COPY-0d** | fact 数 < `decor_line_min_fact_count` 且无 voice → decorLine 空 | `decor_line.py` · `config.py` | 0c | ☑ |
| **COPY-0e** | 禁用模板句「留在这一章」「记住{secondary}」作独立候选 | `decor_line.py` `_template_candidates` | 0d | ☑ |
| **COPY-0f** | decorLine 渲染加 `data-editable` + `data-edit-path` | `chapter.hbs` · `chapters.py`（`editableDecorLine`） | — | ☑ |
| **COPY-0g** | save-copy 支持 `chapters[n].decorLine` path | `copy_patch.py` · `guardrails.py` · `manifest.json` | 0f | ☑ |
| **COPY-0h** | decorLine 编辑态样式对齐 hook/lead | `inline-edit.css`（复用通用 `[data-editable]`） | 0f | ☑ |
| **COPY-0i** | 纯照片模式下禁用 decorLine 点击编辑 | `inline-edit.js` | 0f | ☑ |
| **COPY-0j** | 单测：scope=frame 无 lead/caption；fact skip；decorLine 可保存 | `tests/test_copy_optimization.py` | 0a–0g | ☑ |
| **COPY-0k** | 回归：render / narrate / phase11 toggle | `test_render.py` · `test_phase11_*` | 0j | ☑ |

---

## COPY-P1 · 走心生成管线

| ID | 任务 | 文件 / 模块 | 依赖 | 状态 |
|----|------|-------------|------|------|
| **COPY-1a** | voice 精简 → decorLine 候选 #1（≤30 字） | `voice_excerpt.py` · `decor_line.py` | 0c | ☑ |
| **COPY-1b** | 配置 `decor_line_voice_first` / `decor_line_llm_enabled` | `config/misc.py` · `config.yaml.example` | — | ☑ |
| **COPY-1c** | `build_chapter_decor_brief()` 注入 voice 汇总 | `narrative_brief.py` | 1a | ☑ |
| **COPY-1d** | LLM decorLine：Step1 facts JSON → Step2 K=3 单句 | `llm_decor_line.py` | 1b·1c | ☑ |
| **COPY-1e** | 候选池合并：voice + note + 规则 + LLM → 去重 | `decor_line.py` | 1a·1d | ☑ |
| **COPY-1f** | 重排阈值校准；低分留空 | `decor_line.py` `pick_best_decor_line` | 1e | ☑ |
| **COPY-1g** | hook/caption prompt 加负向示例 | `llm_narrate.py` `SYSTEM_PROMPT` | — | ☑ |
| **COPY-1h** | 扩展 BANNED / `_GENERIC_RE` 至 narrate | `narrate.py` | — | ☑ |
| **COPY-1i** | 工具栏：默认只暴露「纯照片」主开关；「隐藏导语」移 longshot 二级 | `longshot-toolbar.hbs` · `screenplay-toolbar.hbs` | — | ☑ |
| **COPY-1j** | 单测：voice 候选优先；LLM mock；无 fact 不调用 LLM | `tests/test_copy_optimization.py` | 1a–1f | ☑ |
| **COPY-1k** | 离线脚本：decorLine 质量抽样 | `scripts/copy_opt_acceptance.py` | 1f | ☑ |

---

## COPY-P2 · 意图推断与 UX 完善

| ID | 任务 | 文件 / 模块 | 依赖 | 状态 |
|----|------|-------------|------|------|
| **COPY-2a** | 从 voice/anchors 被动推断 mood/focus | `copy_intent_infer.py` · `decor_line.py` | 1a | ☑ |
| **COPY-2b** | Studio copyIntent 可选 UI：默认折叠；有 voice 章跳过 | `preview-toolbar.js` | — | ☑ |
| **COPY-2c** | decorLine 与 lead 互斥：同章有 decorLine 则不生成 lead | `narrative_scope.py` · `narrate.py` | 0b | ☑ |
| **COPY-2d** | validator：decorLine 与 chapter.title / lead 去重 | `decor_line.py` `validate_decor_line` | 2c | ☑ |
| **COPY-2e** | 首次 draft 轻 toast「点一下文案可修改」 | `inline-edit.js` | 0f | ☑ |
| **COPY-2f** | 有 voice 的 media-card 弱标注「来自你的录音」 | `voice-bar.hbs` · `journal.css` | — | ☑ |
| **COPY-2g** | 单测：互斥 / 被动 intent / toast 一次性 | `tests/test_copy_optimization.py` | 2a–2e | ☑ |

---

## COPY-P3 · 质量灰度与 VLM 试点

| ID | 任务 | 文件 / 模块 | 依赖 | 状态 |
|----|------|-------------|------|------|
| **COPY-3a** | 指标落盘：`curation.copyMetrics`（fill/empty/generic/edit_retention 等） | `copy_metrics.py` · `decor_line.py` · `copy_patch.py` | P1 | ☑ |
| **COPY-3b** | 盲评记录模板与 30 章样本 | `docs/acceptance-records/copy-opt-blind-review.json` | 1k | ☑ |
| **COPY-3c** | 轻量 visual facts：代表图 tags/mediaClass → brief（非 VLM） | `visual_facts.py` · `narrative_brief.py` | — | ☑ |
| **COPY-3d** | 灰度开关 `lite-copy-v1.1` + runbook | PRD §7 · `config.yaml.example` | — | ☑ |
| **COPY-3e** | 全量回归 + demo verify | `tests/test_copy_optimization.py` · `travelogue demo verify` | P0–P2 | ☑ |

---

## COPY-P4 · PRD 遗漏补全

| ID | 任务 | 文件 / 模块 | 依赖 | 状态 |
|----|------|-------------|------|------|
| **COPY-4a** | copyIntent「应用到后续章节」 | `trip_intent_handlers.py` · `decor_line.py` · `preview-toolbar.js` | P2 | ☑ |
| **COPY-4b** | 有 voice 章跳过 copyIntent UI | `studio_entry.py` · `preview-toolbar.js` | P2 | ☑ |
| **COPY-4c** | `intent_adoption_rate` + `photos_only_rate` 埋点 | `copy_metrics.py` · `copy-toggle.js` · copy-telemetry API | P3 | ☑ |
| **COPY-4d** | 验收脚本扩展（≥20 章 · AC-COPY-01 中位数） | `scripts/copy_opt_acceptance.py` | P3 | ☑ |
| **COPY-4e** | AC 补测 12/16/19 + NR-COPY-04 | `tests/test_copy_optimization.py` | P0–P3 | ☑ |
| **COPY-4f** | 灰度 runbook | [COPY-OPT-ROLLOUT.md](./COPY-OPT-ROLLOUT.md) | P3 | ☑ |

---

## 与 Phase 11 任务对照

| Phase 11（已完成） | v1.1 增量 |
|--------------------|-----------|
| M11-1 decorLine schema/渲染/toggle | COPY-0f 编辑；COPY-1a–1f 管线升级 |
| M11-2 copyIntent 主动输入 | COPY-2a 被动推断；COPY-2b UI 折叠 |
| M11-3 指标/盲评 | COPY-3a–3b 修订 KPI |

---

## 建议排期

| 周次 | 任务块 | 人力粗估 |
|------|--------|----------|
| W1 | COPY-P0 全量 | 前端 1d + 后端 2d |
| W2 | COPY-P1a–1f（管线） | AI/后端 3d |
| W3 | COPY-P1g–1k + COPY-P2 | 前端 1d + 后端 2d |
| W4 | COPY-P3 + 盲评灰度 | 全员 2d |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.3 | 2026-06-09 | COPY-P4 PRD 遗漏补全（copyIntent 后续章/voice 跳过/埋点/runbook） |
| v1.0.2 | 2026-06-09 | COPY-P1/P2 合入；P3 盲评模板 + 验收脚本 |
| v1.0.1 | 2026-06-09 | COPY-P0 全量合入 |
| v1.0.0 | 2026-06-09 | 跨职能评审后 P0–P3 任务拆单 |
