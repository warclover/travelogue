# IMPLEMENTATION · 敢发闭环优化 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-SHARE-READY-OPTIMIZATION-V1.md](./PRD-SHARE-READY-OPTIMIZATION-V1.md) **v1.0.2** |
| **评审** | [acceptance-records/share-ready-optimization-v1-review-2026-07-17.md](./acceptance-records/share-ready-optimization-v1-review-2026-07-17.md) · Conditional Go · MF 已回写 |
| **验收** | [ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md](./ACCEPTANCE-SHARE-READY-OPTIMIZATION-V1.md) |
| **线框** | [wireframes/share-ready-optimization-v1-wireframe.html](./wireframes/share-ready-optimization-v1-wireframe.html) · F1–F6 |
| **更新日期** | 2026-07-17 |
| **状态** | **W0–W2 工程已合入** · 产品手测待签 · 可选补 QA-SR-02 |
| **估时** | W0 ≈ **2.5–3.5 人日** · W1 ≈ **2–3 人日**（含 FTUE 成功面联调）· W2 ≈ **2 人日** |

---

## 0. 波次摘要

| 波次 | 目标 | Go |
|------|------|-----|
| **Doc/Design** | 评审 · 线框 · AC · OR 回写 | ✅ 2026-07-17 |
| **W0** | 敢信：真图 · `kept_n` 同源 · stale 不绕过 · 零泄漏 · e2e | AC-SR-01～07 |
| **W1** | 敢选敢发：CTA · 进度人话 · 成功面（联合 FTUE） | AC-SR-08～11 |
| **W2** | 敢秀：stub 门槛 · title 可读化 · 书架降噪 | AC-SR-12～14 |

**所有权**

| 能力 | 所有者 |
|------|--------|
| `kept_n` / 意图卡裁决 | **本主题**（回写 Output Recipe D-OR-27） |
| 默认长图成功面 COPY（已保存 · 打开文件夹 · 不教微信） | **[First-Session Trust](./PRD-FIRST-SESSION-TRUST-V1.md)**（2026-07-17 supersede） |
| 「换种分享方式」动作 | **本主题**（挂成功面次要动作；不改主句） |
| 发群操作说明 publishGuide / H4 | **Help**（按需查阅，非默认成功面） |
| showcase 资产 | **本主题** W0 |
| stub 深度润色 | Copy；本主题只清禁止句式 |
| 海外 IG | **不做** |

---

## 1. W0 任务卡（编码 Kickoff 时启用）

> W0 编码进行中（分支 `feat/share-ready-optimization-v1-w0`）。

### 1.1 前端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SR-01** | 替换 `demo-showcase` 真图；缺失非黑屏占位；样品区 **「示例」徽标**（USR-04） | `demo-showcase/` · homepage carousel/phone CSS | 0.6d | 01 · 01b | ✅ |
| **FE-SR-02** | `startLongshotWithRecipe`：先取服务端 recipe / 注入 `keptN`，再判 `needs_intent`；**禁止**单独 DOM 估数裁决 | `preview-toolbar/longshot.js` · `js/output-recipe.js` | 1.0d | 02～04 | ✅ |
| **FE-SR-03** | stale「重新导出」走同一门；无 intent 弹卡；提供「换种分享」 | `preview-toolbar-v3-task-dock.js` · `longshot.js` | 0.4d | 05 | ✅（同门 `startLongshotWithRecipe`） |
| **FE-SR-04** | 版心/封面隐藏工程 tip 与「已省略封底」；精修内保留 | preview CSS/JS · render 输出类名 | 0.4d | 06～07 | ✅ |
| **FE-SR-04b** | 意图卡用户文案去工程词（§4.6）；微信群长图唯一 primary 样式（USR-01/02） | `output-recipe.js` · intent card CSS | 0.3d | 03 · 15 | ✅ |

### 1.2 后端

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-SR-01** | preview HTML/bootstrap 注入 `keptN` 或 recipe 摘要，减少竞态 | studio preview inject / trip bootstrap | 0.4d | 02～04 | ⏳ 可选（点击 fetch + 缓存） |
| **BE-SR-02** | 确认 `handle_output_recipe` 与 longshot resolve 同源 | `studio_handlers` · export resolve | 0.2d | 04 | ✅ |
| **BE-SR-03** | templateFeedback / veil 提示不进 hook 与读者字段 | narrate / render | 0.3d | 06 | ✅ |
| **BE-SR-06** | 封底省略不写进读者可见 HTML | template / render | 0.2d | 06 | ✅ 不渲染该句 |

### 1.3 测试（BLK-07）

| ID | 任务 | 估时 | AC | 状态 |
|----|------|------|-----|------|
| **QA-SR-01** | e2e：`kept_n=18`（或 fixture）+ mock/减少 DOM 槽 → **仍**出意图卡 | 0.5d | **02** | ✅ `test_share_ready_w0_playwright.py` |
| **QA-SR-02** | 单测/扫描：§4.4 禁止串不进读者字段 | 0.3d | 06 | ⏳ CSS/JS 挡；扫描可后续补 |
| **QA-SR-03** | 回归 `tests/e2e/test_output_recipe_persona_playwright.py` 8/8 | 0.2d | NR-01 | ✅ |

### 1.4 文档（可与编码并行或先做）

| ID | 任务 | 锚点 | 估时 | AC |
|----|------|------|------|-----|
| **DOC-SR-01** | README / 线框索引（本轮已做） | `docs/README.md` · `wireframes/README.md` | — | — |
| **DOC-SR-02** | Output Recipe D-OR-27 回写（本轮已做） | `PRD-OUTPUT-RECIPE-V1.md` | — | — |
| **DOC-SR-03** | showcase 烘焙/刷新步骤 | `templates/studio/assets/demo-showcase/README` | 0.2d | 01 | ✅ |

### 1.5 W0 完成定义（编码后勾）

- [x] 线框 F1/F2/F3/F6 对照合入  
- [x] AC-SR-02 e2e 绿（DOM 少图仍出卡）  
- [x] 首页样品非 PLACEHOLDER 黑屏  
- [x] 版心/Share 无 §4.4 泄漏  
- [x] **不**宣称主题完成（W1/W2 未做）  
- [x] **不**改海外 IG 相关默认  

---

## 2. W1 任务卡

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **FE-SR-05** | Dock 可见 CTA：完整 `cta_label` 或缩短「发微信群」；aria/tooltip 完整句 | `longshot.js` `syncLongshotCtaLabel` | 0.4d | 08 | ✅ |
| **FE-SR-06** | 文内「保存长图」降强调（对齐 FTUE） | visual-journal / screenplay toolbar | 0.2d | R01 | ✅ |
| **FE-SR-07** | 进度第一行人话；参数次行；冻结失败 toast（BLK-05） | `longshot.js` / task-dock busy | 0.4d | 11 · 11b | ✅ |
| **FE-SR-08** | 成功面入口矩阵回归；**必含「换种分享方式」**（USR-03）；禁止新栈；与 FTUE W1 联调 | task-dock · shelf-longshot · `resolvePublishGuide` | 0.8d | 09 · 09b · 10 | ✅ Dock + 书架；产品狗粮待联签 |

### 2.1 W1 完成定义

- [x] 线框 F4/F5 对照  
- [ ] FTUE 成功面 AC 同绿（联合挡门 · **产品手测**）  
- [x] Sparse 用户可见「微信」语义  

---

## 3. W2 任务卡

| ID | 任务 | 建议锚点 | 估时 | AC | 状态 |
|----|------|----------|------|-----|------|
| **BE-SR-04** | stub hook 去掉说明书句式；places 无信号不强展「旅途」 | narrate stub | 0.5d | 12～13 | ✅ |
| **BE-SR-05** | 新导入默认 title 可读化；不覆盖已编辑 | ingest / meta title | 0.4d | 14 相关 | ✅ |
| **FE-SR-09** | 书架主 meta 降噪；stale 角标保留 | `shelf.js` | 0.3d | 14 | ✅ |
| **QA-SR-05** | stub 禁止模式单测 | unit | 0.2d | 12 | ✅ |

---

## 4. 建议编码顺序（Kickoff 后）

```text
1) BE-SR-01/02 + FE-SR-02/03 + QA-SR-01   ← P0 意图卡
2) FE-SR-04 + BE-SR-03/06 + QA-SR-02     ← 泄漏
3) FE-SR-01 + DOC-SR-03                  ← 真图
4) QA-SR-03 回归
5) W1 CTA/进度/成功面（与 FTUE 合流）
6) W2 stub/shelf
```

---

## 5. 风险（实现时）

| 风险 | 缓解 |
|------|------|
| recipe 请求拖慢点击导出 | preview 注入 + ≤2s 超时降级 |
| 与 FTUE 分支冲突 | 成功面只复用不分叉 |
| showcase 体积 | webp 控制；勿提交巨大 PNG |

---

## 6. 签字

| 项 | 日期 | 结论 |
|----|------|------|
| 实施清单初稿 | 2026-07-17 | ✅ 文档 |
| 编码 Kickoff | 2026-07-17 | ✅ W0–W2 工程落地；产品手测/联合挡门待签 |
