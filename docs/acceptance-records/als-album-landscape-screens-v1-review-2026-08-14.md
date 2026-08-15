# PRD-ALBUM-LANDSCAPE-SCREENS-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-ALBUM-LANDSCAPE-SCREENS-V1.md](../PRD-ALBUM-LANDSCAPE-SCREENS-V1.md)（**ALS** · 横版画册） |
| **触发** | 产品：桌面预览与印刷要同一部；新开第七出口，不改现有六种，不碰 [画册编排.md](../画册编排.md) |
| **相邻挡门** | [ADR-016](../adr/016-longshot-platform-export.md) · [ADR-021](../adr/021-export-compose-dual-engine.md) · [ECC](../PRD-EXPORT-CARD-COMPOSE-V1.md) · [ABE](../PRD-ALBUM-EXPORT-BOOKENDS-V1.md) · [BEX](../PRD-BATCH-EXPORT-MULTISELECT-V1.md) · [AEL](../PRD-ALBUM-EDITORIAL-LAB-V1.md)（仍只挂 `album_spread`）· `longshot.py` `_BROWSER_POOL` · `enabledPlatformsFromConfig` |
| **评审版本** | PRD **v0.1.0** → Must-Fix 回写后升 **v0.2.0** |
| **日期** | 2026-08-14 |
| **结论** | **有条件通过（Conditional Go · 主线可冻结；W0 只做注册/隔离单测，不点亮菜单；W1 合码挡 BLK-ALS-01～05）** |
| **编码** | ☑ 策划回写 v0.2　☐ W0 注册+隔离　☐ W1 按屏截图（菜单点亮）　☐ W2 文案/池/取消 |
| **参评角色（七席）** | 产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD v0.1 §0～§14 · D/G/AC/OQ + **对照现网**（`DEFAULT_LONGSHOT2_PLATFORMS`、`COMPOSE_PLATFORM_IDS`、`enabledPlatformsFromConfig` 硬白名单、`detectPlatformFromProgressHint`、`_BROWSER_POOL`、`index.html` vs `index-longshot.html`、`.breath-pause-screen` 几何、`.cover-opening` 非 16:9 舞台） |
| **记录人** | 七席联合纪要（跨职能模拟联评 · 基于 2026-08-14 PRD v0.1.0 + 代码事实核查） |
| **本纪要状态** | **已结案 · Conditional Go** · **PRD v0.2.0 已回写 BLK-ALS-01～05** |
| **审查基线** | 第七出口不得改六种路径 · 捕获源是预览不是长图展平 · 不把现网缝/章票根误当成 16:9 屏 · **不把「菜单能点」写成 W0 完成** |

---

## 0. 会前宣读（主持人）

1. **切口**：横版画册 = 把桌面预览每一屏截成 16:9 页。不是第二套排版引擎，也不是把 `album_spread` 改比例。  
2. **已拍（勿重开）**：新 id `album_landscape`；不改默认五元组 / Compose 集合；不管印厂工艺；不管画册编排 √2 线；V1 不进批量。  
3. **勿重开**：并回 3:4 画册、截 `index-longshot.html`、微信长图改 16:9、跨页 SKU、Output Recipe。  
4. **本场必拍**：进度 hint「画册」会不会误判成跨页；呼吸缝算不算一页；封面节点是不是 16:9；W0 能否对用户点导出；浏览器池能不能 import 私有对象。  
5. **OQ-ALS-01～04** 本场关闭。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：主线立得住——第七出口、按屏截 `index.html`、六种零回归，比改道 `album_spread` 可验收。但 v0.1 有五处按原文 Kickoff 会假绿或打穿现网：（1）W0 允许「菜单可点、后端 501」，用户会以为第七项已坏；（2）`album_landscape.py` 若 import `_BROWSER_POOL` 是私有耦合，池子一改六种长图一起炸；（3）`detectPlatformFromProgressHint` 的 `/画册|跨页/` 会把「横版画册」认成 `album_spread`，进度/成功态串台；（4）`.cover-opening` / 章分隔不是 16:9 舞台，整节点 letterbox 会印出细条或大空边，不是预览里看到的那一屏；（5）`.breath-pause-screen` 现网只是约 12px 节奏缝，算一页会印出大量近空白页。关 BLK 后升 v0.2；W0 只注册隔离；菜单与真截图同 PR 点亮。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 第七项、与跨页并列、失败不影响六种，切口对。对外不能说「和预览每一屏一样」却把 ··· 缝打成一页。W0 不要先挂一个点了就失败的按钮。OQ-01 改成 **不算** 呼吸缝。 |
| **算法** | **Go** | 本出口没有新选型、不二次分组，正确。禁止再跑 CardGrouper / flatten。没有算法门。 |
| **架构** | **Conditional Go** | 新 id、不进 Compose、append 不改默认元组，对。池必须走 `longshot` 公开 acquire/release，禁止碰 `_BROWSER_POOL`。捕获盒要写成视口合同，不能只写 CSS 选择器。 |
| **开发** | **Conditional Go** | W0 开工面清晰：config + YAML + allow append + 前端白名单。W1 真活是视口锁 + 藏壳 + 逐节点截。`longshot.py` 只加一分支。前端 `enabledPlatformsFromConfig` 硬名单和 `isComposePlatform` 漏改会静默丢第七项或显示「正在合成长图」。 |
| **测试 / QA** | **Conditional Go** | AC-ALS-03（六种 collage 单测零改）是本主题第一门。`test_longshot_client.py` / `longshot-export-panel.test.mjs` 大量写死 `album_spread` 文案，改 hint 时禁止误伤。进度误判必须有单测：含「横版」不得返回 `album_spread`。W0 点亮菜单不可验收。 |
| **视觉 / 排版** | **Conditional Go** | `layout-screen` 截整节点成立。封面/封底/票根章分隔是另一套盒子；按内容流高度压进 16:9 会不像预览。呼吸缝更不是一页。letterbox 纸色用页背景，不要黑边。 |
| **用户体验 · 狗粮** | **Conditional Go** | 仍是一键。不要跨页张数。不要批量里突然多一个很慢的项。确认页不要猜「约 37 页」却对不上。产物 80 张 4K 会很大，成功态提一句即可。 |

**汇总**：**6 Conditional Go + 1 Go（算法）**。未回写 Must-Fix 前 **不批无条件 Go** · **不批对用户点亮第七项** · **不批 W1 合码**。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **8** | 「同一部」→截预览屏，因果对 |
| 与现网能力对齐 / 防假绿 | **5** | 呼吸缝、封面盒、进度「画册」三处假绿 |
| 与六种 / ECC / 编排边界 | **9** | 隔离写清楚，且不碰编排线 |
| 工程可开工性 | **8** | W0/W1 文件面清楚 |
| AC 可测性 | **7** | 屏数合同要改成「可见 16:9 框」才测得动 |
| 回归护栏 | **8** | 六种 frozenset 断言够用 |

---

## 3. 事实核查（对照现网 · 影响结论）

| # | PRD v0.1 假设 | 代码事实（2026-08-14） | 会中 |
|---|----------------|------------------------|------|
| **F-01** | 用户可见六种；默认五元组不含本 id | `DEFAULT_LONGSHOT2_PLATFORMS` = moments/xhs/mp/poster/album_spread；`wechat_chat` 另挂；`COMPOSE_PLATFORM_IDS` 四元 | **属实 · 保持不改** |
| **F-02** | 前端可 append 第七项 | `enabledPlatformsFromConfig` **硬白名单六种**；`album_spread` 还无条件 concat | **属实**；必须改白名单，且 **禁止** 对本 id 做无条件 concat |
| **F-03** | 进度文案写「横版画册」即可 | `detectPlatformFromProgressHint`：`/画册\|跨页/` → `album_spread` | **修正**：会串台。hint 禁用「画册」或检测器先匹配横版/landscape |
| **F-04** | 可 import `_BROWSER_POOL` | 类与实例均在 `longshot.py` 模块私有，无公开 acquire API | **修正**：加公开函数；ALS 不得引用下划线名 |
| **F-05** | 捕获 `index.html` 即与预览一致 | `index-longshot.html` 展平 screens；Studio 只给 `index.html` 注入顶栏 | **属实**；藏壳合同成立 |
| **F-06** | `breath-pause-screen` 占预览一整屏 | CSS：`min-height: var(--screen-rhythm-gap)`（约 12px），**不是** 16:9；`insert_breath_screens_in_chapters` 默认每 4 内容屏插一条 | **修正**：V1 **不进** 页集合，否则近空白页爆炸 |
| **F-07** | 截 `.cover-opening` 再 letterbox = 预览封面 | `.cover-opening` 无 `aspect-ratio: 16/9`，高度随 hero+文案面板；snap 对齐的是整块，用户看到的「第一屏」≈ 视口框 | **修正**：捕获盒 = 1920×1080 视口内该节点的可见 16:9 框 |
| **F-08** | 章分隔是一屏 | `chapter-separator--ticket` 是票根条，不是 16:9 舞台 | **属实风险**；进页集合可以，但必须按视口 16:9 框截，不能整条内容流压扁 |
| **F-09** | W0 菜单可点、后端 501 | 现网导出 CTA 一经出现用户就会点；`test_longshot_client` / 面板单测把「能看见」当合同 | **修正**：W0 不点亮；点亮与 W1 同出门 |
| **F-10** | `isComposePlatform` 与本出口无关 | `COMPOSE_PLATFORMS` 仅四元；未登记则 `progressSynthesizingTitle` 走「正在合成长图…」 | **修正**：本 id 既不是 compose 也不是长图，要有自己的进度标题 |
| **F-11** | `slideCount` 可忽略 | 画册跨页面板有 `showAlbumCountOptions`；compose 仍可能带 scale | **属实**；本平台必须关跨页控件；scale 建议隐藏（SHD） |
| **F-12** | 批量可 400 | BEX 单测大量带 `album_spread`，不含本 id | **属实**；新测只断言含 landscape → 400，不改旧序 |
| **F-13** | Writer 可直接用 | `PlatformExportWriter` 在 `platform_longshot.py`，`{prefix}-{nn:02d}.png` | **属实**；prefix 走 `file_prefix_for_platform` |
| **F-14** | 画册编排 / AEL 会缠上来 | AEL / ECC 只认 `album_spread` | **属实 · 保持不接线** |

**会中新增事实**

- `breath.js` 把 `breath-pause-screen` 和 `chapter-separator` 列进阅读选择器，但几何上前者是缝、后者是票根，与 `layout-screen` 不是同类盒子。  
- 面板 JS 单测用 `/画册/` 识别 `album_spread`（`detectPlatformFromProgressHint("画册跨页排队中…")`）。ALS hint 若含「画册」会红这批测试或运行时串台——应先改检测器再写 hint。  
- `_BROWSER_POOL.acquire` 按线程认主；ALS 必须与 job 线程同一套 acquire/release，禁止另起 sync_playwright。

---

## 4. 全场共识

1. **主线冻结**：第七出口、截预览 16:9、六种零回归、不管编排线。  
2. **W0 不点亮菜单**；注册与隔离单测可以先合。  
3. **页集合 V1**：封面 + 章分隔 + `layout-screen` + 封底。**不含** `breath-pause-screen`。  
4. **捕获盒**：`layout-screen` 可元素截图；其余节点按 **1920×1080 视口内可见 16:9 框** 截，禁止内容流全高压进 16:9。  
5. **进度文案禁用「画册」二字**（用「横版页」）；检测器先匹配 landscape / 横版。  
6. **池走公开 API**。  
7. **OQ-01～04** 按 §7 关闭。  
8. **不进批量、不进 Recipe、不改 Compose 集合** 不回退。

---

## 5. Must-Fix（阻塞 · 升 v0.2 前关闭）

| ID | 议题 | 要求（冻结一字面） | 挡 | 状态 |
|----|------|-------------------|----|------|
| **BLK-ALS-01** | W0 点亮会 501 | **D-ALS-16**：功能开关默认 true 只表示「允许挂载」。**对用户可见/可点的第七项与真捕获同 PR 出门**。W0 只合注册、allow append、隔离单测；`enabledPlatformsFromConfig` 在捕获函数未落地前不得 push。 | 对用户点亮 · W1 合码 | ✅ **已回写 v0.2.0** |
| **BLK-ALS-02** | 私有浏览器池 | **D-ALS-17**：`longshot.py` 提供公开 `acquire_browser()` / `release_browser()`（或等价）。`album_landscape.py` **禁止** import `_BROWSER_POOL` / `_PlaywrightBrowserPool`。禁止本出口 `sync_playwright().start()` 另起实例。 | W1 合码 | ✅ **已回写** |
| **BLK-ALS-03** | hint「画册」串台 | **D-ALS-18**：`detectPlatformFromProgressHint` 必须 **先** 匹配横版/landscape/`album_landscape`。本出口一切用户可见进度/成功文案 **禁止**出现「画册」「跨页」（用「横版页」）。现网 `/画册\|跨页/` → `album_spread` 保留，但不得误伤本出口。 | W1 合码 · W2 文案 | ✅ **已回写** |
| **BLK-ALS-04** | 捕获盒 / 呼吸缝 | **D-ALS-19**：页节点 = `cover-opening` + `chapter-separator` + `layout-screen` + `cover-closing`。**不含** `breath-pause-screen` / `breath-pause-card`。`layout-screen` 元素截图；其余三者截 **视口内可见 16:9 框**（1920×1080），禁止把内容流全高 letterbox 成细条。 | W1 合码 · AC-ALS-05 | ✅ **已回写** |
| **BLK-ALS-05** | 进度标题走长图默认 | **D-ALS-20**：本 id **不得** 写入前端 `COMPOSE_PLATFORMS`。须自备 `progressTitle` / 合成中文案（「正在截取横版页…」）。`isComposePlatform("album_landscape") === false`。 | W1 前端 | ✅ **已回写** |

**Should-Fix（不阻塞 v0.2）**

| ID | 建议 | 状态 |
|----|------|------|
| **SHD-ALS-01** | V1 前端不估算具体 N，只写「页数与预览相同」；N 以导出结果为准 | W2 |
| **SHD-ALS-02** | 本平台隐藏 scale / 跨页张数；避免用户以为 3× 会生效 | W1 |
| **SHD-ALS-03** | 成功态提一句「页数较多时文件较大」 | W2 |
| **SHD-ALS-04** | `test_longshot_client.py` / 面板单测 **additive** 加 landscape 令牌，禁止删 `album_spread` 断言 | W0/W1 |
| **SHD-ALS-05** | 狗粮三册与 AEL 同口径：`demo-d6697c8dca` · `demo-2025` · `demo-49cbe46479`；对屏数用人眼滑预览 | W1 出门 |
| **SHD-ALS-06** | letterbox / 视口垫色用页背景（`--bg-page` / `#f5f2ea`），禁止黑边 | W1 |
| **SHD-ALS-07** | ACCEPTANCE 专页可后补；v0.2 AC 表已够 W0/W1 | 不挡 |

---

## 6. 典型用户提问 Q&A

| 提问 | 会中回应 |
|------|----------|
| 和现在的「画册印刷」有什么区别？ | 跨页是 3:4 两页拼起来送印；横版页是把你桌上预览的每一屏原样导出。 |
| 会不会把小红书/旧画册一起改掉？ | 不会。这是新的第七项，关掉就当没这回事。 |
| 为什么有的 ··· 没打成一页？ | 那是预览里的换气缝，不是一屏。印出来会是一张空纸。 |
| 可以自己选只要 8 页吗？ | V1 不行。要哪几章，先在预览里改册，再导出。 |
| 能和小红书一起勾选批量吗？ | V1 不行。横版页要开浏览器逐屏截，请单独导出。 |
| 套 A4 会不会切到脸？ | 请印厂按 16:9 留白，不要铺满裁切。 |

---

## 7. 开放问题结案

| ID | 结案 |
|----|------|
| **OQ-ALS-01** | ✅ **不算** `breath-pause-screen`（F-06）。若日后呼吸缝改成真正 16:9 屏，再开选择器，不在 V1 猜。 |
| **OQ-ALS-02** | ✅ **2**（3840×2160）。不在 V1 做分辨率 UI。 |
| **OQ-ALS-03** | ✅ **否** PDF。 |
| **OQ-ALS-04** | ✅ 配置默认 `true`，但 **对用户点亮遵循 D-ALS-16**（与真捕获同出门）。W0 阶段用户仍只见六种。 |

---

## 8. 可 Kickoff 门

| 门 | 条件 |
|----|------|
| **W0 注册/隔离** | v0.2 已回写；**不**点亮第七项 |
| **W1 合码 + 点亮** | BLK-ALS-01～05 在 PRD 与实现清单闭合；六种回归绿 |
| **W2 文案/池** | W1 狗粮三册屏数对得上 |
| **无条件 Go / 默认当主画册** | **本场不批**。不取代 `album_spread`。 |

---

## 9. 签字（模拟联评）

| 席 | 表决 | 日期 |
|----|------|------|
| 产品 | Conditional Go | 2026-08-14 |
| 算法 | Go | 2026-08-14 |
| 架构 | Conditional Go | 2026-08-14 |
| 开发 | Conditional Go | 2026-08-14 |
| 测试 / QA | Conditional Go | 2026-08-14 |
| 视觉 / 排版 | Conditional Go | 2026-08-14 |
| 用户体验 · 狗粮 | Conditional Go | 2026-08-14 |

---

## 10. 模板

后续若再开席，纪要文件名：`als-album-landscape-screens-v1-review-YYYY-MM-DD.md`。
