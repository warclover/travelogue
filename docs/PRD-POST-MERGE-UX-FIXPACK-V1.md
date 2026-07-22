# Travelogue · 合入后 UX 修复包 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2** |
| **状态** | **Conditional Go**（2026-07-22 决策已锁 · 见 IMPLEMENTATION §0） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「合入后 UX 修复包 V1（Post-Merge UX Fixpack）」— 示例不穿帮 · 状态即承诺 · 一名到底 · 弹层可关 |
| **调研来源** | 2026-07-22 CSC #16 + SFI #17 合入 `master` 后完整用户路径走查（Studio v2 · Playwright 实机） |
| **走查底稿** | [acceptance-records/post-merge-ux-trial-2026-07-22.md](./acceptance-records/post-merge-ux-trial-2026-07-22.md) |
| **关联文档** | [SFI](./PRD-SHARE-FACE-INTEGRITY-V1.md) · [SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md) · [FST](./PRD-FIRST-SESSION-TRUST-V1.md) · [CSC](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) · [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) · [Chapter Naming](./PRD-CHAPTER-NAMING.md) · [Dogfood Fixpack](./PRD-DOGFOOD-UX-FIXPACK-V1.md) · [Refine UX 1.1](./PRD-PREVIEW-REFINE-UX-V1.1.md) |
| **验收** | [ACCEPTANCE-POST-MERGE-UX-FIXPACK-V1.md](./ACCEPTANCE-POST-MERGE-UX-FIXPACK-V1.md)（合同 §9） |
| **实施 / RCA** | [IMPLEMENTATION-POST-MERGE-UX-FIXPACK-V1.md](./IMPLEMENTATION-POST-MERGE-UX-FIXPACK-V1.md) |
| **更新日期** | 2026-07-22 |

> **定位**
>
> CSC 与 SFI 合入后，**主链路已敢用**：首页、导入忙碌壳、Recipe 自适应 CTA、意图卡、导出成功面、长图人话命名、窄屏 gate、设置折叠面均实测通过。
>
> 但走查证明：**敢发内容层与部分交互摩擦仍在穿帮**，且有两条是 SFI 铁律的直接违反——
>
> 1. **示例「再做一遍」读者面写出「示例游记」**（禁词表已列 `示例游记`，旁路未收口）。  
> 2. **设置写「AI 文案已就绪 · DeepSeek」，成功面/精修仍说「本机文案 · 配置写作引擎」**（状态即承诺失败）。  
> 3. **书架 humanize / 封面脏名半修好**（一名到底未兑现到可编辑封面）。  
> 4. **Wizard 与复用卡叠层、精修 × 被工具栏挡住**（高频操作受阻）。
>
> 本 PRD 是一次**修复包（Fixpack）**，不引入新功能面：硬化已有合同的**旁路与回归点**，把合入后仍能复现的破绽收成可独立合入的 M1–M3。

> **一句话目标**：用户从「用示例试一次 / 再做一遍」到「发微信群」的全程，**找不到「示例游记」、找不到「请去配置引擎」（当 Key 已就绪）、找不到封面与书架两套名字、关得掉每一个弹层。**

> **完成定义**
>
> | 门 | 含义 | 不等于 |
> |----|------|--------|
> | **M1 Go** | 不出糗：示例路径零「示例游记」；Key 就绪文案与动作一致；封面展示名与书架同源 | 文案突然优美 |
> | **M2 Go** | 可操作：Wizard/复用卡互斥；精修可关；大册 CTA 可见文案诚实 | 新导出平台 |
> | **M3 Go** | 不误导：时间离群知情或隔离；章名无 `(3)` 工程味；预览窄屏不装死 | 策展算法重写 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题的边界

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [SFI](./PRD-SHARE-FACE-INTEGRITY-V1.md) | **硬化执行点 / 旁路收口** | 不重开 SFI 叙事；接管「示例题名」「状态即承诺」「一名到底」合入后仍破的执行点 |
| [SFC](./PRD-SHARE-FACE-CLOSEOUT-V1.md) | **禁词表所有者** | `示例游记` / `--` 仍归 SFC 表；本包确保**题名写入与 FirstSuccess** 也走同一护栏 |
| [FST](./PRD-FIRST-SESSION-TRUST-V1.md) | **FirstSuccess 所有者** | 不改成功面栈结构；修成功面**文案分支**（L0 stub vs L1 就绪） |
| [CSC](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) | **设置/完成面已合入** | 不重开设置 IA；仅要求设置状态与预览/成功面**同源读取** `llm/status` |
| [FTUE](./PRD-FTUE-OPTIMIZATION-V1.md) | **示例入口所有者** | 示例默认展示名 / 「再做一遍」产物合同在本包 supersede 执行层 |
| [Chapter Naming](./PRD-CHAPTER-NAMING.md) | **章名权威** | 禁止 `日期（N）` 工程后缀上读者面；走 CN 规则链 |
| [Dogfood Fixpack](./PRD-DOGFOOD-UX-FIXPACK-V1.md) | **前序修复包** | 导出链路 / 改名 SSOT 已拍板；本包不重复认领，只补合入后新复现项 |
| [Refine UX 1.1](./PRD-PREVIEW-REFINE-UX-V1.1.md) | **精修状态机所有者** | 不改「× ≠ 退出精修」设计；只修 **× 被挡住点不到** 的层叠缺陷 |

### 0.2 走查问题 → 本文落点

| 走查 ID | 问题 | 严重度 | 落点 |
|---------|------|--------|------|
| **T1** | 示例再做一遍 → 封面/FirstSuccess「示例游记」 | **P0** | §4 R1.1 · D-PMX-01 |
| **T2** | Key 就绪仍提示「本机文案 · 配置写作引擎」 | **P0** | §4 R1.2 · D-PMX-02 |
| **T3** | 书架「武大 米娜」/ 封面「武大--米娜」半修好 | **P0** | §4 R1.3 · D-PMX-03 |
| **T4** | Wizard +「示例已经做过了」双层叠弹 | **P1** | §4 R2.1 · D-PMX-04 |
| **T5** | 精修关闭 × 被导出设置 ▾ 拦截 | **P1** | §4 R2.2 · D-PMX-05 |
| **T6** | 图注/决定性瞬间露出离群年份（如 2015） | **P1** | §4 R3.1 · D-PMX-06 |
| **T7** | 章名 `5月27日（3）` / hook 空干 | **P1** | §4 R3.2 · D-PMX-07 |
| **T8** | 书架两本「武大 米娜」易混淆 | **P2** | §4 R3.3 · Park 可选 |
| **T9** | `HEAD /v2` → 404（GET 正常） | **P2** | §4 R3.4 |
| **T10** | 大册 CTA 可见文案偏「发微信群」，按章语义主要在 aria | **P2** | §4 R2.3 · D-PMX-08 |
| **T11** | 预览页 390px 无首页同款 gate，曾近黑屏 | **P2** | §4 R3.5 |

### 0.3 已拍板决策（2026-07-22 锁定）

| 决策 | 锁定结论 |
|------|----------|
| **D-PMX-01 示例题名** | 锁定 **「京都雨季漫游」**。禁止「示例游记」写入 title / displayTitle / FirstSuccess / `<title>` / 导出 stem。前端常量 + 后端 fail-closed + 展示名拒禁词。 |
| **D-PMX-02 状态即承诺** | **两维分离**：导入主链继续 stub；UI 只按 `llm/status` 分支。就绪 →「重新生成文案」；未就绪 →「配置写作引擎」。禁止用「本次 stub 成稿」推出「去配置」。 |
| **D-PMX-03 一名到底（封面）** | **展示只绑** `resolve_display_title` / `displayTitle`；`/entry` 增 `displayTitle`；保存双写；用户未改名不得把脏 `--` 推上封面。 |
| **D-PMX-04 弹层互斥** | 复用卡出现前**关闭** Wizard；取消则重开；同时最多一个焦点陷阱。 |
| **D-PMX-05 精修可关** | Sheet 打开时 Dock 整体 `pointer-events:none`（点击透传到 Sheet 关闭 ×），**仅「返回」保持可点**；导出区另加 `inert`；**不**改 Dock z-index；Esc/「完成」语义不变。 |
| **D-PMX-06 时间图注** | 本包只做**新产出硬闸**（outlier / daySpan / low-confidence）。**不**纳入武大等存量批量重渲；旧页随日后「更新版面」消化。 |
| **D-PMX-07 章名** | 禁止 `日期（N）`；链为 **时段 → segment → `·二`/`·三`**（仅时段不够）；空 hook 优于假句。 |
| **D-PMX-08 大册 CTA** | `by_chapter` 时可见文案须含「按章」语义。 |

**挂钩**：本主题为合入后唯一修复合同；与 SFI/FST/CSC **一并在本包修复旁路**，不拆平行 PRD/PR。

---

## 1. 背景与证据

### 1.1 走查环境

| 项 | 内容 |
|----|------|
| 分支 / HEAD | `master` @ `3efc0ed`（含 PR #16 CSC · PR #17 SFI） |
| Studio | `http://127.0.0.1:8766` · homepage `data-homepage-variant=v2` |
| 方式 | Playwright 实机 · 桌面 1440×900 · 窄屏 390×844 |
| AI 状态 | `llmAvailable=true` · DeepSeek · tier L1 |
| 样本 | `demo-album`（示例重做）· `demo-e863ec0da9`（武大·25）· `demo-815dc906d3`（张智慧·249）· 书架 14 本 |
| 截图 | 仓库根 `qa-full-*.png`（本地走查产物，非提交资产） |

### 1.2 合入后已验证通过（本包不重开）

| 能力 | 证据摘要 |
|------|----------|
| 首页双预览 + 书架 | v2 Bento；14 本；无 console error |
| 导入忙碌壳 + Wait Tips | 「正在整理/分章/排版」阶段句可读 |
| 导出闭环 | 发微信群 →「长图已保存」；文件 `京都雨季漫游-长图.png` |
| Recipe / 意图卡 | 6 张发群 · 23 张意图卡 · 大册 `chat_longshot_chapter` |
| 导出设置 | 五目标 · 改选诚实 · 长图密度默认/紧凑 |
| 窄屏首页 gate | 「请在电脑浏览器打开 Studio」 |
| 设置折叠 | 导入 · 外观 · AI · 存储；AI 摘要「已就绪 · DeepSeek」 |
| 精修词表 | 「照片类型」；未见 `Plate` / `screen-portrait-*` |
| 路由 | `GET /` 200 · `GET /v2` 302 `/` · `GET /classic` 200 |

### 1.3 根因初判（实施前须摸底确认）

| 现象 | 疑似根因 | 非根因 |
|------|----------|--------|
| 「示例游记」上封面 | 示例导入默认 title 仍写禁词；FirstSuccess 直读 `meta.title`；护栏未覆盖题名写入 | 禁词表缺失（表内已有） |
| 「配置写作引擎」误显 | FirstSuccess / 精修文案未读 `llmAvailable`，沿用 L0 默认句 | 设置面板撒谎（设置正确） |
| 封面脏名 | 可编辑控件绑 `meta.title` 原值，未绑 `resolve_display_title`；书架已 humanize | 完全未做 humanize |
| 双层弹窗 | 复用 dialog 未 dismiss Wizard | 设计需要双层 |
| × 点不到 | 工具栏 `z-index` / 命中盒盖住 sheet close | V1.1「× 不退出」本身（那是另一合同） |

---

## 2. 问题陈述（P-PMX-*）

| ID | 问题 | 严重度 | 证据 |
|----|------|--------|------|
| **P-PMX-01** | 示例再做一遍后 FirstSuccess / 封面 / `<title>` 为「示例游记」 | **P0** | `trip.json meta.title=示例游记`；成功面《示例游记》；SFI W0-3 回归失败 |
| **P-PMX-02** | Key 就绪时成功面/精修仍说「本机文案 · 配置写作引擎后可升级」 | **P0** | `llm/status` ok；成功面 status 段落与精修「这本」矛盾 |
| **P-PMX-03** | 封面可编辑标题保留脏名 `武大--米娜`，书架已是 `武大 米娜` | **P0** | 武大册预览首屏；辑封已 humanize |
| **P-PMX-04** | Import Wizard 与示例复用卡同时可见 | **P1** | 叠层截图；焦点混乱 |
| **P-PMX-05** | 精修 sheet 关闭 × 被「导出设置 ▾」拦截点击 | **P1** | Playwright timeout · pointer intercept |
| **P-PMX-06** | 决定性瞬间/图注露出离群年份 | **P1** | 武大 `2015.07.09 · 下午` |
| **P-PMX-07** | 章名出现 `5月27日（3）` 工程后缀；多章 hook 空 | **P1** | 示例重做后 chapters |
| **P-PMX-08** | 大册主按钮可见文案丢失「按章」 | **P2** | 249 张册可见「发微信群」；aria 含按章 |
| **P-PMX-09** | `HEAD /v2` 404 | **P2** | curl `-I`；GET 正常 |
| **P-PMX-10** | 预览页窄屏无 gate / 近黑屏 | **P2** | 390px 打开大册预览 |
| **P-PMX-11** | 书架重复展示名（两本武大） | **P2** | **Park**（可选消歧，不挡 M1） |

---

## 3. 目标与非目标

### 3.1 产品目标

1. **示例不穿帮**：任何示例导入 / 再做一遍路径，读者面与成功面零「示例游记」。  
2. **状态即承诺**：设置 · 成功面 · 精修 · Dock 对 AI 就绪状态同读同源。  
3. **一名到底**：封面编辑框展示值 = 书架展示名 = 导出 stem 所用展示名。  
4. **弹层可关可点**：模态互斥；精修 × 可点。

### 3.2 非目标

- 不新增导出平台 / 不改 Recipe 分档阈值。  
- 不重写 narrate / 聚类 / 封面选图算法。  
- 不重开 SFI W2 紧凑档盲评 / 小红书文案包。  
- 不做影楼批量、不做手机完整制作台。  
- 不强制存量 14 册全量重渲（可提供惰性修复路径；全量狗粮另排）。  
- P-PMX-11 书架消歧 **Park**，除非评审升档。

### 3.3 成功指标

| 指标 | 现状（2026-07-22） | 目标 |
|------|-------------------|------|
| 示例再做一遍后读者面含「示例游记」 | 是 | **0** |
| Key 就绪时出现「配置写作引擎后可升级」 | 是（成功面/精修） | **0** |
| 封面编辑值与书架展示名不一致（脏 `--`） | 武大复现 | **0**（约定样本） |
| Wizard+复用同时可见 | 是 | **0** |
| 精修 × 可点率（桌面默认工具栏） | 0%（被拦截） | **100%** |

---

## 4. 需求详述

### WS1 · 敢发止血（P0）— M1

#### R1.1 示例题名护栏（P-PMX-01 · D-PMX-01）

- 示例相册导入（含「再做一遍」）写入：  
  - `meta.displayTitle` = **「京都雨季漫游」**（或 demo manifest 配置名）  
  - `meta.title` 不得为「示例游记」；若历史默认是该串，写入前替换  
- FirstSuccess 标题、预览封面、`<title>`、导出 stem **同读展示名**  
- 回归：`is_unsafe_share_copy("示例游记")` 已为真 → **题名路径也必须 fail-closed**（空或回退展示名，禁止落盘禁词）  
- 章名同步：禁止生成 `日期（N）`（见 R3.2）；示例重做后至少不比「京都雨季漫游」基线更差

#### R1.2 AI 就绪文案同源（P-PMX-02 · D-PMX-02）

| 表面 | `llmAvailable=false` | `llmAvailable=true` |
|------|----------------------|---------------------|
| FirstSuccess 副句 | 可保留「本机文案；可先预览导出」 | **禁止**「配置写作引擎」；改为「AI 文案已就绪，可在预览重新生成」或省略降级句 |
| 精修「这本」 | 降级提示 + 配置入口 | 「重新生成文案」单一入口；状态句与设置摘要一致 |
| Dock 提示 | 可提示去设置 | 「重新生成文案」；不遮主 CTA「发微信群」 |

- 读取契约：前端只信 `llm/status`（或 bootstrap 注入的同构字段）；禁止本地硬编码 L0 句覆盖就绪态。  
- 与 SFI D-SFI-02/04 对齐：就绪 ⇒ 有刷新动作；做不到则弱化设置摘要（本包优先修文案分支，刷新能力已有则接线）。

#### R1.3 封面展示名同源（P-PMX-03 · D-PMX-03）

- 封面「点击编辑杂志名」**初始展示** = `resolve_display_title()`  
- 含 `--` / 文件夹噪声的 `meta.title`：**不得**直接作为封面巨字  
- 用户显式保存新名：沿用 Dogfood D2（同写 `title` + `displayTitle`）  
- 约定样本：`demo-e863ec0da9` 打开即见「武大 米娜」，不见「武大--米娜」

### WS2 · 交互摩擦（P1）— M2

#### R2.1 Wizard / 复用卡互斥（P-PMX-04 · D-PMX-04）

- 触发复用卡前：关闭 Wizard 或将其 `inert` + 隐藏  
- 复用卡「取消」：回到可再次打开 Wizard 的干净首页态  
- 同时仅一个 `[role=dialog]` 持有焦点陷阱

#### R2.2 精修关闭可点（P-PMX-05 · D-PMX-05）

- 关闭 × 命中测试：在默认桌面预览工具栏展开态下，× 中心点可点击  
- 层叠对策：Sheet `z-index` 仍低于 Dock 时，以 `pointer-events` 透传关闭 ×（仅 inert 导出区不够——整条 Dock 会挡命中）  
- 不改变 V1.1「× 关闭 sheet ≠ 退出精修模式」的语义；若需退出仍走「完成」  
- Esc 关闭 sheet 保持可用

#### R2.3 大册 CTA 可见语义（P-PMX-08 · D-PMX-08）

- 当 recipe `layout=by_chapter`（或等价 band）：主按钮可见文本包含「按章导出」或产品已冻结短句（须评审锁一句）  
- aria-label 与可见文案不得互相矛盾

### WS3 · 可信与边角（P1/P2）— M3

#### R3.1 时间图注新产出硬闸（P-PMX-06 · D-PMX-06）

- 决定性瞬间图注：`timeOutlier` / 低置信 / 与 daySpan 矛盾时不得输出误导绝对年  
- 补挂 `moment_screen` 传 `daySpan` 等旁路  
- **不做**武大等存量批量重渲（D7）；旧 HTML 不纳入本包 AC 必过项

#### R3.2 章名去工程味（P-PMX-07 · D-PMX-07）

- 禁止读者面：`日期（N）`、`…续`（SFC/FST 已禁「续」——回归）  
- 同日多章：走 Chapter Naming（时段 / 地点 / 序号人话），禁止括号数字后缀  
- hook 空优于弱枚举假句（不新造文案）

#### R3.3 HEAD /v2（P-PMX-09）

- `HEAD /v2` 与 `GET /v2` 同为 302 → `/`（或 405 且 Allow 明确——优先 302 以利探测工具）

#### R3.4 预览窄屏（P-PMX-10）

- 预览路由在 `<768px`（或与首页同一断点）：展示诚实门面（返回首页制作 / 复制地址），禁止近黑屏无说明  
- 不要求手机完成导出

#### R3.5 书架重名（P-PMX-11 · Park）

- 默认不实施；若升档：副文案加日期范围或来源文件夹短名消歧

---

## 5. 交互与文案规格

| 场景 | 规格 |
|------|------|
| 示例 FirstSuccess 主句 | `《京都雨季漫游》已生成 · 照片 N 张`（不得出现「示例游记」） |
| 示例 FirstSuccess · L1 就绪 | `游记已做好，可预览与导出。AI 文案已就绪，可在预览重新生成。` |
| 示例 FirstSuccess · L0 | `游记已做好，可预览与导出。当前为本机文案。`（可保留配置引导） |
| 精修「这本」· L1 | 状态：「AI 文案已就绪」；动作：「重新生成文案」；**无**「配置写作引擎后可升级」 |
| 封面编辑占位/值 | 展示名；脏名仅存在于未 humanize 的原始字段时不得上屏 |
| 复用卡 | 单层；主按钮「打开示例 →」/「再做一遍」/「取消」 |
| 大册主 CTA（草案） | 可见：`按章导出长图` 或 `按章导出 · 发微信群`（评审锁一句） |

文案总则：无内部词；状态与设置同源；禁词不上题名；空优于假。

---

## 6. 技术实现要点（摸底清单）

| 工作流 | 疑似落点 | 备注 |
|--------|----------|------|
| R1.1 示例题名 | `desktop/demo_album.py` · `studio_pipeline` demo 分支 · FirstSuccess 模板/JS · `share_face_copy` 题名写入点 | 写入前护栏；manifest 默认名 |
| R1.2 就绪文案 | `homepage-v2/first-success.js` · 精修「这本」· Dock · `llm/status` 消费处 | 统一 readiness 选择器 |
| R1.3 封面名 | 预览 inline-edit · `resolve_display_title` · render context | 展示绑 display；保存走 DFX D2 |
| R2.1 弹层 | `import-wizard.js` · demo reuse dialog | 互斥状态机 |
| R2.2 z-index | `preview-toolbar` · `preview-sheet` CSS | 命中测试 |
| R2.3 CTA | `output-recipe.js` · longshot CTA label 映射 | 可见 vs aria |
| R3.1 离群 | SFI 合并/挑选旁路 · 决定性瞬间图注 | 能复用则复用 |
| R3.2 章名 | Chapter Naming · demo narrate/stub | 禁 `(N)` |
| R3.3 HEAD | `studio_dispatch` / handler HEAD | 与 GET 同路由 |
| QA | Playwright：示例再做一遍 · 武大封面 · 精修 × · 390 预览 | 临时 trips_dir / 自由端口 |

---

## 7. 里程碑

| 里程碑 | 范围 | 出口 |
|--------|------|------|
| **M1（P0 止血）** | R1.1 · R1.2 · R1.3 | AC-PMX-01～05；可独立合入 |
| **M2（交互）** | R2.1 · R2.2 · R2.3 | AC-PMX-06～08 |
| **M3（可信边角）** | R3.1 · R3.2 · R3.3 · R3.4 | AC-PMX-09～12；R3.5 不进出口 |

---

## 8. 遥测

复用 `studio-event`，不新增采集面：

| 事件 / 字段 | 用途 |
|-------------|------|
| `ftue_demo_album_success` + 展示名 | 抽样「示例游记」残留（期望 0） |
| FirstSuccess / refine 文案分支 | `copy_branch=l0_degraded|l1_ready`（若已有字段则复用） |
| `export_ok` / stale 徽标 | 回归：不因本包回退 CSC 成功面 |
| 可选：`refine_close_click_blocked` | 修前诊断；修后期望 0 |

---

## 9. 验收标准（AC-PMX-*）

| ID | 标准 | 验证 |
|----|------|------|
| **AC-PMX-01** | 示例「再做一遍」完成后：FirstSuccess / 封面 / `document.title` / `meta.displayTitle` **均无**「示例游记」 | Playwright + trip.json |
| **AC-PMX-02** | 同上路径展示名为「京都雨季漫游」（或 manifest 配置名） | Playwright |
| **AC-PMX-03** | `llm/status.llmAvailable=true` 时：FirstSuccess 与精修「这本」**不出现**「配置写作引擎后可升级」；出现「重新生成文案」或等价就绪句 | Playwright（本机 Key 或 mock status） |
| **AC-PMX-04** | `llmAvailable=false` 时：仍允许本机文案降级句 + 配置引导 | Playwright / 单元 |
| **AC-PMX-05** | 打开 `demo-e863ec0da9`（或等价脏名 fixture）：封面编辑控件与巨字为「武大 米娜」，**无** `武大--米娜` | Playwright + DOM |
| **AC-PMX-06** | 点「用示例照片试一次」出现复用卡时：Wizard 不可见；仅一个 dialog 焦点陷阱 | Playwright |
| **AC-PMX-07** | 精修打开后，关闭 × 中心可点击；sheet 关闭 | Playwright |
| **AC-PMX-08** | 大册 `by_chapter`：主按钮可见文案含「按章」语义 | Playwright |
| **AC-PMX-09** | 重做示例后无章名 `（N）` / 「续」 | trip.json + 预览 |
| **AC-PMX-10** | **新渲染**路径（fixture 现渲，非依赖本机旧 HTML）：决定性瞬间图注不出现误导绝对年；存量未重渲页不挡门 | pytest / 现渲断言 |
| **AC-PMX-11** | `HEAD /v2` 与 `GET /v2` 均为 302 → `/` | HTTP |
| **AC-PMX-12** | 390px 打开预览：有诚实说明或跳转门面，非无文案黑屏 | Playwright |
| **AC-PMX-13** | 回归：小册导出成功面、意图卡、设置 AI 摘要、首页窄屏 gate、长图人话文件名 **不回退** | 冒烟清单 |

**M1 门禁**：须同时验证 trip.json · FirstSuccess DOM · 封面 DOM；禁止只改成功面文案而放任 `meta.title=示例游记`。

---

## 10. 风险与开放问题

| # | 项 | 状态 |
|---|-----|------|
| 1 | 示例「京都雨季漫游」是否允许产品改名 | **开放**：默认锁定该名；若改须同步 homepage showcase |
| 2 | L1 就绪但未对旧册自动刷新 — 是否在成功面强推「立即重新生成」 | **草案**：不自动跑；只修正误导句 + 保留显式入口（对齐 SFI） |
| 3 | 脏名存量是否打开即改盘 | **草案**：展示层先修；落盘跟用户保存 / 可选惰性迁移（对齐 DFX D2） |
| 4 | 时间离群完整知情条 / 存量重渲 | **知情条跟 SFI**；**存量批量重渲不进本包（已锁）**；本包只闸新产出 |
| 5 | 书架重名消歧 | **Park** |
| 6 | 预览窄屏是否允许只读浏览 | **开放**：M3 最低为诚实门面；只读增强另议 |

---

## 11. 变更记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-07-22 | 初稿 · 基于合入后完整走查 T1–T11 · D-PMX-01～08 草案 · M1–M3 · AC-PMX-01～13 |
| v0.2 | 2026-07-22 | Conditional Go · 决策锁定（示例名/两维分离/displayTitle/弹层/inert/章名链/不做存量重渲）· 与 IMPLEMENTATION 同包一并修复 |
