# 附录 A · 中间页数据包目录

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-15 |
| **DOC-STATUS** | **active** |
| **规范上级** | [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（D-U-03 / D-U-06 / D-U-10） |
| **字段合同** | [TEMPLATE-SYSTEM-UPGRADE.md](./TEMPLATE-SYSTEM-UPGRADE.md) §5 |
| **示意图来源** | [`画册编排.md`](../画册编排.md) §22（舞台 √2 **已作废**；槽账与用途保留） |
| **状态** | `designed` = 示意图已审、数据包已写、**未入库代码** |

本目录是活目录的机器合同，不是示意图相册。新稿按同一字段追加。舞台一律 **16:9**（D-U-06）。裁切一律 `fitPolicy: relative-to-slot`（D-U-10）。文案区可空，**不计入** `slotCount`。

---

## 0. 目录总表

| 正式 id | 示意图别名 | 账徽 | 槽 | 角色 | 状态 |
|---------|------------|------|----|------|------|
| `page-1-hero-land` | 同 | `1L` | 1L | `hero-land` | designed |
| `page-2-pair-port` | 同 | `2P` | 2P | `pair-port` | designed |
| `page-3-port` | `page-3-organic-port` | `3P` | 3P | `row-port-3` | designed |
| `page-4-grid-land` | `page-4-grid-equal` | `4L` | 4L | `grid-4-land` | designed |
| `page-3-2l1p-right` | `page-3-organic-rport` | `2L1P` | 2L1P | `stack-l-port` | designed |
| `page-3-2l1p-left` | `page-3-organic-lport` | `2L1P` | 1P2L | `port-stack-l` | designed |

正式 id 服从 `page-{槽数}-{朝向或混向}[-几何词]`。示意图里带 `organic` 的名字只作别名，系列与 CI 认正式 id。

`page-4-grid-equal` 改为 `page-4-grid-land`：槽全是横，`equal` 不表达朝向账。

---

## 1. 全库引用

```yaml
stage.aspect: "16:9"
fitPolicy: relative-to-slot
# 同比例铺满
# 比槽更宽 → 以宽对齐，上下留白
# 比槽更高 → 以高对齐，左右留白
# 朝向不符 → 禁入，不硬裁
```

`margin` / `gap` 为相对页宽（或页高，见字段）的比例，不写毫米。

---

## 2. `page-1-hero-land` · 单图 · 横版英雄

来源：画册编排 §22 首张范例。现网顶岗：`screen-landscape-1`（满幅，无页边距，**不是同一张**）。

```yaml
id: page-1-hero-land
version: 1
status: designed
kind: primitive
displayName: 单图 · 横版英雄
familyId: hero-land
canonical: page-1-hero-land
aliases: []
program: hero
densityClass: airy
role: hero-land

stage:
  aspect: "16:9"
  margin: { top: 0.08, right: 0.10, bottom: 0.08, left: 0.10 }

slotCount: 1
mix: { portrait: 0, landscape: 1 }

placement:
  groupAlign: center
  distribute: none

slots:
  - { index: 0, role: main, orient: landscape, aspect: "4:3" }

copyRegions: []

admit:
  forbidOrient: [portrait]
  requireOrient: [landscape]

themes: [landscape, architecture, portrait]
usage:
  whenToUse: 单张横图高光；风光或合影优先
  whenNotToUse: 必须消化竖图；需要多图并置

fitPolicy: relative-to-slot
glyph:
  badge: 1L
  thumb: 一横槽居中，四周留白
```

槽尺寸：`slotWidth = contentWidth`；`slotHeight = slotWidth / (4/3)`；整槽在 content 盒内居中。4:3 横槽落在 16:9 纸上，左右留白宽于上下——与示意图「槽比等于所标比」一致。

---

## 3. `page-2-pair-port` · 双竖版并排

来源：画册编排 §22。现网顶岗：`screen-portrait-2-gallery`（更近：等大居中留白）或 `screen-portrait-2`（满幅等分）。

```yaml
id: page-2-pair-port
version: 1
status: designed
kind: primitive
displayName: 双竖版并排
familyId: portrait-row
canonical: page-2-pair-port
aliases: []
program: mosaic
densityClass: standard
role: pair-port

stage:
  aspect: "16:9"
  margin: { top: 0.08, right: 0.06, bottom: 0.14, left: 0.06 }
  gapX: 0.02

slotCount: 2
mix: { portrait: 2, landscape: 0 }

placement:
  groupAlign: center
  distribute: even-x

slots:
  - { index: 0, role: portrait, orient: portrait, aspect: "3:4" }
  - { index: 1, role: portrait, orient: portrait, aspect: "3:4" }

copyRegions:
  - { id: caption, edge: bottom, optional: true }

admit:
  forbidOrient: [landscape]
  requireOrient: [portrait]

themes: [portrait, pet, landscape]
usage:
  whenToUse: 双人像并排；竖构图风景或宠物成对
  whenNotToUse: 本页必须消化横图；需要明显主次

fitPolicy: relative-to-slot
glyph:
  badge: 2P
  thumb: 两红竖并排，组居中；底可空文案
```

几何：content 宽三等分思路的双槽版——`slotWidth = (contentWidth - gapX) / 2`；`slotHeight = slotWidth / 0.75`；底部 margin 更大，给可选底栏。

---

## 4. `page-3-port` · 三竖版并排

来源：画册编排 `page-3-organic-port`（由早期 `page-3-port` 补全）。升级方案 §5.6 范例与本条合并为同一张。现网顶岗：`screen-portrait-3`（9:16 满幅三竖，**不是同一张**）；杂志向可参考 `screen-portrait-3-editorial`。

```yaml
id: page-3-port
version: 1
status: designed
kind: primitive
displayName: 三竖版并排
familyId: portrait-row
canonical: page-3-port
aliases: [page-3-organic-port]
program: grid
densityClass: standard
role: row-port-3

stage:
  aspect: "16:9"
  margin: { top: 0.08, right: 0.06, bottom: 0.08, left: 0.06 }
  gapX: 0.02

slotCount: 3
mix: { portrait: 3, landscape: 0 }

placement:
  groupAlign: center
  distribute: even-x

slots:
  - { index: 0, role: portrait, orient: portrait, aspect: "3:4" }
  - { index: 1, role: portrait, orient: portrait, aspect: "3:4" }
  - { index: 2, role: portrait, orient: portrait, aspect: "3:4" }

copyRegions:
  - { id: kicker, edge: top, optional: true }
  - { id: caption, edge: bottom, optional: true }

admit:
  forbidOrient: [landscape]
  requireOrient: [portrait]

themes: [portrait, pet, food, landscape]
usage:
  whenToUse: 三人像、宠物、美食或竖构图风景需要并排、无主次时
  whenNotToUse: 本页必须消化横图；或需要一张明显更大的英雄

fitPolicy: relative-to-slot
glyph:
  badge: 3P
  thumb: 三红竖均分、组垂直居中，上下留白
```

美食可进 `themes: food`，默认不当 `hero` / `opener` 满幅（FRP）。

---

## 5. `page-4-grid-land` · 横版四宫

来源：画册编排 `page-4-grid-equal`。现网顶岗：`screen-landscape-4`（16:9 四横 2×2，现网偏满幅；本脸要求整组居中留白）。

```yaml
id: page-4-grid-land
version: 1
status: designed
kind: primitive
displayName: 横版四宫
familyId: land-grid
canonical: page-4-grid-land
aliases: [page-4-grid-equal]
program: grid
densityClass: standard
role: grid-4-land

stage:
  aspect: "16:9"
  margin: { top: 0.07, right: 0.07, bottom: 0.07, left: 0.07 }
  gapX: 0.02
  gapY: 0.03

slotCount: 4
mix: { portrait: 0, landscape: 4 }

placement:
  groupAlign: center
  distribute: even-grid
  columns: 2
  rows: 2

slots:
  - { index: 0, role: landscape, orient: landscape, aspect: "4:3" }
  - { index: 1, role: landscape, orient: landscape, aspect: "4:3" }
  - { index: 2, role: landscape, orient: landscape, aspect: "4:3" }
  - { index: 3, role: landscape, orient: landscape, aspect: "4:3" }

copyRegions: []

admit:
  forbidOrient: [portrait]
  requireOrient: [landscape]

themes: [portrait, landscape, pet, food]
usage:
  whenToUse: 四张横构图等权并置（人像/风景/宠物/美食）
  whenNotToUse: 必须消化竖图；需要一张明显英雄

fitPolicy: relative-to-slot
glyph:
  badge: 4L
  thumb: 2×2 蓝横槽，整组居中，槽间与页边留白
```

---

## 6. `page-3-2l1p-right` · 左双横 · 右竖主

来源：画册编排 `page-3-organic-rport`。现网顶岗：`screen-landscape-2-portrait-1`（左两横叠 + 右竖满高；现网更满幅）。

```yaml
id: page-3-2l1p-right
version: 1
status: designed
kind: primitive
displayName: 三图 · 左双横右竖
familyId: land-stack-port
canonical: page-3-2l1p-right
aliases: [page-3-organic-rport]
program: mosaic
densityClass: standard
role: stack-l-port

stage:
  aspect: "16:9"
  margin: { top: 0.07, right: 0.06, bottom: 0.07, left: 0.06 }
  gapX: 0.02
  gapY: 0.025

slotCount: 3
mix: { portrait: 1, landscape: 2 }

placement:
  groupAlign: center
  distribute: split-left-stack-right-port

slots:
  - { index: 0, role: landscape, orient: landscape, aspect: "4:3" }
  - { index: 1, role: landscape, orient: landscape, aspect: "4:3" }
  - { index: 2, role: main, orient: portrait, aspect: "3:4" }

copyRegions: []

admit:
  perSlot: true
  # 横槽禁竖，竖槽禁横；不要整页一刀切

themes: [landscape, portrait, architecture, sequence]
usage:
  whenToUse: 右竖为主图，左两张横图辅（过程/对仗）
  whenNotToUse: 三张都是竖或都是横；需要等权三竖

fitPolicy: relative-to-slot
glyph:
  badge: 2L1P
  thumb: 左两蓝横叠，右一红竖，竖高等于左列
```

几何：右竖槽高度 = 左两横槽高度 + `gapY`；左列宽与右列宽按 4:3 / 3:4 解，使整组落在 content 盒内居中。

---

## 7. `page-3-2l1p-left` · 左竖主 · 右双横

来源：画册编排 `page-3-organic-lport`，为上一条左右镜像。现网顶岗：`screen-portrait-1-landscape-2`。

```yaml
id: page-3-2l1p-left
version: 1
status: designed
kind: primitive
displayName: 三图 · 左竖右双横
familyId: land-stack-port
canonical: page-3-2l1p-left
aliases: [page-3-organic-lport]
program: mosaic
densityClass: standard
role: port-stack-l

stage:
  aspect: "16:9"
  margin: { top: 0.07, right: 0.06, bottom: 0.07, left: 0.06 }
  gapX: 0.02
  gapY: 0.025

slotCount: 3
mix: { portrait: 1, landscape: 2 }

placement:
  groupAlign: center
  distribute: split-left-port-right-stack

slots:
  - { index: 0, role: main, orient: portrait, aspect: "3:4" }
  - { index: 1, role: landscape, orient: landscape, aspect: "4:3" }
  - { index: 2, role: landscape, orient: landscape, aspect: "4:3" }

copyRegions: []

admit:
  perSlot: true

themes: [landscape, portrait, architecture, sequence]
usage:
  whenToUse: 左竖为主图，右两张横图辅
  whenNotToUse: 三张同朝向；需要等权三竖

fitPolicy: relative-to-slot
glyph:
  badge: 2L1P
  thumb: 左一红竖，右两蓝横叠（上条镜像）
```

与 `page-3-2l1p-right` 同族。系列写角色即可换边，不必当成两本系列。

---

## 8. 待画（活目录配额 12–18，本波先列角色）

下列没有示意图，**不写假几何**。系列 W1 用附录 B 的现网顶岗；W3 才换 `page-*`。

| 建议正式 id | 角色 | 账徽 | 要画什么 |
|-------------|------|------|----------|
| `page-1-hero-port` | `hero-port` | `1P` | 单竖英雄，3:4 居中留白 |
| `page-2-pair-land` | `pair-land` | `2L` | 双横上下或左右，等权 |
| `page-2-land-asym` | `pair-land-hero` | `2L` | 双横左大右小 |
| `page-4-2p2l` | `grid-2p2l` | `2L2P` | 2×2 棋盘，横蓝竖红 |
| `page-1-breath` | `breath` | `1L` 或字页 | 低密度呼吸；槽 0–1 |
| `page-journal-1` | `journal` | 字+图 | 字是建筑，1–2 槽 |
| `page-4-hero-rail` | `hero-rail-4` | `1L3?` | 大图 + 侧栏；对照现网 hero-70 |
| `page-6-dense` | `grid-dense` | `6L` | 密网；全书少用 |

观察室配额 ≤8，不进本表直到有假说与到期日。

---

## 9. 不进本目录

| 对象 | 去向 |
|------|------|
| 全部 `screen-*` | 历史归档；只 `get` |
| `card-*` | ECC 柜，本波不动 |
| 封面 / 封底 | 封面封底入口登记，不在此写拼图槽账 |
| 成册系列 | 另文；图标是密度条 |

---

## 10. 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-08-15 | 收录 6 张已画脸；舞台改 16:9；冻结正式 id 与示意图别名。 |
