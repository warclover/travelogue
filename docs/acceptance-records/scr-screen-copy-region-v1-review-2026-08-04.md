# PRD-SCREEN-COPY-REGION-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-SCREEN-COPY-REGION-V1.md](../PRD-SCREEN-COPY-REGION-V1.md)（**SCR** · 屏级文案区） |
| **模板来源** | [scr-screen-copy-region-v1-review-TEMPLATE.md](./scr-screen-copy-region-v1-review-TEMPLATE.md) |
| **相邻挡门** | [4mix](../PRD-screen-editorial-4mix.md) · [TPC](../PRD-TEMPLATE-CONTRACT-V1.md) · [COPY](../PRD-COPY-OPTIMIZATION.md) · [Refine](../PRD-PREVIEW-REFINE-V1.md) · [SFC](../PRD-SHARE-FACE-CLOSEOUT-V1.md) · [AIR](../PRD-AI-RETURN-V1.md) · [TEMPLATE-SURFACES](../TEMPLATE-SURFACES.md) |
| **验收 / 实施** | [ACCEPTANCE…](../ACCEPTANCE-SCREEN-COPY-REGION-V1.md) · [IMPLEMENTATION…](../IMPLEMENTATION-SCREEN-COPY-REGION-V1.md) |
| **先例** | [TPC W2 captionAreas spike · Defer](./tpc-w2-caption-areas-spike-2026-07-18.md) |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-04 |
| **结论** | **有条件通过（Conditional Go）** |
| **编码** | ☑ **可 Kickoff M0（文档冻结）**　□ **M1 合码**（关 BLK-SCR-02～06 后）　□ M2　□ M3 默认延期 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD §0～§10 · D/OQ 表 + **对照现网**（`context._enrich_editorial_4mix_copy` · `screen-editorial-4mix.yaml` status · `screens_to_longshot_items` · `platform_longshot` Moments · `copy_patch` · `layout-screen.hbs`） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-04 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写** |
| **审查基线** | 图主文辅 · 空优于假句 · 文案立即保存 · 不绑 MCS 选版 · 渠道包分家 |

---

## 0. 会前宣读（主持人）

1. **切口**：SCR = **可选屏级文本区**（模板声明 · 空隐 · 导出带走），不是每图 caption、不是渠道配文、不是再开拼图专题。  
2. **产品定调**：拼图观感已满意；本波只做「合适位置可写字」；空不挡路；导出默认含字。  
3. **勿重开**：MCS/TPC caption tie-break、每屏必有框、equal-grid 挖洞、默认 AI 填 L1、迟晒灌版心、LVP/密度重开。  
4. **本场必拍**：D-SCR-01～20 · OQ-01～04 · **4mix 是否仍可作为首发 GA SKU** · **长图展平是否丢 L1** · 焦点显现 vs 4mix 常驻 draft 空框。  
5. **列车**：M0 冻结 → M1 通用 enrich + 首发 GA SKU + 长图 L1 最小路径；禁单 PR 塞满 M1–M3。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：产品切口正确、与 COPY/SFC/Refine/TPC 边界清晰、不绑选版是对的；但 v0.1 有两处会被现网打脸——（1）`screen-editorial-4mix` 已 `deprecated`/`rollout.percent=0`，不能当「首发 GA SKU」；（2）长图面把 screens 展平为 media-card，当前不消费 `screens[].copy`，与「导出默认含字」未闭环。M0 立即冻结并回写；M1 以 `screen-landscape-1` 为第一 GA SKU，4mix 仅作迁移/回归参考；长图须在 flatten 路径插入 L1 文本块；焦点显现统一取代 draft 常驻虚线。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 体感合同成立；必须可发现「哪些页能写」但不能催填；导出含字是主承诺，长图缺口必须进 M1 |
| **算法** | **Conditional Go** | 强烈支持 D-SCR-12（不读 caption 改选版）；4mix park 与选版无关，勿借 SCR 解 park |
| **架构** | **Conditional Go** | `textRegions` SSOT + 复用 `screens[].copy` 正确；enrich 去硬编码 patternId；配置 fail-loud；TPC 只接渲染切片 |
| **开发** | **Conditional Go** | M1 可开工：LTE schema + 泛化 enrich + hbs 已有钩子；长图插入 copy 块需新 AC；禁顺手 unpark 4mix |
| **测试 / QA** | **Conditional Go** | AC-01～10 可测；须补「长图有 L1 / 无 L1 不挡导出」双路径；4mix 行为回归防抽公共路径打坏 |
| **视觉 / 排版** | **Conditional Go** | overlay band + 空隐保住拼图；landscape-1 底栏一句最像杂志；L4/L6 禁字同意；字阶克制待狗粮 |
| **用户体验 · 狗粮** | **Conditional Go** | 焦点显现对；反对全书虚线；Share 只读；朋友圈纯图 + L3 分家需在狗粮脚本写清，避免用户以为「导出丢字」 |

**汇总**：**七席 7/7 Conditional Go**。  
- **M0**：文档冻结 ✅（本纪要 + PRD v0.2 + AC/IMPL 初稿）。  
- **M1**：关 BLK-SCR-02～06 后方可合码宣称 Done。  
- **M2**：Dock 索引 / SKU 扩面。  
- **M3**：默认 **延期**（AI / absorb）。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案完整度 | **8** | 三层分家清晰；长图缺口会前未钉死 |
| 与 4mix/TPC/COPY/Refine 边界 | **9** | 所有权表可签；4mix 角色需降级为参考 SKU |
| 工程可开工性 | **7** | enrich/hbs/patch 现成；长图 L1 + LTE schema 为新工 |
| AC 可测性 / 防假绿 | **8** | 补长图 AC；几何 AC-10 容差须书面化 |
| 视觉/敢发可签核性 | **8** | 空隐 + 焦点显现；观感否决权在狗粮 |

---

## 3. 事实核查（对照现网）

| # | 假设 | 会中 |
|---|------|------|
| **F-01** | Mosaic 槽无文本；SCR 非现网通用能力 | ✅ 属实 |
| **F-02** | `screens[].copy` schema 已有；patch 白名单已通 | ✅ 属实（`copy_patch.py`） |
| **F-03** | enrich 硬编码 `patternId == screen-editorial-4mix` | ✅ 属实（`context.py`） |
| **F-04** | draft 空 copy 仍输出 `hasCopy*` + empty 占位（非焦点显现） | ✅ 属实；与 D-SCR-08/09 **冲突** → 统一焦点显现 |
| **F-05** | 读者态空则不渲（非 draft） | ✅ 属实（`kicker or is_draft`） |
| **F-06** | Moments 强制 `copy_display=photos` | ✅ 属实（`platform_longshot.py`） |
| **F-07** | TPC captionAreas spike defer；LTE 无 captionAreas | ✅ 属实 |
| **F-08** | MCS 不读 caption | ✅ 属实；V1 接受（D-SCR-12） |

**新增事实（评审发现 · 挡门级）**

| # | 事实 | 影响 |
|---|------|------|
| **F-09** | `screen-editorial-4mix.yaml`：`status: deprecated` · `rollout.percent: 0` · PARKED（role/AR 矛盾） | → **不得**把 4mix 当 M1「首发 GA SKU」；降为迁移/回归参考 |
| **F-10** | `TEMPLATE-SURFACES`：longshot = screens **展平** media-card；`screens_to_longshot_items` **不读** `copy` | → 「导出默认含字」在长图主路径 **未闭环**；M1 必修 flatten 插入 L1 |
| **F-11** | `layout-screen.hbs` 已有 `.layout-copy` kicker/body 钩子 | → Web scroll 渲染成本低；长图另轨 |
| **F-12** | `screen-landscape-1` 为 **ga** 原始单图，高频出现 | → **冻结为 M1 第一 GA SKU**（OQ-02 关闭） |
| **F-13** | 4mix CSS 大量 `data-pattern="screen-editorial-4mix"` 特化 | → landscape-1 overlay 须独立轻量样式，禁止绑死 4mix 棋盘 padding |

---

## 4. 全场共识

1. **SCR 是版心可选字，不是选版、不是 L2、不是 L3。**  
2. **模板声明 0～2 region；无声明 = 零成本零节点。**  
3. **空隐 + 焦点显现**；否决全书常驻虚线；4mix draft 常驻空框在 SCR 通用路径上 **被取代**。  
4. **不绑 MCS/TPC tie-break**（D-SCR-12 红线）。  
5. **M1 第一 GA SKU = `screen-landscape-1`**（单 `band-bottom` → body）；4mix = 代码迁移与行为回归参考，unpark **不在本主题**。  
6. **长图 M1**：flatten 时若该屏 `copy` 非空，插入 L1 文本块（顺序随屏）；空则不插；不要求长图复刻 mosaic DOM。  
7. **朋友圈强制纯图保留**；用户预期靠狗粮/导出说明，话术走 L3。  
8. **M3（AI/absorb）默认延期**；NAS 默认面不自动填 L1。  
9. **列车**：通用 enrich → landscape-1 + 长图 L1 → 4mix 迁入回归；禁单 PR 塞满。

---

## 5. Must-Fix（阻塞）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-SCR-01** | D/OQ 回写 | D-01～21 · OQ-01～04 按本纪要写入 PRD v0.2；状态 Conditional Go | M0 | ✅ 本纪要回写 |
| **BLK-SCR-02** | 拆 AC/IMPL | M1 合码前须有 ACCEPTANCE / IMPLEMENTATION | M0 | ✅ 初稿已拆 |
| **BLK-SCR-03** | 首发 GA SKU | M1 **必须**交付 `screen-landscape-1` + `textRegions`（body/band-bottom）；**禁止**以「仅泛化 4mix enrich」宣称 M1 Done | M1 | ⏳ Kickoff |
| **BLK-SCR-04** | 长图 L1 | flatten/longshot 路径：非空 `screens[].copy` → 可见 L1 文本块；空不挡导出；AC-SCR-06/06b 锁 | M1 | ⏳ |
| **BLK-SCR-05** | 4mix 角色 | 抽公共 enrich；4mix 硬编码删除；**不**要求 unpark；回归：强制 pattern 时行为符合焦点显现 + 空隐 | M1 | ⏳ |
| **BLK-SCR-06** | 焦点显现 | draft 空 region **仅**焦点/「加字」显现；读者/share/失焦空 = 无节点；取代 4mix「draft 一律 hasCopy」 | M1 | ⏳ |

**Should-Fix（不阻塞 M1）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-SCR-01** | TPC PRD 脚注指针 SCR（OQ-04） | ⏳ 文档小改 |
| **SHD-SCR-02** | 狗粮 GUIDE：可写屏如何发现 + Moments「图内无字属预期」 | ⏳ M1 狗粮前 |
| **SHD-SCR-03** | AC-SCR-10 几何容差书面化（建议 bbox 像素差 = 0，因 overlay 不改槽） | ⏳ IMPL |
| **SHD-SCR-04** | M2 第二 airy mosaic SKU 设计师点名 | ⏳ M2 |
| **SHD-SCR-05** | `copyMeta.regionsApplied` 可选，不挡 M1 | 可选 |

---

## 6. 拍板 D / OQ（锁定）

| ID | 结论 |
|----|------|
| **D-SCR-01～07** | ✅ 维持 v0.1（对象 / copy 载体 / textRegions / ≤2 / 子集 SKU / mosaic overlay / editorial） |
| **D-SCR-08** | ✅ **修订** — 空态：读者/share/export 空隐；draft = **焦点显现**（统一，含原 4mix 路径） |
| **D-SCR-09** | ✅ 否决常驻虚线 |
| **D-SCR-10** | ✅ V1 默认不生成 L1；M3 延期 |
| **D-SCR-11** | ✅ 导出默认含 L1；Moments 强制折叠保留 |
| **D-SCR-12** | ✅ **合码红线** — 不改选版读 caption/SCR |
| **D-SCR-13～17** | ✅ 维持 |
| **D-SCR-18** | ✅ **修订** — `screen_copy_region.enabled` 默认 **true**（内部 dogfood）；false 时新 SKU 不挂 region，4mix 若仍手动强制则走旧行为或同等空隐（IMPL 注明） |
| **D-SCR-19** | ✅ SSOT = `textRegions` |
| **D-SCR-20** | ✅ **修订** — 4mix 几何仍归 4mix PRD；**执行层**归 SCR；**产品角色** = 迁移参考，**非** M1 首发 GA |
| **D-SCR-21**（新增） | ✅ **M1 第一 GA SKU = `screen-landscape-1`**（单 region：`mapTo=body` · `placement=band-bottom` · `collapse=hide`） |
| **D-SCR-22**（新增） | ✅ **长图 L1**：flatten 时按屏插入非空 copy 文本块；不要求复刻 layout-screen mosaic DOM |
| **OQ-01** | ✅ **关闭** · 内部 dogfood 默认 **on**；对外 GA 另签字 |
| **OQ-02** | ✅ **关闭** · M1 = `screen-landscape-1`（非等权、非 4mix） |
| **OQ-03** | ✅ **关闭** · body 硬顶 80；产品软提示 ≤56 |
| **OQ-04** | ✅ **关闭** · TPC 加脚注指针，不重开 TPC 全文 |

---

## 7. 结论栏

| 项 | 结论 |
|----|------|
| **总体** | **Conditional Go** |
| **可 Kickoff M0** | ✅ |
| **可 Kickoff M1 编码** | ✅ 文档齐后可开；**合码 Done** 须关 BLK-03～06 |
| **M2** | Dock + 扩面；不挡 M1 |
| **M3** | **延期**（AI / absorb / AIR 联调） |
| **PRD** | 升 **v0.2.0** |

### 会后动作

1. 回写 PRD v0.2.0（本纪要 D/OQ/F-09～13）。  
2. 维护 ACCEPTANCE / IMPLEMENTATION 初稿。  
3. 工程：按 IMPL M1 切片开工；合码说明列 BLK-03～06。  
4. TPC 脚注（SHD-01）可另小 PR。  
5. 狗粮按 GUIDE（SHD-02）填记录。

### 签字

| 席位 | 表决 | 日期 |
|------|------|------|
| 产品 | Conditional Go | 2026-08-04 |
| 算法 | Conditional Go | 2026-08-04 |
| 架构 | Conditional Go | 2026-08-04 |
| 开发 | Conditional Go | 2026-08-04 |
| 测试/QA | Conditional Go | 2026-08-04 |
| 视觉/排版 | Conditional Go | 2026-08-04 |
| 用户体验·狗粮 | Conditional Go | 2026-08-04 |
