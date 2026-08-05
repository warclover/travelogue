# PRD-EXPORT-CARD-COMPOSE-V1 · 3:4 卡片拼贴统一管线

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.1 |
| **状态** | Draft（决策已定 · 模板设计稿待补） |
| **模块代号** | Export Card Compose（小红书 / 单张海报 / 画册三出口统一） |
| **前置条件** | [ADR-021 v0.2](./adr/021-export-compose-dual-engine.md)（本 PRD 是 ADR-021 D2/D4 的产品化展开） |
| **关联文档** | [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) §6.4（**被本 PRD 取代**）· [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) §6（`poster_bric` 拼贴方式**被本 PRD 取代**，Writer/flag 挂点不变）· [ADR-014](./adr/014-mosaic-proximity-window-order.md)（分镜聚类信号来源） |
| **更新日期** | 2026-08-05 |

---

## 1. 背景

`feat/export-compose-redesign` 已把小红书 / 单张海报 / 画册三个出口从「HTML 长卷截图」迁到「固定画布 Compose」（ADR-021 v0.1），解决了长宽比错误的问题，但实测出现新问题：

> **底板比例正确，但照片没有铺满 / 拼贴生硬** —— 根因是 `compose_canvas.py` 用 `bric_compose` 做通用矩形装箱 + cover 裁切，**不是真正的版式模板**，选图也是盲切页（`pack_photo_pages` 按固定张数切，不看分镜边界）。

本 PRD 把三个出口重新收敛到**同一套 3:4 卡片管线**，用「选图分组 → 模板选择 → 渲染」三段式替换「装箱 → 裁切」，且尽量**复用现有的分镜聚类与模板选择算法**，只新增一个 3:4 专用模板库。

---

## 2. 目标 / 非目标

**目标**

- G1：小红书、单张海报、画册三出口统一为「N 张 3:4 卡片」的不同排列方式，共用一套选图 + 渲染内核。
- G2：卡片内部用**真模板**（按张数 + 横竖版构成选版式），不是任意矩形装箱。
- G3：选图分组尊重已有的分镜 / 场景聚类边界，不盲切。
- G4：渲染保持 Pillow 确定性路径，不引入 Playwright（延续 ADR-016 分支 D 的稳定性原则）。

**非目标**

- 不在本 PRD 内做卡片内文案排版（标题、正文）——三出口当前均为纯图卡片。
- 不重新设计朋友圈（Slice-B）/ 微信群（Slice-A）——两者维持 ADR-021 D1 现状。
- 不在 v0.1 内铺开模板变体（起步每张数 1 套，见 §6）。

---

## 3. 统一模型：3:4 卡片（Card）

**Card** = 一张 3:4 画布，内含 1–4 张照片，按模板摆放。三出口只是「卡片的取用方式」不同：

| 出口 | Card 用法 | 输出文件 |
|------|-----------|----------|
| 小红书 `xiaohongshu` | N 张 Card，每张独立导出 | N 张 3:4 PNG |
| 单张海报 `poster_bric` | 固定 **1 张** Card | 1 张 3:4 PNG |
| 画册 `album_spread` | Card **两两成对**，中间加 gutter 拼成跨页 | M 张「2×3:4+gutter」跨页 PNG |

### 3.1 几何更正（对照 ADR-021 v0.1）

画册跨页**不是** 2.8:1。两张 3:4 卡片左右并排：

$$\text{spread 宽:高} = \left(2 \times \frac{3}{4} + \text{gutter 系数}\right) : 1 \approx 1.5:1$$

- Gutter 建议：细分隔线或窄留白（占比 ~2–4% 总宽），让 spread 读成「两页打开」而不是一张无缝拼图。
- ADR-021 已同步改为该几何（见 v0.2 版本记录）。

---

## 4. 架构：CardGrouper → CardTemplateSelector → CardRenderer

```
kept 照片（有序，已过滤 is_kept_image / is_collage_asset）
      │
      ▼
CardGrouper
  · 复用 shot_grouping.py / scene_clusters.py 的分镜/聚类边界
  · 把有序照片切成一组组「卡候选」（1–4 张 / 组）
  · 不跨分镜边界硬切；组内 > 4 张才在组内再拆
      │
      ▼
CardTemplateSelector
  · 复用 screen_planner.py 的横竖判断算法（asset_has_person / portrait_fit_for_asset）
  · 不复用 16:9 的 slot 数值，只复用「按数量+横竖构成选版式」的规则
  · 从 3:4 模板库（§6）里选一个 slot 方案
      │
      ▼
CardRenderer（新，Pillow slot 渲染，方案 A）
  · 按 slot 矩形 cover-crop 贴图
  · 复用 subject.py 的主体安全裁切信号，避免裁到人脸/主体
      │
      ├─ 小红书：每张 Card 单独落盘
      ├─ 单张海报：只产 1 张 Card（选图见 §5.2）
      └─ 画册：Card 两两拼 spread（gutter，见 §3.1）
```

| 组件 | 复用来源 | 说明 |
|------|----------|------|
| 分组边界 | [`shot_grouping.py`](../travelogue/curation/shot_grouping.py)（`adaptive_soft_split_hours` / `_merge_small_groups`）、[`scene_clusters.py`](../travelogue/curation/scene_clusters.py) | 只取「边界」，不取原有 Web 屏的张数上限 |
| 横竖构成信号 | [`layout_contract/subject.py`](../travelogue/layout_contract/subject.py)（`asset_has_person`、`portrait_fit_for_asset`） | 直接调用，纯 Python，无 CSS 依赖 |
| 模板选择规则 | [`screen_planner.py`](../travelogue/layout_engine/planner/screen_planner.py) 的 `PATTERN_*` 选择逻辑 | 复用「按张数+横竖比选 pattern」的判定顺序，不复用其 16:9 `displayAspect` 数值 |
| 已精选照片有序读取 | `photo_grid_pack.py` / `poster_bric_pack.py` 的 `_ordered_kept_ids` / `is_collage_asset` | 直接沿用，保证与预览「保留哪些照片」口径一致 |

替换范围：本 PRD 落地后，`compose_canvas.py` 的 `bric_compose` + cover 装箱路径与 `collage_pack.py` 的 `pack_photo_pages` 盲切页逻辑**整体退役**，由 CardGrouper/CardTemplateSelector/CardRenderer 取代。

---

## 5. 三出口详细定义

### 5.1 小红书 `xiaohongshu`

- Card 数量 N：延续 [PRD-LONGSHOT-2.0.md §6.4.3](./PRD-LONGSHOT-2.0.md) 的 auto 张数校准公式（`N0 = ceil(photo_count/4)`，clamp 到 3–10），但改为按 **CardGrouper 实际分组数**取整，而不是对切片数取整。
- 每张 Card 独立导出：`{title}-xhs-{nn}.png`，footer `{i}/{n}` 沿用现有页码约定。
- 不再有 `letterbox` / `smart_crop` 选择——Compose 卡片天然铺满画布，`padMode` UI 继续隐藏（已在 Studio 面板做过）。

### 5.2 单张海报 `poster_bric`

- 固定只产 **1 张 Card**（1–4 张代表图，实际张数由 CardTemplateSelector 按可用素材质量决定）。
- **选图策略：代表性精选**，不是简单取前 N 张。复用现有「精选/封面权重」信号（如 `DEFAULT_FEATURED_WEIGHT` 及封面挑选已用的加权维度），优先覆盖：开篇 / 高光 / 结尾三类时间位置，避免同一分镜出现两张。
- 具体权重公式留在实施阶段定稿，本 PRD 先锁定「非顺序前 N 张」这个产品约束。

### 5.3 画册 `album_spread`

- 章内先按 CardGrouper 分卡，再把卡两两配对成 spread（章末奇数卡允许与下一章首卡配对，或该章单独出「半页」——留作实施选项，见 §10）。
- Spread 几何见 §3.1；输出命名延续现有 `album_spread` 平台前缀。

---

## 6. 模板库规格（v0.1 起步规模）

新目录：`docs/templates/card-aspect-3x4/`（与既有 `docs/templates/slot-aspect/` 16:9 屏模板**分离**，避免数值混用）。

起步范围：**每种槙数 1 套，共 4 套**：

| 槙数 | 版式 | 状态 |
|------|------|------|
| 1 | 全卡单图（cover + 主体安全裁切） | 待设计稿（用户已设计，待发） |
| 2 | 双图（上下 / 左右） | 待设计稿 |
| 3 | 1 主 + 2 副 | 待设计稿 |
| 4 | 2×2 等分 | 待设计稿 |

模板文件格式沿用 `docs/templates/slot-aspect/*.md` 的 slot 表约定（`slot | role | displayAspect`），但 `displayAspect` 按 3:4 画布重新计算，不得直接复制 16:9 数值。设计稿到位后在 `docs/templates/card-aspect-3x4/` 下逐套落地，并在 §12 验收前补齐。

---

## 7. 与既有系统的关系（Supersedes）

| 被取代对象 | 取代方式 |
|------------|----------|
| ADR-021 v0.1 的 `compose_fixed_canvas`（bric + cover 装箱） | 由 CardGrouper/Selector/Renderer 三段式取代；ADR-021 同步升版 v0.2 |
| `collage_pack.py` 的 `pack_photo_pages` / `pack_album_pages_by_chapter` 盲切页 | 由 CardGrouper（分镜边界感知）取代 |
| [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) §6.4 小红书（letterbox 1080×1440 切片） | 本 PRD 全面取代；§6.4 保留存档，文首加 superseded 标注 |
| [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) §6 `poster_bric` 的拼贴方式 | Writer / feature flag 挂点不变，**拼贴内核**改走本 PRD 的 CardRenderer |

---

## 8. 验收标准（草案）

| 编号 | 内容 |
|------|------|
| AC-ECC-01 | 小红书导出 N 张 3:4 PNG，每张照片铺满对应 slot，无大面积背景空白 |
| AC-ECC-02 | 单张海报导出 1 张 3:4 PNG，选图非机械前 N 张（可抽样核对与「精选/封面」重合度） |
| AC-ECC-03 | 画册 spread 几何为「2×3:4+gutter」，肉眼可辨两页边界（非无缝拼接） |
| AC-ECC-04 | 同一分镜/聚类内的照片不被硬切到两张不同 Card（除非该分镜本身 >4 张） |
| AC-ECC-05 | 三出口均不触发 Playwright / HTML capture 路径 |

---

## 9. 分阶段计划

1. **Stage 1**：3:4 画布常量 + 模板库骨架（等设计稿）+ `CardRenderer`（Pillow slot 渲染 + 主体安全裁切）。
2. **Stage 2**：`CardGrouper`（接 `shot_grouping.py` / `scene_clusters.py` 边界）+ `CardTemplateSelector`（接 `screen_planner.py` 选择规则，映射到 3:4 模板库）。
3. **Stage 3**：三出口接线——小红书（N 卡）、单张海报（1 卡 + 精选选图）、画册（配对 spread）。
4. **Stage 4**：退役 `compose_canvas.py` 的 bric 装箱路径与 `pack_photo_pages` 盲切页；更新 Studio 文案/测试；`docs/adr/021` 升版收口。

---

## 10. 开放问题

| 编号 | 问题 | 备注 |
|------|------|------|
| OQ-ECC-01 | 单张海报「代表性精选」的具体权重公式 | 待实施阶段与精选/封面逻辑对齐后定稿 |
| OQ-ECC-02 | 画册章末奇数卡如何配对（跨章 vs 单独半页） | 待补，不阻塞 Stage 1–2 |
| OQ-ECC-03 | 模板库是否需要「小红书 3:4」与「画册 3:4」用不同留白/安全区 | 待设计稿到位后评估 |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-05 | 初稿：三出口统一 3:4 卡片管线，锁定 CardGrouper/Selector/Renderer 架构、Pillow 渲染、画册几何更正、模板库起步规模（4 套，待设计稿） |
