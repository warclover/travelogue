# 3:4 卡片模板库（card-aspect-3x4）

| 属性 | 内容 |
|------|------|
| **来源** | [PRD-EXPORT-CARD-COMPOSE-V1](../../PRD-EXPORT-CARD-COMPOSE-V1.md) §6 · [ADR-021 v0.2](../../adr/021-export-compose-dual-engine.md) |
| **用途** | 小红书 / 单张海报 / 画册三出口共用的 3:4 卡片版式库 |
| **状态** | Draft · 起步 4 套（每槙数 1 套），设计稿待补 |

---

## 与 `docs/templates/slot-aspect/` 的关系

`slot-aspect/` 是 16:9 Web 长卷屏模板（`stage: 16:9`），本目录是**独立的 3:4 画布模板**（`stage: 3:4`）。两者共用同一份 `.md` slot 表格式约定（`slot | role | displayAspect`），但 **不共用数值**——16:9 屏的 `displayAspect` 是按那个画幅算的，不能直接套进 3:4 画布。

选版式的**算法**（按张数 + 横竖版构成挑 pattern）复用 `screen_planner.py` 的判定顺序，但落点是本目录的模板，不是 `slot-aspect/`。

## 文件约定

沿用 `slot-aspect/*.md` 的表头：

```markdown
# card-{n}-{name}

- displayName: 中文名
- status: pending-design | experimental | ga
- stage: 3:4

| slot | role | displayAspect |
|------|------|---------------|
| 0 | portrait/landscape/main | 0.xxxx |
```

`displayAspect` 必须按 3:4 母版重新计算（不得复制 16:9 数值）。

## 起步规模（4 套，每槙数 1 套）

| 文件（待建） | 槙数 | 版式 | 状态 |
|---|---|---|---|
| `card-1-full.md` | 1 | 全卡单图（cover + 主体安全裁切） | pending-design |
| `card-2-split.md` | 2 | 双图（上下 / 左右，具体待设计稿定） | pending-design |
| `card-3-hero-plus-2.md` | 3 | 1 主 + 2 副 | pending-design |
| `card-4-grid.md` | 4 | 2×2 等分 | pending-design |

> 设计稿到位后，按此文件名逐套落地 slot 表；渲染侧对接 `CardTemplateSelector` / `CardRenderer`（见 PRD §4、§6）。
