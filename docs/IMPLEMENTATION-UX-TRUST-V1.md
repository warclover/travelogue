# 信任闭环 V1 · 实施清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) v1.1.0 |
| **验收** | [ACCEPTANCE-UX-TRUST-V1.md](./ACCEPTANCE-UX-TRUST-V1.md) |
| **更新日期** | 2026-07-11 |

---

## 归属

| 波次 | 归属 | 状态 |
|------|------|------|
| **P0-A** 验货壳 + Share | Trust | ✅ 代码 |
| **P0-B** 成功 vs stale | Facade 增量（本清单） | ✅ 代码 |
| **P0-C** 续跑 platform / 话术 | Facade 增量 | ✅ 代码（断服文案已补；跳首页=探针） |
| **P0-D** 门禁 + 杂志名写路径 | Trust | ✅ 代码 |
| **P1** 图说 / 平台成功话术 | Trust | ✅ 平台成功/进度话术；图说 happy path 沿用既有 |
| **P2** 首页降噪 | 可并行 | ✅ 代码 |

---

## 改动文件

| 文件 | 说明 |
|------|------|
| `templates/studio/preview-toolbar/preview-mode.js` | **新增** refine 权威状态 |
| `templates/studio/preview-toolbar/init-v3.js` | refine 默认 off；Sheet 开/关；废止 copy→stale |
| `templates/studio/preview-toolbar-v3-sheet.js` | `onSheetClosed` |
| `templates/studio/preview-toolbar/features.js` | 注入后 sync 可见性 |
| `templates/studio/preview-toolbar/share.js` | Share 加固 + **「保存图片」**（wechat_chat） |
| `templates/studio/preview-toolbar/longshot.js` | exportSideEffect、门禁、platform flag、成功话术、**断服反馈**、COPY-06b |
| `templates/studio/preview-toolbar-v3-task-dock.js` | showError 支持副句 +「回到预览」链 |
| `templates/studio/preview-toolbar/inline-edit.js` | `saveMagazineTitleValue`；同步 document.title |
| `templates/studio/preview-toolbar/drawers.js` | 「这本」改名同步封面 |
| `templates/studio/preview-toolbar/drawers.css` | refine=off 藏 ★/拼图 |
| `templates/studio/preview-toolbar/shell.css` | 藏 Plate |
| `templates/visual-journal/journal-screens.css` | 藏 Plate |
| `templates/visual-journal/inline-edit.js` | Share 守卫；验货不提示可编辑 |
| `templates/studio/studio-home-v2.html` | P2：去用户可见「Bento」；导入偏好副文案 |
| `templates/studio/homepage-v2/css/bento.css` | P2：settings popover 说明样式 |
| `templates/studio/homepage-v2/css/shelf.css` | P2：书架标题权重 |

---

## 任务勾选

| ID | 任务 | 状态 |
|----|------|------|
| M-TRU-A1 | `data-preview-refine` 默认 off | ✅ |
| M-TRU-A2 | ★/拼图仅精修可见 | ✅ |
| M-TRU-A3 | Plate 验货/Share 隐藏 | ✅ |
| M-TRU-A4 | Share 禁 inline-edit | ✅ |
| M-TRU-B1 | 废止 copy-saved→showStaleHint | ✅ |
| M-TRU-B2 | exportSideEffect 60s | ✅ |
| M-TRU-C1 | exportAfterLayout 带 platform | ✅ |
| M-TRU-C2 | 进度/成功平台话术 | ✅ |
| M-TRU-C3 | 断服文案 + 回到预览（EXP-04） | ✅ |
| M-TRU-C4 | 续跑 platform 双写 resume + prefs 同步（AC-07 复测修） | ✅ |
| M-TRU-C5 | layout 更新 90s 超时收口 + 409 不空挂 | ✅ |
| M-TRU-A5 | Share「保存图片」（SHARE-03） | ✅ |
| M-TRU-A6 | Share 剥 editable + 藏「可编辑」提示（AC-13 复测修） | ✅ |
| M-TRU-D1 | assessMagazineTitleRisk | ✅ |
| M-TRU-D2 | 门禁 Modal + 改名写路径 | ✅ |
| M-TRU-D3 | bypass 成功回声 | ✅ |
| M-TRU-D4 | COPY-06b 首次出示记 seen | ✅ |
| M-TRU-D5 | 附录 D 表驱动单测 | ✅ |
| M-TRU-DOC | ACCEPTANCE + 本清单（含禁止选择器） | ✅ |
| M-TRU-WF | 线框帧 2+3 | ✅ |
| M-TRU-P2 | 首页对外文案降噪 | ✅ |
