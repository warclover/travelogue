# 备用库总表

人读索引。机器合同以 [catalog.yaml](./catalog.yaml) 与各夹 `packet.yaml` 为准。微缩见 [gallery.html](./gallery.html)。

| 备用 id | 中文名 | 账徽 | 槽 | 角色 | 同族兄弟 | 意图顶岗 | 状态 |
|---------|--------|------|----|------|----------|----------|------|
| `page-1-hero-land-right` | 单图 · 横版英雄 · 右齐 | `1L` | 1L | `hero-land` | `page-1-hero-land` · `-wide` · `-ultra` | `screen-landscape-1`（满幅，不是同一张） | sketch |
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
| `page-4-grid-land` | 横版四宫 | `4L` | 4L | `grid-4-land` | `page-2-pair-land` · `page-3-land` | `screen-landscape-4`（偏满幅，不是同一张） | sketch |
| `page-4-1p3l-left` | 左竖右三横 | `1P3L` | 1P3L | `port-stack-3l` | **`page-4-1p3l-right`** | 无合格现网顶岗 | sketch |
| `page-4-1p3l-right` | 左三横右竖 | `3L1P` | 3L1P | `stack-3l-port` | **`page-4-1p3l-left`**（镜像） | 无合格现网顶岗 | sketch |

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
