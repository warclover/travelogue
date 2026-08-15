# PRD-ALBUM-LANDSCAPE-SCREENS-V1 · 横版画册（16:9 按屏导出）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | parked |
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.2.0 |
| **状态** | **parked**（2026-08-15 · [截屏不可用纪要](./acceptance-records/als-screenshot-parked-2026-08-15.md)）· 长图/预览逐屏截图 **不可用** 作 16:9 画册 · 导出模式等待独立 `page-*` 模板，不再截屏 · 原七席 [纪要](./acceptance-records/als-album-landscape-screens-v1-review-2026-08-14.md) 仅作考古 |
| **模块代号** | **ALS**（Album Landscape Screens · 横版画册） |
| **前置条件** | Web `layoutEngine=screens` 已写出 `index.html` · Playwright 浏览器池（ADR-005 / ADR-016 分支 A）可用 · Studio 导出面板（Longshot 2.0） |
| **关联文档** | [ADR-016](./adr/016-longshot-platform-export.md) · [ADR-021](./adr/021-export-compose-dual-engine.md)（**不改**）· [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md)（现网六种之一「画册跨页」维持原状）· [PRD-ALBUM-EXPORT-BOOKENDS-V1.md](./PRD-ALBUM-EXPORT-BOOKENDS-V1.md)（只服务 `album_spread`）· [PRD-BATCH-EXPORT-MULTISELECT-V1.md](./PRD-BATCH-EXPORT-MULTISELECT-V1.md)（V1 **不进**批量）· [TEMPLATE-SURFACES.md](./TEMPLATE-SURFACES.md) · [ADR-020](./adr/020-narrative-contract.md)（`preserveGroup`：本出口截整屏，禁止长图式拆槽） |
| **明确不关联** | [画册编排.md](./画册编排.md)（√2 / 册型 / 系列编译 · **本主题不管**）· [PRD-ALBUM-EDITORIAL-LAB-V1.md](./PRD-ALBUM-EDITORIAL-LAB-V1.md)（AEL 仍只挂 `album_spread`）· [PRD-EDITORIAL-COMPILER-V1.md](./PRD-EDITORIAL-COMPILER-V1.md) |
| **评审纪要** | [als-album-landscape-screens-v1-review-2026-08-14.md](./acceptance-records/als-album-landscape-screens-v1-review-2026-08-14.md) |
| **更新日期** | 2026-08-14 |

---

## 0. 一句话

新增**第七个**导出选项「横版画册」：每一页 = 桌面预览（`index.html`）里的一屏，固定 **16:9** PNG。现有六种导出（微信群 / 朋友圈 / 小红书 / 公众号 / 单张海报 / 画册跨页）**零行为变化**；本出口成败不得改它们的代码路径。

---

## 1. 背景与问题

产品要「桌上看到的游记，印出来还是同一部」。现网「画册印刷 / `album_spread`」是另一条管线：Pillow 把精选照片重排成 3:4 卡，再两卡+gutter 成跨页（ECC + ABE）。预览是 16:9 `screens[]`，两者页数、分组、封面都不是同一部作品。

本轮对话已拍板：

1. **不改**现有 `album_spread`，也不和 [画册编排.md](./画册编排.md) 的印刷页线缠在一起。
2. **新开出口**，平台 id 独立；功能开关可整项卸下，菜单回到六种。
3. 捕获源是 **Web 16:9 预览屏**，不是 `index-longshot.html`（后者会展平 mosaic，屏数对不上预览）。
4. 不管印厂工艺；导出图按 16:9 原样。套 A4 时请印厂留白，禁止裁切。

现网 Studio 用户可见六种：

| # | 平台 id | 用户名 | 引擎 |
|---|---------|--------|------|
| 1 | `wechat_chat` | 微信群 | Playwright 长图（分支 A） |
| 2 | `wechat_moments` | 朋友圈 | Playwright 长卷切分（分支 B） |
| 3 | `xiaohongshu` | 小红书 | Compose 3:4 |
| 4 | `wechat_official` | 公众号 | Compose 3:4 |
| 5 | `poster_bric` | 单张海报 | Compose 3:4 |
| 6 | `album_spread` | 画册印刷 · 跨页 | Compose 3:4 两卡+gutter |

`DEFAULT_LONGSHOT2_PLATFORMS` 只含 2–6；`wechat_chat` 始终在面板里。前端 `enabledPlatformsFromConfig` 对这六种有**硬白名单**。

---

## 2. 目标 / 非目标

| 编号 | 目标 | 说明 |
|------|------|------|
| **G-ALS-01** | 导出面板多一个「横版画册」，与「画册印刷」并列、可区分 | 用户名见 §5.1 |
| **G-ALS-02** | 每一页 16:9 PNG = 预览里对应的一屏；页数 = 预览屏数 | 合同见 §4 |
| **G-ALS-03** | 与预览同一部：同序、同照片集合、同组边界（不拆 mosaic） | 截 `index.html` 整屏节点 |
| **G-ALS-04** | 现有六种导出的代码路径、单测、批量、产物命名零回归 | 禁止改 `collage_pack` / CardGrouper / ABE |
| **G-ALS-05** | 开关关闭后，面板与 API 都回到六种 | 与海报 `gcs_poster_bric` 同构 |
| **G-ALS-06** | 本出口失败只失败本 job；必须归还浏览器池 | 唯一允许的共享资源 |

| 编号 | 非目标 | 说明 |
|------|--------|------|
| **N-ALS-01** | 不改 `album_spread` 几何、选图、ABE 书衣、AEL | 3:4 跨页继续服务「画册印刷」 |
| **N-ALS-02** | 不实施 [画册编排.md](./画册编排.md) 的 √2 页库 / 系列 / 跨页 SKU | 那条线独立，本主题不管 |
| **N-ALS-03** | 不改微信长图 / `index-longshot.html` / 9:16 移动面 | 禁止为「一致」把长图改成 16:9 |
| **N-ALS-04** | 不做装订、出血、页码、对页、一张图跨两页 | 印厂自行适配 |
| **N-ALS-05** | V1 不进批量多选、不进 Output Recipe | 稳定后再加 |
| **N-ALS-06** | 不新增 `trip.json` 字段、不新开模板库、不二次排版 | 没有 CardGrouper |
| **N-ALS-07** | 不让用户自选页数 / 复用 4–16 跨页控件 | 页数只等于预览屏数 |
| **N-ALS-08** | 不把本出口写进 `COMPOSE_PLATFORM_IDS` / `DEFAULT_LONGSHOT2_PLATFORMS` | 隔离合同 |

---

## 3. 拍板决策

| ID | 决策 | 状态 |
|----|------|------|
| **D-ALS-01** | 平台 id = **`album_landscape`**。禁止复用 `album_spread` / `album_16x9`。 | 已钉 |
| **D-ALS-02** | `DEFAULT_LONGSHOT2_PLATFORMS`、`COMPOSE_PLATFORM_IDS`、`PHASE_A_PLATFORMS` **一字不改**。本 id 只进 `KNOWN_PLATFORM_IDS` + 新集合 `SCREEN_CAPTURE_PLATFORM_IDS`。 | 已钉 |
| **D-ALS-03** | 功能开关 `features.album_landscape.enabled`（兼读 `studio.album_landscape`）。**默认 `true`**。`false` ≡ 面板无此项、API 拒单。 | 已钉 |
| **D-ALS-04** | 捕获源 = 已渲染的 **`index.html`**（`data-layout=web` + `layoutEngine=screens`）。**禁止**打开 `index-longshot.html` / `index-mobile.html`。 | 已钉 |
| **D-ALS-05** | 一页 = 预览阅读序中的一个整屏节点，选择器见 §4.1。封面/封底用 Web 的 `.cover-opening` / `.cover-closing`，**不**走 Pillow ABE。 | 已钉 |
| **D-ALS-06** | 视口锁死 **1920×1080**；`device_scale_factor=2` → 输出 **3840×2160**。关掉 `viewport-fit` 收窄。每页输出必须是精确 16:9；源节点不是则 **letterbox** 到 16:9（纸色 = 页背景），禁止 cover 裁切。 | 已钉 |
| **D-ALS-07** | **元素截图**（`locator.screenshot`），禁止整页 `page.screenshot`。捕获前隐藏 Studio 顶栏 / 放映工具条，并冻结动效（复用长图 performance teardown 的同类手段）。 | 已钉 |
| **D-ALS-08** | 忽略请求里的 `slideCount` / 跨页数 / 填充模式。传入只打日志，不改变页数。 | 已钉 |
| **D-ALS-09** | 文件前缀 `{slug}-landscape-{nn}.png`，与 `{slug}-album-*.png` 可并存。 | 已钉 |
| **D-ALS-10** | V1 **禁止**进入批量 `platforms[]`：前端多选列表不出现；后端若收到则 **400** `E_ALS_BATCH_FORBIDDEN`，不得默默跑。 | 已钉 |
| **D-ALS-11** | 使用现有 `_BROWSER_POOL`。`acquire` 后必须 `try/finally release`。单页超时与整单超时见 §6.4。取消走现网 `cancel_check`。 | 已钉 |
| **D-ALS-12** | Output Recipe / intent 映射 **V1 不做**。面板点选本平台即直出，不经 Recipe 改道。 | 已钉 |
| **D-ALS-13** | 现网「画册印刷」对外文案可加「3:4 对页」以免两个画册撞名；**行为不变**。 | 已钉 |
| **D-ALS-14** | 缺 `index.html`、非 screens 引擎、或屏集合为空 → 本出口失败，提示先完成预览渲染。不得回退到 `album_spread` 或长图。 | 已钉 |
| **D-ALS-15** | 发布指引一句话：「按 16:9 原样印刷或发图；若套 A4 请留白，禁止裁切。」不标毫米、不画页框。 | 已钉 |
| **D-ALS-16** | （BLK-01）开关默认 `true` 只表示允许挂载。**对用户可见/可点的第七项与真捕获同 PR 出门**。W0 只合注册与隔离单测，`enabledPlatformsFromConfig` 在 `export_album_landscape` 未落地前不得 push。 | 已钉 · 七席 |
| **D-ALS-17** | （BLK-02）`longshot.py` 提供公开 `acquire_browser()` / `release_browser()`。`album_landscape.py` **禁止** import `_BROWSER_POOL`。禁止本出口另起 Playwright 实例。 | 已钉 · 七席 |
| **D-ALS-18** | （BLK-03）进度/成功文案 **禁止**出现「画册」「跨页」，改用「横版页」。`detectPlatformFromProgressHint` **先**匹配横版 / landscape / `album_landscape`；现网 `/画册\|跨页/` → `album_spread` 保留。 | 已钉 · 七席 |
| **D-ALS-19** | （BLK-04）页节点 = Opening + 章分隔 + `layout-screen` + Closing。**不含**呼吸缝。`layout-screen` 元素截图；其余截 **视口内可见 16:9 框**，禁止内容流全高压进 16:9。 | 已钉 · 七席 |
| **D-ALS-20** | （BLK-05）本 id **不得**写入前端 `COMPOSE_PLATFORMS`。自备进度标题「正在截取横版页…」。`isComposePlatform("album_landscape") === false`。 | 已钉 · 七席 |

---

## 4. 屏合同（「与预览屏数一致」）

### 4.1 页节点（权威）

在 `index.html` 的 `<main>`（若无则 `body`）内，按 **DOM 文档序** 收集：

```
[data-block="cover-opening"],
[data-block="chapter-separator"],
[data-block="layout-screen"],
[data-block="cover-closing"]
```

| 进 | 不进 |
|----|------|
| 封面 Opening、封底 Closing | `.preview-toolbar` / `data-preview-toolbar` / 放映工具条 |
| 全部 `.layout-screen`（含 moment 屏：它已带 `layout-screen`，**不要**再按 `moment-screen` 收一次） | `index-longshot` 展平卡、`media-card` 竖栈 |
| 章分隔 `chapter-separator` | `trip-index` / `featured-grid` / `foreword-spread` / `data-present-aux` 目录 |
| | **`breath-pause-screen` / `breath-pause-card`**（现网是约 12px 节奏缝，不是 16:9 屏 · D-ALS-19） |
| | 独立 `cover-hero`（封面内部件，避免与 Opening 重复） |
| | `chapter-header`（legacy 章头，现网 screens 以 separator 为准） |

页数 **N** = 上述节点数。对账对象是「预览里可当作一页的整屏」（封面/章分隔/照片屏/封底），**不是**滑过的每一条缝。禁止用「长图段数」或「3:4 卡数」对账。

`preserveGroup`：整屏截图天然保持组。禁止再跑 `screens_to_longshot_items`。

**捕获盒（D-ALS-19）**

| 节点 | 怎么截 |
|------|--------|
| `layout-screen` | 元素截图（本身已是 16:9） |
| Opening / 章分隔 / Closing | 在 1920×1080 视口内，截该节点的 **可见 16:9 框**（通常顶对齐视口），不是内容流全高 |
| 任何截幅仍 ≠ 16:9 | 居中 letterbox 到 3840×2160，垫色 `--bg-page` / `#f5f2ea`，**禁止黑边、禁止 cover 裁** |

### 4.2 几何

| 项 | V1 |
|----|-----|
| 画幅 | 16:9 |
| 视口 | 1920×1080 CSS px |
| 输出像素 | 3840×2160（`device_scale_factor=2`） |
| `viewport-fit` / `--screen-fit-ar` | 捕获态强制按 16:9 铺满视口宽，禁止按 `dvh` 收窄 |
| 非 16:9 源节点 | 先取视口内 16:9 可见框，再必要时 letterbox；禁止把整段内容流压成细条 |
| 禁止 | 对屏做 cover 裁切、智能裁、Pillow 重排、黑边 |

### 4.3 与预览一致的三条硬门

1. 第 *k* 页的 `data-asset-ids`（或封面/封底主图 id）= 预览第 *k* 个页节点的照片集合。
2. 封面艺术字与 Web 同源 `assetPath`（沿用 CAL：截的是同一 DOM）。
3. 改一屏并重新渲染 `index.html` 后再导出，对应页必须变。禁止读旧 3:4 画册缓存。

---

## 5. 用户面

### 5.1 名称与位置

| | 现有第 6 项（不动行为） | **本出口（第 7 项）** |
|--|-------------------------|------------------------|
| id | `album_spread` | `album_landscape` |
| label | 画册印刷 | **横版画册** |
| subtitle | 跨页 · 3:4 对页（D-ALS-13 可补「3:4 对页」） | **与预览同屏 · 16:9** |
| cta | 导出画册跨页 | **导出横版画册** |
| expectHtml | 维持现网两卡+gutter 说明 | 将按预览顺序导出 16:9 横版页（封面/章分隔/每一屏/封底）· 页数与预览相同 · 屏数多时约 1–2 分钟 |
| 张数控件 | 现有 4/8/12/16 跨页 | **无**。只读「页数与预览相同」，**不估具体 N**（SHD-ALS-01） |
| 要不要字 | 无 | 无（字已在屏上） |
| 菜单顺序 | 保持原位 | **紧挨其下** |

开关关闭：第 7 项不渲染，白名单不含 `album_landscape`。

### 5.2 进度与成功

- 进度文案：`正在截取横版页 第 k/N 屏…`（**禁止**「画册」「跨页」· D-ALS-18）
- 成功：`已生成 N 张 16:9 横版页（与预览同屏）· 可预览或送印（套 A4 请留白，勿裁切）`
- 运行中主按钮：`正在导出横版页…`
- 失败：只报本出口错误码（§8），Task Dock 其它平台不受牵连。

### 5.3 批量

多选勾选列表 **不出现** 横版画册。用户只能单独点它导出。

---

## 6. 架构

### 6.1 数据流

```
Studio 点「导出横版画册」
  → POST export-longshot  platform=album_landscape
  → 开关？否 → 400 E_ALS_DISABLED
  → 批量 platforms[] 含本 id？ → 400 E_ALS_BATCH_FORBIDDEN
  → export_trip_longshot
       不进 collage_pack / 不进 platform_longshot 切分
       → export_album_landscape()
            校验 index.html + screens
            收集页节点（§4.1）
            _BROWSER_POOL.acquire
            打开 /{tripId}/index.html
            藏壳 + 冻结动效 + 锁 16:9
            逐节点：滚入视口 → 等图 → element screenshot → letterbox
            PlatformExportWriter 写 {slug}-landscape-{nn}.png
            finally release
```

### 6.2 路由隔离（`longshot.py`）

在现有

```
xiaohongshu / wechat_official / album_spread → collage_pack
poster_bric → poster_bric_pack
```

**之前或并列**增加：

```
album_landscape → export_album_landscape
```

禁止：把 `album_landscape` 推进 `COMPOSE_PLATFORM_IDS`；禁止 flag 关闭时改道 `album_spread`。

### 6.3 允许名单怎么挂（勿改默认五元组）

与海报同构，**append 不改默认元组**：

| 层 | 做法 |
|----|------|
| `DEFAULT_LONGSHOT2_PLATFORMS` | **不改** |
| `studio_config_expose` | 增加 `albumLandscape.enabled` |
| `export_handlers` 组 `allowed_platforms` | flag 开则 `append("album_landscape")` |
| 前端 `enabledPlatformsFromConfig` | flag 开则推进白名单并 `push`；关则当未知 id 丢掉 |
| `resolve_profile` | flag 关或不在 allow → `E_LNG2_INVALID_PLATFORM` / `E_ALS_DISABLED` |

### 6.4 性能与池

| 项 | V1 |
|----|-----|
| 浏览器 | 复用 `_BROWSER_POOL`，禁止另起全局 Playwright |
| 整单超时 | 10 分钟（约 80 屏 × 数秒） |
| 单屏超时 | 20 秒（等图+截图） |
| 取消 | 每屏前 `raise_if_longshot_cancelled` |
| 内存 | 不 captur 整卷长 canvas；一次一屏 |
| 进度 | `progress(k, N, hint)` 与现网 job 字段兼容 |

### 6.5 捕获实现要点

1. `page.set_viewport_size({width:1920,height:1080})`，`device_scale_factor=2`。
2. `goto` Studio 已在跑的 `http://127.0.0.1:{port}/{tripId}/index.html`（与长图同一 host，禁止 `file://`）。
3. 注入：隐藏 `[data-preview-toolbar]`、`.preview-toolbar`、`.screenplay-toolbar`；`data-breath` 置性能态 / 去掉 motion class（可复用长图 teardown 片段，**复制必要行，不要 import 长图切分逻辑**）。
4. CSS：`.layout-screen--viewport-fit { width:100% !important; max-height:none !important; aspect-ratio:16/9 !important; }`。
5. 按 §4.1 query；空 → `E_ALS_NO_PAGES`。
6. 每个 handle：`scroll_into_view_if_needed` → 等待内部 `img` `complete` 且 `naturalWidth>0`（上限单屏超时）→ `screenshot(type=png)`。
7. 若像素比 ≠ 16:9，Pillow letterbox 到 3840×2160。
8. `PlatformExportWriter` 原子写；失败 `rollback()`。

---

## 7. 配置

```yaml
# config.yaml 或 features:
features:
  album_landscape:
    enabled: true    # 默认 true；false = 卸下第七项
```

兼读 `studio.album_landscape.enabled`（与 `gcs_poster_bric` 相同双键）。

`platform_profiles.yaml` 新增（**additive**）：

```yaml
album_landscape:
  label: 横版画册
  label_en: Landscape Album
  segment: screen_capture
  capture: album_landscape
  allow_p1: false
  output:
    width: 3840
    height: 2160
    aspect: "16:9"
    naming: "{title}-landscape-{nn}"
  publish_guide: >-
    按 16:9 原样印刷或发图（每一页 = 预览里的一屏）。
    若套 A4 请留白，禁止裁切。
```

---

## 8. 错误码

| 码 | 何时 | 用户提示 |
|----|------|----------|
| `E_ALS_DISABLED` | 开关关仍请求 | 横版画册未开启 |
| `E_ALS_BATCH_FORBIDDEN` | 批量数组含本 id | 横版画册请单独导出，暂不支持批量 |
| `E_ALS_NO_INDEX` | 无 `index.html` | 请先完成预览渲染 |
| `E_ALS_NOT_SCREENS` | 非 screens 引擎 | 横版画册需要 16:9 预览（screens） |
| `E_ALS_NO_PAGES` | 选择器 0 个节点 | 预览里没有可导出的屏 |
| `E_ALS_CAPTURE_FAILED` | 截图失败 / 过小 | 截取横版画册失败，请重试 |
| `E_ALS_TIMEOUT` | 整单或单屏超时 | 屏数较多导致超时，请重试或减少章节后导出 |
| `E_LNG_NO_LONGSHOT` | **本出口不得使用此码** | 避免用户以为缺的是长图面 |

Playwright 未安装：沿用现网长图同类错误，文案写「横版画册需要本机浏览器组件」。

---

## 9. 验收

| ID | 标准 | 波次 |
|----|------|------|
| **AC-ALS-01** | 开关 `false`：面板只有原六种；单/批量 API 带 `album_landscape` → 4xx；六种回归绿 | W0 |
| **AC-ALS-02** | 真捕获落地且开关 `true`：第七项在「画册印刷」正下方；点它不改其它五项的选中态与设置。**W0 阶段面板仍只有六种** | W1 |
| **AC-ALS-03** | `album_spread` 导出页数、画幅、文件前缀与本主题前 **像素级合同不变**（现网 collage 单测全绿） | W0 / 全程 |
| **AC-ALS-04** | 本出口产物为 N 张 16:9（3840×2160 或 letterbox 后的该尺寸），前缀 `-landscape-` | W1 |
| **AC-ALS-05** | N = §4.1 节点数（不含呼吸缝）；与 `index-longshot` 卡数、3:4 卡数都不必相等 | W1 |
| **AC-ALS-06** | 捕获 URL 的 pathname 以 `index.html` 结尾，测试断言 **不得** 请求 `index-longshot.html` | W1 |
| **AC-ALS-07** | 截图不含 Studio 顶栏 / 放映条；封面艺术字与预览同一 `assetPath` | W1 |
| **AC-ALS-08** | mosaic 屏仍是一块拼图，不是拆开的单图序列 | W1 |
| **AC-ALS-09** | 传入 `slideCount=8` 仍输出 N（预览屏数），不是 8 | W1 |
| **AC-ALS-10** | 批量 `platforms` 含本 id → 400，**不**开始截图、不占池 | W2 |
| **AC-ALS-11** | 中途失败 / 取消：`release()` 被调用；随后微信群长图仍能导出 | W2 |
| **AC-ALS-12** | 无 `index.html` → `E_ALS_NO_INDEX`，不写半成品 | W1 |
| **AC-ALS-13** | 成功文案含「16:9」与「与预览同屏」；指引含「套 A4 请留白」；进度/成功 **不含**「画册」「跨页」 | W2 |

---

## 10. 实施任务（可落地）

原则：能加文件就加文件；改旧文件只做 **append / 一处分发**。禁止为了本出口去「顺手重构」`collage_pack`。

### W0 · 注册与隔离（先让第七项出现，后端可先 501）

**后端**

| ID | 任务 | 文件 |
|----|------|------|
| B-W0-01 | `AlbumLandscapeConfig(enabled: bool = True)` | `travelogue/config/studio.py` |
| B-W0-02 | 解析 `features.album_landscape` / `studio.album_landscape` | `travelogue/config/loader.py` |
| B-W0-03 | `studio_config_expose` 增加 `albumLandscape.enabled` | `travelogue/config/studio.py` |
| B-W0-04 | YAML 增加 `album_landscape` profile（§7） | `config/platform_profiles.yaml` |
| B-W0-05 | `PLATFORM_SEGMENT_IDS` / `KNOWN_PLATFORM_IDS` 收入本 id；新增 `SCREEN_CAPTURE_PLATFORM_IDS = frozenset({"album_landscape"})`；**不**写入 `COMPOSE_*` / `PHASE_A_*` / `DEFAULT_LONGSHOT2_*` | `travelogue/export/platform_profiles.py` |
| B-W0-06 | `file_prefix_for_platform`：`album_landscape` → `{slug}-landscape` | 同上 |
| B-W0-07 | `export_handlers`：flag 开则 `allowed_platforms.append("album_landscape")`；批量校验若含本 id → 400 `E_ALS_BATCH_FORBIDDEN` | `travelogue/web/studio_handlers/export_handlers.py` |
| B-W0-08 | `export_trip_longshot`：`pid == "album_landscape"` 时调用新模块（W0 可先 raise `E_ALS_DISABLED` 的占位，W1 换真实现） | `travelogue/export/longshot.py` |
| B-W0-09 | 单测：flag 关不在 allow；flag 开 prefix 正确；`test_collage_pack` / `test_album_slide_count` **零改预期** | `tests/unit/export/test_album_landscape_isolation.py`（新） |

**前端**

| ID | 任务 | 文件 |
|----|------|------|
| F-W0-01 | `PLATFORMS.album_landscape` 文案（§5.1）；`showAlbumCountOptions: false` | `templates/studio/js/longshot-export-panel.js` |
| F-W0-02 | `enabledPlatformsFromConfig`：白名单增加 `album_landscape`；**仅当** `cfgStudio.albumLandscape.enabled !== false` 时 append。禁止像 `album_spread` 那样无条件 concat | 同上 |
| F-W0-03 | 「画册印刷」subtitle / expectHtml 可加「3:4 对页」（D-ALS-13） | 同上 |
| F-W0-04 | 面板渲染顺序：在 `album_spread` 后插入本项（若 build 按数组序，保证 append 在 spread 之后） | 同上 |
| F-W0-05 | 多选/批量：从可勾选列表 **排除** `album_landscape` | `longshot-export-panel.js` + `preview-toolbar/longshot.js` |
| F-W0-06 | 单测/面板单测：flag 开有第七项，关无；六种 id 集合不变 | 现网 `test_longshot_client.py` 或面板单测 |

**W0 出门**：AC-ALS-01～03。点第七项可以 501/明确「即将截屏」，但不得误走 3:4。

### W1 · 按屏截图（内核）

**后端**

| ID | 任务 | 文件 |
|----|------|------|
| B-W1-01 | **新建** `travelogue/export/album_landscape.py`：`export_album_landscape(...)` 签名对齐 `export_collage_pack` 常用参数（`trip_dir`, `scale` 忽略几何、只作日志, `fmt`, `progress`, `cancel_*`, `base_url`/`port`） | 新文件 |
| B-W1-02 | 校验 `index.html`、screens 引擎、§4.1 收集（无浏览器的纯 HTML 解析可先单测选择器） | 同上 |
| B-W1-03 | Playwright：视口、藏壳、锁 16:9、逐屏截、letterbox、Writer | 同上；复用 `longshot._BROWSER_POOL`（import 池对象，不复制启动逻辑） |
| B-W1-04 | `longshot.py` 占位换成真调用 | `travelogue/export/longshot.py` **仅增一分支** |
| B-W1-05 | 进度 hint：`正在截取横版页 第 k/N 屏…`（禁「画册」） | `album_landscape.py` |
| B-W1-06 | 单测：HTML fixture 数页；断言不请求 longshot URL（mock page.goto）；`slideCount` 不影响 N；letterbox 尺寸；空 main → `E_ALS_NO_PAGES` | `tests/unit/export/test_album_landscape.py`（新） |
| B-W1-07 | 可选 1 条 Playwright smoke（有浏览器才跑）：真实 demo trip 导出 N>0 且 AR=16/9 | `tests/unit/export/test_album_landscape_smoke.py` 或现网 longshot smoke 旁 |

**前端**

| ID | 任务 | 文件 |
|----|------|------|
| F-W1-01 | `enabledPlatformsFromConfig`：白名单增加本 id；**仅当** flag 开 **且** 捕获已落地时 push；禁止无条件 concat | `longshot-export-panel.js` |
| F-W1-02 | 选中本平台：只读「页数与预览相同」，不估 N；`showAlbumCountOptions: false`；隐藏 scale（SHD-ALS-02） | 同上 |
| F-W1-03 | `isComposePlatform` 保持 false；自备 progressTitle「正在截取横版页…」 | 同上 |
| F-W1-04 | 进度条 `else if` 识别本 platform（禁止改 spread 文案）；hint 检测先匹配横版 | `templates/studio/preview-toolbar/longshot.js` |

**W1 出门**：AC-ALS-02、04～09、12。此时才点亮第七项。狗粮三册（SHD-ALS-05）预览对页数。

### W2 · 文案、取消、池、收口

**后端**

| ID | 任务 | 文件 |
|----|------|------|
| B-W2-01 | 取消与超时；`finally: release` 单测（mock pool） | `album_landscape.py` + 单测 |
| B-W2-02 | `user_hint` / `publish_guide` 走 profile（D-ALS-15） | profile + 导出结果 |
| B-W2-03 | CLI `export-longshot --platform album_landscape` 可用（若 CLI 只认已知 id，做 additive） | `travelogue/cli/` 里现网 platform 枚举 |

**前端**

| ID | 任务 | 文件 |
|----|------|------|
| F-W2-01 | 成功态文案（§5.2）；打开产物文件夹仍走现网 writer 目录 | `longshot.js` |
| F-W2-02 | 失败 toast 映射 §8 错误码 | `longshot.js` / 现网 error map |
| F-W2-03 | 运行中主按钮：「正在导出横版页…」；**不要**复用「画册跨页排队」 | `longshot.js` |
| F-W2-04 | Help 若有导出说明表，加一行横版画册（可选，不阻塞） | `help-onboarding.js` |

**W2 出门**：AC-ALS-10、11、13 + 六种回归再跑一遍。

### W3 · 不做（本主题冻结）

- Output Recipe intent
- 批量多选
- PDF 合订
- 印厂出血
- 与 EDC / AEL / 画册编排 的任何接线
- 把 `album_spread` 标成 deprecated

---

## 11. 回归护栏（六种不受影响）

合并本主题的 PR 必须保持：

| 护栏 | 怎么验 |
|------|--------|
| `COMPOSE_PLATFORM_IDS` 仍是四元 | 单测断言 frozenset 相等 |
| `DEFAULT_LONGSHOT2_PLATFORMS` 仍是五元 | 单测 |
| `tests/unit/export/test_collage_pack.py` | 全绿、不改断言 |
| `test_album_slide_count.py` / ABE / AEL 画册用例 | 全绿 |
| 批量单测仍只含原平台 | 新测只断言「含 landscape → 400」 |
| 前端 `enabledPlatformsFromConfig` 在 flag 关时返回的 id 集合与现网六种一致 | 单测 |

---

## 12. 风险

| 风险 | 缓解 |
|------|------|
| 顶栏叠在封面上被截进去 | 元素截图 + 捕获前强制隐藏壳（AC-ALS-07） |
| `viewport-fit` 导致不是 16:9 | 捕获 CSS 覆盖 + 最终 letterbox |
| 懒加载图未解码 | 单屏等 `img.complete`；超时记该页失败可重试整单 |
| 与长图抢浏览器池 | `finally release`；V1 不进批量 |
| 选择器漏章分隔 / 多算 hero | §4.1 冻结；用 1 本 demo 人工对屏数 |
| 实施时误改 `album_spread` 分支 | PR 检查清单：collage / grouper / ABE diff 必须为空 |

---

## 13. 开放问题

| ID | 问题 | V1 默认 |
|----|------|---------|
| **OQ-ALS-01** | `breath-pause-screen` 是否算一页？ | **已关 · 不算**（现网是节奏缝 · D-ALS-19）。日后若改成真 16:9 屏再开选择器。 |
| **OQ-ALS-02** | 默认 `device_scale_factor` 用 1 还是 2？ | **已关 · 2**（3840×2160）。不在 V1 做 UI。 |
| **OQ-ALS-03** | 要不要顺带出一份 PDF？ | **已关 · 否**。 |
| **OQ-ALS-04** | 开关默认 true 还是 false？ | **已关 · 配置默认 true**，对用户点亮遵循 D-ALS-16（与真捕获同出门）。 |

---

## 14. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-08-14 | 初稿。第七出口 `album_landscape`；按屏截 `index.html`；与六种及画册编排隔离；含 W0–W2 前后端任务。 |
| v0.2.0 | 2026-08-14 | [七席](./acceptance-records/als-album-landscape-screens-v1-review-2026-08-14.md) **Conditional Go**。回写 BLK-ALS-01～05：W0 不点亮菜单；池走公开 API；进度禁「画册」防串台；页集合不含呼吸缝；非 layout-screen 截视口 16:9 框；前端不得标 compose。OQ-01～04 关闭。 |
