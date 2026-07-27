# PRD · Landscape-3 Editorial（三横 2+1）V1

| 属性 | 内容 |
|------|------|
| 状态 | 一期试点 |
| 关联 | [Landscape-2](./PRD-LANDSCAPE-2-EDITORIAL-V1.md) · [MTSO 狗粮 §0](./acceptance-records/mtso-local-dogfood-GUIDE.md) |
| 家族 | `landscape-3-editorial` |

## 1. 目标

在 GA `screen-landscape-3`（等权竖向 stack）之上，增加 **一大两小侧栏** 左右镜像，服务连续三张横图。

## 2. 轮换集

| patternId | 布局 | status |
|-----------|------|--------|
| `screen-landscape-3` | 等权三层 stack（fill） | ga |
| `screen-landscape-3-asymmetric-left` | 左大满高 + 右两小叠 | experimental |
| `screen-landscape-3-asymmetric-right` | 左两小叠 + 右大满高 | experimental |

## 3. 几何（16:9 · CSS-primary）

- 舞台 **固定 16:9**（勿沿用 stack 的 `aspect-ratio: auto`）
- 大槽一列满高；侧栏两槽等分上下
- 列比约 `1.7fr | 1fr`；小 gap；镜像只换列序
- 三槽 `fit: cover`；opt-out 通用 contain-collapse

## 4. 准入与选型

- 双开关：`layout.landscape_3_editorial.enabled` ∧ `mosaic.template_experiments`
- 窗口恰 3 横且近时；家族 OFF → fill stack
- 左强 → asym-left；右强 → asym-right；tie → **仅**两 asym 轮换（`reason=asym_tie`，勿被 fill 权重压过）

## 5. 验收

| ID | 断言 |
|----|------|
| AC-L3E-01 | 默认 OFF → 短三横仍可为 stack / 单图路径，不出 asym |
| AC-L3E-02 | ON + cohort → 可出现 asym-left/right；fill 仍可 |
| AC-L3E-03 | schema 含两 asym id + `landscape3Picker` |
| AC-L3E-04 | tie → asym（非 fill） |
| AC-L3E-05 | 连续 triple 节奏不连发炸版（走 triple 连续禁） |
