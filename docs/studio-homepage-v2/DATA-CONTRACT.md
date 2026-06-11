# Studio 首页 v2 · 数据契约

> **权威**：工程实现与 QA 以本文 + `manifest.schema.json` 为准；PRD §11.2 / §13.1 仅作摘要。

---

## 1. demo-showcase · `manifest.json`

**路径**：`templates/studio/assets/demo-showcase/manifest.json`  
**加载**：`GET /__studio/assets/demo-showcase/manifest.json`（静态资源，无新 API）

### 1.1 顶层字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `version` | string | ✓ | 素材包版本；替换 assets 时 **必须递增**（cache-bust） |
| `title` | string | ✓ | 示例标题，如「京都·雨后」 |
| `meta` | object | | 工作台展示用 |
| `meta.photoCount` | number | | 照片张数 |
| `meta.chapterCount` | number | | 正文章节数（不含封面/尾声） |
| `meta.subtitle` | string | | 副标题/季节标签 |
| `assets.background` | string | ✓ | 相对路径 · Ken Burns 背景 WebP（≤180KB 预算） |
| `assets.longshot` | string | ✓ | 相对路径 · 9:16 长图 WebP |
| `pages` | array | ✓ | **卷轴单页序列**（见 §1.2） |

> PRD 旧稿写 `chapters` 一词 — **冻结为 `pages[]`**，每项带 `role` 区分封面/章/尾声。

### 1.2 `pages[]` · 单页（scroll 卷轴的一页）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✓ | 稳定 ID，如 `cover`、`ch01`、`epilogue` |
| `role` | enum | ✓ | `cover` \| `chapter` \| `epilogue` |
| `label` | string | ✓ | 无障碍 / dots 文案，如「封面」「第一章」 |
| `chapterIndex` | number | | `role=chapter` 时 1-based 章序号 |
| `webp` | string | ✓ | 相对路径 · 该页 16:9 spread **半页** WebP（文件名含 content hash） |

**约束**：

- 顺序固定：`cover` → `chapter`×N → `epilogue`（至少 3 项：cover + 1 chapter + epilogue）
- 所有 `webp` 同源 trip「京都·雨后」统一切图包
- 文件名建议：`scroll/{id}-{hash8}.webp`

### 1.3 Carousel · spread · dots 映射（M20-b 直接消费）

设 `pageCount = pages.length`，viewport 一次显示 **2 半页**（spread），横滑 **每次移动 1 半页**（D-10 **clamp，不 wrap**）。

| 概念 | 公式 / 规则 |
|------|-------------|
| **dot 数量** | `pageCount`（每 dot = 当前 **左缘对齐** 的 page 索引） |
| **carousel 索引 `i`** | `0 … pageCount - 1` |
| **scrollLeft** | `i × (viewportWidth / 2)` |
| **spread 内容** | 左半 = `pages[i]`；右半 = `pages[i+1]` 若存在，否则 **留白**（奇数尾页） |
| **clamp** | `i = clamp(requested, 0, pageCount - 1)`；首尾箭头 disabled |
| **键盘 ←/→** | 同上索引 ±1 clamp |

**示例**（5 pages：cover, ch1, ch2, ch3, epilogue）：

| i | 左半 | 右半 |
|---|------|------|
| 0 | cover | ch1 |
| 1 | ch1 | ch2 |
| 2 | ch2 | ch3 |
| 3 | ch3 | epilogue |
| 4 | epilogue | *(空白)* |

Lightbox scroll 模式：按 `pages[]` 顺序纵向拼接全部 `webp`（或单张长卷 asset，实现二选一，**首版用 pages 拼接**）。

### 1.4 冷启动 Importing 背景

无 Import 前壳层时，使用 `assets.background` 对应静帧 + veil（§9.2），不跑 Ken Burns。

---

## 2. 首页只读 API · 最小字段子集

> PRD：「无新增 API，继承 v1.4 §9」。本文为 **首页 v2 实际读取字段**，避免工程翻全量 PRD。

### 2.1 `GET /__travelogue/trips`

**用途**：Loading → IdleEmpty vs IdleReturning 路由；书架网格。

**响应形**（已有实现 `travelogue/web/studio_trips.py`）：

```json
{ "ok": true, "trips": [ /* TripRow */ ], "total": 12 }
```

**首页只读 · 每项 `TripRow`**：

| 字段 | 类型 | 首页用途 |
|------|------|----------|
| `tripId` | string | resume 链接、job 关联、埋点 |
| `title` | string | 书架卡标题 |
| `photoCount` | number | 书架副文案「N 张」 |
| `updatedAt` | number | 排序、相对时间（Unix 秒） |
| `previewUrl` | string | 卡片跳转 `/slug/index.html`（**非** Bento 封面源） |
| `previewRelPath` | string \| null | 封面图相对路径 → 拼 `GET /{tripId}/{previewRelPath}` |
| `longshotStale` | boolean | stale 徽章「长图待更新」 |
| `algorithmStale` | boolean | 算法/选片/排版配置过期（含审美、preview 等聚合） |
| `layoutCssStale` | boolean | 卷轴布局 CSS 过期；首页徽章「布局待更新」，预览内并入暂存状态条 |
| `aestheticStale` | boolean | 审美评分明细过期 |
| `cullStale` | boolean | 选片 `keepRatioFloor` 低于当前配置 |
| `layoutStale` | boolean | 封面/排版算法 hash 过期 |
| `previewStale` | boolean | `preview.jpg` 早于 `trip.json` |
| `staleHints` | string[] | 人类可读提示列表（书架 / Bento 条） |
| `staleHint` | string \| null | 首选提示文案 |

**首页派生（客户端）**：

| 派生 | 规则 |
|------|------|
| `coverUrl` | `previewRelPath ? \`/${tripId}/${previewRelPath}\` : null` |
| `isDemo` | `isDemoTrip(trip)`（`constants.js` 已有） |
| `hasUserTrips` | 存在 `trips` 且至少 1 条 **非** demo |
| `route` | **始终 Bento**；`hasUserTrips →` 追加下方书架区（IdleReturning），否则仅 Bento（IdleEmpty） |

**首页不读**：trip.json 全文、assets 列表、editor 配置。

**分页**：当前 `limit=20, offset=0`；书架规模化见 PRD §8.2 / 本文 §4。

### 2.5 `GET /__travelogue/trips/{tripId}/bento-preview`

**用途**：Bento Tab「我的最近一本」· manifest 形只读 payload。

**响应**（200）：`ok` + 与 §1.1 同形字段；`source: "user"`；`pages[].url` 为 `/{tripId}/…` 绝对路径（非 demo `webp`）。

**404**：无 `preview.jpg` → `E_BENTO_PREVIEW_UNAVAILABLE`。

**选取规则**：客户端对 `GET /trips` 取 **第一条非 demo**（`updatedAt` 降序）。

### 2.2 `GET /__travelogue/status?jobId=`

**用途**：Importing 进度、刷新恢复、FirstSuccess。

**首页只读 · `StudioJob`**：

| 字段 | 类型 | 首页用途 |
|------|------|----------|
| `jobId` | string | 与 `sessionStorage` 对齐 |
| `status` | enum | `queued` \| `running` \| `succeeded` \| `failed` \| `cancelled` |
| `stage` | string | 四阶段 machine key |
| `stageIndex` | number | 进度条 |
| `stageCount` | number | 恒 4 |
| `stageHint` | string | 用户可见阶段文案 |
| `tripId` | string \| null | 成功后 resume |
| `error` | object \| null | `error.code` → Toast |
| `result` | object \| null | `g1Pending` 等 FirstSuccess 分支 |

**轮询**：继承 `job-poll.js`；首页 v2 **不修改**轮询间隔与 endpoint。

### 2.3 `POST /__travelogue/studio-event`

见 [TELEMETRY.md](./TELEMETRY.md)。首页 v2 **扩展** ALLOWED 事件列表，endpoint 不变。

### 2.4 sessionStorage / localStorage（只读 + 新增）

**继承 v1.4 · v2 不得改形状**：

| 键 | 用途 |
|----|------|
| `travelogue.studio.activeJobId` | Import 恢复 |
| `travelogue.studio.activePending` | 冷启动 pending body |
| `localStorage` 见 `constants.js` `LS.*` | FirstSuccess 等 |

**v2 新增（加法）**：

| 键 | 用途 |
|----|------|
| `travelogue.studio.homepageVariant` | `v2` \| `v3` 持久分桶 |

**护栏**：v2 **禁止** rename/delete/改类型既有键；v3 读 storage 时 **忽略**未知键。回滚见 [FEATURE-FLAG.md](./FEATURE-FLAG.md)。

---

## 3. PRD 字段名对照（避免歧义）

| PRD / 口语 | 实际字段 |
|------------|----------|
| `count` | `photoCount` |
| `lastEditedAt` | `updatedAt` |
| `cover` | `previewRelPath` → URL |
| `stale`（长图） | `longshotStale` |
| `stale`（算法） | `algorithmStale` |
| `stale`（布局 CSS） | `layoutCssStale` |
| 重新排版 CTA | `POST /trips/{id}/curate` → job poll → `V2.reroute()` + `refreshUserBentoPreview` |
| `status`（trip） | **无服务端字段**；由 activeJob + trip 列表推断 |

---

## 4. 内容边界（PRD v2.0.3 补充）

### 4.1 书架规模化（§8.2）

| 条件 | 行为 |
|------|------|
| `total ≤ 20` | 单页网格，无分页 |
| `total > 20` | **M20-e 后迭代**：服务端分页 `limit/offset` +「加载更多」；M20 **不**做虚拟滚动 |
| 长标题 | 2 行 clamp + ellipsis（CSS `-webkit-line-clamp: 2`） |
| 无封面 | 纯色 `--forest` 底 + 标题首字/前两字 |

### 4.2 L2 懒加载触发（§12.4）

| 环境 | 行为 |
|------|------|
| loopback `127.0.0.1` | **默认 L0**；`effectiveType` 通常 `4g`，**L2 不触发** |
| L2 条件（实现） | `(navigator.connection?.saveData === true) \|\| ['slow-2g','2g'].includes(navigator.connection?.effectiveType)` |
| 若 connection 不可用 | 视为 fast；标注 **「L2 仅 saveData/慢网客户端；loopback 验收不测 L2」** |

L2 行为：carousel 仅 eager 加载 `pages[0..1]`，其余 `loading="lazy"`。
