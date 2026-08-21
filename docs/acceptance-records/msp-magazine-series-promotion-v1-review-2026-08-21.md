# PRD-MAGAZINE-SERIES-PROMOTION-V1 · 七席 + 典型用户评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MAGAZINE-SERIES-PROMOTION-V1.md](../PRD-MAGAZINE-SERIES-PROMOTION-V1.md)（**MSP** · 成册档位全量升格与页序忠实度）**v0.2.0**（OQ-MSP-01～07 已由产品关闭） |
| **上游合同** | [PFM](../PRD-PORTFOLIO-FOLIO-MODE-V1.md) v0.2.0（本文推进其 AS-PFM-03、定向放宽其 AC-PFM-09） |
| **相邻挡门** | [RSC](../PRD-RESERVE-SERIES-CABINET-V1.md) · [TSU](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md) · [TDV](../PRD-TEMPLATE-DESIGN-VERIFICATION-V1.md) · [LVP](../PRD-LAYOUT-VIBE-PICKER-V1.md) |
| **前序纪要** | [PFM 八席 2026-08-20](./pfm-portfolio-folio-mode-v1-review-2026-08-20.md) · [AS-PFM-03 对账 2026-08-21](./pfm-as-pfm-03-atelier-reconcile-2026-08-21.md) |
| **日期** | 2026-08-21 |
| **结论** | **有条件通过（Conditional Go）**。升格方向成立，八档供货与「页序是产品」的立场可冻结。**BLK-MSP-01～09 回写 v0.3.0 前：不批无条件 Go · 不批 W1 合码 · 不批 `page-10-grid-port` 解锁 · 不批 W2 填充组拆单**。 |
| **编码** | ☑ 现状实测盘点　☑ 产品关 OQ×7　☐ v0.3.0 回写 BLK　☐ W1 升格流水线　☐ W2 页序忠实度　☐ W3 狗粮三册 |
| **参评角色** | **七席**：产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测）· **加席**：典型用户（非从业者 · 一次旅行拍 180 张 · 现网只用过「选夹→开始→发群」，昨天第一次点了「做一本作品集」） |
| **评审方式** | 分席只读 PRD v0.2.0 §0～§12 + 附录 A，对照现网代码事实（`editorial_series/{catalog,intake,match,place,compose}.py`、`layout_templates/{page_promote,validator,cli}.py`、`config/{edition,studio}.py`、`schemas/trip.schema.json`、`pyproject.toml [tool.importlinter]`、`tests/unit/layout_engine/`）与工坊柜实测数据（八本 YAML 逐本跑脚本） |
| **记录人** | 八席联合纪要（跨职能模拟联评 · 2026-08-21） |
| **本纪要状态** | **已结案 · Conditional Go** · **Must-Fix 待回写 PRD v0.3.0** |
| **审查基线** | 游记逐字不动 · 引擎不读工坊（ISO-05）· import-linter 既有契约不得为本波松绑 · **不把「档位上了」当成「编排兑现了」** · **加席否决权与产品同等：用户点了一个数字却不知道会发生什么，算没写完** |

---

## 0. 会前宣读（主持人）

1. **切口**：工坊柜里躺着八本已编排好的页序（8–36 页），运行时目录只有一本 16 页。用户昨天的原话是「只有用编排好的页面，才有顺序逻辑，才有设计感」。PRD 选的是：编译期升格 + 目录驱动芯片 + 页序忠实度兜底。方向本场不重开。
2. **已拍（勿重开）**：八档全量入库；升格是编译期；`-r2` 进 `version`；上限抬 48；32/36 同波；`photo_span` 与 `capacity` 拆字段；按容量选档；填充组 + 换档两级叠加；九芯片平铺。这七条是产品 2026-08-21 回话关闭 OQ-MSP-01～07 的结果，**本场只审「怎么落」，不重投「要不要」**。
3. **勿重开**：疏/密矩阵、`/series-editor` UI、新画脸、导入向导加页数控件、把作品集设成默认。
4. **本场必拍**：升格工具放哪一层（现有 import-linter 契约挡不挡）；「按容量选档」的目标函数到底是「装得下」还是「填得满」；`magazine-8-standard` 这个 id 在仓库里已经被占了；把全局槽数上限从 9 抬到 10 会不会顺手削弱游记护栏；九个纯数字芯片普通用户怎么选；P0 金样会不会被自己的升格工具盖掉。
5. **加席说明**：典型用户不知道 `capacity`、不知道 `slotBand`。他只会问三句——这八个数字有什么区别、我选错了会怎样、我选了 12 出来的东西凭什么和 16 不一样。他说「看不出区别」，就是 Must-Fix。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：这份 PRD 最大的优点是它没有靠估计写——八本 YAML 逐本跑过、75 张脸的覆盖率数过、五处页数上限和三处槽数上限逐个点出来、连「16 页只兑现了 11 页」都是实测而不是推测，§1 现状盘点的含金量高于本仓库多数 PRD 的同章节，而且它诚实地承认了「光升档位不解决设计感」这个反直觉结论，没有拿档位数量交差。但 v0.2.0 有九处按原文 Kickoff 会撞墙或会假绿：（1）§5.1 把升格工具放在 `layout_engine/editorial_series/promote.py` 并从 `layout_templates/cli.py` 调用，而 `pyproject.toml` 里「PFM editorial_series isolation (D-U-15 / ISO-05)」这条 forbidden 契约明文禁止 `travelogue.layout_templates` 导入 `travelogue.layout_engine.editorial_series`——按原文写第一次跑 lint 就红，且不能为本波松绑；（2）D-MSP-08「按容量选档」的目标函数写成了「最小的容量 ≥ kept 的档」，这只保证不溢出、完全不保证填满：kept=82 会选 32 页（容量 116，欠 34 张），于是密页成批被丢、兑现率崩掉——而兑现率恰恰是 §7 要救的东西，两节自相矛盾；（3）`magazine-8-standard` 这个 id 仓库里已经有了，是 `tests/unit/layout_engine/fixtures/editorial_series/magazine-8-standard.yaml`，页数同为 8 但 `photo_span [8,16]`、容量 21、`patternId` 全是 `page-hero-1` 这类不存在的脸，两本同名书会在评审、日志和排障时长期互相冒充；（4）把 `LTE_SLOT_MAX` 和 `V-P16-12` 从 9 抬到 10 是全局松绑，`validator.py` 是游记与作品集共用的，为一张脸削弱所有模板的槽数护栏不划算，现成的 `_dense_freeze_exempt` 已经给出了「按 `page-*` 前缀定向豁免」的写法；（5）D-MSP-07 宣布 `photo_span` 只管文案，但 `config/edition.py` 的 `min_kept_for_portfolio` 正拿它的下界当导入向导置灰的功能闸门，一个字段刚被降级又被当门用；（6）AC-MSP-16 要求三档产出的 `patternId` 序列「各自等于对应档页序」，AC-MSP-20 又承认会有降级英雄页并要求计数，两条 AC 直接互斥，QA 按哪条都能判对方错；（7）升格工具会重新生成 `magazine-16-standard.yaml`，而那是 PFM W1/W2 全部验收所依据的 P0 金样，PRD 没有任何防覆盖约定，RSC 铁律 4 的运行时对偶缺失；（8）20 页容量 72 与 24 页容量 73 只差一张，选档阶梯在这里退化成悬崖——第 73 张照片会让书从 20 页跳到 24 页，页数 +4 而收录 +1，这是工坊数据问题不是代码问题，但 PRD 把它当成了正常阶梯；（9）九个纯数字芯片对典型用户是九个等价的谜，PRD 明写「平铺不分组」却没给任何选择依据，加席实测反应是「我会一直点自动，那你做这八个干嘛」。关 BLK 后升 v0.3.0；W1 可先做升格流水线与上限，但 `page-10-grid-port` 解锁与 32/36 两档必须等 BLK-04 与 AS-MSP-03。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「页序是产品，不是建议」这条铁律我签，它把这一波从「加七个数字」提升成了「保证编排落地」，方向对。但两件事没闭合：一是九个数字对用户没有意义，我在精修面板上写不出一句让他知道该点哪个的话——要么给每档一句「约 27 张 · 短册」，要么就别平铺九个；二是用户钉 8 页而手里有 180 张时，PRD 只说「明示溢出」，可 27/180 这个比例不是「明示」能救的，应该在他点下去之前就劝住。 |
| **算法** | **Conditional Go** | §1.4 找出 `photo_span` 上界超容量 1.3–1.7 倍，是本文最有价值的发现，`capacity` 拆字段我完全同意。但 D-MSP-08 的目标函数写错了：「最小的容量 ≥ kept」只优化了溢出，没优化填充率。kept=82 时它选 32 页（容量 116），实际填充率 0.71，密页会成批掉；而 28 页（容量 81）只溢出 1 张，填充率 0.99，页序几乎完整兑现。选档要在「溢出」和「欠填」之间做权衡，不能只压一边——否则 §6 亲手制造了 §7 要修的病。另外 20 页 72 槽 / 24 页 73 槽这一对基本退化，阶梯在这里不连续，请运营看一眼 24 页那本是不是排得过疏。 |
| **架构** | **Conditional Go** | 编译期升格、产物进仓库、运行时守卫不动，这个骨架是对的，跟 `page_promote.py` 的先例一致。但 §5.1 的落点会被现有契约直接打回：`pyproject.toml` 里 `[[tool.importlinter.contracts]]` 有一条 name = "PFM editorial_series isolation (D-U-15 / ISO-05)"，`forbidden_modules` 明确列了 `travelogue.layout_engine.editorial_series`，`source_modules` 里就有 `travelogue.layout_templates`。PRD 却让 `layout_templates/cli.py` 去调 `editorial_series/promote.py`。这条契约是 PFM 评审的产物，不能为了一个编译期工具松绑。升格工具要么整个搬到 `layout_templates` 侧、用 `yaml.safe_load` 直接读写两边的文件而不 import `editorial_series`，要么做成 `scripts/` 下的独立编译期脚本。我倾向后者：它天然不参与运行时导入图，也顺手把「编译期」这个身份钉死。 |
| **开发** | **Conditional Go** | 任务表颗粒度可开工，16.4 人日的分布合理。三处要调：BE-MSP-03「解锁三处 + 编译 + CSS + bundle 回写 1.0 天」偏低——`page-10-grid-port` 是 10 槽 5×2，`boxes_to_grid` 的轨道推导 + `intentionalGaps` 声明 + CSS 重生成 + `test_asset_version` 金样，参照上次改 `css_gen.py` 的实际耗时按 2.0 天报；BE-MSP-05 现在把 `capacity` 字段和选档合成一条，建议拆开，因为按算法席意见选档目标函数要重写，两件事的风险不一样；另外升格工具需要读 75 份 LTE YAML 拿真实槽数来烘焙 `capacity`，这个读取路径要跟架构席的结论对齐后才能动手，先别开分支。 |
| **测试 / QA** | **Conditional Go** | §9「会被改红的既有测试」这一节写得罕见地负责，把判别式都点出来了，我很少见到 PRD 主动列自己会打红哪些测试。但 AC 层有三处会假绿或互斥：AC-MSP-16 要求 `patternId` 序列等于页序，AC-MSP-20 又要求降级页数可以不为 0，这两条不能同时成立，必须给 AC-MSP-16 加一个「允许降级尾差，且尾差等于 `demotedPages`」的口径；`magazine-8-standard` 在 `tests/unit/layout_engine/fixtures/editorial_series/` 下已经是一本假书（`photo_span [8,16]`、容量 21、脸全是 `page-hero-1` 这种不存在的 id），真书入库后同名两本，`test_select_series_pinned` 断言的 `cap == 16` 也会随 `capacity` 语义翻——请把 fixture 改名（`magazine-8-sparse` 合法且不撞）；还有 §9 漏了一条：`test_editorial_series.py` 里 `test_compose_items_match_screens_when_stub_can_cover` 直接断言 `load_official_series()` 只有 `magazine-16-standard` 且 `photo_span == [48, 80]`，八档入库后必红。 |
| **视觉 / 排版** | **Conditional Go** | 八档页序我看过工坊试印，节奏是对的，升格我签。两件必须说穿：第一，`page-10-grid-port` 是 5×2 十个 3:4 竖槽、每槽宽 18.75%，在 16:9 桌面上单张约 360px 宽还能看，但 `page_promote.py` 给每张脸都声明了 `mobile 9:16` 变体，十个竖槽塞进 9:16 意味着什么，PRD 一个字没写——这不是签不签几何的问题，是移动端到底怎么重排的问题，AS-MSP-03 得把这一问包进去；第二，容量除页数看下来 24 页那本是 3.0 张/页、20 页是 3.6 张/页，24 页比 20 页更疏却更长，用户在这两档之间感受到的差别可能是「更空」而不是「更多」，请运营复核。 |
| **用户体验 · 狗粮** | **Conditional Go** | 「不允许静默把预设编排拆成英雄页流水」这条我举双手，它正好是我昨天在 `demo-f90d82b3a5` 上看到的病。D-MSP-09 的三级兜底（填充组 → 换档 → 降级）顺序也对。但第二级「自动换到能兑现的档」有个体验坑 PRD 没处理：用户手动钉了 12 页，系统觉得兑现不了就换成 8 页——这跟 D-MSP-08 里「手动钉档不被容量逻辑改写」是打架的。手动钉档到底能不能被兑现率逻辑改写？我的意见是不能，钉了就忠于页序、宁可留空洞也要给他 12 页，然后告诉他「有 3 页没排满，换 8 页会更饱满」，把决定权还给他。自动档才允许系统换。 |
| **典型用户（加席）** | **Conditional Go** | 我昨天点了「做一本作品集」，今天你给我八个数字：8、12、16、20、24、28、32、36。我老实说——我会一直点「自动」，因为这八个我一个都看不懂。你要是在旁边写「12 页 · 约 36 张 · 薄一点」「24 页 · 约 73 张 · 厚一点」，我就知道该点哪个了。第二件事，我拍了 180 张，我点 8 页，然后呢？你说会告诉我「收录 27 / 180 张」——那我 153 张去哪了？我点之前就该有人拦我一下，而不是点完了通知我。第三件事，你说 12 页和 16 页是两种不同的编排——我怎么知道？我看到的就是页数不一样。要是点了 12 出来的东西跟 16 只是少四页，那这八个选项对我就是一个选项。 |

**汇总**：**8/8 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批 W1 合码** · **不批 `page-10-grid-port` 解锁** · **不批 W2 填充组拆单** · **不批覆盖 `magazine-16-standard`**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **9** | 现状盘点全部实测；诚实指出「光升档位不解决设计感」这个反直觉结论 |
| 与现网代码对齐 / 防假绿 | **5** | 六道门槛点得准，但漏了 import-linter 契约与 `magazine-8-standard` id 占用两处硬事实 |
| 与 PFM / RSC / TSU 边界 | **8** | 所有权表清楚；AC-PFM-09 定向放宽的写法（只放宽作品集侧 + 双向断言）是本文最漂亮的处理 |
| 算法自洽性 | **4** | §6 的选档目标函数与 §7 的兑现率目标互相拆台 |
| 工程可开工性 | **6** | 任务表可拆；但升格工具落点被契约挡住，两项估时偏低 |
| AC 可测性 | **6** | 隔离类与升格类扎实；AC-MSP-16/20 互斥，且漏了一条会红的既有测试 |
| 普通用户可完成一次 | **4** | 九个数字无选择依据；钉小档时的大量丢弃只在事后告知 |

---

## 3. 事实核查（对照现网代码 · 影响结论）

| # | PRD v0.2.0 假设 | 代码 / 数据事实（2026-08-21） | 会中 |
|---|-----------------|------------------------------|------|
| **F-MSP-01** | 升格工具可放 `layout_engine/editorial_series/promote.py`，由 `layout_templates/cli.py` 加子命令调用（§5.1） | `pyproject.toml` `[tool.importlinter]` 契约 "PFM editorial_series isolation (D-U-15 / ISO-05)"：`source_modules` 含 `travelogue.layout_templates`，`forbidden_modules` 含 `travelogue.layout_engine.editorial_series`，`allow_indirect_imports = true` | **落点违约 · BLK-MSP-01** |
| **F-MSP-02** | 「按容量选档」= 选最小的 `capacity >= kept` 的档（§6.3） | 该规则只压溢出不压欠填。kept=82：28 页容量 81（填充率 0.99，溢出 1）vs 32 页容量 116（填充率 0.71，溢出 0）。PRD 选后者，而 `place.py` 的 `DENSE_MIN_SLOTS = 5` 会在欠填时成批丢密页 | **与 §7 互相拆台 · BLK-MSP-02** |
| **F-MSP-03** | `magazine-8-standard` 是本波新 id | 已存在：`tests/unit/layout_engine/fixtures/editorial_series/magazine-8-standard.yaml`（`pageCount: 8`、`photo_span: [8, 16]`、容量 21、`patternId` 为 `page-hero-1` / `page-pair-2` 等不存在的脸），并被 `test_load_official_series_skips_folio_prefix`、`test_compose_items_match_screens_when_stub_can_cover` 引用 | **同名两本 · BLK-MSP-03** |
| **F-MSP-04** | `LTE_SLOT_MAX` 与 `V-P16-12` 从 9 抬到 10 即可放行 `page-10-grid-port`（§3.5） | `validator.py` 是游记与作品集共用校验器；`V-P16-12` 是 `level="block"` 的全局闸。同文件已有 `_dense_freeze_exempt()` 给出按 `page-*` 前缀定向豁免的先例（LTN R-A3） | **全局松绑 · BLK-MSP-04** |
| **F-MSP-05** | `photo_span` 降级为「只管文案与工坊校验」（D-MSP-07） | `config/edition.py` `min_kept_for_portfolio()` 用 `catalog_min`（来自 `catalog.min_photo_span_lo()`，即 `photo_span[0]`）作导入向导置灰阈值——这是功能闸门，不是文案 | **字段双身份未清 · BLK-MSP-05** |
| **F-MSP-06** | AC-MSP-16 三档 `patternId` 序列各自等于对应档页序 | AC-MSP-20 同时要求 `demotedPages` 可不为 0；`place.py` 现有 solo→hero 兜底会改写 `patternId` | **两条 AC 互斥 · BLK-MSP-06** |
| **F-MSP-07** | 升格八档，产物入库（§5.2 / BE-MSP-06） | 其中一档是 `magazine-16-standard`——PFM P0 金样，AC-PFM-08/12/29/31 与 `test_as_pfm_03_folio16_matches_official_p0_faces` 全部依据它。RSC 铁律 4 有「禁止默认盖 `folio-16-standard`」的工坊侧对偶，运行时侧无此约定 | **金样可被自己盖掉 · BLK-MSP-07** |
| **F-MSP-08** | 八档容量构成连续阶梯（§5.2 尾行） | 实测：27 / 36 / 53 / **72 / 73** / 81 / 116 / 134。20 页与 24 页只差 1 张容量，却差 4 页；张/页密度 3.6 vs 3.0，24 页更长更疏 | **阶梯退化 · BLK-MSP-08** |
| **F-MSP-09** | 九芯片平铺、纯数字即可（D-MSP-10 / §8.2） | 前端 `pageCountChipOptions()` 现在就是 `{ id, label }` 结构，label 直接取数字字符串；加副文需要扩结构 | **无选择依据 · BLK-MSP-09**（加席主诉） |
| **F-MSP-10** | `sequenceFulfillment` 加进 `studio.portfolio` 即可 | `schemas/trip.schema.json` `tripStudioPortfolio` 是 `additionalProperties: false`，现有属性仅 `seriesId` / `pageCount` / `pageCountSource` / `density` / `photosPlaced` / `photosKept` / `overflow` / `match` | **属实 · 保持**。须显式加 `$defs` 分支，PRD 附录 A 已列 |
| **F-MSP-11** | 只缺 `page-10-grid-port` 一张脸 | 逐本比对八本页序 faceHint 对 75 份运行时 `page-*.yaml`：唯一缺项确为 `page-10-grid-port`，被 `folio-32-standard-r2` / `folio-36-standard` 引用 | **属实 · 保持** |
| **F-MSP-12** | 八本 id / `pageCount` / `sequence` 长度自洽 | 逐本核对全部一致（含 `folio-24-standard` 已是 24 页，与 AS-PFM-03 对账记录相符） | **属实 · 保持** |
| **F-MSP-13** | 五处页数上限须同步抬 | 核实：`config/edition.py PAGE_COUNT_MAX`、`config/studio.py max_pages`、`match.PAGE_COUNT_CHIPS`、`schemas/trip.schema.json pageCount.maximum`、`match.{catalog_page_count_chips,select_series}` 的 `max_pages` 过滤 | **属实 · 保持** |
| **F-MSP-14** | 靠档梯子补到 48 不会多出芯片 | `catalog_page_count_chips()` 只回目录中真实存在且 `<= max_pages` 的 `pageCount`，梯子仅供 `snap_to_chip()` | **属实 · 保持** |
| **F-MSP-15** | 16 页页序只兑现 11 页（§1.5） | `place.py` `DENSE_MIN_SLOTS = 5` 丢密页 + solo→hero 兜底改写 `patternId`，与 `demo-f90d82b3a5` 实测一致 | **属实 · 保持**。本波要修的正是这条 |

---

## 4. Must-Fix（回写 v0.3.0 前不批无条件 Go · 不批 W1 合码）

| ID | 挡哪一波 | 要求 |
|----|----------|------|
| **BLK-MSP-01** | W1 落点 | **升格工具改为独立编译期脚本，不进任何运行时包的导入图。** 落点从 `travelogue/layout_engine/editorial_series/promote.py` + `layout_templates/cli.py` 子命令，改为 `scripts/promote-series.py`（或 `tools/`），用 `yaml.safe_load` 直接读工坊 YAML 与 `travelogue/layout_templates/templates/page-*.yaml`、直接写 `travelogue/layout_engine/editorial_series/series/*.yaml`，**不 import `travelogue.layout_engine.editorial_series`，也不 import `travelogue.layout_templates`**。理由见 F-MSP-01：现有 import-linter 契约「PFM editorial_series isolation (D-U-15 / ISO-05)」明文禁止该方向，且该契约是 PFM 评审产物，**不得为本波松绑或加 ignore**。§5.1、§10.1 BE-MSP-01/02、附录 A 同步；新增 AC 断言「`import-linter` 全绿且契约文本未被修改」。 |
| **BLK-MSP-02** | W1 选档 | **选档目标函数改为看填充率，不只看装得下。** 现文「最小的 `capacity >= kept`」只压溢出（F-MSP-02）。改为：在候选档中取**填充率 `kept / capacity` 落入 `[0.85, 1.05]` 且页数最小**者；无候选时，比较「最接近的欠填档」与「最接近的溢出档」，**溢出 ≤ 5% 时优先选溢出档**（页序几乎全兑现，代价是明示少收几张），否则选欠填档。§6.3 的样例表按新规则重算（kept=82 应落 28 页而非 32 页），AC-MSP-10 同步重写并补 82 这个判别式样例。填充率同时进 `sequenceFulfillment`。 |
| **BLK-MSP-03** | W1 入库 | **消除 `magazine-8-standard` 同名冲突。** 把测试夹具 `tests/unit/layout_engine/fixtures/editorial_series/magazine-8-standard.yaml` 改名为 `magazine-8-sparse.yaml`（`sparse` 是 `MAGAZINE_ID_RE` 合法密度，且本波不产 `sparse` 档，不会二次撞车），同步改 `test_load_official_series_skips_folio_prefix`、`test_select_series_*`、`test_compose_items_match_screens_when_stub_can_cover` 的引用与断言。理由见 F-MSP-03：真书容量 27 / `photo_span [24,40]`，假书容量 21 / `[8,16]`，同 id 两本会在排障时长期互相冒充。§9 加一行。 |
| **BLK-MSP-04** | W1 脸解锁 | **不抬全局槽数上限，改按 `page-*` 定向豁免。** `validator.py` 的 `V-P16-12`（≤9，`level="block"`）是游记与作品集共用闸（F-MSP-04），不得为一张脸抬到 10。改为沿用同文件 `_dense_freeze_exempt()` 的写法：`page-*` 前缀的脸上限放到 10，其余模板仍 ≤9；`page_promote.py` 的 `LTE_SLOT_MAX` 同样改成「`page-*` 走 10、其余 9」；`intake.slot_band_from_role` 的 `min(band, 8)` 抬到 10 时须同时断言「烘焙值 == 脸真实槽数」，不靠上限兜。新增 AC 断言「非 `page-*` 模板槽数 >9 仍 block」。 |
| **BLK-MSP-05** | W0 契约 | **`photo_span` 的双身份要清干净。** D-MSP-07 宣布它只管文案，但 `min_kept_for_portfolio()` 正拿它的下界当导入向导置灰的功能闸门（F-MSP-05）。二选一写死：(a) 置灰阈值改由最小 `capacity` 派生（八档最小 = 27），`photo_span` 彻底退出功能路径；(b) 保留 `photo_span[0]` 作阈值来源，但在 D-MSP-07 里明写「下界仍是功能值，只有上界退化为建议」。评审倾向 **(a)**——一个字段一个身份。AC-MSP-14 的数字随裁决改（24 → 27）。 |
| **BLK-MSP-06** | W2 验收 | **AC-MSP-16 与 AC-MSP-20 的互斥要解开。** 改 AC-MSP-16 口径为：三档产出的 `patternId` 序列互不相同，且**每一档与其页序的差异集合恰好等于该次装配的 `demotedPages` + `droppedRoles`**（即允许降级，但降级必须被诊断字段完整解释，不允许出现无法归因的偏离）。这样 QA 有单一判据，且降级不再能藏。 |
| **BLK-MSP-07** | W1 入库 | **P0 金样防覆盖。** 升格工具默认**拒绝**写已存在的 `magazine-*.yaml`，覆盖须显式 `--overwrite <id>`；`magazine-16-standard` 额外列入保护名单，覆盖它须 `--overwrite magazine-16-standard --i-know-this-is-the-p0-gold-sample` 双确认，且产物必须先通过与旧文件的逐页 `patternId` diff 打印（F-MSP-07）。这是 RSC 铁律 4 在运行时侧的对偶。新增 AC 断言「不带 `--overwrite` 时重复升格是 no-op 且退出码非 0」。 |
| **BLK-MSP-08** | W0 数据 | **20 页 / 24 页阶梯退化要有处置。** 实测容量 72 / 73（F-MSP-08），差 1 张却差 4 页，24 页那本 3.0 张/页明显比 20 页的 3.6 更疏。升格闸门新增 **GATE-10：相邻档容量差 < 该档页数**（即每多一页至少多带一张容量）时红灯，逼出数据问题；本波对 24 页这一本，二选一：(a) 运营调整 `folio-24-standard` 页序补密（首选）；(b) 本波先不升 24 页，留七档。禁止「知道退化但照升」。 |
| **BLK-MSP-09** | W2 前端 / 产品 | **芯片必须给选择依据，并在钉小档时事前拦。** 加席实测：九个纯数字等于一个选项（F-MSP-09）。两件事一起做：① 芯片扩为「数字 + 一行副文」，副文由 `capacity` 派生（例「12 页 · 约 36 张」），`pageCountChipOptions()` 返回结构加 `hint` 字段；D-MSP-10「平铺不分组」保持，但不再是「纯数字」。② 当所选档 `capacity` 小于 kept 的 60% 时，**点下去之前**出一次轻确认：「这一档只收 27 张，你有 180 张。要更厚的一本吗？」并给出推荐档一键切换——不允许只在事后角标里说。AC 新增两条覆盖副文与事前拦。 |

---

## 5. Should-Fix（不挡 Kickoff）

| ID | 说明 |
|----|------|
| **SHD-MSP-01** | 手动钉档与兑现率兜底的优先级要写明（狗粮席）：**手动钉档不被兑现率逻辑改写**——钉了 12 页就给 12 页，宁可留空洞，然后提示「有 3 页没排满，换 8 页会更饱满」把决定权还给用户；只有 `pageCountSource == "auto"` 才允许系统换档。D-MSP-09 第二级补一句作用域。 |
| **SHD-MSP-02** | `page-10-grid-port` 的移动端重排要一并签（视觉席）：`page_promote.py` 给每张脸都声明 `mobile 9:16` 变体，十个 3:4 竖槽在 9:16 下怎么排 PRD 未写。AS-MSP-03 的签收范围扩到含移动端实样。 |
| **SHD-MSP-03** | BE-MSP-03 估时 1.0 → **2.0 天**（开发席）：10 槽 5×2 的轨道推导 + `intentionalGaps` + CSS 重生成 + `test_asset_version` 金样回写，参照上一次改 `css_gen.py` 的实际耗时。 |
| **SHD-MSP-04** | BE-MSP-05 拆成两条（开发席）：`capacity` 字段烘焙与选档目标函数重写风险不同源，合成一条会互相拖延。 |
| **SHD-MSP-05** | §9 漏了一条会红的测试（QA 席）：`test_compose_items_match_screens_when_stub_can_cover` 断言 `load_official_series()` 只有 `magazine-16-standard` 且 `photo_span == [48, 80]`，八档入库后必红。补进表。 |
| **SHD-MSP-06** | `sequenceFulfillment` 字段体积要克制（架构席）：只落 `plannedPages` / `renderedPages` / `fillRatio` / `demotedPages` 四个标量 + `droppedRoles` 短列表，不落逐页明细，避免 `trip.json` 膨胀与快照噪声。 |
| **SHD-MSP-07** | 运营复核 24 页那本是否偏疏时，顺带核 20 页 / 24 页在工坊试印下的观感差异（视觉 + 运营），避免用户在这两档之间只感受到「更空」。 |
| **SHD-MSP-08** | W3 狗粮沿用 PFM 的盲评法（`pfm-blind-review-TEMPLATE.md`）：同一相册出 8 / 12 / 24 三册，隐藏来源，三问定量——「这三本是不是三种编排」「哪一本最像一本书」「有没有哪页看起来是凑的」。不要停在主观描述。 |

---

## 6. 七个已关闭 OQ 的复核

产品已于 2026-08-21 关闭 OQ-MSP-01～07。本场**不重投方向**，只核「落法是否成立」。

| ID | 产品裁决 | 评审复核 | 处置 |
|----|----------|----------|------|
| **OQ-MSP-01** | (b) `photo_span` / `capacity` 拆两字段 | **成立 · 但未拆干净** | `photo_span` 下界仍是功能闸门 → BLK-MSP-05 |
| **OQ-MSP-02** | (a) 按容量选档 | **方向成立 · 目标函数错** | 只压溢出不压欠填 → BLK-MSP-02 |
| **OQ-MSP-03** | (c) 填充组 + 换档两级叠加 | **成立** | AC-PFM-09 定向放宽 + 双向断言的写法评审一致称好，保持 |
| **OQ-MSP-04** | (c) 上限抬 48 | **成立** | 五处已核实无遗漏（F-MSP-13）；梯子不外溢芯片已核实（F-MSP-14） |
| **OQ-MSP-05** | (a) 32 / 36 与前六档同波 | **有条件成立** | 依赖 `page-10-grid-port`，而解锁方式要改（BLK-MSP-04）、移动端未签（SHD-MSP-02）。同波保持，但**该脸不过 AS-MSP-03 则退回先上六档**，且 24 页受 BLK-MSP-08 影响可能变七档 |
| **OQ-MSP-06** | (a) 兑现不了自动换档 + 告知 | **成立 · 需限作用域** | 自动档可换，手动钉档不可 → SHD-MSP-01 |
| **OQ-MSP-07** | (a) 九芯片平铺 | **成立 · 但不能是纯数字** | 平铺保持，副文必加 → BLK-MSP-09 |

---

## 7. 新增开放问题（回写 v0.3.0 时须带答案）

| ID | 问题 | 会中倾向 |
|----|------|----------|
| **OQ-MSP-08** | 填充率窗口 `[0.85, 1.05]` 的上界（允许 5% 溢出换页序兑现）是否可接受？ | 可接受。少收 4 张换一本完整编排，比多 4 页空档好解释（BLK-MSP-02） |
| **OQ-MSP-09** | 24 页那本走「运营补密」还是「本波先不升，留七档」？ | 先问运营排期；补密来不及就留七档，不带退化档出门（BLK-MSP-08） |
| **OQ-MSP-10** | 导入向导置灰阈值改由 `capacity` 派生（27）还是保留 `photo_span[0]`（24）？ | 由 `capacity` 派生，一个字段一个身份（BLK-MSP-05 倾向 a） |
| **OQ-MSP-11** | 升格脚本放 `scripts/` 还是 `tools/`？仓库现有约定为何？ | 跟现有 `scripts/` 一致即可，本场不纠 |

---

## 8. 本场关闭 / 保持

| 项 | 处置 |
|----|------|
| D-MSP-01 八档全量入库 | **保持 · 可能变七档**（BLK-MSP-08） |
| D-MSP-02 编译期升格 | **保持 · 落点改**（BLK-MSP-01） |
| D-MSP-03 `-r2` 进 `version` | **保持** |
| D-MSP-04 上限抬 48 | **保持** · 五处已核实 |
| D-MSP-05 32/36 同波 | **保持 · 带门**（AS-MSP-03 + BLK-MSP-04） |
| D-MSP-06 显式烘焙 `slotBand` / `patternId` | **保持 · 硬化** · 烘焙值须断言等于脸真实槽数（BLK-MSP-04 尾） |
| D-MSP-07 `photo_span` / `capacity` 拆字段 | **保持 · 未拆干净**（BLK-MSP-05） |
| D-MSP-08 按容量选档 | **改** · 目标函数换成填充率（BLK-MSP-02） |
| D-MSP-09 三级兜底 | **保持 · 限作用域** · 手动钉档不被换档（SHD-MSP-01） |
| D-MSP-10 目录驱动 + 平铺 | **保持 · 加副文**（BLK-MSP-09） |
| D-MSP-11 只做 `standard` | **保持** · 本场无人要求重开 |
| D-MSP-12 `_promotedFrom` 可追溯 | **保持** · 配合 BLK-MSP-07 的 diff 打印 |
| D-MSP-13 AC-PFM-09 定向放宽 | **保持** · 评审一致认为「只放宽作品集侧 + 双向断言」是本文最稳的处理 |
| G-MSP-01～06 | **保持** |
| N-MSP 全部非目标 | **保持** · 本场无人要求重开 |
| 加席典型用户 | **本场关闭**：主诉已写入 BLK-MSP-09 与 SHD-MSP-01 |

本场 **不关** AS-PFM-03（要等八档真的入库且 GATE 全绿才能从「对账完成 · 不升格」翻成「已升格」）。**不动** import-linter 任何契约文本。

---

## 9. 出门顺序（回写后）

```
v0.3.0 回写 BLK-MSP-01～09（落点 · 选档目标函数 · id 撞车 · 定向豁免 · 字段双身份 · AC 互斥 · 金样防覆盖 · 阶梯退化 · 芯片副文）
  → 运营回话：folio-24 补密排期（OQ-MSP-09）
  → W1a：scripts/promote-series.py + 上限 48 + capacity 烘焙 + 六档（8/12/16/20/28/32）入库
  → W1b：填充率选档 + 既有测试回写 + import-linter 复跑
  → AS-MSP-03 签 page-10-grid-port（含移动端实样）→ 放行 36 页
  → W2：填充组 + 兑现率兜底 + sequenceFulfillment + 芯片副文与事前拦
  → W3：狗粮三册盲评（8 / 12 / 24），三问定量
```

**W1 出门硬门**：GATE-01～10 全绿 · `import-linter` 全绿且契约未改 · `magazine-16-standard` 未被覆盖 · `test_editorial_series.py` / `test_atelier_series_audit.py` / `test_studio_entry.py` 三处回写完成。在此之前，界面不得出现 8 / 12 之外未验证的档位芯片。

---

## 10. 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0 | 2026-08-21 | 首场七席 + 典型用户加席。8/8 Conditional Go。BLK-MSP-01～09；复核产品已关闭的 OQ-MSP-01～07（其中 02 目标函数改判、01/06/07 加限）；新增 OQ-MSP-08～11。PRD 仍为 v0.2.0，待回写 v0.3.0。 |
