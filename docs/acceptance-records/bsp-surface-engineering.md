# BSP Surface · 工程决策记录

| 日期 | 2026-06-08 |
|------|------------|
| 关联 | [PRD-页面优化.md](../PRD-页面优化.md) |

## 1. `full_frame_fit_for_asset`（P0.5 增强）

**问题**：仙本那 103 屏 `screen-full-frame` 素材普遍带 `person/face` vision 标签，原 `portrait_fit_for_asset` 将全部判为 `contain`，导致左右信箱。

**策略**：

| 条件 | fit |
|------|-----|
| 无人物标签 | `cover` |
| 竖图 + 人物 | `contain` |
| 横图 + 人物 + `faceRatio < 0.15` | `cover`（远景人物） |
| 横图 + `faceRatio ≥ 0.15` | `contain`（合影/近景） |

**触点**：`travelogue/curation/asset_subject.py` · `screen_planner` · `context.py`

**阈值校准**：Dogfood 若误裁人脸，调高 `face_ratio_contain`（默认 0.15）。

## 2. viewport-fit 宽度 vs AC-BSP-01

PRD §2.2.2 原式：`width = min(rail, vw, vh×ar)` 会使不同 aspect 屏宽不一致，违反 AC-BSP-01。

**决议（2026-06-08，2026-06-08 修订）**：

- **宽度**：`width: min(100%, 100dvh × --screen-weight × --screen-fit-ar)` + `max-width: --content-rail`
  - 未触顶时等同满 rail；`max-height` 触顶时收窄宽度，**保持原生 `--screen-fit-ar`**，避免标准 3:2 被拉成超宽槽
- **高度**：`aspect-ratio: --screen-fit-ar` + `max-height: 100dvh × --screen-weight`

未实现运行时 `--viewport-ar`；按屏输出 `--screen-fit-ar` 即可。

## 3. T2 Wide 呈现

`presentation tier = wide`（2.0–2.8）的单槽 `screen-landscape-1` **使用原生 `--screen-aspect`**，不启用 viewport-fit。仅 **ultra（≥2.8）** 单槽走 `layout-screen--viewport-fit` + `tier-ultra`。

**规划层**：`aspectKind=panorama` 且 native w/h &lt; 2.8 的素材按 **landscape** 组屏，不单开超宽舞台。

## 4. 阅读面拆分（BSP-3）

| profile | folio | plate meta |
|---------|-------|------------|
| `studio_preview` | lite | 显示 |
| `reader_immersive` | off | CSS 隐藏 |

Studio preview-toolbar「阅读视图」在客户端切换 `data-surface-mode`，无需重渲染。
