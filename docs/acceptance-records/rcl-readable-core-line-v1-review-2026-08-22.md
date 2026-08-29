# PRD-READABLE-CORE-LINE-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-READABLE-CORE-LINE-V1.md](../PRD-READABLE-CORE-LINE-V1.md)（**RCL** · 可读主链）审的是 **v0.1.0**；本纪要 Must-Fix 回写 **v0.2.0** |
| **上游合同** | [DPI](../PRD-DUAL-PIPELINE-ISOLATION-V1.md)（窄缝 / 身份 / 分发 · **不重开**）· [dual-pipeline-ownership.md](../dual-pipeline-ownership.md) |
| **前序纪要** | [DPI 七席 2026-08-22](./dpi-dual-pipeline-isolation-v1-review-2026-08-22.md)（同日 · Conditional Go · W0–W3 已合入） |
| **日期** | 2026-08-22 |
| **结论** | **有条件通过（Conditional Go）**。切口成立：主链「可审计不可阅读」，拆核 + 热路径类型 + 活路径清单是对的排序。**BLK-RCL-01～10 回写 v0.2.0 前：不批 W1 开工 · 不批 AC-RCL-19 作为出门硬门 · 不批「TypedDict ⊆ schema」按原文执行 · 不批 `build_render_context` ≤120 行。** W0 在回写 BLK-RCL-05 / 06 / 09 后可开工。 |
| **编码** | ☑ 现状实测（行号级）　☑ OQ 裁决　☑ v0.2.0 回写　☑ W0 门禁　☐ W1 拆核 |
| **参评角色** | **七席**：产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD v0.1.0 §0～§14，对照现网（`curate.py` / `assemble.py` / `journal_chapters.py` / `context_types.py` / `schemas/trip.schema.json` / `lint_csc_god_module_ratchet.py` / `pyproject.toml` import-linter / `ci.yml` / `studio-home-v2.html` / `journal-screens.css` marker） |
| **本纪要状态** | **已结案 · Conditional Go** · BLK 已回写 v0.2.0 · **W0 可按 PRD §0.3 开工清单开工** · **无 C 端加席** |
| **审查基线** | 零行为是本波唯一产品承诺 · 不新开 DPI 窄缝 · 「拆得更薄」不等于「读得更懂」：把 467 行循环原样搬进 `journal_screens.py` 只是换房间 · **行数门不能再拍一次 DPI 已经否决过的空数字** |

---

## 0. 会前宣读（主持人）

1. **切口**：DPI 刚把身份 `if` 收到 S-01 / S-04，边界可读。主链三个编排核仍是 536 / 467 / 616 行，下一波功能只会继续往里塞。本场不重开「要不要做可读性」。
2. **已拍（勿重开）**：零行为；不复制 `curate.py`；不重写 mosaic / planner；不拆第三份 CSS；不把身份分发下沉到阶段模块；不做全仓库函数行数门。
3. **勿重开**：档位 / 兑现率（MSP）；`page-*` 几何（TSU）；DPI 窄缝表与 CSS 分族。
4. **本场必拍**：`titleArt` 不在 schema 时 W2 合同怎么成立；`build_render_context` ≤120 会不会逼出空拆；注释门会不会假绿；`curate.py` 已有 god-module 棘轮怎么交接；11 人天零用户价值的排期硬门。
5. **本波无 C 端可见变更，不设典型用户加席。** 用户体验席保留「活路径说错会误删正在跑的 JS」的否决权。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go。** 这份 PRD 最大的优点是它没有把「可读性」写成口号——三个编排核带了 AST 行数，§1.4 主动纠正了「v3 是死代码」的误判，DPI 边界表写清楚了「拆的是阶段、不是第二扇身份门」。门禁先行、W0 当天能绿，排序也对。但 v0.1.0 有十处按原文 Kickoff 会撞墙或假绿，其中一处是 W2 方向级的：`meta.titleArt` 是热路径第一批，而 `schemas/trip.schema.json` 的 `meta` 是 `additionalProperties: false` 且**没有** `titleArt` 键——AC-RCL-20「字段 ⊆ schema」按原文要么逼 RCL 去改 schema（越权），要么 W2 一写单测就红。其余硬伤：`build_render_context` ≤120 行无视 `TripRenderContext` 近 80 个键的组装面（DPI 刚用 BLK-DPI-08 否决过同类行数拍脑袋）；注释横幅门「只扫新增」没定义 git base，CI 会空转；新 `journal_folio.py` / `journal_screens.py` 不进既有 import-linter 源列表，DPI 隔离合同对它们隐形；`curate.py` 已在 CSC god-module 棘轮内（基线 1986，工作区 2014），W1 提取必须同 PR 下调基线，PRD §10 只字未提；AC-RCL-19「没读过书法 PRD 的人 90 秒能讲清」不能当出门硬门。关 BLK 后升 v0.2.0。**W0 回写排期门 / 活路径根 / 注释门定义后可开工；W1 必须等提取相关 BLK 回写。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「零行为 + 拆核不拆壳」我签。11.4 人天对用户仍是零可见价值，且就在 DPI 同日合入之后——不设排期门就会排到永远。我要 **G-RCL-01**：下一支**功能** PR 若改 `assemble.py` / `journal_chapters.py` / `_stage_build_chapters_compose`，W0 必须已合入。W1–W3 允许延后，但每次延后在 PRD 状态行记一笔。§13.3 的四处代价够用，不用再编用户故事。 |
| **算法** | **Conditional Go** | 本波不碰阈值，我确认。`compose_stages.py` 要搬走的剥异常 / 打分权重必须是**原样搬家**，`peel_time_outliers` 的「≥2 才剥离」是现网语义，提取时改数字 = 本波失败。`titleArt` 不在我这，但夹具纪律沿用 DPI：不要为了 TypedDict 单测去读 `phase16-dogfood`。 |
| **架构** | **Conditional Go** | 阶段模块零身份 `if`、S-01/S-04 不搬家，模型对。两处方向问题：① **D-RCL-07 与 D-RCL-08 互相打架**——热路径钉 `titleArt`，权威又钉 schema，而 schema 没有这个键（F-RCL-01）。正确口径是：TypedDict 覆盖**运行时 trip.json 事实 + 具名合同**，schema 未列字段标 `runtime`，**禁止**本波扩 `trip.schema.json`。② **≤120 行是第二次拍空数字**。`TripRenderContext`（`context_types.py:300-379`）键太多，组装返回值就会把编排核顶破；请改成结构判据 + 更宽上限，或允许 `return TripRenderContext(**bundle)` 一次组装。另外新 journal 模块必须进 DPI import-linter 的 `source_modules`，否则隔离合同对拆出去的文件隐形（IE-DPI-04 刚教过）。 |
| **开发** | **Conditional Go** | 任务表能开，W0 / W1 分开我赞成。四处要调：① `curate.py` 已在 `lint_csc_god_module_ratchet.py` 里，基线 **1986**、现文件 **2014**——W1 提取会降行数，必须同 PR `--update-baseline`（只降，不要 `--allow-growth`）；§10 漏了，漏了会红。② import-linter 现在只扫 `journal_chapters`（`pyproject.toml:185`），`journal_folio` / `journal_screens` 同一提交要加进源列表。③ `build_render_context` 上限 120 我核过组装面，过不去除非把返回值再藏一层；我建议 **≤160** 且结构判据优先。④ W1 三核 4.5 d 在「指纹零 diff + 先搬后整理」下偏紧，记 SHD，不挡。注释门不要做成「扫描 git 新增」——做成 **RCL 新模块允许清单** 的文档字符串行数即可。 |
| **测试 / QA** | **Conditional Go** | 形状 + 指纹 + 反向验证（故意加身份 `if` 要红）是对的。三处假绿 / 不可测：① AC-RCL-20 ⊆ schema **现网就不成立**（F-RCL-01）。② AC-RCL-19 是主观抽查，不能进 `test-pr`，降为 SHD，W3 收口纪要写 90 秒走读即可。③ D-RCL-11「只扫新增横幅」没有 merge-base，CI 对文档/脚本 PR 会空转——改成允许清单。另：AC-RCL-10/11 的 `render_fingerprint` 是 **trip 载荷**（`render_fingerprint.py:31-51`），W3 改 CSS 文件头动的是 `?v=` / `test_asset_version`，不要写成「指纹因目录注释而变」。 |
| **视觉 / 排版** | **Conditional Go** | 不拆 CSS 文件我签。W3 目录必须写死：**落在 `@lte-generated` / `@journal-overlays` 之外、文件最顶**。`journal-screens.css:147` 起是生成区，`:1430` 起 overlays 会被 `export --sync-journal` 换掉——目录写进去等于没写。加一条 AC：sync 之后目录还在。`portfolio-pages.css` 同理。目录本身会 bump `test_asset_version`，沿用「W3 一次」纪律。 |
| **用户体验 · 狗粮** | **Conditional Go** | §1.4 纠正 v3 误判，这正是我怕的：没有活路径表就会有人把正在跑的 sheet/dock 当遗物删。闭包根请写死：`templates/studio/preview-toolbar.js` **和** `templates/studio/homepage-v2/bootstrap.js`（`studio-home-v2.html:11,770` 已 preload + module）。§7.2 十个文件漏了首页入口，补上。AC-RCL-19 我可以做一次走读，但那是收口记录，不是红灯。 |

**汇总**：**7/7 Conditional Go**。未回写 Must-Fix 前 **不批 W1** · **不批 AC-RCL-19 硬门** · **不批 TypedDict ⊆ schema 原文** · **不批 assemble ≤120**。**W0 在回写 BLK-RCL-05 / 06 / 09 后可开工。**

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 三个核、活路径误判、过期架构图都有实证；成功标准 §2.3 清楚 |
| 与现网代码对齐 / 防假绿 | **5** | 行数盘点准；漏 schema 缺口、god-module 棘轮、import-linter 源列表、注释门空转 |
| 与 DPI 边界 | **9** | 不重开窄缝、分发不搬家，是本文最稳的一处 |
| 可读性彻底性 | **6** | 编排核会变薄；屏循环搬家后仍可能 >200 行，合同已承认但没钉「搬家后仍要可读」 |
| 工程可开工性 | **7** | W0 可开；W1 有三处会当天红 |
| AC 可测性 | **5** | 反向验证好；AC-RCL-19/20 按原文不可执行 |
| 排期 / 不做的代价 | **7** | §13.3 有实证；缺「何时必须做」硬门 |

---

## 3. 事实核查（对照现网 · 影响结论）

| # | PRD v0.1.0 假设 | 代码事实（2026-08-22） | 会中 |
|---|-----------------|----------------------|------|
| **F-RCL-01** | AC-RCL-20 / D-RCL-07：热路径字段 ⊆ `trip.schema.json`；`titleArt` 可钉 | `meta` 为 `additionalProperties: false`（`trip.schema.json:2509-2511`）；属性含 `coverSecondaryAssetId`（2590），**全文件无 `titleArt`**。CAL 运行时写入 `trip.meta.titleArt`，与 schema 长期漂移 | **W2 方向级 · BLK-RCL-01** |
| **F-RCL-02** | 新 `journal_*.py` 自动受 DPI 隔离门保护 | import-linter「DPI journal render isolation」`source_modules` **只有** `travelogue.render.journal_chapters`（`pyproject.toml:184-186`） | **拆文件即漏门 · BLK-RCL-02** |
| **F-RCL-03** | §10 已列全会红测试 | `lint_csc_god_module_ratchet.py` 钉 `curate.py` 行数；基线 **1986**（`csc-w2b-god-module-ratchet-baseline.json`），现文件 **2014**。W1 提取必须下调基线，否则下一步功能再长会更乱；漏列会让 W1 CI 红或该门空转 | **漏棘轮交接 · BLK-RCL-03** |
| **F-RCL-04** | `build_render_context` ≤120 可执行（§5.4） | 函数现 536 行；返回值型 `TripRenderContext` 约 80 键（`context_types.py:300-379`）。纯组装返回即可 >100 行。DPI BLK-DPI-08 刚否决过「`chapters.py` ≤120」 | **数字无依据 · BLK-RCL-04** |
| **F-RCL-05** | 注释横幅 lint「只扫新增」可在 W0 棘轮 | CI 无「本波新增文件」定义；`ci.yml:12-20` 还 ignore `**.md` / `.cursor/**`。无 merge-base 的「新增」扫描 = 空转或误伤 | **门会假绿 · BLK-RCL-05** |
| **F-RCL-06** | R-RCL-05「W0 可单独合入」足够当排期 | 同日 DPI 刚用 G-DPI-06 才把隔离波排上。RCL 全文无「下一支功能 PR 何时必须先有 W0」 | **无排期门 · BLK-RCL-06** |
| **F-RCL-07** | CSS 文件头目录（≤10 行）即可 | `journal-screens.css:147` `@lte-generated:start`，`:1430` `@journal-overlays:start`，overlays 会被 `export --sync-journal` 替换。目录若写进生成/覆盖区会丢 | **落点未钉 · BLK-RCL-07** |
| **F-RCL-08** | AC-RCL-19 可作出门验收 | 「未读过书法 PRD 的开发 90 秒能定位」无机器判据，也不能进 `test-pr` | **不可测硬门 · BLK-RCL-08** |
| **F-RCL-09** | 活路径闭包根写「preview-toolbar.js 与 homepage-v2/bootstrap.js（或现网真实入口）」 | 首页真实入口已钉死：`studio-home-v2.html:11,770` → `/__studio/homepage-v2/bootstrap.js`。§7.2 必打文件头名单漏了它 | **根未写死 · BLK-RCL-09** |
| **F-RCL-10** | AC-RCL-10/11 指纹零 diff 覆盖拆核与 CSS 目录 | `trip_render_fingerprint_payload` 只摘要 trip 字段（`render_fingerprint.py:31-51`），**不含** CSS 字节。W3 目录注释动 `?v=` / `test_asset_version`，不动指纹 | **判据混用 · BLK-RCL-10** |
| **F-RCL-11** | 三核行数 536 / 467 / 616 | 2026-08-22 AST 实量与 PRD 一致 | **属实 · 保持** |
| **F-RCL-12** | `preview-toolbar-v3-*` 是活路径 | `preview-toolbar.js` → `init-v3.js` → `preview-toolbar-v3-sheet.js` / `preview-toolbar-v3-task-dock.js` | **属实 · 保持** |
| **F-RCL-13** | `assemble.py` 仅一处 `is_portfolio_trip` | `assemble.py:206` 一处 | **属实 · 保持** |
| **F-RCL-14** | 作品集 builder 已短，W1 不拆 | `portfolio_chapters.py` 约 110 行 | **属实 · 保持** |

---

## 4. Must-Fix（回写 v0.2.0 前不批 W1）

| ID | 挡哪一波 | 要求 |
|----|----------|------|
| **BLK-RCL-01** | **W2（方向级）** | **改 D-RCL-07 / AC-RCL-20，禁止本波改 `trip.schema.json`。** 热路径 TypedDict 的权威是：（1）schema 已列字段必须 ⊆ schema；（2）schema 未列但运行时已存在、且有具名合同的字段（本波仅 `meta.titleArt`，合同为 CAL D-CAL-09）标 `runtime`，允许进 `TripHot`。AC-RCL-20 改为：`studio.edition` / `chapters` 骨架 / `coverSecondaryAssetId` ⊆ schema；`titleArt` 有单测「缺字段不炸」+ 模块注释指向 CAL；**不**要求 `titleArt ∈ schema`。schema 补洞另开 CAL/数据模型债，不进 RCL。 |
| **BLK-RCL-02** | **W1** | **新 journal 模块与 import-linter 同一提交。** `journal_folio.py` / `journal_screens.py` 加入「DPI journal render isolation」的 `source_modules`。禁止先建文件、后补契约（IE-DPI-04）。 |
| **BLK-RCL-03** | **W1** | **§10.1 补 CSC god-module 棘轮。** W1 提取 `compose_stages.py` 的同一 PR 必须下调 `csc-w2b-god-module-ratchet-baseline.json` 的 `curate.py` 行数（只降，不用 `--allow-growth`）。写明：本波目标是让 `curate.py` **低于** 现基线 1986，而不是把债挪走后假装没动棘轮。 |
| **BLK-RCL-04** | **W1** | **编排核上限改结构优先。** `build_render_context` 出门上限改为 **≤160**；允许最后一步 `return TripRenderContext(**bundle)`（bundle 在阶段函数里组）。`build_journal_chapters` ≤140、`_stage_build_chapters_compose` ≤160 保留。**结构判据**（升格为 AC）：编排核正文只含阶段调用 + 守卫 + 组装返回；封面印章切分 / 屏循环 / 剥异常细节不得留在核内。禁止为过门再拆空文件。 |
| **BLK-RCL-05** | **W0** | **注释预算门改允许清单，不扫「git 新增」。** 扫描对象 = W1 将建的阶段模块 + `types/trip_hot.py`（W0 可先把清单写进脚本，文件未存在则跳过）。文档字符串 >15 行红。不扫旧 `assemble.py` 横幅。 |
| **BLK-RCL-06** | **W0** | **G-RCL-01 排期硬门。** 下一支以产品功能为目的、且改 `assemble.py` 或 `journal_chapters.py` 或 `curate.py` 中 `_stage_build_chapters_compose` 的 PR，合并前 W0 必须已在主干。W1–W3 可延后，延后须在本 PRD 状态行记日期与原因。RCL 本身的 W1 不算「功能 PR」。 |
| **BLK-RCL-07** | **W3** | **CSS 目录落点写死 + AC。** 三份大 CSS 的目录必须在文件最顶、**第一个 `@lte-generated` / overlays marker 之前**。新增 AC：跑 `export --sync-journal`（及 portfolio sync）后，目录注释仍在且 marker 外。 |
| **BLK-RCL-08** | **W3 验收** | **AC-RCL-19 降为 SHD。** 90 秒走读写入 W3 收口纪要，不挡 merge、不进 CI。 |
| **BLK-RCL-09** | **W0** | **活路径闭包根写死。** 脚本常量只有：`templates/studio/preview-toolbar.js`、`templates/studio/homepage-v2/bootstrap.js`。§7.2 必打文件头名单加上 `homepage-v2/bootstrap.js`。删除「或现网真实入口」这种开口。 |
| **BLK-RCL-10** | **W1/W3 验收** | **指纹与 bundle 金样分开写。** AC-RCL-10/11 只约束 `render_fingerprint` 字段级（拆核不得动 trip 载荷）。W3 CSS 目录只允许触发 `test_asset_version` **一次** bump（已有 D-RCL-13），不得写成指纹变化。 |

---

## 5. Should-Have（不挡 W1，回写时一并处理）

| ID | 内容 |
|----|------|
| **SHD-RCL-01** | W1 三核估时各 +0.3 d 缓冲（指纹零 diff + 先搬后整理）。不改里程碑顺序。 |
| **SHD-RCL-02** | `journal_screens.py` 若阶段函数仍 >200 行：文件头顶 6 步大纲（每步一行），并列入附录 A 已知债。不挡 W1。 |
| **SHD-RCL-03** | W3 收口纪要附一次 90 秒走读（原 AC-RCL-19），点名 `assemble_cover.py` 贴纸守卫。 |
| **SHD-RCL-04** | `docs/readable-core-line.md` 加一行：改主链前先 `--explain` 新阶段文件。 |
| **SHD-RCL-05** | W1 提交信息带核名（`RCL W1 assemble` / `journal_chapters` / `curate`），便于按核回退。 |

---

## 6. 开放问题裁决

| ID | 问题 | 会议裁决 |
|----|------|---------|
| **OQ-RCL-01** | 是否顺手拆 `build_layout_screen`？ | **不拆**（七席一致）。附录 A 已知债。 |
| **OQ-RCL-02** | 是否删 `curate.py` 兼容别名墙？ | **不删**（一致）。只允许移到文件底 + 警告。 |
| **OQ-RCL-03** | 是否全仓库函数行数门？ | **否**（一致）。只棘轮三核。 |
| **OQ-RCL-04** | `TripHot` 是否改 dataclass？ | **不要**（一致）。 |
| **OQ-RCL-05** | W1 是否必须七席？ | **本场已开。** W0：回写 BLK-RCL-05/06/09 后开发负责人可合。W1：须本纪要 BLK-RCL-02/03/04 已回写且 W0 已合入。 |
| **OQ-RCL-06** | `docs/README.md` 现行导读是否立刻加 RCL？ | **W0 合入且 v0.2.0 回写后再加 2b**（一致）。Draft 不加。 |

---

## 7. 里程碑放行条件（本纪要授权范围）

| 里程碑 | 放行条件 |
|--------|---------|
| **W0** | 回写 **BLK-RCL-05 / 06 / 09** 后**即可开工**（门禁定义、排期硬门、闭包根；零编排搬家） |
| **W1** | 须 **BLK-RCL-02 / 03 / 04 / 10** 已回写且 W0 已合入。三核串行，禁止同一提交 |
| **W2** | 须 W1 出门门全绿，且 **BLK-RCL-01** 已回写（否则类型波合同自相矛盾） |
| **W3** | 须 W2 合入；**BLK-RCL-07 / 08** 已回写。金样至多一次 bump |

**本纪要不关** 算法阈值、DPI 窄缝、CSS 分族、`longshot.js` 拆分。**不批**在本波顺手处理 `screen_planner.py` 算法核或 `build_layout_screen`。

---

## 8. 一页结论（对外）

**7/7 Conditional Go。** 做，但按 v0.2.0 做。

- **现在能做：** W0 地图 + 两条 lint（允许清单式注释门 + 写死的双入口活路径）+ `TECH-ARCHITECTURE.md` 刷新 + G-RCL-01。
- **现在不能做：** W1 拆核（等上限 / import-linter / god-module 交接回写）；W2 按「⊆ schema」去补 `titleArt`。
- **不要再争论：** 要不要做可读性；要不要拆 planner；v3 JS 是不是死的（不是）。
