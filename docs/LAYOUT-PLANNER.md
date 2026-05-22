# Travelogue · 横竖版统计与版面编排（Layout Planner）

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.2 |
| **文档角色** | **算法 / 工程细则**（产品需求见 [PRD-LAYOUT.md](./PRD-LAYOUT.md)） |
| **状态** | 已拍板（规则）· 代码 `travelogue/curation/layout_planner.py` |
| **关联** | `PRD-LAYOUT.md`、`ADAPTIVE-LAYOUT.md`、`TEMPLATE-visual-journal.md`、`PRD-MVP.md` §6.3 |
| **更新日期** | 2026-05-19 |

---

## 1. 目标

在用户选定 **手机 9:16** 或 **Web 16:9** 版面后，系统应：

1. **统计** 上传照片数量及 **五类构图** 数量；  
2. **按版面规则** 将照片编排为 `media-card` / `media-row` / `media-scroll`；  
3. 对 **1:1、全景、超长竖、非标准裁切比例** 单独处理，避免强行塞进标准横/竖模板。

---

## 2. 输入与输出

### 2.1 输入

| 字段 | 来源 |
|------|------|
| `assets[].width/height` | ingest 按构图类型裁切后的展示尺寸 |
| `assets[].aspectKind` | 可选；`classify_aspect` 写入 |
| `exportLayout` | `trip.json`：`auto` \| `mobile` \| `web` |
| 章内照片顺序 | 策展 Agent / 用户排序 |

### 2.2 输出

**统计**（`trip.curation.orientationSummary`）：

```json
{
  "total": 18,
  "landscape": 5,
  "portrait": 7,
  "square": 2,
  "panorama": 3,
  "tall": 1,
  "exportLayout": "mobile"
}
```

**编排**：`items[]` + 可选 `layout.slot` / `rowLayout`：

| 字段 | 含义 |
|------|------|
| `layout.slot` | `panorama` \| `square` \| `tall`（单卡） |
| `rowLayout` | `landscape-triple` \| `landscape-pair` \| `portrait-triple` \| `portrait-pair` \| `square-triple` \| `square-pair` |

### 2.3 双端一次写出（`exportLayout=auto` · 2026-05-21）

| 阶段 | 输出 | 说明 |
|------|------|------|
| **Curate** (`run_curate`) | `chapters[].items[]` | 按 **mobile** 规则规划（`plan_chapter_items`） |
| **Curate** + `layoutEngine=screens` | `chapters[].screens[]` | 同日桶组屏；与 items 资产集合一致（见 `test_chapter_items_screens_sync`） |
| **Layout CLI** | 重算 items + screens | 不改章桶；`travelogue layout --web-layout screens` |
| **Render** | `index.html` + `index-mobile.html` | `render_trip_surfaces()`：Web+screens / 手机+legacy |

`exportLayout=web` 时仅 Web 规则；`mobile` 时仅手机规则；**不**重复维护两份 `trip.json`。

**封面（auto）**：`curation.coverByLayout.mobile` / `.web` 由 `sync_trip_covers()` 写入；`coverAssetId` 默认等于 mobile。渲染 `index.html` / `index-mobile.html` 时按 profile 解析（`resolve_cover_asset_id`）。

**章首 hero（Web screens）**：章内 ≥5 张时，优先将得分最高的横/全景单开一屏 `screen-landscape-1` 或 `screen-panorama-1`，其余再组屏。

**横/竖 pattern 分离（screens-2）**：

| 构图 | 多图组屏 | 单图 |
|------|----------|------|
| 横 `landscape` | 2/3 张 → `landscape-stack-2/3` **横条行**；4+ → 2×2 / 3×2 / 3×3 | `screen-landscape-1` cover |
| 竖 `portrait` | 2/3 张 → `screen-portrait-2/3` **竖列槽** | `screen-portrait-1` cover（非 contain 信箱） |
| 超长竖 `tall` | — | `screen-tall-1` contain |

槽位写入前校验 `aspectKind`，横图不进 `screen-portrait-*`。

---

## 3. 构图五类（AspectKind）

由 `image_ops.classify_aspect(width, height)` 根据 **裁切后** 宽高比判定（阈值可配置于代码常量）。

| 类型 | 宽高比 w/h | 典型来源 | 勿与谁混排 |
|------|------------|----------|------------|
| **panorama** 全景 | **≥ 2.0** | 手机全景、超宽裁切、2:1 横幅 | 横版三联 `landscape-triple` |
| **landscape** 标准横 | 1.08 – 2.0 | 16:9、3:2、**5:4、4:3** 等用户裁切 | 全景 |
| **square** 方图 | 0.93 – 1.08 | **1:1**、近似正方 | 当作「竖版」并排（Web 除外） |
| **portrait** 标准竖 | 0.5 – 0.93 | 9:16、3:4、**4:5** 等 | 超长竖 |
| **tall** 超长竖 | **≤ 0.5** | 长截图、窄长裁切、全屏录屏竖条 | 两竖并排 |

### 3.1 「非标准比例」如何处理？

用户自行裁剪的 **4:5、5:4、3:2** 等仍落在 **标准横/竖带** 内，按横/竖规则编排即可，**不单独建类**，以避免规则爆炸。

仅当比例 **极端**（超宽 / 超窄 / 近方）时升为 panorama / square / tall，从而获得 **专用比例盒与裁切**，视觉效果优于硬套 9:16 或 16:9。

### 3.2 Ingest 裁切（可选 · 默认关闭）

默认 **不裁切**：ingest 输出等比 WebP，`aspectKind` 仍由原始宽高分类，供 CSS 比例盒与长图限高使用。

`generate_crops: true` 时（legacy）：

| aspectKind | 默认裁切比例 | 说明 |
|------------|--------------|------|
| panorama | **2:1** | 保留横幅气势；Web 可用 21:9 比例盒 |
| square | **1:1** | 中心裁切 |
| tall / portrait | **9:16** | 竖卡；tall 允许更高 `max-height` |
| landscape | **16:9** | 标准横卡 |

函数：`crop_for_aspect_kind(img, kind, slot=...)`。

---

## 4. 手机版面（`exportLayout: mobile` · 单列扫读）

**当前实现（P0 + 大图集拼图）**：

- **≤30 张**（布局可用总数）：章内每张照片一张 `media-card`，纵向单列；标准横图 CSS 限高约 **28dvh**，竖图 `contain` 满宽。
- **>30 张**（拼图资格，见 `mobile_layout_state.py`）：
  - **横图连拍**：连续 **≥8** 张标准横图、相邻 `takenAt` ≤ `burst_seconds` → **`mobile-landscape-grid-8`**（2×4，`cover`）。配额：31–80 **2** 块；81–150 **5**；>150 **8**。
  - **竖图连拍**：连续 **≥4** 张标准竖图、相邻间隔同上 → **`mobile-portrait-grid-4`**（2×2 并排双列；风景 `cover`，含人物 `layoutHint: person-grid-4` + `contain`）。配额：31–80 **4** 块；81–150 **8**；>150 **12**。
  - 余片仍为单卡；≤30 张整趟不拼图。

| 优先级 | 条件 | 块类型 | 视觉效果 |
|--------|------|--------|----------|
| 1 | 任意×1 | `media-card` | 单列；全景 / 方 / 竖 / 横均独立成卡 |
| — | 横滑章（gallery） | 仍 `media-scroll` | 屏上横滑；**长图导出**时纵向展开 |

**已废弃（文档旧版）**：方×3 三联、横×2/×3 拼图在手机端 **不再生成**（见 `layout_planner._mobile_card`）。

**禁止**：全景进入横版三联；超长竖与另一竖并排（手机窄条无效）。

---

## 5. Web 版面（`exportLayout: web` · 16:9）

| 优先级 | 条件 | 块类型 |
|--------|------|--------|
| 1 | 全景×1 | `media-card` · `panorama`（21:9 盒） |
| 2 | 超长竖×1 | `media-card` · `tall` |
| 3 | 方×3 / 方×2 | `square-triple` / `square-pair` |
| 4 | 方×1 | `media-card` · `square` |
| 5 | 标准竖×3 / ×2 | `media-row` · `portrait-triple` / `portrait-pair` |
| 6 | 标准横×3 / ×2 | `landscape-triple` / `landscape-pair` |
| 7 | 其余×1 | `media-card` |

---

## 5b. Web · `layoutEngine: screens`（v screens-2）

> 产品 PRD：[web端模板.prd](./web端模板.prd) · 代码：`travelogue/curation/screen_planner.py`

| 项 | 说明 |
|----|------|
| 触发 | `trip.layoutEngine=screens` 且 `exportLayout=web`（或 `config.yaml` → `layout.web_layout_engine: screens`） |
| 数据 | `chapters[].screens[]`：`patternId` + `slots[]`（`fit`: cover \| contain） |
| 单屏上限 | **9** 张；满屏后下一屏重算 pattern |
| 宫格 | 横/竖/方：1·2·3·4（2×2）·6（3×2）·9（3×3） |
| 竖三列 | `screen-portrait-3` · **cover** 拼满 16:9 |
| 单竖 | `screen-portrait-1` · **cover** 满屏兜底；或 `screen-portrait-1-landscape-2`（1 竖+2 横，时间邻近） |
| 五图拼版 | `screen-mosaic-5-main-portrait-3land`：左上主横图（cover 分最高）+ 右上 1 竖 + 底行 3 横；连续 5 张且 `takenAt` 跨度 ≤ `burst_seconds`；整章恰好 5 张时不另起章首 Hero |
| 八竖 2×4 | `screen-portrait-grid-8`：总量 **>50** 且 **竖图多于横图**；连续 8 竖、相邻 `takenAt` ≤ `burst_seconds`；配额 51–100 **2** 屏 / 101–200 **4** / >200 **6**（不计九宫格）；人物 `layoutHint: person-grid-8` + `contain` |
| 连拍 | `takenAt` 间隔 ≤ `ingest.burst_seconds` 且同构图族 → 优先 4/9 宫格 |
| 九宫格配额 | 按游记**布局可用照片总数**：≤50 最多 1 次；51–100 为 2–5 次；101–200 为 4–8 次；>200 为 6–10 次；**禁止连续两屏均为 `*-9`** |
| 连续排版禁令 | 禁止连续两屏 `*-3`（三张一排）；禁止连续两屏 `*-6`（六张两排）；禁止 `*-3` 与 `*-6` 相邻（任意顺序）；禁止连续两屏 `screen-portrait-1` / `screen-tall-1` |
| gallery 章 | screens 引擎下仍从 items 展平为 **多屏 mosaic**；渲染不用 `media-scroll` |
| legacy | `layoutEngine=legacy` 仍走 §5 上表 `media-row` / `media-card` |

```powershell
python -m travelogue layout trips\<id>\trip.json --layout web --web-layout screens
python -m travelogue render trips\<id>\trip.json --web-layout screens
```

---

## 6. `auto` 模式

| 阶段 | 行为 |
|------|------|
| 策展编排 | 按 **mobile** 规则生成结构 |
| 浏览器 | CSS 断点 + `data-layout` 切换比例盒 |

改 `exportLayout` 为 `web` 后应 **重跑策展** 以应用竖版配对逻辑。

---

## 7. 封面与特殊素材

| 规则 | 说明 |
|------|------|
| 封面 | **mobile**：优先标准竖 / tall；**web**：优先 **横图 / 全景**（近 16:9）；跳过 square |
| 视频 | 不参与五类统计；`media-card--video` |
| 横滑 scroll | 仍以 9:16 缩略；与章内全景条区分 |

---

## 8. CSS 契约

| 类 / rowLayout | 用途 |
|----------------|------|
| `.media-card--panorama` | 2:1 / 21:9 宽条 |
| `.media-card--square` | 1:1 |
| `.media-card--tall` | 高竖卡 |
| `.media-row--square-triple` | 三方格 |
| `.media-row--landscape-triple` | 三横（仅标准横） |

---

## 9. 边界与降级

| 情况 | 处理 |
|------|------|
| 仅 1–3 张 | 少章；可能无 row |
| 横图不足 3 | pair 或单卡 |
| 竖图奇数（Web） | 末张单卡 |
| 全景与横图相邻 | 各走各 slot，不合并 row |
| 用户调序 | 重算 `plan_chapter_items` |

---

## 10. Agent / CLI

**G1 闸口文案示例**：

> 共 18 张：横 5 · 竖 7 · 方 2 · 全景 3 · 超长 1。手机版：横图三联、全景宽条、方图三宫格。

```powershell
travelogue demo from-album .\photos --layout mobile
travelogue demo from-album .\photos --layout web
```

---

## 11. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 横竖统计 + 手机三横 / Web 两竖 |
| v0.2 | 2026-05-19 | 五类构图：panorama / square / tall + 方图 row + 文档 |
| v0.3 | 2026-05-21 | §5b layoutEngine screens-2：宫格 4/6/9、连拍、tone |
