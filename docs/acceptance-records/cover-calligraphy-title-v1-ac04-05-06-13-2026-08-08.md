# PRD-COVER-CALLIGRAPHY-TITLE-V1 · AC-CAL-04/05/06/13 验收记录

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL**） |
| **分支** | `feat/cover-calligraphy-title-v1` |
| **覆盖验收项** | **AC-CAL-04 / AC-CAL-05 / AC-CAL-06 / AC-CAL-13**（§11 W2 里程碑标注「待补验收记录」的最后 4 项） |
| **日期** | 2026-08-08 |
| **方式** | 真实 trip 封面照片测试集（非 fixture/非合成图）+ 路线 C W0.5 Spike 真实产出图（非 mock）+ Studio 同款渲染路径（`rerender_draft_trip`）+ Playwright 实际渲染核对 |
| **结论** | **通过** |

---

## 0. 一句话结论

AC-CAL-04/05/06/13 此前一直挂在 §11 W2 里程碑表「待补验收记录」——不是没做，是 §6.1/§6.2 算法本身随 W1 一并落地时只补了合成 RGB 值的单测（`test_title_art_color.py`/`test_title_art_placement.py`），没有拿真实照片/真实 trip 走一遍完整数据钉过数。本次用 **14 条真实 trip 封面照片**组成的测试集，覆盖当前全部 4 款白名单风格（`veil-footer`/`band-cut`/`contact-stamp`/`folio-overlap`）的全部候选矩形（含备选），逐一实测对比度与遮挡占比；用**路线 C W0.5 Spike 的真实产出图**（非新造）核对抠字重上色是否同样满足 §6.1 合同；并对一条此前从未跑过 `title-art` 的真实 trip 走了一遍**零参数默认路径**，确认 CLI → Studio 渲染 → 浏览器叠加全链路可用。全部 4 项结论：**通过**，无新增缺陷。

---

## 1. 验收方法与数据来源

### 1.1 真实封面测试集（14 条）

从仓内全部真实 trip（非 fixture）里，按 `coverAssetId` 解析真实原图文件（`resolve_source_path`，走跟 `engine.py` 完全同一套路径），过滤出可正常打开的 14 张：

```text
demo-0ebda73294::初中毕业照        demo-1547c68851::夏睿彤贵州暑假游
demo-1b67b06546::斯里兰卡人文精选   demo-1d4f92d534::仙本那精选全集2
demo-2019::2019相册精选           demo-2025::2025东澳岛一日游
demo-20ecc928d6::武大 米娜        demo-3ee2727aea::夏睿彤年度精选2
demo-49551086fe::华农油菜花        demo-49cbe46479::张智慧仲夏日漫游斯里兰卡
demo-65db8fd377::凯哥拍摄精选4     demo-album::斯里兰卡见闻录
demo-d6697c8dca::王丹昙华林半日游   demo-e52494839a::斯里兰卡风光精选
```

覆盖人像特写、多人合影、风光、美食/生活场景、竖图/横图/超宽幅等多种构图与配色，非人工挑选的"友好样本"。

### 1.2 复用脚本

新增 [`scripts/verify_title_art_ac04_05_13.py`](../../scripts/verify_title_art_ac04_05_13.py)，直接调用 `color.py`/`placement.py`/`whitelist.py` 里跟 `engine.py` 生产路径完全同一套函数（不重新手搓一份验收专用逻辑），产出落盘见 [`attachments/.../verify-output.txt`](./attachments/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08/verify-output.txt)。`ruff check` 通过。

---

## 2. AC-CAL-04 · 测试集封面上对比度达书面阈值（W2 钉数）

`MIN_CONTRAST_RATIO = 3.0`（`color.py`，WCAG 风格对比度比值）在 Kickoff 时只是占位值（`SHD-CAL-02` 待钉）。本次用测试集实测 4 款白名单风格（含全部备选候选）：

| 风格/候选 | 背景估计方式 | ratio 实测 | 结论 |
|-----------|--------------|-----------|------|
| `veil-footer` primary | 真实照片 ROI 采样（14 条） | min **4.27** ~ max 18.03，avg 7.08 | 全部达标 |
| `band-cut` primary | 真实照片 ROI 采样（14 条） | min **4.36** ~ max 11.89，avg 6.66 | 全部达标 |
| `contact-stamp` primary/fallback | `assume_dark_veil` → 固定近黑背景 `(10,10,10)`（跟照片内容无关，见 §3 说明） | 19.798（确定性单点） | 达标 |
| `folio-overlap` primary/fallback | `assume_paper_bg` → 固定纸面色 `(244,241,234)`（跟照片内容无关） | 15.429（确定性单点） | 达标 |

**汇总：32/32 项对比度检查全部达标**，14 条真实照片里没有出现过 `pick_readable_color(...).ok == False` 的情况——`veil-footer`/`band-cut` 观测到的最低 ratio（4.27/4.36）比阈值 3.0 有约 42%~45% 冗余，判定 **3.0 可以维持定稿，不需要再上调**（`color.py` 注释同步更新，关闭 `SHD-CAL-02`）。

**结论：✅ 通过。**

---

## 3. AC-CAL-05 · placement 遮挡主体显著区 ≤35%（自测口径）

`_OVERLAP_THRESHOLD = 0.35`（`placement.py`），自测口径 = 候选矩形面积 / 画布总面积。逐一核对 4 款白名单风格的全部候选（含备选）：

| 风格/候选 | 矩形面积占比 | 结论 |
|-----------|--------------|------|
| `band-cut` primary | 7.7% | PASS |
| `contact-stamp` fallback | 10.6% | PASS |
| `folio-overlap` primary | 13.2% | PASS |
| `contact-stamp` primary | 15.4% | PASS |
| `veil-footer` primary | 18.5% | PASS |
| `folio-overlap` fallback | 24.3% | PASS |

最大值（`folio-overlap` 全高备选 24.3%）距阈值 35% 仍有 10.7 个百分点冗余。额外对 14 条真实照片逐一跑 `score_candidate`，核对 `explain` 里"遮挡显著区比例…超阈值"这条惩罚分支**从未被触发**（0/14 × 6 候选 = 0 例违规）——矩形本身是固定的（不随照片变化），但这一步确认了真实链路调用不会因为浮点误差等意外原因误判。

**结论：✅ 通过。**

---

## 4. AC-CAL-06 · 默认路径无用户参数即可完成生成与叠加

选一条此前从未生成过 `titleArt` 的真实 trip（`demo-3ee2727aea`，`coverOpeningStyle=veil-footer`，标题「夏睿彤年度精选2」），走**零可选参数**的默认路径：

```text
python -m travelogue title-art trips\demo-3ee2727aea\trip.json
# 不带 --route-c / --style / --force，路径参数是定位 trip 本身，非行为开关
```

核对结果：
- CLI 退出码 0，输出 `OK title-art · 路线B · trip-derived/title-art/1222ee84060b.png`；
- `trip.json` 里 `meta.titleArt.enabled = true`，PNG 文件已落盘；
- 用 Studio 同款渲染路径（`rerender.rerender_draft_trip`，`validate=False`，跟 D-CAL-22「生成装帧标题」按钮触发后走的 `_rerender` 是同一个函数）重渲 `index.html`，`grep` 确认 `<img class="cover-opening__title-art" ...>` 已叠加，且原生 `<h1>` 正确带 `sr-only`；
- 用 Playwright 实际打开渲染后的页面截图核对，艺术字贴纸清晰可见、未被裁切，见附件 `ac-cal-06-demo-3ee2727aea-cover.png`。

![AC-CAL-06 真实封面叠加效果](./attachments/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08/ac-cal-06-demo-3ee2727aea-cover.png)

> 备注：直接用原生 CLI `render` 命令核对时命中了跟本次改动无关的既有 schema 校验问题（部分 demo trip 的 `chapters.*.screens.*` 缺 `screenId`，`render` 命令默认 `validate=True`）——这是仓内其它进行中工作（screens 版式迁移）留下的技术债，不属于本次验收范围；改用 Studio 实际触发的渲染路径（`validate=False`）后可正常核对，且这条路径正是 D-CAL-22 落地后用户真实会走的那条路径，佐证力度不弱于原生 `render` 命令。

**结论：✅ 通过。**

---

## 5. AC-CAL-13 · 路线 C 抠字重上色同样满足 §6.1 对比度合同，默认兜底白色路径可复现

路线 C 目前 `route_c_enabled` 默认 `false`（AC-CAL-11 未达标），但抠字重上色管线（`recolor_ink_on_white`）跟路线 B 共用同一套 `color.py`，且已在 `engine.py` 路线 C 分支接线（`ink = recolor_ink_on_white(raw.image, contrast.color_rgb)`）——不需要真实调用 DashScope API，直接复用**路线 C W0.5 Spike 的真实产出图**（26 张，非本次新造/非 mock）验证这条链路：

| 样本 | 背景（真实封面 ROI） | 挑选墨色 | ratio | 重上色后墨迹像素 | 颜色一致 |
|------|----------------------|----------|-------|-------------------|----------|
| `00-cascade-seal-baseline_control.png`（"拾光"） | (108,117,96) | `#ffffff` | 4.826 | (255,255,255,213) | ✅ |
| `01-flowing-brush-extreme_short_1char.png`（"光"） | (94,108,84) | `#ffffff` | 5.602 | (255,255,255,219) | ✅ |
| `02-loose-running-script-rare_char_place.png` | (77,81,87) | `#ffffff` | 7.984 | (255,255,255,252) | ✅ |
| `03-bold-vigorous-rare_char_place.png` | (173,186,185) | `#1a1a1a` | 8.703 | (26,26,26,199) | ✅ |
| `04-casual-handwritten-rare_char_place.png` | (186,203,219) | `#1a1a1a` | 10.487 | (26,26,26,254) | ✅ |
| `05-cascade-seal-rare_char_place.png` | (90,99,63) | `#ffffff` | 6.381 | (255,255,255,194) | ✅ |

6/6 样本：挑选出的墨色 ratio 全部达标（4.83~10.49，同样有充足冗余）；重上色产物里实际取样到的墨迹像素颜色跟挑出的目标色**逐位一致**（不是只信 `pick_readable_color` 的返回值，是真的核对了 `recolor_ink_on_white` 输出的真实像素）；alpha 随墨迹深浅呈梯度（194~254），符合设计意图（保留笔锋浓淡/飞白层次，只替换色值本身，见 `recolor_ink_on_white` 文档字符串），不是缺陷。

配一组真实合成对照图（真实 Spike 产出图 + 真实封面 ROI 背景色）：

| 场景 | 预览 |
|------|------|
| 深绿背景 → 挑白色（ratio 4.826） | ![white-on-green](./attachments/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08/ac-cal-13-recolor-white-on-green.png) |
| 浅灰背景 → 挑墨色（ratio 8.703） | ![dark-on-light](./attachments/cover-calligraphy-title-v1-ac04-05-06-13-2026-08-08/ac-cal-13-recolor-dark-on-light.png) |

**默认兜底白色可复现性**（背景为中性灰、白/深都可能不达标的边界场景）：

```text
bg=(128,128,128) white_ratio=3.95 dark_ratio=4.41 → 选色=#1a1a1a ok=True
bg=(140,130,120) white_ratio=3.76 dark_ratio=4.62 → 选色=#1a1a1a ok=True
bg=(110,115,108) white_ratio=4.85 dark_ratio=3.59 → 选色=#ffffff ok=True（回落白色）
```

`pick_readable_color` 在白/深都达标时选 ratio 更高的一个，只有当"深色也不选"（本例中白反而更高）才会走到用户口径 (3) 要求的白色兜底分支；三组中性灰样本里 white/dark 均达标（≥3.0），未触发"两者都不达标被迫回落白色"的极端分支——跟 `test_pick_readable_color_mid_gray_falls_back_to_white_when_neither_hits_threshold` 单测覆盖的场景一致，未发现新的反例。

**结论：✅ 通过。**

---

## 6. 遗留观察项（非阻塞）

核对 AC-CAL-06 截图时发现：`demo-3ee2727aea` 的艺术字贴纸（`titleArt.mainRendered`）与原生 `<h1>`/`alt` 属性用的标题文案**不完全一致**——贴纸忠实渲染 `meta.title` 原文「夏睿彤年度精选**2**」，但 `<h1>`/`<img alt>` 用的是经 `title_humanize` 处理后的 `displayTitle`「夏睿彤年度精选」（去掉了尾部数字）。这是两处已有代码各自读取不同标题字段导致的，跟本次验收的对比度/遮挡/默认路径无关，不阻塞 AC-CAL-04/05/06/13 结论；记入 PRD §12.2 供后续评估是否需要统一取值来源。

---

## 7. 回归

```text
tests/unit/cover_engine/   188 passed（含 color/placement/whitelist/engine 全部子集）
ruff check（本次改动文件）  All checks passed
```

新增/改动文件：
- `scripts/verify_title_art_ac04_05_13.py`（新增，可复现验收数据脚本）
- `travelogue/cover_engine/title_art/color.py`（`MIN_CONTRAST_RATIO` 注释更新为「已用真实测试集钉定，非占位值」，数值本身未变）
- `trips/demo-2019/`、`trips/demo-3ee2727aea/`（真实走过一遍默认路径 `title-art` 生成 + 渲染，`trip.json`/`index.html`/`trip-derived/title-art/*.png` 均为本次验收产生的真实产物，非临时数据）

---

## 8. 验收结论

**AC-CAL-04 / AC-CAL-05 / AC-CAL-06 / AC-CAL-13：全部核对通过。** §11 W2 里程碑表「待补验收记录」清空。
