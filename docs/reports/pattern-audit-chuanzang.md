# 模板调用统计 · 川藏线

- **tripId**: `chuanzang`
- **照片总数**: 211
- **参与排版**: {'total': 190, 'landscape': 139, 'portrait': 18, 'square': 3, 'panorama': 30, 'tall': 0, 'export_layout': 'auto'}
- **屏总数**: 151（内容屏 121）
- **九宫格配额**: min=4, max=8；实际横版九宫 **6** 次
- **竖版八宫格配额上限**: 4
- **layoutMetrics**: repeat_rate=0.942149, diversity=0.0579

## 已调用模板（按次数）

| 次数 | 中文名 | patternId | layoutHint |
|------|--------|-----------|------------|
| 94 | 单张横版 | `screen-landscape-1` | — |
| 30 | 呼吸留白屏 | `screen-breath-pause` | — |
| 11 | 单张竖版 | `screen-portrait-1` | — |
| 6 | 九宫格（9张横版） | `screen-landscape-9` | — |
| 3 | 单张方图 | `screen-square-1` | — |
| 3 | 四宫格（4张横版） | `screen-landscape-4` | — |
| 2 | 5窗马赛克（主竖+3横） | `screen-mosaic-5-main-portrait-3land` | — |
| 2 | 两张竖版 | `screen-portrait-2` | person-pair |

## 复合模板明细（除单横版/呼吸屏外）

- 章1「4月1–2日」第33屏 · **单张方图** · 1张 · 构成 {'square': 1}
- 章2「4月2日」第12屏 · **5窗马赛克（主竖+3横）** · 5张 · 构成 {'landscape': 4, 'portrait': 1}
- 章2「4月2日」第13屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章2「4月2日」第15屏 · **九宫格（9张横版）** · 9张 · 构成 {'landscape': 9}
- 章2「4月2日」第21屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章2「4月2日」第27屏 · **5窗马赛克（主竖+3横）** · 5张 · 构成 {'landscape': 4, 'portrait': 1}
- 章2「4月2日」第28屏 · **九宫格（9张横版）** · 9张 · 构成 {'landscape': 9}
- 章2「4月2日」第35屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章2「4月2日」第36屏 · **四宫格（4张横版）** · 4张 · 构成 {'landscape': 4}
- 章2「4月2日」第42屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章2「4月2日」第48屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章2「4月2日」第55屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章2「4月2日」第56屏 · **九宫格（9张横版）** · 9张 · 构成 {'landscape': 9}
- 章3「4月2日·二」第7屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章3「4月2日·二」第9屏 · **九宫格（9张横版）** · 9张 · 构成 {'landscape': 9}
- 章3「4月2日·二」第11屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章3「4月2日·二」第12屏 · **四宫格（4张横版）** · 4张 · 构成 {'landscape': 4}
- 章3「4月2日·二」第20屏 · **九宫格（9张横版）** · 9张 · 构成 {'landscape': 9}
- 章3「4月2日·二」第25屏 · **两张竖版** · 2张 · 构成 {'portrait': 2} · hint=`person-pair`
- 章3「4月2日·二」第30屏 · **四宫格（4张横版）** · 4张 · 构成 {'landscape': 4}
- 章3「4月2日·二」第31屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章3「4月2日·二」第47屏 · **九宫格（9张横版）** · 9张 · 构成 {'landscape': 9}
- 章3「4月2日·二」第54屏 · **单张方图** · 1张 · 构成 {'square': 1}
- 章3「4月2日·二」第55屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章3「4月2日·二」第57屏 · **两张竖版** · 2张 · 构成 {'portrait': 2} · hint=`person-pair`
- 章3「4月2日·二」第59屏 · **单张竖版** · 1张 · 构成 {'portrait': 1}
- 章3「4月2日·二」第60屏 · **单张方图** · 1张 · 构成 {'square': 1}

## 已调用原因（要点）

- **单张横版** ×94：横版 run≤3 直接单屏；或九/四宫消费后剩余单张；全景 pano 也映射到此（共 94 次，占主导）。
- **呼吸留白屏** ×30：章节节奏留白（非照片屏）。
- **单张竖版** ×11：竖版单张或短 run 被拆开后的单屏。
- **九宫格（9张横版）** ×6：横版连续 run≥9 且 `can_use_nine()`；206 张相册配额允许最多 8 次，实际 6 次（在配额内）。同一 geo bucket 内凑满 9 张横图时优先吃满九宫。
- **单张方图** ×3：方图单张展示。
- **四宫格（4张横版）** ×3：横版 run≥4 但未走九宫（配额/连续禁忌/桶内不足 9 张）时，burst 或密度规则下选 4 宫格。
- **两张竖版** ×2：竖版连续 2 张；本 trip 仅 1 次，带 `person-pair` hint，人物成对竖图专用。

## 未调用模板及原因

相册取向极度偏横：横 139 · 竖 18 · 方 3 · 全景 30。多数 MCS/竖版模板因「窗口内凑不齐竖版张数」或「已在代码中退役」而未出现。

- `screen-landscape-6`（六宫格（6张横版））：横版 run 切完 nine/4 后常剩 ≤1 张；六宫受连续/配额限制。
- `screen-landscape-3`（三横叠放）：横 run≤3 时规则直接 landscape-1，不组三横。
- `screen-portrait-9`（九宫格（9张竖版））：竖版仅 12 张，无法形成 9 连竖 run；九宫配额也优先横版。
- `screen-portrait-6`（六宫格（6张竖版））：6 连竖 run 不存在。
- `screen-portrait-4`（四宫格（4张竖版））：4 连竖 run 不足。
- `screen-portrait-3`（三竖并列）：竖版 run 太短，被拆成 portrait-1。
- `screen-portrait-grid-8`（竖版八宫格（2×4））：需 >50 张且竖版主导；竖版 18 张，配额 4。
- `screen-portrait-1-landscape-2`（1竖+2横）：需连续 1P+2L 三窗；横版主导流里混合段少。
- `screen-portrait-2-landscape-2`（2竖+2横）：需 2P+2L 四窗；竖版稀缺。
- `screen-mosaic-5-3portrait-2land-balanced`（5窗马赛克（3竖+2横））：需 3P+2L 五窗；竖版仅 12 张。
- `screen-mosaic-5-2portrait-3land-balanced`（5窗马赛克（2竖+3横，已退役））：已从 MOSAIC_5 候选退役（5e97d46）。
- `screen-mosaic-5-main-landscape-2portrait-2land`（5窗马赛克（主横+2竖2横，已退役））：已从 MOSAIC_5 候选退役。
- `screen-mosaic-6-main-hero-plus-5`（6窗主图+5格）：六宫 MCS 需特定 hero 窗；横版 run 多被 nine/4 切走。
- `screen-square-4`（四方格）：方图 3 张，未触发 food/sign 等 mundane grid。
- `screen-tall-1`（超高单图）：无 tall 资产。

## mosaicDecisionLog

共 2 条（可查 winner/fallback 细因）。