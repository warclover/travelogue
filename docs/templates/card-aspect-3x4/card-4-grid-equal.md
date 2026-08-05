# card-4-grid-equal

- displayName: 四图 · 2×2 等分
- status: ga
- stage: 3:4
- grid: 2x2
- source: 用户设计稿 img11（2026-08-05）

| slot | role | row | col | rowSpan | colSpan | displayAspect |
|------|------|-----|-----|---------|---------|---------------|
| 0 | portrait | 0 | 0 | 1 | 1 | 0.75 |
| 1 | portrait | 0 | 1 | 1 | 1 | 0.75 |
| 2 | portrait | 1 | 0 | 1 | 1 | 0.75 |
| 3 | portrait | 1 | 1 | 1 | 1 | 0.75 |

**用途**：无主图槙，4 张零裁切竖版拼图（一横一竖分割线，2×2 田字格）。**基准网格为 2x2，而非 3x3**。与 `card-4-square-top-triband` 同为 4 槙模板但定位不同：本模板无主图、无强制裁切，用于 4 张照片时的"平权"备选（`pick_template_for_count(4, ...)` 在两者间轮询）；不作为单张海报首选（无主图）。
