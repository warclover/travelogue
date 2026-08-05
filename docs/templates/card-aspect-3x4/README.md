# 3:4 卡片模板库（card-aspect-3x4）

| 属性 | 内容 |
|------|------|
| **来源** | [PRD-EXPORT-CARD-COMPOSE-V1](../../PRD-EXPORT-CARD-COMPOSE-V1.md) §6 · [ADR-021 v0.5](../../adr/021-export-compose-dual-engine.md) |
| **用途** | 小红书 / 单张海报 / 画册三出口共用的 3:4 卡片版式库 |
| **状态** | 用户设计稿已到位（2026-08-05 初版 9 套 + 2026-08-05 追加 4 套等分模板）· **13 套** |

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

`row/col` 为**该模板自身声明的 `grid` 基准网格坐标**（0-indexed，`rowSpan/colSpan` 为合并跨度）——**并非固定 3×3**：原始 9 套模板都用 3×3 网格，但 2026-08-05 追加的 4 套等分模板（`card-2/4/8/16-grid-equal`）各自声明 `2x1`/`2x2`/`4x2`/`4x4` 网格，因为纯 N 等分拼版没有自然的 3×3 落点。`displayAspect` 按 3:4 母版重新计算，全库出现的取值：`0.75` = 竖版/方形单元，`1.5` = 横版单元（3×3 网格上的 2 列合并，或等分网格里天然较宽的一整行），`1.125` = 满宽 2 行合并近方形单元（仅 1 处使用，需裁切）。

## 模板全集（13 套，用户设计稿 2026-08-05 初版 9 套 + 追加 4 套）

| 文件 | 槙数 | 基准网格 | 版式 | 含主图槙 |
|---|---|---|---|---|
| [`card-1-full-frame.md`](./card-1-full-frame.md) | 1 | 3x3 | 满版单图 | ✓ |
| [`card-2-stack-equal.md`](./card-2-stack-equal.md) | 2 | 2x1 | 上下等分（两条横版带） | ✗ |
| [`card-4-square-top-triband.md`](./card-4-square-top-triband.md) | 4 | 3x3 | 顶部近方图（**唯一需裁切**）+ 底部三竖版 | ✓（弱） |
| [`card-4-grid-equal.md`](./card-4-grid-equal.md) | 4 | 2x2 | 田字格等分 | ✗ |
| [`card-6-hero-tl-stack.md`](./card-6-hero-tl-stack.md) | 6 | 3x3 | 左上主图 + 右侧堆叠 + 底部三等分 | ✓ |
| [`card-6-hero-br-stack.md`](./card-6-hero-br-stack.md) | 6 | 3x3 | 顶部三等分 + 左侧堆叠 + 右下主图 | ✓ |
| [`card-6-bookend-rows.md`](./card-6-bookend-rows.md) | 6 | 3x3 | 首尾呼应（1/2 行宽图+方图，第 3 行翻转） | ✗ |
| [`card-6-brick-alt.md`](./card-6-brick-alt.md) | 6 | 3x3 | 逐行交替（宽图/方图左右互换） | ✗ |
| [`card-7-triband-2-2-3.md`](./card-7-triband-2-2-3.md) | 7 | 3x3 | 第 1/2 行各两图，第 3 行三等分 | ✗ |
| [`card-7-triband-2-3-2.md`](./card-7-triband-2-3-2.md) | 7 | 3x3 | 第 1/3 行各两图，第 2 行三等分 | ✗ |
| [`card-8-grid-equal.md`](./card-8-grid-equal.md) | 8 | 4x2 | 4 行 × 2 列等分（横版单元） | ✗ |
| [`card-9-grid-equal.md`](./card-9-grid-equal.md) | 9 | 3x3 | 3×3 等分 | ✗ |
| [`card-16-grid-equal.md`](./card-16-grid-equal.md) | 16 | 4x4 | 4×4 密网格等分（`card-9-grid-equal` 加密版） | ✗ |

**单张海报模板优先级**（详见 [PRD-EXPORT-CARD-COMPOSE-V1 §5.2](../../PRD-EXPORT-CARD-COMPOSE-V1.md)）：`card-1-full-frame` / `card-6-hero-tl-stack` / `card-6-hero-br-stack` > `card-4-square-top-triband` > 其余无主图模板（不用于海报，含 2026-08-05 追加的 4 套等分模板）。

**追加的 4 套等分模板对 `AVAILABLE_SLOT_COUNTS` 的影响**：`CardGrouper.plan_slot_counts` 是"largest-fits-first"贪心算法，槙数集合从 `{1,4,6,7,9}` 扩展为 `{1,2,4,6,7,8,9,16}` 后，以下张数的默认拆分发生变化（均为预期行为，非回归）：
- `n=2` → `[2]`（原 `[1,1]`）
- `n=3` → `[2,1]`（原 `[1,1,1]`）
- `n=8` → `[8]`（原 `[7,1]`）
- `n=4` 恰好命中时在 `card-4-square-top-triband` / `card-4-grid-equal` 间轮询（原来只有前者）
