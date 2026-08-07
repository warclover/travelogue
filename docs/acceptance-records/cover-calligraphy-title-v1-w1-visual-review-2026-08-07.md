# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W1 真实素材视觉验收

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL**） |
| **分支** | `feat/cover-calligraphy-title-v1` |
| **覆盖验收项** | **AC-CAL-03 / AC-CAL-07 / AC-CAL-08 / AC-CAL-09 / AC-CAL-12**（§11 里程碑表标注 W1 待补的那五项） |
| **日期** | 2026-08-07 |
| **方式** | 真实 trip（非 fixture）跑通 CLI `title-art` → `render` → Playwright 实际渲染核对 + 代码审查 + 端到端脚本验证 |
| **结论** | **有条件通过——过程中发现 3 处真实实现缺口，均已定位、修复、补测，随本次验收一并提交** |

---

## 0. 一句话结论

原计划只是拿真实素材核对既有实现，**但核对过程中发现 3 个此前 83 条单测未覆盖到的真实集成缺口**（字库资产没随包分发、艺术字贴纸的容器嵌套写错导致跟雾带文案重叠、改标题不会触发 stale）——这些缺口在纯 mock 单测下不可见，只有跑通真实 trip + 真实浏览器渲染才会暴露。三处均已修复并补充回归测试，本记录同时是验收记录和缺陷修复记录。

---

## 1. 发现的问题与修复

### 1.1 【已修复】字库资产未随包分发 → 生产环境静默退化成微软雅黑

- **现象**：`FONT_POOL` 里 `ZhiMangXing-Regular.ttf`（`licensed=True`，生产默认字库）用裸文件名交给 `PIL.ImageFont.truetype()`，只有系统装了这款字体才能解析到；本机验证 `ImageFont.truetype('ZhiMangXing-Regular.ttf', size=40)` 直接抛 `OSError: cannot open resource`。
- **影响**：`load_truetype_named` 的 fallback 链会静默退到 `FALLBACK_STACK[0]`（`msyh.ttc`），**不报错、不告警**——这正是此前 `demo-1547c68851` 生成的 `titleArt.font` 字段写的是 `"msyh.ttc"` 而不是 `"ZhiMangXing-Regular.ttf"` 的原因。产品核心卖点「书法感手写体贴纸」在没装该字体的机器上等于没实现，但看起来一切正常（不报错、图能生成）。
- **根因**：`D-CAL-07` 只核查了「字库授权」，没核查「字库文件在生产环境是否真的可加载」。
- **修复**：
  - 把 `arttext-miniapp/assets/fonts/ZhiMangXing-Regular.ttf` 随包复制到 `travelogue/cover_engine/title_art/assets/fonts/`；`fonts.py` 新增 `resolve_font_source()`，优先加载随包资产，找不到再退回裸文件名（未核查字体沿用原行为，不随包分发）。
  - `glyphs_covered()` 同步经 `resolve_font_source()` 解析——此前它探测的字形覆盖率其实是 `msyh.ttc` 的，跟实际渲染用的字体是两张脸，字形覆盖检查形同虚设。
  - 补 `travelogue/cover_engine/title_art/assets/fonts/LICENSE-NOTES.md`：核实 ZhiMangXing-Regular 为 Google Fonts 收录字体「钟齐志莽行书」，SIL Open Font License 1.1，个人/商用均可免费使用、无需署名（来源：`github.com/google/fonts/ofl/zhimangxing/OFL.txt`）；另两款候选（Aa剑豪体 / 鸿雷板书简体-测试版）保持 `licensed=False`、不随包分发。
- **验证**：修复后重跑 `demo-1547c68851`，`trip.meta.titleArt.font` 变为 `"ZhiMangXing-Regular.ttf"`；隔离渲染 + 深色底合成核对，见附件①。
- **回归**：`tests/unit/cover_engine/test_title_art_fonts.py` 全绿（含新逻辑）；无需改断言（原测试只测「加载不到时 fail-open」，行为不变）。

### 1.2 【已修复】艺术字贴纸嵌套进雾带文案面板 → 与 hook 文案重叠 / 顶穿视口

- **现象**：真实浏览器渲染 `demo-1547c68851` 后，用 `elementFromPoint` 核对贴纸中心点，命中的是 `.cover-opening__hook`（钩子文案段）而不是背景照片——贴纸和文案物理重叠。人工截图复核（用户手测截图）确认标题字被裁切/遮挡。
- **根因**（两层）：
  1. `cover-opening.hbs` 把 `<img class="cover-opening__title-art">` 塞进了 `.cover-opening__panel`（雾带底部文案面板）内部；该面板 `position:relative` 且高度**只由 hook 文案撑起**（trip-meta/subtitle/archive-strip 在 veil-footer 下全是 `display:none` 或 `position:absolute` 脱离文档流）。CSS 里 `top:28%` 是相对这个矮面板算的百分比，跟白名单 rect 「雾带**上方**留白区」的设计语义完全对不上——面板本身贴在底部，`top:28%` 算出来的落点几乎必然撞进面板自身文案里。
  2. §6.2 `placement_score` 算出来的 `position.x`/`position.y` 从来没接进渲染上下文（`assemble.py` 只传了 `hasTitleArt`/`titleArtSrc`/`titleArtAlt`），CSS 用的是写死的 `50%/28%`——「自动定位」这个功能实际上是死代码，从未真正生效。
  3. 连带发现：`render_b.py` 出的是固定 1200×720 工作画布，标题只占其中一小块、下方一大片透明留白；`transform: translate(-50%,-50%)` 是按**整张画布的几何中心**居中，不是按**字形可见区域**居中——即便修好上面两处，字形视觉中心仍会明显偏离锚点（甚至顶出视口顶部，见附件②的中间修复版截图）。
- **修复**：
  - `cover-opening.hbs`：`<img>` 挪到 `.cover-opening__panel` **外面**，作为 `.cover-opening` 的直接子层（`.cover-opening` 本身早已 `position:relative`，覆盖整张封面照片）。
  - `assemble.py`：`_resolve_title_art_src` 新增回传 `titleArt.position.x/y`（0~1 归一化）→ 转成百分比字符串（缺失时回退到 rect 几何中心 `50%/25%`）；`context_types.py` 新增 `titleArtX`/`titleArtY` 字段。
  - `journal.css`：`left/top` 改用 `var(--title-art-x, 50%)`/`var(--title-art-y, 25%)`；同时把单一 `max-width` 改成 `max-width` + `max-height` 双约束（避免某张贴纸因长宽比「矮胖」在居中时顶穿 rect 上边界）。
  - `render_b.py`：新增 `_crop_to_content()`，出稿前按 `Image.getbbox()` 裁到实际墨迹范围（留 6% 呼吸边），让贴纸自身几何中心跟视觉中心重合，`translate(-50%,-50%)` 才能真正对上 §6.2 算出的锚点。
- **验证**：见 §2 三张真实封面截图（不同人像构图/不同长宽比照片），标题均不再与 hook 文案重叠、不再顶出视口，配色对比度正常。
- **回归**：`tests/unit/cover_engine/test_title_art_render_b.py` 更新受影响的 3 个尺寸断言（不再断言 `img.size == CANVAS_SIZE`，改断言裁剪后更小）；新增 `test_render_title_art_content_fills_most_of_cropped_frame` 作为「裁剪后墨迹应几乎填满裁剪结果」的专项回归防线。

### 1.3 【已修复】改 `meta.title` / `coverOpeningStyle` 不会触发 `titleArt.stale`

- **现象**：`engine.py` 里定义了 `mark_title_art_stale()`，但全仓搜索发现**从未被任何调用方引用**——纯粹的死代码。`travelogue/web/copy_patch.py` 的 `meta.title` / `meta.coverOpeningStyle` 编辑路径完全没有调用它。
- **影响**：直接违反 **AC-CAL-09**——用户在 Studio 内联编辑改了标题后，`<h1>`（sr-only）和 `meta.title` 都已经是新文案，但已生成的贴纸（PNG 里烧的是旧标题的字形）会继续原样展示，且不会被判定为「已过期」。这是一个真实的用户可感知的「显示错误信息」缺陷,而不是理论风险。
- **修复**：`copy_patch.py` 的 `meta.title` 与 `meta.coverOpeningStyle` 两个分支末尾各加一行 `mark_title_art_stale(trip)`。
- **验证**（端到端，用真实 `demo-1547c68851/trip.json` 跑通，非纯 mock）：

  ```text
  before stale: False enabled: True
  before render: has_title_art = True trip-derived/title-art/....png
  after stale: True
  after edit render: has_title_art = False None
  ```

  改标题后 `stale` 置真，`assemble.py` 的 `_resolve_title_art_src` 立即按 fail-open 处理（回退到可见 `<h1>`），不会展示「贴着旧字的过期贴纸」。
- **回归**：新增 `tests/unit/domain/test_copy_patch.py::test_apply_meta_title_marks_existing_title_art_stale`、`test_apply_meta_title_noop_when_no_title_art`、`test_apply_cover_opening_style_marks_existing_title_art_stale`。

---

## 2. AC 逐项核对

| AC | 核对方式 | 结果 |
|----|----------|------|
| **AC-CAL-03**（代码审查：无 brush_effects / engine v3/v4 生产路径） | `grep -i "brush_effect\|engine_v[234]\|骨架\|arttext_miniapp"` 遍历 `travelogue/cover_engine/title_art/` | ✅ 唯一命中是 `render_b.py` 里「明确不做飞白/骨架/笔锋做旧」的红线声明本身；`style_registry.py` 里的「笔锋」字样是路线 C 的 diffusion prompt 文案（D-CAL-02 明确路线 C 不受此红线约束）；无 `arttext_miniapp` 运行时依赖 |
| **AC-CAL-07**（字库/印章授权留痕） | 见 §1.1；核实 ZhiMangXing-Regular = Google Fonts「钟齐志莽行书」，SIL OFL 1.1（可商用、免署名）；新增 `assets/fonts/LICENSE-NOTES.md` 留痕；印章 V1 为程序生成矢量图形（自制，无外部素材版权问题） | ✅（连带修复了资产实际不可加载的问题） |
| **AC-CAL-08**（缺字形 / 非白名单 style → 不叠加贴纸且 h1 可见） | 真实 trip `demo-0ebda73294`（`coverOpeningStyle=band-cut`，非白名单）跑 `title-art` CLI + `render`；核对输出 HTML | ✅ CLI 报 `未生成（非白名单 openingStyle...已 fail-open）`；`trip.meta.titleArt.enabled=false`；渲染出的 `index.html` 里只有裸 `<h1 class="cover-opening__title cover-opening__title--vertical">`，**无** `sr-only`、**无** `<img class="cover-opening__title-art">` |
| **AC-CAL-09**（改 title 后 stale 生效，禁止继续展示旧文案贴纸） | 见 §1.3；发现即修复 | ✅（修复前 ❌） |
| **AC-CAL-12**（路线 C 失败必须静默降级路线 B，禁止展示错误态/半成品） | 真实条件（当前环境 `DASHSCOPE_API_KEY` 未设置，非 mock）跑 `title-art --route-c --force` | ✅ CLI 退出码 0，输出 `OK title-art · 路线B · ...` + `fallback: diffusion-fixed-prompt-v1 → clean-pipeline-v1（D-CAL-16）`；`trip.meta.titleArt.fallbackFrom="diffusion-fixed-prompt-v1"`、`engine="clean-pipeline-v1"`、`enabled=true`——路线 B 结果完整可用，无错误态 |

---

## 3. 真实封面视觉核对（修复后）

三张不同构图/配色的真实照片，`veil-footer` 白名单风格，均为 `--force` 重新生成后过 Playwright 实测（非 mock/fixture）：

| 附件 | trip | 标题 | 说明 |
|------|------|------|------|
| ① | — | — | 修复字体资产路径后，隔离渲染 + 深色底合成，核对 ZhiMangXing 真实笔锋（对照修复前一直是无衬线体） |
| ② | `demo-1547c68851` | 夏睿彤贵州暑假游（8 字） | 修复中间态：容器嵌套已修，但贴纸未裁剪，仍顶出视口顶部——留作过程证据 |
| ③ | `demo-1547c68851` | 夏睿彤贵州暑假游（8 字） | 三处均修复后：不重叠 hook、不顶视口、配色（白字）在实拍照片上对比度正常 |
| ④ | `demo-20ecc928d6` | 武大 米娜（5 字，含空格） | 人像特写构图；标题居中留白区域干净，无遮挡 |
| ⑤ | `demo-65db8fd377` | 凯哥拍摄精选4（7 字） | 高动态运动照片（冲浪）；白字在蓝色水面上对比度良好 |

图见 [`attachments/cover-calligraphy-title-v1-w1-visual-review-2026-08-07/`](./attachments/cover-calligraphy-title-v1-w1-visual-review-2026-08-07/)。

**遗留观察项（非阻塞，记入 §12.2 开放问题）**：③ 中标题最左字「彤」的笔画末端与人物银饰头冠顶端有轻微视觉重叠——`placement_score` 目前只对**人脸 bbox** 做重叠惩罚，头饰/帽子等延伸物未纳入检测，属于 §6.2 定位算法精度问题，不是本次验收范围内的渲染 bug。建议 W2 收集更多真实素材后评估是否需要扩大人体/头部检测框。

---

## 4. 回归测试

```text
tests/unit/cover_engine/          120 passed
tests/unit/render/                （含 assemble.py 改动）全绿
tests/unit/config/                全绿
tests/unit/domain/test_copy_patch.py   16 passed（含 3 条新增 stale 回归）
tests/unit/web/test_studio_preview_m16.py   6 passed
合计（cover_engine + render + config + copy_patch 关键子集）  359 passed, 6 skipped
```

`ruff check` 全部通过（含本次改动文件）。

---

## 5. 验收结论

- **AC-CAL-03 / 07 / 08 / 12**：核对通过。
- **AC-CAL-09**：核对时发现未接线，**已修复并转为通过**。
- **本次审查的副产品**：发现并修复了 2 个此前未被 83 条单测捕获的真实集成缺口（字体资产路径、贴纸容器定位），说明「纯 mock 单测全绿」和「真实素材端到端可用」之间存在缺口——建议后续每次涉及渲染表面的改动，都补一次真实 trip + Playwright 的人工核对，不能只信单测绿灯。
- **仍然开放**：AC-CAL-11（路线 C OCR 回读通过率阈值）依赖完整 W0.5 Spike（20~30 条真实/边界标题），本次未做，维持 PRD 现状「`route_c_enabled` 默认 false」。
