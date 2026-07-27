# PRD · Mixed 1P2L（竖+两横）V1

| 属性 | 内容 |
|------|------|
| 状态 | 一期试点 |
| 关联 | [Mixed 1L1P](./PRD-MIXED-1L1P-V1.md) · [MTSO 狗粮 §0](./acceptance-records/mtso-local-dogfood-GUIDE.md) |
| 家族 | `mixed-1p2l` |

## 1. 目标

在 GA `screen-portrait-1-landscape-2`（左竖 + 右两横叠）之上，增加 **左右镜像**（左两横叠 + 右竖满高）。不新建 fill id。

## 2. 轮换集

| patternId | 布局 | status |
|-----------|------|--------|
| `screen-portrait-1-landscape-2` | 左竖满高 + 右两横叠（fill） | ga |
| `screen-landscape-2-portrait-1` | 左两横叠 + 右竖满高 | experimental |

## 3. 几何（16:9 · CSS-primary）

- 2×2 网格：竖槽 `row span 2`；两横等分另一列
- 列比与 fill 对齐（等宽 `1fr 1fr`）
- 竖槽满高；横槽 cover；opt-out contain-collapse

## 4. 准入与选型

- 双开关：`layout.mixed_1p2l.enabled` ∧ `mosaic.template_experiments`
- 硬门复用 p1l2：标准竖 + 两横、近时、**竖图不得含人**
- OFF / 不可见 → fill p1l2
- 竖强 → fill；横侧更强 / tie → 可轮换镜像（`strength` / `rotate`）

## 5. 验收

| ID | 断言 |
|----|------|
| AC-M1P2L-01 | OFF → 仍只出 `screen-portrait-1-landscape-2` |
| AC-M1P2L-02 | ON + cohort → 可出 `screen-landscape-2-portrait-1` |
| AC-M1P2L-03 | schema 含镜像 id + `mixed1p2lPicker` |
| AC-M1P2L-04 | 竖图含人仍拒混排（硬门） |
