# Travelogue · Phase 4 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE4.md](./PRD-PHASE4.md) v0.4.3 |
| **UX 线框** | [wireframes/studio-import-sheet-v1.html](./wireframes/studio-import-sheet-v1.html) |
| **代号** | P4-Intent |
| **更新日期** | 2026-05-29 |

> **状态图例**：☑ 已落地（有代码证据）· ◑ 部分（多为前端已做、后端/测试缺）· ☐ 未开始
>
> ⚠️ **代码核查基线（2026-05-29，负责人审核）**
> - 下表状态基于**源码存在性**核查，**不**代表已通过测试或端到端验证。
> - **全部 P4 改动尚未提交 git**：前端 `studio.{html,js,css}` 与 `studio_routes/pipeline/subprocess.py` 为未暂存修改；本三份文档与 wireframe 为未跟踪文件。**存在丢失风险，建议尽快固化入库。**
> - **零自动化测试**：`tests/test_studio_intent.py`、`tests/test_studio_entry.py` 均不存在。
> - **后端 intent 地基缺位**：schema 无顶层 `intent` 对象、无 `TripService.apply_intent()`、无 `g1_confirm_structure` config、无 `GET .../entry` 路由、brief 未统一 intent 源。AC-P4-01/03/04/06 **当前不可能通过**。

---

## 里程碑总览（实际完成度）

| 里程碑 | 目标 | 状态 | 估算 | 备注 |
|--------|------|------|------|------|
| **M15** | 导入 panel + Intent + API + 进度/成功反馈 + brief | ◑ | ~35% | 前端 UI + intentLine 已落地；schema/apply_intent/brief/config/测试缺 |
| **M15-HP** | 首页极易用（§PRD-PHASE4 §6） | ◑ | ~90% | 仅缺 `/trips` 骨架屏；其余 panel/确认区/回访大卡/coach 均有代码 |
| **M16** | 预览：书名/感受/promote/peak 深链 | ☐ | ~5% | 仅 `promote-tier`（附录 A 既有）；`entry` 深链未实现 |
| **M16b** | 预览编辑/结构 drawer | ☐ | 0% | — |
| **M17** | G1 结构确认 + memoryAnchors UI | ☐ | 0% | `g1_confirm_structure` config 不存在 |
| **M18** | plan.txt + 解析 + curate hints | ☐ | 0% | 无 `planFile`/`intent_plan.py`/`intentHints` |
| **M19** | 关键词/锚点轻权重 + 盲评 fixture | ☐ | 0% | — |

---

## M15 · Studio Intent Layer

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M15-01 | `trip.intent` schema + `validate_trip` | `schemas/trip.schema.json` · `services/validate.py` | ☐ | schema 无顶层 `intent` 对象 |
| M15-02 | `TripService.apply_intent()` 双写 meta/userNotes | `services/trip.py` | ☐ | grep 零命中 |
| M15-03 | studio.html：Intent 带 UI（title/place/feeling） | `templates/studio/studio.html` | ☑ | `trip-title`/`trip-feeling`/`trip-place` 在 panel |
| M15-04 | studio.js：sessionStorage · import body | `templates/studio/studio.js` | ◑ | import body 带 title/place/userNotes；sessionStorage 恢复待确认 |
| M15-05 | import API：`userNotes` · worker 写 intent | `web/studio_routes.py` · `studio_subprocess.py` | ◑ | `userNotes` 已解析(routes 370/428/484)；**worker 未写 intent 对象**（无 schema） |
| M15-06 | 双文件夹静态说明文案 | `studio.html` · `studio.css` | ☑ | hint 行 + 折叠树形图（html 168/170） |
| M15-07 | Job.result：`intentLine` featured/segment | `studio_pipeline.py` · `studio_jobs.py` | ☑ | 真实计算（`_format_intent_line`/`_trip_import_stats`） |
| M15-08 | 成功 overlay 动态文案 | `studio.js` | ☑ | `studio-success-msg`/chips/countdown（js 1204-1246） |
| M15-09 | `narrative_brief` 统一 userNotes 源 | `services/narrative_brief.py` | ☐ | 仍直接读 `meta.userNotes`，无 `intent` 回退（line 58） |
| M15-10 | pytest：import 带 title/userNotes | `tests/test_studio_intent.py` | ☐ | 文件不存在 |
| M15-11 | `config.yaml` `g1_confirm_structure: false` 默认 | `config.py` · example | ☐ | config 无此项 |

> **M15 缺口聚焦**：前端与 intentLine 已可用，但 **intent 落盘契约（M15-01/02）缺失** 是阻塞点——前端已在发 `userNotes`/`title`，后端却无 `intent` 对象承接，brief 也未消费。建议 M15 收口顺序：**01 → 02 → 09 → 05(worker 写 intent) → 10(测试)**。

---

## M15-HP · 首页极易用

> 编号修正：原表有两个 `M15-HP-11`，手测清单改记为 **M15-HP-13**。

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M15-HP-01 | `studio-import-sheet` DOM + CSS（对照线框 v1） | `studio.html` · `studio.css` | ☑ | DOM + CSS 标志物齐全 |
| M15-HP-02 | 主 CTA「制作我的杂志」→ 打开 panel | `studio.js` | ☑ | `openImportSheet`（js 357） |
| M15-HP-03 | pick-folder → **确认区** → 开始制作/跳过 → import | `studio.js` | ☑ | 确认区 show/hide（js 325/350/411） |
| M15-HP-04 | 路径栏迁入「其他导入方式」；Hero 去掉常驻 path form | `studio.html` | ☑ | `<details>` 内 path form（html 188-205） |
| M15-HP-05 | title 从文件夹 basename 预填 + 确认区 | `studio.js` | ☑ | `basenameTitleFromPath`（js 280/349） |
| M15-HP-06 | 双文件夹折叠图示 + 一行摘要 | `studio.html` | ☑ | html 168/170 |
| M15-HP-07 | 回访 hybrid：最近 trip **继续编辑** 大卡 + stale「更新长图」 | `studio.js` · `studio.css` | ☑ | `studio-continue-card` + stale（js 415-461/665/763） |
| M15-HP-08 | `/trips` loading 骨架（F 区网格） | `studio.js` · `studio.css` | ☐ | 无 skeleton 实现 |
| M15-HP-09 | 首次 coach mark `coachImportV1` | `studio.js` | ☑ | `coachImportV1`（js 26/468-489） |
| M15-HP-10 | 试用示例后自动打开 panel + 转化文案 | `studio.js` | ◑ | `useDemoAlbum` 入口在（js 1754）；「现在用你的照片」转化文案待确认 |
| M15-HP-11 | Importing 时禁止 reopen panel | `studio.js` | ☑ | `_sheetOpen` 守卫 + Esc 守卫（js 1117/1157/1710） |
| M15-HP-12 | 行内错误文案（附录 B） | `studio.js` | ☑ | `trip-title-error`（html 155） |
| M15-HP-13 | AC-HP-26～28 手测清单 | `ACCEPTANCE-PHASE4.md` | ☐ | 未执行 |

> **M15-HP 状态**：前端主体 ~90% 完成，**唯一代码缺口是骨架屏（08）**；其余为"已写代码、未测未提交"。建议优先补自动化/手测验证 + git 固化，而非继续堆功能。

---

## M16 · Preview Toolbar

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M16-01 | `GET /__travelogue/trips/{id}/entry` peak 深链 | `studio_routes.py` | ☐ | 无 entry 路由 |
| M16-02 | 打开预览使用 entry URL | `studio.js` | ☐ | — |
| M16-03 | toolbar 杂志名 inline + save-copy | `preview-toolbar.js` | ☐ | — |
| M16-04 | 「编辑感受」textarea + PATCH intent | `preview-toolbar.js` · routes | ☐ | 无 PATCH intent 路由 |
| M16-05 | 「标为精选」→ promote-tier + toast | `preview-toolbar.js` | ◑ | `promote-tier` 路由既有（附录 A）；toolbar ★ UI 待接 |
| M16-06 | 「应用排版」→ rerender | 复用 `web/rerender.py` | ◑ | rerender 既有；预览入口待接 |
| M16-07 | AC-P4-03 自动化 | `tests/test_studio_entry.py` | ☐ | 文件不存在 |

---

## M16b · 预览 Drawer

| 任务 ID | 任务 | 文件/模块 |
|---------|------|-----------|
| M16b-01 | 顶栏精简 ≤4 项 | `preview-toolbar.js` |
| M16b-02 | 编辑 drawer：感受 · 锚点 | `preview-toolbar.js` · `.css` |
| M16b-03 | 结构 drawer：G1 · chapter-explain | `preview-toolbar.js` |
| M16b-04 | 屏角 ★ promote-tier | `preview-toolbar.js` + template hook |

---

## M17 · G1 产品化

| 任务 ID | 任务 | 文件/模块 |
|---------|------|-----------|
| M17-01 | `studio.g1_confirm_structure` config | `config.py` · `config.yaml.example` |
| M17-02 | pipeline 停 `structure_draft` + 跳过 narrate | `studio_pipeline.py` · `orchestrator/run.py` |
| M17-03 | `PATCH .../pipeline` structure_locked | `studio_routes.py` |
| M17-04 | preview G1 条 UI | `preview-toolbar.js` · `.css` |
| M17-05 | memoryAnchors chip 输入 + save-copy | `preview-toolbar.js` |
| M17-06 | `POST .../curate` 重跑 Job（可选） | `studio_routes.py` |
| M17-07 | NR-P4-01：`g1_confirm_structure: false` 回归 | `tests/test_studio_pipeline.py` |

---

## M18 · Travel Plan

| 任务 ID | 任务 | 文件/模块 |
|---------|------|-----------|
| M18-01 | `services/intent_plan.py` 规则解析 | 新建 |
| M18-02 | multipart `planFile` · 落盘 `source/intent/plan.txt` | `studio_routes.py` |
| M18-03 | 写入 `intent.travelPlan` + `curation.intentHints` | `studio_pipeline.py` |
| M18-04 | curate 消费 `planCities` | `curate.py` · `chapter_titles.py` |
| M18-05 | chapter_explain 显示 plan 来源 | `chapter_explain.py` · toolbar |
| M18-06 | fixture `tests/fixtures/intent/plan-kyoto.txt` + AC-P4-07 | `tests/` |

---

## M19 · 轻权重 + 评估

| 任务 ID | 任务 | 文件/模块 |
|---------|------|-----------|
| M19-01 | `userNotes` 关键词 → peak 权重 | `curation/intent_hints.py` 新建 |
| M19-02 | memoryAnchors 子串匹配选图 +分 | `curate_scoring.py` |
| M19-03 | intent golden 对比脚本 | `scripts/diff_curate.py` 扩展 |
| M19-04 | 文档 acceptance record | `docs/acceptance-records/phase4-intent.json` |

---

> **M16b / M17 / M18 / M19 状态**：均为 ☐（0%）。`g1_confirm_structure` config、`services/intent_plan.py`、`curation/intent_hints.py`、multipart `planFile`、预览 drawer 均未开始。

---

## 依赖与闸门

- **启动**：Phase 2 Studio 可导入并 preview（M8+）。  
- **建议**：Phase 3 M12 geo 已合入，成功页可展示「行程 N 段」。  
- **发布闸门**：AC-P4-01～06 全绿；AC-P4-05 附录 A 不回归。

---

## 收口待办（负责人 · 2026-05-29）

> 当前 P4 的真实障碍不是"功能没做"，而是"前端跑在地基与流程治理之前"。建议按下列顺序收口：

| 优先级 | 动作 | 关联 |
|--------|------|------|
| **P0** | **git 固化**：把未提交的 P4 前端 + 三份文档 + wireframe 拆成合理 commit 入库 | 防丢失 |
| **P0** | **后端 intent 地基**：M15-01 schema `intent` + 迁移、M15-02 `apply_intent()`、M15-09 brief 统一 | 解锁 AC-P4-01/04/06 |
| **P0** | **暖金对比度定稿**：`--accent #d2a657` + 白字实测 ~1.9:1 不达标，先定色再继续 UI | PRD §6.12/§6.13 |
| **P1** | M15-10 / M16-07 自动化测试补齐 | 验收门禁 |
| **P1** | M15-HP-08 骨架屏 | 唯一前端缺口 |
| **P2** | M16 entry 深链 → M17 G1 → M18 plan → M19 评估 | 按依赖推进 |
