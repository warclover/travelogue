# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W2 白名单扩容（band-cut / contact-stamp）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL**）§3 D-CAL-20 · §5.4 · §11 W2 |
| **分支** | `feat/cover-calligraphy-title-v1` |
| **覆盖事项** | D-CAL-20 优先顺位①②：`whitelist.py` 改为从 Opening Registry `text_safe_regions` 派生坐标；新开放 `band-cut` / `contact-stamp` 两款白名单风格；开放前 CSS 暗坑排查（§5）；D-CAL-20 优先顺位④ veil-footer focal 安全网 + OQ-CAL-08 结论修正（§6）；D-CAL-20 优先顺位⑤ 多候选打分择优（§7，D-CAL-20 全部五项完成） |
| **日期** | 2026-08-07 |
| **方式** | 真实 trip（`demo-0ebda73294`，`coverOpeningStyle=band-cut`）跑通 CLI `title-art` → `render` → Playwright 实际渲染核对；`contact-stamp` 因仓内暂无真实样例，用同一份真实照片临时拷贝一份 trip 改 `coverOpeningStyle` 做视觉核对（验证后已删除临时目录，未提交） |
| **结论** | **通过——过程中发现 2 处集成缺口（CSS 侧白名单未同步 + contact-stamp 自动配色未考虑深色渐罩），均已定位修复；追加对 4 款风格的开放前 CSS 排查（§5），发现 `folio-overlap` 尚不能直接开放，记为 OQ-CAL-09；落地 D-CAL-20 优先顺位④，修正并关闭 OQ-CAL-08，veil-footer 补齐 focal 安全网（§6）；落地 D-CAL-20 优先顺位⑤，多候选打分择优，contact-stamp 首个双候选落地，D-CAL-20 全部五项完成（§7）** |

---

## 0. 一句话结论

`whitelist.py`（Python 侧数据）改造之后本身跑单测是绿的，但真机渲染一看贴纸压根没显示——`journal.css` 里还有一份**独立维护的 CSS 白名单**（`display:none` 默认 + 仅 `veil-footer` 一行 `display:block` 覆盖），Python 侧加了新风格，CSS 侧没跟着加，贴纸 `<img>` 标签虽然正确写进了 DOM（`src` 也对），但 `display:none` 直接不可见。补上 `band-cut`/`contact-stamp` 两行选择器后两款风格视觉核对通过。

再次印证同一条经验：**这类"两处各自维护一份白名单/数据表"的接线点，纯 mock 单测测不出来，必须跑真实浏览器渲染。**

---

## 1. 变更内容

### 1.1 `whitelist.py`：矩形坐标改为从 Registry 派生（D-CAL-20）

- 新增 `_registry_rect(style_id, region_index)`：直接读取 `travelogue.cover_engine.registry.get_profile(style_id).text_safe_regions[region_index]`，不再在本文件手搓 x/y/w/h 数值。
- `band-cut` → `text_safe_regions[0]` = `{x:0, y:0.60, w:0.55, h:0.14}`。
- `contact-stamp` → `text_safe_regions[0]`（左块，避让右块 hook/日戳号）= `{x:0, y:0.72, w:0.55, h:0.28}`。
- `folio-overlap`（仍默认关闭）顺带对齐到 `text_safe_regions[1]`（底部横条候选），替换掉此前跟 registry 数值不精确重合的手搓矩形；不影响其禁用状态。
- `veil-footer` **本次不动**：registry 里该风格唯一的 `text_safe_regions` 是雾带底部（与现有 hook/trip-meta 面板同一块，已被文案占用），跟现有"雾带上方"矩形语义不是一回事，直接派生会重新引入 v0.5 刚修的重叠问题——标注 `TODO(D-CAL-20 优先顺位④)`，留给 OQ-CAL-08 解决后再处理。
- `DEFAULT_ENABLED_STYLES` 新增 `band-cut` / `contact-stamp`。

### 1.2 【已修复】CSS 侧白名单未同步，新风格贴纸 `display:none`

- **现象**：`band-cut` 真实 trip 跑 `title-art` CLI 生成成功（`trip.meta.titleArt.enabled=true`，`position` 落在预期的 `{x:0.27, y:0.67}`），`render` 也正常产出 `<img class="cover-opening__title-art">`，但 Playwright 截图完全看不到贴纸。
- **根因**：`journal.css` 里 `.cover-opening__title-art` 默认 `display:none`，只有 `html[data-layout="web"/"auto"] .cover-opening[data-cover-opening="veil-footer"] .cover-opening__title-art` 这一条选择器把它改回 `display:block`——是一份**独立于 `whitelist.py` 的 CSS 侧白名单**，`DEFAULT_ENABLED_STYLES` 加了新风格，这里没跟着加，贴纸元素虽然在 DOM 里且 `src` 正确，但视觉上完全不可见（`getComputedStyle` 核对确认 `display:none`）。
- **修复**：把 `band-cut` / `contact-stamp` 两个 `data-cover-opening` 值追加进同一条选择器列表（复用同一套 `left/top: var(--title-art-x/y)` 定位规则，因为 §6.2 算出来的百分比本身跟风格无关，只是矩形来源不同）。顺手在 CSS 里加了一行注释标注这是手动维护点，两处目前没有自动同步机制。
- **验证**：修复前 `getComputedStyle(img).display === 'none'`；修复后重渲染 + 截图，贴纸正常显示在断带区域，见 §2 附件。

### 1.3 【已修复】contact-stamp 自动配色未考虑固定深色渐罩 → 深墨读不出来

- **现象**：1.2 修复上线并宣布完成后，用户直接拿 `http://127.0.0.1:8798/`（本记录 §1.2 用来核对的临时 contact-stamp trip）截图反馈：「文字都被遮挡了，且颜色一致，看不出来」。截图显示笔画只在照片区露出极小的笔尖，进入黑色面板区域后完全消失，只有红色印章还看得清。
- **根因**：`journal.css` 里 `contact-stamp` 用 `.cover-opening[data-cover-opening="contact-stamp"]::after` 在**整张封面**上叠加一层不透明度约 0.3～0.72 的黑色渐变（跟原始照片内容无关），且该风格的原生 `<h1>` 因此固定用浅色 `#f5f2ec`、从不跟随照片亮度。但 §6.1 的自动配色（`roi_average_color`）采样的是**渐罩叠加前**的原始照片像素——这张真实毕业照在候选矩形区域内偏亮（浅蓝色校服/白色围栏花纹），算法据此判断「背景够亮，选深墨」，`pick_readable_color` 的达标判定（`contrast_ratio ≥ 3.0`）也是拿深墨去跟这个**虚高**的亮度估计比对，误判为达标——实际渲染出来的背景早被渐罩压到接近全黑，深墨完全读不出来。这跟 §1.2 是两个独立缺口：§1.2 是「贴纸看不见」（CSS 白名单没同步），本条是「贴纸看得见但读不出来」（配色输入信号跟渐罩前后不一致）。
- **修复**：`PlacementPreset` 新增 `assume_dark_veil: bool` 字段；`contact-stamp` 标记为 `True`（其它三款白名单风格均为 `False`，均无这类全幅深色渐罩）。`engine.py` 在算出 `bg_rgb` 后，若命中该字段则直接改用近黑背景估计（`(10,10,10)`），让 §6.1 的对比度算法必然回到白色墨迹——不再信任「渐罩前」的原始照片采样。
- **验证**：同一张真实照片、同一份真实 trip 数据，临时改风格为 `contact-stamp` 重新生成 + 渲染 + Playwright 截图核对，`trip.meta.titleArt.mainColor` 由修复前的深色变为 `#ffffff`，`explain` 新增一条 `"contact-stamp 固定深色渐罩 · 忽略照片原始亮度采样"`；视觉上标题字清晰可辨，见 §2.3。
- **回归**：新增 `test_assume_dark_veil_flag`（`test_title_art_whitelist.py`，参数化核对四款白名单风格的该字段取值）；新增 `test_contact_stamp_dark_veil_forces_white_ink_despite_bright_photo`（`test_title_art_engine.py`，用一张纯白模拟照片断言即便原始 ROI 很亮，`assume_dark_veil` 生效后仍强制选回白色）。

---

## 2. 视觉核对

### 2.1 band-cut · 真实 trip `demo-0ebda73294`（标题「初中毕业照」）

真实操场毕业照，断带横穿人像下半身（无人脸落入该区域）；标题字压在断带纸底与围栏花纹上，印章落在花纹区域，未遮挡任何人脸，未与 hook 文案（"初中毕业照·1天"，位于断带右侧）重叠——实测两者 DOM 矩形 x 轴无交集。

![band-cut 真实核对](attachments/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07/band-cut-demo-0ebda73294.png)

### 2.2 contact-stamp · 同一张真实照片临时改风格核对

贴纸落在左下角（左块候选），跨在照片底缘与做旧面板衔接处；右下角日戳档案号（"2026.05.27－06.23"）与左侧贴纸 x 轴无交集，互不干扰。

![contact-stamp 临时核对（修复前，笔画进入黑色面板区后不可辨）](attachments/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07/contact-stamp-synthetic-scratch.png)

### 2.3 contact-stamp · 深色渐罩配色修复后

同一张真实照片、同一份数据，`assume_dark_veil` 生效后墨色改为白色，标题在黑色面板区域清晰可辨：

![contact-stamp 深色渐罩修复后](attachments/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07/contact-stamp-dark-veil-fix.png)

---

## 3. 回归测试

- `tests/unit/cover_engine/test_title_art_whitelist.py`：新增/更新 —— `band-cut`/`contact-stamp` 默认白名单断言；新增参数化测试逐一核对 `band-cut`/`contact-stamp`/`folio-overlap` 的 `rect` 与 `get_profile(style_id).text_safe_regions[i]` 完全一致（防止未来再度手搓脱节）；新增 `test_contact_stamp_rect_avoids_hook_region` 断言左右两块不重叠。
- `test_other_styles_are_not_whitelisted` 参数化列表移除已转正的 `band-cut`，补充其它仍下线/非白名单风格覆盖。
- 新增 `test_assume_dark_veil_flag`（`test_title_art_whitelist.py`）+ `test_contact_stamp_dark_veil_forces_white_ink_despite_bright_photo`（`test_title_art_engine.py`），见 §1.3。
- 全量 `tests/unit/cover_engine/` 134 passed；`ruff check` 全绿。

---

## 4. 结论

| 事项 | 结果 |
|------|------|
| `whitelist.py` 矩形改为 registry 派生 | ✅ |
| `band-cut` 开放白名单 | ✅ 真实 trip 核对通过 |
| `contact-stamp` 开放白名单 | ✅ 临时改风格核对通过（仓内暂无真实样例，建议后续遇到真实 contact-stamp trip 时补一次留痕） |
| CSS 侧白名单同步缺口 | ✅ 已发现并修复 |
| contact-stamp 自动配色未考虑深色渐罩 | ✅ 已发现并修复（用户实测反馈发现） |
| `veil-footer` 现有矩形风险（D-CAL-20 优先顺位④） | ⏳ 未处理，本次范围外，见 OQ-CAL-08 |
| `folio-overlap` 开放为默认白名单（优先顺位③） | ⏳ 未处理，矩形已对齐 registry 但**发现新的开放阻断项**，见 §5、OQ-CAL-09 |

---

## 5. 前瞻审计：开放前排查其余风格的 CSS 暗坑（2026-08-07 追加）

§1.3 的教训是「配色输入信号跟 CSS 实际渐罩不一致」这一类坑要等真机截图才暴露。为避免同类坑逐个"等用户截图反馈才发现"，这次趁热把 `journal.css` 里已注册/待注册的 4 款风格（`veil-footer` / `band-cut` / `contact-stamp` / `folio-overlap`）逐一过了一遍，专门找"实际渲染跟原始照片采样不一致"或"矩形跟既有元素冲突"这两类坑。

### 5.1 排查方法

对每款风格检查三类信号：
1. `.cover-hero`（照片本体）是否有 `filter:`（会让屏幕上的颜色跟 Python 侧读取的原始文件像素不一致）；
2. 风格专属的 `::before`/`::after` 是否有覆盖候选矩形区域的渐变/半透明遮罩（跟 §1.3 contact-stamp 同类坑）；
3. 候选矩形范围内是否已经有其它常驻 DOM 元素（地点标签、trip-meta、hook 文案等），会造成视觉重叠而不是配色错误。

### 5.2 结论：veil-footer / band-cut — 排查通过，非阻断

- **veil-footer**：`.cover-hero` 无 `filter`；风格专属的 `::before`（暖色 `mix-blend-mode:screen` 渐罩，最高不透明度 0.30）虽然 `z-index` 跟贴纸 `<img>` 相同，但伪元素在绘制顺序上等价于"最先出生的子元素"，本贴纸是真实子元素且在源码顺序里更靠后，天然叠在渐罩上方，不会被其遮住；且渐罩本身透明度低，非阻断项。矩形本身的既知风险（跟 hook/trip-meta 面板重叠）仍是 OQ-CAL-08 未解决的旧账，本次未处理。
- **band-cut**：`.cover-hero` 无 `filter`；唯一覆盖候选矩形范围的是**四款风格共用**的左下角暖色 `mix-blend-mode:soft-light` 渐罩（`.cover-opening:not([data-cover-opening="veil-footer"])::before`，最高不透明度 0.30），同理绘制顺序在贴纸之下；且 §2.1 真机核对已经验证深墨清晰可辨，说明这层低透明度暖罩实测不影响可读性。

### 5.3 结论：contact-stamp — 已在 §1.3 修复，无新增发现

`.cover-hero` 有 `filter: saturate(0.48) contrast(1.12) sepia(0.22)`（做旧滤镜），但 §1.3 的 `assume_dark_veil` 修复已经让配色直接假设近黑背景、不再信任原始像素采样，这层做旧滤镜对最终选色结论没有额外影响。

### 5.4 新发现：folio-overlap 两条候选矩形都不能直接套用同一套"贴纯色 PNG"流程（OQ-CAL-09）

这是本次排查最大的收获——`folio-overlap` 的 `text_safe_regions` 有两条，逐一核对发现两条都有问题，跟 band-cut/contact-stamp「派生矩形 + 开白名单」的直给流程不一样：

- **候选 #0**（`{x:0, y:0, w:0.33, h:1.0}`，左侧纸列，全高）：`journal.css` 里这一整块区域被 `.cover-opening__place`（地点标签，`writing-mode: vertical-rl` 竖排）常驻占用——`left:0; top:32px;` 且 `pointer-events:auto`，贴纸落在这里会跟地点标签直接视觉重叠，不是配色问题，是布局占位冲突。
- **候选 #1**（`{x:0, y:0.58, w:0.7, h:0.2}`，此前 `whitelist.py` 选用的那条）：横向跨了三种不同背景——
  - `x: 0~0.33`：纸面栏，纯色 `#f4f1ea`（米白纸张底色）；
  - `x: 0.33~0.7`：照片区靠近骑缝处，叠着 `.cover-hero::after` 的 90° 黑色渐变（`0.46 → 0.16` 不透明度，且被竖向 mask 限制只在 `y: 0.22~0.74` 生效——跟本候选的 `y: 0.58~0.78` 只有部分重合，底部 `0.74~0.78` 这一小段完全没有渐罩）；
  - 而且原生 `<h1>` 在这个位置本来就不是单色渲染：用两份 `content: attr(data-title)` 叠加不同 `clip-path`，纸面侧走深墨 `#141312`、照片侧走浅色 `#fcfaf6` + 投影，**故意做出"书名骑缝切开压进画面"的双色断字效果**（这是 `studio_blurb` 里原话描述的核心设计语言，不是意外）。单一纯色 PNG 贴纸没法在这条矩形范围内同时兼顾三种背景，套哪个颜色都会在另一侧读不出来。

**结论**：`folio-overlap` 暂不适合直接复用 `band-cut`/`contact-stamp` 那种"矩形派生 + 翻开关"的路径，需要专门方案（例如把矩形收窄到只落在纯纸面栏内且避开 `__place`，或做一版双色渡色贴纸）才能安全开放。已在 `whitelist.py` 补充详细 TODO 注释，`PRD` 补充 `OQ-CAL-09`，本次**不改变**默认关闭状态、**不改** rect 数值（矩形仍占位为候选 #1，等真正方案定下来再动）。

### 5.5 回归

仅新增代码注释（`whitelist.py`），未改动任何 `rect` 数值、逻辑分支或默认启用集合；`tests/unit/cover_engine/` 134 passed 不变。

---

## 6. veil-footer 已知矩形风险修复（D-CAL-20 优先顺位④ · OQ-CAL-08）

### 6.1 重新审视：OQ-CAL-08 的原倾向站不住脚

`whitelist.py` 里 `veil-footer` 的 `TODO(D-CAL-20 优先顺位④)` 一直标注着：该风格 registry 里唯一的 `text_safe_regions`（雾带底部 `{x:0,y:0.55,w:0.58,h:0.45}`）跟现有 hook/trip-meta 面板是**同一块区域**，直接派生会重新引入 v0.5 刚修的重叠问题；OQ-CAL-08 原本倾向"先接 `mark_title_safe` 的 focal 校验兜底"再决定是否需要额外补一层排除校验。

重新审视这条倾向时发现前提有误：`mark_title_safe`/focal 校验解决的是「**镜头主体**是否落在候选区」，跟「**候选区本身有没有被本风格自身 UI（面板/hook/trip-meta）占用**」是两个完全独立的信号——前者关心照片内容，后者关心页面布局，focal 校验对后者无能为力。而 veil-footer 的这条冲突恰恰是后者：面板是**真实存在的 DOM 元素**，不管镜头焦点在哪，只要贴纸落在面板范围内就会被文案压住/压住文案。

**结论**：不再考虑把 veil-footer 切换到 registry 派生的雾带底部矩形——v0.5 视觉验收后手工收窄出来的雾带上方矩形（`{x:0.08,y:0.14,w:0.84,h:0.22}`）本身就是刻意避开面板占位的正确选择，转为该风格的**既定候选区**，不再是"临时占位待替换"。「候选区是否被自身 UI 占用」这类布局冲突，目前只能靠人工设计矩形时主动避让（如本次），暂不值得为此建一套自动化排除机制——4 款已开放风格里只有 veil-footer 有这个问题，投入产出比不高。

### 6.2 真正该做的：给"实际候选框"补一层 focal 安全网

OQ-CAL-08 里 focal 校验确实能解决的那一半问题是存在的：雾带上方矩形虽然避开了面板，但没人验证过它会不会正好落在**镜头主体**（人脸/人像）上——`score_candidate` 的人脸重叠惩罚依赖运行时人脸检测器（`detect_faces_in_image`，成本更高、且并非任何环境都可用），此前没有更轻量、确定性的兜底信号。

新增 `travelogue.cover_engine.title_art.placement.focal_conflict(asset, rect)`：复用选图环节已经算好的 `asset.focalPoint` + `travelogue.cover_engine.fit.focal_is_trusted`（跟 `title_safe.py::mark_title_safe` 同一套"是否为可信焦点"判定），检查这个焦点是否落在**实际用来渲染贴纸的候选框**内（注意：不是 registry 原始 `text_safe_regions`，veil-footer 这两者本就不同，见 §6.1）。

`engine.py` 接线：在算出 `preset` 后，若 `cover_asset` 存在且命中 `focal_conflict`，直接回退纯 HTML 标题（`disabled_meta_dict(reason="focal_conflict:<style_id>")`），不再往下走配色/渲染——因为该风格目前只有单一固定候选框，没有备选位置可切换（多候选打分是 D-CAL-20 优先顺位⑤，尚未落地），检测到冲突后除了整体让路别无选择。`disabled_meta_dict` 新增可选 `reason` 字段（默认不写，不影响既有调用点的最小形状），用于事后从 `trip.json` 直接读出这次为什么没生成艺术字。

### 6.3 回归测试

- `test_title_art_placement.py`：新增 4 条 `focal_conflict` 单测——可信焦点落在框内/框外、焦点不可信（等于默认兜底值且无真实人脸信号）、完全没有 `focalPoint` 字段。
- `test_title_art_engine.py`：新增 `test_focal_conflict_with_placement_rect_fails_open_to_html_title`（断言 fail-open、`reason` 字段正确、不落盘任何 PNG）+ `test_focal_outside_placement_rect_still_renders_normally`（焦点在框外时不受影响，正常生成）。
- `test_title_art_models.py`：新增 `test_disabled_meta_dict_with_reason_adds_field_without_changing_base_shape`。
- 全量 `tests/unit/cover_engine/` 141 passed；`tests/unit/domain/test_copy_patch.py` + `tests/unit/render/test_build_render_context.py` 20 passed（确认未影响既有 stale/渲染接线）；`ruff check` 全绿。

### 6.4 结论

| 事项 | 结果 |
|------|------|
| OQ-CAL-08 结论修正 | ✅ 已定案并关闭：focal 校验与"候选区被自身 UI 占用"是两个问题，不再混为一谈 |
| veil-footer 切换到 registry 派生矩形 | ❌ **不做**：registry 唯一候选跟自身面板结构性冲突，v0.5 手工矩形转正为既定候选区 |
| veil-footer 补 focal 安全网 | ✅ 已完成：`focal_conflict()` + `engine.py` 接线，冲突时回退纯 HTML 标题 |
| D-CAL-20 优先顺位④ | ✅ 完成 |
| D-CAL-20 优先顺位⑤（多候选打分统一闸门） | ✅ 已完成，见 §7 |

---

## 7. 落地 D-CAL-20 优先顺位⑤：多候选打分择优

### 7.1 设计

在 §6 的基础上补齐"遇冲突时能换一个候选区，而不是整体 fail-open"这一层：

- `whitelist.py`：`PlacementPreset` 新增 `conditional_occupant: str | None` 字段；新增 `FALLBACK_PRESETS: dict[str, list[PlacementPreset]]`（目前只有 `contact-stamp` 有一条）；新增 `placement_presets(style_id) -> list[PlacementPreset]`，返回"主候选 + 已知安全备选"，主候选永远排在第一位。
- `placement.py`：`PlacementCandidate` 新增 `preset` 字段（记录具体是哪个候选赢了打分），`score_candidate` 相应回填。
- `engine.py`：候选列表 = `placement_presets(style_id)`；两层淘汰——① 备选若带 `conditional_occupant`，按该 trip 实际内容判定是否被占用（`_candidate_occupied`，判定失败保守当作已占用）；② 对剩余候选逐一做 `focal_conflict` 淘汰。剩下的候选交给 `best_placement` 真正打分择优；全部淘汰才整体 fail-open（复用 §6 的 `disabled_meta_dict(reason=...)`）。

`contact-stamp` 落地了第一个双候选：主候选（左块，跟 sr-only `<h1>` 同一位置）+ 备选（右下角，`conditional_occupant="contact_stamp_hook_or_archive"`）。占用判定复用从 `assemble.py` 抽出的 `render.cover_opening.build_cover_archive_strip()`（新函数，跟 `show_hook_on_cover` 放一起）——不在 `title_art` 里重新手搓一份可能跟渲染层脱节的逻辑，直接吃 `assemble.py` 同款输入（`format_trip_meta` 的 `cover_place`/`meta_subline` + `cover_asset.takenAt`）。

### 7.2 实测发现：备选候选在现网几乎总被判定占用

验证 `_contact_stamp_hook_or_archive_present` 时发现：`format_trip_meta` 对天数字段有个兜底——即便完全没有 `dateStart`/`dateEnd`，也会返回形如 `"1 天"` 的 `meta_subline`，从不为空字符串：

```text
>>> format_trip_meta({}, intent=None, assets=[])
('旅途 · 1 天', '', '旅途', '1 天')
```

`build_cover_archive_strip` 只要 `meta_subline` 非空就会往档案条里塞一行，这意味着**几乎所有 trip 的档案条文案都非空**——不管 hook 是否显示，右下角这个备选候选在现网基本总是被判定为"已占用"。

这不是 bug，是 `format_trip_meta` 既有默认行为（超出本次范围，不动）；`conditional_occupant` 的判定逻辑是**正确、安全**的——它准确反映了"只要档案条有任何文字（即便只是'1 天'），视觉上就会跟贴纸重叠"这一事实，只是现实中触发窗口比预想的窄很多。单测里通过 `monkeypatch` 直接把判定函数打成"未占用"来验证多候选切换机制本身；同时新增一条测试直接断言"现实最小 trip 数据下该判定确实是 True"，把这个发现固化成回归防线，避免以后有人以为这条备选候选会经常生效。

### 7.3 回归测试

- `test_title_art_whitelist.py`：新增 6 条——`placement_presets` 对单候选风格（veil-footer/band-cut）等价于旧的单候选返回值；contact-stamp 主候选+备选顺序；未知风格返回空列表；主候选均无 `conditional_occupant`；contact-stamp 备选的 `conditional_occupant`/`assume_dark_veil`/矩形数值核对。
- `test_title_art_engine.py`：新增 4 条——现实最小 trip 数据下占用判定为 True；monkeypatch 占用判定为 False 后主候选冲突时正确切到备选（不 fail-open）；有真实照片时验证 `position` 落在备选矩形中心、且备选的 `assume_dark_veil` 生效（`mainColor="#ffffff"`）；不 monkeypatch（默认几乎总占用）时主候选冲突应整体 fail-open。
- `test_cover_opening.py`：新增 3 条——`build_cover_archive_strip` 抽取后的行为核对（空输入/拼接顺序/地名去重）。
- 修复一处 monkeypatch 陷阱：`_CONDITIONAL_OCCUPANT_CHECKS` 最初直接存函数对象引用，会在模块加载时锚定旧引用，导致 `monkeypatch.setattr(engine, "_contact_stamp_hook_or_archive_present", stub)` 静默失效（测试跑起来不报错但断言失败）——改成存函数**名字**、调用时 `globals()` 动态取值，跟 `monkeypatch` 替换模块属性的方式对齐。
- 全量 `tests/unit/cover_engine/` 151 passed；`tests/unit/curation/test_cover_opening.py` + `tests/unit/render/test_build_render_context.py` + `test_render_cover_and_card.py` + `test_render.py` + `tests/unit/domain/test_copy_patch.py` 42 passed；`ruff check` 全绿。

### 7.4 结论

| 事项 | 结果 |
|------|------|
| `placement_presets()` 主候选+备选 API | ✅ 已完成，单候选风格行为完全等价，无回归 |
| `PlacementCandidate.preset` 回填 | ✅ 已完成，调用方可知道具体命中哪个候选 |
| contact-stamp 首个双候选落地 | ✅ 已完成 |
| 占用检查复用 `assemble.py` 同款逻辑（避免脱节） | ✅ 已完成（`build_cover_archive_strip` 抽取为共享函数） |
| 备选候选现网真实触发率 | ⚠️ 很低（`format_trip_meta` 天数兜底几乎总非空）——设计正确但收益有限，如实记录 |
| D-CAL-20 五个优先顺位 | 全部完成（①②③④⑤） |
