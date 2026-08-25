# 备用库总表

人读索引。机器合同以 [catalog.yaml](./catalog.yaml) 与各夹 `packet.yaml` 为准。微缩见 [gallery.html](./gallery.html)。星级只看 [stars.yaml](./stars.yaml)，本表不列。

| 备用 id | 中文名 | 账徽 | 槽 | 角色 | 同族兄弟 | 意图顶岗 | 状态 |
|---------|--------|------|----|------|----------|----------|------|
| `page-1-hero-land-right` | 单图 · 横版英雄 · 居中 | `1L` | 1L | `hero-land` | `page-1-hero-land` · `-wide` · `-ultra` | `screen-landscape-1`（满幅，不是同一张） | sketch |
| `page-1-hero-land-wide` | 单图 · 横版英雄 · 16:9 | `1L` | 1L | `hero-land` | `page-1-hero-land` · `-right` · `-ultra` | `screen-landscape-1`（满幅，不是同一张） | sketch |
| `page-1-hero-land-ultra` | 单图 · 横版英雄 · 21:9 | `1L` | 1L | `hero-land` | `page-1-hero-land` · `-right` · `-wide` | `screen-panorama-1`（文档有、仓库未见 YAML） | sketch |
| `page-1-hero-square-right` | 单图 · 方图英雄 · 右齐 | `1S` | 1S | `hero-square` | （本族第一张；旧名 `page-1-hero-square`） | 无合格现网顶岗 | sketch |
| `page-1-hero-port` | 单图 · 竖版英雄 | `1P` | 1P | `hero-port` | （本族第一张；附录 A 已预留） | `screen-portrait-1`（满幅 9:16，不是同一张） | sketch |
| `page-2-pair-port` | 双竖版并排 | `2P` | 2P | `pair-port` | `page-3-port`（附录 A 已画） | `screen-portrait-2-gallery`（不是同一张） | sketch |
| `page-2-1p1l` | 左竖右横 | `1P1L` | 1P1L | `mix-1p1l` | **`page-2-1l1p`** | `screen-portrait-1-landscape-1`（满高 cover，不是同一张） | sketch |
| `page-2-1l1p` | 左横右竖 | `1L1P` | 1L1P | `mix-1l1p` | **`page-2-1p1l`**（镜像） | `screen-landscape-1-portrait-1`（满高 cover，不是同一张） | sketch |
| `page-2-pair-land` | 双横版并排 | `2L` | 2L | `pair-land` | `page-2-pair-land-ultra`（超宽叠，不是 4:3 叠） | `screen-landscape-2`（上下 stack，不是同一张） | sketch |
| `page-2-pair-land-ultra` | 双超宽叠放 | `2L` | 2L | `pair-land-ultra` | `page-2-pair-land` | `screen-landscape-2`（不是同一张） | sketch |
| `page-3-port` | 三竖并排 | `3P` | 3P | `row-port-3` | `page-2-pair-port` | `screen-portrait-3`（9:16 满幅，不是同一张） | sketch |
| `page-3-2l1p-left` | 左竖右双横 | `1P2L` | 1P2L | `port-stack-l` | **`page-3-2l1p-right`** | `screen-portrait-1-landscape-2`（不是同一张） | sketch |
| `page-3-2l1p-right` | 左双横右竖 | `2L1P` | 2L1P | `stack-l-port` | **`page-3-2l1p-left`**（镜像） | `screen-landscape-2-portrait-1`（不是同一张） | sketch |
| `page-2-pair-square` | 双方图并排 | `2S` | 2S | `pair-square` | `page-1-hero-square-right` | 无合格现网顶岗 | sketch |
| `page-3-1s2l-left` | 左方右双横 | `1S2L` | 1S2L | `square-stack-l` | **`page-3-1s2l-right`** | 无合格现网顶岗 | sketch |
| `page-3-1s2l-right` | 左双横右方 | `2L1S` | 2L1S | `stack-l-square` | **`page-3-1s2l-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-2-1s1p` | 左方右竖 | `1S1P` | 1S1P | `mix-1s1p` | **`page-2-1p1s`** | 无合格现网顶岗 | sketch |
| `page-2-1p1s` | 左竖右方 | `1P1S` | 1P1S | `mix-1p1s` | **`page-2-1s1p`**（镜像） | 无合格现网顶岗 | sketch |
| `page-2-1l1p-wide` | 左宽右竖 | `1L1P` | 1L1P | `mix-1l1p-wide` | **`page-2-1p1l-wide`** | 无合格现网顶岗 | sketch |
| `page-2-1p1l-wide` | 左竖右宽 | `1P1L` | 1P1L | `mix-1p1l-wide` | **`page-2-1l1p-wide`**（镜像） | 无合格现网顶岗 | sketch |
| `page-3-land` | 三横并排 | `3L` | 3L | `land-row-3` | `page-2-pair-land` · `page-3-port`（对偶） | `screen-landscape-3`（上下 stack，不是同一张） | sketch |
| `page-3-port-hero-left` | 左大右双小 | `3P` | 3P | `port-hero-l` | **`page-3-port-hero-right`** | 无合格现网顶岗 | sketch |
| `page-3-port-hero-right` | 左双小右大 | `3P` | 3P | `port-hero-r` | **`page-3-port-hero-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-3-2l1p-hero-left` | 左主横右上横下竖 | `2L1P` | 2L1P | `land-hero-l` | **`page-3-2l1p-hero-right`** | 无合格现网顶岗 | sketch |
| `page-3-2l1p-hero-right` | 左上横下竖右主横 | `1P2L` | 1P2L | `land-hero-r` | **`page-3-2l1p-hero-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-3-2l1p-hero-wide-left` | 左主宽横右上宽横下竖 | `2L1P` | 2L1P | `land-hero-l-wide` | **`page-3-2l1p-hero-wide-right`** · `page-3-2l1p-hero-left` | 无合格现网顶岗 | sketch |
| `page-3-2l1p-hero-wide-right` | 左上宽横下竖右主宽横 | `1P2L` | 1P2L | `land-hero-r-wide` | **`page-3-2l1p-hero-wide-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-4-grid-land` | 横版四宫 | `4L` | 4L | `grid-4-land` | `page-2-pair-land` · `page-3-land` | `screen-landscape-4`（偏满幅，不是同一张） | sketch |
| `page-4-1p3l-left` | 左竖右三横 | `1P3L` | 1P3L | `port-stack-3l` | **`page-4-1p3l-right`** · `page-4-1p3l-wide-left`（上宽横，不是同一张） | 无合格现网顶岗 | sketch |
| `page-4-1p3l-right` | 左三横右竖 | `3L1P` | 3L1P | `stack-3l-port` | **`page-4-1p3l-left`**（镜像）· `page-4-1p3l-wide-right`（上宽横，不是同一张） | 无合格现网顶岗 | sketch |
| `page-4-1p3l-wide-right` | 左上宽横下两小横右竖 | `3L1P` | 1P3L | `stack-3l-port-wide` | **`page-4-1p3l-wide-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-4-1p3l-wide-left` | 左竖右上宽横下两小横 | `1P3L` | 1P3L | `port-stack-3l-wide` | **`page-4-1p3l-wide-right`**（镜像） | 无合格现网顶岗 | sketch |
| `page-3-2p1s` | 两竖夹一方 | `2P1S` | 2P1S | `row-2p1s` | `page-3-port` · `page-2-1s1p` | 无合格现网顶岗 | sketch |
| `page-4-2p2l-cross` | 十字两横两竖 | `2P2L` | 2P2L | `cross-2p2l` | `page-4-grid-land` · `page-3-2p1s` | `screen-mosaic-4-2p2l-portrait-bookends`（满高书挡，不是同一张） | sketch |
| `page-4-grid-land-wide` | 宽版横版四宫 | `4L` | 4L | `grid-4-land-wide` | `page-4-grid-land` · `page-1-hero-land-wide` | `screen-landscape-4`（偏满幅，不是同一张） | sketch |
| `page-3-2l1p-wide-left` | 左竖右双宽横 | `1P2L` | 1P2L | `port-stack-l-wide` | **`page-3-2l1p-wide-right`** · `page-3-2l1p-left` | `screen-portrait-1-landscape-2`（不是同一张） | sketch |
| `page-3-2l1p-wide-right` | 左双宽横右竖 | `2L1P` | 2L1P | `stack-l-port-wide` | **`page-3-2l1p-wide-left`**（镜像） | `screen-landscape-2-portrait-1`（不是同一张） | sketch |
| `page-3-1s2l-wide-left` | 左方右双宽横 | `1S2L` | 1S2L | `square-stack-l-wide` | **`page-3-1s2l-wide-right`** · `page-3-1s2l-left` | 无合格现网顶岗 | sketch |
| `page-3-1s2l-wide-right` | 左双宽横右方 | `2L1S` | 2L1S | `stack-l-square-wide` | **`page-3-1s2l-wide-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-4-1l3l-left` | 左主横右三小 | `1L3L` | 1L3L | `land-hero-3l` | **`page-4-1l3l-right`** | `screen-mosaic-4-hero-70-sidebar`（约 70%，不是同一张） | sketch |
| `page-4-1l3l-right` | 左三小右主横 | `3L1L` | 3L1L | `stack-3l-land-hero` | **`page-4-1l3l-left`**（镜像） | `screen-mosaic-4-hero-70-sidebar`（约 70%，不是同一张） | sketch |
| `page-4-1l3l-wide-left` | 左主宽横右三小 | `1L3L` | 1L3L | `land-hero-3l-wide` | **`page-4-1l3l-wide-right`** · `page-4-1l3l-left` | `screen-mosaic-4-hero-70-sidebar`（约 70%，不是同一张） | sketch |
| `page-4-1l3l-wide-right` | 左三小右主宽横 | `3L1L` | 3L1L | `stack-3l-land-hero-wide` | **`page-4-1l3l-wide-left`**（镜像） | `screen-mosaic-4-hero-70-sidebar`（约 70%，不是同一张） | sketch |
| `page-4-port` | 四竖并排 | `4P` | 4P | `row-port-4` | `page-3-port` · `page-2-pair-port` | `screen-portrait-4`（9:16 四竖 2×2，不是同一张） | sketch |
| `page-4-2p2p` | 两大夹两小竖 | `2P2P` | 4P | `port-bookend-2p` | `page-5-1p4p-left`（同尺寸）· `page-4-port` | 无合格现网顶岗 | sketch |
| `page-5-1p4l-left` | 左竖右四横 | `1P4L` | 1P4L | `port-grid-4l` | **`page-5-1p4l-right`** · `page-5-1p4l-center` | `screen-mosaic-5-1p4l-portrait-hero`（满高+四轨，不是同一张） | sketch |
| `page-5-1p4l-right` | 左四横右竖 | `4L1P` | 4L1P | `grid-4l-port` | **`page-5-1p4l-left`**（镜像）· `page-5-1p4l-center` | `screen-mosaic-5-1p4l-portrait-hero`（满高+四轨，不是同一张） | sketch |
| `page-5-1p4l-center` | 中竖左右各两横 | `2L1P2L` | 1P4L | `port-center-4l` | **`page-5-1p4l-left`** · **`page-5-1p4l-right`** | `screen-mosaic-5-1p4l-portrait-hero`（满高+四轨，不是同一张） | sketch |
| `page-5-1p4p-left` | 左大竖右四小竖 | `1P4P` | 5P | `port-grid-4p` | **`page-5-1p4p-right`** · `page-5-1p4p-center` · `page-5-1p4l-left`（右四横） | 无合格现网顶岗 | sketch |
| `page-5-1p4p-right` | 左四小竖右大竖 | `4P1P` | 5P | `grid-4p-port` | **`page-5-1p4p-left`**（镜像）· `page-5-1p4p-center` | 无合格现网顶岗 | sketch |
| `page-5-1p4p-center` | 中大竖左右各两小竖 | `2P1P2P` | 5P | `port-center-4p` | **`page-5-1p4p-left`** · **`page-5-1p4p-right`** | 无合格现网顶岗 | sketch |
| `page-7-1p6l-left` | 左竖右六横 | `1P6L` | 1P6L | `port-grid-6l` | **`page-7-1p6l-right`** · `page-7-1p6l-center` | 无合格现网顶岗 | sketch |
| `page-7-1p6l-right` | 左六横右竖 | `6L1P` | 6L1P | `grid-6l-port` | **`page-7-1p6l-left`**（镜像）· `page-7-1p6l-center` | 无合格现网顶岗 | sketch |
| `page-7-1p6l-center` | 中竖左右各三横 | `3L1P3L` | 1P6L | `port-center-6l` | **`page-7-1p6l-left`** · **`page-7-1p6l-right`** | 无合格现网顶岗 | sketch |
| `page-5-3p2l-left` | 左大竖右交错 | `3P2L` | 3P2L | `port-stagger-2col` | **`page-5-3p2l-right`** | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-right` | 左交错右大竖 | `2L3P` | 2L3P | `stagger-2col-port` | **`page-5-3p2l-left`**（镜像） | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-stack-left` | 左大竖右上二竖下二横 | `3P2L` | 3P2L | `port-stack-2p2l` | **`page-5-3p2l-stack-right`** · `page-5-3p2l-stack-center` · `page-5-3p2l-left` | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-stack-right` | 左上二竖下二横右大竖 | `2L3P` | 2L3P | `stack-2p2l-port` | **`page-5-3p2l-stack-left`**（镜像）· `page-5-3p2l-stack-center` | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-stack-center` | 中大竖左右上竖下横 | `3P2L` | 3P2L | `port-center-stack-2p2l` | **`page-5-3p2l-stack-left`** · **`page-5-3p2l-stack-right`** | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-center` | 中大竖左上竖右上横 | `3P2L` | 3P2L | `port-center-stagger` | **`page-5-3p2l-center-flip`** · `page-5-3p2l-left` · `page-5-3p2l-stack-center`（同构，不是同一张） | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-center-flip` | 中大竖左上横右上竖 | `2L3P` | 2L3P | `port-center-stagger-flip` | **`page-5-3p2l-center`**（镜像） | `screen-mosaic-5-2p3l-portrait-hero-rail`（不是同一张） | sketch |
| `page-5-3p2l-wide` | 上三竖下两宽横 | `3P2L` | 3P2L | `row-3p-pair-l-wide` | 左右对称，无镜像 · `page-3-port`（单行） | 无合格现网顶岗 | sketch |
| `page-9-grid-land-wide` | 宽幅九宫格 | `9L` | 9L | `grid-9-land-wide` | `page-4-grid-land-wide` · `page-3-land` | `screen-landscape-9`（文档已 deprecated，边距未必同） | sketch |
| `page-6-grid-land` | 横版六宫格 | `6L` | 6L | `grid-6-land` | `page-4-grid-land` · `page-3-land` · `page-9-grid-land-wide` | `screen-landscape-6`（3×2 等分，槽比约 1.185，不是同一张） | sketch |
| `page-8-grid-land` | 横版八宫格 | `8L` | 8L | `grid-8-land` | `page-4-grid-land` · `page-6-grid-land` | 无合格现网顶岗 | sketch |
| `page-8-grid-port` | 竖版八宫格 | `8P` | 8P | `grid-8-port` | `page-10-grid-port`（5×2）· `page-4-port` | 无合格现网顶岗（`screen-portrait-grid-8` 是 9:16） | sketch |
| `page-10-grid-port` | 竖版十宫格 | `10P` | 10P | `grid-10-port` | `page-8-grid-port`（4×2）· `page-4-port` · `page-5-1p4p-left`（同宽小竖） | 无合格现网顶岗 | sketch |
| `page-8-2l6p` | 上横三竖下三竖横 | `2L6P` | 2L6P | `diag-2l6p` | **`page-8-2l6p-flip`**（垂直镜像） | 无合格现网顶岗 | sketch |
| `page-8-2l6p-flip` | 上三竖横下横三竖 | `2L6P` | 2L6P | `diag-2l6p-flip` | **`page-8-2l6p`**（垂直镜像） | 无合格现网顶岗 | sketch |
| `page-6-2l4p-left` | 左两横右四竖 | `2L4P` | 2L4P | `stack-2l-grid-4p` | **`page-6-2l4p-right`** · `page-6-2l4p-wide`（16:9 对角，不是同一张） | 无合格现网顶岗 | sketch |
| `page-6-2l4p-right` | 左四竖右两横 | `4P2L` | 4P2L | `grid-4p-stack-2l` | **`page-6-2l4p-left`**（镜像） | 无合格现网顶岗 | sketch |
| `page-6-2l4p-wide` | 上两竖一宽横下一宽横两竖 | `2P1L` | 2L4P | `diag-2l4p-wide` | **`page-6-2l4p-wide-flip`**（镜像） | 无合格现网顶岗 | sketch |
| `page-6-2l4p-wide-flip` | 上一宽横两竖下两竖一宽横 | `1L2P` | 2L4P | `diag-2l4p-wide-flip` | **`page-6-2l4p-wide`**（镜像） | 无合格现网顶岗 | sketch |
| `page-6-4l2p` | 四横夹两竖 | `4L2P` | 4L2P | `bookend-4l-2p` | `page-6-2l4p-left`（同尺寸） | 无合格现网顶岗 | sketch |
| `page-6-1l5l-wide-left` | 左主宽横右下五小 | `1L5L` | 1L5L | `land-hero-5l-wide` | **`page-6-1l5l-wide-right`** · `page-4-1l3l-wide-left` | 无合格现网顶岗 | sketch |
| `page-6-1l5l-wide-right` | 左下五小右主宽横 | `5L1L` | 5L1L | `stack-5l-land-hero-wide` | **`page-6-1l5l-wide-left`**（镜像） | 无合格现网顶岗 | sketch |

---

## 修订

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.1.0 | 2026-08-16 | 建库；收第一张 `page-1-hero-land-right`。 |
| 0.2.0 | 2026-08-16 | 收第二张 `page-1-hero-land-wide`（16:9 槽居中）。 |
| 0.3.0 | 2026-08-16 | 收第三张 `page-1-hero-square`（1:1 方槽居中；不当横槽）。 |
| 0.3.1 | 2026-08-16 | 方槽改右齐；id 更名为 `page-1-hero-square-right`。 |
| 0.4.0 | 2026-08-16 | 收第四张 `page-1-hero-land-ultra`（21:9 顶齐）。 |
| 0.5.0 | 2026-08-16 | 收第五张 `page-1-hero-port`（3:4 竖槽居中；用途栏「横版」已更正）。 |
| 0.6.0 | 2026-08-16 | 收第六张 `page-2-pair-port`（双竖 3:4 均分；与附录 A 同 id、边距不同）。 |
| 0.7.0 | 2026-08-16 | 收第七张 `page-2-1p1l`（左竖 3:4 + 右横 4:3 顶齐）。 |
| 0.7.1 | 2026-08-16 | 收镜像兄弟 `page-2-1l1p`（左横右竖；无独立示意图）。 |
| 0.8.0 | 2026-08-16 | 收第九张 `page-2-pair-land`（双横 4:3 并排顶齐；用途栏「竖版」已更正）。 |
| 0.9.0 | 2026-08-16 | 收第十张 `page-2-pair-land-ultra`（双超宽上下均分；槽比 64:17，不是 21:9）。 |
| 0.10.0 | 2026-08-16 | 收第十一张 `page-3-port`（三竖 3:4 三等分居中；与附录 A 同 id、边距不同）。 |
| 0.11.0 | 2026-08-16 | 收 `page-3-2l1p-left`（示意图）+ 镜像兄弟 `page-3-2l1p-right`。 |
| 0.12.0 | 2026-08-16 | 收第十四张 `page-2-pair-square`（双方槽 1:1 并排；优先方图，4:3/3:4 可进）。 |
| 0.13.0 | 2026-08-16 | 收 `page-3-1s2l-left`（图上 1 方 + 2 横；表头槽数已更正）+ 镜像 `page-3-1s2l-right`。 |
| 0.14.0 | 2026-08-16 | 收 `page-2-1s1p`（左方 1:1 半宽 + 右竖 3:4）+ 镜像 `page-2-1p1s`。 |
| 0.15.0 | 2026-08-16 | 收 `page-2-1l1p-wide`（左宽 16:9 + 右竖 3:4）+ 镜像 `page-2-1p1l-wide`。 |
| 0.16.0 | 2026-08-16 | 收 `page-3-land`（三横 4:3 一行；现网三横是上下叠）。 |
| 0.17.0 | 2026-08-16 | 收 `page-3-port-hero-left`（三竖一大二小）+ 镜像 `page-3-port-hero-right`。 |
| 0.18.0 | 2026-08-16 | 收 `page-3-2l1p-hero-left`（71% 横主 + 右上横下竖）+ 镜像 `page-3-2l1p-hero-right`。 |
| 0.19.0 | 2026-08-16 | 收 `page-4-grid-land`（2×2 四横；用途栏「三张」已按图更正；与附录 A 同 id、边距不同）。 |
| 0.20.0 | 2026-08-16 | 收 `page-4-1p3l-left`（左竖 8/9 + 右上二下一横）+ 镜像 `page-4-1p3l-right`。 |
| 0.21.0 | 2026-08-17 | 收 `page-3-2p1s`（两竖夹一方；表头竖槽数已按图更正）。 |
| 0.22.0 | 2026-08-17 | 建四档星级（0–3）；七张标 ★★★：`pair-port` / `pair-land` / `1l1p-wide` / `page-3-port` / `2l1p-left` / `grid-land` / `2p1s`。 |
| 0.23.0 | 2026-08-17 | 星级改由 `stars.yaml` 权威；微缩页点星后「写入本库」。 |
| 0.24.0 | 2026-08-17 | 收 `page-4-2p2l-cross`（十字 2 竖 5/9 + 中 2 横 5/16；表头「方版」已按图更正；不占附录 A 的 `page-4-2p2l`）。 |
| 0.25.0 | 2026-08-17 | 收 `page-4-grid-land-wide`（2×2 横槽 16:9，单槽宽 7/16；不是 4:3 的 `page-4-grid-land`）。 |
| 0.26.0 | 2026-08-17 | 收宽版 `page-3-2l1p-wide-left` + 镜像 `page-3-2l1p-wide-right`（右/左栏 16:9 叠满高；剩余宽三等分；无独立示意图）。 |
| 0.27.0 | 2026-08-17 | 收宽版 `page-3-1s2l-wide-left` + 镜像 `page-3-1s2l-wide-right`（方槽仍半宽；横槽 16:9 宽 1/3；无独立示意图）。 |
| 0.28.0 | 2026-08-17 | 收 `page-4-1l3l-left`（主 4:3 半宽 + 右三小 22%）+ 镜像 `page-4-1l3l-right`；不占附录 A 的 `page-4-hero-rail`。 |
| 0.29.0 | 2026-08-17 | 收宽版 `page-4-1l3l-wide-left`（主 16:9 半宽 + 右三小 25%）+ 镜像 `page-4-1l3l-wide-right`。 |
| 0.30.0 | 2026-08-17 | 收 `page-4-port`（四竖 3:4 各 25% 顶齐无缝；底通栏文案可空；左右对称无镜像）。 |
| 0.31.0 | 2026-08-17 | 收 `page-5-1p4l-left`（竖 8/9 + 右 2×2 横 25%）+ 镜像 `page-5-1p4l-right`。 |
| 0.32.0 | 2026-08-17 | 收 `page-7-1p6l-left`（竖 8/9 + 右 2×3 宽横 16:9 各 25%）+ 镜像 `page-7-1p6l-right`。 |
| 0.33.0 | 2026-08-17 | 收 `page-5-3p2l-left`（大竖 8/9 + 右两列横竖交错）+ 镜像 `page-5-3p2l-right`；表头「1竖6横」已按图更正。 |
| 0.34.0 | 2026-08-17 | 收 `page-5-3p2l-stack-left`（大竖 + 右两列同构上竖下横）+ 镜像 `page-5-3p2l-stack-right`；与交错版不是同一张。 |
| 0.35.0 | 2026-08-17 | 收 `page-5-3p2l-center`（中大竖 8/9 + 左上竖下横、右上横下竖）+ 镜像 `page-5-3p2l-center-flip`；与靠左/靠右大竖不是同一张。 |
| 0.36.0 | 2026-08-17 | 收 `page-9-grid-land-wide`（3×3 横槽 16:9，单槽高 30%；左右对称无镜像）。 |
| 0.37.0 | 2026-08-17 | 收 `page-6-grid-land`（3×2 横槽 4:3，单槽宽 31%；左右对称无镜像；不是现网等分六宫）。 |
| 0.38.0 | 2026-08-17 | 收 `page-8-grid-land`（4×2 横槽 4:3，单槽宽 25% 贴边无横缝；剩余高三等分；左右对称无镜像）。 |
| 0.39.0 | 2026-08-17 | 收 `page-5-1l4l-wide-left`（主 16:9 高 60% 顶齐左齐 + 右二小、下二小各 30%）+ 镜像 `page-5-1l4l-wide-right`。 |
| 0.39.1 | 2026-08-17 | 更正为 `page-6-1l5l-wide-left`：补右下角第五小，五小靠底靠右；旧 id `page-5-1l4l-wide-*` 作废。 |
| 0.39.2 | 2026-08-17 | 修正 `page-6-1l5l-wide-*` 留白：侧栏三小垂直居中均分；底行三小占满宽；大横顶齐左/右齐。 |
| 0.39.3 | 2026-08-17 | 大横改为 65%：吃尽侧栏顶到的剩余高，底贴底行；右侧 5% 不对齐。 |
| 0.40.0 | 2026-08-17 | 行排加缝：`page-3-port` / `page-3-land` 余宽四等分；`page-2-pair-square` 余宽三等分；`page-3-port-hero-*` 两辅加 5% 中缝；`page-4-port` 槽宽收到 21.875%。 |
| 0.40.1 | 2026-08-17 | `page-8-grid-land` 列间加 1% 最小横缝，左右仍贴边；槽宽 25% → 24.25%。 |
| 0.41.0 | 2026-08-17 | 收 `page-5-1p4p-left`（左主竖 + 右 2×2 小竖 3:4 各 18.75%；余高三等分、余宽四等分）+ 镜像 `page-5-1p4p-right`。 |
| 0.42.0 | 2026-08-17 | 收 `page-4-2p2p`（左右大竖夹中两小；大/小尺寸同 `page-5-1p4p-left`；左右对称无镜像）。 |
| 0.43.0 | 2026-08-17 | 收 `page-10-grid-port`（5×2 竖槽 3:4 各宽 18.75%；余宽六等分、余高三等分；左右对称无镜像）。 |
| 0.44.0 | 2026-08-17 | 收 `page-8-2l6p`（上横 1/3 + 三竖；下三竖 + 横；竖 18.75% / 横 1/3 等高 4/9）+ **垂直镜像** `page-8-2l6p-flip`。 |
| 0.45.0 | 2026-08-17 | 收 `page-6-2l4p-left`（左两横 1/3 叠 + 右 2×2 竖 18.75%；两行等高 4/9）+ 镜像 `page-6-2l4p-right`。 |
| 0.46.0 | 2026-08-17 | 收 `page-6-4l2p`（左右各两横 1/3 叠，中两竖 18.75%；同尺寸只改位置；左右对称无镜像）。 |
| 0.47.0 | 2026-08-17 | 收 `page-3-2l1p-hero-wide-left`（两横改 16:9；右栏宽仍 25%、主宽仍 71%；顶齐，余高三等分）+ 镜像 `page-3-2l1p-hero-wide-right`。 |
| 0.47.1 | 2026-08-17 | `page-3-2l1p-hero-wide-*` 主图改为相对整页上下居中；辅栏仍余高三等分。 |
| 0.48.0 | 2026-08-18 | 缝令牌试验（仅 `page-3-port`）：槽宽仍 30%；列缝 2.5% → 1.5%；余宽归左右纸边各 3.5%。 |
| 0.48.1 | 2026-08-18 | 缝令牌试验扩到 `page-6-grid-land`：槽宽仍 31%；列缝 1.75% → 1.5%；行缝改为等价页高（不再三等分余高）。 |
| 0.48.2 | 2026-08-18 | 缝令牌试验扩到 `page-4-grid-land-wide`：槽宽仍 7/16；列/行缝从 1/24 收到令牌，剩余归纸边。 |
| 0.48.3 | 2026-08-18 | 缝令牌试验扩到 `page-5-3p2l-center` + 镜像：只收列缝 3.125% → 1.5%；中竖不动；列内竖缝不改。 |
| 0.48.4 | 2026-08-18 | `page-6-1l5l-wide-*`：侧栏三格（含底行共用格）整体平移，中缝 5% → 1/60；大横与底行另外两格不动。 |
| 0.48.5 | 2026-08-18 | `page-3-2l1p-hero-*`：辅栏整体平移，列缝 4% → 4%/3；主图尺寸与两列等高不动。 |
| 0.48.6 | 2026-08-18 | `page-2-1p1l-wide` + 镜像：竖槽整体靠向主图，列缝 5% → 1/60；宽横 60% 不动。 |
| 0.49.0 | 2026-08-18 | 缝令牌续：均分行/宫格只收缝（`page-3-land` / `page-4-port` / `page-2-pair-square` / `page-2-pair-port` / `page-4-grid-land` 行列令牌 / `page-9-grid-land-wide` 只收列缝）；同构三列族（`page-5-3p2l-*` / `page-5-1p4l-*` / `page-7-1p6l-*` / `page-5-1p4p-*` / `page-6-2l4p-*` / `page-6-4l2p`）只收列缝；`page-3-2l1p-hero-wide-*` 辅栏平移，中缝收成 1/3。拿不准的不动。 |
| 0.49.1 | 2026-08-18 | `page-8-2l6p` + 垂直镜像 `page-8-2l6p-flip`：每行三道竖缝 1/48 → 1.5%；槽宽不动；余宽归左右纸边。 |
| 0.50.0 | 2026-08-20 | 收 `page-7-1p6l-center`：竖槽居中，左右各 1×3 宽横；槽尺寸与列缝令牌同 `page-7-1p6l-right`。 |
| 0.50.1 | 2026-08-20 | 收 `page-5-1p4l-center`：竖槽居中，左右各 1×2 横 4:3；槽尺寸与列缝令牌同 `page-5-1p4l-right`。 |
| 0.50.2 | 2026-08-20 | 收 `page-5-1p4p-center`（中大竖 + 左右各两小竖；五槽皆竖）+ `page-5-3p2l-stack-center`（中大竖 + 左右同构上竖下横）。槽尺寸与列缝令牌分别同 `page-5-1p4p-right` / `page-5-3p2l-stack-right`。不是交错的 `page-5-3p2l-center`。 |
| 0.50.3 | 2026-08-20 | 收 `page-8-grid-port`：4×2 竖槽 3:4 各宽 18.75%；列缝/行缝令牌各 1.5%；整组居中。不是 `page-8-grid-land`，也不是现网 9:16 的 `screen-portrait-grid-8`。 |
| 0.50.4 | 2026-08-20 | 收 `page-6-2l4p-wide`（上两竖 + 右 16:9 宽横顶齐；下左宽横 + 两竖底齐；横宽 40.625%）+ 左右镜像 `page-6-2l4p-wide-flip`。不是 4:3 叠侧的 `page-6-2l4p-left`。 |
| 0.50.5 | 2026-08-20 | 收 `page-4-1p3l-wide-right`（右竖 8/9 + 左上 16:9 宽 53.75% + 左下两横 4:3 各 25%；列缝 1.5%）+ 左右镜像 `page-4-1p3l-wide-left`。不是 4:3 上二下一的 `page-4-1p3l-*`。 |
| 0.50.6 | 2026-08-20 | 收 `page-5-3p2l-wide`：上三竖 3:4 各 22%（外沿与下两横齐、中间均分）+ 下两宽横 16:9 各 37.5%（中缝 1.5% 居中）。左右对称。不是大竖三列的 `page-5-3p2l-*`。 |
| 0.50.7 | 2026-08-20 | 星级重标定：按桌上新表覆盖 `stars.yaml`；未列出仍为 0，镜像不自动继承。 |
| 0.50.8 | 2026-08-24 | 星级旁加禁用：`stars.yaml` 的 `disabled:` 名单；试印 / 成册库存 / 升格共用 `stars.js`，禁用后面都不进。 |
| 0.50.9 | 2026-08-25 | `page-1-hero-land-right`：槽 67.5%×90% 不变，左右居中（左 16.25%），取消文案栏。id 仍叫 `-right`。 |
| 0.50.10 | 2026-08-25 | `page-2-pair-land`：两槽 42.5%×56.666667% 与左右位置不变，上下居中（顶 21.666667%），取消下文案栏。 |
| 0.50.11 | 2026-08-25 | `page-4-port`：四槽 21.875%×51.851852% 与左右位置不变，上下居中（顶 24.074074%），取消下文案栏。 |
| 0.50.12 | 2026-08-25 | 星级重标定：按桌上新表覆盖 `stars.yaml`；禁用 `page-4-2p2p` · `page-6-4l2p`；未列出仍为 0。 |
| 0.50.13 | 2026-08-25 | 成册重编：覆盖 `folio-8/12/16/20/24-standard` 与 `folio-28/32-standard-r2`、`folio-36-standard`；金样种子同步。 |
