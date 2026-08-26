# Travelogue · 作品集成册管线 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.2**（BLK-PFM-01～09 已回写 · AS-PFM-03 MSP 后继 · **身份/票根后继见 PIS**） |
| **状态** | **Conditional Go · 线框已签**（八席 2026-08-20 · 产品 2026-08-20 重签 F1/F3/F6）。**W0–W3 编码已清** · ISO-04/06 已关 · **AS-PFM-03 已升格 · 五档入库**（[MSP 后继](./acceptance-records/pfm-as-pfm-03-msp-promote-2026-08-21.md)）· W4 狗粮协议已锁、[语料已定点](./acceptance-records/pfm-w4-kickoff-2026-08-22.md)、人评未开（`feat/pfm-portfolio-folio-mode-v1`）；仓库 `homepage_entry` 仍关 |
| **DOC-STATUS** | **active** |
| **主题代号** | 「作品集成册」— **PFM**（Portfolio Folio Mode） |
| **界面用词** | **游记**（快分享）· **作品集**（杂志风卷轴）。禁止对 C 端说「第七种模式 / page-* / 成册引擎 / 画册已经按页」 |
| **文档类型** | 双管线运行时合同（入口 + 装配分叉 + 导出门面 + 前后端任务） |
| **触发来源** | 2026-08-20 产品：两条管线都有需求、互不干扰；筛选/聚类与现网游记一致，页面装配走成册编排。前序：[临时模板库管线讨论备忘录 §4](./templates/reserve/临时模板库管线讨论备忘录.md) · [TSU D-U-09](./PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) · [TDV D-TDV-22](./PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md) |
| **评审** | [八席纪要 2026-08-20](./acceptance-records/pfm-portfolio-folio-mode-v1-review-2026-08-20.md)（七席 + 典型用户 · 8/8 Conditional Go · BLK-PFM-01～09 · OQ-02 否决 / OQ-06 改判） |
| **前置条件** | 现网游记 GA（`layoutEngine=screens` + MCS/MTSO）· 六平台导出 GA（ADR-021）· **正式 `series/` 收件目录已定（TDV OQ-03 关闭）** · **P0 系列 `magazine-16-standard` 已入现网目录** · 活目录 `page-*` 由 TSU W3 供货（PFM 只消费） |
| **线框** | [wireframes/portfolio-folio-mode-v1-wireframe.html](./wireframes/portfolio-folio-mode-v1-wireframe.html) **v1.1**（**F0–F8 已签** · 2026-08-20 产品重签 F1/F3/F6） |
| **关联文档** | [CHARTER.md](./CHARTER.md) · [TSU](./PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) · [TDV](./PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md) · [PIS](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md)（**后继**：票根 / 双身份话术 / 成册页 X / 堂亲按星）· [RSC](./PRD-RESERVE-SERIES-CABINET-V1.md) · [EDC](./PRD-EDITORIAL-COMPILER-V1.md) · [LVP](./PRD-LAYOUT-VIBE-PICKER-V1.md) · [AEL](./PRD-ALBUM-EDITORIAL-LAB-V1.md) · [ECC](./PRD-EXPORT-CARD-COMPOSE-V1.md) · [ADR-003](./adr/003-experience-reading-modes.md) · [ADR-021](./adr/021-export-compose-dual-engine.md) · [导出门面](./PRD-PREVIEW-EXPORT-FACADE-V1.md) · [Output Recipe](./PRD-OUTPUT-RECIPE-V1.md) · [Import Wizard](./PRD-IMPORT-SHEET-v3-WIZARD.md) |
| **验收** | [ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md](./ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md)；本文 **§14 为源** |
| **实施** | [IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md](./IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md)；本文 **§12 为源** |
| **更新日期** | 2026-08-26 |
| **流程改判** | **2026-08-25 起**：导入页数、满意即导、导出面板、张数推荐口径以 [PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md)（**PFO v0.2.0**）为准。本文 **D-PFM-28 / D-PFM-13「仅精修钉页」/ N-PFM-14 / OQ-PFM-02** 视为被 PFO 改判。**D-PFM-10 / SHD-PFM-06「两种书不并排」的意图保留**：PFO D-PFO-04 和解为点法对齐 + 六种分组降级，**不按「取消折叠」落地**。装配隔离、`page-*`、身份字段、游记零改仍以本文为准。 |
| **身份/票根后继** | **2026-08-26 起**：同夹双本话术、票根「游记 / 作品集 · N 页」、成册页 X、堂亲/升星以 [PRD-PORTFOLIO-IDENTITY-STARS-V1.md](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md)（**PIS**）为准。本文 **FE-PFM-11 游记票根空串** 视为被 AMD-PIS-01 改判。装配隔离、`page-*`、身份字段仍以本文为准。 |

> **定位**
>
> 现网已经能「选相册 → 出游记 → 发群长图」。工坊已经能手编一本 16:9 杂志页序，试印观感好于现网长图。缺的是运行时那一条：**用户显式选择「做一本作品集」之后，筛选和聚类仍走现网游记，页面装配换成册系列 + `page-*`。**
>
> 这不是第七个社交平台，也不是替换默认游记，更不是把 `page-*` 接到印刷跨页。快分享与作品集是两条管线、两套装配、两套导出门面，共用上游照片池。
>
> **一句话目标**：默认零步仍出游记；想要杂志风作品集时走显式入口；两条线互不改对方的屏序、模板序列和导出主 CTA。
>
> **产品铁律**
>
> 1. **两条活，两条线。** 禁止合成「又快又精」的一条管线。平的需求由游记接着；杂志语法不降级去迁就乱组。  
> 2. **默认仍是游记。** 作品集必须用户选；关旗 ≡ 现网 GA（导入两击、六平台、LVP 两卡）。  
> 3. **分叉在装配，不分叉在策展。** ingest / cull / cluster / SSG 共用；`compose_trip` 之前插入匹配器。  
> 4. **出口让用户选，系统不猜。** 发群 → 游记长图；做一本看看 → 作品集；印书 → 仍是 `album_spread`。  
> 5. **编辑器，不是模板工厂。** 运行时不发明页拓扑；系列是写死的页清单；引擎不读工坊目录。  
> 6. **词汇不撞车。** 「游记 / 作品集」≠ 导入「快速 / 精细」≠ LVP「杂志成册 / 更贴比例」≠ 导出「印刷跨页」。**内部标识符也不许撞**（`folio` 现网已有四义 → 一律改用 `portfolio`，见 D-PFM-01）。  
> 7. **一份合同管运行时。** TSU 管资产面，TDV 管工坊，本文管 C 端入口、装配分叉、导出门面。禁止平行 Kickoff 五个算法专题。  
> 8. **做完必须有下一步动作。** 作品集导出成功面必须给出用户会照做的一件事（打开这一本 / 发这份压缩包），不许只写「已保存」。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.1 / §0.2 | 术语；与相邻主题所有权 |
| §1 | 问题与现网三轴易混 |
| §2 | 目标 / 非目标 |
| §3 | 已拍板决策（v0.2 已关 BLK） |
| §4 | 双管线地图与隔离合同 |
| §5 | 用户入口（导入 / 首页 / 精修切换） |
| §6 | 导出入口（这一本 + 页图 / 换种分享） |
| §7 | 数据模型与配置 |
| §8 | 装配合同（匹配器 / 系列 / 溢出 / 降级） |
| §9 | 渲染、阅读、文字策略 |
| §10 | 界面信息架构与文案 |
| §11 | 线框帧与签核 |
| §12 | 前后端任务（实施源） |
| §13 | 里程碑 |
| §14 | 验收 AC-PFM-* |
| §15 | 风险与开放问题 |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **成册身份 `edition`** | `trip.studio.edition` = `journal`（游记）\| `portfolio`（作品集）。一趟只属一个身份。**权威字段** |
| **游记** | 现网 Web 卷轴 + `screen-*` + 长图主分享 |
| **作品集** | 16:9 杂志卷轴 + 成册系列 + `page-*` |
| **印刷画册** | 导出平台 `album_spread`（3:4 两卡 + gutter）。**不是**本主题身份 |
| **成册系列** | 现网正式 YAML：档位页数 × 密度 × `photo_span` + 角色序。权威在现网 `series/`，不在工坊 |
| **匹配器** | `travelogue/layout_engine/editorial_series/`：选系列、组→页、溢出、flex / 靠档。TSU D-U-15 |
| **这一本** | 作品集主产物之一：现网分享包机制（`export/packager.py`）产出的可翻阅 `index.html` + 资产 zip |
| **页图** | 作品集主产物之二：按 `screens[]` 一页一张 16:9 PNG（平台 id `portfolio_pages`） |
| **换种分享** | 作品集次级出口：仍走现网六平台，用 **同一 kept 池 + ECC**，不把 `page-*` 压进竖条。默认折叠 |
| **父开关** | `studio.portfolio_pipeline.enabled`。关 = 隐藏全部作品集入口，行为 ≡ 现网 |

> **禁用标识符（D-PFM-01）**：`folio` 在现网已表示阅读皮肤 `reading.scroll.folio`、精选格 `curation.folioPlan`、封面样式 `folio-overlap`、工坊设计稿前缀 `folio-*`；`surface` 在 `render/surface.py` 已表示渲染面（draft / share / present / longshot）。本主题**一律不得**复用这两个词作为成册身份、字段名、平台 id 或错误码。

### 0.2 与相邻主题（所有权）

| 主题 | PFM 做 | PFM 不做 |
|------|--------|----------|
| **Curate / SSG / Cluster** | 只读组与 kept；作品集补角色标签供匹配 | 不重写漏斗、不按页数拆组 |
| **MCS / MTSO / LTE** | 游记继续现网；作品集在槽数带内选型 | 不把 MCS 写进匹配器；不打开 MSA |
| **TSU** | **消费**正式系列与活目录 `page-*` | **不入库页型几何**（属 TSU W3）；不建 `/series-editor`；不交 B7 手写义务 |
| **TDV / RSC** | 收升格包；不扫工坊 | 不引用工坊 HTML/JS；不把 `folio-*` 当运行时 id |
| **EDC** | `program` 枚举共用 | 不实施扉页 SKU / W3 80% 门；不等 EDC Kickoff |
| **LVP** | **只作用于游记** | 不给作品集加第三张气质卡；不把 MSA 绑进作品集 |
| **AEL / ECC / ADR-021** | 作品集「换种分享」与印刷画册仍走 ECC | 不把 `page-*` 写入 `_ALL_TEMPLATES`；不改小红书默认卡序 |
| **ABE / CAL** | 书衣沿用（作品集**唯一**有字的地方） | 不成册生成题字 |
| **导出门面 / OR** | 按身份换主 CTA；作品集**旁路** OR 意图矩阵 | 不把 `portfolio_pages` 塞进六平台平铺列表；不进批量多选 |
| **Import Wizard** | Step 2 增加身份选择，**不替换**快速/精细 | 不在导入问页数；不做第三张「精细卡」别名 |
| **ADR-003** | `screens[]` 仍是浏览/放映/长图唯一序 | 不为作品集另排 present 序 |

---

## 1. 背景与问题

### 1.1 对照事实

| 活 | 要什么 | 现网给什么 |
|----|--------|------------|
| 发群 / 朋友圈 | 快、能发、允许平 | 游记 + 六平台 · **保留** |
| 做一本看看 | 杂志节奏、页数有意、组先于脸 | 工坊试印已验证，**引擎未接** |
| 真要印 | 跨页 3:4 | `album_spread` · **保留、与作品集脱钩** |

若合成一条「又快又精」：游记被密页杂志槽拖慢、作品集被乱组装错。隔离失败的典型症状：开作品集旗后小红书卡序变了，或微信竖条出现 9 槽杂志页。

### 1.2 现网三轴（禁止混用文案）

| 轴 | 问的问题 | 现网控件 | 本主题 |
|----|----------|----------|--------|
| **成册身份** | 这趟是游记还是作品集？ | **无** | **本主题新增** |
| **导入深度** | 开始前填不填细节？ | 快速分享 / 精细制作 | 正交，保留 |
| **游记气质** | MTSO/MSA 哪一档？ | LVP 两卡 | **仅游记** |
| **发行平台** | 这张图发到哪？ | 六平台 | 游记主路径不变；作品集主路径换「这一本 + 页图」 |

LVP 卡面「杂志成册（推荐）」指的是 **游记 GA 拼图栈**，不是作品集。作品集 UI **禁止**再占用「杂志成册」四字。

### 1.3 用户可感知问题

| ID | 问题 | 落点 |
|----|------|------|
| **P-PFM-01** | 想要「一本」只能看现网长图或印刷跨页，没有杂志卷轴 | §5 / §8 |
| **P-PFM-02** | 怕选错入口把默认发群路径变慢、变难 | §5.1 零步合同 |
| **P-PFM-03** | 「画册」口语同时指作品集和印刷跨页 | §10 词表 |
| **P-PFM-04** | 做好作品集后不知道导出什么、发给谁 | §6.2 / §6.3 |
| **P-PFM-05** | 切身份会不会把精选/聚类重做一遍、会不会丢我改过的字 | §4.3 / §5.4 |
| **P-PFM-06** | **照片没全收进去，却没人告诉我** | §8.5 溢出 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-PFM-01** | 用户能在导入时显式选 **游记** 或 **作品集**；默认游记；快速游记路径仍 2 次点击 |
| **G-PFM-02** | 作品集：筛选/聚类/SSG ≡ 同册游记；装配走正式系列 + 匹配器 + `page-*` |
| **G-PFM-03** | 作品集预览是 16:9 卷轴；`screens[]` 为唯一阅读序 |
| **G-PFM-04** | 作品集主导出 = **这一本（可翻阅 zip）+ 页图序列**；六平台不出现在作品集主 CTA |
| **G-PFM-05** | 游记 trip 开 PFM 旗后：屏序、小红书/画册卡序、Dock「导出长图」与 GA 一致 |
| **G-PFM-06** | 父开关可关；关后作品集入口消失，已有作品集 trip 打开时提示并可一键改回游记重装 |
| **G-PFM-07** | 精修可在游记 / 作品集之间切换，二次确认；**只重装配 + 渲染**，不重 ingest/cull/cluster |
| **G-PFM-08** | **照片装不下时不静默**：先升档兜底，仍装不下则明示实收张数并给出改用游记的出口 |
| **G-PFM-09** | 对外零算法缩写；默认可达零外呼（NAS） |

### 2.2 非目标

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-PFM-01** | 把作品集设成默认 | 破坏零步与 80% 发群 |
| **N-PFM-02** | 第六平台旁再平铺第七个社交出口 | 身份 ≠ 平台 |
| **N-PFM-03** | `page-*` 接到 `album_spread` | TSU D-U-09；印刷另立 |
| **N-PFM-04** | 引擎读 `docs/templates/reserve/` | TDV 机器隔离 |
| **N-PFM-05** | 重写 MCS / CardGrouper / Curate | 分叉只在装配 |
| **N-PFM-06** | 运行时生成模板 / 小本×2 当正式 SKU | TSU |
| **N-PFM-07** | LVP 第三卡、导入 Wizard 改成三张模式卡抢快速/精细 | 轴会缠死 |
| **N-PFM-08** | 人手拖图进槽当 C 端主路径 | 另一个产品 |
| **N-PFM-09** | 等 EDC 80% / AEL 探针绿 | 那些管裁切与扉页 |
| **N-PFM-10** | 作品集默认把 5/7/9/10 槽页 flatten 进微信竖条 | 备忘录隔离第 1 条 |
| **N-PFM-11** | 首页主 CTA 改成「做作品集」 | 主路径仍是游记 |
| **N-PFM-12** | **新增 `layoutEngine` 第三个值** | 输出同构 `screens[]`，加值只为标身份，护栏爆破面大（D-PFM-04） |
| **N-PFM-13** | **作品集正文页排图注 / 章导语** | 现有 `page-*` 无文案区（D-PFM-22）；要文字须先在 TSU 侧供货 |
| **N-PFM-14** | **导入时问用户要几页** | **已被 PFO 推翻**（页数是规格，见 [PFO](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) D-PFO-01） |
| **N-PFM-15** | `portfolio_pages` 进批量导出多选面板 | 与社交批量混淆（SHD-01） |

---

## 3. 已拍板决策

v0.1.0 的方向合同 + 八席 Must-Fix 回写。**隔离原则不可改**；文案与落点在 F1/F3/F6 重签时可微调。

### 3.1 身份与分叉

| ID | 决策 | 来源 |
|----|------|------|
| **D-PFM-01** | **命名收口。** 成册身份字段 = `trip.studio.edition`，值 `journal` \| `portfolio`；配置 `studio.portfolio_pipeline`；参数块 `studio.portfolio`；平台 id `portfolio_pages`；错误码 `E_PORTFOLIO_UNAVAILABLE`。**禁止**使用 `folio` / `surface` 作本主题标识符（§0.1 禁用表）。匹配器包名 `editorial_series` 保留。C 端用词「作品集」不变 | BLK-01 |
| **D-PFM-02** | **默认游记。** 父开关关或用户未选 → 行为 ≡ 现网 GA | — |
| **D-PFM-03** | **分叉点。** ingest→cull→cluster→SSG→开章 **共用**；`compose_trip` 仅游记走；作品集走匹配器 → 写同构 `chapters[].screens[]` | — |
| **D-PFM-04** | **不动 `layoutEngine`。** 两种身份都写 `layoutEngine=screens` + `layoutEngineVersion`。作品集的差异体现在 `screens[].patternId`（`page-*`）与 `studio.edition`，**不体现在引擎枚举**。现网 `services/layout.py` 的 `legacy\|screens` 白名单、`screens_layout_active`、指纹、手机 items、封面解析一律不改 | BLK-02 |
| **D-PFM-32** | **游记不写身份字段。** `edition=journal` 时**不落** `studio.edition`（缺省即游记），避免快照与 `render_fingerprint` 产生无谓 diff | SHD-02 |

### 3.2 入口

| ID | 决策 | 来源 |
|----|------|------|
| **D-PFM-05** | **导入入口。** Step 2 在现有快速/精细**上方**加分段：「这次做：游记 \| 作品集」。默认游记。作品集 + 快速 = 仍两击开始 | — |
| **D-PFM-06** | **首页入口。** 主 CTA 文案不变。次入口弱链「做一本作品集」→ 打开同一 Wizard 且预选作品集。`homepage_entry` **默认 false，W2 换真 `page-*` 前不得开** | OQ-01 |
| **D-PFM-07** | **精修切换。** 精修「这本」新增「成册类型」两卡（游记 / 作品集），**不是** LVP 那两张。切换须二次确认 | — |
| **D-PFM-08** | **LVP 作用域。** 仅游记显示「成册风格」。作品集显示页数档位，不显示 MSA 实验卡 | — |
| **D-PFM-28** | **导入不问页数。** 作品集 + 精细（2b）**不出页数芯片**，一律 `auto`。页数只在精修改（那时用户已看到成品） | **已被 [PFO D-PFO-01](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) 改判** · 原文保留 |
| **D-PFM-29** | **照片过少。** kept 低于「系列库最小 `photo_span`」时，Wizard 作品集卡**默认置灰** + 一句「照片较少，作品集更适合 30 张以上」，点击可知情继续（不硬拒）。阈值由系列库派生，配置只做覆盖 | OQ-06 改判 · SHD-04 |

### 3.3 装配

| ID | 决策 | 来源 |
|----|------|------|
| **D-PFM-13** | **页数。** 自动：按 kept N 查正式系列 `photo_span` 选档。用户可在**精修**钉 8/12/16/20/24/28/32。非 4 的倍数靠档，不升 SKU | **「仅精修钉页」已被 [PFO D-PFO-02](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) 改判**；自动选档算法仍有效 |
| **D-PFM-14** | **章保留。** 不重切 `chapters` 边界。页序列跨章连续 | — |
| **D-PFM-15** | **降级。** 组装不上：换同纲领兄弟 → flex → 靠档少页 → 丢低优先级页。不改槽比、不打开 MSA、不拆组硬拼 | — |
| **D-PFM-16** | **资产。** 引擎只读现网正式 `series/` 与活目录。工坊 `folio-*` 禁止当运行时 id；正式 id `magazine-{pages}-{density}` | — |
| **D-PFM-21** | **溢出策略（照片装不下）。** 顺序执行：① 自动升档到能装下的最大档（≤32 页）；② 仍溢出 → 收录上限张数，并在**预览角标 + 成功面**明示「本册收录 96 / 180 张」，同时给「改用游记（全收）」一键出口；③ **禁止静默丢弃**。被留下的照片记入 `studio.portfolio.overflow` | BLK-03 |
| **D-PFM-27** | **手机 items 同源。** 作品集的 `chapters[].items[]` 从 `screens[]` **实收集合**派生，不用全 kept 池，保证现网出门门 `test_chapter_items_screens_sync` 不红。手机端仍是游记式降级排版，只是资产集合与网页一致 | BLK-09 |

### 3.4 渲染与文字

| ID | 决策 | 来源 |
|----|------|------|
| **D-PFM-19** | **阅读。** 作品集预览默认 `reading.profile=magazine`（现网已有该档）；不改游记默认 `default_hybrid`。密页 + 大 trip 沿用现网 WARN 写法 | SHD-08 |
| **D-PFM-22** | **V1 正文纯图。** 现有 `page-*` 数据包 `copyRegions` 绝大多数为空，作品集 V1 **正文页不排图注与章导语**；文字仅存在于封面/封底（书名、地点，沿用 CAL/ABE）。narrate 阶段在作品集路径**不落正文文案槽**；UI 与等待态**不得**出现「正在写文案」类措辞。要文字须 TSU 先供带 `copyRegions` 的页型，属另一波 | BLK-04 |

### 3.5 导出

| ID | 决策 | 来源 |
|----|------|------|
| **D-PFM-23** | **主产物并列两件。** 作品集 Dock 主钮 = **导出作品集**，一次动作产出：① **这一本**——复用现网分享包（`export/packager.py`：`index.html` + `journal.css` + `assets/`，可点开翻）；② **页图序列**——`portfolio_pages` 的 N 张 16:9 PNG。成功面主按钮 = **打开这一本**，次要 = 发送压缩包 / 打开文件夹。**禁止**只写「已保存」 | BLK-05 |
| **D-PFM-25** | **旁路 Output Recipe。** `edition=portfolio` 时不进入按 kept N 分带的意图矩阵（10–30 张 Ambiguous 意图卡不弹），默认直接走 D-PFM-23；游记路径逐字不变 | BLK-07 |
| **D-PFM-10** | **换种分享。** 作品集导出 ▾ 仍可取现网六平台，分组标题「用同一批照片出社交图」，**默认折叠**。走 ECC / Slice，**禁止**用作品集 `screens` flatten | **视觉等级经 [PFO D-PFO-04](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md) 和解**：点法对齐，六种不得与主产物平铺；分组可折叠，不强制取消折叠。ECC 不读 page-* 仍有效 |
| **D-PFM-30** | **印刷项副文。** 换种分享里的 `album_spread` 文案固定为「印刷跨页（现网画册）· 给印刷公司的 3:4 跨页，不是这一本」 | SHD-06 |
| **D-PFM-11** | **游记导出零改。** 游记的 Dock、六平台、OR 意图矩阵与 GA 逐字一致 | — |
| **D-PFM-12** | **印刷脱钩。** 即使用户人话「导出画册」，作品集主路径仍是这一本 + 页图；`album_spread` 只出现在换种分享 | — |
| **D-PFM-31** | **CLI 显式。** 作品集 trip 未传 `--platform` 时**硬要求显式**（报错并列出 `portfolio_pages` / `wechat_chat`），不再静默用 `wechat_chat` + WARN | SHD-03 |

### 3.6 切换、回滚、其它

| ID | 决策 | 来源 |
|----|------|------|
| **D-PFM-24** | **切身份的文案与锁。** 切换前二次确认须含一句「你手动改过的文字可能无法全部保留」。后端按 assetId → 章序尽力回填；回填不上的落 `studio.copyOrphans` 草稿而**不是**直接丢。与 `pipeline_state` 的 structure / copy 锁交互写进实施：解除哪些锁、解除前是否再问 | BLK-06 |
| **D-PFM-17** | **回滚。** 关旗或清除 `edition` → 游记 + 现网装配。作品集持久化字段保留但装配不读 | — |
| **D-PFM-18** | **零外呼。** W1–W3 默认可达不 MayCall | — |
| **D-PFM-20** | **书架。** 作品集 trip 票面弱标「作品集」；菜单「改为游记重排」走与精修相同确认 | — |
| **D-PFM-26** | **资产门与顶岗纪律。** W1 出门须满足 AS-PFM-01。在正式系列与 `page-*` 到位前，**任何界面与对外文档不得称「作品集」**，只能内部说「版式试验」。`page-*` 活目录入库归 **TSU W3**，PFM 不吸收 | BLK-08 |

---

## 4. 双管线地图与隔离合同

### 4.1 系统地图

```
选夹
  → ingest / cull / cluster / SSG / kept        ← 共用，禁止分叉
  → 读 trip.studio.edition（缺省 journal）
        │
        ├─ journal   → compose_trip → screen-* → 预览游记
        │                Dock：导出长图 → 六平台
        │
        └─ portfolio → 匹配器（选系列 · 组→页 · 溢出）→ page-*
                         layoutEngine 仍 = screens（D-PFM-04）
                         预览作品集卷轴（正文无文字 · D-PFM-22）
                         Dock：导出作品集 → 这一本 zip + 页图序列
                         ▾ 换种分享（默认折叠）→ 六平台（ECC，不读 page-*）
```

### 4.2 隔离验收（污染红线）

| ID | 红线 |
|----|------|
| **ISO-01** | 开旗 + 只做游记 trip：`render_fingerprint` **字段级**比对与关旗一致（不再用「允许压缩头差」这种模糊口径） |
| **ISO-02** | 开旗后导出 `xiaohongshu` / `album_spread`：模板 id 序列与 GA 一致（游记 trip） |
| **ISO-03** | 作品集导出文件名不得占用 `*-longshot.png` / `*-album-*` / `*-xhs-*` 前缀 |
| **ISO-04** | 微信群路径不得出现作品集 5 槽以上 `page-*` 几何 |
| **ISO-05** | 代码与测试禁止新增对 `docs/templates/reserve/` 的业务读取（检索范围沿用 TDV AC-07） |
| **ISO-06** | LVP 写入不得改变 `edition`；改 `edition` 不得暗改 `layoutVibe` |
| **ISO-07** | **`layoutEngine` 枚举与现网一致**：全库检索不得出现第三个引擎值 |
| **ISO-DPI** | 读者面隔离（渲染 builder / CSS 产物 / 导出分发 / Dock 分发）以 [PRD-DUAL-PIPELINE-ISOLATION-V1.md](./PRD-DUAL-PIPELINE-ISOLATION-V1.md) 为准。**不改 ISO-01～07 原文** |

### 4.3 重排边界

| 用户动作 | 重跑 | 不重跑 |
|----------|------|--------|
| 导入时选身份 | 全管线 | — |
| 精修切换身份 | 装配 + 文案迁移（D-PFM-24）+ render | ingest / cull / cluster / SSG |
| 只改作品集页数档 | 匹配器 + 装填 + render | 上游 |
| 游记 LVP 切换 | 现网 layout | 身份 |

---

## 5. 用户入口

### 5.1 零步合同（游记）

与 Import Wizard AC-IW-13 对齐：**首次用户选夹 → 开始制作 = 2 次点击**。身份默认游记，分段控件不增加必点击。

### 5.2 入口 A · 导入 Wizard（主）

**落点**：Step 2「确认并开始」，在模式卡（快速/精细）**之上**。

```
这次做
  [ 游记（推荐） ]  [ 作品集 ]

然后（现网保留）
  ● 快速分享     ○ 精细制作
```

| 组合 | CTA | 下游 |
|------|-----|------|
| 游记 + 快速 | 开始制作 → | 现网 payload（不写 `edition`） |
| 游记 + 精细 | 填写细节 → | 2b，现网 |
| 作品集 + 快速 | 开始制作作品集 → | `edition=portfolio`，页数 `auto` |
| 作品集 + 精细 | 填写细节 → | 2b **与游记同款**，**不增加页数芯片**（D-PFM-28） |

作品集卡副文：`按杂志页编排，做完能点开翻。发群请选游记。`（副文须回答「做出来是什么」——BLK-05 精神）

**照片过少**（D-PFM-29）：作品集卡置灰 + 副文改「照片较少，作品集更适合 30 张以上」，点击弹一次确认后仍可继续。

**禁止**：把作品集做成第三张与快速/精细并列的大卡；在导入阶段问页数。

### 5.3 入口 B · 首页次链

Bento 主 CTA 不变。主按钮旁弱链 `做一本作品集`：

- 打开同一 Wizard，身份预选作品集。  
- 父开关关、`homepage_entry=false`、或 FTUE 首访：隐藏。  
- **W2 换真 `page-*` 前保持 false**（D-PFM-06）。

### 5.4 入口 C · 精修「这本」

分区名：**成册类型**（不要用「成册风格」——那是 LVP）。

| 卡 | 选中时 |
|----|--------|
| 游记 | 现网卷轴 + 长图导出 |
| 作品集 | 杂志页 + 这一本 + 页图导出 |

作品集选中时下方出现**页数**芯片（自动 / 8 / 12 / 16 / 20 / 24 / 28 / 32）——这是页数唯一的用户入口。

切换 → 模态：

- 标题：`改成「作品集」？` / `改回「游记」？`  
- 正文：`精选和分组会保留，页面将按另一套版式重排。`  
- **必带一句**（D-PFM-24）：`你手动改过的文字可能无法全部保留。`  
- 作品集方向再加：`页数可能变少，照片可能收录不全；发群请改用「换种分享」。`  
- 主钮：`重排页面` · 次：`取消`

LVP「成册风格」整组：作品集时 **卸载**（DOM 不渲染）。

### 5.5 不做的入口

- 全屏阻塞「请选择产品形态」Wizard（违反零步）  
- 导出面板里用平台单选来「生成作品集」（身份必须先于导出）  
- Studio 底栏「版式」（那是 TSU 治理，D-TDV-19）

---

## 6. 导出入口

### 6.1 按身份的门面

| | 游记 | 作品集 |
|--|------|--------|
| Dock 主钮 | **导出长图**（现网） | **导出作品集** |
| 默认 recipe | Output Recipe / 六平台（现网） | **旁路 OR**（D-PFM-25）→ 这一本 + 页图 |
| 产物 | 现网 | ① `index.html` 分享包 zip ② N 张 16:9 PNG |
| 成功面 | 现网发群一句 | 「作品集已导出 · 共 N 页」+ 主按钮**打开这一本** + 溢出提示（若有） |
| ▾ 高级 | 现网六平台 + zip | 只出页图 / 只出这一本 · **换种分享（默认折叠）** |

### 6.2 主导出「导出作品集」

| 项 | 合同 |
|----|------|
| 动作 | 一次点击产出两件（D-PFM-23）；任一失败不阻断另一件 |
| ① 这一本 | 复用 `export/packager.py` 分享包：`index.html` + `journal.css` + `assets/` + 封面图，用户双击即可翻 |
| ② 页图 | 平台 id `portfolio_pages`；每屏一张 16:9 PNG，顺序 = `screens[]`（含封面/封底渲染结果） |
| 命名 | `{title}-portfolio-{nn}.png`；zip 沿用现网 `share_zip_filename` |
| 引擎 | 页图走预览同源渲染（Playwright 按屏截，参照现网分章截图管线），**禁止** Pillow 3:4 CardGrouper 顶岗 |
| 失败 | 单页失败可跳过并在清单标注；不因一页失败回滚全部。成功面页数须报**实际成功页数**与跳过页 |
| 平台接入面 | 只登记到 `KNOWN_PLATFORM_IDS` + Studio 作品集门面 + CLI；**不进** `PHASE_A_PLATFORMS` 平铺、**不进**批量多选（N-PFM-15） |

V1 **不做** PDF / 印刷出血。用户把页图交给对方缩放。

### 6.3 作品集 × 六平台（换种分享）

允许，但必须满足：

1. UI 分组且**默认折叠**，不与主钮平铺成七个圆点。  
2. 数据源 = kept 照片顺序/池，走现网 `export_collage_pack` / Slice-A，**不读**作品集 `patternId`。  
3. 提示一句：`社交图仍按现网拼贴，不是这一本作品集的页。`  
4. `album_spread` 副文按 D-PFM-30 固定。  
5. Isolation：作品集 trip 的 `album_spread` 卡序算法 ≡ 同 kept 池的游记导出。

### 6.4 游记 × 作品集产物

**禁止。** 游记的导出设置里不出现「导出作品集 / 页图」。想要杂志页走入口 C 改身份。

### 6.5 CLI

```
travelogue render --platform portfolio_pages   # 仅作品集 trip，否则明确错误
travelogue render --platform wechat_chat       # 游记默认
```

作品集 trip 未传 `--platform`：**报错并列出可选值**（D-PFM-31），不静默默认。

---

## 7. 数据模型与配置

### 7.1 trip.json（增量）

```json
{
  "layoutEngine": "screens",
  "studio": {
    "edition": "portfolio",
    "portfolio": {
      "seriesId": "magazine-16-standard",
      "pageCount": 16,
      "pageCountSource": "auto",
      "density": "standard",
      "photosPlaced": 96,
      "photosKept": 180,
      "overflow": { "count": 84, "resolution": "tier_upgraded_then_capped" },
      "match": {
        "flexUsed": ["s07"],
        "droppedRoles": [],
        "nearMiss": "photo_span"
      }
    },
    "copyOrphans": []
  }
}
```

| 字段 | 说明 |
|------|------|
| `studio.edition` | 权威。**游记不写**（缺省即 journal，D-PFM-32） |
| `layoutEngine` | **恒为 `screens`**（D-PFM-04）。不因身份变化 |
| `studio.portfolio.seriesId` | 命中的正式系列 |
| `pageCountSource` | `auto` \| `user`（`user` 只可能来自精修） |
| `photosPlaced` / `photosKept` / `overflow` | 溢出口径（D-PFM-21）；UI 明示的数据源 |
| `studio.copyOrphans` | 切身份时回填不上的文案草稿（D-PFM-24） |

`layoutVibe` 仅游记有效；作品集 trip 可保留旧值但装配忽略。

### 7.2 配置

```yaml
studio:
  portfolio_pipeline:
    enabled: false            # 父开关；狗粮再开
    homepage_entry: false     # 次链；W2 换真 page-* 前不得开（D-PFM-06）
    allow_refine_switch: true
    max_pages: 32
    min_kept_override: null   # 缺省由系列库最小 photo_span 派生（D-PFM-29）
```

### 7.3 Schema

`trip.schema.json`：

- **不改** `layoutEngine` 枚举（D-PFM-04）。  
- `studio.edition`（enum `journal|portfolio`）、`studio.portfolio`、`studio.copyOrphans` 入 `$defs`。  
- `layoutScreen.patternId`：游记仍走封闭 `screen-*` 枚举（H8 / Critic 白名单）；作品集允许 `page-*` 前缀（LTE 已收的脸才能过语义校验）。**不把 `page-*` 写入 mosaic 活跃集。**  
- 关旗校验：`enabled=false` 时 API 拒绝新建作品集（已有 trip 只读提示 + 可改回游记）。

---

## 8. 装配合同

### 8.1 匹配器包

路径：`travelogue/layout_engine/editorial_series/`（TSU D-U-15）。禁止 `layout_templates` / `mosaic` 反向 import；import-linter 加边。

职责：

1. 输入：kept N、可选 P、shotGroup 列表、朝向、正式系列库。  
2. 选系列：`pageCount` 匹配且 `density` 匹配且 N ∈ `photo_span`；多命中取 version 最新。  
3. 零命中：**先按 §8.5 升档**，再靠档（TSU D-U-11），仍零则最近系列 + 受约束删/flex。  
4. 组→页：一组一页为默认；大组可连续多页；**禁止一页跨两个 shotGroup**。密页（槽≥5）只给 `kind=scene` 且组内张数 ≥ 槽下限。  
5. 输出：每页 `{ role, program, slotBand, faceHint?, assetIds[] }` → 写成 `screens[]`；同时派生 `items[]`（D-PFM-27）。

### 8.2 与 compose_trip

`run_curate` 在现网调用 `compose_trip` 处分支：

```
if edition == "portfolio" and flag: compose_portfolio_trip(...)
else:                               compose_trip(...)   # 零改签名
```

禁止复制 `curate.py`。作品集失败（无系列、全组装不上）：**硬失败并回用户话**「作品集暂时排不出，可改回游记」（`E_PORTFOLIO_UNAVAILABLE`）；禁止静默掉回 `screen-*` 却仍标作品集。

### 8.3 正式系列最小集（出门）

| 优先级 | 系列 | 说明 |
|--------|------|------|
| P0 | `magazine-16-standard` | 金样；无此本不得宣称 W1 绿 |
| P1 | `magazine-8-standard` | 短档 |
| P1 | `magazine-24-standard` 或 `magazine-32-standard` | 长档一根即可 |
| P2 | 其余 12/20/28 × 疏正密 | 不挡 W1，挡「档位芯片全开」 |

工坊 `folio-16-standard` 只作设计稿，运营升格后改 id。工坊 `folio-24-standard` **已纠正为 24 页**（历史 `pageCount: 32` 不再存在）；升格检查单仍硬拒 id 与页数不一致。对账见 [AS-PFM-03 纪要](./acceptance-records/pfm-as-pfm-03-atelier-reconcile-2026-08-21.md)。

### 8.4 装填

拼图漏斗形态不变：朝向硬门、供给感知、失败链。作品集只多吃「槽数带 ∩ 数据包 `slots[].aspect` 软靠档」。裁切：`page-*` 走 TSU D-U-10。

### 8.5 溢出（照片装不下）· D-PFM-21

游记是**全收**（所有 body 资产上屏），作品集受系列 `photo_span` 上限约束。处理顺序：

| 步 | 行为 |
|----|------|
| 1 | 命中档位装不下 → **自动升到能装下的最大档**（≤ `max_pages`，且档位存在于系列库） |
| 2 | 升到 32 页仍装不下 → 按系列角色优先级收录上限张数，其余记入 `overflow` |
| 3 | 写 `photosPlaced` / `photosKept` / `overflow`，**预览角标 + 成功面明示**：`本册收录 96 / 180 张` |
| 4 | 明示旁边给一键出口：`改用游记（全收）` → 走 §5.4 同一确认 |
| 5 | 用户在精修手动钉小页数导致溢出：同样明示，不再自动升档（尊重显式选择） |

**禁止**：静默丢弃、只在日志里写、用「已优选」这类话术遮盖。

---

## 9. 渲染、阅读与文字

| 项 | 游记 | 作品集 |
|----|------|--------|
| `index.html` | 现网 screens | 同壳；`patternId` 为 `page-*` |
| `layoutEngine` | `screens` | **`screens`**（D-PFM-04） |
| CSS | 现网 LTE | 活目录 `page-*` 几何（TSU W3 供货） |
| 阅读 profile | `default_hybrid` | `magazine`（现网已有） |
| 放映 | 1 screen = 1 slide | 同 |
| 手机 items | 现网 | 从 `screens[]` 实收集合派生（D-PFM-27） |
| 正文文字 | 现网图注/章导语 | **无**（D-PFM-22） |
| 封面封底 | 现网 | 同；书名与地点沿用 CAL/ABE；封底无内容不硬造空页 |
| 长图 HTML | 现网 flatten | V1 **不**用作品集密页生成默认分享长图；换种分享走平台 Writer |

**文字策略的对外说法**（§10 词表配套）：作品集是「一本以照片为主的册子」，不承诺图注。等待态文案禁止出现「正在写文案」。

---

## 10. 界面文案（单一词表）

| 用户可见 | 用在 | 禁止搭配 |
|----------|------|----------|
| 游记 | 身份、书架标 | 「普通 / 旧版 / 第六种」 |
| 作品集 | 身份、入口 B/C | 「画册」（易与印刷撞）、「杂志成册」（LVP 占用） |
| **导出作品集** | 作品集主 CTA | 「导出长图」「导出画册」 |
| 这一本 | 成功面主按钮「打开这一本」 | 「打开 HTML」「打开站点」 |
| 页图 | 产物名、次级导出项 | 单独当主 CTA（v0.1 旧稿口径，已废） |
| 导出长图 | 游记主 CTA | 作品集主钮 |
| 印刷跨页（现网画册） | 换种分享里的 `album_spread` | 单独叫「画册」而不加「印刷/跨页」 |
| 本册收录 N / M 张 | 溢出明示 | 「已智能优选」「已为你精简」 |
| 重排页面 | 切换确认主钮 | 「重新导入」 |
| 成册类型 | 精修分区 | 「成册风格」（LVP） |

算法缩写（PFM / MCS / page-* / seriesId / edition）不进 C 端。

---

## 11. 线框帧与签核

权威稿：[portfolio-folio-mode-v1-wireframe.html](./wireframes/portfolio-folio-mode-v1-wireframe.html) **v1.1**

| 帧 | 审什么 | 八席结论 |
|----|--------|----------|
| **F0** | 双管线地图 + 三轴对照 | **已签** |
| **F1** | Wizard Step 2：身份分段 + 快速/精细 | **已签**（2026-08-20 产品重签：撤页数芯片、补成品副文、置灰+知情继续） |
| **F2** | 首页次链 | **已签**（绑 W2 才露） |
| **F3** | 作品集预览 Dock + 成功面 | **已签**（2026-08-20 产品重签：主钮「导出作品集」、成功面「打开这一本」、溢出明示） |
| **F4** | 游记预览 Dock（对照：零变化） | **已签** |
| **F5** | 作品集导出 ▾ 换种分享 | **已签（有条件）** · 默认折叠 + 印刷副文 |
| **F6** | 精修成册类型 + 确认模态 | **已签**（2026-08-20 产品重签：「文字可能无法全部保留」、页数芯片仅精修） |
| **F7** | 书架标 + 菜单改身份 | **已签** |
| **F8** | 禁止形态 | **已签** · 新增两条红线（无正式系列不得称作品集、不得静默丢照片） |

**签核规则**：F0 已过 → W1 线框门通过。**AS-PFM-01 P0 已入库。** 界面仍不得称作品集（等 `page-*`）。**F1/F3/F6 已于 2026-08-20 重签** → W3 入口可拆。

---

## 12. 前后端任务（实施源）

估时为单人工程日，含单测，不含盲评与画新脸。

### 12.1 后端

| ID | 任务 | 落点 | 估时 | 里程碑 |
|----|------|------|------|--------|
| **BE-PFM-01** | 父开关 + config schema（`portfolio_pipeline`） | `config` / `runtime.py` | 0.3 | W0 |
| **BE-PFM-02** | trip schema：`studio.edition` / `studio.portfolio` / `copyOrphans`；**不动 `layoutEngine` 枚举** | `schemas/trip.schema.json` | 0.5 | W0 |
| **BE-PFM-03** | import payload 接受 `edition`；游记不落字段；默认游记 | studio import handlers | 0.5 | W1 |
| **BE-PFM-04** | `run_curate` 身份分支；游记调用签名零改 | `curate.py` | 0.5 | W1 |
| **BE-PFM-05** | 新建 `editorial_series` 包：读正式系列 YAML、选系列、靠档 | 新包 | 2.0 | W1 |
| **BE-PFM-06** | 组→页 + 密页硬门 + flex + 降级诊断写入 `studio.portfolio.match` | 同上 | 2.5 | W1 |
| **BE-PFM-07** | 装填：槽数带内调现网选型；写出 `screens[]` | mosaic 薄适配 / `compose_portfolio_trip` | 2.0 | W1 |
| **BE-PFM-21** | **溢出：自动升档 + 收录上限 + `overflow` 口径**（D-PFM-21） | `editorial_series` | 1.0 | W1 |
| **BE-PFM-22** | **`items[]` 从实收 `screens` 派生**，保 `test_chapter_items_screens_sync` 绿（D-PFM-27） | curate / layout 适配 | 0.8 | W1 |
| **BE-PFM-08** | 关旗 / 无系列 → `E_PORTFOLIO_UNAVAILABLE`，不静默 | pipeline_state / handlers | 0.5 | W1 |
| **BE-PFM-09** | import-linter 边：lte/mosaic 不得反向依赖 `editorial_series` | `importlinter` | 0.3 | W1 |
| **BE-PFM-10** | 正式系列目录加载器（不扫 reserve） | 现网 `series/` | 0.5 | W1 |
| **BE-PFM-11** | **消费**活目录 `page-*` 几何 + 渲染打通（**入库归 TSU W3**，本任务不含画脸/写几何） | render / LTE 适配 | 1.0 | W2 |
| **BE-PFM-12** | 阅读 profile：作品集默认 `magazine` + 大 trip WARN | `reading_profile.py` | 0.3 | W2 |
| **BE-PFM-13** | 平台 `portfolio_pages` Writer：逐屏 16:9 截图、原子写、单页失败继续、文件名隔离 | `export/` | **3.5** | W2 |
| **BE-PFM-23** | **「导出作品集」编排**：一次动作产出分享包 zip（复用 `packager.export_trip`）+ 页图，任一失败不阻断另一件 | `export/` / handlers | 1.0 | W2 |
| **BE-PFM-24** | **Output Recipe 旁路**：作品集不进意图矩阵（D-PFM-25） | output recipe / handlers | 0.5 | W2 |
| **BE-PFM-14** | 作品集 trip 调六平台时走 ECC/Slice，忽略作品集 patternId | `longshot.py` / collage_pack | 1.0 | W2 |
| **BE-PFM-15** | 精修切换 API：只从 curate 装配段重入 | trip_replan / pipeline | 1.0 | W3 |
| **BE-PFM-25** | **文案迁移 + 锁交互**：按 assetId/章序回填，落 `copyOrphans`（D-PFM-24） | copy / pipeline_state | 1.5 | W3 |
| **BE-PFM-16** | GET trip 投影：`edition`、主 CTA、溢出提示、LVP 是否可见 | studio handlers | 0.5 | W3 |
| **BE-PFM-17** | CLI：`--edition portfolio`；作品集缺 `--platform` 硬报错（D-PFM-31） | `cli/pipeline.py` / render_cmds | 0.5 | W3 |
| **BE-PFM-18** | 隔离回归：游记指纹字段级 + xhs/album 卡序夹具 + `layoutEngine` 枚举检索（ISO-07） | tests/ | 1.5 | W2 |
| **BE-PFM-19** | 匹配器单测：跨组硬拼拒绝、`photo_span`、靠档、**溢出升档** | tests/unit/layout_engine/ | 1.8 | W1 |
| **BE-PFM-20** | telemetry：`edition`、`seriesId`、`pageCountSource`、`overflow.count` | studio_telemetry | 0.3 | W3 |

后端合计约 **25.3 人日**（不含画脸与 TSU 入库）。

### 12.2 前端

| ID | 任务 | 落点 | 估时 | 里程碑 |
|----|------|------|------|--------|
| **FE-PFM-01** | Wizard Step 2 身份分段；默认游记；payload `edition` | import wizard JS | 1.0 | W3 |
| **FE-PFM-02** | 作品集 CTA 与副文；**照片过少置灰 + 知情继续**（D-PFM-29）。**不做页数芯片** | 同上 | 0.6 | W3 |
| **FE-PFM-03** | 首页次链；flag / FTUE 隐藏（默认不露） | homepage-v2 | 0.5 | W3 |
| **FE-PFM-04** | 预览 Dock：按身份切主钮「导出作品集」 | dock.js / longshot.js | 1.0 | W3 |
| **FE-PFM-05** | 作品集导出 ▾：主产物两项 + **换种分享默认折叠** + 印刷副文 | export popover | 1.0 | W3 |
| **FE-PFM-06** | 游记导出 UI 快照测试：零 diff | fixtures | 0.5 | W3 |
| **FE-PFM-07** | 精修「成册类型」两卡；作品集卸载 LVP 成册风格 | refine 这本 | 1.2 | W3 |
| **FE-PFM-08** | 切换确认模态（含「文字可能无法全部保留」+ 溢出预警） | 同上 | 0.5 | W3 |
| **FE-PFM-09** | 页数档位芯片（自动 + 8–32）——**仅精修** | refine 这本 | 0.6 | W3 |
| **FE-PFM-10** | 成功面：「共 N 页」+ **打开这一本** + 发送压缩包 + 溢出明示 | FirstSuccess / export success | 0.8 | W3 |
| **FE-PFM-16** | **预览溢出角标**「本册收录 96 / 180 张 · 改用游记」 | preview chrome | 0.5 | W3 |
| **FE-PFM-11** | 书架「作品集」弱标 + 菜单改身份 | shelf card | 0.6 | W3 |
| **FE-PFM-12** | 窄屏 gate：作品集精修/导出仍电脑 | narrow-gate.js | 0.2 | W3 |
| **FE-PFM-13** | 等待态：作品集「正在按杂志页编排」（**禁出现写文案措辞**） | wait tips | 0.3 | W3 |
| **FE-PFM-14** | 关旗：隐藏 B/C 入口；打开旧作品集 trip 横幅 | chrome | 0.4 | W3 |
| **FE-PFM-15** | a11y：身份 radiogroup、确认焦点陷阱 | wizard / refine | 0.4 | W3 |

前端合计约 **10.1 人日**。

### 12.3 资产 / 运营（非编码但挡门）

| ID | 任务 | 业主 | 挡门 |
|----|------|------|------|
| **AS-PFM-01** | 正式 `series/` 收件目录定案（TDV OQ-03 关闭）+ P0 `magazine-16-standard` 入库 | TSU + 运营 | **P0 已入运行时目录** |
| **AS-PFM-02** | 活目录 `page-*` 几何入 LTE | **TSU W3** | **75 张已编译（P0 11 张齐；page-10 未收）** |
| **AS-PFM-03** | 工坊 YAML 页数与 id 对账（拒 `folio-24` 标 32） | 运营 | **已升格 · 五档入库**（8/12/16/20/28）；24/32/36 见 [MSP](./PRD-MAGAZINE-SERIES-PROMOTION-V1.md) |
| **AS-PFM-04** | CHARTER 补一行「第二产品形态：作品集」，明确不改主叙事 | 产品 | 不挡波次（SHD-05） |

---

## 13. 里程碑

| 里程碑 | 内容 | 挡门 |
|--------|------|------|
| **W0** | 线框重签 · 命名/schema/flag · 本文 v0.2 | F1/F3/F6 重签 |
| **W1** | 匹配器 + curate 分支 + 溢出 + items 同源 + 关旗回退 | **AS-PFM-01**；AC-PFM-01～12、27～30 |
| **W2** | `page-*` 渲染（TSU 供货）+ 导出作品集（这一本 + 页图）+ OR 旁路 + 隔离回归 | AC-PFM-13～19、31～35；ISO-01～07 |
| **W3** | Wizard / 首页 / Dock / 精修 / 书架 / 文案迁移 | 线框 F1–F7；AC-PFM-20～26、36～38 |
| **W4** | 狗粮三册（短/金样/长）盲评「像一本」；决定是否露出首页次链 | 不自动改默认身份 |

**W1 顶岗纪律**（D-PFM-26）：正式系列与 `page-*` 到位前，W1 只能内部预演，界面与文档一律说「版式试验」，**不得称作品集**。

---

## 14. 验收（源）

### 14.1 隔离与默认

| ID | 断言 |
|----|------|
| **AC-PFM-01** | 父开关默认 false；Studio 无作品集入口 |
| **AC-PFM-02** | 开旗 + 不选作品集：导入两击、Dock「导出长图」、六平台仍在 |
| **AC-PFM-03** | ISO-01 游记 `render_fingerprint` 字段级一致 |
| **AC-PFM-04** | ISO-02 xhs / album 卡序（游记 trip） |
| **AC-PFM-05** | ISO-05 无 reserve 业务读取 |
| **AC-PFM-06** | LVP 两卡在游记仍在；作品集不渲染「成册风格」 |
| **AC-PFM-07** | 关旗后新 import 拒绝作品集；旧 trip 横幅 + 可改回游记 |
| **AC-PFM-27** | **ISO-07**：全库不存在第三个 `layoutEngine` 值；作品集 trip 的 `layoutEngine == "screens"` |
| **AC-PFM-28** | **游记 trip 不写 `studio.edition`**（快照零 diff） |

### 14.2 装配与溢出

| ID | 断言 |
|----|------|
| **AC-PFM-08** | 同相册游记 vs 作品集：shotGroup 边界一致；作品集 kept **实收集合 ⊆ 游记集合**，且等于 `screens` 出现的资产集合 |
| **AC-PFM-09** | 一页 assetIds 不跨两个 shotGroup |
| **AC-PFM-10** | 槽≥5 的页：组规模不足则降级少槽，不硬塞 |
| **AC-PFM-11** | 无命中系列 → `E_PORTFOLIO_UNAVAILABLE`，UI 可改回游记，不静默换身份 |
| **AC-PFM-12** | 精修钉 18 页 → 靠档并显示「非标准页数 · 按 16 页靠档」 |
| **AC-PFM-29** | **溢出升档**：kept 超出命中档 `photo_span` 时先升档；升到 `max_pages` 仍溢出才收录上限 |
| **AC-PFM-30** | **溢出明示**：`photosPlaced < photosKept` 时，预览角标与成功面均出现「本册收录 N / M 张」且带「改用游记」出口；日志-only 视为失败 |
| **AC-PFM-31** | **items 同源**：`test_chapter_items_screens_sync` 在作品集 trip 上绿 |

### 14.3 渲染与文字

| ID | 断言 |
|----|------|
| **AC-PFM-32** | 作品集正文页渲染结果不含图注/章导语文本节点；封面封底书名地点仍在 |
| **AC-PFM-33** | 作品集等待态与成功面文案不含「文案 / 正在写」类措辞 |
| **AC-PFM-34** | 作品集阅读 profile 默认 `magazine`；游记默认不变 |

### 14.4 入口与导出

| ID | 断言 |
|----|------|
| **AC-PFM-13** | Wizard 默认身份=游记；键盘可切到作品集 |
| **AC-PFM-14** | 作品集 + 快速：仍两击（选夹 + 开始） |
| **AC-PFM-35** | **导入 2b 不出现页数控件**（游记与作品集的精细页一致） |
| **AC-PFM-36** | **照片过少**：低于派生阈值时作品集卡置灰 + 提示，确认后仍可继续 |
| **AC-PFM-15** | 首页主 CTA 文案相对 GA 零改；次链只在 flag + `homepage_entry` 且默认 false |
| **AC-PFM-16** | 作品集 Dock 主钮「导出作品集」；不出现主钮「导出长图」 |
| **AC-PFM-37** | **一次动作两件产物**：成功后既有可打开的 `index.html` 分享包，又有 N 张页图；其中一件失败另一件仍产出并在面板标注 |
| **AC-PFM-38** | **成功面主按钮是「打开这一本」**，且能真正打开分享包；页数报实际成功页数 |
| **AC-PFM-17** | 页图文件名前缀隔离；页数 = 成功截图页数（跳过页单列） |
| **AC-PFM-18** | 换种分享导出 xhs 不读取作品集 patternId（单测 spy/契约）；面板默认折叠 |
| **AC-PFM-19** | 作品集路径**不弹** OR 意图卡；游记路径意图矩阵零改 |
| **AC-PFM-20** | 精修切换确认含「精选保留」**与「文字可能无法全部保留」**；取消后身份不变 |
| **AC-PFM-39** | **文案迁移**：改过文案后切换身份，可回填的回填，回填不上的进 `copyOrphans` 且不静默丢 |
| **AC-PFM-21** | 切换只触发装配段（telemetry 无 ingest stage） |
| **AC-PFM-22** | 书架作品集弱标 |
| **AC-PFM-23** | C 端文案零 `page-*` / `PFM` / `MCS` / `edition` |
| **AC-PFM-24** | 窄屏仍提示电脑精修/导出 |
| **AC-PFM-40** | **CLI**：作品集 trip 缺 `--platform` 报错并列可选值；`portfolio_pages` 不出现在批量多选面板 |

### 14.5 观感（W4）

| ID | 断言 |
|----|------|
| **AC-PFM-25** | 金样系列语料上，盲评（成对 · 隐藏来源 · 固定三问评分表）「像不像一本」胜出 |
| **AC-PFM-26** | 对外文档不出现「画册已经按页用 page-*」；正式系列到位前不出现「作品集」对外表述 |

---

## 15. 风险与开放问题

### 15.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-PFM-01** | 正式系列未齐，预演长得像游记 | D-PFM-26 顶岗纪律；`homepage_entry` 默认 false |
| **R-PFM-02** | 用户把作品集当发群路径 | Wizard 副文 + 主 CTA 不叫长图 + 换种分享兜底 |
| **R-PFM-03** | 与 LVP「杂志成册」撞名 | §10 词表 |
| **R-PFM-04** | 匹配器塞进 MCS | TSU D-U-15 + import-linter |
| **R-PFM-05** | 切身份重跑聚类，久等 | D-PFM-07 + AC-PFM-21 |
| **R-PFM-06** | 溢出提示被当成「软件吞图」投诉 | 明示 + 一键改用游记（D-PFM-21 步 4） |
| **R-PFM-07** | 纯图作品集被认为「没做完」 | 副文与成功面明说是以照片为主的册子；封面封底仍有字 |
| **R-PFM-08** | 逐屏截图性能（32 页 × 高分辨） | BE-PFM-13 已按 3.5 天估；单页失败继续；必要时降 scale |

### 15.2 开放问题（v0.1 遗留 · 已裁决）

| ID | 问题 | 裁决 | 落点 |
|----|------|------|------|
| **OQ-PFM-01** | 首页次链？ | **维持 · 加门**：要，但 `homepage_entry` 默认 false，W2 后开 | D-PFM-06 |
| **OQ-PFM-02** | 导入精细露页数芯片？ | **否决**：导入一律 auto，页数只在精修 | D-PFM-28 · N-PFM-14 |
| **OQ-PFM-03** | 换种分享列全部六平台？ | **维持 · 加约束**：列出但默认折叠 + 印刷副文 | D-PFM-10 / 30 |
| **OQ-PFM-04** | 允许改回游记？ | **维持 · 绑文案迁移** | D-PFM-24 |
| **OQ-PFM-05** | 页图含封面封底？ | **维持 · 加验样**：含；W2 看全视窗 Opening 截 16:9 实样；封底无内容不硬造 | §9 |
| **OQ-PFM-06** | kept 过少允许作品集？ | **改判**：置灰 + 知情继续；阈值由系列库派生 | D-PFM-29 |
| **OQ-PFM-07** | 照片装不下怎么办？ | **升档兜底 + 明示实收 + 改用游记出口** | D-PFM-21 · §8.5 |
| **OQ-PFM-08** | 作品集成品形态？ | **并列两件**：这一本（可翻阅 zip）+ 页图；成功面主动作「打开这一本」 | D-PFM-23 |
| **OQ-PFM-09** | V1 是否完全无正文文字？ | **是**，纯图编排，明写 | D-PFM-22 |

### 15.3 仍开放（不挡 Kickoff）

| ID | 问题 | 何时答 |
|----|------|--------|
| **OQ-PFM-10** | 页图是否需要提供 2× / 打印级分辨率选项 | W2 狗粮后 |
| **OQ-PFM-11** | 「这一本」是否需要一个可发链接（而非 zip） | W4 之后另立 |
| **OQ-PFM-12** | 作品集是否值得单独的封面风格（区别于游记 Opening） | 依 W4 盲评结论 |

---

## 16. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-08-20 | 初稿。收口双管线、入口、导出、隔离、前后端任务。待审线框 F0–F8。 |
| 0.2.0 | 2026-08-20 | 八席 Conditional Go 回写：**BLK-01** 命名改 `edition`/`portfolio_*`；**BLK-02** 取消 `layoutEngine` 第三值；**BLK-03** 溢出升档 + 明示（§8.5）；**BLK-04** V1 正文纯图；**BLK-05** 主产物并列两件 + 成功面动作；**BLK-06** 文案迁移与锁；**BLK-07** OR 旁路；**BLK-08** 资产硬门 + 顶岗纪律 + 估时上调；**BLK-09** items 同源。OQ-02 否决、OQ-06 改判，OQ-07～09 补答。SHD-01～08 收入。新增 AC-PFM-27～40、ISO-07。 |
| 0.2.0 | 2026-08-21 | 状态回写：ISO-04/06 已关；AS-PFM-03 工坊对账完成（`folio-24` 已是 24 页，不升格）；W4 狗粮协议与盲评三问已锁，人评未开，`homepage_entry` 仍关。 |
| 0.2.1 | 2026-08-21 | AS-PFM-03 后继：MSP 五档入库（8/12/16/20/28）。原对账纪要不改。 |
| 0.2.2 | 2026-08-26 | **SHD-PIS-06**：文首挂 [PIS](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md) 后继。FE-PFM-11 游记票根空串改判见 AMD-PIS-01；选脸按星见 AMD-PIS-03。 |
