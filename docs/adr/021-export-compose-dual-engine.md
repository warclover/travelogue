# ADR-021 · 导出双引擎：Slice 叙事切片 + Compose 固定画布拼贴

| 属性 | 内容 |
|------|------|
| **状态** | 已采纳（实现中 · `feat/export-compose-redesign`） |
| **日期** | 2026-08-04（v0.2/v0.3 修订 2026-08-05） |
| **关联** | [ADR-016](./016-longshot-platform-export.md) · [PRD-EXPORT-CARD-COMPOSE-V1](../PRD-EXPORT-CARD-COMPOSE-V1.md)（D2/D4 的产品化展开） |
| **影响范围** | `compose_canvas.py` · `collage_pack.py` · `poster_bric_pack.py` · `longshot.py` · Studio 导出面板 · Output Recipe |

---

## 背景

ADR-016 假设「一次 full canvas → 切分 / fit_aspect」即可覆盖朋友圈、小红书等平台。实测与产品定义不符：

- 小红书需要的是 **N 张竖版 3:4 拼贴海报**，不是杂志长卷截屏再压比例。
- 单张海报应对齐 **A4**；画册应对齐 **≈2.8:1 横版跨页**。（**v0.2 更正**：见 D2.1/D2.2，三出口统一 3:4，画册几何改为两卡+gutter）
- 朋友圈与九宫格语义重复；Studio 只保留 **长图连读 ≤9 段**。
- 微信群长图行为正确，应冻结。
- v0.1 落地后新问题：三出口比例正确但**照片没有铺满/拼贴生硬**——根因是 `bric_compose` 通用装箱 + cover 裁切，不是真模板；v0.2 改为 CardGrouper/Selector/Renderer 三段式（详见 D2、[PRD-EXPORT-CARD-COMPOSE-V1](../PRD-EXPORT-CARD-COMPOSE-V1.md)）。

---

## 决策

### D1 · 用户可见五出口

| 出口 | platform | 引擎 |
|------|----------|------|
| 微信群 | `wechat_chat` | Slice-A（ADR-016 A，**零改**） |
| 朋友圈 | `wechat_moments` | Slice-B（长卷切分，不锁比例，不截断屏） |
| 小红书 | `xiaohongshu` | **Compose** 多张 3:4 卡片 |
| 单张海报 | `poster_bric` | **Compose** 单张 3:4 卡片 |
| 画册印刷 | `album_spread` | **Compose** 多张跨页（两张 3:4 卡片 + gutter，**非** 2.8:1，见 D2） |

Studio **下线** `moments_grid`；CLI 暂留兼容。

### D2 · Compose 内核（v0.2 · 三出口统一 3:4 卡片）

v0.1 的 `compose_fixed_canvas`（`bric_compose` 通用装箱 + cover 裁切）**退役**。三出口统一到「3:4 卡片」模型，详见 [PRD-EXPORT-CARD-COMPOSE-V1](../PRD-EXPORT-CARD-COMPOSE-V1.md)：

- **CardGrouper**：按模板库实际槙数（{1,4,6,7,9}，见下）顺序消耗照片 + 横竖版角色匹配。**不要求**分镜/聚类边界感知（用户明确：三出口无需严格按聚类/分镜拼图，只需槙位横竖版正确即可）；分镜信号降级为可选平局打破项。
- **CardTemplateSelector**：复用 `screen_planner.py` 的横竖判断算法，从 `docs/templates/card-aspect-3x4/` 模板库（用户设计稿 2026-08-05 已交付 **9 套**：1/4/6×4/7×2/9 槙）选版式（不复用 16:9 的 slot 数值）。
- **CardRenderer**：Pillow slot 渲染 + `subject.py` 主体安全裁切，**不引入 Playwright**（延续分支 D 原则）。
- 三出口差异只是「卡片取用方式」：小红书 = N 张独立卡；单张海报 = 固定 1 张卡（**由 A4 改为 3:4**，见下方 D2.1）；画册 = 卡两两配对成跨页。
- `collage_pack` 保留「分页 + 多文件原子写」（`PlatformExportWriter`）壳层，内部盲切页逻辑（`pack_photo_pages`）由 CardGrouper 取代。
- **禁止** 对 Compose 目标走 Playwright full capture + `fit_aspect`。

#### D2.1 · 修订：单张海报画幅由 A4 → 3:4

v0.1 定义单张海报对齐 A4；v0.2 为与小红书/画册共用同一套模板库和渲染内核，**改为 3:4**（与小红书单卡同规格）。打印场景如仍需 A4，留作后续独立需求，不在本轮范围。

#### D2.2 · 修订：画册跨页几何由 2.8:1 → 两卡 + gutter

两张 3:4 卡片左右拼接，几何为 $2\times\frac{3}{4} : 1 \approx 1.5:1$，非 v0.1 拍定的 2.8:1；中间需可见 gutter（细线/窄留白），使跨页读成「两页打开」而非无缝拼贴。

### D3 · 相对 ADR-016

- Branch A：不变。
- Branch B：仅服务仍属「长卷切片」的平台（当前主路径：`wechat_moments`；Phase C CLI 可选保留）。
- `xiaohongshu` **迁出** Branch B，进入 Compose。
- Branch D / GCS：升级为 Compose 家族（poster / xhs / album）。

### D4 · 单张海报选图策略（v0.2 新增）

固定只产 1 张 3:4 Card，选图为**代表性精选**（非顺序前 N 张），复用现有精选/封面加权信号（如 `DEFAULT_FEATURED_WEIGHT`），优先覆盖开篇/高光/结尾三类时间位置。具体权重公式见 PRD-EXPORT-CARD-COMPOSE-V1 §5.2 / OQ-ECC-01。**模板优先级**（用户明确：优选带主图或单张大图模板）：`card-1-full-frame` / `card-6-hero-tl-stack` / `card-6-hero-br-stack` > `card-4-square-top-triband`（含裁切槙）> 其余无主图模板（不用）。

---

## 后果

- **正面**：出口语义与真实发帖/印刷物件对齐；拼贴复用一套内核。
- **负面**：旧 `*-xhs-*` 杂志切片与新拼贴海报同名前缀，需靠 job 产物与成功态区分。
- **迁移**：Output Recipe Ambiguous 卡仅「发群 / 朋友圈连读」；更多出口走导出设置面板。

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-04 | 初稿并随 `feat/export-compose-redesign` 落地（编号 ADR-021，避开 Bookends ADR-017） |
| v0.2 | 2026-08-05 | 三出口统一 3:4 卡片管线（[PRD-EXPORT-CARD-COMPOSE-V1](../PRD-EXPORT-CARD-COMPOSE-V1.md)）：单张海报 A4→3:4（D2.1）；画册 2.8:1→两卡+gutter（D2.2）；Compose 内核由 `bric_compose` 装箱改为 CardGrouper/CardTemplateSelector/CardRenderer；新增 D4 单张海报代表性精选策略 |
| v0.3 | 2026-08-05 | 用户设计稿到位（9 套模板，槙数 1/4/6×4/7×2/9）：CardGrouper 简化为顺序消耗 + 横竖版匹配，**不再要求**分镜/聚类边界感知；D4 补充单张海报模板优先级的具体模板名 |
