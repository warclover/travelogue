# Travelogue · 成品账本与票根副券 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.1.4**（帧 A/B **产品已签** · **M1–M3 已落地** · 发布默认开旗） |
| **状态** | **有条件通过（Conditional Go）** · 八席 8/8 · **BLK-OLT-01～07 已回写** · **M1–M3 已落地** · **M4 狗粮未开** · 不批无条件 Go（挡 M4 狗粮） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「成品账本与票根」— **OLT**（Output Ledger & Ticket） |
| **界面用词** | **成品** · **长图 / 朋友圈 / 小红书 / 公众号 / 海报 / 画册 / 作品集页图 / 分享包 / PDF** · **有更新** · **重新导出** · **在文件夹中显示**。禁止对 C 端说 output / surface / ledger / 指纹 / fingerprint / stale / revision / profile / batchId / outputId / 账本。**禁止**用「更新版面」（PFO 禁令延续） |
| **文档类型** | **数据结构 + 前端票面**合同。零管线改动、零 `trip.json` schema 改动、零装配改动 |
| **触发来源** | 2026-08-26 [架构重构交流备忘录](./架构重构交流备忘录.md) §5：产品提出「一套作品保存多种导出模式、通过票根标识」；架构评估确认这是现网真缺口，且是 stale 误报的根因（无产物实体记录来源快照） |
| **评审** | [七席+典型用户 2026-08-26](./acceptance-records/olt-output-ledger-ticket-v1-review-2026-08-26.md) · **8/8 Conditional Go** · BLK-OLT-01～07 **已回写本文** · 加席两条否决（副券数字重犯 36/37 · 同卡双状态） |
| **前置条件** | [EOI](./PRD-EXPORT-OUTPUT-ISOLATION-V1.md) 导出目录隔离已 GA（`导出文件/`）· 六平台导出 GA（[ADR-021](./adr/021-export-compose-dual-engine.md)）· [DPI](./PRD-DUAL-PIPELINE-ISOLATION-V1.md) W0–W3 已合入 · [PIS](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md) 票根身份行已落地 |
| **线框** | [olt-output-ledger-ticket-v1-wireframe.html](./wireframes/olt-output-ledger-ticket-v1-wireframe.html) **帧 A/B 已签 2026-08-26**（BLK-OLT-04）。§6.2 ASCII **不是**已签帧。签核：[olt-frame-ab-signoff-2026-08-26.md](./acceptance-records/olt-frame-ab-signoff-2026-08-26.md) |
| **关联文档** | [架构重构交流备忘录](./架构重构交流备忘录.md)（本文是其 W1）· [EOI](./PRD-EXPORT-OUTPUT-ISOLATION-V1.md)（产物落盘）· [PIS](./PRD-PORTFOLIO-IDENTITY-STARS-V1.md)（票根身份行 · 不得回退）· [PFO](./PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md)（stale 误报根因 · 导出点法）· [DPI](./dual-pipeline-ownership.md)（窄缝）· [OUTPUT-RECIPE](./PRD-OUTPUT-RECIPE-V1.md)（意图层，本文不改） |
| **验收** | 本文 **§12 为源** |
| **实施** | 本文 **§10 为源** |
| **更新日期** | 2026-08-26 |

> **定位**
>
> 现网导出产物**不是实体**：散在 `导出文件/` 里靠 glob 猜文件名前缀，`longshot-current.json` 只记最近一次，stale 只能靠 mtime 猜。书架因此做不到「一本书挂多份成品」，也一直在误报「需重做」。
>
> 本主题只做一件事：**给成品一本账本，给票根一排副券。** 不改管线、不改装配、不改选片、不改导出算法、不改 `trip.json` schema。
>
> **一句话目标**：同一本作品导出过长图、小红书、作品集页图之后，书架票根上就能看见这三张副券；点副券直达文件夹；内容改过的那一张标「有更新」，没改的不标；旧产物不再失联，误报不再发生。
>
> **产品铁律**
>
> 1. **成品是实体，不是文件名约定。** 账本是唯一索引，glob 只做兼容回退，M3 后退休。
> 2. **账本不进 `trip.json`。** 写 `trip.json` 会顶掉 `updatedAt`，让每次导出**当场把自己标成过期**（现网 `longshot_outputs_stale` 就是 `trip_mtime > latest_png`）。产物是派生物，账本与产物同层。
> 3. **过期判定比指纹，不比 mtime。** 只重渲染不改内容 → **不得**标「有更新」；换页型/换图/改文案 → **必须**标。
> 4. **一「产物身份」一条活跃记录。** 产物身份 = `outputId`，**不等于 profile**：`wechat_chat` 的整卷与分章是两个身份；`custom` 规格无穷因而不进账本（BLK-OLT-01）。账本反映磁盘现状，不做历史堆积（现网按轮 purge session 文件，账本必须跟着自愈）。
> 5. **票根是加一行，不是重画。** 主票面（封面 / 书名 / 身份行 / 装饰序号 / 花体码）**逐项不动**；副券行是新增的一行，零成品时不出现。
> 6. **副券不写数字。** 票根身份行已有唯一的「页」（PIS `AMD-PIS-05`）。副券只写渠道名；任何文件数 / 页数只进「管理成品」详情（BLK-OLT-02 · **加席否决**）。
> 7. **票根状态单一真相源。** 同一张卡不得同时出现「分享图已就绪」与「有更新」。既有徽章（`SFP D-SFP-09` 优先级合同）与副券状态必须同源，见 §6.7（BLK-OLT-04 · **加席否决**）。
> 8. **PIS 身份行不得回退。** 「游记」/「作品集 · X 页」仍在第一行。**身份 ≠ 成品**：身份是这本书是什么，副券是这本书出过什么。两个轴不得混写在一行。
> 9. **不碰装配与管线。** `mosaic/**`、`editorial_series/**`、`screen-*.yaml`、`page-*.yaml`、`curate.py`、`assemble.py`、`orchestrator/**` 本波零改。
> 10. **舞台字段只落不用。** `surface` 本波只做**分组展示**，禁止在其上加任何行为分支 —— Surface registry 归备忘录 W3。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0.2 | **编号约定**（避免与备忘录 W1–W4 撞号） |
| §0.4 | **v0.1.1 实施勘误**：八席 BLK 对照 v0.1.0 改了什么 |
| §1 | 现网缺口与用户可见症状 |
| §2 | 目标 / 非目标 / 成功标准 |
| §3 | 为什么账本不进 `trip.json`（关键设计决策） |
| §4 | 账本数据模型 |
| §5 | 四段指纹与「有更新」判定（§5.6 = 逐 profile 声明） |
| §6 | **票根副券设计**（票面 / 状态 / 文案 / 交互 / 无障碍）· **§6.7 = 状态单一真相源** |
| §7 | API 与配置 |
| §8 | 兼容与退役路径 |
| §9 | 所有权与接缝（DPI）· **§9.4 = 测试夹具策略** |
| §10 | 任务拆解（实施源） |
| §11 | 里程碑与编码门 |
| §12 | 验收 AC-OLT-* |
| §13 | 风险与开放问题 |

### 0.1 术语

| 术语 | 定义 | C 端说法 |
|------|------|---------|
| **成品（Output）** | 一次成功导出产生的一组文件 + 其规格与来源快照 | 成品 |
| **账本（Ledger）** | `导出文件/outputs.json`，一个 trip 的全部活跃成品索引 | （不出现） |
| **profile** | 导出规格 id。平台取 `config/platform_profiles.yaml` 的键；非平台取 `share_zip` / `pdf` | （不出现） |
| **outputId（产物身份）** | 账本主键。**≠ profile**：`wechat_chat` 分 `wechat_chat:whole` / `wechat_chat:chapter`；`custom` 不进账本（§4.3 · BLK-OLT-01） | （不出现） |
| **surface（舞台）** | 成品的画布族。本波取值 `scroll` / `card` / `grid` / `spread` / `folio` / `bundle`，**仅用于分组展示** | （不出现） |
| **四段指纹** | `structureFp`（结构）/ `copyFp`（文案）/ `bundleFp`（读者面字节）/ `optionsFp`（渲染选项，按 profile 声明键集）四个短哈希 | （不出现） |
| **有更新** | 成品记录的指纹与当前 trip 不符 | 有更新 |
| **副券** | 票根下方一排成品小条，每条一个成品 | （无词，直接是「长图」「小红书」等） |
| **主票面** | 票根现有部分：封面、书名、身份行、装饰序号、花体码 | （不出现） |

### 0.2 编号约定（重要）

[架构重构交流备忘录](./架构重构交流备忘录.md) 用 **W1–W4** 指四个架构波次，**本文整体 = 其中的 W1**。

为避免与 PIS §0.3 同类的撞号事故，**本文内部里程碑改称 M1 / M2 / M3**，任务前缀 `BE-OLT-* / FE-OLT-* / QA-OLT-* / DOC-OLT-*`，改判 `AMD-OLT-*`，Must-Fix 留给评审后的 `BLK-OLT-*`。**本文不出现 W 编号。**

### 0.3 与相邻主题

| 主题 | 仍归谁 | 本文接管 |
|------|--------|---------|
| 产物落盘目录、不迁移不清理 | **EOI** | 只在同目录加一个 `outputs.json` |
| 导出算法、切分、画布、双引擎 | **ADR-021 / ECC / LONGSHOT-2.0** | 零改，只在成功后追加账本 |
| 导出点法、面板显隐、成功面文案 | **PFO / PIS / 导出门面** | 零改。副券只在**书架票根**上 |
| 意图 → 平台映射 | **OUTPUT-RECIPE** | 零改 |
| 票根身份行、装饰序号 | **PIS** | 不动；只在其下加一行 |
| 舞台注册表、模板族一等字段 | **备忘录 W3** | 只落 `surface` 字符串，不建 registry |
| 身份值对象化 | **备忘录 W2** | 账本记 `edition` 快照，不改 `edition` 类型 |

### 0.4 v0.1.1 实施勘误（八席 Must-Fix 回写）

[评审纪要 2026-08-26](./acceptance-records/olt-output-ledger-ticket-v1-review-2026-08-26.md) 判 **8/8 Conditional Go**，七条 Must-Fix 已全部回写。**实施以本表为准，v0.1.0 原文对应段落作废。**

| ID | v0.1.0 原文（作废） | v0.1.1 结论 | 落在 |
|----|--------------------|-------------|------|
| **BLK-OLT-01** | `outputId = profile` | **`outputId` ≠ profile。** `custom`（CLI-only · `--width/--height` 可产任意规格）**不进账本**；`wechat_chat`（`capture: chapter_or_full`）显式分 `:whole` / `:chapter` 两个身份。否则后导的会**静默吃掉**前一份 | 铁律 4 · §4.3 · §4.4 |
| **BLK-OLT-02** | 副券 = `label` + `fileCount` | **副券只写 `label`，不写任何数字。** 票根身份行已有唯一的「页」（PIS `AMD-PIS-05` / `AC-PIS-10`），副券写 33 紧挨身份行 32 即重现 36 vs 37。数字只进「管理成品」详情。**加席否决** | 铁律 6 · §6.2 · §6.3 · §6.4 · AC-OLT-15 |
| **BLK-OLT-03** | 读账本时逐条 `stat` 每个文件 | **一次 `os.scandir` 取文件名集合再集合比对。** `SHELF_PAGE_SIZE=20` × 3 成品 × `portfolio_pages.max_pages=48` ≈ **2880 次 `stat()`**／次书架加载，比现网 glob 更慢。`R-OLT-06`「净开销应下降」论断**作废**，改为实测门 `AC-OLT-25` | §4.5 · §13.1 · AC-OLT-25 |
| **BLK-OLT-04** | 副券自带状态，未提既有徽章 | **票根状态必须单一真相源。** 现网已有 `SFP D-SFP-09` 徽章优先级合同（`分享图已就绪` / `分享图需更新` / `可重排` / `可先预览` / `正在准备高清图`），其源是 mtime 的 `trip.longshotStale`；副券用指纹后同卡会两种说法并存。本波必须收敛，**不接受并存、不接受后延**。**加席否决** | 铁律 7 · **§6.7（新增）** · AC-OLT-26 |
| **BLK-OLT-05** | `export` 选项（`copyDisplay`/`breathMode`/`longshotDensity`）进 `structureFp` | **移出 `structureFp`，改为第四段 `optionsFp`，投影键集由 profile 在 `stale_options` 声明。** 否则调一次长图密度会把作品集页图也标「有更新」—— 误报换姿势回来 | §5.2 · §5.6 · QA-OLT-02 |
| **BLK-OLT-06** | `studio.output_ledger` 默认 `false` 到 M3 | **M1 合入后即在开发/狗粮配置开旗。** 否则 M2 前端在默认配置下无副券数据可渲染，M2 无可测对象、M4 狗粮走不了 | §7.2 · §11 |
| **BLK-OLT-07** | 未交代测试夹具归属 | **账本与指纹单测一律用 `trip.render_golden.json` 克隆 + 注入 `edition`。** 禁止读 `phase16-dogfood/**` 或 `editorial_series/**`（DPI 夹具合同），否则 `pipeline_isolation` 当场红 | **§9.4（新增）** · QA-OLT-01/02 |

**两处改判（非 BLK）**

| ID | 改判 | 理由 |
|----|------|------|
| **AMD-OLT-01** | `share_zip` / `pdf` **不上票根副券**，只进「管理成品」列表（原 OQ-OLT-05 倾向「上」） | 加席只关心图；可见上限 3 应留给图类成品 |
| **AMD-OLT-02** | `AC-OLT-08` 与 `AC-OLT-10` **合并**为一条，判据统一表述为「四段指纹投影内字段未变 → 全部 ready」，并列出「重渲染会动而投影不含」的字段清单 | 原两条判据重叠，实现会各自解释（OQ-OLT-09） |

---

## 1. 问题

### 1.1 现网 as-is 事实

| 事实 | 代码位置 |
|------|---------|
| 书架用 6+ 组 glob 模式猜产物（`*-xhs-*`、`*-moments-*`、`*-poster*`、`*-长图-*`、`*-ch*`…） | `studio_trips.py:_longshot_files()` · `_LONGSHOT_FILE_PATTERNS` |
| 权威清单只记**最近一次** job，且只记 `whole` / `segmented` 两种 kind | `export/longshot.py:write_longshot_current()` |
| 过期判定 = `trip_mtime > latest_png + 0.5` | `studio_trips.py:longshot_outputs_stale()` |
| 「在文件夹中显示」优先读清单首个文件，否则取最新匹配 | `studio_trips.py:longshot_reveal_rel_path()` |
| 票根装饰编号是 FNV-1a 哈希，**不承载任何身份** | `shelf-ticket-logic.js:stubSerial/stubCode` |
| 票根身份行只有一行，写「游记」/「作品集 · X 页」 | `portfolio-edition-logic.js:shelfEditionLine()` · PIS §5 |
| `trip.json` 只有 `export`（**选项**），无产物记录 | `schemas/trip.schema.json:$defs/exportOptions` |

### 1.2 缺口与用户会以为什么

| ID | 缺口 | 用户会以为 |
|----|------|-----------|
| **G-OLT-01** | 同一本导出过长图 + 小红书 + 作品集页图，书架只有一个笼统的「分享图已就绪」 | 只能存一种，导第二种会覆盖第一种 |
| **G-OLT-02** | 换了封面重渲染一次（内容没改），全部产物立刻被标过期 | 系统在瞎催我重做 |
| **G-OLT-03** | 真改了页型 / 换了图，但 trip.json 恰好未落盘，产物**不**标过期 | 导出的还是新的（其实是旧的） |
| **G-OLT-04** | 按轮 purge 后旧文件被删，glob 仍匹配到残留同前缀文件 | 「在文件夹中显示」打开的不是刚导的那份 |
| **G-OLT-05** | 加一种导出形态要加一条 glob；改一次文件名规则就失联 | —（工程侧缺口） |
| **G-OLT-06** | 产物没有规格记录，无法回答「这份小红书图是几比几、当时多少页」 | 无法复现、无法比对 |

### 1.3 明确不是本主题的问题

- 导出算法质量、切分点、画布留白（ADR-021 / ECC）
- 导出面板布局与点法（PFO / 导出门面）
- 成功面文案与页数口径（PIS §7）
- 磁盘占用清理、批量删除历史成品（本波只做单条删除，见 SHD-OLT-03）
- 云端 / 跨机同步

---

## 2. 目标 / 非目标 / 成功标准

### 2.1 目标

| ID | 目标 |
|----|------|
| **G-1** | 每次成功导出在 `导出文件/outputs.json` 追加/替换一条成品记录，含规格 + 文件清单 + 四段来源指纹 |
| **G-2** | 一个 trip 可同时持有多条成品记录，互不覆盖；**同一 `outputId`** 重导则替换该条 |
| **G-3** | 书架票根在主票面下新增一排副券，每条成品一张；零成品时票面与今天逐像素一致 |
| **G-4** | 点副券 = 打开该成品所在文件夹并选中其首个文件 |
| **G-5** | 「有更新」按四段指纹判定；**只重渲染不改内容不得触发** |
| **G-6** | 账本自愈：文件已不存在的记录在读取时被剔除，不展示、不报错 |
| **G-7** | 账本缺失（老 trip / 手动删）时回退到现网 glob + `longshot-current.json`，**不迁移、不清理**（EOI D-EOI-05 先例） |
| **G-8** | 票根状态只有一个真相源：既有徽章与副券状态同源，同卡不出现互相矛盾的两句话（§6.7） |

### 2.2 非目标

| 不做 | 原因 |
|------|------|
| 把 `outputs[]` 写进 `trip.json` | §3 · 会自造 stale |
| 建 Surface registry / 把 `surface` 变成行为分支 | 备忘录 W3 |
| 改 `edition` 类型为值对象 | 备忘录 W2 |
| 改任何导出算法、画布、切分 | 本波零导出行为改动 |
| 在预览页 Dock / 导出面板上展示副券 | 只进书架票根，控制面积 |
| 成品重命名、移动、跨 trip 复制 | 未立项 |
| 保留同 `outputId` 的历史多版本 | 铁律 4 · 磁盘已按轮 purge |
| 把 `custom` 平台纳入账本 | BLK-OLT-01 · Phase C · CLI-only · 规格无穷、`outputId` 无法稳定。若日后 `custom` 上 Studio，再补规格判别式 |
| 在副券上显示文件数 / 页数 / 字节 | 铁律 6 · BLK-OLT-02 · 加席否决。数字只进「管理成品」 |
| 把 `share_zip` / `pdf` 放上票根副券 | AMD-OLT-01 · 只进「管理成品」列表 |
| 云同步 / 分享链接 | 超范围 |
| 批量清理磁盘 | SHD-OLT-03 只做单条删除 |

### 2.3 成功标准

- 同一 trip 依次导出「微信群长图 → 小红书 → 作品集页图」后，`outputs.json` 有 3 条，票根有 3 张副券，**副券上无任何数字**。
- 再导一次小红书：仍是 3 条，小红书那条的 `createdAt` 与 `files` 被替换。
- 微信群先导整卷再导分章：账本 **4 条**（`wechat_chat:whole` 与 `wechat_chat:chapter` 并存，互不覆盖）。
- 只点「重新渲染」不改内容：3 张副券**均不**标「有更新」。
- 换一张封面图 / 改一处文案 / 换一个页型：对应副券标「有更新」。
- **只改长图密度**：长图副券标「有更新」，**作品集页图副券不标**（BLK-OLT-05）。
- 任一时刻，同一张卡上**不同时**出现「分享图已就绪」与「有更新」（铁律 7）。
- 手动删掉 `导出文件/` 里小红书的图：票根只剩 2 张副券，无报错、无 500。
- 删掉 `outputs.json`：票根退回现网表现（「分享图已就绪」徽章），无报错。
- 20 本书 × 3 成品的书架首屏，`GET /trips` 耗时**不劣于**改前（AC-OLT-25）。
- `pytest -m pipeline_isolation` 绿；`lint_dual_pipeline_ownership.py` 无新增边；`lint_trip_save_calls.py` 绿（本波不写 trip.json）。

---

## 3. 关键决策：账本不进 `trip.json`

### 3.1 决策

**账本落在 `导出文件/outputs.json`，与产物同层。`trip.json` 零改，schema 零改。**

### 3.2 理由

| ID | 理由 |
|----|------|
| **D-OLT-01** | **自造 stale。** 现网 `longshot_outputs_stale()` = `trip_mtime > latest_png + 0.5`。若导出成功后写 `trip.json`，`updatedAt` / 文件 mtime 立刻晚于刚生成的 png → **每次导出当场把自己标成过期**。这是最硬的一条 |
| **D-OLT-02** | **职责分层。** `trip.json` 是管线状态（输入 + 中间态，`draft_ingest → … → exported`）；成品是派生物。把派生物写进状态源会让「重跑管线」与「重导成品」耦合 |
| **D-OLT-03** | **删除语义一致。** 用户删 `导出文件/` 文件夹 = 删全部成品。账本同层则一起消失，不会留下指向空气的记录；写进 `trip.json` 则要额外写清理逻辑 |
| **D-OLT-04** | **写锁竞争。** `TripService` 是 CAS + 原子替换。导出 job 与 narrate / rerender / inline-edit 并发时会争锁；账本独立文件无此问题 |
| **D-OLT-05** | **约束成本。** 写 `trip.json` 要过 `lint_trip_save_calls.py`、`lint_trip_pipeline_mutations.py`、schema 校验、`trip.render_golden.json` golden 更新。本波可全部绕开 |
| **D-OLT-06** | **先例。** `longshot-current.json` 已按 EOI D-EOI-04 放在产物同层。账本是它的超集，位置一致 |

### 3.3 代价与接受理由

| 代价 | 接受理由 |
|------|---------|
| 账本不受 `trip.schema.json` 校验保护 | 自带 `schemaVersion` + 严格读取（校验失败即视为缺失，回退 glob），与 `read_longshot_current` 同款防御 |
| 备份 `trip.json` 不含成品记录 | 成品本身也不在备份里（是二进制产物），一致 |
| 跨机迁移带不走 | 现网产物同样带不走；且成品可重导 |

---

## 4. 账本数据模型

### 4.1 文件位置与并发

- 路径：`trips/<tripId>/导出文件/outputs.json`（`EXPORT_OUTPUT_DIRNAME` 内）
- 写：临时文件 + `os.replace` 原子替换（与 `write_longshot_current` 同款）
- 并发：**同一 trip 的导出 job 串行**（现网已是单 job 模型）。**硬前置**：导出 job 并行化之前**必须**先给账本追加加文件锁，否则并发 `append_output` 会丢条。这不是「以后再说」，是并行化那一版的准入条件（OQ-OLT-04 裁决）
- 失败即抛：账本写失败**不得**静默，导出不得在无账本时报成功（延续 QFX D-QFX-06b）。**例外**：`profile == "custom"` 时本就不写账本，不适用此条（§4.3.1）

### 4.2 Schema（v1）

```json
{
  "schemaVersion": 1,
  "updatedAt": "2026-08-26T03:11:07Z",
  "outputs": [
    {
      "outputId": "portfolio_pages",
      "profile": "portfolio_pages",
      "surface": "folio",
      "label": "作品集页图",
      "edition": "portfolio",
      "createdAt": "2026-08-26T03:11:07Z",
      "batchId": "lsb-7f3c1a",
      "spec": {
        "width": 1920,
        "height": 1080,
        "aspect": "16:9",
        "format": "png",
        "scale": 1
      },
      "files": ["珠海东澳-portfolio-01.png", "珠海东澳-portfolio-02.png"],
      "fileCount": 2,
      "bytes": 3420112,
      "source": {
        "structureFp": "st:9a1c4e77",
        "copyFp": "cp:2b60d1f4",
        "bundleFp": "lse16f41315f6a",
        "optionsFp": "op:5d8e0a31"
      },
      "staleInputs": ["structure", "copy", "bundle", "options"],
      "staleOptions": ["copyDisplay", "breathMode"]
    }
  ]
}
```

### 4.3 字段合同

| 字段 | 必填 | 说明 |
|------|------|------|
| `schemaVersion` | 是 | `1`。不等则整本视为缺失 → 回退 glob |
| `updatedAt` | 是 | 账本最后写入时间（ISO8601 Z） |
| `outputs[]` | 是 | 活跃成品。**同一 `outputId` 至多一条**（铁律 4） |
| `outputId` | 是 | **不等于 `profile`**，规则见 §4.3.1（BLK-OLT-01）。无需 uuid：一产物身份一条活跃记录，id 天然稳定、可用于删除与 reveal |
| `profile` | 是 | 平台键（`platform_profiles.yaml`）或 `share_zip` / `pdf`。**`custom` 不得出现**（§4.3.1） |
| `surface` | 是 | §4.4 枚举。**仅分组展示**（铁律 8） |
| `label` | 是 | **写入时从 `platform_profiles.yaml` 的 `label` 快照**。快照而非运行时查表：老记录保留历史称呼，前端无需重复维护一张中文表 |
| `edition` | 是 | 导出时的成册身份快照（`journal` / `portfolio`） |
| `createdAt` | 是 | 本次导出完成时间 |
| `batchId` | 否 | 沿用现网 job/批次 id，便于对日志 |
| `spec` | 是 | 画布规格快照：`width` / `height` / `aspect` / `format`；`scale`、`width_css` 视 profile 而定。**回答 G-OLT-06** |
| `files[]` | 是 | **裸文件名**（相对 `导出文件/`），与 `longshot-current.json` 同约定；禁止路径分隔符、`.`、`..` |
| `fileCount` | 是 | `len(files)`，冗余但便于前端不解析数组。**仅供「管理成品」与自愈用，禁止上票根副券**（铁律 6） |
| `bytes` | 否 | 文件总字节，供后续清理功能用。同样禁止上副券 |
| `source` | 是 | 四段指纹，见 §5 |
| `staleInputs[]` | 是 | 该 profile 声明消费哪几段指纹，取值 ⊂ `{structure, copy, bundle, options}`。**按 §5.6 表逐 profile 声明，不再一律全吃** |
| `staleOptions[]` | 条件 | `staleInputs` 含 `options` 时必填：参与 `optionsFp` 的 `trip.export` 键集（§5.6） |

#### 4.3.1 `outputId` 生成规则（BLK-OLT-01）

`outputId = profile` **不成立**，现网有两处会撞号并**静默覆盖**：

| 现网事实 | 后果 |
|---------|------|
| `platform_profiles.yaml:wechat_chat` 是 `capture: chapter_or_full`，naming `{title}-longshot` \| `{title}-ch{nn}` | 整卷与分章是**两种产物**，第二次导出会吃掉第一次的记录 |
| `cli/render_cmds.py`：`--width/--height` → `with_custom_output(profile,…)`，`custom` 规格任意 | 1080×1440 与 1080×1920 两份共用一个 `outputId`，账本静默丢数据 |

**规则**

| profile | `outputId` | 说明 |
|---------|-----------|------|
| `wechat_chat` | `wechat_chat:whole` / `wechat_chat:chapter` | 由本次导出的 `segment_mode` / 实际 naming 决定，二者**并存**，各占一条 |
| `custom` | —— | **不进账本**（本波 · `custom` 是 Phase C、CLI-only、不进 Studio UI）。导出照旧成功，只是不记账、票根无副券、回退 glob |
| 其余全部 | 等于 `profile` | 规格由 yaml 固定，id 天然稳定 |

`append_output()` 收到 `profile == "custom"` 时**直接返回、不抛异常、不写账本**（导出成功与否与账本无关，此处不适用 §4.1「失败即抛」）。若日后 `custom` 上 Studio，须补规格判别式（`custom:{w}x{h}`）并回本文重议。

### 4.4 surface 取值与 profile 映射

`surface` 在 `config/platform_profiles.yaml` 每个平台下新增一行（纯增量）；两个非平台产物在账本模块内建表。

| profile / outputId | surface | label（现有 / 新定义） | 上票根副券 |
|--------------------|---------|----------------------|-----------|
| `wechat_chat:whole` | `scroll` | 微信群 | 是 |
| `wechat_chat:chapter` | `scroll` | 微信群 · 分章 | 是 |
| `wechat_moments` | `scroll` | 朋友圈 | 是 |
| `instagram` | `scroll` | Instagram | 是 |
| `weibo` | `scroll` | 微博 | 是 |
| `douyin_cover` | `scroll` | 抖音封面 | 是 |
| `moments_grid` | `grid` | 朋友圈 · 九宫格 | 是 |
| `xiaohongshu` | `card` | 小红书 | 是 |
| `wechat_official` | `card` | 公众号 | 是 |
| `poster_bric` | `card` | 单张海报 | 是 |
| `album_spread` | `spread` | 画册印刷 | 是 |
| `portfolio_pages` | `folio` | 作品集页图 | 是 |
| `share_zip` | `bundle` | **分享包**（新定义） | **否**（AMD-OLT-01） |
| `pdf` | `bundle` | **PDF**（新定义） | **否**（AMD-OLT-01） |
| ~~`custom`~~ | —— | —— | **不进账本**（§4.3.1） |

`bundle` 舞台的两条**仍进账本、仍进「管理成品」列表**，只是不占票根副券的可见位（加席：可见上限 3 应留给图类）。

**禁止**在本波给 `surface` 加任何 `if` 分支（铁律 10）。它只进前端排序与分组，以及上表最后一列这一处静态映射。

`album_spread` 的 label「画册印刷」出现在作品集票根上**不违 PIS 铁律 3** —— `BLK-PIS-05` 已把用词抽检收窄到选夹 / 确认 / 等待 / 成功面 / Dock 五处，票根不在其中；且**成品名是渠道名，不是身份名**。但身份行与副券**不得写在同一行**（AC-OLT-18）。

### 4.5 读取与自愈

`read_ledger(trip_dir)` 严格校验，任一不满足即返回 `None`（调用方回退 glob）：

1. 文件存在且为合法 JSON dict
2. `schemaVersion == 1`
3. `outputs` 是 list
4. 每条：`outputId` / `profile` / `surface` / `label` / `files` 非空，`files` 元素为合法裸文件名
5. `staleInputs` 含 `options` 时 `staleOptions` 非空

#### 4.5.1 自愈必须一次 scandir，禁止逐文件 stat（BLK-OLT-03）

**禁止**实现为「逐条遍历 `files` 逐个 `os.path.exists`」。现网量级下这是性能反噬：

| 量 | 值 | 来源 |
|----|----|------|
| 书架首屏 trip 数 | **20** | `trips-client.js:SHELF_PAGE_SIZE` |
| 单 trip 成品条数 | 最坏 3+ | 本文可见上限 |
| 单条文件数 | 最坏 **48** | `platform_profiles.yaml:portfolio_pages.max_pages` |
| **最坏 `stat()` 次数／次书架加载** | **≈ 2880** | 20 × 3 × 48 |

现网 `_longshot_files()` 只做**六组 glob**（每目录一次目录读）。逐文件 stat 会比它更慢 —— 这直接推翻 v0.1.0 `R-OLT-06`「账本替代 glob，净开销应下降」的论断。

**必须实现为**：

```
existing = {e.name for e in os.scandir(trip_dir / 导出文件) if e.is_file()}   # 每 trip 一次
for rec in outputs:
    if not set(rec.files) <= existing:   # 纯内存集合比对
        剔除该条
```

即**每 trip 一次目录扫描 + 纯内存集合比对**，与文件数无关。`AC-OLT-25` 为实测门。

#### 4.5.2 剔除规则

| 情况 | 处理 |
|------|------|
| 全部文件存在 | 保留 |
| 部分文件缺失 | **整条剔除**（不展示部分产物，避免「点开发现少图」） |
| 全部文件缺失 | 整条剔除 |
| 剔除后 `outputs` 为空 | 返回空列表（**不是** `None`）—— 账本有效但无成品，票根不显示副券行 |

自愈**只在读取时生效于返回值**；是否回写瘦身后的账本由 `prune_ledger()` 显式调用（M2 在导出成功后顺带调一次，避免每次 `GET /trips` 写盘）。

---

## 5. 四段指纹与「有更新」判定

### 5.1 为什么分四段

单一指纹会让「改一句文案」把纯图产物也标过期。分段后，每个 profile 声明自己吃哪几段，误报面积可控。

v0.1.0 把渲染选项塞进 `structureFp` 并让所有 profile「保守全吃三段」，八席判为**误报换姿势回潮**（BLK-OLT-05）：`longshotDensity` 只影响长图舞台，进了全产物共吃的那一段，等于调一次长图密度就把作品集页图集体标「有更新」。因此 v0.1.1 拆出第四段 `optionsFp`，且**投影键集由 profile 显式声明**（§5.6），不再一律全吃。

### 5.2 四段定义

| 段 | 前缀 | 输入投影 | 实现位置 |
|----|------|---------|---------|
| **structureFp** | `st:` | `studio.edition`；`studio.portfolio.pageCount`（有则）；每章 `chapterId` + 每屏 `patternId` + 该屏槽位顺序的 `assetId` 列表；封面 `assetId` + 封面样式 id。**不含任何 `export` 选项**（BLK-OLT-05） | **新增** `travelogue/domain/output_fingerprint.py`（纯函数，输入 trip dict） |
| **copyFp** | `cp:` | trip `title` / `subtitle`；每章 `hook` / `lead`；每张 `caption` | 同上 |
| **bundleFp** | 无（沿用现网串） | 读者面 CSS/JS 字节哈希 | **复用现网** `render/context.py:_longshot_bundle_version(trip)`，经 `_bundle_version_paths(trip)` 按身份选 `journal-screens.css` / `portfolio-pages.css` |
| **optionsFp** | `op:` | `trip.export` 中**该 profile 声明的键**（`staleOptions`）的取值子集。声明为空 → `optionsFp = null`，永不失配 | `output_fingerprint.options_fp(trip, keys)` |

`structureFp` / `copyFp` / `optionsFp`：对 canonical JSON（`sort_keys=True`、`ensure_ascii=False`、无空格）取 sha256，前 8 位 hex。

### 5.3 bundleFp 必须复用现网函数

`render/context.py:_bundle_version_paths(trip)` **已按身份分族**（`D-DPI-16`：portfolio 字节不进 journal 列表；`AC-DPI-18`：两族 CSS 哈希互斥），这是 DPI 的正确行为。PFO 记录的误报根因之一是「`layoutCssStale` 用 `journal-screens.css` 去查 `page-*` 格子」—— 复用这个已分族的函数即避开同类错误，**且不新增 edition 分支**（不占窄缝额度）。

**禁止**改用同文件里的 `_BUNDLE_VERSION_PATHS` 常量 —— 它是 journal-only 的旧名遗留（源码注释：*journal-only, no portfolio CSS*），用它会重犯 PFO 的族错配。

任务：把私有 `_longshot_bundle_version` 提升为公开访问器（`BE-OLT-03`），**不改其逻辑、不改 `assetVersion` 输出**，`tests/unit/trip/test_asset_version.py` 的 `_EXPECTED_BUNDLE_VERSION` 不得因本波变动。

### 5.4 状态判定

```
对每条 output：
  files 有任一缺失            → missing  → 剔除，不展示
  否则，对 staleInputs 每一段：
      记录值 != 当前值        → outdated
  全部相符                    → ready
```

`staleInputs` 未列出的段**不参与比对**，即使记录里存了值。`optionsFp` 为 `null` 时视为相符。

### 5.5 判定必须成立的三条

| 断言 | 理由 | AC |
|------|------|-----|
| 只点「重新渲染」、内容未改 → **全部 ready** | 修 G-OLT-02。重渲染不改 patternId / assetId / 文案 / bundle 字节，四段指纹全同 | AC-OLT-08 |
| 改页型 / 换槽图 / 改文案 / 换封面 → 对应 **outdated** | 修 G-OLT-03。mtime 方案会漏，指纹方案不会 | AC-OLT-09 |
| **只改 `longshotDensity` → 长图 outdated，作品集页图 ready** | BLK-OLT-05。渲染选项不得跨舞台污染 | AC-OLT-27 |

**「重渲染会动、而投影不含」的字段清单**（AMD-OLT-02 · 实现不得自行扩大投影）：`updatedAt`、`status` / `pipelineStage`、`renderedAt`、`assetVersion`、各 session / job id、`derivatives*` 派生态、缩略图路径、`exportOptions` 中未被任何 `staleOptions` 声明的键。

### 5.6 `staleInputs` / `staleOptions` 逐 profile 声明（BLK-OLT-05）

在 `config/platform_profiles.yaml` 每个 profile 下新增 `stale_inputs:` 与（需要时）`stale_options:` 两行；`share_zip` / `pdf` 在账本模块内建表。**这是纯增量，不动任何规格字段**（AC-OLT-24）。

| profile / outputId | 渲染路径 | `stale_inputs` | `stale_options` |
|--------------------|---------|----------------|-----------------|
| `wechat_chat:whole` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode`, `longshotDensity` |
| `wechat_chat:chapter` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode`, `longshotDensity` |
| `wechat_moments` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode`, `longshotDensity` |
| `instagram` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode`, `longshotDensity` |
| `weibo` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode`, `longshotDensity` |
| `douyin_cover` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode`, `longshotDensity` |
| `xiaohongshu` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode` |
| `wechat_official` | Playwright 读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode` |
| `portfolio_pages` | Playwright 作品集页 | structure, copy, bundle, options | `copyDisplay`, `breathMode` |
| `moments_grid` | Pillow 再切 | structure, copy, bundle | —— |
| `poster_bric` | Pillow 合成 | structure, copy, bundle | —— |
| `album_spread` | Pillow 合成 | structure, copy, bundle | —— |
| `pdf` | Playwright 打印 | structure, copy, bundle, options | `copyDisplay`, `breathMode` |
| `share_zip` | 打包读者面 | structure, copy, bundle, options | `copyDisplay`, `breathMode` |

**关键**：`longshotDensity` 只被 `scroll` 舞台声明 —— 这一列就是 BLK-OLT-05 的落地点。`QA-OLT-02` 必须有一组断言专测「改 `longshotDensity` 后 `portfolio_pages` 仍 ready」。

进一步按证据收窄（如 Pillow 路径能否摘掉 `bundle`）走 SHD-OLT-11，不在本波。

---

## 6. 票根副券设计

### 6.1 信息层级（两个轴不得混写）

| 轴 | 回答 | 位置 | 归属 |
|----|------|------|------|
| **身份** | 这本书**是什么** | 主票面第一行：`游记` / `作品集 · X 页` | **PIS，本波不动** |
| **成品** | 这本书**出过什么** | 主票面下方新增副券行 | 本波 |

产品原话「通过票根标识（比如游记，长图，作品集等）」里，**游记/作品集是身份，长图是成品**。PIS 已把身份放在第一行；本波把成品放在副券行。**禁止**把「长图」写进身份行，也禁止把「游记」做成副券。

### 6.2 票面布局

零成品（与今天逐像素一致）：

```
┌──────────────────────────────┐
│ ┌────────┐ ⋮                 │
│ │  封面  │ ⋮  《珠海东澳》     │
│ │        │ ⋮  作品集 · 32 页 · 2026 · 08 · 129 张
│ └────────┘ ⋮  NO.20263841    │
│            ⋮      KJPM4R8T ▮▮▎▎▮ │
└──────────────────────────────┘
```

有成品（新增 `v2-shelf__stubs` 一行，插在 `v2-shelf__serial` 之后、`v2-shelf__code` 之前）：

```
┌──────────────────────────────┐
│ ┌────────┐ ⋮                 │
│ │  封面  │ ⋮  《珠海东澳》     │
│ │        │ ⋮  作品集 · 32 页 · 2026 · 08 · 129 张
│ └────────┘ ⋮  NO.20263841    │
│            ⋮  ┄┄┄┄┄┄┄┄┄┄┄┄┄  │
│            ⋮  [作品集页图] [小红书 ·] [+1]
│            ⋮      KJPM4R8T ▮▮▎▎▮ │
└──────────────────────────────┘
```

- `┄┄┄` 为骑缝虚线，复用票根既有齿孔语汇（`v2-shelf__perf`），不引入新视觉语言
- **副券条 = `label`，仅此。禁止任何数字**（铁律 6 · BLK-OLT-02）。身份行的「32 页」是这张卡上唯一的计数（PIS `AMD-PIS-05`）；副券再写 33 就是把 36 vs 37 搬到票根上
- 「有更新」= 条尾一个小圆点 `·`，**不用红色**（不是错误），用弱化前景色
- 既有徽章（`分享图已就绪` 等）与副券的共存规则见 **§6.7**，签帧时必须一并画出

### 6.3 排序、上限与溢出

| 规则 | 值 |
|------|-----|
| 入选 | 仅 §4.4 「上票根副券 = 是」的 outputId。`share_zip` / `pdf` 不入（AMD-OLT-01） |
| 排序 | 先 `surface` 固定序（`folio` → `scroll` → `card` → `grid` → `spread`），同 surface 内按 `createdAt` 倒序 |
| 可见上限 | **3 条** |
| 溢出 | 第 4 条起折叠为 `+N`，点击进「管理成品」（§6.5）。`+N` 的 N **须含** `share_zip` / `pdf` 等未上券的成品，否则「管理成品」里的条数与 `+N` 对不上 |
| 零成品 | 整行不渲染（无空行、无占位） |
| `folio` 优先 | 作品集页图是作品集的默认产物，应排首位（与 PFO「默认产物仍是这一本」一致） |
| 数字 | **一处都不出现**（铁律 6）。`+N` 的 N 是「还有几种」，不是文件数，`aria-label` 须说清 |

排序与截断为**纯函数**，落在新模块 `shelf-outputs-logic.js`，单测覆盖。

### 6.4 文案表（C 端）

| 位置 | 文案 | 禁令 |
|------|------|------|
| 副券条主体 | `{label}`，**仅此** | **禁止任何数字**（BLK-OLT-02）。不写文件数、页数、张数、字节 |
| 副券 `title` / `aria-label`（ready） | `{label} · 在文件夹中显示` | 同上，`title` 里也不许出现数字 |
| 副券 `title` / `aria-label`（outdated） | `{label} · 内容有更新，可重新导出` | **禁止**「更新版面」（PFO）；禁止「过期」「失效」「stale」 |
| 溢出条 | `+{N}` / `aria-label`：`还有 {N} 种成品，点击查看` | N 是**种类数**，须与「管理成品」列表条数一致 |
| 菜单入口 | `管理成品` | 不说「导出账本」。这是「成品」一词在 C 端唯一出现处 |
| 管理列表条目 | `{label} · {fileCount} 个文件 · {年·月·日}` + 状态 | **数字只在这里出现**；不得与身份行同屏并列 |
| 管理列表动作 | `在文件夹中显示` / `重新导出` / `删除这份成品` | — |
| 删除确认 | `删除《{title}》的{label}？只删这份成品，不影响这本书本身。` | — |
| reveal 失败兜底 | `没找到这份文件，可能已被移动或删除。` | 不弹技术错误码（SHD-OLT-07） |

**术语禁令**（延续 PIS / PFO 体例）：C 端不得出现 output / surface / ledger / profile / 指纹 / fingerprint / stale / revision / batchId / outputId / 账本 / 舞台 / **副券**。「副券」是本文的内部词，票面上只出现 `label`（SHD-OLT-09）。

### 6.5 交互

| 动作 | 结果 |
|------|------|
| 点副券（ready） | `POST /__travelogue/reveal`，`relPath = 导出文件/{files[0]}`（复用现网端点） |
| 点副券（outdated） | 同上（仍打开文件夹）；不劫持为重导 —— 用户点的是「看看」 |
| **副券右键 / 长按** | 就地弹出 `重新导出` —— 加席原话「你告诉我旧了，但我点它是打开文件夹，那我到底在哪重做？」。标了「有更新」就必须在同一处给出下一步，**不得只给状态**（SHD-OLT-06） |
| reveal 失败 | toast「没找到这份文件，可能已被移动或删除。」并触发该 trip 的 `outputSummary` 重取；**不得静默无反应**（SHD-OLT-07） |
| 点 `+N` | 打开「管理成品」列表 |
| 卡片菜单 → 管理成品 | 列全部成品（**含 `share_zip` / `pdf`**）+ 状态 + 三个动作 |
| 重新导出 | 复用现网导出入口，预置该 profile（**不新增导出路径**） |
| 删除这份成品 | `DELETE …/outputs/{outputId}`，删文件 + 删账本条目（SHD-OLT-03，可后置到 M3） |
| 键盘 | 副券可 Tab 聚焦，Enter/Space 等价点击 |

**副券点击不得触发打开画册**。现网 `v2-shelf__open--meta` 覆盖整块 stub 区域并绑定 `openTrip` —— 副券行必须在其**外部**或阻止冒泡，否则点副券会跳进预览页。这是实现上最容易踩的一处（`FE-OLT-02` 完成定义已写入）。

### 6.6 视觉与线框门槛

- 票面新增一行会改变信息层级 → **需新签两帧**（BLK-OLT-04）。不接受「先按现网猜」。§6.2 ASCII **不是**已签帧。
  - **看帧入口**：[olt-output-ledger-ticket-v1-wireframe.html](./wireframes/olt-output-ledger-ticket-v1-wireframe.html)
  - **签核记录**：[olt-frame-ab-signoff-2026-08-26.md](./acceptance-records/olt-frame-ab-signoff-2026-08-26.md)（**帧 A/B 已签 2026-08-26**）
  - **帧 A**：票根含副券行，**且必须同时画出 §6.7 收敛后的既有徽章**。只画副券行的帧不予签核 —— 双真相就是这么漏进去的。线框已出浅 / 深 / 禁三套。
  - **帧 B**：「管理成品」列表。M2a 降级路径要靠它单独出门。线框已出列表 + 交互（右键重导 / 删除确认 / reveal 失败 toast）。
- 不改票根形状、不加新色条、不改封面区尺寸（延续 PIS §5.4 精神）。
- 副券字号 ≤ 身份行字号，权重更弱：身份优先级高于成品。
- 深色 / 浅色主题各出一套。
- 若签帧受阻，M2 可先只做「管理成品」列表（需帧 B），票面改动留到帧 A 签完 —— 见 §11 降级路径。

### 6.7 票根状态必须单一真相源（BLK-OLT-04 · 加席否决）

#### 6.7.1 现网已有一套徽章合同

| 徽章 | 常量 | 触发 | 层级 |
|------|------|------|------|
| `分享图需更新` | `STALE_LONGSHOT` | `shelfShowCoverLongshotBadge(trip)` ← `trip.longshotStale`（**mtime 判定**） | **L1** |
| `分享图已就绪` | `READY_LONGSHOT` | `shelfShowCoverReadyBadge(trip)` | **L1** |
| `可重排` | `STALE_BADGE` | `trip.algorithmStale && !trip.longshotStale` | **L2**（`SFP D-SFP-09` 明写：不得压过 L1） |
| `正在准备高清图` | `PREPARING_HD` | 派生态 | 进度类 |
| `可先预览` | `PREVIEW_READY` | `g1Pending` / `derivativesStatus === "preview"` | 进度类 |

v0.1.0 未读这套合同。副券一旦带上指纹判定的 outdated，同一张卡就会出现封面角写「分享图已就绪」、下方副券标「有更新」—— 加席原话：**「到底是好了还是没好？你们内部两个地方算的，别都摆给我看。」**

#### 6.7.2 本波裁定：改 `longshotStale` 的源，不隐藏徽章

评审给了两个方案，本文选 **(a)**：

| 方案 | 处置 |
|------|------|
| **(a) 开旗后 `longshotStale` 改由账本指纹供给** | **采用。** 治的是病根 —— `longshotStale` 的 mtime 判定本身就是 G-OLT-02/03 的成因，也是 PFO 记录的误报来源。改源之后 L1 徽章与副券天然同源，两者不可能矛盾 |
| (b) 有副券时隐藏 L1 徽章 | 不采用。徽章是现网用户已经认得的东西，为了让新功能不打架而藏掉旧功能是倒因为果；且 M2a 降级时票面无副券，L1 又得复原，两套显隐逻辑 |

**实现合同**

```
studio.output_ledger = false（关旗）
  → longshotStale 沿用现网 mtime 判定，逐字不动          （AC-OLT-13）

studio.output_ledger = true（开旗）且账本有效
  → longshotStale = 账本中任一「上票根副券」的成品为 outdated
  → L1 徽章与副券状态同源，不可能矛盾                    （AC-OLT-26）

studio.output_ledger = true 但账本缺失/校验失败
  → 回退 mtime 判定（§8.1 第二层），此时票面也无副券，不产生矛盾
```

`longshotStale` 的**字段名、JSON 契约、徽章文案、`SFP D-SFP-09` 的 L1/L2 优先级全部不动** —— 只换它的计算来源。这样前端 `shelf-actions-logic.js` 零改，`algorithmStale` 的 L2 关系自动保持。

#### 6.7.3 硬约束

- 任一时刻、任一张卡，**不得**同时渲染「分享图已就绪」与任一 outdated 副券（`AC-OLT-26`）。
- **不接受**把收敛留到 M3 或后续波次。M2 若带着两套状态出门，就是把加席否决的东西发出去了。
- `algorithmStale` / `layoutCssStale` / 派生态徽章**本波不碰** —— 它们回答的是别的问题（能不能重排、缩略图好没好），与成品是否最新不冲突。

---

## 7. API 与配置

### 7.1 API 变更

| 端点 | 变更 | 说明 |
|------|------|------|
| `GET /__travelogue/trips` | **新增** `outputSummary` | 轻量：`{ total, chips: [{ outputId, label, state, revealRelPath }] }`，`chips` 最多 3 条（服务端截断）。**`chips` 内不含 `fileCount`** —— 副券禁止显示数字（铁律 6），不下发即不会被误用。`total` 是种类数（含未上券的 `share_zip` / `pdf`），供 `+N` 用 |
| `GET /__travelogue/trips` | 保留 `hasLongshotExport` / `longshotStale` / `longshotRevealRelPath` | 字段与契约不变；**开旗后 `longshotStale` 改由账本指纹供给**（§6.7.2），前端零改 |
| `GET /__travelogue/trips/{tripId}/outputs` | **新增** | 返回完整账本（自愈后），供「管理成品」用 |
| `POST /__travelogue/reveal` | 零改 | 复用；副券传 `导出文件/{file}` |
| `DELETE /__travelogue/trips/{tripId}/outputs/{outputId}` | **新增（SHD-OLT-03）** | 删文件 + 删条目；可后置 M3 |
| 导出相关端点 | 零改 | 账本写入在 `dispatch` 内部，不改请求/响应契约 |

新端点须走 `studio_dispatch.ROUTE_SPECS` 声明式注册 + Studio auth token（与现网一致）。

### 7.2 配置

| 项 | 默认 | 说明 |
|----|------|------|
| `studio.output_ledger` | **M3 已执行：发布默认 `true`。** 关旗仍可回退 | 关旗 ≡ 现网（不写账本、不返回 `outputSummary`、票面无副券、`longshotStale` 走 mtime） |

**开旗时序（BLK-OLT-06）**：v0.1.0 写「M1/M2 默认 `false`，M3 转 `true`」是**自锁** —— M2 前端要渲染副券必须有账本数据，默认关旗下 M2 无可测对象，M4 狗粮也走不了。改为：**M1 合入即在开发/狗粮配置开旗**（发布默认仍 `false`，保住「可独立回退」），M3 只做发布默认值切换与 baseline 收口。

**注意**：**发布**默认值转 `true` 时须过 `lint_csc_recipe_baseline.py`（Happy Path Recipe 默认开关不静默增长）与 `orchestrator/happy_path_recipe.py` 快照更新。任务 `QA-OLT-04` 位置不变（仍在 M3）—— 开发配置开旗不触发 baseline。

### 7.3 遥测（建议）

`output_ledger_write{profile,surface,fileCount}` · `output_chip_click{profile,state}` · `output_stale_detected{profile,segment}` · `output_ledger_fallback{reason}`（回退 glob 的频次，用于判断何时可退休 glob）

---

## 8. 兼容与退役

### 8.1 三层回退

```
1. outputs.json 有效        → 用账本（自愈后）
2. 账本缺失/版本不符        → 回退 longshot-current.json + glob（现网逻辑，逐字不动）
3. 两者皆无                 → 无成品（现网表现）
```

老 trip **不迁移、不补写、不清理**（EOI D-EOI-05 先例）。首次重导时自然长出账本。

**账本有效时不再回落 glob（SHD-OLT-08）**：三层是**互斥择一**，不是并集。后果是**孤儿文件不可见** —— 导出中途失败写了 12/18 张时，账本无条目（`AC-OLT-04`：失败不写），而 glob 能匹配到那 12 张。本文裁定为**不展示**：

| 取舍 | 理由 |
|------|------|
| 展示孤儿文件 | 用户点开发现少图，与 §4.5.2「部分文件缺失整条剔除」自相矛盾 |
| **不展示（采用）** | 宁缺勿错。文件仍在磁盘上，用户从文件夹能找到；重导一次即长出正确记录 |

`custom` 平台的产物同理不可见（§4.3.1），这是把 `custom` 排除出账本的已知代价，**属可接受**：`custom` 是 CLI-only、Phase C，不进 Studio UI，其使用者本就在命令行环境。

### 8.2 `longshot-current.json` 去留

**M1–M3 全程保留，逐字不动。** 它被 `longshot_reveal_rel_path()` 和外部脚本依赖，且是 QFX D-QFX-06b 的成功门。账本是超集但不是替代品。

退役条件（不在本波）：`output_ledger_fallback` 遥测连续两个版本为 0，且无脚本依赖。

### 8.3 glob 退役

`_LONGSHOT_FILE_PATTERNS` 与 `_longshot_files()` **M3 后仍保留**作回退层。真正删除需另立项，条件同 §8.2。

**本波不删任何现网代码。** 这是「可独立回退」的前提：关旗即回到今天。

---

## 9. 所有权与接缝（DPI）

改文件前：`python scripts/lint_dual_pipeline_ownership.py --explain <file>`

### 9.1 窄缝影响：**零新增**

| 文件 | 现状 | 本波做什么 | 是否占额度 |
|------|------|-----------|-----------|
| `export/dispatch.py` | **S-07**（按 `(platform, edition)` 选 Writer） | 成功后调 `append_output()`。**账本写入与 edition 无关**（`edition` 只作为快照字段被动记录，不做分支） | **不占**。无新 `is_portfolio` 分支 |
| `render/context.py` | **S-06** | 只把私有 `_longshot_bundle_version` 提升为公开访问器，**逻辑零改** | **不占** |
| `web/studio_trips.py` | 允许清单（`web/studio*`） | 加 `outputSummary`；开旗时把 `longshotStale` 的源换成账本指纹（§6.7.2）。**换源不引入 edition 分支** —— 指纹本身已通过 `_bundle_version_paths(trip)` 按身份分族 | 不占 |
| `web/studio_dispatch.py` + handlers | 允许清单 | 注册新端点 | 不占 |
| `templates/studio/homepage-v2/**` | 共享壳 | 票根副券 | 不占（副券不按 edition 分支） |

**窄缝仍为 12 / 14。** 若实现中发现必须加 edition 分支才能落地，视为设计错误，回本文重议 —— 不得先加分支再补登记。

### 9.2 允许 / 禁止

| 允许 | 禁止 |
|------|------|
| 新增 `travelogue/export/output_ledger.py` | 在账本或副券逻辑里写 `is_portfolio` 分支 |
| 新增 `travelogue/domain/output_fingerprint.py`（纯函数，最底层，无向上 import） | 改 `mosaic/**` · `editorial_series/**` · `screen-*.yaml` · `page-*.yaml` |
| `config/platform_profiles.yaml` 每平台加 `surface:` / `stale_inputs:` / `stale_options:` 行 | 改任何平台的 `output` 规格 / `segment` / `capture` |
| 换 `longshotStale` 的**计算来源**（§6.7.2） | 改 `longshotStale` 的字段名 / JSON 契约 / 徽章文案 / `SFP D-SFP-09` 优先级 |
| — | 改 `shelf-actions-logic.js`（徽章判定逻辑不动，只换上游数据） |
| — | 在副券 / `chips` / `aria-label` 里放任何数字（铁律 6） |
| — | 逐文件 `stat` 做账本自愈（§4.5.1） |
| — | 让 `custom` 进账本（§4.3.1） |
| `studio_trips.py` / `studio_dispatch.py` / 新 handler | 改 `curate.py` · `assemble.py` · `orchestrator/**` |
| `shelf.js` / `shelf-menu.js` / `shelf.css` / 新 `shelf-outputs-logic.js` | 改 `shelf-ticket-logic.js`（装饰编号不动） |
| — | 改 `portfolio-edition-logic.js:shelfEditionLine`（PIS 身份行不动） |
| — | 写 `trip.json` / 改 `trip.schema.json` |
| — | 在 `journal-screens.css` / `portfolio-pages.css` 加任何规则 |

### 9.3 import-linter 分层

| 新模块 | 层 | 依赖 |
|--------|-----|------|
| `domain/output_fingerprint.py` | 最底层 `domain` | 仅 stdlib（`hashlib` / `json`）。**禁止**向上 import |
| `export/output_ledger.py` | `render/export` 层 | stdlib + `export.longshot.EXPORT_OUTPUT_DIRNAME` + `domain.output_fingerprint` |

两者均不引入跨层边，`lint-imports` 应零变化。

### 9.4 测试夹具策略（BLK-OLT-07）

账本与指纹要**同时覆盖两个身份**（游记 / 作品集），但 DPI 夹具合同规定：

| 夹具 | 归属 |
|------|------|
| `phase16-dogfood/**` | **游记独占** |
| `editorial_series/**` | **作品集独占** |
| `schemas/fixtures/trip.render_golden.json` | **共享基线**（克隆后注入 `edition` 合法） |

**本波强制**

| 测试 | 夹具 | 禁止 |
|------|------|------|
| `QA-OLT-01` 账本单测 | `trip.render_golden.json` **克隆** | 读 `phase16-dogfood` 或 `editorial_series` |
| `QA-OLT-02` 指纹单测 | `trip.render_golden.json` **克隆 + 注入 `edition`**（两身份各一份） | 同上 |
| `QA-OLT-03` `/trips` 契约 | 同上 | 同上 |
| `QA-OLT-06` e2e | 真实 trip 目录（狗粮），不受此约束 | —— |

夹具不交代就会有人顺手去读对面的夹具，`pytest -m pipeline_isolation` 当场红。**克隆 + 注入 `edition` 是唯一合法的双身份取法**，写进 `QA-OLT-01/02` 完成定义。

---

## 10. 任务拆解（实施源）

### 10.1 M1 · 账本与指纹（后端 · 发布关旗、开发开旗 · 现网用户无感）

| ID | 席 | 任务 | 完成定义 |
|----|----|------|---------|
| **BE-OLT-01** | 平台 | 新增 `domain/output_fingerprint.py`：`structure_fp(trip)` / `copy_fp(trip)` / `options_fp(trip, keys)`，canonical JSON + sha256 前 8 位。**`structure_fp` 投影不含任何 `export` 选项**（BLK-OLT-05） | 纯函数无 I/O；同 trip 两次调用同值；改 patternId 必变；改 `updatedAt` 不变；**改 `longshotDensity` 时 `structure_fp` 不变** |
| **BE-OLT-02** | 平台 | 新增 `export/output_ledger.py`：`OutputRecord` / `read_ledger` / `append_output` / `prune_ledger`；严格校验 + 自愈（§4.5）；原子写。**自愈用一次 `os.scandir` + 集合比对，禁止逐文件 stat**（BLK-OLT-03）。`profile == "custom"` 时 `append_output` 直接返回不写（§4.3.1） | 校验失败返回 `None`；文件缺失整条剔除；写失败抛异常；**`scandir` 调用次数 = 1／trip，与文件数无关**（可用 mock 计数断言） |
| **BE-OLT-03** | 渲染 | 把 `render/context.py:_longshot_bundle_version` 提升为公开访问器，**逻辑零改** | `test_asset_version.py:_EXPECTED_BUNDLE_VERSION` 不变；`assetVersion` 输出不变 |
| **BE-OLT-04** | 导出 | `config/platform_profiles.yaml` 每平台加 `surface:` / `stale_inputs:` /（需要时）`stale_options:`；`output_ledger` 内建 `share_zip` / `pdf` 表 | §4.4 + §5.6 两表全覆盖；**无平台规格 / segment / capture 被改动**（AC-OLT-24） |
| **BE-OLT-05** | 导出 | `export/dispatch.py` 成功后 `append_output()`（含 `spec` / `files` / `label` / 四段指纹快照 / `staleInputs` / `staleOptions`）；失败不写。**`wechat_chat` 按整卷/分章生成两种 `outputId`**（§4.3.1） | 六平台 + `portfolio_pages` + zip + pdf 全覆盖；`custom` 不写账本且导出仍成功；关旗时零行为变化 |
| **BE-OLT-06** | 平台 | `studio.output_ledger` 开关接入 config loader；**发布默认 `false`，开发/狗粮配置 `true`**（BLK-OLT-06） | 关旗时 `append_output` 不被调用；开发配置下 M2 有数据可测 |
| **QA-OLT-01** | 测试 | `tests/unit/export/test_output_ledger.py`：schema 往返、版本不符、自愈、原子写、同 `outputId` 替换、`wechat_chat` 两态并存、`custom` 不写。**夹具用 `trip.render_golden.json` 克隆**（§9.4） | 覆盖 §4.5 全部分支；`scandir` 计数断言；**不读 `phase16-dogfood` / `editorial_series`** |
| **QA-OLT-02** | 测试 | `tests/unit/domain/test_output_fingerprint.py`：改 patternId / 改 caption / 改封面 / 只改 `updatedAt` / **只改 `longshotDensity`** 五组断言。夹具克隆 + 注入 `edition`，两身份各一份（§9.4） | 对应 §5.5 三条铁断言；**「改 `longshotDensity` 后 `portfolio_pages` 仍 ready」必须有独立断言** |

### 10.2 M2 · 票根副券（前端 + API）

| ID | 席 | 任务 | 完成定义 |
|----|----|------|---------|
| **BE-OLT-07** | 平台 | `studio_trips._trip_rows` 加 `outputSummary`（服务端截断 3 条 + `total`）；账本缺失时字段缺省。**`chips` 不下发 `fileCount`**（铁律 6） | `/trips` JSON 可断言；老 trip 无该字段不报错；`chips` 内无任何计数字段 |
| **BE-OLT-08** | 平台 | 新端点 `GET /trips/{tripId}/outputs`，走 `ROUTE_SPECS` + auth | 返回自愈后完整账本（**含 `share_zip` / `pdf`**）；无账本返回空列表 |
| **BE-OLT-09** | 平台 | **开旗时把 `longshotStale` 的源换成账本指纹**（§6.7.2）；字段名 / JSON 契约 / 徽章文案 / `SFP D-SFP-09` 优先级全不动 | 关旗走 mtime（AC-OLT-13）；开旗后 L1 徽章与副券同源（AC-OLT-26）；`shelf-actions-logic.js` 零改 |
| **FE-OLT-01** | 前端 | 新增纯模块 `homepage-v2/shelf-outputs-logic.js`：`outputChips(row)` 排序 / 截断 / 状态 / 文案。**输出不含任何数字**（铁律 6） | 单测覆盖 §6.3 排序与溢出、§6.4 文案；断言 chip 文本匹配 `/^[^\d]+$/` |
| **FE-OLT-02** | 前端 | `shelf.js:buildBook` 插入 `v2-shelf__stubs` 行；**副券点击不冒泡到 `openTrip`**；reveal 失败 toast 兜底（SHD-OLT-07） | 点副券只开文件夹，**不**跳预览页；零成品时 DOM 与改前一致；reveal 404 时有可见提示 |
| **FE-OLT-03** | 前端 | `homepage-v2/css/shelf.css`：`.v2-shelf__stubs` / `__stub-chip` / `--outdated` / 骑缝虚线 | 深浅两主题；票根形状与封面区尺寸不变 |
| **FE-OLT-04** | 前端 | `shelf-menu.js` 加「管理成品」→ 列表 + 在文件夹中显示 / 重新导出 / 删除；**副券右键/长按就地给「重新导出」**（SHD-OLT-06） | 无成品时该项不出现；标了「有更新」的副券必有可达的重导入口 |
| **FE-OLT-05** | 前端 | 副券与溢出条的键盘可达 + `aria-label`（§6.4） | Tab 可聚焦；Enter/Space 等价点击 |
| **QA-OLT-03** | 测试 | `tests/js/shelf-outputs-logic.test.mjs`；`/trips` 契约单测；票根零成品快照不变；**同卡不双状态**断言。夹具见 §9.4 | 现网票面快照零 diff；chip 无数字；「已就绪」与 outdated 副券不共存 |

### 10.3 M3 · 发布开旗与收敛

| ID | 席 | 任务 | 完成定义 |
|----|----|------|---------|
| **BE-OLT-10** | 平台 | `studio.output_ledger` **发布**默认转 `true` | 关旗仍可回退 |
| **QA-OLT-04** | 测试 | 过 `lint_csc_recipe_baseline.py` + 更新 `happy_path_recipe` 快照 | CI 绿 |
| **QA-OLT-05** | 测试 | `pytest -m pipeline_isolation` + `lint_dual_pipeline_ownership.py`（**须零新增边**）+ `lint_imports` | 窄缝仍 12 / 14 |
| **QA-OLT-06** | 测试 | e2e：导三种 → 票根三券 → 重导一种 → 仍三券 → 微信群整卷+分章 → 四条 → 手删文件 → 剩三券 | 无 500、无空券 |
| **QA-OLT-07** | 测试 | **性能门**：20 本 × 3 成品（含一条 48 文件的 `portfolio_pages`）的 `GET /trips` 耗时不劣于改前基线（BLK-OLT-03 / AC-OLT-25） | 有基准数落在 PR 描述里 |
| **DOC-OLT-01** | 文档 | `DOC-STATUS.md` 登记 OLT；备忘录 §10 回写「W1 已落地」 | 表内可查 |
| **DOC-OLT-02** | 文档 | `dual-pipeline-ownership.md` 注明本波零新增窄缝（供后续对账） | — |

### 10.4 Should-Fix（不挡 M1/M2）

| ID | 做什么 | 绑哪条 |
|----|--------|-------|
| **SHD-OLT-02** | 「管理成品」列表显示 `bytes` 合计 / 磁盘占用（加席第 5 问）。**不上票根** | FE-OLT-04 |
| **SHD-OLT-03** | `DELETE …/outputs/{outputId}` + 删除确认 | BE-OLT-08 / FE-OLT-04 |
| **SHD-OLT-04** | 「重新导出」直接复用该条 `spec`（而非只预置 profile） | FE-OLT-04 |
| **SHD-OLT-05** | `output_ledger_fallback` 遥测加一维**回退原因**（无账本 / 版本不符 / 校验失败），否则攒不出 glob 退役的证据 | BE-OLT-07 |
| **SHD-OLT-06** | 「有更新」必须给下一步：副券右键/长按就地弹「重新导出」（已并入 §6.5 / FE-OLT-04 完成定义） | FE-OLT-04 |
| **SHD-OLT-07** | reveal 失败兜底 toast（已并入 §6.4 / FE-OLT-02 完成定义） | FE-OLT-02 |
| **SHD-OLT-08** | 孤儿文件裁定（已并入 §8.1 正文） | BE-OLT-02 |
| **SHD-OLT-09** | 「副券」不进 C 端；「管理成品」是「成品」一词唯一出现处，M4 狗粮复验加席是否听得懂，不懂即改 | FE-OLT-04 |
| **SHD-OLT-11** | 按证据进一步收窄 `staleInputs`（如 Pillow 路径能否摘掉 `bundle`）。**替代原 SHD-OLT-01** —— 原条与 BLK-OLT-05 讲的是同一件事的两半，`options` 那半已升为 M1 必做（§5.6），此处只留剩余部分 | BE-OLT-04 |

### 10.5 明确不排期

Surface registry（备忘录 W3）· `EditionSpec`（W2）· 阶段图（W4）· 云同步 · 批量清理 · 成品跨 trip 复制 · `longshot-current.json` 与 glob 的删除。

---

## 11. 里程碑与编码门

| 里程碑 | 出门标准 | 编码门 |
|--------|---------|--------|
| **M0 合同** | 本文过八席；`BLK-OLT-01～07` 回写 | ✅ **已通过**（本文 v0.1.1） |
| **M1** | 账本 + 四段指纹，发布关旗、开发开旗；单测覆盖自愈与三条铁断言；`scandir` 计数断言 | ✅ **已开**（BLK-01/03/05/07 已回写） |
| **M2** | 票根副券 + 管理成品 + 新端点 + **状态收敛**；零成品票面零 diff | ✅ **已落地**（帧 A/B 已签 2026-08-26） |
| **M3** | 发布默认开旗；CSC baseline 过；窄缝仍 12 / 14；性能门过 | ✅ **已落地**（v0.1.4 · 关旗可回退） |
| **M4 狗粮** | 真夹三种导出 → 三券；微信群整卷+分章并存；重渲染不误报；只改长图密度不污染作品集；手删文件自愈；**加席复验用词** | 不挡称 M1/M2/M3 已通；挡「OLT 已通」 |

**BLK 与里程碑的对应**

| 里程碑 | 须先关的 Must-Fix | 状态 |
|--------|------------------|------|
| **M1** | BLK-OLT-01（outputId）· 03（scandir）· 05（投影）· 07（夹具） | ✅ 已回写 · **可开工** |
| **M2** | BLK-OLT-02（去数字）· 04（状态收敛）· 06（开旗时序）+ 帧 A/B 已签 | ✅ 已落地 |
| **无条件 Go** | 全部 BLK 关 + M4 狗粮四项 + 性能基准数 | 待 M4 |

BLK-01/03/05/07 是纯后端，与 BLK-02/04/06 无依赖 —— **M1 不必等票根帧即可开工**。

### 11.1 降级路径

若票根帧 A 签核受阻（§6.6），M2 可拆为：

- **M2a**：只做「管理成品」菜单入口 + 列表（无票面副券，但**需帧 B**）
- **M2b**：票面副券行（待帧 A 签完）

M2a 已能兑现「一套作品多种成品可见、可达」，只是不在票面上。**不接受**为赶进度先按猜的样式改票面。

**M2a 也须先关 BLK-OLT-04**：管理列表同样会与封面角的「分享图已就绪」打架 —— 用户在列表里看到「有更新」、回到书架看到「已就绪」，是同一个双真相问题换了个位置。状态收敛不随降级豁免。

---

## 12. 验收（AC-OLT-*）

| ID | 断言 | 里程碑 |
|----|------|-------|
| **AC-OLT-01** | 成功导出后 `导出文件/outputs.json` 存在，含该 profile 一条，`files` 与磁盘一致 | M1 |
| **AC-OLT-02** | 依次导三种 → 账本 3 条，`outputId` 互不相同，互不覆盖 | M1 |
| **AC-OLT-03** | 同一 `outputId` 重导 → 条数不变，该条 `createdAt` / `files` 被替换 | M1 |
| **AC-OLT-04** | 账本写失败 → 导出**不**报成功（延续 QFX D-QFX-06b） | M1 |
| **AC-OLT-05** | `schemaVersion != 1` → `read_ledger` 返回 `None`，调用方回退 glob，无异常 | M1 |
| **AC-OLT-06** | 手删某条的一个文件 → 该条整体被剔除；其余条不受影响 | M1 |
| **AC-OLT-07** | 删掉 `outputs.json` → 书架退回现网表现，无 500 | M1 |
| **AC-OLT-08** | **四段指纹投影内的字段未变 → 全部 ready。** 判据含「只点重新渲染」与「只改 `trip.updatedAt`」两种走法，以及 §5.5 的「重渲染会动而投影不含」字段清单逐项验证（**AMD-OLT-02 合并原 AC-OLT-08 + AC-OLT-10**） | M1 |
| **AC-OLT-09** | 改 patternId / 换槽图 / 改 caption / 换封面 → 对应条 outdated | M1 |
| **AC-OLT-10** | *（已并入 AC-OLT-08 · AMD-OLT-02）* | — |
| **AC-OLT-11** | `bundleFp` 走 `_bundle_version_paths(trip)` 身份分族；作品集 trip 不因 `journal-screens.css` 变动而 outdated | M1 |
| **AC-OLT-12** | `test_asset_version.py:_EXPECTED_BUNDLE_VERSION` 与 `assetVersion` 输出不因本波改变 | M1 |
| **AC-OLT-13** | 关旗（`studio.output_ledger=false`）→ 不写账本、`/trips` 无 `outputSummary`、票面与今天一致 | M1 |
| **AC-OLT-14** | 零成品 trip 的票根 DOM 与改前快照零 diff | M2 |
| **AC-OLT-15** | 3 条以内全部可见；第 4 条起折叠 `+N`；`folio` 排首位；**副券文本不含任何数字**（正则 `/^[^\d]+$/`）；`share_zip` / `pdf` 不上票根但计入 `+N` | M2 |
| **AC-OLT-16** | **点副券只打开文件夹，不跳进预览页** | M2 |
| **AC-OLT-17** | 副券 `aria-label` 含 label；outdated 条含「内容有更新」；**`aria-label` 内亦不含文件数** | M2 |
| **AC-OLT-18** | 票根身份行仍是「游记」/「作品集 · X 页」（PIS AC-PIS-06 不回退）；装饰序号与花体码不变；**身份行与副券不在同一行**（`album_spread` 的「画册印刷」不得与作品集身份并排） | M2 |
| **AC-OLT-19** | 副券及「管理成品」全部可见文案**不含** output / surface / 账本 / 指纹 / stale / profile / 过期 / **副券** / **更新版面** | M2 |
| **AC-OLT-20** | `GET /trips/{id}/outputs` 无账本时返回空列表而非 404 | M2 |
| **AC-OLT-21** | **窄缝仍 12 / 14**；`lint_dual_pipeline_ownership.py` 零新增边 | M3 |
| **AC-OLT-22** | `pytest -m pipeline_isolation` 绿；`lint-imports` 零变化 | M3 |
| **AC-OLT-23** | 本波 PR **不改** `trip.json` 写入路径、`trip.schema.json`、`mosaic/**`、`editorial_series/**`、`screen-*.yaml`、`page-*.yaml`、`curate.py`、`assemble.py`、`orchestrator/**`、`shelf-ticket-logic.js`、`shelfEditionLine`、`shelf-actions-logic.js` | 每里程碑 |
| **AC-OLT-24** | `platform_profiles.yaml` 除新增 `surface:` / `stale_inputs:` / `stale_options:` 行外零 diff（规格 / segment / capture 未动） | M1 |
| **AC-OLT-25** | **性能门**：20 本 × 3 成品（含一条 48 文件的 `portfolio_pages`）的 `GET /trips` 耗时**不劣于**改前基线；`read_ledger` 的目录扫描次数 = 1／trip，与文件数无关（BLK-OLT-03） | M1（计数）· M3（端到端基准） |
| **AC-OLT-26** | **同一张卡不同时出现「分享图已就绪」与任一 outdated 副券**；开旗后 `longshotStale` 与副券状态同源；关旗后 `longshotStale` 逐字回到 mtime 判定（BLK-OLT-04 · §6.7） | M2 |
| **AC-OLT-27** | **只改 `longshotDensity` → 长图条 outdated，`portfolio_pages` 条仍 ready**（BLK-OLT-05） | M1 |
| **AC-OLT-28** | `wechat_chat` 先导整卷再导分章 → 账本**两条**（`:whole` + `:chapter`）并存，互不覆盖（BLK-OLT-01） | M1 |
| **AC-OLT-29** | `--platform custom --width … --height …` 导出**成功**，且账本**不新增条目**、不抛异常；该 trip 票根无副券、回退 glob（§4.3.1） | M1 |
| **AC-OLT-30** | 账本与指纹单测**不读** `phase16-dogfood/**` 与 `editorial_series/**`；双身份用 `trip.render_golden.json` 克隆 + 注入 `edition`（BLK-OLT-07 · §9.4） | M1 |

---

## 13. 风险与开放问题

### 13.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-OLT-01** | 账本与磁盘漂移（外部删改文件） | §4.5 读时自愈 + 整条剔除；`prune_ledger` 在导出后回写 |
| **R-OLT-02** | 指纹投影漏字段 → 真改了却不标更新（比误报更危险） | QA-OLT-02 五组断言；投影表进本文 §5.2 / §5.6 作为合同；新增影响渲染的字段须同步更新投影（写入 `docs/DEVELOPMENT.md` checklist） |
| **R-OLT-03** | 指纹投影过宽 → 误报回潮 | §5.6 逐 profile 声明（不再一律全吃）；`longshotDensity` 只给 `scroll` 舞台；进一步收窄走 SHD-OLT-11 带证据 |
| **R-OLT-04** | 副券行挤爆票面（长 label + 多成品） | 上限 3 + `+N`；去掉数字后每条更短；label 最长「朋友圈 · 九宫格」已在设计中量过 |
| **R-OLT-05** | 副券点击冒泡到 `openTrip`（现网整块 stub 是打开按钮） | AC-OLT-16 专项断言；FE-OLT-02 完成定义写明 |
| **R-OLT-06** | `/trips` 每行多读一个 JSON + 目录扫描影响书架加载 | **v0.1.0 的「净开销应下降」论断已作废**（BLK-OLT-03）。自愈改为每 trip 一次 `scandir` + 内存集合比对（§4.5.1）；`AC-OLT-25` 为实测门，须给出 20 本 × 3 成品的基准数，**耗时不劣于改前**才算过 |
| **R-OLT-07** | 并行导出 job 同时追加账本导致丢条 | 现网单 job 模型；**并行化前必须先加文件锁**（§4.1 硬前置 · OQ-OLT-04） |
| **R-OLT-08** | 「成品」这个词 C 端不好懂 | 副券上不出现该词（只出现 label）；仅菜单入口「管理成品」用一次；M4 狗粮由加席复验，不懂即改（SHD-OLT-09） |
| **R-OLT-09** | 换 `longshotStale` 的源可能影响现网徽章表现（§6.7.2） | 字段名 / 契约 / 文案 / `SFP D-SFP-09` 优先级全不动，只换计算来源；`shelf-actions-logic.js` 零改（AC-OLT-23）；关旗即逐字回到 mtime（AC-OLT-13）。反过来说，这一改**同时修掉** PFO 记录的 `longshotStale` 误报，是净收益 |
| **R-OLT-10** | `custom` 产物不可见（§4.3.1 的已知代价） | `custom` 是 CLI-only / Phase C / 不进 Studio UI，其使用者在命令行环境；导出仍成功、文件仍在盘上。若日后上 Studio 须回本文重议 |

### 13.2 开放问题（**已由八席裁决** · 2026-08-26）

| ID | 问题 | **裁决** |
|----|------|---------|
| **OQ-OLT-01** | 「管理成品」入口放卡片菜单还是设置里 | **卡片菜单**（就近；加席不会去设置里找导出） |
| **OQ-OLT-02** | outdated 副券点击是否直接触发重导 | **不**（用户点的是「看看」）。但须在同处给出重导入口（SHD-OLT-06） |
| **OQ-OLT-03** | 是否保留同 `outputId` 的历史版本 | **不**（铁律 4；磁盘已按轮 purge） |
| **OQ-OLT-04** | 导出并行化后账本的写锁方案 | 本波不做，但 **§4.1 须写明「并行化前必须先加文件锁」为硬前置** |
| **OQ-OLT-05** | `share_zip` / `pdf` 是否上票根副券 | **改判：不上，只进「管理成品」列表**（AMD-OLT-01）。加席只关心图；上限 3 留给图类 |
| **OQ-OLT-06** | 「成品」用词是否改为「导出」 | **维持「成品」待验证**，M4 狗粮由加席复验（SHD-OLT-09） |
| **OQ-OLT-07** | M2a/M2b 降级是否可接受 | **可**，但 **M2a 也须先关 BLK-OLT-04**（§11.1） |
| **OQ-OLT-08** | 作品集票根上出现「画册印刷」副券是否违 PIS 铁律 3 | **不违。** `BLK-PIS-05` 已把抽检收窄到选夹/确认/等待/成功面/Dock，票根不在其中；成品名是渠道名不是身份名。但身份行与副券不得同行（AC-OLT-18） |
| **OQ-OLT-09** | `AC-OLT-08` 与 `AC-OLT-10` 判据重叠 | **合并为一条**（AMD-OLT-02），并列出「重渲染会动而投影不含」的字段清单（§5.5） |
| **OQ-OLT-10** | `custom` 是否根本不该进账本 | **排除**（BLK-OLT-01 · §4.3.1）。日后上 Studio 再补规格判别式 |

---

## 14. 文档关系

```
要改架构方向、四波顺序、为什么不按渠道切管线
  → 架构重构交流备忘录

要改成品怎么存、票根怎么挂副券、什么时候标「有更新」
  → 本文 OLT

要改产物落在哪个目录
  → EOI

要改导出算法 / 画布 / 切分
  → ADR-021 · ECC · LONGSHOT-2.0

要改导出点法 / 面板 / 成功面页数
  → PFO · PIS · 导出门面

要改票根身份行（游记 / 作品集 · X 页）
  → PIS（本文不动）

要知道八席为什么否掉 outputId=profile / 副券数字 / 双状态
  → 评审纪要 olt-…-review-2026-08-26（Must-Fix 已回写本文 §0.4）

要看帧 A / 帧 B、签 M2 编码门
  → 线框 olt-output-ledger-ticket-v1-wireframe.html · 签核 olt-frame-ab-signoff-2026-08-26（已签）
```

`DOC-STATUS.md` / 备忘录 §10：`DOC-OLT-01` **已回写**（W1 已落地 · M4 未开）。

---

## 15. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-26 | 初稿。承接[架构重构交流备忘录](./架构重构交流备忘录.md) §5–§6 的 W1。定账本落 `导出文件/outputs.json`（不进 `trip.json`）、三段指纹、票根副券设计、前后端任务与 AC-OLT-01～24。**草案未评审，编码门未开** |
| **v0.1.1** | 2026-08-26 | [八席评审](./acceptance-records/olt-output-ledger-ticket-v1-review-2026-08-26.md) **8/8 Conditional Go**，BLK-OLT-01～07 全部回写（§0.4 勘误表为实施依据）：① `outputId` ≠ profile，`custom` 排除、`wechat_chat` 分整卷/分章；② 副券去掉一切数字（加席否决 · 防 36 vs 37 重演）；③ 自愈改一次 `scandir` 集合比对，`R-OLT-06` 论断作废、升 `AC-OLT-25` 实测门；④ **新增 §6.7 票根状态单一真相源**，开旗后 `longshotStale` 改由账本指纹供给（加席否决双状态）；⑤ 渲染选项移出 `structureFp`，改第四段 `optionsFp` + §5.6 逐 profile 声明；⑥ 开旗时序改为 M1 即在开发/狗粮配置开旗；⑦ **新增 §9.4 夹具策略**（`trip.render_golden.json` 克隆 + 注入 `edition`）。两处改判：`share_zip`/`pdf` 不上票根（AMD-OLT-01）、`AC-OLT-08`/`10` 合并（AMD-OLT-02）。AC 扩至 **AC-OLT-01～30**；线框改为**需签两帧**。**M1 编码门打开；M2 待帧 A/B 签核** |
| **v0.1.2** | 2026-08-26 | 落地看帧入口 [olt-output-ledger-ticket-v1-wireframe.html](./wireframes/olt-output-ledger-ticket-v1-wireframe.html)（帧 A 浅/深/禁 · 帧 B 列表/交互）+ 待签记录 [olt-frame-ab-signoff-2026-08-26.md](./acceptance-records/olt-frame-ab-signoff-2026-08-26.md)。合同、BLK、AC、徽章裁定零改。**M2 编码门仍关，等产品勾完拍板清单** |
| **v0.1.3** | 2026-08-26 | 产品勾完拍板清单八条，[帧 A/B 签核](./acceptance-records/olt-frame-ab-signoff-2026-08-26.md) 结论改「认可」。**M2 编码门打开**。合同、BLK、AC、徽章裁定零改 |
| **v0.1.4** | 2026-08-26 | **M3**：`studio.output_ledger` 发布默认转 `true`（BE-OLT-10）；CSC Happy Path 快照收口（QA-OLT-04）；`DOC-OLT-01/02` 回写。关旗仍可回退。**不称 OLT 已通**（挡 M4 狗粮） |
