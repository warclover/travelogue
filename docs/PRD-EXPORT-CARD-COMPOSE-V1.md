# PRD-EXPORT-CARD-COMPOSE-V1 · 3:4 卡片拼贴统一管线

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.3.0 |
| **状态** | **Conditional Go**（[七席评审](./acceptance-records/ecc-export-card-compose-v1-review-2026-08-05.md) 2026-08-05 · BLK-ECC-01～05 已回写） |
| **模块代号** | Export Card Compose（小红书 / 单张海报 / 画册三出口统一） |
| **前置条件** | [ADR-021 v0.4](./adr/021-export-compose-dual-engine.md)（本 PRD 是 ADR-021 D2/D4 的产品化展开） |
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

> **v0.2 简化（2026-08-05）**：小红书 / 单张海报 / 画册**均不要求**按聚类 / 分镜结果拼图——只需保证每个槙位填入**横竖版正确**的照片即可。CardGrouper 不再承担「分镜边界感知」，退化为「按模板槙数切块 + 按槙位角色（`portrait` / `landscape` / `main`）匹配照片朝向」的**顺序消耗**逻辑。分镜/聚类信号在这三出口中降级为**可选的次要平局打破项**（例如同张数候选下优先选不切断同一分镜的边界），不是硬约束。

```
kept 照片（有序，已过滤 is_kept_image / is_collage_asset）
      │
      ▼
CardGrouper（v0.2 · 顺序消耗，非分镜感知）
  · 决定 Card 数量 N 及每张 Card 用几槙（只能取模板库已有槙数：1/4/6/7/9，见 §6）
  · 按序从 kept 照片池里为每张 Card 取出所需张数
  · 每张照片按朝向（横/竖）匹配槙位角色，不足则跳过/回填，不追求分镜完整性
      │
      ▼
CardTemplateSelector（**独立新实现，不 import screen_planner.py 内部状态**）
  · 输入：该 Card 分到的照片张数 + 横竖构成
  · 从 3:4 模板库（§6）选一个槙数匹配、且横竖槙位数量能被覆盖的版式
  · 同槙数存在多套时（6 槙×4 套 / 7 槙×2 套）按 Card 序号轮换（见 §10 OQ-ECC-04 默认解）
  · 单张海报强制只从「含主图槙」的模板中选（见 §5.2 优先级）
      │
      ▼
CardRenderer（Pillow slot 渲染，方案 A）
  · 按 slot 矩形 cover-crop 贴图
  · 复用 subject.py 的主体安全裁切信号，避免裁到人脸/主体
  · `card-4-square-top-triband` 的主图槙（`displayAspect≈1.125`）需额外裁切保护（见 §6 备注）
      │
      ├─ 小红书：每张 Card 单独落盘
      ├─ 单张海报：只产 1 张 Card（选图见 §5.2）
      └─ 画册：Card 两两拼 spread（gutter，见 §3.1）
```

| 组件 | 复用来源 | 说明 |
|------|----------|------|
| 横竖构成信号 | [`layout_contract/subject.py`](../travelogue/layout_contract/subject.py)（`asset_has_person`、`portrait_fit_for_asset`） | 直接调用，纯 Python，无 CSS 依赖；用于判断照片朝向以匹配槙位角色 |
| 模板选择规则 | [`screen_planner.py`](../travelogue/layout_engine/planner/screen_planner.py) 的 `PATTERN_*` 选择逻辑 | **仅借鉴**「按张数+横竖比选 pattern」的判定思路重新实现；`screen_planner.py` 是 ~1930 行状态化规划器（`ScreenLayoutPlannerState`），`CardTemplateSelector` **禁止** import 其内部函数/状态，避免耦合（对齐 [ADR-011](./adr/011-import-strategy.md) 延迟 import 精神）。**BLK-ECC-02 已回写** |
| 已精选照片有序读取 | `photo_grid_pack.py` / `poster_bric_pack.py` 的 `_ordered_kept_ids` / `is_collage_asset` | 直接沿用，保证与预览「保留哪些照片」口径一致 |
| 分镜/聚类信号（次要，非必需） | [`shot_grouping.py`](../travelogue/curation/shot_grouping.py)、[`scene_clusters.py`](../travelogue/curation/scene_clusters.py) | 仅用于同槙数候选下的平局打破，不阻塞出图 |

替换范围：本 PRD 落地后，`compose_canvas.py` 的 `bric_compose` + cover 装箱路径与 `collage_pack.py` 的 `pack_photo_pages` 盲切页逻辑**整体退役**，由 CardGrouper/CardTemplateSelector/CardRenderer 取代。

---

## 5. 三出口详细定义

### 5.1 小红书 `xiaohongshu`

- Card 数量 N：不再对齐 [PRD-LONGSHOT-2.0.md §6.4.3](./PRD-LONGSHOT-2.0.md) 的「切片数」公式，改为按**模板库槙数**（{1,4,6,7,9}）贪心切块——优先用大槙数模板（6/7/9）消耗照片，尾部不足一整套槙数时，用较小模板（4/1）收尾，避免出现「最后一张只放 1 张照片却用了 9 槙模板」的浪费。
- 每张 Card 独立导出：`{title}-xhs-{nn}.png`，footer `{i}/{n}` 沿用现有页码约定。
- 不再有 `letterbox` / `smart_crop` 选择——Compose 卡片天然铺满画布，`padMode` UI 继续隐藏（已在 Studio 面板做过）。
- **不要求**按分镜/聚类分组，只要求槙位横竖版正确填充（见 §4 v0.2 简化）。

### 5.2 单张海报 `poster_bric`

- 固定只产 **1 张 Card**，**模板优先级**（§6）：`card-1-full-frame` / `card-6-hero-tl-stack` / `card-6-hero-br-stack`（裁切损失小）> `card-4-square-top-triband`（含裁切槙，损失较大）> 其余无主图模板（**不用**）。即优先「带主图的拼图模板」或「单张大图模板」，符合用户明确要求。
- **选图策略：代表性精选**，不是简单取前 N 张。复用 [`curation/cover_scoring_v2.py`](../travelogue/curation/cover_scoring_v2.py) 的 `cover_score_v2(asset, pool, ...)` —— 逐张打封面分、对 kept 照片池排序取 top-N，优先覆盖开篇 / 高光 / 结尾三类时间位置。
  > **BLK-ECC-01 回写（2026-08-05 评审）**：此前草稿误引 `DEFAULT_FEATURED_WEIGHT`（该常量语义是 `screen_planner.py` **屏内主图资格评分**的权重，非全书代表性排序信号，对口错误），已订正为 `cover_scoring_v2.cover_score_v2()`。
- 具体权重公式留在实施阶段定稿，本 PRD 先锁定「非顺序前 N 张、复用 cover_score_v2 排序」这个产品约束。

### 5.3 画册 `album_spread`

- 按 §5.1 同样的「模板槙数贪心切块」逻辑分卡，再把卡两两配对成 spread（末尾单卡允许与相邻卡配对，或单独出「半页」——留作实施选项，见 §10）。
- Spread 几何见 §3.1；输出命名延续现有 `album_spread` 平台前缀。
- **不要求**按章/分镜严格切卡，只要求槙位横竖版正确填充；章节边界可作为配对候选的次要平局打破项。

---

## 6. 模板库规格（v0.2 · 用户设计稿已落地）

新目录：`docs/templates/card-aspect-3x4/`（与既有 `docs/templates/slot-aspect/` 16:9 屏模板**分离**，避免数值混用）。

用户设计稿（2026-08-05）交付 **9 套**，均基于 **3×3 等分基准网格**（合并部分格子成大槙），比原计划「每槙数 1 套共 4 套」更丰富，槙数分布为 **{1, 4, 6×4, 7×2, 9}**：

| 文件 | 槙数 | 版式 | 含主图槙 | 备注 |
|------|------|------|----------|------|
| [`card-1-full-frame.md`](./card-1-full-frame.md) | 1 | 满版单图 | ✓ | 单张海报首选 |
| [`card-4-square-top-triband.md`](./card-4-square-top-triband.md) | 4 | 顶部近方图 + 底部三竖版 | ✓（弱） | **唯一需裁切**的槙位（顶部 `aspect≈1.125`） |
| [`card-6-hero-tl-stack.md`](./card-6-hero-tl-stack.md) | 6 | 左上主图 + 右侧堆叠 + 底部三等分 | ✓ | 单张海报首选 |
| [`card-6-hero-br-stack.md`](./card-6-hero-br-stack.md) | 6 | 顶部三等分 + 左侧堆叠 + 右下主图 | ✓ | 上一版镜像；单张海报首选 |
| [`card-6-bookend-rows.md`](./card-6-bookend-rows.md) | 6 | 首尾呼应（1/2 行宽图+方图，第 3 行翻转） | ✗ | 无主图，不作海报首选 |
| [`card-6-brick-alt.md`](./card-6-brick-alt.md) | 6 | 逐行交替（宽图/方图左右互换） | ✗ | 无主图，不作海报首选 |
| [`card-7-triband-2-2-3.md`](./card-7-triband-2-2-3.md) | 7 | 第 1/2 行各两图，第 3 行三等分 | ✗ | 无主图，不作海报首选 |
| [`card-7-triband-2-3-2.md`](./card-7-triband-2-3-2.md) | 7 | 第 1/3 行各两图，第 2 行三等分 | ✗ | 上一版镜像；无主图 |
| [`card-9-grid-equal.md`](./card-9-grid-equal.md) | 9 | 3×3 等分 | ✗ | 无主图，不作海报首选 |

**单张海报模板优先级**（§5.2）：`card-1-full-frame` / `card-6-hero-tl-stack` / `card-6-hero-br-stack` > `card-4-square-top-triband`（需裁切，损失更大）> 其余无主图模板（不用于海报）。

模板文件格式在 `docs/templates/slot-aspect/*.md` 的 slot 表约定（`slot | role | displayAspect`）基础上，**新增 `row/col/rowSpan/colSpan` 列**（3×3 网格坐标），因为本库无 CSS 网格承接位置信息，Pillow 渲染器需要直接可用的矩形坐标。`displayAspect` 均按 3:4 画布重新计算：`0.75` = 竖版/方形单元，`1.5` = 2 列合并的横版单元，`1.125` = 满宽 2 行合并的近方形单元（仅 `card-4-square-top-triband` 使用，需裁切）。

---

## 7. 与既有系统的关系（Supersedes）

| 被取代对象 | 取代方式 |
|------------|----------|
| ADR-021 v0.1 的 `compose_fixed_canvas`（bric + cover 装箱） | 由 CardGrouper/Selector/Renderer 三段式取代；ADR-021 同步升版 v0.2 |
| `collage_pack.py` 的 `pack_photo_pages` 盲切页 | 由 CardGrouper（按模板槙数顺序消耗，横竖版匹配，不要求分镜边界）取代 |
| `collage_pack.py` 的 `pack_album_pages_by_chapter`（**当前按章分页**，章节优先打包） | **BLK-ECC-05 回写**：本函数体现的「章节边界优先」正是 v0.2 明确移除的约束，Stage 2/3 需**主动退役**，由 CardGrouper 的顺序消耗逻辑取代，不得保留双轨 |
| [PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) §6.4 小红书（letterbox 1080×1440 切片） | 本 PRD 全面取代；§6.4 保留存档，文首加 superseded 标注 |
| [PRD-GENERATIVE-COLLAGE-SURFACES-V1.md](./PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) §6 `poster_bric` 的拼贴方式 | Writer / feature flag 挂点不变，**拼贴内核**改走本 PRD 的 CardRenderer |

---

## 8. 验收标准（草案）

| 编号 | 内容 |
|------|------|
| AC-ECC-01 | 小红书导出 N 张 3:4 PNG，每张照片铺满对应 slot，无大面积背景空白 |
| AC-ECC-02 | 单张海报导出 1 张 3:4 PNG，选图非机械前 N 张（可抽样核对与「精选/封面」重合度） |
| AC-ECC-03 | 画册 spread 几何为「2×3:4+gutter」，肉眼可辨两页边界（非无缝拼接） |
| AC-ECC-04 | 每个槙位填入的照片朝向与槙位角色（`portrait`/`landscape`/`main`）一致；不要求对齐分镜/聚类边界 |
| AC-ECC-05 | 三出口均不触发 Playwright / HTML capture 路径 |
| AC-ECC-06 | `card-4-square-top-triband` 的主图槙裁切走主体安全裁切，不裁到人脸/主体 |

---

## 9. 分阶段计划

> **BLK-ECC-04 回写（2026-08-05 评审）**：以下 Stage 3/4 的落地清单**显式列出需改动的现网文件**——当前分支代码仍是 v0.1 状态（`compose_canvas.py` 的 `A4_CANVAS`/`ALBUM_CANVAS=2.8:1`/`bric_compose`；`platform_profiles.yaml` 的 `poster_bric.output.aspect="A4"` / `album_spread.output.aspect="2.8:1"` / 对应 `publish_guide` 文案；`poster_bric_pack.py` 的 `MIN_N/MAX_N=3/9`；`collage_pack.py` 的 `_XHS_PER_PAGE_MIN/MAX=3/6` / `_ALBUM_PER_PAGE=6`），**均未随本 PRD v0.2/v0.3 决策同步**，不是「结构已就位只换模板」。

1. **Stage 1**：3:4 画布常量 + 模板库（**9 套已交付**，见 §6）+ `CardRenderer`（Pillow slot 渲染 + 主体安全裁切，`card-4-square-top-triband` 主图槙走保守裁切）。
2. **Stage 2**：`CardGrouper`（按模板槙数 {1,4,6,7,9} 顺序消耗切块 + 横竖版角色匹配，**退役** `pack_album_pages_by_chapter` 的按章分页，不接分镜/聚类边界）+ `CardTemplateSelector`（独立实现，禁止 import `screen_planner.py`；张数+横竖构成 → 选模板，同槙数多套按 Card 序号轮换；海报走 §5.2 优先级 + `cover_scoring_v2` 选图）。
3. **Stage 3**：三出口接线——小红书（N 卡）、单张海报（1 卡 + `cover_score_v2` 精选选图，`MIN_N/MAX_N` 按所选模板槙数动态定，不再固定 3–9）、画册（配对 spread）。
4. **Stage 4**：退役 `compose_canvas.py` 的 `A4_CANVAS`/`ALBUM_CANVAS`/bric 装箱路径；更新 `platform_profiles.yaml` 的 `poster_bric`/`album_spread` 的 `output.aspect`/`publish_guide`（对齐 3:4 / 两卡+gutter，不再写"A4"/"2.8:1"）；更新 Studio 文案/测试；`docs/adr/021` 升版收口。

---

## 10. 开放问题

| 编号 | 问题 | 备注 |
|------|------|------|
| OQ-ECC-01 | 单张海报「代表性精选」的具体权重公式 | 待实施阶段与精选/封面逻辑对齐后定稿 |
| OQ-ECC-02 | 画册章末奇数卡如何配对（跨章 vs 单独半页） | 待补，不阻塞 Stage 1–2 |
| OQ-ECC-03 | 模板库是否需要「小红书 3:4」与「画册 3:4」用不同留白/安全区 | 9 套模板已到位，待实施阶段抽样评估 |
| OQ-ECC-04 | `card-6-hero-tl-stack` / `card-6-hero-br-stack` / `card-6-bookend-rows` / `card-6-brick-alt`（同为 6 槙）与 `card-7-triband-2-2-3` / `card-7-triband-2-3-2`（同为 7 槙）之间，CardTemplateSelector 具体按什么信号选哪一套 | **BLK-ECC-03 回写（2026-08-05 评审）**：默认解 = 同槙数候选按 Card 序号轮换（`card_index % len(候选)`）；实施阶段可升级为按横竖版构成精选，不阻塞开工 |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-08-05 | 初稿：三出口统一 3:4 卡片管线，锁定 CardGrouper/Selector/Renderer 架构、Pillow 渲染、画册几何更正、模板库起步规模（4 套，待设计稿） |
| v0.2 | 2026-08-05 | 用户设计稿到位：模板库实际交付 **9 套**（槙数 1/4/6×4/7×2/9，§6）；CardGrouper 简化为「按模板槙数顺序消耗 + 横竖版角色匹配」，**不再要求**分镜/聚类边界感知；单张海报模板优先级锁定（含主图/满版 > 含裁切主图 > 不用无主图模板）；新增 `card-4-square-top-triband`（全库唯一需裁切槙位） |
| v0.3.0 | 2026-08-05 | [七席评审](./acceptance-records/ecc-export-card-compose-v1-review-2026-08-05.md) **Conditional Go**，回写 BLK-ECC-01～05：①海报选图复用对象订正为 `cover_scoring_v2.cover_score_v2()`（非 `DEFAULT_FEATURED_WEIGHT`）；②`CardTemplateSelector` 明确不 import `screen_planner.py` 内部状态；③OQ-ECC-04 给默认解（同槙数按序轮换）；④§9 补现网文件迁移清单；⑤§7 补 `pack_album_pages_by_chapter` 退役说明 |
