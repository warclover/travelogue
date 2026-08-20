# Web 端游记拼图模板清单

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-14 |
| **范围** | Web 游记预览屏（16:9 `index.html`），不含导出画册 `card-*` |
| **权威源** | `travelogue/layout_templates/templates/*.yaml`（LTE） |
| **渲染** | `journal-screens.css` |
| **几何说明** | [slot-aspect/](./slot-aspect/)（与 YAML 一一对应） |
| **统一窗政策** | `travelogue/layout_templates/lte_policy.yaml` → `MOSAIC_*_PATTERN_IDS` |
| **实验门** | `config.yaml` → `mosaic.template_experiments` |

仓库里一共 **47** 份屏模板（不含 `_example`）。真正会进新 trip 候选的，远少于这个数。下面按**会不会被现网选中**来列。槽标见图：[tsu-screen-template-glyphs-v1.html](../wireframes/tsu-screen-template-glyphs-v1.html)（红竖 / 蓝横）。

---

## 怎么进候选

| 门槛 | 含义 |
|------|------|
| **现网统一窗** | 写在 `lte_policy.yaml` 的 `MOSAIC_*_PATTERN_IDS`，新 trip 默认会评 |
| **实验白名单** | `config.yaml` → `mosaic.template_experiments`：开关开 + 在 allowlist + trip 在 cohort |
| **退役** | `status: deprecated` 或生命周期硬拒；新 trip 不选，旧 `screens[]` 仍能渲染 |

这和导出画册的 `card-*` 模板是两套库，本文只列 **Web 游记屏**。`mix` 写「竖 + 横」配比（P = portrait，L = landscape）。

---

## 一、现网统一候选（11）

这 11 个是拼图选型（MCS）默认会评的。

| ID | 显示名 | 张数 | 配比 | 版式一句话 | 权重 |
|---|---|---|---|---|---|
| `screen-portrait-3` | portrait · 3 | 3 | 3P | 9:16 舞台，三竖横排等分 | 1.00 |
| `screen-landscape-3` | landscape · 3 | 3 | 3L | 三横上下 stack，消化横图连拍 | 1.00 |
| `screen-portrait-1-landscape-2` | portrait · 1 · landscape · 2 | 3 | 1P2L | 左满高竖 + 右上下两横 | 1.00 |
| `screen-portrait-2-landscape-2` | portrait · 2 · landscape · 2 | 4 | 2P2L | 16:9 等分 2×2，无 hero | 1.00 |
| `screen-portrait-4` | portrait · 4 | 4 | 4P | 9:16 舞台，四竖 2×2 | 1.00 |
| `screen-landscape-4` | landscape · 4 | 4 | 4L | 16:9 四横 2×2 等权 | 1.12 |
| `screen-mosaic-4-hero-70-sidebar` | 四图 · 七成英雄 + 侧栏三格 | 4 | 4L | 左约 70% 满高主图 + 右三格 | 0.98 |
| `screen-mosaic-5-main-portrait-3land` | mosaic · 5 · main · portrait · 3land | 5 | 1P4L | 主横 2×2 + 右满高竖 + 底三横 | 1.00 |
| `screen-mosaic-5-hero-3-2-plus-4` | 五图 · 加权轨道 hero + 四配图 | 5 | 5L | 左列满高偏竖主槽 + 右 2×2；主槽其实是竖形窗 | 0.98 |
| `screen-mosaic-5-main-hero-plus-4` | mosaic · 5 · main · hero · plus · 4 | **6** | 6L | 主横 2×2 + 右列双图 + 底行三图（几何孪生） | 1.00 |
| `screen-mosaic-6-main-hero-plus-5` | mosaic · 6 · main · hero · plus · 5 | 6 | 6L | 与上一行同拓扑，六图 hero 家族正名 | 1.00 |

`screen-mosaic-5-main-hero-plus-4` 名字带 5，实际是 **6 槽**，和 `screen-mosaic-6-main-hero-plus-5` 是同一家族。

---

## 二、实验白名单（11，本机 `config.yaml` 已开）

要同时满足：`template_experiments.enabled`、ID 在 allowlist、trip 在 `cohort_trip_ids`（空 cohort = 谁都不进）。

| ID | 张数 | 配比 | 版式一句话 |
|---|---|---|---|
| `screen-portrait-2-gallery` | 2 | 2P | 双竖等大居中，四周留白 |
| `screen-portrait-2-asymmetric-left` | 2 | 2P | 双竖左主右辅 |
| `screen-portrait-2-asymmetric-right` | 2 | 2P | 双竖右主左辅 |
| `screen-landscape-1-portrait-1` | 2 | 1L1P | 左横右竖，两槽等高 |
| `screen-portrait-1-landscape-1` | 2 | 1P1L | 左竖右横（上一行的镜像） |
| `screen-landscape-2-asymmetric-left` | 2 | 2L | 双横左大右小 |
| `screen-landscape-2-portrait-1` | 3 | 2L1P | 左两横叠 + 右竖满高 |
| `screen-landscape-3-asymmetric-left` | 3 | 3L | 左大满高 + 右两小叠 |
| `screen-landscape-3-asymmetric-right` | 3 | 3L | 左两小叠 + 右大满高 |
| `screen-mosaic-5-3p2l-portrait-hero-quad` | 5 | 3P2L | 左满高竖主 + 右上双竖 + 右下双横 |
| `screen-mosaic-5-3p2l-portrait-hero-lp-stack` | 5 | 3P2L | 左满高竖主 + 右（横\|竖）×2 成对 |

---

## 三、仓库里有、默认不进新 trip（7）

YAML 是 `experimental`，但没进本机 allowlist，所以默认不会被选。

| ID | 张数 | 配比 | 版式一句话 |
|---|---|---|---|
| `screen-mosaic-4-1l3p-rail` | 4 | 1L3P | 左满高横主 + 右三竖叠轨 |
| `screen-mosaic-4-2l2p-weighted` | 4 | 2L2P | 等分 2×2 棋盘，Z 字横竖交错 |
| `screen-mosaic-4-2p2l-portrait-bookends` | 4 | 2P2L | 左右满高竖书挡 + 中列上下双横 |
| `screen-mosaic-5-1p4l-portrait-hero` | 5 | 1P4L | 左满高竖主 + 右四横轨 |
| `screen-mosaic-5-1p4l-portrait-center-rails` | 5 | 1P4L | 中列满高竖 + 左右各上下双横 |
| `screen-mosaic-5-2p3l-portrait-hero-rail` | 5 | 2P3L | 左竖主 + 中辅竖 + 右三横 |
| `screen-mosaic-5-2p3l-rail` | 5 | 2P3L | 双竖满高 + 右三横（复活已退役拓扑，不转 GA） |

---

## 四、退役 / 仅历史渲染（12）

新 trip 不选；旧游记里已经写下的 `patternId` 仍能画出。

| ID | 张数 | 说明 |
|---|---|---|
| `screen-mosaic-5-2p3l-equal` | 5 | 双竖满高 + 右三横；密度过高、缺主次 |
| `screen-mosaic-5-2portrait-3land-balanced` | 5 | 命名与 mix 不符（id 写 2P，实际 3P2L） |
| `screen-mosaic-5-3portrait-2land-balanced` | 5 | 上三竖 + 底两横 |
| `screen-mosaic-5-main-landscape-2portrait-2land` | 5 | `main-portrait-3land` 的无守卫前身 |
| `screen-landscape-2-overlap-bltr` | 2 | 对角叠压（左下/右上） |
| `screen-landscape-2-overlap-tlbr` | 2 | 对角叠压（左上/右下） |
| `screen-editorial-4mix` | 4 | 棋盘 2L2P，PARKED（role/AR 矛盾） |
| `screen-landscape-6` | 6 | 3×2 等分；YAML 仍是 experimental，生命周期默认硬拒（EGA 等权六图旗可例外放回） |
| `screen-portrait-6` | 6 | 9:16 六竖 3×2 |
| `screen-portrait-9` | 9 | 9:16 九竖 3×3 |
| `screen-landscape-9` | 9 | 16:9 九横 3×3 |
| `screen-portrait-grid-8` | 8 | 9:16 八竖 4×2 |

---

## 五、同属 Web 游记屏、但不是拼图窗（6）

这些是 GA/beta 单图或双竖/杂志三竖，走普通 screen planner，**不进** `MOSAIC_*` 统一拼图窗。

| ID | 状态 | 张数 | 用途 |
|---|---|---|---|
| `screen-landscape-1` | ga | 1 | 单横满屏 cover，章首/全景默认 |
| `screen-portrait-1` | ga | 1 | 单竖满屏（9:16） |
| `screen-full-frame` | ga | 1 | 全幅 contain + 模糊补边，特殊比例 |
| `screen-portrait-2` | ga | 2 | 双竖等分并排 |
| `screen-landscape-2` | ga | 2 | 双横上下 stack |
| `screen-portrait-3-editorial` | beta | 3 | 杂志三竖并列；planner hook，未进统一窗 |

---

## 盘点

| 类别 | 份数 |
|------|------|
| 现网统一拼图候选 | 11 |
| 实验白名单（本机 cohort 可见） | 11 |
| 实验未进白名单 | 7 |
| 退役 / 仅历史渲染 | 12 |
| 单图 / 非拼图窗 | 6 |
| **YAML 合计** | **47** |
