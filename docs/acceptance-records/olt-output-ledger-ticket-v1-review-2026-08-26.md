# PRD-OUTPUT-LEDGER-TICKET-V1 · 七席 + 典型用户评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-OUTPUT-LEDGER-TICKET-V1.md](../PRD-OUTPUT-LEDGER-TICKET-V1.md)（**OLT** · 成品账本与票根副券）审的是 **v0.1.0 Draft** |
| **上游合同** | [架构重构交流备忘录](../架构重构交流备忘录.md)（本文 = 其 W1）· [EOI](../PRD-EXPORT-OUTPUT-ISOLATION-V1.md) · [PIS](../PRD-PORTFOLIO-IDENTITY-STARS-V1.md)（票根身份行 · **不得回退**）· [PFO](../PRD-PORTFOLIO-FLOW-OPTIMIZATION-V1.md)（页数口径 · stale 误报）· [DPI](../dual-pipeline-ownership.md)（窄缝 + 夹具）· [ADR-021](../adr/021-export-compose-dual-engine.md) |
| **前序纪要** | [PIS 八席 2026-08-26](./pis-portfolio-identity-stars-v1-review-2026-08-26.md) · [PFO 八席 2026-08-25](./pfo-portfolio-flow-optimization-v1-review-2026-08-25.md) |
| **日期** | 2026-08-26 |
| **结论** | **有条件通过（Conditional Go）**。切口成立：成品必须是实体、账本不进 `trip.json`、过期要比指纹不比 mtime、票根加副券。**按 v0.1.0 原文 Kickoff 会有七处假绿或反噬。** BLK-OLT-01～07 **须回写 v0.1.1**。仍不批无条件 Go · **不批 M1 开工**（须 01/03/05/07）· **不批 M2**（须 02/04/06）。 |
| **编码** | ☑ 分席只读 v0.1.0　☑ 对照现网　☑ **v0.1.1 回写**　☐ M1 |
| **参评角色** | **七席**：产品 · 架构 · 前端 · 平台（存储/API） · 渲染 · 导出 · 测试/QA · **加席**：典型用户（非从业者 · 现网走过「导长图 → 导小红书 → 导作品集页图」三种 · **本场否决权与产品同等**） |
| **评审方式** | 分席只读 OLT v0.1.0 §0～§15，对照 `studio_trips.py:_longshot_files/_LONGSHOT_FILE_PATTERNS/longshot_outputs_stale/_trip_rows`、`export/longshot.py:write_longshot_current/EXPORT_OUTPUT_DIRNAME`、`render/context.py:_bundle_version_paths/_longshot_bundle_version`、`config/platform_profiles.yaml`、`cli/render_cmds.py:--width/--height/with_custom_output`、`shelf.js:buildBook/buildCoverWrap`、`shelf-actions-logic.js`、`trips-client.js:SHELF_PAGE_SIZE=20`、PIS AMD-PIS-05 / AC-PIS-10、SFP D-SFP-09、DPI 夹具合同 |
| **记录人** | 八席联合纪要（跨职能模拟联评 · 2026-08-26） |
| **本纪要状态** | **已结案 · Conditional Go** · Must-Fix **已回写** [OLT v0.1.3](../PRD-OUTPUT-LEDGER-TICKET-V1.md) §0.4 · **M1 已落地** · [帧 A/B 已签](./olt-frame-ab-signoff-2026-08-26.md) · **M2 编码中** |
| **审查基线** | 备忘录四波顺序不重开 · 不按渠道切管线不重开 · 账本不进 `trip.json` 不重开 · PIS 票根身份行不得回退 · PIS 页数口径 X 不得被新数字破坏 · 窄缝须仍 12/14 · 加席「一张卡上两种说法我不知道信哪个」= Must-Fix |

---

## 0. 会前宣读（主持人）

1. **切口**：备忘录已裁「不按渠道切管线」「四波增量」。本场**只评 W1 = 成品账本 + 票根副券**。W2 身份值对象、W3 舞台注册表、W4 阶段图不重开。
2. **已拍（勿重开）**：账本落 `导出文件/outputs.json` 不进 `trip.json`（§3 六条理由八席无异议）；过期比三段指纹不比 mtime；本波零管线改动。
3. **本场必拍**：`outputId` 用 profile 够不够唯一；副券上那个数字会不会重犯 36/37；自愈要不要逐文件 stat；票根已有的徽章跟副券谁说话；开旗时序对不对；账本测试用谁的夹具。
4. **加席说明**：他不知道 profile / 指纹 / 账本 / 舞台。他只会问 —— 我导过的三种在哪、点了会不会跳错页、为什么这张写「已就绪」那张写「有更新」、33 和 32 到底哪个对、这些图占多少地方。他说「我不知道信哪个」，就是 Must-Fix。

---

## 1. 总评（一句话）

> **八席一致 Conditional Go：方向对 —— 成品必须是实体，glob 猜前缀该退休，过期该比指纹，票根该能挂多张副券，账本确实不能进 `trip.json`（否则每次导出当场自标过期，这条八席一致认为是全文最硬的发现）。** 但 v0.1.0 有七处按原文会假绿或反噬：（1）`outputId = profile` 不唯一 —— `custom` 可由 `--width/--height` 产生多种规格、`wechat_chat` 是 `chapter_or_full` 两种产物同一 profile，后导的会**静默吃掉**前一份；（2）副券写「作品集页图 33」，紧挨着身份行「作品集 · 32 页」，正是 PIS 用一整波锁掉的 36 vs 37，**加席当场否决**；（3）§4.5 逐文件 stat 自愈是性能反噬 —— `SHELF_PAGE_SIZE=20` × 3 成品 × `portfolio_pages` 最多 48 张 ≈ 2880 次 `stat()`/次书架加载，比现网 glob 更慢，R-OLT-06「净开销下降」的论断作废；（4）票根已有 SFP D-SFP-09 的 L1/L2 徽章序，其 stale 源是 mtime 的 `longshotStale`，副券用指纹判 outdated 后同一张卡会**两种说法并存**，**加席第二条否决**；（5）`export` 选项进 `structureFp`，调一次长图密度会把作品集页图也标有更新；（6）默认关旗到 M3 但 M2 前端要副券数据，M2 在默认配置下**无可测对象**；（7）账本/指纹单测的夹具归属未写，违 DPI 夹具合同。关 BLK 后升 v0.1.1；**M1 须先关 01/03/05/07；M2 须先关 02/04/06。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「一套作品多种成品、票根能看见」我签，这就是我提的东西被翻译对了。账本不进 `trip.json` 的理由我读懂了，签。**但副券上不许出现跟身份行打架的数字** —— PIS 刚花一整波把「页」锁成一个 X，现在票根上一边 32 一边 33，等于我自己推翻自己。副券只写名字，数字进详情。 |
| **架构** | **Conditional Go** | 窄缝零新增、`dispatch.py` 走已登记 S-07、账本写入 edition 无关、新模块分层干净（`domain/output_fingerprint.py` 只吃 stdlib），这几条我签。§9.1 那句「若必须加 edition 分支视为设计错误、回 PRD 重议」写得好，保留。**但 `outputId = profile` 是设计洞** —— `custom` 和 `wechat_chat` 都能在同一 profile 下产出规格不同的两份，账本会静默丢数据。另外复用 `_bundle_version_paths(trip)` 且禁用 `_BUNDLE_VERSION_PATHS` 旧名这条写得准，`AC-OLT-11/12` 当门。 |
| **平台（存储/API）** | **Conditional Go** | 原子写、严格校验、版本不符即回退、写失败即抛，都对齐 `write_longshot_current` 现网体例，签。`outputSummary` 服务端截断 3 条也对。**否两处**：① §4.5 每次读账本逐文件 `stat` —— 书架一页 20 本，作品集一条 48 张，最坏近三千次系统调用，比 `_longshot_files()` 的六组 glob 更贵，必须改成对 `导出文件/` 做一次 `os.scandir` 再集合比对；② 孤儿文件（导出中途失败写了 12/18 张）账本无条目、glob 有文件，§8.1 没裁定谁说话。 |
| **渲染** | **Conditional Go** | `bundleFp` 复用 `_bundle_version_paths(trip)`（`D-DPI-16` / `AC-DPI-18`）而不是那个 journal-only 的 `_BUNDLE_VERSION_PATHS` 常量，这个点抓得准，PFO 那次族错配就是这么来的。`BE-OLT-03` 只加公开访问器、逻辑零改、`_EXPECTED_BUNDLE_VERSION` 不变，签。**但 `structureFp` 把 `copyDisplay`/`breathMode`/`longshotDensity` 收进去是错的** —— 这三个只影响长图舞台，进了全产物共吃的那一段，等于调一次长图密度就让作品集页图集体标「有更新」，误报换了个姿势回来。 |
| **导出** | **Conditional Go** | 在 `dispatch.py` 成功点追加账本、失败不写、关旗零行为变化，颗粒度够开工。`platform_profiles.yaml` 只加 `surface:` 一行、规格零 diff（`AC-OLT-24`）我当门。**两处提醒**：① `wechat_chat` 的 `capture: chapter_or_full`、naming 是 `{title}-longshot|{title}-ch{nn}`，整卷和分章是**两种产物**；② `custom` 是 Phase C、CLI-only、`with_custom_output(width, height)` 可任意规格 —— 这两个都撞 `outputId`。`share_zip` / `pdf` 不在 profiles 里、label 本文新定义，这个交代清楚了，签。 |
| **前端** | **Conditional Go** | 零成品票面逐像素不变、副券行插在 serial 之后 code 之前、上限 3 + `+N`、纯函数落 `shelf-outputs-logic.js`，可开工。「副券点击不得冒泡到 `openTrip`」这条抓得对 —— `v2-shelf__open--meta` 确实覆盖整块 stub 并绑了 `openTrip`，`AC-OLT-16` 我当门。**否一处**：票根现在已经有 `分享图已就绪` / `分享图需更新` / `可重排` / `可先预览` / `正在准备高清图` 五种徽章，且 `SFP D-SFP-09` 明写「可重排不得压过 L1 分享图态」—— 这是个既有优先级合同。副券再带一套状态，同一张卡两个真相，本波必须裁定收敛，不接受并存。 |
| **测试 / QA** | **Conditional Go** | AC-OLT-01～10/13～17/20～24 可测，§5.5 那两条铁断言（只重渲染不得标更新 / 真改了必须标）写法很好，就是该当门的样子。**三处假绿**：① `AC-OLT-08` 说「只点重新渲染 → 全部 ready」，但没说清「重新渲染」是否会改 `trip.updatedAt` 以外的任何字段，`AC-OLT-10` 又单独测 `updatedAt`，两条要合并判据否则实现会各自解释；② `R-OLT-06`「净开销下降」没有基准数，无法验收，必须给 20 trip × 3 成品的实测门；③ **账本与指纹单测用谁的夹具没写** —— DPI 合同规定游记独占 `phase16-dogfood/**`、作品集独占 `editorial_series/**`、共享只有 `trip.render_golden.json`（克隆再注入 `edition` 合法）。账本要同时覆盖两身份，夹具策略不写就会有人去读对面的夹具，`pipeline_isolation` 当场红。 |
| **典型用户（加席）** | **Conditional Go · 两条否决** | 见 §2.1。总的说：我支持「我导过的三种在书架上能看见、点一下能打开文件夹」。**我否决两件事**：在写着「32 页」的旁边给我一个「33」；在同一张卡上一边说「分享图已就绪」一边说「有更新」。 |

**汇总**：**8/8 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go** · **不批 M1**（须 BLK-01/03/05/07）· **不批 M2**（须 BLK-02/04/06）。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **9** | G-OLT-01～06 每条都指到现网函数；§3 六条理由把「不进 trip.json」论死 |
| 与现网代码对齐 / 防假绿 | **6** | `_bundle_version_paths` / `open--meta` 冒泡 / `_BUNDLE_VERSION_PATHS` 三处抓得准；`outputId` 唯一性、逐文件 stat、既有徽章三处漏了 |
| 与 PIS / PFO / EOI / DPI 边界 | **6** | 窄缝零新增、EOI 不迁移不清理、身份行不动都守住了；**PIS 页数口径被新数字破坏**；DPI 夹具未交代 |
| 普通用户可走完一次 | **7** | 副券语义他一眼懂；33 vs 32 和双真相两处会停住 |
| 工程可开工性 | **8** | 任务颗粒度好，M1/M2/M3 + 降级路径清楚；开旗时序自锁 |
| AC 可测性 | **7** | 24 条大半可测；性能无基准、08/10 判据重叠 |
| 对前序合同的诚实 | **8** | 主动写了「不删任何现网代码」「关旗即回到今天」；徽章合同漏读 |

### 2.1 加席原话（本场权重最高）

典型用户（现网已对同一本导过长图、小红书、作品集页图三种）：

1. **「我导过的三种能看见，这个我要。」**
   「以前我导完小红书再导长图，书架上还是那句『分享图已就绪』，我不知道之前那份还在不在，只能自己去文件夹翻。票根上排三个小条，点一下打开文件夹 —— 这就够了，不用给我看别的。」
   → 签 §6 副券方向；**不否决**上限 3 + `+N`。

2. **「不要在 32 旁边给我一个 33。」**
   「上次你们已经改过一次了 —— 做好写 36 页、导出写 37 页，我以为少导一页。现在票根上面一行写『作品集 · 32 页』，下面小条写『作品集页图 33』，我又要算半天。名字给我就行，数字你们自己留着。」
   → **否决**副券显示文件数。BLK-OLT-02。

3. **「一张卡上两种说法，我不知道信哪个。」**
   「封面角上写着『分享图已就绪』，下面小条又标了个点说『有更新』。到底是好了还是没好？你们内部两个地方算的，别都摆给我看。」
   → **否决**双状态并存。BLK-OLT-04。

4. **「『有更新』之后我该干什么？」**
   「你告诉我旧了，但我点它是打开文件夹。那我到底在哪重做？」
   → 不否决（点副券开文件夹是他自己认同的），但要求「重新导出」入口必须在同一处可达。SHD-OLT-06。

5. **「这些图占多少地方？」**
   「导了七八次以后我担心硬盘。有个地方能看见占多少、能删掉旧的就行，不着急。」
   → 不挡。SHD-OLT-02 / SHD-OLT-03 保留。

6. **「『成品』『副券』这两个词我没听过。」**
   「小条上写『小红书』『长图』我懂。菜单里叫『管理成品』我大概能猜。别再造词了。」
   → 签 §6.4 禁令；「副券」不得进 C 端。SHD-OLT-09。

---

## 3. 事实核查（对照现网 · 影响结论）

| # | OLT v0.1.0 假设 | 代码 / 现网事实（2026-08-26） | 会中 |
|---|-----------------|-------------------------------|------|
| **F-01** | 写 `trip.json` 会自造 stale | `studio_trips.longshot_outputs_stale()` = `trip_mtime > latest_png + 0.5` | **属实 · §3 决策成立 · 不重开** |
| **F-02** | 产物靠 glob 猜前缀 | `_LONGSHOT_FILE_PATTERNS` 六组 + `_export_search_dirs` 双目录 | **属实** |
| **F-03** | 清单只记最近一次、只两种 kind | `write_longshot_current(kind ∈ {whole, segmented})` | **属实** |
| **F-04** | `outputId = profile` 唯一 | `cli/render_cmds.py`：`--width/--height` → `with_custom_output(profile,…)`，`custom` 规格任意；`platform_profiles.yaml:wechat_chat` = `capture: chapter_or_full`，naming `{title}-longshot\|{title}-ch{nn}` | **不成立 · 两处撞号 · BLK-01** |
| **F-05** | `bundleFp` 可复用现网分族函数 | `render/context.py:_bundle_version_paths(trip)` 按 `is_portfolio_trip` 选族（`D-DPI-16`）；同文件 `_BUNDLE_VERSION_PATHS` 注释自写 *journal-only, no portfolio CSS* | **属实 · 禁用旧名这条正确 · 保持** |
| **F-06** | 自愈逐文件 stat 可接受 | `trips-client.js:SHELF_PAGE_SIZE = 20`；`platform_profiles.yaml:portfolio_pages.max_pages = 48`；`xiaohongshu.max_pages = 18` | **反噬 · 最坏 ≈2880 次 stat · BLK-03** |
| **F-07** | 票根只有身份行，副券是唯一状态源 | `shelf.js`：`READY_LONGSHOT="分享图已就绪"` · `STALE_LONGSHOT`/"分享图需更新" · `STALE_BADGE="可重排"` · `PREVIEW_READY` · `PREPARING_HD`；`shelf-actions-logic.js:shelfShowCoverLongshotBadge` 读 `trip.longshotStale`；注释 `SFP D-SFP-09`「可重排不得压过 L1 分享图态」 | **既有徽章优先级合同 · 双真相 · BLK-04** |
| **F-08** | 副券数字无害 | PIS `AMD-PIS-05` / `AC-PIS-10`：成册页 X 唯一，禁止 `outputs.length` 当主数字（36 vs 37 根因） | **破坏前序合同 · BLK-02** |
| **F-09** | `export` 选项属结构 | `exportOptions` 里 `copyDisplay`/`breathMode`/`longshotDensity` 是 trip 级，但只影响长图/读者面舞台 | **跨舞台污染 · BLK-05** |
| **F-10** | 副券点击安全 | `shelf.js:buildBook` 的 `v2-shelf__open--meta` 包住整块 `stub-main` 并绑 `openTrip` | **属实 · 风险已被 PRD 识别 · AC-OLT-16 当门** |
| **F-11** | M2 可在默认配置下验收 | §7.2：`studio.output_ledger` 默认 M1/M2 `false`，M3 转 `true` | **自锁 · BLK-06** |
| **F-12** | 夹具无需交代 | DPI 夹具合同：游记独占 `phase16-dogfood/**`、作品集独占 `editorial_series/**`、共享 `trip.render_golden.json`（克隆注入 `edition` 合法） | **缺失 · BLK-07** |
| **F-13** | 窄缝零新增可达 | `dispatch.py` = S-07（`(platform, edition)`）；`context.py` = S-06；`web/studio*` 在允许清单 | **属实 · 仍 12/14 · 保持** |
| **F-14** | `album_spread` label 上票根无碍 | label = 「画册印刷」；PIS 铁律 3 禁「画册」但 `BLK-PIS-05` 已把抽检收窄到选夹/确认/等待/成功面/Dock，**票根不在其中** | **不冲突 · 转 OQ-OLT-08 裁定** |
| **F-15** | 「不删任何现网代码」可行 | `longshot-current.json` 被 `longshot_reveal_rel_path()` 依赖且是 QFX `D-QFX-06b` 成功门 | **属实 · §8.2 保留正确** |

---

## 4. Must-Fix（回写 v0.1.1 前不批开工）

| ID | 挡哪个里程碑 | 要求 |
|----|-------------|------|
| **BLK-OLT-01** | **M1** | **`outputId` 必须唯一。** `outputId = profile` 在两处不成立：① `custom`（Phase C · CLI `--width/--height` → `with_custom_output`）可产出任意规格；② `wechat_chat` 是 `capture: chapter_or_full`，整卷 `{title}-长图` 与分章 `{title}-ch{nn}` 是两种产物。按原文后导的会**静默替换**前一份。二选一：（a）`outputId = profile` + 规格判别式（`custom` 附 `{w}x{h}`、`wechat_chat` 附 `whole`/`chapter`），或（b）M1 明确把 `custom` 排除出账本（CLI-only、不进 Studio UI）并把 `wechat_chat` 的两态显式建模。§4.3 `outputId` 行与铁律 4「一 profile 一条活跃记录」须同步改写。 |
| **BLK-OLT-02** | **M2** | **副券不得显示文件数。** 票根身份行是「作品集 · X 页」（PIS），副券写「作品集页图 33」即在同一张卡上重现 36 vs 37（`AMD-PIS-05` / `AC-PIS-10` 明令禁止 `outputs.length` 当主数字）。**加席否决权已用于此条。** 改为：副券**只显示 `label`**；文件数只进「管理成品」详情。§6.2 票面示意图、§6.3「`fileCount === 1` 省略数字」、§6.4 文案表第一行同步改写。`AC-OLT-15` 删去数字相关断言，新增「副券不得出现与身份行页数不一致的数字」。 |
| **BLK-OLT-03** | **M1** | **禁止逐文件 stat；`R-OLT-06` 论断作废。** `SHELF_PAGE_SIZE = 20`、`portfolio_pages.max_pages = 48`，最坏一次书架加载近 **2880 次 `stat()`**，比现网六组 glob 更贵。§4.5 自愈改为：对 `导出文件/` 做**一次 `os.scandir`** 得到文件名集合，再与各条 `files` 做集合比对。`R-OLT-06` 改写为「须给出 20 trip × 3 成品的实测基准，`/trips` 耗时不得劣于改前」，并升为 `AC-OLT-25` 当门。 |
| **BLK-OLT-04** | **M2** | **票根状态必须单一真相源。** 现网已有 `SFP D-SFP-09` 的徽章优先级合同（`分享图已就绪` / `分享图需更新` / `可重排` / `可先预览` / `正在准备高清图`），其 stale 源是 mtime 的 `trip.longshotStale`。副券用指纹判 outdated 后，同一张卡会出现「已就绪」与「有更新」并存。**加席第二条否决。** 本波须裁定收敛，二选一：（a）开旗后 `longshotStale` 改由账本指纹供给，L1 徽章与副券同源；或（b）有副券时隐藏 L1 分享图徽章。**不接受两套并存**，也不接受留到后续波次。§6.2 须补票面与既有徽章的共存图，`AC` 补「同一卡不得同时出现『已就绪』与『有更新』」。 |
| **BLK-OLT-05** | **M2** | **`export` 选项移出 `structureFp`。** `copyDisplay` / `breathMode` / `longshotDensity` 只影响长图与读者面舞台，放进全产物共吃的 `structureFp` 会让「调一次长图密度」把作品集页图也标「有更新」—— 误报换姿势回来。改为：从 §5.2 `structureFp` 投影中删除，落进各条 output 自己的 `spec` 快照比对；或新增第四段 `optionsFp` 并由 profile 在 `staleInputs` 声明。§5.2 投影表、§5.4 判定、`QA-OLT-02` 断言同步改。 |
| **BLK-OLT-06** | **M2** | **开旗时序解锁。** 默认 `studio.output_ledger=false` 到 M3，但 M2 前端要渲染副券必须有账本数据 —— M2 在默认配置下无可测对象，M4 狗粮也走不了。改为：M1 合入后即在开发/狗粮配置开旗；或 M2 起默认开旗、M3 只做 CSC baseline 收口（`QA-OLT-04` 位置不变）。§7.2 与 §11 里程碑表同步。 |
| **BLK-OLT-07** | **M1** | **写明账本/指纹单测的夹具策略。** DPI 夹具合同：游记独占 `phase16-dogfood/**`、作品集独占 `editorial_series/**`、共享基线只有 `trip.render_golden.json`（克隆再注入 `edition` 合法）。账本与指纹须同时覆盖两身份，夹具不交代会有人去读对面夹具，`pipeline_isolation` 当场红。§9 补一节：`QA-OLT-01/02` **一律用 `trip.render_golden.json` 克隆 + 注入 `edition`**；**禁止**从账本/指纹测试读 `phase16-dogfood` 或 `editorial_series` 夹具。 |

---

## 5. Should-Fix（不挡 M1/M2）

| ID | 说明 |
|----|------|
| **SHD-OLT-06** | **「有更新」必须给下一步。** 加席第 4 问：告诉他旧了，点下去却是开文件夹。要求「重新导出」在副券同处可达（右键 / 长按 / 悬浮小钮均可），不新增一层跳转。绑 FE-OLT-04。 |
| **SHD-OLT-07** | reveal 失败（文件被移走、Windows 权限、路径超长）须有 toast 兜底，不得静默无反应。绑 FE-OLT-02。 |
| **SHD-OLT-08** | **孤儿文件裁定写进 §8.1。** 导出中途失败留下 12/18 张时：账本无条目、glob 有文件。裁定为**不展示**（宁缺勿错），并在 §8.1 三层回退里显式写出「账本有效时不再回落 glob，孤儿文件不可见」。绑 BE-OLT-02。 |
| **SHD-OLT-09** | **「副券」与「成品」不得进 C 端可见文案。** 副券上只出现 `label`；「管理成品」作为唯一一次用词，M4 狗粮须复验加席是否听得懂，不懂即改。绑 §6.4。 |
| **SHD-OLT-10** | `bytes` 合计与「删除这份成品」是加席第 5 问的答案，优先级可后置但不要砍掉。绑 SHD-OLT-02 / SHD-OLT-03。 |
| **SHD-OLT-11** | `staleInputs` 收窄（原 SHD-OLT-01）须在 BLK-OLT-05 落地后重新表述 —— 两条讲的是同一件事的两半，回写时合并，避免实施时按两套改。 |
| **SHD-OLT-12** | `output_ledger_fallback` 遥测（原 SHD-OLT-05）加一维「回退原因」（无账本 / 版本不符 / 校验失败），否则攒不出 glob 退役的证据。 |

---

## 6. 开放问题 · 本场裁决

| ID | 草案预裁 | **本场裁决** | 理由 |
|----|----------|--------------|------|
| **OQ-OLT-01** 管理入口位置 | 卡片菜单 | **维持卡片菜单** | 就近；加席不去设置里找导出 |
| **OQ-OLT-02** outdated 副券点击是否直接重导 | 不 | **维持不**（点的是「看看」）+ 绑 SHD-OLT-06 给重导入口 | 加席自述「点它是打开文件夹」是他预期 |
| **OQ-OLT-03** 是否留同 profile 历史版本 | 不 | **维持不** | 磁盘已按轮 purge；账本须反映现状 |
| **OQ-OLT-04** 并行导出写锁 | 本波不做 | **维持不做**，但 §4.1 须写明「并行化前必须先加文件锁」为硬前置 | 平台席：现网单 job，改并行时容易忘 |
| **OQ-OLT-05** `share_zip`/`pdf` 是否上票根 | 上，排最后 | **改判：只进「管理成品」，不上票根副券** | 加席只关心图；上限 3 应留给图类成品 |
| **OQ-OLT-06** 「成品」用词 | 待验证 | **维持待验证**，M4 狗粮复验（SHD-OLT-09） | 加席「别再造词」 |
| **OQ-OLT-07** M2a/M2b 降级 | 可 | **维持可**，但 M2a 也须先关 BLK-OLT-04（列表同样会与徽章打架） | 前端席 |

**本场新增**

| ID | 问题 | 裁决 |
|----|------|------|
| **OQ-OLT-08** | 作品集票根上出现「画册印刷」副券，是否违 PIS 铁律 3？ | **不违。** `BLK-PIS-05` 已把抽检收窄到选夹/确认/等待/成功面/Dock，票根不在其中；且**成品名是渠道名，不是身份名**。但须加 AC：身份行不得被成品名污染，两者不得写在同一行。 |
| **OQ-OLT-09** | `AC-OLT-08` 与 `AC-OLT-10` 判据重叠（「重新渲染」vs「只改 updatedAt」） | **合并为一条**，判据统一表述为「三段指纹投影内的字段未变 → 全部 ready」，并列出「重新渲染会动而投影不含」的字段清单，防实现各自解释。 |
| **OQ-OLT-10** | `custom` 是否根本不该进账本 | **倾向排除**（Phase C · CLI-only · 不进 Studio UI），作为 BLK-OLT-01 的 (b) 方案首选；若日后 `custom` 上 Studio 再补规格判别式。 |

---

## 7. 与前序合同如何和解

| 前序 | 当时 | 本场 |
|------|------|------|
| PIS `AMD-PIS-05` 成册页 X 唯一 | 导出主句用 X，Y 只进副句 | **延伸到票根**：副券不得出现与 X 打架的数字（BLK-02） |
| PIS 票根身份行 | 游记 / 作品集 · X 页 | **不动**；副券是新增一行，身份与成品分轴（`AC-OLT-18` 当门） |
| PIS `BLK-PIS-05` 用词抽检收窄 | 主路径五处 | **票根不在抽检内** → 「画册印刷」副券合法（OQ-OLT-08） |
| PFO stale 误报 | `layoutCssStale` 族错配 | **指纹方案 + 复用分族函数**即修；但不得引入第二套 stale 真相（BLK-04） |
| SFP `D-SFP-09` 徽章优先级 | 可重排不得压过 L1 分享图态 | **必须收敛**，不接受副券另开一套（BLK-04） |
| EOI `D-EOI-05` 不迁移不清理 | 老产物不动 | **保持** · 账本缺失即回退，老 trip 不补写 |
| QFX `D-QFX-06b` 成功须有清单 | `longshot-current.json` | **保持** · 账本是超集不是替代（§8.2 正确） |
| DPI 窄缝 12/14 | 上限 14 | **零新增** · `AC-OLT-21` 当门 |
| DPI 夹具合同 | 三方独占/共享 | **须写进本文**（BLK-07） |
| 备忘录 W3 舞台注册表 | 归 W3 | **保持** · `surface` 本波只落不用（铁律 8 正确） |

---

## 8. 线框

| 帧 | 本场 | 处置 |
|----|------|------|
| 票根 · 零成品 | **无需新帧** | 逐像素不变（`AC-OLT-14`） |
| 票根 · 有副券 | **须新签一帧** | 且必须**同时画出既有徽章**（BLK-04 收敛后的样子），不接受只画副券行 |
| 票根 · 深/浅两主题 | **各一帧** | 保持 |
| 管理成品列表 | **须一帧** | 原文未列，本场补：M2a 降级路径要靠它单独出门 |
| 导出面板 / 成功面 | **不新开** | 本波不碰（PFO / PIS 已签） |

---

## 9. 本场关闭 / 保持

| 项 | 处置 |
|----|------|
| 账本不进 `trip.json`（§3 六条） | **保持 · 论死 · 不重开** |
| 过期比三段指纹不比 mtime | **保持方向 · 投影须改（BLK-05）** |
| `bundleFp` 复用分族函数 + 禁用 journal-only 旧名 | **保持 · 当门** |
| 票根加副券、身份与成品分轴 | **保持 · 数字须去（BLK-02）** |
| `outputId = profile` | **不成立 · 改（BLK-01）** |
| 逐文件 stat 自愈 | **否决 · 改 scandir 集合比对（BLK-03）** |
| 副券与既有徽章并存 | **否决 · 须收敛（BLK-04）** |
| 窄缝零新增 · 不删现网代码 · 关旗即回到今天 | **保持 · 三条都当门** |
| `surface` 只落不用 | **保持** |
| `share_zip` / `pdf` 上票根 | **改判：只进管理列表（OQ-OLT-05）** |
| 按渠道切管线 / W2–W4 内容 | **不重开** |
| 云同步 / 批量清理 / 跨 trip 复制 | **不做** |

---

## 10. 编码门（回写 v0.1.1 后）

| 里程碑 | 回写前 | 回写后 |
|--------|--------|--------|
| **M1** 账本 + 指纹 | 须 BLK-01（outputId）· BLK-03（scandir）· BLK-05（投影）· BLK-07（夹具） | 可开工 |
| **M2** 票根副券 | 须 BLK-02（去数字）· BLK-04（状态收敛）· BLK-06（开旗时序）+ 票根新帧已签 | 可开工 |
| **M2a** 仅管理列表（降级） | 须 BLK-04 + 管理列表帧 | 可开工 |
| **M3** 默认开旗 + 收敛 | 须 M2 绿 + `AC-OLT-25` 性能基准 | 可开工 |
| **无条件 Go** | 全部 BLK 关 + M4 狗粮（三种导出 → 三券 · 重渲染不误报 · 手删自愈 · 加席复验用词） | — |

BLK-01/03/05/07 是纯后端，与 BLK-02/04/06 无依赖，**M1 可先行回写先开工**，不必等票根帧。

---

## 11. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 本纪要 | 2026-08-26 | 八席 Conditional Go。BLK-OLT-01～07。加席两条否决（副券数字重犯 36/37、同卡双状态）。OQ-OLT-05 改判（zip/pdf 不上票根）、新增 OQ-OLT-08～10。待回写 OLT v0.1.1。 |
| 回写 | 2026-08-26 | Must-Fix 已全部写入 [OLT v0.1.1](../PRD-OUTPUT-LEDGER-TICKET-V1.md)：§0.4 勘误表 · 铁律 4/6/7 · §4.3.1 outputId 规则 · §4.4 映射（`custom` 除籍 · zip/pdf 不上券）· §4.5.1 scandir 自愈 · §5.2/§5.6 四段指纹与逐 profile 声明 · §6.2/6.3/6.4 副券去数字 · **§6.7 状态单一真相源**（新增）· §7.2 开旗时序 · §8.1 孤儿文件裁定 · **§9.4 夹具策略**（新增）· AC 扩至 AC-OLT-01～30 · R-OLT-06 作废改实测门。BLK-OLT-01 采纳方案 (b)：`custom` 排除出账本 + `wechat_chat` 显式分 `:whole`/`:chapter`。**M1 编码门打开。** |
| 线框 | 2026-08-26 | 看帧入口落地 [olt-output-ledger-ticket-v1-wireframe.html](../wireframes/olt-output-ledger-ticket-v1-wireframe.html)；签核底稿 [olt-frame-ab-signoff-2026-08-26.md](./olt-frame-ab-signoff-2026-08-26.md) **待产品签**。合同零改。**M2 门仍关。** |
