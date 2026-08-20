# 附录 B · 页型角色对照表

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-15 |
| **DOC-STATUS** | **active** |
| **规范上级** | [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（D-U-05 / D-U-08 / D-U-09 · BLK-TSU-03） |
| **目标脸** | [PAGE-PACKET-CATALOG.md](./PAGE-PACKET-CATALOG.md) |
| **现网脸** | [WEB-JOURNAL-MOSAIC-TEMPLATES.md](./WEB-JOURNAL-MOSAIC-TEMPLATES.md) |
| **用途** | 系列只写 **角色**。W1 用「现网顶岗」出预演；W3 换成「目标 `page-*`」。 |

系列 YAML 禁止写死脸 ID。顶岗与目标都挂在角色下，换脸只改 `faceHint`。

---

## 0. 怎么读

| 列 | 含义 |
|----|------|
| **角色** | 系列画布上的芯片；统计按此聚合 |
| **纲领** | 与 EDC `program` 共用 |
| **narrativeRole** | 引用 [EDC §6.2.1](../PRD-EDITORIAL-COMPILER-V1.md)；禁止第三枚举。缺 `program` 时由此 + `patternId` 推导 |
| **槽数带** | 匹配器硬约束；拼图不得越带选脸 |
| **目标脸** | 数据包正式 id；`designed` 才能进正式页型 |
| **现网顶岗** | 界面称**暂用旧版**：W1 可渲染的 `screen-*`；几何不必同构，朝向账必须能用 |
| **柜** | 目标进正式页型后，暂用旧版退历史归档 |

「近」= 槽数与朝向账接近，舞台或留白不同。**不是同一张**，旧 trip 继续认顶岗 id。

---

## 1. 系列会用到的角色

| 角色 | 纲领 | narrativeRole | 槽数带 | 账徽 | 目标脸 | 现网顶岗 | 顶岗近因 | W1 |
|------|------|---------------|--------|------|--------|----------|----------|----|
| `title-opener` | opener | `plate` + 封面前缀（W0 可增 `opener`） | 0–2 | 书衣 | 登记 CAL/ABE 封面，不写 `page-*` | 书衣现行 SKU | 封面不是拼图窗 | 登记 |
| `chapter-opener` | opener | `plate` + opener 前缀（或 W0 `opener`） | 0–2 | `1L` | 待画或复用 `page-1-hero-land` | `screen-landscape-1` | 单横满屏，现网章首默认 | 顶岗 |
| `hero-land` | hero | `hero_single` | 1 | `1L` | **`page-1-hero-land`** | `screen-landscape-1` | 单横；顶岗满幅、目标留白 | 目标已画 |
| `hero-port` | hero | `hero_single` | 1 | `1P` | `page-1-hero-port`（待画） | `screen-portrait-1` | 单竖满屏 9:16 | 顶岗 |
| `pair-port` | mosaic | `mosaic_flat` | 2 | `2P` | **`page-2-pair-port`** | `screen-portrait-2-gallery` | 双竖等大居中；次选 `screen-portrait-2` | 目标已画 |
| `pair-land` | mosaic | `mosaic_flat` | 2 | `2L` | `page-2-pair-land`（待画） | `screen-landscape-2` | 双横上下 stack | 顶岗 |
| `pair-land-hero` | mosaic | `mosaic_hero` | 2 | `2L` | `page-2-land-asym`（待画） | `screen-landscape-2-asymmetric-left` | 双横左大右小（实验白名单） | 顶岗·实验 |
| `row-port-3` | grid | `stack` | 3 | `3P` | **`page-3-port`** | `screen-portrait-3` | 三竖；顶岗 9:16 满幅 | 目标已画 |
| `row-land-3` | grid | `stack` | 3 | `3L` | 待画 | `screen-landscape-3` | 三横上下 stack | 顶岗 |
| `stack-l-port` | mosaic | `mosaic_hero` | 3 | `2L1P` | **`page-3-2l1p-right`** | `screen-landscape-2-portrait-1` | 左两横 + 右竖 | 目标已画 |
| `port-stack-l` | mosaic | `mosaic_hero` | 3 | `2L1P` | **`page-3-2l1p-left`** | `screen-portrait-1-landscape-2` | 左竖 + 右两横 | 目标已画 |
| `mix-1p2l` | mosaic | `mosaic_hero` | 3 | `1P2L` | 可先复用 `port-stack-l` | `screen-portrait-1-landscape-2` | 与上同族 | 复用 |
| `grid-4-land` | grid | `stack` | 4 | `4L` | **`page-4-grid-land`** | `screen-landscape-4` | 四横 2×2 | 目标已画 |
| `grid-4-port` | grid | `stack` | 4 | `4P` | 待画 | `screen-portrait-4` | 四竖 2×2，9:16 舞台 | 顶岗 |
| `grid-2p2l` | grid | `stack` | 4 | `2L2P` | `page-4-2p2l`（待画） | `screen-portrait-2-landscape-2` | 16:9 等分 2×2 | 顶岗 |
| `hero-rail-4` | mosaic | `mosaic_hero` | 4 | `1L3L` | `page-4-hero-rail`（待画） | `screen-mosaic-4-hero-70-sidebar` | 左约 70% + 右三格 | 顶岗 |
| `grid-dense` | grid | `stack` | 6–9 | `6L` | `page-6-dense`（待画） | `screen-mosaic-6-main-hero-plus-5` | 现网统一窗六图；密网全书少用 | 顶岗·慎用 |
| `breath` | breath | `breath` | 0–2 | 疏 | `page-1-breath`（待画） | `screen-full-frame` 或空页+单图 | 密度跌一档，勿用密网顶 | 顶岗 |
| `journal` | journal | `plate` + SCR/editorial | 1–3 | 字 | `page-journal-1`（待画） | 无合格顶岗 | 字是建筑；**W1 金样禁止写此角色** | 缺 |
| `peak` | peak | `data-role=peak\|moment`（与 narrativeRole 并存） | 1–2 | `1L`/`1P` | 复用 hero | `screen-landscape-1` / `screen-portrait-1` | 高潮位，不随页数加倍 | 复用 hero |
| `closer` | hero / opener | `hero_single` | 1–2 | `1L` | 复用 `hero-land` 或书衣封底 | `screen-landscape-1` + 封底登记 | 只在收束 | 复用 |

**W1 可写系列的角色（目标已画或顶岗可用）**：上表除 `journal` 外均可。`journal` 等有示意图再进金样。

**W1 优先用已画 6 张**：`hero-land` / `pair-port` / `row-port-3` / `grid-4-land` / `stack-l-port` / `port-stack-l`。8/16 疏正密应先用这 6 个角色把节奏写出，缺的用 hero / breath 顶岗补位，不要为了填满配额去锁 6 槽密网。

---

## 2. 现网统一窗 → 角色（反向，防选错顶岗）

现网 11 个统一窗只作顶岗，**不**因这张表进入活目录。

| 现网 id | mix | 顶给哪个角色 | 不要顶给 |
|---------|-----|--------------|----------|
| `screen-portrait-3` | 3P | `row-port-3` | `page-3-port` 的「同一张」 |
| `screen-landscape-3` | 3L | `row-land-3` | 三竖 |
| `screen-portrait-1-landscape-2` | 1P2L | `port-stack-l` | 右竖主（那是 `stack-l-port`） |
| `screen-portrait-2-landscape-2` | 2P2L | `grid-2p2l` | 四横宫 |
| `screen-portrait-4` | 4P | `grid-4-port` | `grid-4-land` |
| `screen-landscape-4` | 4L | `grid-4-land` | 四竖 |
| `screen-mosaic-4-hero-70-sidebar` | 4L | `hero-rail-4` | 等权四宫 |
| `screen-mosaic-5-main-portrait-3land` | 1P4L | 观察室候选，W1 不进系列 | 当 hero |
| `screen-mosaic-5-hero-3-2-plus-4` | 5L* | 观察室；主槽实为竖形窗 | 按名字当 5 横 |
| `screen-mosaic-5-main-hero-plus-4` | **6L** | 禁止：id 撒谎 | 任何 5 槽角色 |
| `screen-mosaic-6-main-hero-plus-5` | 6L | `grid-dense` 慎用 | opener / hero / peak |

\* `screen-mosaic-5-hero-3-2-plus-4` 主槽是竖形窗，账徽不要标成 `5L`。W1 不要用它顶岗。

非拼图窗（planner，不进 MCS 统一窗）只给单图/双竖角色顶岗：

| 现网 id | 顶给 |
|---------|------|
| `screen-landscape-1` | `hero-land` / `chapter-opener` / `peak` / `closer` |
| `screen-portrait-1` | `hero-port` / `peak` |
| `screen-full-frame` | `breath`（特殊比） |
| `screen-portrait-2` | `pair-port` 次选（满幅，不如 gallery） |
| `screen-landscape-2` | `pair-land` |
| `screen-portrait-3-editorial` | `row-port-3` 杂志向次选 |

实验白名单可作观察室顶岗，**不**写进 W1 金样默认序列：`screen-portrait-2-gallery` 已破例（它是 `pair-port` 最近的顶岗）。其余非对称双图、3p2l 家族等 W3 再议。

---

## 3. 封面 / 封底 / 成册（不是中间页角色）

| 对象 | 系列里怎么写 | 顶岗 | 目标 |
|------|--------------|------|------|
| 封面 | 系列头 `coverHint`，不占中间页档位 | 现行 ABE/CAL SKU | 登记，不重造（D-U-13） |
| 封底 | 系列尾 `backHint` | 现行书衣 | 同上 |
| 成册 | 文件自身（`magazine-16-standard`） | 无 | 密度条图标；不是一张脸 |

统计：封面 1 / 封底 1 单独一行，通常不计入 8/16 中间页档。

---

## 4. 匹配器怎么用这张表

```
页.role → 本表槽数带 + 目标族
组.朝向账 → 与族 mix 求交
  交得上：W3 选目标 page-*；W1 选顶岗 screen-*
  交不上：同纲领兄弟角色 → flex → 靠档
```

禁止：为了用上某张现网脸，改系列角色名。禁止：把撒谎 id（`…hero-plus-4` 实为 6 槽）写进系列。

---

## 5. 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-08-15 | 首版。6 个已画角色对齐附录 A；其余给现网顶岗。 |
| 0.2.0 | 2026-08-15 | BLK-TSU-03：每行补 `narrativeRole`（引用 EDC §6.2.1）；`journal` 标明 W1 禁写。 |
