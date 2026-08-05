# card-4-square-top-triband

- displayName: 四图 · 顶部近方图 + 底部三竖版
- status: ga
- stage: 3:4
- grid: 3x3
- source: 用户设计稿 img9（2026-08-05）

| slot | role | row | col | rowSpan | colSpan | displayAspect |
|------|------|-----|-----|---------|---------|---------------|
| 0 | main | 0 | 0 | 2 | 3 | 1.125 |
| 1 | portrait | 2 | 0 | 1 | 1 | 0.75 |
| 2 | portrait | 2 | 1 | 1 | 1 | 0.75 |
| 3 | portrait | 2 | 2 | 1 | 1 | 0.75 |

**用途**：全模板库中**唯一需要裁切**的槙位（slot 0，`displayAspect≈1.125` 接近方形，横/竖版照片都无法零裁切贴入，需 cover-crop）。渲染时 slot 0 应走更保守的主体安全裁切（`subject.py`），避免裁到人脸/主体。因含近方形主图槙，可作为单张海报候选之一，但优先级低于 `card-1-full-frame` / `card-6-hero-tl-stack` / `card-6-hero-br-stack`（那三者裁切损失更小）。
