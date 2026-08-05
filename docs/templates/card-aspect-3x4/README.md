# 3:4 卡片模板库（card-aspect-3x4）

| 属性 | 内容 |
|------|------|
| **来源** | [PRD-EXPORT-CARD-COMPOSE-V1](../../PRD-EXPORT-CARD-COMPOSE-V1.md) §6 · [ADR-021 v0.5](../../adr/021-export-compose-dual-engine.md) |
| **用途** | 小红书 / 单张海报 / 画册三出口共用的 3:4 卡片版式库 |
| **状态** | 用户设计稿已到位（2026-08-05 初版 9 套 + 2026-08-05 追加 4 套等分模板 + 2026-08-05 追加 15 套用户设计稿模板）· **28 套** |

---

## 与 `docs/templates/slot-aspect/` 的关系

`slot-aspect/` 是 16:9 Web 长卷屏模板（`stage: 16:9`），本目录是**独立的 3:4 画布模板**（`stage: 3:4`）。两者共用同一份 `.md` slot 表格式约定（`slot | role | displayAspect`），但 **不共用数值**——16:9 屏的 `displayAspect` 是按那个画幅算的，不能直接套进 3:4 画布。

选版式的**算法**（按张数 + 横竖版构成挑 pattern）复用 `screen_planner.py` 的判定顺序，但落点是本目录的模板，不是 `slot-aspect/`。

## 文件约定

在 `slot-aspect/*.md` 表头基础上，**新增 `row/col/rowSpan/colSpan` 列**（网格坐标）——本库没有 CSS 网格承接位置信息，Pillow 渲染器需要直接可用的矩形坐标：

```markdown
# card-{n}-{name}

- displayName: 中文名
- status: designed | pending-confirm | ga
- stage: 3:4
- grid: {rows}x{cols}

| slot | role | row | col | rowSpan | colSpan | displayAspect |
|------|------|-----|-----|---------|---------|---------------|
| 0 | portrait/landscape/main | 0 | 0 | 1 | 1 | 0.75 |
```

`row/col` 为**该模板自身声明的 `grid` 基准网格坐标**（0-indexed，`rowSpan/colSpan` 为合并跨度）——**并非固定 3×3**：原始 9 套模板都用 3×3 网格，2026-08-05 追加的 4 套等分模板（`card-2/4/8/16-grid-equal`）各自声明 `2x1`/`2x2`/`4x2`/`4x4` 网格，同日再追加的 15 套用户设计稿模板则各自声明 `2x2`/`4x2`/`4x4` 网格，均因原稿本身不是 3×3 落点。`displayAspect` 按 3:4 母版重新计算，全库出现的取值：`0.75` = 竖版/方形单元（含任意网格上的 2x2/2 行/2 列同比例合并），`1.5` = 横版单元（3×3/4x4 网格上的 2 列或 2 行合并，或等分网格里天然较宽的一整行），`1.125` = 满宽 2 行合并近方形单元（仅 1 处使用，需裁切）。

## 模板全集（28 套，用户设计稿 2026-08-05 初版 9 套 + 追加 4 套等分模板 + 追加 15 套用户设计稿模板）

| 文件 | 槙数 | 基准网格 | 版式 | 含主图槙 |
|---|---|---|---|---|
| [`card-1-full-frame.md`](./card-1-full-frame.md) | 1 | 3x3 | 满版单图 | ✓ |
| [`card-2-stack-equal.md`](./card-2-stack-equal.md) | 2 | 2x1 | 上下等分（两条横版带） | ✗ |
| [`card-3-mini-triband.md`](./card-3-mini-triband.md) | 3 | 2x2 | 顶部两竖版 + 底部横版主图 | ✓ |
| [`card-4-square-top-triband.md`](./card-4-square-top-triband.md) | 4 | 3x3 | 顶部近方图（**唯一需裁切**）+ 底部三竖版 | ✓（弱） |
| [`card-4-grid-equal.md`](./card-4-grid-equal.md) | 4 | 2x2 | 田字格等分 | ✗ |
| [`card-5-hero-mid-landscape.md`](./card-5-hero-mid-landscape.md) | 5 | 4x2 | 上下两横版 + 中部横版主图（全横版构成） | ✓ |
| [`card-6-hero-tl-stack.md`](./card-6-hero-tl-stack.md) | 6 | 3x3 | 左上主图 + 右侧堆叠 + 底部三等分 | ✓ |
| [`card-6-hero-br-stack.md`](./card-6-hero-br-stack.md) | 6 | 3x3 | 顶部三等分 + 左侧堆叠 + 右下主图 | ✓ |
| [`card-6-bookend-rows.md`](./card-6-bookend-rows.md) | 6 | 3x3 | 首尾呼应（1/2 行宽图+方图，第 3 行翻转） | ✗ |
| [`card-6-brick-alt.md`](./card-6-brick-alt.md) | 6 | 3x3 | 逐行交替（宽图/方图左右互换） | ✗ |
| [`card-6-pinwheel-diagonal.md`](./card-6-pinwheel-diagonal.md) | 6 | 4x2 | 风车对角（横版堆叠 vs 竖版长柱对角对称） | ✗ |
| [`card-6-sandwich-bands.md`](./card-6-sandwich-bands.md) | 6 | 4x2 | 上下横版带 + 中部竖版双柱（轴对称） | ✗ |
| [`card-7-triband-2-2-3.md`](./card-7-triband-2-2-3.md) | 7 | 3x3 | 第 1/2 行各两图，第 3 行三等分 | ✗ |
| [`card-7-triband-2-3-2.md`](./card-7-triband-2-3-2.md) | 7 | 3x3 | 第 1/3 行各两图，第 2 行三等分 | ✗ |
| [`card-7-hero-top-halves.md`](./card-7-hero-top-halves.md) | 7 | 4x4 | 顶部大槙 + 左右小格 + 底部两等分 | ✗ |
| [`card-7-triband-hero-mid.md`](./card-7-triband-hero-mid.md) | 7 | 4x4 | 顶/底镜像三分 + 中部满宽横版主图 | ✓ |
| [`card-8-grid-equal.md`](./card-8-grid-equal.md) | 8 | 4x2 | 4 行 × 2 列等分（横版单元） | ✗ |
| [`card-8-pinwheel-diagonal.md`](./card-8-pinwheel-diagonal.md) | 8 | 4x4 | 对角双大槙风车（`card-6-pinwheel-diagonal` 密度加强版） | ✗ |
| [`card-9-grid-equal.md`](./card-9-grid-equal.md) | 9 | 3x3 | 3×3 等分 | ✗ |
| [`card-9-hero-mid-triband.md`](./card-9-hero-mid-triband.md) | 9 | 4x4 | 中部满宽横版主图 + 上下四等分（`card-4-square-top-triband` 角色反转版） | ✓ |
| [`card-10-dual-hero-column.md`](./card-10-dual-hero-column.md) | 10 | 4x4 | 中列双主图堆叠，左右两列各四等分收边 | ✗ |
| [`card-10-dual-hero-diagonal.md`](./card-10-dual-hero-diagonal.md) | 10 | 4x4 | 左上/右下对角双主图，另两角各四等分收边 | ✗ |
| [`card-12-alt-side-rows.md`](./card-12-alt-side-rows.md) | 12 | 4x4 | 逐行横竖版侧位交替（横版左右轮换） | ✗ |
| [`card-12-center-land-rows.md`](./card-12-center-land-rows.md) | 12 | 4x4 | 每行居中横版，两侧竖版收边（横版不交替） | ✗ |
| [`card-12-sandwich-bands.md`](./card-12-sandwich-bands.md) | 12 | 4x4 | 顶/底整排竖版四等分 + 中部两整排横版 | ✗ |
| [`card-13-hero-center-stack.md`](./card-13-hero-center-stack.md) | 13 | 4x4 | 主图居中（rows1-2），上下各一整排四等分对称 | ✗ |
| [`card-13-hero-top-stack.md`](./card-13-hero-top-stack.md) | 13 | 4x4 | 主图居顶（rows0-1），下方两整排四等分（不对称） | ✗ |
| [`card-16-grid-equal.md`](./card-16-grid-equal.md) | 16 | 4x4 | 4×4 密网格等分（`card-9-grid-equal` 加密版） | ✗ |

**单张海报模板优先级**（详见 [PRD-EXPORT-CARD-COMPOSE-V1 §5.2](../../PRD-EXPORT-CARD-COMPOSE-V1.md)）：`card-1-full-frame` / `card-6-hero-tl-stack` / `card-6-hero-br-stack` > `card-3-mini-triband` / `card-5-hero-mid-landscape` / `card-7-triband-hero-mid` / `card-9-hero-mid-triband`（均零裁切，2026-08-05 追加）> `card-4-square-top-triband`（唯一需裁切）> 其余无主图模板（不用于海报）。**注意**：`plan_poster_card`（`card_grouper.py`）目前仍只按 pool_size 硬编码选前 3 + 裁切兜底 4 者，尚未接入新增的 4 套零裁切主图模板——见下方「待决问题」。

**追加的 4 套等分模板对 `AVAILABLE_SLOT_COUNTS` 的影响**（2026-08-05）：`CardGrouper.plan_slot_counts` 是"largest-fits-first"贪心算法，槙数集合从 `{1,4,6,7,9}` 扩展为 `{1,2,4,6,7,8,9,16}` 后，以下张数的默认拆分发生变化（均为预期行为，非回归）：
- `n=2` → `[2]`（原 `[1,1]`）
- `n=3` → `[2,1]`（原 `[1,1,1]`）
- `n=8` → `[8]`（原 `[7,1]`）
- `n=4` 恰好命中时在 `card-4-square-top-triband` / `card-4-grid-equal` 间轮询（原来只有前者）

**追加的 15 套用户设计稿模板对 `AVAILABLE_SLOT_COUNTS` 的进一步影响**（2026-08-05，同日第二次扩容）：槙数集合从 `{1,2,4,6,7,8,9,16}` 扩展为 `{1,2,3,4,5,6,7,8,9,10,12,13,16}`（新增 `3,5,10,12,13`；`6/7/8/9` 已有槙数各追加候选模板但集合本身不变）。贪心拆分结果进一步变化，例如：
- `n=3` → `[3]`（此前 `[2,1]`）
- `n=5` → `[5]`（此前 `[4,1]`）
- `n=10` → `[10]`（此前 `[9,1]`）
- `n=12` → `[12]`（此前 `[9,2,1]`）
- `n=13` → `[13]`（此前 `[9,4]`）
- `n=15` → `[13,2]`（此前 `[9,6]`）
- 同槙数多套候选按 `card_index` 轮换的范围也扩大：`n=6` 现有 6 套候选（原 4 套）、`n=7` 现有 4 套（原 2 套）、`n=8`/`n=9`/`n=10`/`n=12`/`n=13` 各自新增候选。

## 待决问题（2026-08-05 追加 15 套后）

- **OQ-ECC-07**：**已决策（2026-08-05，方案B）**——新增的 4 套零裁切主图模板（`card-3-mini-triband` / `card-5-hero-mid-landscape` / `card-7-triband-hero-mid` / `card-9-hero-mid-triband`）**不接入** `card_grouper.py::plan_poster_card`。单张海报选型维持现状（按 `ranked_photos` 池大小硬编码 3 档阈值：<4→`card-1-full-frame`，4~5→`card-4-square-top-triband`，≥6→`card-6-hero-*`），坚持「构图优先」——池子较小时（如 2/3/5/7/8/9 张）允许只用其中一部分照片，以保证主图占比与视觉冲击力，不为了「用满所有照片」牺牲构图质量。这 4 套新模板继续只服务于小红书/画册的多槙位路径；它们已在 `POSTER_TEMPLATE_PRIORITY` 中登记（供 `has_main_slot` 一致性校验），保留代码位置以便未来若产品方向反转时可低成本重新评估，但当前不接线。
