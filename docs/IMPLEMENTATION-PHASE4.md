# Travelogue · Phase 4 实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE4.md](./PRD-PHASE4.md) v0.4.3 |
| **UX 线框** | [archive/import-sheet/studio-import-sheet-v1.html](./archive/import-sheet/studio-import-sheet-v1.html)（已归档） |
| **代号** | P4-Intent |
| **更新日期** | 2026-06-06 |

> **状态图例**：☑ 已落地（有代码证据）· ◑ 部分（多为前端已做、后端/测试缺）· ☐ 未开始
>
> ⚠️ **代码核查基线（2026-05-29，负责人审核）**
> - 下表状态基于**源码存在性**核查，**不**代表已通过测试或端到端验证。
>
> ✅ **进度更新（2026-06-06 · Phase 4 自动化 gate）**
> - **`scripts/phase4_acceptance_gate.py`**：聚合 a11y + intent_ac + intent/entry/telemetry/plan/g1/user_tier（59 passed，`--skip-integration`）。
> - **AC-P4-02/05/A11Y-03** 已由 `tests/test_studio_intent_ac_p4.py` · `tests/test_studio_a11y_p4.py` 覆盖。
> - **仍待人工**：P-EVAL 盲评（UX-P4-02）、AC-P4-HP 手测。AC-P4-02 e2e：`test_studio_intent_ac_p4_playwright.py`；CI：`validate` 跑 gate `--skip-integration`，`test-integration` 跑全量 87 项。

---

## 里程碑总览（实际完成度）

| 里程碑 | 目标 | 状态 | 估算 | 备注 |
|--------|------|------|------|------|
| **M15** | 导入 panel + Intent + API + 进度/成功反馈 + brief | ☑ | 100% | telemetry + tierMode 已补 |
| **M15-HP** | 首页极易用（§PRD-PHASE4 §6） | ☑ | ~100% | F-P4-HP-08 样张 CTA 已对齐 |
| **M16** | 预览：toolbar + drawer + peak 深链 | ☑ | 100% | entry 链含 arcSegment 优先 |
| **M16b** | 预览编辑/结构 drawer | ☑ | 100% | 锚点保存 → narrate 提示 |
| **M17** | G1 结构确认 + pipeline 模式 B | ☑ | 100% | 含 Studio 高级 G1 开关 |
| **M18** | plan.txt + 解析 + curate hints | ☑ | 100% | 含 plan-empty 负向 fixture |
| **M19** | 关键词/锚点轻权重 + 评估脚本 | ☑ | 100% | P-EVAL 盲评数据待填 |

---

## M15 · Studio Intent Layer

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M15-01 | `trip.intent` schema + `validate_trip` | `schemas/trip.schema.json` · `services/validate.py` | ☑ | `$defs/intent` + 顶层属性（optional，旧 trip 放行）；测试守护 |
| M15-02 | `TripService.apply_intent()` 双写 meta/userNotes | `services/trip.py` | ☑ | 单写入口；镜像 meta.title/places + trip.userNotes，**不**写 meta.userNotes；AC-P4-09 测试 |
| M15-03 | studio.html：Intent 带 UI（title/place/feeling） | `templates/studio/studio.html` | ☑ | `trip-title`/`trip-feeling`/`trip-place` 在 panel |
| M15-04 | studio.js：intent 持久化 · import body | `templates/studio/studio.js` | ☑ | `localStorage.studioIntent`（强于 PRD sessionStorage）+ job pending sessionStorage |
| M15-05 | import API：`userNotes` · worker 写 intent | `web/studio_routes.py` · `studio_pipeline.py` | ☑ | pipeline 经 `apply_intent` 落盘 intent + folders 检测；schema 校验通过 |
| M15-06 | 双文件夹静态说明文案 | `studio.html` · `studio.css` | ☑ | hint 行 + 折叠树形图（html 168/170） |
| M15-07 | Job.result：`intentLine` featured/segment/tierMode | `studio_pipeline.py` · `studio_subprocess.py` | ☑ | `_format_intent_line` + `tierMode` |
| M15-08 | 成功 overlay 动态文案 | `studio.js` | ☑ | `studio-success-msg`/chips/countdown（js 1204-1246） |
| M15-09 | `narrative_brief` 统一 userNotes 源 | `services/narrative_brief.py` | ☑ | `resolve_user_notes` + `travelPlanSummary` |
| M15-10 | pytest：import 带 title/userNotes | `tests/test_studio_intent.py` | ☑ | 双写不变量 / brief / pipeline |
| M15-11 | `config.yaml` `g1_confirm_structure: false` 默认 | `config.py` · example | ☑ | M17-01 已合并 |
| M15-12 | telemetry `runs/studio-intent.json` | `web/studio_intent_telemetry.py` | ☑ | AC-P4-TEL-01 · `tests/test_studio_intent_telemetry.py` |

> **M15 状态**：✅ 代码完成。AC-P4-02 cull 第二行 + dual-folder resolver 单测 ☑；FirstSuccess chips e2e 可选手测。

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
| M15-HP-08 | `/trips` loading 骨架（F 区网格） | `studio.js` · `studio.css` | ☑ | `renderTripsSkeleton()` + `.studio-skeleton-card` shimmer（reduced-motion 关） |
| M15-HP-09 | 首次 coach mark `coachImportV1` | `studio.js` | ☑ | `coachImportV1`（js 26/468-489） |
| M15-HP-10 | 试用示例后自动打开 panel + 转化文案 | `studio.js` · `studio.html` | ☑ | 样张 CTA「现在用你的照片做一篇」 |
| M15-HP-11 | Importing 时禁止 reopen panel | `studio.js` | ☑ | `_sheetOpen` 守卫 + Esc 守卫（js 1117/1157/1710） |
| M15-HP-12 | 行内错误文案（附录 B） | `studio.js` | ☑ | `trip-title-error`（html 155） |
| M15-HP-13 | AC-HP-26～28 手测清单 | `ACCEPTANCE-PHASE4.md` | ☐ | 未执行 |

> **M15-HP 状态**：✅ 全部落地（含骨架屏 08）。前端主体已 git 固化。

---

## M16 · Preview Toolbar

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M16-01 | `GET /__travelogue/trips/{id}/entry` peak 深链 | `studio_routes.py` · `studio_entry.py` | ☑ | §8.5：arcSegment peak → cluster → 首内容屏 |
| M16-02 | 打开预览使用 entry URL | `studio.js` | ☑ | 成功页 fetch `/entry` 升级 previewUrl |
| M16-03 | toolbar 杂志名 inline + save-copy | `preview-toolbar.js` · `copy_patch.py` | ☑ | apply_intent 双写 |
| M16-04 | 「编辑感受」textarea + PATCH intent | `preview-toolbar.js` · `studio_routes.py` | ☑ | 编辑 drawer |
| M16-05 | 「标为精选」→ promote-tier + toast | `preview-toolbar.js` | ☑ | 屏角 ★ |
| M16-06 | 「应用排版」→ rerender | `serve.py` · `studio_routes.py` | ☑ | ⋯ 菜单 |
| M16-07 | AC-P4-03 自动化 | `tests/test_studio_entry.py` | ☑ | 含 arcSegment 优先用例 |
| M16-08 | curate 写入 `screens[].arcSegment` | `curation/arc_screen_tags.py` | ☑ | schema `layoutScreen.arcSegment` |

---

## M16b · 预览 Drawer

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M16b-01 | 顶栏精简 ≤4 项 | `preview-toolbar.js` | ☑ | 工作台 · 杂志名 · 长图 · ⋯ |
| M16b-02 | 编辑 drawer：感受 · 锚点 | `preview-toolbar.js` · `.css` | ☑ | bottom sheet · PATCH intent + memoryAnchors save-copy |
| M16b-03 | 结构 drawer：G1 · chapter-explain | `preview-toolbar.js` | ☑ | pipeline 说明 + chapter-layout 嵌入 |
| M16b-04 | 屏角 ★ promote-tier | `preview-toolbar.js` | ☑ | M16 已落地 |
| M16b-05 | present「放映精选」 | `preview-toolbar.js` | ☑ | ⋯ 菜单触发 featured-present + screenplay |

---

## M17 · G1 产品化

| 任务 ID | 任务 | 文件/模块 | 状态 | 核查 |
|---------|------|-----------|------|------|
| M17-01 | `studio.g1_confirm_structure` config | `config.py` · `config.yaml.example` | ☑ | `StudioConfig` + GET config 暴露 `g1ConfirmStructure` |
| M17-02 | pipeline 停 `structure_draft` + 跳过 narrate | `studio_pipeline.py` | ☑ | mode B 停于 structure_draft + draft render；mode A 默认全链路 |
| M17-03 | `PATCH .../pipeline` structure_locked | `studio_routes.py` · `studio_g1.py` | ☑ | 确认 + 可选 continue job |
| M17-04 | preview G1 条 UI | `preview-toolbar.js` | ☑ | 结构 drawer：章节顺序 OK / 重新生成结构 |
| M17-05 | memoryAnchors chip 输入 + save-copy | `preview-toolbar.js` · `copy_patch.py` | ☑ | M16b 编辑 drawer 已接 |
| M17-06 | `POST .../curate` 重跑 Job | `studio_routes.py` | ☑ | `POST /__travelogue/trips/{id}/curate` |
| M17-07 | NR-P4-01 回归 | `tests/test_studio_g1.py` | ☑ | mode A/B + PATCH pipeline |
| M17-08 | Studio 高级 G1 开关 UI | `studio.html` · `studio.js` | ☑ | PATCH config `studio.g1ConfirmStructure` |

---

## M18 · Travel Plan

| 任务 ID | 任务 | 文件/模块 | 状态 |
|---------|------|-----------|------|
| M18-01 | `services/intent_plan.py` 规则解析 | 新建 | ☑ |
| M18-02 | multipart `planFile` · 落盘 `source/intent/plan.txt` | `studio_routes.py` | ☑ |
| M18-03 | 写入 `intent.travelPlan` + `curation.intentHints` | `studio_pipeline.py` | ☑ |
| M18-04 | curate 消费 `planCities` | `curate.py` · `chapter_titles.py` | ☑ |
| M18-05 | chapter_explain 显示 plan 来源 | `chapter_explain.py` | ☑ |
| M18-06 | fixture + AC-P4-07/07b | `tests/fixtures/intent/` | ☑ | plan-kyoto.txt + plan-empty.txt |

---

## M19 · 轻权重 + 评估

| 任务 ID | 任务 | 文件/模块 |
|---------|------|-----------|
| M19-01 | `userNotes` 关键词 → peak 权重 | `curation/intent_hints.py` | ☑ |
| M19-02 | memoryAnchors 子串匹配选图 +分 | `curate_scoring.py` | ☑ |
| M19-03 | intent golden 对比脚本 | `scripts/diff_curate.py` | ☑ |
| M19-04 | 文档 acceptance record | `docs/acceptance-records/phase4-intent.json` | ☑ |

---

## 发布前仍待人工（非代码）

| 项 | 说明 |
|----|------|
| **UX-P4-02 / G-P4-07** | P-EVAL 盲评 6 对 · 填 `phase4-intent.json` |
| **AC-P4-HP-01～06** | 极易用手测清单 |
| **FirstSuccess chips e2e** | v2 成功页「精选 N 张」第一行 | ✅ `test_studio_intent_ac_p4_playwright.py` |
| **G-P4-01 / UX-P4-03** | 访谈 · 20 分钟成稿计时 |

---

## 依赖与闸门

- **启动**：Phase 2 Studio 可导入并 preview（M8+）。  
- **建议**：Phase 3 M12 geo 已合入，成功页可展示「行程 N 段」。  
- **发布闸门**：AC-P4-01～06 全绿；AC-P4-05 附录 A 不回归。

---

## 收口待办（负责人 · 2026-05-30）

> Phase 4 **代码主线已收口**；剩余为人工验收与 P-EVAL 数据收集。

| 优先级 | 动作 | 关联 | 状态 |
|--------|------|------|------|
| **P0** | **git 固化**：未提交 P4 前端 + 文档 + wireframe 入库 | 防丢失 | ✅ 已完成（8678afc/13b33fe/7e11dae/8019502） |
| **P0** | **后端 intent 地基**：M15-01 schema、M15-02 `apply_intent()`、M15-09 brief 统一、M15-05 pipeline 落盘 | 解锁 AC-P4-01/04/09 | ✅ 已完成（含 13 回归测试，修 2 处 schema bug） |
| **P0** | **暖金对比度定稿** | PRD §6.12/§6.13 | ✅ `--accent-ink` |
| **P1** | telemetry + G1 UI + arcSegment peak 链 | PRD 缺口收口 | ✅ |
| **P1** | M16-07 entry 测试 | 验收门禁 | ✅ |
| **P1** | M15-HP-08 骨架屏 | HP-GAP-08 | ✅ |
| **P2** | M17→M18→M19 | 按依赖推进 | ✅ |
| **P3** | P-EVAL 盲评 + HP 手测 | 发布闸门 | ☐ |
| **P2** | Phase 4 自动化 gate | `phase4_acceptance_gate.py` | ✅ 2026-06-06 |
