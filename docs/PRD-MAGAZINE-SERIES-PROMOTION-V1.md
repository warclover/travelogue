# Travelogue · 成册档位全量升格与页序忠实度 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.6.0** |
| **状态** | **有条件通过（Conditional Go）** · **W1a+W1b+W2 已落地**：五档入库 · 填充率选档 · 填充组（三重护栏）· `sequenceFulfillment` · 芯片副文 / 薄档轻确认 · 上限 48（32/36 仍等 ASK-MSP-02）· 24 页仍等 ASK-MSP-01 · 金样未覆盖 |
| **DOC-STATUS** | **active** |
| **评审** | [八席纪要 2026-08-21](./acceptance-records/msp-magazine-series-promotion-v1-review-2026-08-21.md)（七席 + 典型用户加席 · 8/8 Conditional Go） |
| **特性代号** | **MSP**（Magazine Series Promotion） |
| **文档类型** | 运行时成册档位供货合同（把工坊柜的本变成用户能点的档） |
| **触发来源** | 2026-08-21 本机狗粮：用户要按预设编排出 8 页 / 12 页，界面只有「16」一档 |
| **上游合同** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](./PRD-PORTFOLIO-FOLIO-MODE-V1.md)（**PFM**）。本文是 PFM 的档位供货细则，**不废止 PFM，不改 PFM 的身份/导出/隔离铁律** |
| **工坊柜合同** | [PRD-RESERVE-SERIES-CABINET-V1.md](./PRD-RESERVE-SERIES-CABINET-V1.md)（**RSC**）。工坊怎么编排归 RSC，本文只管**怎么升格进运行时** |
| **正式编排器** | [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](./PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（TSU · `/series-editor`）。**本文不开编排器 UI** |
| **关闭的挡门** | PFM **AS-PFM-03**（现记「对账完成 · 不升格」），本文把它推进到「升格」 |
| **不改** | 游记管线、`layoutEngine == "screens"`、导出/分享面、`page-*` 几何、封面封底砖、trip 身份字段 |
| **更新日期** | 2026-08-21 |

> **一句话目标**：把工坊柜里已编排好的 8 / 12 / 16 / 20 / 24 / 28 / 32 / 36 八本，升格成运行时正式档位，用户在精修里点一下就按那本的页序出书；并且**保证点了以后真的按那个页序出**，而不是退化成一串英雄页。
>
> **产品铁律**
>
> 1. **档位由目录驱动，不由代码枚举。** 以后再加一本，只要放一份合规 YAML 就出芯片，不改一行 Python。
> 2. **升格是编译期动作。** 运行时永不读 `docs/templates/reserve/`（ISO-05 不变）。工坊稿改了不会偷偷影响线上。
> 3. **页序是产品，不是建议。** 点了「12 页」就得出那 12 页的编排顺序。兑现不了要么明说，要么换能兑现的档——不允许静默把预设编排拆成英雄页流水。
> 4. **不动游记。** 本波所有改动只在作品集身份下生效；游记指纹字段级零 diff。
> 5. **本波不做疏/密矩阵。** 八本都是 `standard`。疏/密留给后续波次。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §1 | 现状实测盘点（八本长什么样、缺什么） |
| §2 | 目标 / 非目标 / 与 PFM·RSC·TSU 的边界 |
| §3 | 六道硬门槛（不改就升不上去） |
| §4 | 已拍板决策 D-MSP-01～13 |
| §5 | 升格流水线（工坊 → 运行时） |
| §6 | 选档语义（本波最大的行为回归） |
| §7 | 页序忠实度（用户真正在意的「设计感」） |
| §8 | 页数上限与 UI |
| §9 | 会被改红的既有测试与文档 |
| §10 | 任务表与里程碑 |
| §11 | 验收 AC-MSP-* |
| §12 | 风险 · OQ-MSP-01～07（已关闭）· §12.3 八席新增 OQ-MSP-08～11 |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **档 / SKU** | 运行时一个可选页数，对应一份 `magazine-{页数}-{密度}.yaml` |
| **本** | 工坊柜里一份 `folio-*.yaml`（RSC 语义）。升格后才成为「档」 |
| **升格** | 编译期把工坊的本改写成运行时合规 YAML，写进 `travelogue/layout_engine/editorial_series/series/` |
| **页序** | 一本的 `sequence`：第 N 页用哪张脸、几个槽、什么角色 |
| **脸 / face** | `page-*` 版式，运行时住在 `travelogue/layout_templates/templates/` |
| **槽 / slotBand** | 一页能放几张照片 |
| **容量** | 一本页序所有页 `slotBand` 之和，即这本最多能收多少张 |
| **兑现率** | 实际渲染出的页数 ÷ 页序页数。低于 1 说明预设编排没落地 |
| **填充组** | 为了填满多槽页而临时合并的照片集合（§7 提案，需产品拍板） |

---

## 1. 现状实测盘点（2026-08-21 跑脚本得到，非估计）

### 1.1 运行时只有一档

`travelogue/layout_engine/editorial_series/series/` 里只有 `magazine-16-standard.yaml`（version 1）。
因此 `catalog_page_count_chips()` 只返回 `[16]`，精修面板只有「自动 / 16」两个芯片。用户点不到 8 或 12。

### 1.2 工坊柜八本齐，但全是草稿

| 工坊 id | 页数 | `sequence` 长度 | `photo_span` | 页序总槽（容量） | 槽≥5 的密页 | `status` | `version` |
|---------|------|------|------|------|------|------|------|
| `folio-8-standard` | 8 | 8 | [24, 40] | **27** | 3 | `sketch` | 缺 |
| `folio-12-standard` | 12 | 12 | [36, 60] | **36** | 3 | `sketch` | 缺 |
| `folio-16-standard` | 16 | 16 | [48, 80] | **53** | 5 | `sketch` | 缺 |
| `folio-20-standard` | 20 | 20 | [60, 100] | **72** | 7 | `sketch` | 缺 |
| `folio-24-standard` | 24 | 24 | [72, 120] | **73** | 6 | `sketch` | 缺 |
| `folio-28-standard-r2` | 28 | 28 | [84, 140] | **81** | 6 | `sketch` | 缺 |
| `folio-32-standard-r2` | 32 | 32 | [96, 160] | **116** | 9 | `sketch` | 缺 |
| `folio-36-standard` | 36 | 36 | [108, 180] | **134** | 11 | `sketch` | 缺 |

八本的 `id` 页数、`pageCount`、`sequence` 长度三者全部自洽（AS-PFM-03 对账结论仍成立）。

### 1.3 脸覆盖：只缺一张

运行时已编译 **75** 张 `page-*`。八本页序引用的脸里，只有 **`page-10-grid-port`（竖版十宫格，5×2）** 不在运行时——它被 `folio-32-standard-r2` 和 `folio-36-standard` 用到。其余 8/12/16/20/24/28 六本**脸全齐，今天就能升**。

### 1.4 `photo_span` 上界普遍超容量（本文发现的新问题）

| 档 | `photo_span` 上界 | 容量 | 超出倍数 |
|----|------|------|------|
| 8 | 40 | 27 | 1.48× |
| 12 | 60 | 36 | 1.67× |
| 16 | 80 | 53 | 1.51× |
| 20 | 100 | 72 | 1.39× |
| 24 | 120 | 73 | 1.64× |
| 28 | 140 | 81 | 1.73× |
| 32 | 160 | 116 | 1.38× |
| 36 | 180 | 134 | 1.34× |

`photo_span` 在工坊语义里是「这本适合多少张照片」，但运行时 `select_series()` 拿它当**收录上限**（`cap = min(kept_n, hi)`）。两者差 1.3–1.7 倍，意味着**只要 kept 落在 span 上半区，就必然溢出**，用户会看到「本册收录 96 / 140 张」这种角标。今天只有 16 页一档时被升档逻辑掩盖；八档齐了会变成常态。

**处置**：`photo_span` 与收录上限拆开成两个字段（D-MSP-07），上限交给新增的 `capacity`（= 页序总槽数）。见 §5.2 与 §6.3。

### 1.5 页序兑现率实测：16 页只出了 11 页

狗粮 trip `demo-f90d82b3a5`（81 张，无 `shotGroupId`，即每张自成一组）：

- 5 个「槽 ≥ 5」的密页因组规模不足被整页丢弃（`place.py` 的 `DENSE_MIN_SLOTS = 5`，符合 AC-PFM-10），页序出现空洞；
- 其余 2–4 槽页因每组只有 1 张，全部降级成英雄页（今天上午刚加的 solo→hero 兜底）。

**结果：16 页的预设编排，实际只兑现了 11 页，且几乎全是单图英雄页。** 这正是用户说的「没有顺序逻辑、没有设计感」。**这不是页数不够的问题，把八本都升上去也不会自动解决。** 见 §7。

### 1.6 角色登记（需运营复核）

八本共用 29 个 `role`。脚本在工坊附录/目录文本里 grep 不到的有 `hero-land`、`pair-port`、`row-port-3` 三个——但这三个正是 16 页金样在用的角色、运行时已接受，判断是附录 B 登记漏项而非真缺角色。**该结论来自文本 grep，不是权威对账，需运营在 W0 人工确认。**

---

## 2. 目标 / 非目标

### 2.1 目标

| ID | 目标 |
|----|------|
| G-MSP-01 | 八档（8–36）全部进运行时目录，精修面板出现对应芯片，点了就按那本页序重排 |
| G-MSP-02 | 升格可重复执行：一条命令从工坊柜生成运行时 YAML，产物可审、可 diff、可回滚 |
| G-MSP-03 | 以后加第九本零改码：合规 YAML 落目录即出芯片 |
| G-MSP-04 | 点了某一档，页序兑现率有下限保证；兑现不了要么换档要么明示，不静默降级 |
| G-MSP-05 | 溢出不再是常态：`photo_span` 与容量对齐，或选档改按容量 |
| G-MSP-06 | 游记零回归（ISO-01/07 仍绿） |

### 2.2 非目标

- **不做疏/密矩阵。** 八本都是 `standard`，不新增 `sparse` / `dense` 档。
- **不开 `/series-editor`。** 正式编排器仍归 TSU。
- **不改工坊编排交互。** 怎么在 `gallery.html` 排本子归 RSC。
- **不新画脸。** 只补 `page-10-grid-port` 一张（它已有几何，只是未编译）。
- **不改导入向导。** 页数控件仍只在精修（AC-PFM-35 不变）。
- **不改导出/分享/六平台。**
- **trip schema 只动两处**：`studio.portfolio.pageCount` 上界，以及新增 `studio.portfolio.sequenceFulfillment` 诊断。其余字段一律不动。

### 2.3 边界

| 谁 | 管什么 |
|----|--------|
| **RSC** | 工坊柜里怎么手编、存盘、试印 |
| **MSP（本文）** | 工坊 → 运行时的升格闸门、运行时档位语义、页序兑现 |
| **TSU** | 正式编排器 UI、脸的长期供货 |
| **PFM** | 身份、导出、隔离、溢出提示的存在形式 |

---

## 3. 六道硬门槛

升格不是「拷贝文件改个名」。以下每一条不改，对应的档就上不去。

### 3.1 门槛 A · id 命名（八本全挡）

`intake.MAGAZINE_ID_RE` 要求 `^magazine-(\d+)-(standard|sparse|dense)$`，且显式拒绝 `folio-` 前缀（D-PFM-01）。
→ 八本必须改名。`folio-28-standard-r2` / `folio-32-standard-r2` 的 `-r2` **不合法**，须落成 `magazine-28-standard` / `magazine-32-standard`，轮次信息进 `version`（见 D-MSP-03）。

### 3.2 门槛 B · `status: sketch`（八本全挡）

`intake._ALLOWED_STATUS = {"", "official", "promote-ready"}`，`sketch` 被拒。
→ 升格时必须改写 `status`。**这是有意的闸门**：工坊草稿不该被运行时误收。

### 3.3 门槛 C · 缺 `version`（八本全挡「选最新」）

八本都没有 `version`，`match._version()` 会算成 0。同 id 多版本时 `_pick_latest()` 无法排序。
→ 升格时必须烘焙 `version`。

### 3.4 门槛 D · `slotBand` / `patternId` 靠正则反推（八本全命中）

工坊页序只写 `role` + `faceHint`，没有 `slotBand` / `patternId`。运行时 `intake.slot_band_from_role()` 用 `page-(\d+)` 从 `faceHint` 反推槽数，并 `min(band, 8)` 截断。
→ 今天能跑，但是**静默推断**：脸改名或槽数变了不会报错，只会安静少放几张照片。升格必须把两个字段显式烘焙下来（D-MSP-06）。

### 3.5 门槛 E · `page-10-grid-port` 三处被拦（挡 32 / 36 两档）

| 拦点 | 现值 | 后果 |
|------|------|------|
| `layout_templates/page_promote.py` · `LTE_SLOT_MAX = 9` | 9 | 10 槽脸编译时直接 `raise` |
| `layout_templates/validator.py` · `V-P16-12` | `> 9` block | 即便编译出来也过不了校验 |
| `editorial_series/intake.py` · `slot_band_from_role` | `min(band, 8)` | 槽数被压成 8，页面留 2 个空槽 |

（`validator` 的 LTN R-A3 「>6 槽冻结」已对 `page-*` 前缀豁免，这条不挡。）

→ 三处都要放行 10，但**不是全局抬到 10**：`validator.py` 是游记与作品集共用的校验器，`V-P16-12` 是 `level="block"` 的全局闸，为一张脸削弱所有模板的槽数护栏不划算。改为沿用同文件 `_dense_freeze_exempt()` 的写法——**`page-*` 前缀走 10，其余模板仍 ≤ 9**（BLK-MSP-04）。`intake` 侧抬到 10 的同时必须断言「烘焙值 == 脸真实槽数」，不靠上限兜（D-MSP-06）。

### 3.6 门槛 F · 页数上限 32（挡 36 档）

| 拦点 | 现值 |
|------|------|
| `travelogue/config/edition.py` · `PAGE_COUNT_MAX` | 32 |
| `schemas/trip.schema.json` · `studio.portfolio.pageCount.maximum` | 32 |
| `editorial_series/match.py` · `PAGE_COUNT_CHIPS` | `(8, 12, 16, 20, 24, 28, 32)` |
| `travelogue/config/studio.py` · `PortfolioPipelineConfig.max_pages` | 32 |
| `match.catalog_page_count_chips()` / `select_series()` | 按 `max_pages` 过滤，`pc > max_pages` 的档被丢 |

→ 五处必须同步抬到 **48**（D-MSP-04），漏一处 36 档就「入库了但点不到」。

---

## 4. 已拍板决策

> 产品于 **2026-08-21** 回话关闭 OQ-MSP-01～07（见 §12.2）；同日八席评审复核，D-MSP-08 目标函数改判、D-MSP-01/05/06/07/09/10 加限，见 §12.3 与[纪要](./acceptance-records/msp-magazine-series-promotion-v1-review-2026-08-21.md)。

| ID | 决策 | 理由 |
|----|------|------|
| **D-MSP-01** | 八档全量入库，id 为 `magazine-{页数}-standard`。**24 页受 GATE-10 约束，运营补密来不及则本波留七档**（BLK-MSP-08） | 用户诉求：预设编排才有设计感，档位要能选；但不带退化档出门 |
| **D-MSP-02** | 升格是**编译期**动作，产物提交进仓库；运行时仍不读工坊树。**工具是 `scripts/` 下的独立脚本，不进任何运行时包的导入图**（BLK-MSP-01） | ISO-05 / AC-PFM-05 不变；且现有 import-linter 契约禁止 `layout_templates → layout_engine.editorial_series`，不得为本波松绑 |
| **D-MSP-03** | `-r2` 不进 id，进 `version`：`folio-28-standard-r2` → `magazine-28-standard` v2 | id 是档位身份，不是轮次；`_pick_latest` 才有意义 |
| **D-MSP-04** | 页数上限从 32 抬到 **48**（留两档余量：40 / 44 / 48） | 一次改完五处，之后加 40 / 44 / 48 页零改码（关闭 OQ-MSP-04） |
| **D-MSP-05** | 先补 `page-10-grid-port`，32 / 36 档与其他六档**同波**上。**槽数上限不做全局松绑，改按 `page-*` 前缀定向豁免到 10**（BLK-MSP-04）；该脸不过 AS-MSP-03 则退回先上六档 | 分两波会出现「32 档存在但页序有洞」的中间态（关闭 OQ-MSP-05）；`validator.py` 是游记共用闸，不为一张脸削弱全局护栏 |
| **D-MSP-06** | `slotBand` / `patternId` 升格时显式烘焙，并**断言烘焙值 == 脸的真实槽数**；运行时反推逻辑降级为**兜底 + 告警** | 消掉静默失配；上限抬到 10 后更不能靠上限兜 |
| **D-MSP-07** | **`photo_span` 与 `capacity` 拆成两个字段**：`photo_span` **彻底退出功能路径**，只管文案与工坊校验；新增 `capacity`（= 页序 `slotBand` 之和）作为唯一收录上限，**导入向导置灰阈值也改由最小 `capacity` 派生**（BLK-MSP-05） | 一个字段兼两个身份是 §1.4 那 1.3–1.7 倍错位的根因（关闭 OQ-MSP-01）；一个字段一个身份 |
| **D-MSP-08** | 自动选档**按填充率**：取填充率 `kept / capacity` 落入 **`[0.85, 1.05]` 且页数最小**的档；无候选时比较最近的欠填档与最近的溢出档，**溢出 ≤ 5% 优先选溢出档**，否则选欠填档（BLK-MSP-02） | 只看「装得下」会选出欠填的大档，密页成批被丢、兑现率崩掉——那正是 §7 要修的病（关闭 OQ-MSP-02） |
| **D-MSP-09** | 页序忠实度**两级兜底叠加**：① 先用填充组填满预设多槽页——**保留既有 `shotGroup` 不切碎，只合并相邻的单张组；三重护栏 = 同 `curation.segments` + `takenAt` 邻接 ≤ 10 min + 组内总跨度 ≤ 45 min**（[实测](./acceptance-records/msp-oq-msp-12-boundary-study-2026-08-21.md)：兑现率 48% → 69%）；② 仍兑现不了才自动换到能兑现的档并告知用户。降级成英雄页只作最后手段且必须计数暴露。**第二级只对 `pageCountSource == "auto"` 生效；手动钉档忠于页序，宁可留空洞 + 提示**（SHD-MSP-01） | 用户明说要的是编排感（关闭 OQ-MSP-03 / OQ-MSP-06）；钉了 12 页却给 8 页会背叛用户意图 |
| **D-MSP-10** | 芯片列表纯目录派生，代码里不再硬编码页数枚举；UI 九芯片**平铺**不分组，但**每档带一行由 `capacity` 派生的副文**（例「12 页 · 约 36 张」）；**所选档 `capacity` < kept 的 60% 时，点下去之前出一次轻确认**（BLK-MSP-09） | G-MSP-03（关闭 OQ-MSP-07）；纯数字对普通用户等于一个选项，事后角标救不回来 |
| **D-MSP-11** | 本波 `density` 只有 `standard`；`sparse` / `dense` 不进目录 | 控幅 |
| **D-MSP-12** | 升格产物必须带 `_promotedFrom`（工坊 id + 内容哈希），可追溯可比对；**默认拒绝覆盖已存在的 `magazine-*.yaml`，`magazine-16-standard` 额外双确认 + 逐页 diff 打印**（BLK-MSP-07） | 出问题能定位到哪一稿；`magazine-16-standard` 是 PFM 全部验收依据的 P0 金样，不能被自己的工具盖掉 |
| **D-MSP-13** | **AC-PFM-09 定向放宽**：「一页 assetIds 不跨两个 shotGroup」在作品集身份下改为「**不跨 D-MSP-09 的三重护栏**」（同 segment + 邻接 ≤ 10 min + 组内跨度 ≤ 45 min）；游记路径该铁律**一字不动**。**原方案「改为不跨 sceneCluster」已废**——[实测](./acceptance-records/msp-oq-msp-12-boundary-study-2026-08-21.md)显示把同簇作必要条件时合并一次都不触发，与 baseline 逐列相同（607 组 / 48% 兑现），等于没写 | D-MSP-09 的填充组必须能合并相邻单张组；真正的安全绳是**组内跨度 ≤ 45 min**（邻接可传递，仅卡邻接时跨度 p90 仍达 140 min） |

---

## 5. 升格流水线

### 5.1 落点（BLK-MSP-01 已改）

**升格工具是 `scripts/` 下的独立编译期脚本，不进任何运行时包的导入图。**

- `scripts/promote-series.py` — 用 `yaml.safe_load` 直接读三处文件、写一处文件：
  - 读 `docs/templates/reserve/series/folio-*.yaml`（工坊页序）
  - 读 `travelogue/layout_templates/templates/page-*.yaml`（拿脸的真实槽数烘焙 `slotBand` / `capacity`）
  - 读 `docs/templates/reserve/` 附录 B（校验 `role` 登记）
  - 写 `travelogue/layout_engine/editorial_series/series/magazine-*.yaml`（进仓库）
- **不 `import travelogue.layout_engine.editorial_series`，也不 `import travelogue.layout_templates`。**

> **为什么不放在包里。** `pyproject.toml` 的 import-linter 契约「PFM editorial_series isolation (D-U-15 / ISO-05)」把 `travelogue.layout_engine.editorial_series` 列为 `forbidden_modules`，`source_modules` 里就有 `travelogue.layout_templates`。原本设想的「`editorial_series/promote.py` + `layout_templates/cli.py` 子命令」会直接违约，而这条契约是 PFM 评审的产物，**不得为本波松绑或加 ignore**。做成独立脚本还顺手把「编译期」这个身份钉死：它天然不在运行时导入图里。
>
> 运行时侧的 `catalog.assert_not_reserve_path()` 一行不动。

### 5.2 改写规则

| 字段 | 工坊 | 运行时 |
|------|------|------|
| `id` | `folio-8-standard` | `magazine-8-standard` |
| `id`（带 `-r2`） | `folio-28-standard-r2` | `magazine-28-standard` + `version: 2` |
| `status` | `sketch` | `official` |
| `version` | 缺 | 1，`-rN` 稿为 N |
| `pageCount` / `sequence` | 原样 | 原样（已自洽，不动） |
| `photo_span` | 原样 | 原样带过。**语义收窄为编辑建议区间**，不再当收录上限（D-MSP-07） |
| `capacity` | — | **新增**：烘焙为 `sum(slotBand)`。唯一收录上限，选档与溢出判定都只看它 |
| `sequence[].slotBand` | 缺 | 从脸的真实槽数烘焙 |
| `sequence[].patternId` | 缺 | 从 `faceHint` 烘焙 |
| `_promotedFrom` | — | `{ atelierId, contentHash, promotedAt }` |

八档烘焙后的 `capacity`：8 页 = 27、12 页 = 36、16 页 = 53、20 页 = 72、24 页 = 73、28 页 = 81、32 页 = 116、36 页 = 134。

### 5.3 升格闸门（任一红灯即拒，不写文件）

| 闸门 | 断言 |
|------|------|
| GATE-01 | `id` 页数 == `pageCount` == `len(sequence)` |
| GATE-02 | 每页 `faceHint` 都在运行时 `page-*` 目录里 |
| GATE-03 | 烘焙的 `slotBand` == 该脸 LTE YAML 里的真实槽数 |
| GATE-04 | `capacity` == `sum(slotBand)`，且 > 0 |
| GATE-05 | `photo_span[0] > 0` 且 `[0] <= [1]`（建议区间自洽即可，**不再要求 `<= capacity`**） |
| GATE-06 | 每页 `role` 在附录 B 登记（§1.6 待复核） |
| GATE-07 | 产物过 `intake.normalize_series_document()` 不抛错 |
| GATE-08 | 同 `pageCount` + `density` 不出现两个 `version` 相同的档 |
| GATE-09 | `pageCount <= 48`（D-MSP-04 上限） |
| GATE-10 | **相邻档「每新增一页带来的容量增量」>= 1.5 张**。挡的是 §1.4 尾部发现的 20 页 72 槽 / 24 页 73 槽这种退化对（BLK-MSP-08）。实测七对相邻档的增量为 2.25 / 4.25 / 4.75 / **0.25** / 2.0 / 8.75 / 4.5，只有 20→24 这一对不过关 |
| GATE-11 | **目标文件不存在**。已存在须显式 `--overwrite <id>`；`magazine-16-standard` 再加一道双确认并先打印逐页 `patternId` diff（BLK-MSP-07） |

### 5.4 加第九本的路径（G-MSP-03 验证用）

1. 在工坊柜排一本 `folio-40-standard`；
2. 跑 `python scripts/promote-series.py --id folio-40-standard`；
3. GATE-01～11 全绿 → 目录里多一份 `magazine-40-standard.yaml`；
4. 重启即出「40」芯片（副文由 `capacity` 自动派生）。**运行时代码零改动。**

---

## 6. 选档语义（本波最大的行为回归）

### 6.1 今天的行为

目录只有一档，任何照片量都出 16 页。用户感知不到「选档」这件事。

### 6.2 八档齐后，按现有代码会发生什么

`select_series()` 现在的自动路径是：按 `pageCount` 升序排，取**第一个 `photo_span[0] <= kept` 的档**；若 `kept > photo_span[1]` 再往上升一档。

| kept | 今天 | 八档齐后（不改代码） | 那一档的容量 | 结果 |
|------|------|------|------|------|
| 20 | 16 页 | **8 页**（无档 `lo<=20`，回退 `ranked[0]`） | 27 | 勉强 |
| 50 | 16 页 | **12 页**（8 页 hi=40 装不下 → 升 12） | 36 | **溢出 14 张** |
| 81（狗粮） | 16 页 | **16 页** | 53 | **溢出 28 张** |
| 120 | 16 页 | **24 页** | 73 | **溢出 47 张** |

**结论：不动选档逻辑就升档位，等于让 auto 结果整体下移一档，并把溢出从边缘情况变成默认体验。** 这是本波必须一起解决的，不能拆。

### 6.3 已定方案（D-MSP-08 · BLK-MSP-02 改判后）

**「最小的 `capacity >= kept` 的档」是错的。** 它只优化溢出、完全不优化填充：kept=82 会选 32 页（容量 116，填充率 0.71），于是 9 个密页里多数因组规模不足被丢，兑现率崩掉——那正是 §7 要修的病。§6 不能亲手制造 §7 的病。

**正式规则：按填充率选档。**

1. 候选 = 填充率 `kept / capacity` 落入 **`[0.85, 1.05]`** 的档，取**页数最小**者；
2. 无候选时，比较「最近的欠填档」与「最近的溢出档」：**溢出 ≤ 5% 时优先选溢出档**（页序几乎全兑现，代价是明示少收几张），否则选欠填档；
3. kept 超过最大档容量（36 页 = 134）时取最大档，收录上限并明示溢出。

| kept | 命中档 | `capacity` | 填充率 | 溢出 | 若按「最小的装得下」会选 |
|------|------|------|------|------|------|
| 20 | 8 页 | 27 | 0.74 | 0 | 8 页（同） |
| 50 | 16 页 | 53 | 0.94 | 0 | 16 页（同） |
| 76 | 24 页 | 73 | 1.04 | 3（明示） | 28 页（填充 0.94） |
| 82 | **28 页** | 81 | 1.01 | 1（明示） | **32 页（填充 0.71）** |
| 120 | 36 页 | 134 | 0.90 | 0 | 36 页（同） |
| 200 | 36 页 | 134 | — | 66（明示） | 36 页（同） |

> 若 24 页因 GATE-10 本波不升（BLK-MSP-08），kept=76 落 28 页（填充 0.94，溢出 0）。

`photo_span` 退回它原本的语义——**编辑建议区间**，用于「这本适合多少张」的文案与工坊校验，**彻底退出功能路径**（D-MSP-07）。用户手动钉档（`pageCountSource == "user"`）的路径不变：钉了就用那档，装不下就明示溢出，不偷偷升档，也不被兑现率逻辑改写（SHD-MSP-01）。

**护栏 · 兑现率不得作为换档的触发条件。** 填充率选档是第一目标，兑现率只能在同一档内影响填充与降级策略。依据是[实测](./acceptance-records/msp-oq-msp-12-boundary-study-2026-08-21.md) §5：`demo-1d4f92d534`（247 张）在 8 页时兑现率最高（62% > 36 页的 57%），但 8 页只收 27 张、**要扔掉 220 张**。若让兑现率参与选档，最优解会退化成「出一本极小的书、把大部分照片扔掉」。D-MSP-09 第二级与此不冲突：它的触发条件是「兑现率 < 0.8 **且** `pageCountSource == "auto"`」，而换到哪一档仍由上面的填充率规则决定，不是由兑现率最大化决定。

---

## 7. 页序忠实度（用户真正在意的部分）

### 7.1 问题陈述

用户的原话是「只有用编排好的页面，才有顺序逻辑，才有设计感」。§1.5 实测说明：**光有档位不够**。今天 16 页的预设编排落地成 11 页、且几乎全是英雄页，原因是照片没有分组：

- 每张自成一组 → 槽 ≥ 5 的密页被整页丢弃（AC-PFM-10 的正确行为）；
- 2–4 槽页拿到单张组 → 降级成英雄页（今天上午的兜底，避免照片挤在左上角）。

这两条各自都对，合起来把「杂志页序」磨成了「单图流水」。

### 7.2 已定方案：两级叠加（D-MSP-09）

**第一级 · 填充组**
装配前增加一道「填充」：把页序需要的槽数拿去**主动凑组**。规则（经[实测](./acceptance-records/msp-oq-msp-12-boundary-study-2026-08-21.md)定稿）：

1. **既有 `shotGroup` 一律保留，不切碎**；
2. **只把相邻的单张组**合并成填充组，喂给多槽页；
3. 合并须同时满足三重护栏：**同一 `curation.segments`** · **相邻 `takenAt` 间隔 ≤ 10 min** · **合并后组内总跨度 ≤ 45 min**。

第 3 条的第三重是关键：邻接是可传递的，只卡邻接时组内跨度 p90 仍达 140 min（一串「每张相隔 9 分钟」能连成两小时以上的链），那就真会从海边连到餐厅。**组内跨度上限才是 AC-PFM-09 放宽后的安全绳。**

第 1 条同样是实测结论而非直觉：若反过来用「segment + 时间」重切全部分组，已有良好 `shotGroup` 的 trip 会被切碎——`demo-2019` 兑现 93% → 89%、`demo-81d3442e92` 93% → 82%、`demo-9a32512fea` 89% → 71%。**填充组的职责是补缺口，不是重新划分。**

这一级要求 **AC-PFM-09 定向放宽**（D-MSP-13）：作品集身份下判据从「不跨两个 shotGroup」改为「不跨上述三重护栏」，游记路径该铁律一字不动。因为本方案不切碎 `shotGroup`，与游记铁律天然相容。

> **已废弃的写法**：原 PRD 此处写的是「同一 sceneCluster 内相邻的单张组」。实测证明把同簇作为**必要条件**时，合并在 16 本真实 trip 上**一次都没触发**，各项指标与 baseline 逐列相同（607 组 / 兑现 48%）。详见 §12.4 与 §12.5。

**第二级 · 兑现不了就换档（仅自动档）**
填充后仍兑现不了（兑现率 < 0.8）的，自动降到能兑现的档，并告诉用户「你的照片更适合 N 页」。

**这一级只对 `pageCountSource == "auto"` 生效**（SHD-MSP-01）。用户手动钉了 12 页，就给他 12 页——宁可留空洞，也不擅自换成 8 页；空洞连同一句「有 3 页没排满，换 8 页会更饱满」一起给他，决定权还在他手上。

**最后手段 · 降级英雄页**
两级都救不回来的单页才降级成英雄页（今天的行为），且必须计入 `sequenceFulfillment.demotedPages` 暴露出来，不允许静默。

### 7.3 兑现率要可观测

装配诊断落 `sequenceFulfillment`，**只四个标量 + 一个短列表**（SHD-MSP-06，避免 `trip.json` 膨胀与快照噪声）：

| 字段 | 含义 |
|------|------|
| `plannedPages` | 页序页数 |
| `renderedPages` | 实际渲染页数 |
| `fillRatio` | `photosPlaced / capacity` |
| `demotedPages` | 降级成英雄页的页数 |
| `droppedRoles` | 被整页丢弃的 role 短列表 |

不落逐页明细。狗粮时这五项就能一眼看出「这本到底按没按编排出」。

---

## 8. 页数上限与 UI

### 8.1 上限（D-MSP-04）

五处同步抬到 **48**：`config/edition.py` · `schemas/trip.schema.json` · `match.PAGE_COUNT_CHIPS` · `config/studio.py` · 依赖 `max_pages` 的两个过滤。
`PAGE_COUNT_CHIPS`（靠档梯子）补到 `(8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48)`。

> 梯子有 40 / 44 / 48，但目录里没有对应的本，所以 **UI 不会多出这三个芯片**——`catalog_page_count_chips()` 只回目录里真实存在的档。梯子只影响用户钉了非标准页数时的靠档落点：钉 44 会先靠到梯子的 44、再由 `snap_user_page_count()` 落到目录最近的 36。

### 8.2 芯片（BLK-MSP-09 已改）

- 数量从 2 个（自动 / 16）变成 **9 个**（自动 + 八档），**平铺不分组**（D-MSP-10）。`preview-sheet__chip-row` 需要确认换行不破版。
- **每档带一行由 `capacity` 派生的副文**，例「12 页 · 约 36 张」「24 页 · 约 73 张」。九个纯数字对普通用户等于一个选项——加席实测原话是「我会一直点自动，那你做这八个干嘛」。前端 `pageCountChipOptions()` 的返回结构加 `hint` 字段。
- **事前拦**：所选档 `capacity` 小于 kept 的 60% 时，点下去之前出一次轻确认——「这一档只收 27 张，你有 180 张。要更厚的一本吗？」并给出推荐档一键切换。不允许只在事后角标里说。
- 芯片来源仍是 `portfolio.pageCountChips`（服务端派生，D-MSP-10 目录驱动不变）。
- `snap_to_chip(18)` 仍靠档到 16（平票向下），**AC-PFM-12 的验收样例不变**。

### 8.3 顺带变化：导入向导置灰阈值

原本 `min_kept_for_portfolio()` 走 `min_photo_span_lo()`（目录最小 `photo_span[0]`）：今天 48，八档齐后是 24。但 D-MSP-07 已把 `photo_span` 彻底赶出功能路径，**阈值改由最小 `capacity` 派生 = 27**（BLK-MSP-05）。

导入向导「照片太少」的置灰门槛从 48 降到 **27**（AC-PFM-36 行为不变，数字变）。这是好事——短相册也能出作品集了——但狗粮 GUIDE 里写的「48」要改。

---

## 9. 会被改红的既有测试与文档

这一节给审核者估工用。**这些不是 bug，是本波必然要一起改的。**

| 落点 | 现在断言什么 | 为什么会红 |
|------|------|------|
| `tests/unit/layout_engine/test_atelier_series_audit.py` | 目录里只有 `magazine-16-standard`；`over_max == ["folio-36-standard"]`；`page-10-grid-port not in lte_ids` | 三条全部反转 |
| `tests/unit/web/test_studio_entry.py` | `pageCountChips == [16]` | 变九项 |
| `tests/unit/layout_engine/test_editorial_series.py` · `test_compose_from_official_magazine_16` | 53 张 → `magazine-16-standard` | 按 §6.3 填充率规则仍是 16 页（53/53 = 1.0）；按原有 `photo_span` 逻辑会变 12 页。**这条测试正好是 D-MSP-08 的判别式** |
| 同上 · `test_select_series_upgrades_when_span_misses` | 20 张 → 16 页 | 填充率规则下变 8 页（20/27 = 0.74），断言要重写 |
| 同上 · `test_compose_items_match_screens_when_stub_can_cover` | `load_official_series()` 只有 `magazine-16-standard` 且 `photo_span == [48, 80]` | 八档入库后必红（SHD-MSP-05 补入） |
| 同上 · `test_select_series_pinned_*` | 钉 8 页时 `cap == 16`、`capped is True` | `cap` 改由 `capacity` 算（夹具容量 21，kept 20）→ `capped` 翻 False |
| `tests/unit/layout_engine/fixtures/editorial_series/magazine-8-standard.yaml` | 一本 `photo_span [8,16]` / 容量 21 / 脸全是 `page-hero-1` 的假书 | **与真书同 id**。改名为 `magazine-8-sparse.yaml` 并同步三处引用（BLK-MSP-03） |
| `tests/unit/trip/test_asset_version.py` | bundle 哈希 | 补 `page-10-grid-port` 的 CSS 后要回写 |
| `docs/ACCEPTANCE-PORTFOLIO-FOLIO-MODE-V1.md` | AS-PFM-03「不升格」 | 改成「已升格 · 八档入库」 |
| `docs/acceptance-records/pfm-as-pfm-03-atelier-reconcile-2026-08-21.md` | 「不升格」结论 | 追一条后继记录，不改原记录 |
| `docs/acceptance-records/pfm-local-dogfood-GUIDE.md` | 阈值 48 / 单档 | 改数字 |
| `docs/DOC-STATUS.md` | — | 加本文一行 |

---

## 10. 任务表与里程碑

### 10.1 后端

| ID | 任务 | 落点 | 估时 | 里程碑 |
|----|------|------|------|--------|
| **BE-MSP-01** | 升格脚本：改写规则 + GATE-01～11（含金样防覆盖） | `scripts/promote-series.py` | 2.0 | W1a |
| **BE-MSP-02** | 脚本 CLI（`--id` / `--all` / `--dry-run` / `--overwrite`） | 同上 | 0.5 | W1a |
| **BE-MSP-03** | `page-10-grid-port`：**`page-*` 定向豁免**（非全局抬）+ 编译 + CSS + bundle 回写 | `page_promote.py` / `validator.py` / `intake.py` | 2.0 | W1a |
| **BE-MSP-04** | 页数上限 32 → 48（五处 + schema + 靠档梯子） | `config/` · `schemas/` · `match.py` | 0.5 | W1a |
| **BE-MSP-05** | `capacity` 字段烘焙与归一 | `intake.py` · 脚本 | 0.6 | W1a |
| **BE-MSP-06** | 六～八档升格执行 + 产物入库（24 页视 GATE-10） | `series/` | 0.5 | W1a |
| **BE-MSP-07** | 升格闸门单测（八本逐条 + 故意坏样 + 覆盖保护） | `tests/unit/layout_engine/` | 1.5 | W1a |
| **BE-MSP-08** | **按填充率选档**（D-MSP-08 改判后）+ 置灰阈值改走 `capacity` | `match.py` · `config/edition.py` | 1.2 | W1b |
| **BE-MSP-09** | 选档语义单测（§6.3 六组样例，含 82 判别式） | tests/ | 1.0 | W1b |
| **BE-MSP-10** | 夹具改名 `magazine-8-sparse` + 三处引用回写 | tests/ | 0.3 | W1b |
| **BE-MSP-11** | **填充组**：同 sceneCluster 相邻单张组合并 | `place.py` / `compose.py` | 2.5 | W2 |
| **BE-MSP-12** | **兑现率兜底换档**（仅 auto 档）+ 手动钉档留空洞提示 | `compose.py` | 1.2 | W2 |
| **BE-MSP-13** | AC-PFM-09 定向放宽（作品集走 D-MSP-09 三重护栏；游记判据不动）+ 双向单测 | `place.py` / tests | **1.3** | W2 |
| **BE-MSP-14** | `sequenceFulfillment` 五字段 + schema `$defs` + telemetry | `compose.py` / `schemas/` | 0.8 | W2 |
| **BE-MSP-15** | 既有测试与金样回写（§9） | tests/ | 1.5 | W2 |
| **BE-MSP-16** | 游记隔离回归 + `import-linter` 复跑（契约文本未改） | tests/ | 0.4 | W2 |

后端约 **19.3 人日**。

### 10.2 前端

| ID | 任务 | 落点 | 估时 | 里程碑 |
|----|------|------|------|--------|
| **FE-MSP-01** | 九芯片换行/密度不破版 | `preview-toolbar` CSS | 0.5 | W2 |
| **FE-MSP-02** | 芯片副文（`hint` 字段 + 「12 页 · 约 36 张」渲染） | `portfolio-edition-logic.js` / features.js | 0.6 | W2 |
| **FE-MSP-03** | 事前轻确认（`capacity` < kept 60% 时 + 推荐档一键切换） | refine sheet | 0.8 | W2 |
| **FE-MSP-04** | 芯片 a11y（`role="group"` 下九项键盘遍历 + 副文进可访问名） | features.js | 0.4 | W2 |
| **FE-MSP-05** | 换档 / 留空洞的提示文案（C 端零术语） | refine sheet | 0.4 | W2 |

前端约 **2.7 人日**。

### 10.3 运营 / 资产

| ID | 任务 | 业主 | 挡门 |
|----|------|------|------|
| **AS-MSP-01** | 附录 B 复核 `hero-land` / `pair-port` / `row-port-3` 登记（§1.6） | 运营 | GATE-06 |
| **AS-MSP-02** | 八本 `photo_span` 建议区间复核（**不挡工期**：`capacity` 已接手收录上限，`photo_span` 只影响文案） | 运营 + 设计 | 不挡门 |
| **AS-MSP-03** | `page-10-grid-port` 几何签收：10 槽在 16:9 下的可读性 **+ 移动端 9:16 变体怎么重排**（SHD-MSP-02） | 设计 | BE-MSP-03 · 36 页放行 |
| **AS-MSP-04** | `folio-24-standard` 补密排期（容量 73 vs 20 页的 72，GATE-10 退化对） | 运营 + 设计 | 24 页是否本波入库（OQ-MSP-09） |

### 10.4 里程碑

| 里程碑 | 内容 | 挡门 |
|--------|------|------|
| **W0** | 本文审核 · OQ 关闭 · **八席评审 8/8 Conditional Go** · BLK-MSP-01～09 回写 v0.3.0（**2026-08-21 已完成**） | 产品签字 ✅ |
| **W1a** | 升格脚本 + `capacity` 烘焙 + **六档（8/12/16/20/24/28）入库**。这六本最大槽数均为 6，**不碰任何页数上限、槽数上限、新脸、CSS 与 bundle**（见 §10.5） | AC-MSP-01～08 |
| **W1b** | 填充率选档 + 置灰阈值改源 + 夹具改名 + `import-linter` 全绿 | AC-MSP-10～15 |
| **W1c** | 上限抬 48 + `page-*` 定向豁免 + `page-10-grid-port` 编译 + 32 / 36 两档入库 | AC-MSP-09 · AS-MSP-03 |
| **W2** | 填充组 + 兑现率兜底 + 诊断 + 芯片副文与事前拦 + 回归回写 | AC-MSP-16～24 |
| **W3** | 狗粮：同一相册跑 8 / 12 / 24 三档，盲评三问定量（SHD-MSP-08） | AC-MSP-17 |

**W1 出门硬门**：GATE-01～11 全绿 · `import-linter` 全绿且契约文本未被修改 · `magazine-16-standard` 未被覆盖 · §9 三处测试回写完成。在此之前界面不得出现未验证的档位芯片。

### 10.5 为什么 W1a 能只做六档（实测依据）

逐本核对八本页序引用的脸的**真实槽数**（读 `travelogue/layout_templates/templates/page-*.yaml` 的 `slots` 长度，不靠 id 数字反推）：

| 本 | 最大槽数 | >8 槽的脸 |
|----|------|------|
| `folio-8/12/16/20/24/28` 六本 | **均为 6** | 无 |
| `folio-32-standard-r2` | 10 | `page-9-grid-land-wide` · `page-10-grid-port` |
| `folio-36-standard` | 10 | 同上 |

**所有 >8 槽的依赖都只落在 32 与 36 两本上。** 因此 W1a 那六档对以下每一处都是零改动：

| 落点 | 现值 | 六档是否需要动 |
|------|------|------|
| `config/edition.py` `PAGE_COUNT_MAX` | 32 | 否（最大 28） |
| `config/studio.py` `max_pages` | 32 | 否 |
| `schemas/trip.schema.json` `pageCount.maximum` | 32 | 否 |
| `match.PAGE_COUNT_CHIPS` | 已含 8/12/16/20/24/28 | 否 |
| `page_promote.py` `LTE_SLOT_MAX` | 9 | 否（最大 6） |
| `validator.py` `V-P16-12` | ≤9 block | 否 |
| `intake.slot_band_from_role` | `min(band, 8)` | 否 |
| `page-10-grid-port` / CSS / bundle 哈希 | — | 否（不新增脸） |
| AS-MSP-03 设计签收（含移动端） | 待办 | **否——不挡 W1a** |

这就是把 BLK-MSP-04（定向豁免）与 D-MSP-04（上限抬 48）整体推到 W1c 的依据：它们只服务 32 / 36 两档，而那两档还压着设计签收这个长周期项。用户当前的诉求（点得到 8 页 / 12 页）在 W1a 就已满足。

### 10.6 外部问询单（长周期 · 现在就发）

两项都不挡 W1a，但各自压着后面一段，**越早发越好**。

| # | 收件 | 问什么 | 挡什么 | 需要的答复 |
|---|------|--------|--------|------|
| **ASK-MSP-01** | 运营 + 设计（AS-MSP-04） | `folio-24-standard` 现在容量 73 槽 / 24 页 = 3.0 张每页，而 `folio-20-standard` 是 72 槽 / 20 页 = 3.6。两本容量只差 1 张却差 4 页，24 页那本明显偏疏，会被 GATE-10 判红（阈值 1.5 张每新增页，这一对实测 0.25）。**能否给 `folio-24-standard` 补密到容量 ≥ 84？** 若排期来不及，本波先留七档（8/12/16/20/28/32/36），24 页后补。**另附**：R-MSP-06 实测显示容量阶梯上的"档"是稀缺资源（81→116 之间有一个 13 个 kept 取值宽的洞），所以这不只是"数据不整齐"，是浪费了一级台阶。 | 24 页是否本波入库（OQ-MSP-09） | 「补密，X 月 X 日前给」或「本波不补，留七档」 |
| **ASK-MSP-02** | 设计（AS-MSP-03） | `page-10-grid-port` 是 5×2 十个 3:4 竖槽、每槽宽 18.75%。**两问**：① 16:9 桌面下单张约 360px 宽，可读性能否接受？② `page_promote.py` 给每张脸都声明了 `mobile 9:16` 变体，**十个竖槽在 9:16 下怎么重排？**（现在 PRD 一个字没写，这是签收的真正难点，不是桌面几何。） | W1c · 32 / 36 两档放行 | 「两问都签」或「桌面可、移动端须改几何」或「不签，砍 32/36」 |

问询发出后 W1a 照常开工，两者互不阻塞。

---

## 11. 验收

### 11.1 升格与入库

| ID | 断言 |
|----|------|
| **AC-MSP-01** | 运行时目录含 `magazine-{8,12,16,20,24,28,32,36}-standard`，全部过 `intake` |
| **AC-MSP-02** | 八档的 `sequence` 页序（`patternId` 序列）与对应工坊本逐页相同 |
| **AC-MSP-03** | 每页烘焙的 `slotBand` 等于该脸 LTE YAML 的真实槽数 |
| **AC-MSP-04** | `magazine-28/32-standard` 的 `version == 2`；id 里不含 `r2` |
| **AC-MSP-05** | 八档的 `capacity` 分别为 27 / 36 / 53 / 72 / 73 / 81 / 116 / 134，且等于各自 `sum(slotBand)` |
| **AC-MSP-06** | 故意改坏 `capacity` 或引用不存在的脸 → 升格脚本红灯且不写文件（GATE-02 / 04） |
| **AC-MSP-07** | **ISO-05 仍绿**：全库无运行时读 `docs/templates/reserve/`；`load_official_series(series_dir=工坊)` 仍抛错 |
| **AC-MSP-08** | 新放一份合规 `magazine-40-standard.yaml` 后，芯片自动出现「40」，无 Python 改动 |
| **AC-MSP-09** | `page-10-grid-port` 在 LTE 目录、过 validator、CSS 有 10 个 slot 定位声明；**非 `page-*` 模板槽数 >9 仍 block**（BLK-MSP-04 定向豁免） |
| **AC-MSP-25** | **`import-linter` 全绿，且 `pyproject.toml` 的 contracts 段文本零 diff**（BLK-MSP-01：不为本波松绑） |
| **AC-MSP-26** | 不带 `--overwrite` 重复升格是 no-op 且退出码非 0；`magazine-16-standard` 需双确认并先打印逐页 diff（GATE-11） |
| **AC-MSP-27** | GATE-10：构造一对「多 4 页只多 1 槽」的档 → 红灯；且对现有八档跑一遍，**只有 20→24 这一对触发**（阈值不能宽到放过它，也不能严到误伤另外六对） |
| **AC-MSP-28** | 仓库内不存在两个 `magazine-8-standard`：夹具已改名 `magazine-8-sparse`（BLK-MSP-03） |

### 11.2 选档与溢出

| ID | 断言 |
|----|------|
| **AC-MSP-10** | auto 选档按**填充率**：kept=20→8 页、50→16 页、**82→28 页（不是 32 页）**、120→36 页；82 这例允许 1 张溢出并明示 |
| **AC-MSP-11** | kept > 134 时收录上限，且预览角标与成功面都出现「本册收录 N / M 张」（AC-PFM-30 不变） |
| **AC-MSP-12** | 手动钉档既不被容量逻辑改写、也不被兑现率逻辑改写：钉 8 页就出 8 页；钉 12 页排不满时留空洞 + 提示，不自动换 8 页 |
| **AC-MSP-13** | `snap_to_chip(18) == 16`（AC-PFM-12 文案不变）；`snap_user_page_count(44)` 落到目录里的 36 |
| **AC-MSP-14** | 导入向导置灰阈值 == **27**（目录最小 `capacity`，不再读 `photo_span[0]`） |
| **AC-MSP-15** | `photo_span` 彻底退出功能路径：把某档 `photo_span` 改成 `[1, 999]` 后，该档的选档命中、收录量、溢出提示、置灰阈值**四项全部不变** |

### 11.3 页序忠实度

| ID | 断言 |
|----|------|
| **AC-MSP-16** | 同一相册钉 8 / 12 / 24 三档，`patternId` 序列三者互不相同；且**每档与其页序的差异集合恰好等于该次装配的 `demotedPages` + `droppedRoles`**——允许降级，但降级必须被诊断字段完整解释，不允许出现无法归因的偏离（BLK-MSP-06 解 AC-MSP-16/20 互斥） |
| **AC-MSP-17** | 狗粮 trip（81 张单张组）在本波后兑现率 ≥ 0.8；达不到时自动换档并在界面告知，不静默降级 |
| **AC-MSP-18** | 装配诊断含 `sequenceFulfillment` 五项：`plannedPages` / `renderedPages` / `fillRatio` / `demotedPages` / `droppedRoles`，且**不含逐页明细**（SHD-MSP-06） |
| **AC-MSP-19** | **填充组只合并相邻单张组，且不跨三重护栏**。四条断言：① 既有多张 `shotGroup` 不被切碎；② 跨 `segment` 的相邻单张组不合并；③ `takenAt` 间隔 > 10 min 不合并；④ **合并后组内总跨度 > 45 min 必须切开**（构造一串每张相隔 9 min、总跨 2 h 的照片，断言被切成多组） |
| **AC-MSP-28** | **兑现率基线**（防回归）：16 本本机 trip 平均页序兑现率 **≥ 65%**（改造前实测 48%，方案预期 69%），且**无 `shotGroupId` 的 trip 增益 > 20 个百分点**。度量脚本与[实测记录](./acceptance-records/msp-oq-msp-12-boundary-study-2026-08-21.md) §7 复现口径一致 |
| **AC-MSP-20** | 降级成英雄页的页数出现在 `sequenceFulfillment.demotedPages`，不为 0 时界面有出口 |
| **AC-MSP-29** | 每个页数芯片都带由 `capacity` 派生的副文（例「12 页 · 约 36 张」），无裸数字芯片（BLK-MSP-09） |
| **AC-MSP-30** | 所选档 `capacity` < kept 的 60% 时，**点下去之前**出确认并给出推荐档；确认后仍可继续（不硬拒） |

### 11.4 隔离

| ID | 断言 |
|----|------|
| **AC-MSP-21** | **游记侧 AC-PFM-09 判据一字未改**：游记 trip 仍断言一页不跨两个 shotGroup（D-MSP-13 只放宽作品集） |
| **AC-MSP-22** | 游记 `render_fingerprint` 字段级零 diff（ISO-01） |
| **AC-MSP-23** | 全库仍无第三个 `layoutEngine` 值（ISO-07） |
| **AC-MSP-24** | 游记导出 UI 快照零 diff |

---

## 12. 风险与开放问题

### 12.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| R-MSP-01 | 选档语义一改，所有作品集 trip 的重排结果都变 | 作品集仍是 flag 关闭的未 GA 功能，无线上存量；本波一次改完，别分两波 |
| R-MSP-02 | 页序忠实度（BE-MSP-09/10）是本波最大不确定项，可能吃掉一半工期 | W1 / W2 切开：W1 先把档位供上（用户马上能点到 8/12），W2 再攻兑现率 |
| R-MSP-03 | 10 槽脸在 16:9 上每张只有 18.75% 宽，可能小到不可读 | AS-MSP-03 设计签收。**D-MSP-05 已定同波上**，若签收不过则退回「先上六档」并在实施文档记一笔 |
| R-MSP-04 | AC-PFM-09 放宽后，作品集可能拼出观感割裂的一页 | 安全绳是**组内总跨度 ≤ 45 min**（D-MSP-09 第三重护栏），而非原先设想的 sceneCluster——后者实测为空操作。AC-MSP-19 四条断言把边界钉死 |
| ~~R-MSP-05~~ | **已量 · 升为阻塞** → 见 §12.4 与[实测记录](./acceptance-records/msp-r05-r06-measurement-2026-08-21.md)。`sceneCluster` 不能作填充组边界 | 转 OQ-MSP-12，W2 开工前必须关闭 |
| ~~R-MSP-06~~ | **已量 · 已关闭** → 见 §12.4。窗口本身可用，问题在容量阶梯有洞 | 窗口保持 `[0.85, 1.05]`；动作转为补阶梯（OQ-MSP-13 / ASK-MSP-01） |

### 12.2 开放问题（**已全部关闭 · 2026-08-21 产品回话 + 八席复核**）

| ID | 问题 | 结论 |
|----|------|------|
| **OQ-MSP-01** | `photo_span` 语义怎么定？ | **(b) 拆两个字段** — `photo_span` 回归编辑建议区间，新增 `capacity` 管收录上限 → D-MSP-07。**评审加限**：`photo_span` 下界原本还在当置灰阈值，须一并赶出功能路径（BLK-MSP-05） |
| **OQ-MSP-02** | auto 选档改按容量？ | **(a) 改** → D-MSP-08。**评审改判目标函数**：不是「最小的装得下」，而是「填充率落窗口的最小页数」（BLK-MSP-02） |
| **OQ-MSP-03** | 填充组允许跨 `shotGroup`？ | **(c) 两级叠加** — 先填充组，仍兑现不了再换档 → D-MSP-09 / D-MSP-13。**护栏字段经实测改为「同 segment + 邻接 ≤ 10 min + 组内跨度 ≤ 45 min」**（原写的 sceneCluster 为空操作，见 §12.5）。且**只合并相邻单张组，既有 `shotGroup` 不切碎** |
| **OQ-MSP-04** | 上限抬到多少？ | **(c) 48**（留两档余量） → D-MSP-04。五处已逐个核实无遗漏 |
| **OQ-MSP-05** | 32 / 36 与前六档同波？ | **(a) 同波** → D-MSP-05。**评审加门**：解锁方式改定向豁免（BLK-MSP-04），且不过 AS-MSP-03 则退回先上六档 |
| **OQ-MSP-06** | 兑现不了目标档时的默认行为？ | **(a) 自动换到能兑现的档 + 告知**（由 OQ-MSP-03 的第二级承接） → D-MSP-09。**评审限作用域**：只对 auto 档生效（SHD-MSP-01） |
| **OQ-MSP-07** | 九个芯片是否分组？ | **(a) 平铺九个** → D-MSP-10。**评审加限**：平铺保持，但不能是裸数字，须带 `capacity` 副文（BLK-MSP-09） |

### 12.3 八席评审新增开放问题（W1 开工前须带答案）

| ID | 问题 | 会中倾向 |
|----|------|----------|
| **OQ-MSP-08** | 填充率窗口上界 1.05（允许 5% 溢出换页序兑现）可接受吗？ | **已关闭（实测）**：可接受，但当前阶梯下 193 个 kept 取值里只命中 1 次——不是规则错，是阶梯太稀疏。阶梯补密后才会开始工作 |
| **OQ-MSP-09** | 24 页走「运营补密」还是「本波先不升，留七档」？ | 先问运营排期（AS-MSP-04）；来不及就留七档，不带退化档出门 |
| **OQ-MSP-10** | 置灰阈值改由 `capacity` 派生（27）还是保留 `photo_span[0]`（24）？ | `capacity`，一个字段一个身份。已按此写入 D-MSP-07 / AC-MSP-14 |
| **OQ-MSP-11** | 升格脚本放 `scripts/` 还是 `tools/`？ | 跟现有 `scripts/` 一致，本场不纠 |

### 12.4 R-MSP-05 / R-MSP-06 实测结论（2026-08-21）

W2 开工前把两项「拍的、没量的」风险量掉了，跑的是本机 `trips/` 下 **16 本真实 trip**。完整数据见[实测记录](./acceptance-records/msp-r05-r06-measurement-2026-08-21.md)。**两项都被证实为真，且比会中估计更严重。**

#### R-MSP-05 · `sceneCluster` 不能作填充组边界（**推翻 D-MSP-13 的安全性论证**）

两个失效模式同时发生：

- **16 本里 9 本（56%）簇数为 0** —— 每一张 kept 都是噪声 `-1` 或压根没有 `sceneClusterId` 字段。这 9 本同时也没有 `shotGroupId`（每张自成一组），**恰恰是最需要填充组的那批**，而填充组在它们身上是完全的空操作。
- **有簇的 7 本，每本只有 2–3 个簇**，最大簇达 **100 张**（`demo-1d4f92d534`）、**85 张**（`demo-2019`）。一个 100 张的簇不是「同一个海边」，是半趟旅行。

D-MSP-13 放宽 AC-PFM-09 的理由写的是「收到 sceneCluster 内就不会拼出『海边 + 餐厅』」。实测表明这条保护两头都不成立：一半 trip 边界不存在，另一半边界宽到不构成约束。**这不是粒度调参问题，是这个字段在真实数据上既缺失又过粗。**

> **OQ-MSP-12 · 已关闭**（见 §12.5）：填充组边界定为「保留 `shotGroup` + 只合并相邻单张组，护栏 = 同 `segment` + 邻接 ≤ 10 min + 组内跨度 ≤ 45 min」。注意**外层护栏不是「章」而是 `curation.segments`**——`trip["chapters"]` 恒为 3 章 × 8 项，不构成 kept 池的分区，拿它当护栏会排除绝大多数照片。

#### R-MSP-06 · 窗口可用，但容量阶梯有洞

扫描 kept = 8…200：`window` 命中 **46%**，`underfill` 23%，`ceiling` 31%，`overflow-tol` 仅 1%。16 本真实 trip **恰好一半落窗口外**，最低填充率 0.48。

落空区间全部对应阶梯空档：

| kept 区间 | 成因 |
|------|------|
| 8–22 | 在最小容量 27 以下，任何档都填不满 |
| 38–45 · 56–61 | 阶梯自然间隙 |
| **86–98** | **81 → 116 之间跨了 35 槽**（8.75 张每新增页，全阶梯最陡），这里缺一个容量约 95–100 的档 |
| **141–200** | 全部超顶档（134） |

三条结论：

1. **窗口不是问题，阶梯是。** 窗口 `[0.85, 1.05]` 保持不动。
2. **`8–22` 不可填充区间与 AC-MSP-14 的置灰阈值 27 精确吻合** —— 阈值把填不满的区间准确挡在门外，**BLK-MSP-05 定为 (a)（阈值改由最小 `capacity` 派生）由此得到实测支持**。
3. **顶档溢出是 1/5 的真实体验，不是边缘情况。** kept > 134 占扫描区间 31%、占真实 trip 19%；典型用户加席自述的「一次旅行 180 张」正落此区间。所以 AC-MSP-11 的溢出明示是**承重构件**；且 **D-MSP-04 抬上限到 48 是对的，但只抬上限不够——得真有一本 40–44 页的书**。

> **OQ-MSP-13**：是否请工坊排一本 40–44 页，用于承接 kept > 134？会中倾向：排。否则 180 张永远只能出 36 页 + 溢出 44 张。

#### 对 D-MSP-11 的措辞修正

补 `81 → 116` 那个洞的正确做法是一个「32 页疏」或「28 页密」变体，不是再画一本新页序。**疏/密仍是本波非目标（控幅不变），但用途从「以后可能加的花样」改记为「补齐容量阶梯的既定手段」。**

### 12.5 OQ-MSP-12 填充组边界实测（2026-08-21 · 已关闭）

同 16 本真实 trip 上扫了 9 个候选边界。完整数据见[实测记录](./acceptance-records/msp-oq-msp-12-boundary-study-2026-08-21.md)。

#### 定稿

**填充组 = 保留既有 `shotGroup` 不切碎，只合并相邻的单张组；三重护栏 = 同 `curation.segments` + `takenAt` 邻接 ≤ 10 min + 组内总跨度 ≤ 45 min。**

页序兑现率 **48% → 69%（+21 个百分点）**，槽填充 52% → 72%，已写入 D-MSP-09 / D-MSP-13 / §7.2 / AC-MSP-19 / AC-MSP-28。

#### 四条实测依据

**① `sceneCluster` 作必要条件 = 完全空操作。** 「≤10 min 且须同 `sceneCluster`」这一候选与 baseline **逐列完全相同**（607 组 / 可填充 64% / ≥6 组 38 个 / 兑现 48% / 槽填充 52%）。加上「须同簇」后，合并在 16 本 trip 上**一次都没触发**。这比 §12.4 的结论更硬：不是保护力不足，是**这条规则等于没写**。

**② 阈值极不敏感，省掉一轮调参。** 邻接阈值从 3 min 扫到 90 min，兑现率只在 67%–71% 之间移动。取 10 min：拿到增益的九成，同时组数 313（vs 90 min 的 277），边界更紧、观感风险更低。

**③ 必须有独立的组内跨度上限。** 邻接可传递——即便相邻间隔卡在 10 min，组内跨度 p90 仍达 **140 min**。一串「每张相隔 9 分钟」的照片能连成两小时以上的链，那才是真会拼出「海边 + 餐厅」的路径。**跨度 ≤ 45 min 是 AC-PFM-09 放宽后真正的安全绳**，比 `sceneCluster` 实在得多。

**④ 不能反向替换 `shotGroup`。** 若用「segment + 时间」重切全部分组，已有良好 `shotGroup` 的 trip 会被切碎：`demo-2019` 93% → 89%、`demo-81d3442e92` 93% → 82%、`demo-9a32512fea` 89% → 71%。**填充组的职责是补缺口，不是重新划分。** 增益也精确落在该落的地方：+25 到 +68 点的 7 本全是 §12.4 里「无 `shotGroupId`」的那批。

#### 新发现 · 第三类人群：时间稀疏合集

`_bai_w1b_titleart` / `demo-65db8fd377`（两者数据一致，应为同一批照片）是唯一治不好的案例：56 张切出 51 组，最大组 3，兑现率 20%，**任何阈值增益均为 +0%**。原因是相邻拍摄间隔 **p10 = 16.5 min、p50 = 8.6 小时、p90 = 47 小时**——p10 就已大于任何合理阈值。对照正常旅行（`demo-e52494839a`）的 p50 是 **0.1 min**。

**换档也救不了**：八档全扫一遍，兑现率始终 20–29%。

> **OQ-MSP-14（新增）**：这类相册是否显式排除预设页序？
> 倾向：是。以「kept 相邻间隔中位数 > 60 min」判定为稀疏合集，**不走预设页序，回落现有按画幅排布的路径，并向用户说明原因**。硬套预设页序只会得到一本七成页面降级的书，比不套更糟。**这不是调参能解决的，是识别问题。**

#### 护栏 · 兑现率不可作为换档触发条件

八档矩阵暴露一个陷阱：`demo-1d4f92d534`（247 张）在 **8 页**时兑现率最高（62% > 自动选中的 36 页 57%），但 8 页只收 27 张，**要扔掉 220 张**。`demo-0ebda73294` 同理（28 页 68% > 36 页 58%，代价是少收 53 张）。

**若把兑现率提为主目标，最优解会退化成「出一本极小的书、把大部分照片扔掉」。** 故 §6.3 已加护栏：**填充率选档是第一目标，兑现率只能在同一档内影响填充与降级策略，不得作为换档的触发条件。** 这与 D-MSP-09 第二级不冲突——第二级的触发条件是「兑现率 < 0.8 **且** `pageCountSource == "auto"`」，且换档方向由填充率规则决定，不是由兑现率最大化决定。

---

## 附录 A · 实施时会动的文件（对照，不是合同正文）

| 文件 | 动什么 |
|------|--------|
| `scripts/promote-series.py` | **新增** · 升格规则与 GATE-01～11。独立编译期脚本，不 import 运行时包（BLK-MSP-01） |
| `travelogue/layout_engine/editorial_series/series/magazine-*.yaml` | 新增六～八份产物（24 页视 GATE-10） |
| `travelogue/layout_engine/editorial_series/intake.py` | `slotBand` 上限 8→10；`capacity` 归一；反推逻辑降级为兜底 + 告警 |
| `travelogue/layout_engine/editorial_series/match.py` | `capacity` 读取；**按填充率选档**；`PAGE_COUNT_CHIPS` 补到 48 |
| `travelogue/layout_engine/editorial_series/place.py` | 填充组；sceneCluster 边界判据（作品集侧） |
| `travelogue/layout_engine/editorial_series/compose.py` | `sequenceFulfillment` 五字段；兑现率兜底换档（仅 auto） |
| `travelogue/layout_engine/editorial_series/catalog.py` | 置灰阈值来源从 `min_photo_span_lo` 改为最小 `capacity` |
| `travelogue/layout_templates/page_promote.py` | `LTE_SLOT_MAX`：`page-*` 走 10，其余仍 9 |
| `travelogue/layout_templates/validator.py` | `V-P16-12`：按 `page-*` 前缀定向豁免到 10，非 `page-*` 仍 block |
| `travelogue/layout_templates/templates/page-10-grid-port.yaml` | 新增 |
| `travelogue/layout_templates/journal-screens.generated.css` | 重生成 |
| `tests/unit/layout_engine/fixtures/editorial_series/magazine-8-standard.yaml` | 改名 `magazine-8-sparse.yaml` + 三处引用回写（BLK-MSP-03） |
| `travelogue/config/edition.py` | `PAGE_COUNT_MAX` 32→48 |
| `travelogue/config/studio.py` | `max_pages` 默认 32→48 |
| `schemas/trip.schema.json` | `pageCount.maximum` 32→48；`studio.portfolio` 增 `sequenceFulfillment` |
| `templates/studio/preview-toolbar/*.css` | 九芯片换行 |
| `tests/unit/...` | §9 全表 |
| `docs/DOC-STATUS.md` · PFM 验收/实施 · 狗粮 GUIDE | §9 全表 |
