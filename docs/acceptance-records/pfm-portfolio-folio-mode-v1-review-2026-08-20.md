# PRD-PORTFOLIO-FOLIO-MODE-V1 · 七席 + 典型用户评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](../PRD-PORTFOLIO-FOLIO-MODE-V1.md)（**PFM** · 作品集成册管线 / 双管线）**v0.2.0**（BLK-PFM-01～09 已回写） |
| **线框** | [portfolio-folio-mode-v1-wireframe.html](../wireframes/portfolio-folio-mode-v1-wireframe.html) **v1.1**（**F0–F8 已签** · 产品 2026-08-20 重签 F1/F3/F6） |
| **讨论底稿** | [画册编排.md](../画册编排.md) · [临时模板库管线讨论备忘录 §4](../templates/reserve/临时模板库管线讨论备忘录.md) · [智能模板建议0813.md](../智能模板建议0813.md) |
| **相邻挡门** | [TSU](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) · [TDV](../PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md) · [RSC](../PRD-RESERVE-SERIES-CABINET-V1.md) · [EDC](../PRD-EDITORIAL-COMPILER-V1.md) · [LVP](../PRD-LAYOUT-VIBE-PICKER-V1.md) · [ECC](../PRD-EXPORT-CARD-COMPOSE-V1.md) · [OR](../PRD-OUTPUT-RECIPE-V1.md) · [IW v3](../PRD-IMPORT-SHEET-v3-WIZARD.md) · [ADR-003](../adr/003-experience-reading-modes.md) · [ADR-021](../adr/021-export-compose-dual-engine.md) |
| **日期** | 2026-08-20 |
| **结论** | **有条件通过（Conditional Go）**。切口成立，双管线主线可冻结。**BLK-PFM-01～09 回写 v0.2.0 前：不批无条件 Go · 不批 W1 匹配器合码 · 不批 W3 前端拆单**。线框 F0/F2/F4/F7/F8 可签；**F1/F3/F6 须改后重签**；F5 有条件签。 |
| **编码** | ☑ 策划回写 v0.2（BLK-PFM-01～09）　☑ W0 命名/schema/flag　☐ W1 匹配器　☐ W2 渲染 + 导出　☐ W3 界面　☐ W4 狗粮盲评 |
| **参评角色** | **七席**：产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测）· **加席**：典型用户（非从业者 · 一次旅行拍 180 张 · 现网只用过「选夹→开始→发群」） |
| **评审方式** | 分席只读 PRD v0.1.0 §0～§16 + 线框 F0–F8，对照现网代码事实（`services/layout.py` 引擎白名单、`render/surface.py`、`export/platform_profiles.py`、`curation/folio_plan.py`、`render/reading_profile.py`、`docs/templates/reserve/*/packet.yaml`）与相邻合同（TSU v1.1.0、TDV v0.2.0 现场） |
| **记录人** | 八席联合纪要（跨职能模拟联评 · 2026-08-20） |
| **本纪要状态** | **已结案 · Conditional Go** · **Must-Fix 已回写 PRD v0.2.0**（核对见 §4 表后） |
| **审查基线** | 默认零步不动 · 游记 GA 逐字不改 · 不接 `album_spread` · 不打开 MSA · 引擎不读工坊 · **不把未升格的系列写成已具备** · **不把顶岗预演说成作品集** · **加席否决权与产品同等：合同若让普通用户拿到一堆不知道往哪发的 PNG，算没写完** |

---

## 0. 会前宣读（主持人）

1. **切口**：现网会「出游记、发长图」，工坊会「手编一本 16:9」，中间缺运行时那一段。PRD 选的是：上游共用、装配分叉、导出换门面。方向本场不重开。
2. **已拍（勿重开）**：默认游记；不合成又快又精；分叉点在 `compose_trip` 之前；`page-*` 不接印刷跨页；引擎不读 `docs/templates/reserve/`；不做 C 端拖图器；不等 EDC 80%。
3. **勿重开**：重写 MCS/Curate、打开 MSA、把作品集设成默认、首页主 CTA 换人、第七个社交平台圆点。
4. **本场必拍**：命名会不会和现网四个 `folio` 撞车；`layoutEngine` 加第三个值要打穿多少护栏；作品集页数装不下的照片去哪；`page-*` 没有文案区意味着什么；16 张 16:9 PNG 到底是不是「成品」；切表面时用户改过的文字怎么办；六个开放问题逐条裁决。
5. **加席说明**：典型用户不是狗粮工程师。他不知道 `page-*`，不关心隔离，只会问三句——这跟上次做的有什么不一样、我会不会选错、做完发给谁。他说「看不懂」，就是 Must-Fix。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：主线立得住——两条活客观存在、上游共用装配分叉、默认仍是两击发群、作品集换主 CTA 不抢六平台，这比「再加一个导出平台」或「把杂志槽混进现网拼图」都更可验收、可关旗。但 v0.1.0 有九处按原文 Kickoff 会假绿、会打穿现网、或会把普通用户丢在半路：（1）`folio` 在现网已经是四个东西（阅读皮肤 `reading.scroll.folio`、`curation.folioPlan`、封面 `folio-overlap`、工坊禁用 id `folio-*`），`surface` 又是渲染层已占的词（`render/surface.py` 的 draft/share/longshot），术语表整条撞车；（2）`layoutEngine=folio` 会撞 `services/layout.py` 的 `legacy|screens` 硬校验和一串 `screens_layout_active` 护栏，而 folio 输出的本来就是同构 `screens[]`，新值收益低、爆破面大；（3）游记是全收照片，系列有 `photo_span` 上限——180 张钉 16 页时多出来的照片去哪，全文没写；（4）工坊 40+ 张页型包 `copyRegions` 几乎全是空数组，作品集 V1 事实上是「一个字都没有的一本」，PRD 却仍写 narrate 按章填槽；（5）主产物 16 张 16:9 PNG 没有真实分享出口，典型用户拿到只会绕回长图；（6）切表面时 `structure/copy` 锁与已改文案的迁移没写，用户会丢字；（7）Output Recipe 的 10–30 张意图卡会在作品集路径上乱弹；（8）正式 `series/` 目录路径仍是 TSU 未关的开放问题、附录 A 只有 6 张 `designed`，W1 用顶岗出门等于自称作品集；（9）folio 若丢照片，`items ↔ screens` 资产集合一致性门会红，手机端会出现网页上没有的照片。关 BLK 后升 v0.2；W0 可先做命名与 flag；W1 必须等 P0 正式系列真的进现网目录。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 两条活是真的，默认不动、次链弱、红线清楚，同意。但「作品集」的成品定义没闭合：用户做完拿到 16 张 PNG，我没法在成功面写出一句他会照做的话。页数装不下的照片必须有说法——现网是「你的精选都在里面」，作品集第一次会打破这个默契，不能靠不写来回避。 |
| **算法** | **Conditional Go** | 组先于脸、一页不跨组、密页要够张数、降级链四段，能执行，这是全文最扎实的一节。两点要钉：靠档只能减页不能改槽比，写进接口不能停在散文；`photo_span` 命中失败时是「换档」还是「丢照片」，是两种完全不同的算法，AC-PFM-12 只测了 18 页靠档，没测溢出。 |
| **架构** | **Conditional Go** | 分叉点选在 `compose_trip` 之前、匹配器独立包、import-linter 加边，对。反对两件事：一是 `layoutEngine` 加第三个值——现网 `services/layout.py` 直接 `raise E_LAYOUT_ENGINE`，`resolve_layout_engine` / `screens_layout_active` / 指纹 / 手机 items / 封面解析都按二值写的，而 folio 产出的仍是 `screens[]`，加值只为标身份不值当；二是 `surface` 这个词，渲染层已经用它表示 draft/share/longshot 面，再叠一层语义，日志和函数签名会看串。身份放 `trip.studio.edition` 一个字段就够。 |
| **开发** | **Conditional Go** | 任务表颗粒度可开工，`editorial_series` 新包边界干净。估时有两处明显偏低：BE-PFM-11「`page-*` YAML/CSS 入库 2.0 天」其实是 TSU W3 的活目录工作（附录 A 现在只有 6 张 `designed`），不是 PFM 两天能吞的；BE-PFM-13 页图 Writer 2.0 天要走 Playwright 逐屏截 + 原子写 + 单页失败继续，参照现网 longshot 分章截图的坑，按 3.5 天报。另外 `E_FOLIO_UNAVAILABLE` 这类 id 请跟命名一起改，别改两遍。 |
| **测试 / QA** | **Conditional Go** | ISO-01～06 可测，`render_fingerprint` 现成能用，很好。四条会假绿：AC-PFM-08 只断言 kept 集合与组边界一致，而 folio 明显会少上照片，这条按原文写会自相矛盾；`test_chapter_items_screens_sync` 是现网出门门（`verify-trip.ps1` 里就有），folio 丢照片会直接红，PRD 没提；AC-PFM-17「页数=screens 正数」不含单页失败跳过的口径；ISO-01 要求「允许压缩头差」太模糊，应改成指纹字段级比对。 |
| **视觉 / 排版** | **Conditional Go** | 16:9 一屏一页、密度带、组先于脸，与工坊试印一致，观感方向我签。但必须说穿：现在的页型包 `copyRegions` 基本是空的，作品集出来是纯图册。纯图册可以很好看，那是设计选择，不是遗漏——请在 PRD 里明写「V1 作品集不排文字」，否则设计侧会以为还有图注要留位，运营也会白编文案。封面封底沿用 CAL/ABE 我同意，但页图第一张若是全视窗 Opening，截成 16:9 要看一眼实样再签。 |
| **用户体验 · 狗粮** | **Conditional Go** | 表面分段放在快速/精细之上、不做第三张大卡、LVP 在作品集整组卸载，这三条是全文最重要的防缠死设计，我签。两处要改：精修切换的确认文案只说「精选和分组会保留」，没说文字会不会保留——用户改过标题和图注再切，丢了会炸；作品集导出面板里六平台若默认展开，等于把刚建立的「这不是发群路径」又拆了，请默认折叠。 |
| **典型用户（加席）** | **Conditional Go** | 我拍了 180 张，选了「作品集」。三个问题：第一，做完弹出来说「16 张页图已保存」，我要拿它干嘛？发微信是竖的，发小红书是方的，16 张图我一张张发朋友会疯。我要么想要一个能点开翻的东西，要么想要一张能直接发的。第二，我 180 张只上了 96 张，剩下 84 张呢？没人告诉我，我会以为软件坏了。第三，导入那一步问我要 8 页还是 24 页——我根本没看过照片长什么样，你让我猜什么？页数这种事，等我看到成品再改。另外「作品集」和「游记」我分得清，但「作品集」和导出里那个「印刷跨页（现网画册）」我分不清，最好别在同一个菜单里同时出现两种「书」。 |

**汇总**：**8/8 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批 W1 匹配器合码** · **不批 W3 前端拆单** · **不批首页次链露出**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 两条活是真需求；分叉点选得准 |
| 与现网能力对齐 / 防假绿 | **4** | 引擎第三值、命名撞车、溢出与文案区三处与代码事实不符 |
| 与 TSU / TDV / LVP / ECC 边界 | **8** | 所有权表写得清楚，红线可执行 |
| 隔离可验收性 | **8** | ISO-01～06 + 指纹现成，是全文最强项 |
| 工程可开工性 | **6** | 包边界清晰；两项估时偏低；资产前置未落地 |
| AC 可测性 | **6** | 隔离类好；装配类（溢出、items 同步、失败页）有洞 |
| 普通用户可完成一次 | **4** | 成品定义未闭合；溢出不告知；导入问页数 |

---

## 3. 事实核查（对照现网代码 · 影响结论）

| # | PRD v0.1.0 假设 | 代码 / 合同事实（2026-08-20） | 会中 |
|---|-----------------|------------------------------|------|
| **F-01** | `folio` 是本主题新词 | 现网已四处占用：`reading.scroll.folio`（lite/full 阅读皮肤）、`curation.folioPlan`（精选格）、封面样式 `folio-overlap`、渲染 `folioLite`/`folioPageLabel`；工坊系列 id 前缀 `folio-*` 还被本 PRD 自己列为**禁止的运行时 id** | **命名撞车 · BLK-01** |
| **F-02** | `trip.studio.surface` 是新字段名 | `travelogue/render/surface.py` 的 `SurfaceContext` / `resolve_surface_context` 已用 surface 表示渲染面（draft / share / present / longshot），含 `is_longshot_surface`、`layout_engine` | **同词双义 · BLK-01** |
| **F-03** | `layoutEngine` 枚举加 `folio` 即可 | `services/layout.py:111` 硬校验 `engine not in (LEGACY, SCREENS) → raise E_LAYOUT_ENGINE`；另有 `resolve_layout_engine`、`screens_layout_active`、`render_fingerprint`、手机 `chapter_items`、封面解析等按二值分支 | **爆破面大 · BLK-02**。folio 输出同构 `screens[]`，新值收益低 |
| **F-04** | folio 只是少上几张，kept 集合与 journal 一致（AC-PFM-08） | 现网 journal **全收**：`apply_layout_to_trip` 用全部 body assets 建屏。系列 `photo_span` 有上限，180 张 × 16 页必然溢出 | **溢出策略缺失 · BLK-03**。AC-PFM-08 按原文自相矛盾 |
| **F-05** | narrate 仍按章填槽（D-PFM-14） | 工坊 40+ 张 `page-*` 数据包中 `copyRegions: []` 是压倒性多数，仅 `page-1-hero-port`、`page-2-pair-land` 两张有区 | **作品集 V1 近乎无字 · BLK-04**。必须明写，不能默认 |
| **F-06** | 页图 = 主产物，用户「按页发朋友或交印刷」 | 六平台画布均为竖/方（`platform_profiles`）；16:9 无社交出口。现网可分享物是长图与 zip | **成品未闭合 · BLK-05**（加席主诉） |
| **F-07** | 切表面「只重装配 + 渲染」 | 现网有 `pipeline_state` 阶段锁与 structure/copy locked 语义；用户已改的槽级文案在新版式里槽位不存在 | **文案迁移未定 · BLK-06** |
| **F-08** | folio 默认 recipe = `folio_pages` | Output Recipe 按 kept N 分带，10–30 张为 Ambiguous 需显式意图卡 | **意图卡会误弹 · BLK-07** |
| **F-09** | 前置「TSU 交出可跑正式系列」 | TSU §5.1 A1–A7 / B7 仍 ☐；正式 `series/` 收件目录是 TDV OQ-03 **未关**；附录 A 仅 6 张 `designed`；工坊 `folio-24-standard` 的 id 与 `pageCount: 32` 仍不一致 | **W1 无开工条件 · BLK-08**。顶岗不得对外称作品集 |
| **F-10** | 手机端出「游记式降级 items」（D-PFM-04） | `test_chapter_items_screens_sync` 是现网出门门（`scripts/verify-trip.ps1` 直接跑）；items 与 screens 资产集合须一致 | **丢照片即红灯 · BLK-09** |
| **F-11** | `reading.profile=magazine` 可用 | `render/reading_profile.py` 枚举含 `magazine`，有独立档位 | **属实 · 保持**。仅需确认与 folio 密页组合的性能告警（`curate.py` 已有 cinematic+folio full 的 WARN 逻辑可参照） |
| **F-12** | 新平台 id 接入面 = 一个 Writer | `KNOWN_PLATFORM_IDS` / `PLATFORM_SEGMENT_IDS` / `COMPOSE_PLATFORM_IDS` / `PHASE_A_PLATFORMS` / `PHASE_C_CLI_ONLY` 五张表 + Studio 白名单 + 批量多选面板 | **接入面比 PRD 写的宽** · SHD-01 |
| **F-13** | 引擎不读 `docs/templates/reserve/` | 与 TDV F-02 一致，现网无业务读取 | **属实 · 保持**。ISO-05 沿用 TDV AC-07 检索范围 |
| **F-14** | 不接 `album_spread`、不打开 MSA、不重写 MCS | 与 ADR-021 / TSU D-U-09 / 备忘录双管线一致 | **属实 · 保持** |

---

## 4. Must-Fix（回写 v0.2 前不批无条件 Go · 不批 W1 合码）

| ID | 挡哪一波 | 要求 |
|----|----------|------|
| **BLK-PFM-01** | W0 命名 | **术语整体改名，一次改干净。** 表面字段 `trip.studio.surface` → **`trip.studio.edition`**（值 `journal` \| `portfolio`）；平台 id `folio_pages` → **`portfolio_pages`**；配置 `studio.folio_pipeline` → `studio.portfolio_pipeline`；`studio.folio.*` → `studio.portfolio.*`；错误码 `E_FOLIO_UNAVAILABLE` → `E_PORTFOLIO_UNAVAILABLE`。理由见 F-01/F-02：`folio` 现网已有四义、`surface` 是渲染层已占词。C 端用词「作品集」不变；包名 `editorial_series` 保留。§0.1 术语表、§7、§12 任务表、§14 AC 同步。 |
| **BLK-PFM-02** | W1 引擎 | **不新增 `layoutEngine` 第三值。** 作品集产出的是同构 `chapters[].screens[]`，身份由 `studio.edition` 单独承担，`layoutEngine` 保持 `screens`，`layoutEngineVersion` 照写。D-PFM-04 与 §7.1/§7.3 重写。若策划坚持新值，则必须在 PRD 附一张**护栏清单**逐条列出并改：`services/layout.py` 白名单、`resolve_layout_engine`、`screens_layout_active`、`render_fingerprint`、`chapter_items`、封面解析、replan 入口，且 W1 出门须带全量回归——本席建议不走这条。 |
| **BLK-PFM-03** | W1 装配 / 产品 | **拍板照片溢出策略，并写进 UI。** kept 数超过命中系列 `photo_span` 上限时，三选一并写死：(a) 自动升档到能装下的最大档（≤32 页）后仍溢出才丢；(b) 丢弃并在预览与成功面明示「本册收录 96 / 180 张」+ 一键「改用游记（全收）」；(c) 硬拒并建议游记。评审倾向 **(a) 兜底 + (b) 告知**，禁止静默丢弃。AC-PFM-08 改写（kept 集合允许子集，但须等于 `screens` 实收集合），新增 AC 断言溢出提示存在。 |
| **BLK-PFM-04** | W0 产品 / W2 渲染 | **明写作品集 V1 的文字策略。** 事实是 `page-*` 数据包 `copyRegions` 几乎全空（F-05）。请在 §9 写死：V1 作品集**为纯图编排**，仅封面/封底保留书名与地点（CAL/ABE 现网能力），正文页不排图注与章导语；对应地 narrate 阶段在作品集路径**不落文案槽**（可跳过或只产书名素材），UI 与等待态不得暗示「正在写文案」。若产品要保留文字，则须先在 TSU 侧给出带 `copyRegions` 的页型，属另一波。 |
| **BLK-PFM-05** | W2 导出 / 成功面 | **闭合「作品集的成品是什么」。** 只交 16 张 16:9 PNG 不构成可分享成品（F-06、加席主诉）。V1 主产物改为**并列两件**：① 可翻阅的一本（`portfolio_pages` 页图 + `index.html` 打包 zip，能本地点开翻页/投屏）；② 页图序列本身。Dock 主钮与成功面须给出一个用户会照做的动作（打开这一本 / 发送这份压缩包），不得只写「打开文件夹」。「换种分享」保留为拿社交图的次级路径。F3 帧据此重画。 |
| **BLK-PFM-06** | W3 切换 | **切表面必须处理锁与文案。** §5.4 确认模态补一句实话：「你手动改过的文字可能无法全部保留」；后端定义迁移规则（按 assetId / 章序尽力回填，回填不上的落到 trip 级草稿而不是直接丢），并写明与 `pipeline_state` structure/copy 锁的交互（哪些锁会被解除、解除前是否再问一次）。AC-PFM-20 扩测「改过文案后切换」的路径。 |
| **BLK-PFM-07** | W2 / W3 | **Output Recipe 旁路写死。** `edition=portfolio` 时不进入按 kept N 分带的意图卡逻辑（10–30 张 Ambiguous 带），默认直接 `portfolio_pages`；journal 路径逐字不变。§6.1 与 OR 合同各加一行，配 AC 断言「作品集路径不弹意图卡」。 |
| **BLK-PFM-08** | W1 出门 | **资产前置写成硬门，且不吸收 TSU 的活。** W1 出门须满足：正式 `series/` 收件目录已定（TDV OQ-03 关闭）+ P0 `magazine-16-standard` 已入现网目录 + 升格检查单拒过 id/页数不一致（F-09）。在此之前 W1 只能内部预演，**任何界面与文档不得称「作品集」**，只能写「版式试验」。BE-PFM-11 中 `page-*` 活目录入库明确划归 **TSU W3**，PFM 只消费；BE-PFM-11 / BE-PFM-13 估时按开发席意见上调（页图 Writer ≥3.5 天）。 |
| **BLK-PFM-09** | W1 / W2 | **`items ↔ screens` 一致性给出方案。** 现网门 `test_chapter_items_screens_sync` 要求章内资产集合一致（F-10）。作品集若少上照片，手机降级 items 必须与 `screens` 实收集合同源（不得用全 kept 池），或显式豁免并改测试口径——二选一写进 §9 与 AC，禁止留到实施时发现红灯再拍。 |

**v0.2.0 回写核对（2026-08-20）**

| ID | 落点 | 状态 |
|----|------|------|
| BLK-01 | D-PFM-01 · §0.1 禁用表 · §7 · §12 任务表全量改名 | 已关 |
| BLK-02 | D-PFM-04 · N-PFM-12 · §7.1/§7.3 · ISO-07 · AC-PFM-27 | 已关 |
| BLK-03 | D-PFM-21 · §8.5 · AC-PFM-29/30 · 线框 F3c | 已关 |
| BLK-04 | D-PFM-22 · N-PFM-13 · §9 · AC-PFM-32/33 | 已关 |
| BLK-05 | D-PFM-23 · §6.1/§6.2 · AC-PFM-37/38 · 线框 F3a/F3b | 已关 |
| BLK-06 | D-PFM-24 · §5.4 · AC-PFM-20/39 · 线框 F6b | 已关 |
| BLK-07 | D-PFM-25 · §6.1 · AC-PFM-19 | 已关 |
| BLK-08 | D-PFM-26 · 前置条件 · AS-PFM-01/02 · BE-PFM-11/13 估时 | 已关 |
| BLK-09 | D-PFM-27 · BE-PFM-22 · AC-PFM-31 | 已关 |

SHD-01～08 一并收进 v0.2（平台接入面、游记不写字段 + 指纹字段级、CLI 硬要求、阈值派生、CHARTER 一行、折叠 + 印刷副文、盲评法、`magazine` 性能 WARN）。

**回写后允许**：W0 命名 / schema / flag 开工。仍禁止：W1 在 AS-PFM-01 未满足时出门；W3 在 F1/F3/F6 重签前拆单；任何界面在正式系列到位前称「作品集」。

---

## 5. Should-Fix（不挡文档 Kickoff）

| ID | 说明 |
|----|------|
| **SHD-PFM-01** | 新平台接入面比 PRD 写的宽（F-12）：请补 `portfolio_pages` 在 `KNOWN_PLATFORM_IDS` / Studio 白名单 / 批量多选面板 / CLI 各处的取舍，尤其**是否进批量多选**（评审倾向不进，避免与社交批量混）。 |
| **SHD-PFM-02** | journal trip **不写** `studio.edition` 字段（缺省即游记），避免快照与指纹产生无谓 diff；ISO-01 用 `render_fingerprint` 做字段级比对，替换「允许压缩头差」这种模糊表述。 |
| **SHD-PFM-03** | CLI 缺省仍 `wechat_chat` + WARN 会让脚本默默产出错东西：改为作品集 trip 未传 `--platform` 时**硬要求显式**，或缺省即 `portfolio_pages`。 |
| **SHD-PFM-04** | `min_kept_for_folio: 12` 与系列 `photo_span` 下限是两个真相：阈值应由系列库最小 `photo_span` 派生，配置只做覆盖。 |
| **SHD-PFM-05** | CHARTER 补一行第二产品形态（作品集），否则对外定位会漂；同时明确它不改章程主叙事。 |
| **SHD-PFM-06** | 加席反馈：导出菜单里「作品集页图」与「印刷跨页（现网画册）」同屏易混。建议「换种分享」默认折叠，且印刷项副文写「给印刷公司的 3:4 跨页，不是这一本」。 |
| **SHD-PFM-07** | W4 盲评沿用 CAL / ALG 的盲评法（成对、隐藏来源、固定评分表），「像一本」需给出可打分的三问，不要停在主观描述。 |
| **SHD-PFM-08** | `reading.profile=magazine` 与密页组合的性能告警参照 `curate.py` 现有 cinematic+folio full 的 WARN 写法，避免大 trip 卡顿无提示。 |

---

## 6. 线框逐帧结论

| 帧 | 表决 | 处置 |
|----|------|------|
| **F0 地图** | **同意** | 隔离模型、三轴对照可签。改名后同步文字（BLK-01） |
| **F1 导入分段** | **改后重签** | 分段位置与默认游记同意；**撤掉 F1c 的页数芯片**（OQ-02 否决）；作品集副文补一句成品是什么 |
| **F2 首页次链** | **同意（带门）** | 保持弱链 + 父开关；**W2 换真 `page-*` 前不露**，与 R-PFM-01 一致 |
| **F3 作品集 Dock** | **改后重签** | 主钮与成功面按 BLK-05 重画：给出「打开这一本 / 发这份压缩包」的动作，不止「打开文件夹」 |
| **F4 游记对照** | **同意** | 零变化帧是回归基准，保留 |
| **F5 换种分享** | **有条件同意** | 维持分组降级；**默认折叠**；印刷项副文按 SHD-06 改 |
| **F6 精修切换** | **改后重签** | 确认模态补「文字可能无法全部保留」（BLK-06）；页数芯片留在此处（这是唯一合适的位置） |
| **F7 书架弱标** | **同意** | 弱标 + ⋯ 菜单改表面，走同一确认 |
| **F8 红线** | **同意 · 加两条** | 新增：**不得在无正式系列时对外称「作品集」**（BLK-08）；**不得静默丢照片**（BLK-03） |

签核规则维持 PRD §11：F0 过才 Kickoff W1，F1/F3/F5/F6/F8 过才 Kickoff W3。本场结果：**W1 的线框门已过（F0），但被 BLK-08 资产门挡住**；**W3 未过门**（F1/F3/F6 待重签）。

---

## 7. 六个开放问题 · 裁决

| ID | 问题 | 草案 | **裁决** | 理由 |
|----|------|------|----------|------|
| **OQ-PFM-01** | 首页要不要次链？ | 要，弱、可关 | **维持 · 加门** | 弱链不抢主 CTA，成立。但绑 W2：真 `page-*` 未入库前 `homepage_entry` 保持 false，否则用户点进去看到的是游记顶岗 |
| **OQ-PFM-02** | 导入精细 2b 露页数芯片？ | 要 | **否决** | 加席原话：还没看过照片就让我猜页数。导入一律 `auto`，页数只在精修改（F6 已有位置）。同时省掉 FE-PFM-02 的一半和一条 AC |
| **OQ-PFM-03** | 换种分享列全部六平台？ | 列出，分组降级 | **维持 · 加约束** | 保留六平台，但**默认折叠**、分组标题「用同一批照片出社交图」、印刷项副文区分（SHD-06）。仍禁止第七个平铺圆点 |
| **OQ-PFM-04** | 允许作品集改回游记？ | 允许 | **维持 · 绑 BLK-06** | 允许是对的（也是溢出与失败的兜底出口），但文案迁移规则未定前不得实施 |
| **OQ-PFM-05** | 页图含封面封底？ | 算 | **维持 · 加验样** | 与预览一致更好解释。但视觉席要求：全视窗 Opening 截成 16:9 的实样须在 W2 看一眼再定；封底无内容时不硬造空页 |
| **OQ-PFM-06** | kept<12 允许作品集？ | 弱提示可继续 | **改** | 弱提示不足：12 张排 8 页会出空翻。改为**默认置灰 + 一句「照片较少，作品集更适合 30 张以上」+ 可知情继续**；阈值由系列库最小 `photo_span` 派生（SHD-04），不写死 12 |

**新增开放问题（本场提出，回写时须带答案）**

| ID | 问题 | 会中倾向 |
|----|------|----------|
| **OQ-PFM-07** | 照片装不下时：升档 / 告知丢弃 / 硬拒？ | 升档兜底 + 明示实收（BLK-03） |
| **OQ-PFM-08** | 作品集成品形态：页图序列 / 可翻阅 zip / 两者并列？ | 并列，且成功面主动作指向「这一本」（BLK-05） |
| **OQ-PFM-09** | 作品集 V1 是否完全无正文文字？ | 是，纯图编排，明写（BLK-04） |

---

## 8. 本场关闭 / 保持

| 项 | 处置 |
|----|------|
| D-PFM-01 双表面 | **改** · 字段与取值按 BLK-01 改名 |
| D-PFM-04 `layoutEngine=folio` | **改** · 按 BLK-02 取消第三值 |
| D-PFM-13 页数档位 | **改** · 导入不出芯片（OQ-02）；档位只在精修 |
| D-PFM-14 章保留 / narrate 填槽 | **改** · 按 BLK-04 明确正文不排文字 |
| D-PFM-02/03/05/06/08/10/11/12/15/16/17/18/20 | **保持** |
| D-PFM-07 精修切换 | **保持 · 硬化** · BLK-06 |
| D-PFM-09 主导出 | **保持方向 · 扩产物** · BLK-05 |
| D-PFM-19 阅读 profile | **保持** · `magazine` 现网已有（F-11） |
| ISO-01～06 | **保持** · ISO-01 按 SHD-02 改成指纹字段级 |
| N-PFM-01～11 全部非目标 | **保持** · 本场无人要求重开 |
| 不重写 MCS / 不打开 MSA / 不接 `album_spread` / 不读工坊 | **保持** |
| 加席典型用户 | **本场关闭**：主诉已写入 BLK-03 / 05 与 OQ-02 裁决 |

本场 **不勾** TSU A1–A7 / B7，**不关** TDV OQ-03（正式收件目录）。PFM 的 W1 反过来被这两项挡着。

---

## 9. 出门顺序（回写后）

```
v0.2 回写 BLK-PFM-01～09（命名 · 取消引擎第三值 · 溢出 · 无文字 · 成品 · 文案迁移 · OR 旁路 · 资产门 · items 同步）
  → 线框改 F1 / F3 / F6，重签
  → W0：edition 字段 + 父开关 + schema（不动 layoutEngine 枚举）
  → 等 TDV OQ-03 收件目录 + P0 magazine-16-standard 入库（BLK-08）
  → W1：匹配器 + curate 分支 + 溢出策略 + 关旗回退（顶岗只许内部说「版式试验」）
  → W2：page-* 渲染（TSU 供货）+ portfolio_pages + 可翻阅 zip + 隔离回归
  → W3：Wizard / Dock / 精修 / 书架（线框重签后才拆）
  → W4：狗粮三册盲评，再决定首页次链是否露出
```

W1 与 TSU 的资产波次**并行推进但不互相顶替**：PFM 不得替 TSU 画脸，TSU 也不因 PFM 预演而勾 B7。

---

## 10. 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-08-20 | 首场七席 + 典型用户加席。8/8 Conditional Go。BLK-PFM-01～09；六个开放问题裁决（OQ-02 否决、OQ-06 改判），新增 OQ-07～09。PRD 仍为 v0.1.0，待回写 v0.2.0。 |
| 1.1 | 2026-08-20 | 策划回写：PRD 升 v0.2.0（BLK-PFM-01～09 全关 + SHD-01～08 收入）；线框升 v1.1（F1 撤页数芯片 + 置灰态、F3 导出作品集 + 成功面 + 溢出明示、F6 文字迁移告知、F5 默认折叠、F8 加三条红线）。**F1/F3/F6 待产品重签**。 |
| 1.2 | 2026-08-20 | 产品重签 F1/F3/F6。W0 开工：`feat/pfm-portfolio-folio-mode-v1`。 |
