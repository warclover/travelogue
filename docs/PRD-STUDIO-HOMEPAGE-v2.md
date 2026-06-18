# Travelogue Studio · 首页（工作台）产品需求文档 v2

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v2.0.6-HOMEPAGE**（D-14 草案） |
| **状态** | **Implemented · dogfood**（D-14 待开发；退役 v3 见 [PRD-M21-studio-homepage-v3-retirement.md](./PRD-M21-studio-homepage-v3-retirement.md)） |
| **页面路由** | **目标态（M21）**：`GET /` → `studio-home-v2.html`；过渡期见 [FEATURE-FLAG §1](./studio-homepage-v2/FEATURE-FLAG.md#1-门控点冻结--双路由模型) |
| **权威线框** | [wireframes/studio-homepage-output-first-v1.6.html](./wireframes/studio-homepage-output-first-v1.6.html)（**Web·空态 / iPad·横屏 / 书架** Tab；Mobile Tab 见 §0.4） |
| **关联文档** | [PRD-PHASE4.md](./PRD-PHASE4.md) · [PRD-PHASE5.md](./PRD-PHASE5.md) · [PRD-STUDIO-DUAL-LAYOUT.md](./PRD-STUDIO-DUAL-LAYOUT.md) · [API-MINIAPP.md](./API-MINIAPP.md) · [SHARING.md](./SHARING.md) |
| **开发前契约** | [DATA-CONTRACT](./studio-homepage-v2/DATA-CONTRACT.md) · [FEATURE-FLAG](./studio-homepage-v2/FEATURE-FLAG.md) · [PRE-DEV](./studio-homepage-v2/PRE-DEV.md) |
| **更新日期** | 2026-06-17 |

---

## 0. 文档说明

### 0.1 与 v1.4 PRD 的关系

| 维度 | v1.4 PRD（已落地 v3） | **本 PRD v2** |
|------|----------------------|---------------|
| 首页范式 | 影像优先 · Hero + SVG 样张 | **输出优先 · Bento 双交付 + 编辑背景** |
| 主 CTA | 选择照片文件夹 | **开始制作我的游记** → Import Sheet 内选文件夹 |
| 回访态 | Hybrid Hero | **恒常 Bento 首页 + 下方书架区**（网格） |
| 端范围 | wide + compact 浏览器 | **Web 桌面 + iPad 横屏**；**手机归小程序**（§0.4） |

**继承不变**（详见 v1.4）：五主态 + 两异常态 · API · pick-folder · FirstSuccess · sessionStorage · Toast/Modal · 认知支架。

### 0.2 设计决策摘要（v2 冻结）

| # | 决策 | 说明 |
|---|------|------|
| D-01 | **Bento 空态** | 16:9 + 9:16 并排 + 工作台；面板外编辑背景 |
| D-02 | **Carousel 屏数** | 封面 + 各章 + 尾声 |
| D-03 | **spread 预览** | Bento 内一屏两页；完整卷轴在 Lightbox / preview |
| D-04 | **Lightbox** | 整区轻点 + 拖拽阈值 + ⤢；不进 editor preview |
| D-05 | **Import Sheet** | 主 CTA 打开 bottom sheet；路径仅在 Sheet 内 |
| D-06 | **示例作品** | 人工精选 1 篇 · 统一 demo-flag |
| D-07 | **响应式** | ≥1024 与 **iPad 横屏** Bento 双列；**拒绝 768 堆叠** |
| D-08 | **回访** | **恒常 Bento 首页**；有用户画册时在 Bento **下方**追加书架区（不整页替换） |
| D-13 | **Bento 双 Tab**（**已由 D-14 supersede**） | v2.0.5：**示例作品** / **最近一本** 双 Tab；v2.0.6 起交互见 D-14 |
| D-14 | **预览画册选择器**（**草案 · v2.0.6**） | 单一选择器指定任意用户画册；**未指定 → 示例作品**；见 §6.8 |
| D-09 | **用词** | In-product「自动」；禁止突出 AI；见 §3.2 |
| D-10 | **Carousel 边界** | **到头 clamp，不循环 wrap**（spread 禁止尾声｜封面拼版） |
| D-11 | **灰度** | 并发 holdback + 性能/错误护栏；见 §19.2 |
| D-12 | **平台边界** | **M20 仅 Web + iPad 横屏**；手机 UI 由 **微信小程序** 承接；见 §0.4 |

### 0.3 修订摘要

**v2.0.6（草案）**：**D-14 预览画册选择器** — 工作台「预览画册」由双 Tab 改为单一 `<select>`（MVP）；用户可指定任意用户画册；未指定默认示例作品；`localStorage` 持久化；`bento-preview` API 不变。详见 §6.8 · [DATA-CONTRACT §2.5](./studio-homepage-v2/DATA-CONTRACT.md#25-get-__traveloguetripstripidbento-preview)。

**v2.0.5**：**D-13 方案 B′** — Bento 双 Tab「示例作品 / 我的最近一本」；`GET /trips/{id}/bento-preview`；demo-flag 仅示例 Tab。

**v2.0.4**：**D-08 方案 A** — 首页恒为 Bento；回访书架降为 Bento 下方区块；AC-HP2-11 / §8 / DATA-CONTRACT 路由修订。

**v2.0.3**：冻结 `manifest.json` schema（`pages[]`）· 首页 API 只读子集 · feature flag 规格 · telemetry M20-i 前置 · dev harness · AC 验证方式 · 线框 reconcile · §8.2/§12.4 边界补充。

**v2.0.2**：收窄端范围（手机→小程序）· 删除 M20 Mobile 空态/书架 · Loading/冷启动 · holdback · clamp · Sheet a11y。

### 0.4 平台边界与分工（D-12 · 冻结）

| 端 | M20 Studio `/` | 负责文档/产品 |
|----|----------------|---------------|
| **Web 桌面**（主窗口 ≥1024，或同机 `127.0.0.1:8766`） | Bento · Sheet · 书架 · pick-folder | **本 PRD** |
| **iPad 横屏**（768–1023 landscape） | 同 Web Bento 双列 | **本 PRD** |
| **iPad 竖屏 / 手机 / 过窄视口** | **不支持完整工坊** → §11.3 轻提示 | 本 PRD（壳层 only） |
| **手机（Phone）** | **不在 Studio Web 范围** | **[API-MINIAPP.md](./API-MINIAPP.md)** · 未来小程序 PRD（上传、进度、长图/卷轴消费） |

**架构事实（M20 信任话术地基）**：

- Studio Web **仅**面向运行 Studio daemon 的 **本机浏览器**（`http://127.0.0.1:8766`）。
- pick-folder / 路径 JSON：照片在用户磁盘；Studio 只读；**「照片留在本机 · 无需注册」** 成立。
- **不**在 M20 支持：手机浏览器访问 LAN IP、手机本地跑 Studio、公网云端 Studio。
- 手机端上传、Importing「请勿关闭页面」、Mobile 信任文案 → **小程序** 另立 PRD，**不**在本稿解。

**与 Phase 5 对齐**：路径 A 长图、路径 B 卷轴的 **手机侧消费与分享** 归小程序 + web-view；Studio Web 首页负责 **桌面工坊导入与双交付验货**。

**线框 v1.6 Mobile Tab**：**小程序方向探索稿**，**非** M20 Studio Web 验收依据（见 §20）。

---

## 1. 背景与问题

### 1.1 为何要 v2

（HP2-GAP-01～08：双交付可见、结果导向 CTA、示例标注、Lightbox 验货、书架回访等 — 略。）

### 1.2 产品目标与指标归属

**首页成功定义（M20）**：用户 **理解双交付** + 完成 **`import_start` / `import_success`**。

**不归首页 PRD**：share/export、保存长图、微信发送、小程序打开卷轴 — 归 **Phase 5 / preview toolbar / 小程序** 指标。

| ID | 目标 | 定性验收 | 代理指标 |
|----|------|----------|----------|
| **G-HP2-01** | 10s 理解双交付 | 5/5 能复述卷轴+长图 | 30s 内 `lightbox_open` 或 `sheet_open` ≥40% |
| **G-HP2-02** | 10s 找到主 CTA | 5/5 点「开始制作我的游记」 | `cta_click`/空态 PV ≥35% |
| **G-HP2-03** | 识别示例非本人数据 | 见 demo-flag | 首屏 demo-flag 可见性自动化 |
| **G-HP2-04** | 回访 5s 继续作品 | resume 可点 | `shelf_resume_click`/回访 PV ≥50% |
| **G-HP2-05** | 愿 Lightbox 验货 | ≥4/5 主动放大 | `lightbox_open`/空态 PV ≥25% |
| **G-HP2-06** | Phase 5 叙事一致 | 产品 sign-off | — |
| **G-HP2-07** | 导入漏斗 | — | `import_success`/`import_start` ≥85%（24h） |

### 1.3 北极星漏斗（Studio Web · M20）

```
homepage_view(state 确定后)
  → cta_click → sheet_open → folder_picked → import_start → import_success
         ↘ lightbox_open（验货）
```

### 1.4 非目标（M20）

- 手机 Studio 首页（空态/书架/上传 Sheet）
- 手机浏览器 / LAN 访问 Studio 的完整产品支持
- 小程序内 UI（见 API-MINIAPP）
- Web 768 Bento 三行堆叠
- 首页 editor preview iframe · 首页改字/导出
- macOS pick-folder 首发 · 账号/云端 · **UI 国际化（EN）**

---

## 2. 目标用户与场景

| Persona | M20 触点 |
|---------|----------|
| **A · 首次旅行者** | Web Bento → Sheet → pick-folder |
| **B · 回访编辑者** | 同一 Bento 首页 · 下方书架 resume |
| **C · 好奇试用者** | 示例 Lightbox → CTA |
| **D · 审美敏感** | spread + 编辑背景 + 示例质量 |

**User Stories（M20）**：US-HP2-01～05、08（双交付、Slogan、Lightbox、结果 CTA、示例标注、iPad 横屏 Bento）。**US-HP2-07（手机上传）** 移出至小程序 backlog。

---

## 3. 产品定位与文案

### 3.1 定位（冻结）

Slogan：**照片导进来，画册自动出来。**

Lead：选一次旅行的照片，**自动分章 · 配文 · 排版**，生成大屏卷轴 + 微信长图。

### 3.2 「自动」vs「智能/AI」（D-09）

| 场景 | 允许 | 禁止 |
|------|------|------|
| Bento / Sheet / 进度 | **自动**分章、配文、排版 | **AI 自动生成**、主界面大字「智能」 |
| 对外营销 / 商店 / 落地页 | 智能游记、AI 辅助 | — |

**Rationale**：产品 chrome 用可验证的「自动」降 over-promise；营销可用「智能」获客——**产品层与营销层刻意分层**。

### 3.3 自动能力标签（Web 空态）

自动分章成文 · 自动配文选封面 · **本地处理 · 免注册**（pick-folder @ loopback）。

### 3.4 双交付用户语言

大屏卷轴 · 16:9 · 沉浸阅读 | 竖版长图 · 9:16 · 发微信

（Bento 内 9:16 手机框为 **样张预览**；真实手机消费归小程序/导出长图。）

### 3.5 信任话术（Studio Web · loopback 冻结）

| 触点 | 文案 |
|------|------|
| 工作台 meta | 照片留在本机 · 无需注册 · 下一步选择照片文件夹 |
| Importing 预估 | 预计… · **可离开稍后回来**（Job 在 Studio 进程内续跑） |
| 禁止 | 未定义架构条件下的「若…」式隐私承诺 |

### 3.6 CTA 层级

| 层级 | 文案 | 行为 |
|------|------|------|
| 主 CTA | 开始制作我的游记 → | Import Sheet |
| Sheet 主按钮 | 选择本次旅行的照片文件夹 | pick-folder · autoStart |
| 书架新建 | + 选择文件夹新建 | Sheet / pick |

---

## 4. 信息架构

### 4.1 分态布局（M20 · Web + iPad 横屏）

| 状态 | UI |
|------|-----|
| **Loading** | **全页 skeleton**（§4.4）；不渲染 Bento/书架 |
| **IdleEmpty** | Bento（无书架区） |
| **IdleReturning** | **Bento + 下方书架区**（同一 URL `/v2`） |
| **Importing** | Import 前壳层 blur **或** §10.1 冷启动静帧背景 |
| **FirstSuccess / Failed / Offline** | 继承 v1.4 |

### 4.2 Bento 网格

```
┌─────────────────────┬──────────┐
│ 16:9 spread carousel │ 9:16 框  │
├─────────────────────┤ 通高内滚 │
│ 工作台 132px         │          │
└─────────────────────┴──────────┘
```

Grid：`1fr 172px` · gap 10px。

### 4.3 与 preview 分工

Lightbox = 只读验货；编辑 preview 仅 **书架 resume / FirstSuccess**。

**P2 deferred**：Lightbox 内「查看完整示例（只读）」→ demo share 态 URL。

### 4.4 Loading 时序与首屏事件（v2.0.2）

1. **`GET /trips` resolve 前**：仅 skeleton；**禁止**先渲染 Bento 再切书架（防闪屏）。
2. **若 `sessionStorage.activeJobId`**：resolve 后直接 **Importing**（跳过 Idle）；背景用 §10.1 冷启动规则。
3. **resolve 后**：**始终**渲染 Bento 首页；若存在非 demo 用户画册，在 Bento 下方追加书架区（IdleReturning）；无用户画册则仅 Bento（IdleEmpty）。
4. **`homepage_view`**：**仅**在最终态首帧触发，属性含 `state: empty|returning|importing`、`layout: wide|tablet_landscape|unsupported`、`variant: v2|v3`。

---

## 5. 页面状态机

五主态 + 两异常态（Loading / IdleEmpty / IdleReturning / Importing / FirstSuccess + Failed / Offline）。

| 状态 | v2 UI |
|------|-------|
| IdleEmpty | Bento |
| IdleReturning | Bento + 下方书架区 |
| Importing | blur 或冷启动静帧 + 进度面板 |
| Import Sheet | 叠加 IdleEmpty Bento |

---

## 6. Web 空态 Bento

### 6.1 顶栏

**已移除**（v2.0.6）。首屏不再显示 `TRAVELOGUE · STUDIO` / 地址复制条；离线状态由 `#v2-offline` 横幅承担。

loopback dev 下「经典首页 → /」链迁入 **Dev Panel**（`?dev=1` 或 `data-studio-dev=1`），Import 进行中仍隐藏（AC-HP2-23）。

### 6.2 Slogan 区

Eyebrow + H1 + lead + auto-tags。`layout-bento__frame` top 在 iPad 横屏/矮视口验收无 overlap（建议 268px，矮屏 ~300px）。

### 6.3 编辑背景

同一示例 trip：Ken Burns · grain · vignette。**素材必须统一**（默认 京都·雨后 golden trip）。

### 6.4 16:9 Carousel

| 项 | 规格 |
|----|------|
| **预览画册（D-14）** | 默认 **示例作品**；用户可从 select 指定任意非 demo 画册（`GET /trips` 首屏列表）；见 §6.8 |
| demo-flag | **仅**选中 **示例作品** 时显示 |
| 用户画册 | 工作台标题为 trip 名；数据来自 `GET /trips/{id}/bento-preview` |
| 屏数 | 封面 + N 章 + 尾声 |
| spread | 50% 宽 · 每次滑 1 页 |
| **边界（D-10）** | **到头 clamp，不 wrap**；禁止末页｜封面循环拼版 |
| **奇数尾页** | 最后一页 **左对齐**，右侧 **刻意留白**（杂志 bleed） |
| 导航 | 箭头 · dots（`aria-current`）· ⤢ |

#### Lightbox 触发

| 输入 | 行为 |
|------|------|
| 轻点（位移 ≤ 阈值） | 开 Lightbox |
| ⤢ / Enter | 开 Lightbox |
| 横拖 >10px（pointer）/ >8px（touch） | 仅翻页 |
| 9:16 内滚超阈值 | 仅滚动 |

常量：`LIGHTBOX_DRAG_THRESHOLD_PX` — 单测覆盖。

### 6.5 9:16 手机框（Bento 内样张）

label + demo-flag · 内滚 · 轻点/⤢ → Lightbox（**非**真机小程序 UI）。

### 6.6 工作台

示例信息 + **开始制作我的游记 →** · meta §3.5。

### 6.7 Lightbox

卷轴堆叠 / 长图竖滚 · focus trap · Esc · 不进 editor preview。

### 6.8 预览画册选择器（D-14 · v2.0.6 草案）

> **替代** D-13 双 Tab 交互形态；**保留** `bento-preview` API 与 manifest 形态。

#### 6.8.1 背景与范围

| 属性 | 内容 |
|------|------|
| **用户价值** | 多本创作者可在首页固定展示「代表作」；验货时可切换任意已完成画册；演示/截图可复现 |
| **MVP 包含** | ghost-select + `localStorage` + 边界态 + 测试 + D-13 迁移 |
| **MVP 不含** | 全库搜索、URL deep link、服务端偏好同步、导入后强制切换预览 |

#### 6.8.2 交互与 IA

| 项 | 规格 |
|----|------|
| **控件位置** | Bench 快捷区，原 `#v2-bench-source-tabs` 位置 |
| **Side label** | **预览画册**（原「预览来源」） |
| **控件类型（MVP）** | 原生 `<select class="v2-bench__ghost-select">`，模式对齐 `#v2-theme-select` |
| **选项结构** | ① 固定首项 `value=""` → **示例作品**；② 动态项 → `GET /trips` 首屏非 demo 画册（`updatedAt` 降序） |
| **demo-flag** | 仅当选中 **示例作品** 时显示 `#v2-bench-sample-flag` / `[data-demo-flag]` |
| **Phase 2** | Combobox + 缩略图 popover；书架卡片菜单 **「在上方预览」** |

#### 6.8.3 状态模型

| 字段 | 类型 | 含义 |
|------|------|------|
| `V2.bentoPreviewTripId` | `null \| string` | `null` = 示例；非 null = 指定 tripId |
| `V2.bentoTab` | `"demo" \| "mine"` | **派生**：`bentoPreviewTripId ? "mine" : "demo"`（兼容 stale / 遥测 shim） |
| `V2.userManifest` | manifest \| null | 当前选中用户画册的 bento-preview 缓存 |
| `V2.userPreviewTrip` | trip row \| null | 对应 `GET /trips` 行（stale / curate） |

**localStorage 键（加法）**：`travelogue.studio.v2.bentoPreviewTripId` — 值 tripId；删除键或空字符串 ≡ 未指定。详见 [DATA-CONTRACT §2.4](./studio-homepage-v2/DATA-CONTRACT.md#24-sessionstorage--localstorage只读--新增)。

#### 6.8.4 默认与边界行为（冻结）

| 场景 | 行为 |
|------|------|
| 首次访问 / 无 preference | **示例作品** |
| 有 preference 且 trip 存在、preview 可用 | 加载该本 `bento-preview` → 渲染 Bento |
| preference 指向已删除 trip | 清除 preference → **回示例** + toast「原预览画册已不可用，已切回示例」 |
| 用户选中 trip 但 `bento-preview` 404 | **保持选中**；Bento 占位帧 + bench 内联提示「预览尚未就绪」+ CTA「打开画册」；**禁止**静默换其他画册 |
| 无用户画册 | select 仅「示例作品」一项（或 disabled + title 提示） |
| 离线 | 用缓存 trips 填充选项；fetch 失败不清 preference |
| Import / FirstSuccess 完成 | **不自动**写入 preference；可选 toast 行动点「设为首页预览」（Phase 2） |
| trips 分页外画册 | MVP 选择器不可见；Phase 2 书架「在上方预览」 |

#### 6.8.5 与相邻区域分工

| 区域 | 职责 |
|------|------|
| **预览画册 select** | 切换 Bento 主舞台（carousel + phone strip + 背景） |
| **Bench 左栏 recent 卡** | 导航打开成稿（`<a href>`）；若 `tripId === bentoPreviewTripId` 加 `is-previewing` 描边（Phase 2） |
| **「继续上次」** | 导航，与预览 preference **独立** |
| **书架** | 打开 / 删除 / 长图；Phase 2 菜单加「在上方预览」 |

#### 6.8.6 数据与 API

- 示例：`GET /__studio/assets/demo-showcase/manifest.json`
- 用户：`GET /__travelogue/trips/{tripId}/bento-preview`（404 → `E_BENTO_PREVIEW_UNAVAILABLE`）
- 画册列表：`GET /__travelogue/trips?limit=20&offset=0`
- **后端 MVP 无变更**；客户端可请求**任意非 demo** tripId

#### 6.8.7 迁移（D-13 → D-14）

一次性迁移（首版加载脚本）：

- 若 localStorage 无新键、且 session 内曾使用 `mine` Tab：将当时 `V2.userPreviewTrip.tripId` 写入 `bentoPreviewTripId`
- 新用户与未交互用户：**不**自动切 mine

> D-13 的「有 manifest 则自动 mine」逻辑 **删除**。

#### 6.8.8 遥测

| 事件 | Payload | 说明 |
|------|---------|------|
| `bento_preview_select`（新增） | `{ trip_id: string \| null, source: "select" }` | `trip_id: null` = 示例 |
| `bento_tab_switch` | 保留 1 个版本 | shim 触发或 deprecate；allowlist 需同步 |

#### 6.8.9 验收标准

| ID | Given | When | Then |
|----|-------|------|------|
| AC-D14-01 | 无 preference | 打开首页 | Bento 展示示例作品；demo-flag 可见 |
| AC-D14-02 | 有 2+ 用户画册 | select 选 B | carousel / 长图 / 背景切为 B；demo-flag 隐藏 |
| AC-D14-03 | 选中 B 后刷新 | 硬刷新 | 仍展示 B（localStorage） |
| AC-D14-04 | preference 指向已删 trip | 打开首页 | 回示例 + toast |
| AC-D14-05 | B 无 preview.jpg | 选 B | 占位 + 说明；select 仍显示 B；不切 A |
| AC-D14-06 | 无用户画册 | 打开首页 | select 仅示例；与 AC-D14-01 一致 |
| AC-D14-07 | B 有 algorithmStale | 选 B | stale bar 出现且绑定 B |
| AC-D14-08 | curate 完成 | reroute | 若 preference 仍为 B，刷新 B 的 manifest |

#### 6.8.10 Phase 划分

| Phase | 内容 | 估时 |
|-------|------|------|
| **MVP（D-14）** | ghost-select + localStorage + 边界 + 测试 + 迁移 | 1.5–2d |
| **Phase 2** | Combobox 封面 / stale chip；recent 卡高亮；书架「在上方预览」 | +1d |
| **Phase 3** | 分页加载 / 搜索；`?preview=` deep link；FirstSuccess CTA | +1–2d |

---

## 7. Import Sheet

对齐 Phase 4 · max-height 58% · scrim blur · 步骤 1/2 · 路径在 details。

### 7.1 Sheet a11y

| 项 | 要求 |
|----|------|
| 角色 | `role="dialog"` · `aria-modal="true"` |
| 焦点 | 打开 trap 至 Sheet；关闭 **归还**触发 CTA |
| 键盘 | Esc 关闭 |
| 触控 | 关闭按钮 ≥44px |

---

## 8. Web 书架（首页内回访区 · 方案 A）

**位置**：`/v2` Bento 首屏 **下方**（滚动可见）；**不**再整页替换 Bento。

内容：标题 **你的游记画册** · resume 卡 · 网格 · + 新建 · stale → 更新长图。

### 8.1 边界态

| 条件 | UI |
|------|-----|
| trips Loading | 全页 skeleton；**不**显示 Bento / 书架 |
| trips 失败 | 错误条 + 重试 |
| Importing | 全局 Importing；**无**半导入卡 |
| Failed import | 无 trip 入库 |
| 仅 demo trip | 徽章 **示例** |

### 8.2 规模化与兜底（v2.0.3）

| 条件 | 行为 |
|------|------|
| `total ≤ 20` | 单页网格 |
| `total > 20` | M20-e 后迭代分页；M20 不做虚拟滚动 |
| 长标题 | 2 行 ellipsis |
| 无封面 | 纯色底 + 标题缩写 |

详见 [DATA-CONTRACT §4.1](./studio-homepage-v2/DATA-CONTRACT.md#41-书架规模化82)。

---

## 9. Importing 与生命周期

### 9.1 Importing UI（Web · pick/path @ loopback）

来源 · 文件夹 · … · 四阶段中文 · **可离开稍后回来** · 取消 → Modal。

### 9.2 冷启动 Importing 背景

无「Import 前壳层」时（如关 tab 后再开、`activeJobId` 恢复）：使用 **demo-showcase 封面静帧 + veil**（无 Ken Burns），**不**闪 Idle 再切 Importing。

### 9.3 生命周期

| 事件 | 行为 |
|------|------|
| 刷新 | `activeJobId` → 续 poll Importing |
| 关 tab 再开 | Studio 进程内 Job 续跑 → 恢复 Importing + 冷启动背景 |
| 「可离开」 | **本机 Studio 服务续跑**；非跨设备 |
| 取消 | 无半成品 trip → Import 前态 |
| 成功 | FirstSuccess；背景 = Import **前** Bento 壳层（书架区若已有则同屏保留） |

---

## 10. 响应式（M20）

### 10.1 支持矩阵

| 视口 | 布局 |
|------|------|
| **≥1024px** | Bento 双列 |
| **768–1023 横屏** | Bento 双列（iPad 横屏） |
| **768–1023 竖屏** | §10.3 旋转提示 |
| **&lt;768 或 phone UA** | §10.3 不支持提示 |
| **桌面窄窗 &lt;768** | §10.3 或 `min-width:1024` 提示拉宽；**不**加载 v3 compact 上传流 |

**拒绝**：768 Web 三行 Bento 堆叠。

### 10.2 与 PRD-STUDIO-DUAL-LAYOUT

M20 **不**扩展 compact 为手机产品路径。`data-studio-layout=compact` 若仍存在，仅用于 v3 过渡；v2 flag 开启时 **优先** unsupported 提示或拉宽引导，**不**实现 v2 Mobile 空态。

### 10.3 轻提示页（UnsupportedViewport）

| 场景 | 文案要点 |
|------|----------|
| iPad 竖屏 | 请 **旋转至横屏** 使用 Studio |
| 手机 | 请在 **电脑浏览器** 打开 Studio；手机阅读/分享请用 **微信小程序**（见 Phase 5 / API-MINIAPP） |
| 桌面过窄 | 请 **拉宽窗口** 至 1024px 以上 |

可选：QR/链接指向小程序（小程序上线后）。**M20 不要求** LAN 扫码访桌面。

---

## 11. 示例作品

### 11.1 策略

1 篇人工精选 · demo-flag · 不 pipeline 自动最新。

### 11.2 资源与缓存（ops）

```
templates/studio/assets/demo-showcase/
  manifest.json           # 见 manifest.schema.json
  manifest.schema.json
  scroll/{id}-{hash}.webp # 16:9 半页（spread 单页）
  longshot.webp
  background.webp
```

**Schema 权威**：[DATA-CONTRACT §1](./studio-homepage-v2/DATA-CONTRACT.md#1-demo-showcase--manifestjson) · [`manifest.schema.json`](../templates/studio/assets/demo-showcase/manifest.schema.json)

- 顶层：`version`, `title`, `meta?`, `assets`, **`pages[]`**
- 每页：`id`, `role`（cover/chapter/epilogue）, `label`, `webp`, `chapterIndex?`
- carousel dots = `pages.length`；spread clamp 映射见 DATA-CONTRACT §1.3

发版替换 assets 须 **hash 文件名或 manifest.version** cache-busting，避免老用户见旧示例。

**设计派单**：[DEMO-ASSETS-BRIEF](./studio-homepage-v2/DEMO-ASSETS-BRIEF.md) — **M20-a 前置 blocker**。

### 11.3 useDemoAlbum · Bento 数据源

- Bento **示例作品**（`bentoPreviewTripId === null`）永不 import；数据仅 demo-showcase。
- **用户指定画册**（D-14）：只读该 trip 的 `preview.jpg` / 章节 PNG / longshot；**不**替换示例素材包。
- 试用示例仍走 Sheet 三级入口；书架 demo 标 **示例**。


### 11.4 加载失败

Slogan + CTA + 占位；不白屏（AC-HP2-22）。

---

## 12. 视觉 · 性能 · a11y

### 12.1 气质与字体

编辑室 + showroom；display serif Slogan + UI sans。

### 12.2 对比度

叠图文字 WCAG AA 4.5:1，或 ≥40% 暗色蒙版。

### 12.3 性能预算（loopback P95）

| 指标 | 目标 |
|------|------|
| LCP | ≤ **2.5s** |
| 首屏背景 | ≤ **180KB** WebP |
| demo-showcase 总包 | ≤ **800KB** |
| homepage v2 JS 增量 | ≤ **+30KB** gzip |

### 12.4 降级

| 层级 | 触发 | 行为 |
|------|------|------|
| L0 | 默认 | Ken Burns + grain + blur |
| L1 | `prefers-reduced-motion` | 静态背景 · 无 Ken Burns · 无 breathing · **无 pulse-hint 动画** |
| L2 | saveData / 慢网 | 懒加载 carousel 2–5 屏 |
| L3 | assets 失败 | §11.4 |

**L2 注（v2.0.3）**：loopback `127.0.0.1` 通常不触发 L2；验收以 L0/L1/L3 为主。触发条件与 `navigator.connection` 见 [DATA-CONTRACT §4.2](./studio-homepage-v2/DATA-CONTRACT.md#42-l2-懒加载触发124)。

### 12.5 Design Tokens

| Token | 用途 |
|-------|------|
| `--demo-flag-bg/border` | 示例作品（**独立于** `--slot` 占位槽紫） |
| `--gold` / `--cream` / `--forest` | 强调 / CTA |

### 12.6 无障碍

Carousel ←/→ · dots `aria-current` · Lightbox trap · Sheet §7.1 · 触控 ≥44px · §12.2 对比度。

---

## 13. 数据 · API · 埋点

### 13.1 API

无新增 endpoint；继承 v1.4。**首页 v2 只读字段子集**：[DATA-CONTRACT §2](./studio-homepage-v2/DATA-CONTRACT.md#2-首页只读-api--最小字段子集)（`GET /trips` · `GET /status` · sessionStorage 护栏）。

### 13.2 事件（M20-h）

| 事件 | 触发 | 属性 |
|------|------|------|
| `experiment_exposure` | 分桶曝光 | `variant`, `bucket_id` |
| `homepage_view` | 最终态首帧 | `state`, `layout`, `variant` |
| `cta_click` | 开始制作… | `surface: bench` |
| `sheet_open/close/abandon` | Sheet | `reason` |
| `folder_picked` | pick 成功 | `auto_start` |
| `import_*` | import 生命周期 | `source: folder\|path\|demo` |
| `lightbox_open` | 放大 | `type: scroll\|longshot`, `surface: bento` |
| `spread_page_view` | 翻页 | `page_index` |
| `shelf_resume_click` | 继续编辑 | `trip_id`, `stale` |

**删除 M20 事件**：`mobile_sheet`、`mobile_dual` 等手机 Studio 事件（归小程序 PRD）。

**M20-i 硬前置**：holdback 需真实聚合 + 看板 + LCP/JS error — 见 [TELEMETRY.md](./studio-homepage-v2/TELEMETRY.md)。首版 localStorage ring buffer **不足以**支撑 §17.2 回滚判据。

### 13.3 sessionStorage

继承 v1.4 + **`travelogue.studio.homepageVariant`（加法）**。v2 **不得**改动既有键形状；回滚护栏见 [FEATURE-FLAG §4](./studio-homepage-v2/FEATURE-FLAG.md#4-v3-共存护栏工程-ci)。

---

## 14. 组件清单（M20）

| ID | 名称 |
|----|------|
| CMP-HP2-01 | OutputLightbox |
| CMP-HP2-02 | ImportSheet |
| CMP-HP2-03 | BentoEmptyLayout |
| CMP-HP2-04 | ScrollCarousel（clamp） |
| CMP-HP2-05 | PhoneLongshotPreview |
| CMP-HP2-06 | WorkbenchBar |
| CMP-HP2-07 | DemoFlag |
| CMP-HP2-08 | AutoTags |
| CMP-HP2-11 | WebShelf |
| CMP-HP2-13 | ImportProgressOverlay |
| CMP-HP2-14 | HomepageVariantGate |
| CMP-HP2-15 | UnsupportedViewport |

**移出 M20**：CMP-HP2-09 MobileEmptyLayout · CMP-HP2-10 DualDeliveryCards · CMP-HP2-12 MobileShelf → 小程序 backlog。

---

## 15. 文案规范

| 位置 | 文案 |
|------|------|
| 主 CTA | 开始制作我的游记 |
| Sheet | 选择本次旅行的照片文件夹 |
| 信任 | 照片留在本机 · 无需注册 |
| Importing | 可离开稍后回来 |
| 样张 | 示例作品 |
| 禁止 in-product | AI 自动生成 |

---

## 16. 验收标准

> **验证方式列**（自动 / 人工 / 可用性）：[AC-VERIFICATION.md](./studio-homepage-v2/AC-VERIFICATION.md)

| ID | Then |
|----|------|
| AC-HP2-01 | 5/5 被试 10s 内复述卷轴+长图两种用途 |
| AC-HP2-02 | 16:9/9:16 均有 demo-flag |
| AC-HP2-03 | 示例同一 trip 素材 |
| AC-HP2-04 | 屏数 = 封面+章+尾声 |
| AC-HP2-05 | spread 每次 1 页；dots 一致 |
| AC-HP2-06 | 轻点/⤢ Lightbox；不进 editor |
| AC-HP2-07 | 横拖不误触 Lightbox |
| AC-HP2-08 | 奇数尾页左对齐留白 |
| AC-HP2-09 | carousel **首尾 clamp 不 wrap** |
| AC-HP2-10 | 主 CTA → Sheet；路径仅在 Sheet |
| AC-HP2-11 | trips≥1 → Bento **与**书架区同屏；Loading 无错误态闪屏 |
| AC-HP2-12 | iPad 1024 横屏 Bento；无 768 堆叠 |
| AC-HP2-13 | 手机访问 → Unsupported 提示（非 Mobile 空态） |
| AC-HP2-14 | iPad 竖屏 → 旋转提示 |
| AC-HP2-15 | Importing 取消无半成品 |
| AC-HP2-16 | 刷新 activeJobId 续 poll |
| AC-HP2-17 | 冷启动 Importing 有静帧背景 |
| AC-HP2-18 | FirstSuccess 背景 = Import 前壳层 |
| AC-HP2-19 | carousel 键盘 ←/→ |
| AC-HP2-20 | 对比度 AA |
| AC-HP2-21 | 触控 ≥44px |
| AC-HP2-22 | assets 失败不白屏 |
| AC-HP2-23 | flag 回滚；Import 中禁切换 variant |
| AC-HP2-24 | Sheet focus trap · Esc · 焦点归还 CTA |
| AC-HP2-25 | `homepage_view` 仅在 state 确定后上报 |
| AC-D14-01 … 08 | 预览画册选择器 · 见 §6.8.9 |

---

## 17. Gap · 灰度 · 里程碑

### 17.1 v3 → v2 Gap（P0 摘要）

Bento · Sheet · 双交付预览 · Lightbox · Web 书架 · 示例策略 · unsupported 视口。

### 17.2 灰度与回滚（D-11）

| 项 | 规格 |
|----|------|
| Flag | `studio.homepage.v2_bento` — 规格 [FEATURE-FLAG.md](./studio-homepage-v2/FEATURE-FLAG.md) |
| 分桶 | **并发 holdback**：同期 v2 曝光 vs v3 曝光；`experiment_exposure` 必报 |
| 阶段 | dogfood → 10%（holdback）→ 100% |
| **回滚判据**（24h，**同期 holdback 对比**，任一触发） | `import_success/import_start` ↓>15%；`cta_click` ↓>20%；**LCP P95 恶化 >30%**；**homepage JS error rate ↑>2×** |
| Import 中 | **禁止**切换 variant |
| 10% 阶段 | **禁止**仅用历史 v3 baseline 自动回滚 |

### 17.3 里程碑

| ID | 范围 | 硬前置 |
|----|------|--------|
| M20-a | Bento + Slogan + demo-showcase | DATA-CONTRACT · FEATURE-FLAG · **demo 素材交期** |
| M20-b | Carousel spread + clamp + 尾页 | manifest.pages · spread spike |
| M20-c | Lightbox + 阈值 + ⤢ | Lightbox spike |
| M20-d | Import Sheet + §7.1 a11y | M20-a |
| M20-e | Web 书架 + §8.1 | M20-a |
| M20-f | iPad 横屏 + §10 Unsupported | M20-a |
| M20-g | Loading 时序 + 冷启动 Importing | DEV-HARNESS（URL param） |
| M20-h | 埋点 + AC 全量 | DEV-HARNESS 全量 |
| M20-i | 灰度 holdback + 回滚演练 | **TELEMETRY 聚合 + 看板** |
| M20-j | 默认 v2 | M20-i 演练通过 |

**移出 M20**：原 M20-f Mobile 空态/双交付条 → **小程序**。

---

## 18. 线框与 PRD

| 线框 v1.6 | PRD v2.0.2 | 工程以谁为准 |
|-----------|------------|--------------|
| **Mobile Tab 全套** | **非 M20**；小程序探索 | **PRD**；不实现 |
| carousel 取模循环 | **clamp 不 wrap** | **PRD** · v1.6 已改 clamp |
| 整区 click Lightbox | 轻点+阈值+⤢ | **PRD** · v1.6 已补 ⤢ 按钮 |
| 9:16 无 demo-flag | 必须有 | **PRD** · v1.6 已补 |
| 素材不一致 | 同一 trip | **PRD** |
| sidebar 旧话术 | v2.0.3 口径 | **PRD** · v1.6 已 reconcile |

**分工**：布局视觉参考 v1.6 **Web·空态 / iPad / 书架** Tab；交互文案以 **本 PRD** 为准。

---

## 19. 版本历史

| 版本 | 说明 |
|------|------|
| **v2.0.6**（草案） | D-14 预览画册选择器（supersede D-13 Tab 交互） |
| **v2.0.5** | D-13 Bento 双 Tab + bento-preview API |
| **v2.0.4** | D-08 方案 A：恒常 Bento + 下方书架区 |
| **v2.0.3** | 开发前契约包；manifest schema；flag/telemetry/harness；AC 验证方式；§8.2/§12.4；线框 reconcile |
| **v2.0.2** | 收窄 Web+iPad 横屏；手机→小程序；Loading/冷启动；holdback；clamp；Sheet a11y；指标划界；删 Mobile M20 |
| v2.0.1 | 审阅修订（Mobile 话术等，已由 v2.0.2 替代范围） |
| v2.0.0 | v1.6 首版 |
| v1.4.0 | v3 实现基线 |

---

## 20. 实施指引

| 角色 | 动作 |
|------|------|
| 设计 | [DEMO-ASSETS-BRIEF](./studio-homepage-v2/DEMO-ASSETS-BRIEF.md) 京都切图 · v1.6 已 reconcile |
| 前端 | [PRE-DEV](./studio-homepage-v2/PRE-DEV.md) · Bento · clamp · flag · harness |
| 数据/平台 | [TELEMETRY](./studio-homepage-v2/TELEMETRY.md) M20-i 前看板 · [OPEN-QUESTIONS](./studio-homepage-v2/OPEN-QUESTIONS.md) |
| 小程序 | 另立项；参考 API-MINIAPP + v1.6 Mobile Tab IA |
| QA | AC-HP2-01～25 · iPad 横屏 · 手机→Unsupported |

**顺序**：M20-a → d → b → c → e → f → g → h → **i** → j。
