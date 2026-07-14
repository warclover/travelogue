# 精修意图可感知闭环 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-REFINE-FEEDBACK-LOOP-V1.md](./PRD-REFINE-FEEDBACK-LOOP-V1.md) **v0.1.2** |
| **验收** | [ACCEPTANCE-REFINE-FEEDBACK-LOOP-V1.md](./ACCEPTANCE-REFINE-FEEDBACK-LOOP-V1.md) |
| **线框** | [wireframes/refine-feedback-loop-v1-wireframe.html](./wireframes/refine-feedback-loop-v1-wireframe.html) |
| **日期** | 2026-07-14 |
| **状态** | **M1+M2+P0+M3 可手测** · AC-FEED-02 真人待补 |

## 冻结决策（执行默认）

| ID | 结论 |
|----|------|
| D-FEED-01 | B′ 分层反馈 |
| D-FEED-02 | 首尾 tip + 区头 |
| D-FEED-03 | **3a** 纯 ★ 不拦导出 |
| D-FEED-04/05 | 「按精选重排」+ demote → **M2** |

## M1 勾选

| 项 | 落点 | 状态 |
|----|------|------|
| 首尾 tip T-BE-OPEN | `help-onboarding.js` `maybeShowBookendsPickTip` · `bookends.js` | ✅ |
| 区头「换封面/封底 · 点选」 | `bookends.js` + `sheet.css` | ✅ |
| 点候选轻确认 toast | `bookends.js` afterMutation | ✅ |
| ★ toast 诚实文案 | `features.js` | ✅ |
| 纯 ★ 不置 pending | `features.js` | ✅ |
| 这页精选语义行 | `preview-toolbar-v3-sheet.js` | ✅ |
| 拦截 Modal / Dock 去掉「精选」绑渲染 | `longshot.js` · `task-dock.js` | ✅ |
| H2/H3/H6 + refineSaveLines | `help-onboarding.js` | ✅ |
| 重播清 bookendsPickSeen | `replayHelpHints` | ✅ |
| 线框 F-BE / F-FEAT | `wireframes/…` | ✅ |

## M2 勾选

| 项 | 落点 | 状态 |
|----|------|------|
| demote（★ 再点取消） | `user_tier.py` · `tier_patch.py` · `serve._handle_promote_tier(tier=material)` · `features.js` | ✅ |
| 「按精选重排」确认→`/curate` | `runFeaturedRerank` · 这页 CTA · `structure_locked` 风险文案 | ✅ |
| H2 文案含取消/重排 | `help-onboarding.js` | ✅ |
| 埋点 tier_rerank_* | `features.js` | ✅ |
| 单测 demote + 静态门禁 | `test_user_tier` · `test_studio_preview_m16` · `test_refine_feedback_loop_v1` | ✅ |

## P0 收口勾选

| 项 | 落点 | 状态 |
|----|------|------|
| Dock「按精选重排」次 CTA | `showFeaturedRerankCue` · `init-v3` `onFeaturedRerank` | ✅ |
| ★ toast「了解更多 →」H2 | `attachFeaturedHelpLinkOnToast` · `.preview-toolbar__toast-link` | ✅ |
| 放映精选空池说明 | 导出 Tab 常显 + `featuredPresentEmpty` | ✅ |
| 重排成功封面更换 toast | `entry.coverAssetId` 前后对比 · `featuredRerankDoneCover` | ✅ |
| 精修 V1 §4.2 / §4.3.1 回写 | `PRD-PREVIEW-REFINE-V1.md` | ✅ |
| 附录 A §6 预览升格注记 | `PRD-EXPERIENCE-附录A-精选上传.md` | ✅ |
| ACCEPTANCE 清单 | `ACCEPTANCE-REFINE-FEEDBACK-LOOP-V1.md` | ✅ |

## M3 勾选

| 项 | 落点 | 状态 |
|----|------|------|
| `run_curate(scope="tier")` layout-only buckets | `curate.py` · 不重建分章 | ✅ |
| `structure_locked` 不解锁 | `trip_pipeline_handlers.handle_trip_curate` | ✅ |
| `force_relayout` 允许章内 beam | `assess_degradation(force_relayout=True)` | ✅ |
| 前端 `scope:"tier"` + Modal 文案 | `features.js` · `HELP_COPY` | ✅ |
| 单测 | `test_curate_tier_scope` · handler tier 门禁 | ✅ |

## 手测要点

### M1
1. 清 `travelogue.studio.help.bookendsPickSeen` → 精修 → 这本 → 展开首尾装帧 → 见 tip  
2. 点候选 → 「已换封面/封底」+ 预览变图  
3. 正文 ★ → toast 含「放映精选」；**无**「点更新版面后生效」；导出不因纯 ★ 拦截  
4. 改拼图 → 仍 pending → 拦截文案只提拼图/版式  
5. 帮助 H2/H6 文案与上表一致  

### M2 + P0
1. 已标 ★ 再点 → 「已取消精选」· ★ 熄灭  
2. 标 ★ → Dock「按精选重排」→ 确认 Modal → 进度 → 刷新；封面变则见「封面已更换」  
3. toast「了解更多 →」→ 打开帮助 H2  
4. 导出 Tab「放映精选」无 ★ 时：禁用 +「先在正文点 ★」  
5. `structure_locked` 时 Modal 含解锁风险说明  
6. 「按精选重排」与「更新版面」不是同一按钮  
