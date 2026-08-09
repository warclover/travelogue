# D-CAL-26 · 装帧身份线：前封回声（D-SFI-13 扩容）

**日期**：2026-08-09
**状态**：已落地并**默认开启**（4 款风格视觉验证通过后，产品负责人拍板翻转默认值）
**关联**：[PRD-COVER-CALLIGRAPHY-TITLE-V1](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · [PRD-SHARE-FACE-INTEGRITY-V1 §3.7 D-SFI-13](../PRD-SHARE-FACE-INTEGRITY-V1.md)

## 1. 起因

产品负责人在讨论"重新设计封面系统"时提出两条 backlog：

1. 三层排版规范化（主标题 + 副标题 + 印记）
2. 装帧身份线（前后封统一品牌标记）

调研后澄清：①「印记」特指印章/图形，产品负责人此前已主动决定不做（审美风险太高），**已关闭，不在本记录范围**。②「装帧身份线」经确认是指纯文字署名（非图形），复用已有的 D-SFI-13 署名三态（`travelogue/domain/works_brand.py`：默认 `Travelogue` / 自定义 ≤14 字 / 隐藏），该机制目前只驱动两处渲染位——`cover-closing__brand`（封底）与 `longshot-boundary-footer__brand`（长图页脚）。本记录评估把它扩展到**第三处**：前封（`cover-opening`）。

## 2. 跨 PRD 边界

D-SFI-13 原文（`PRD-SHARE-FACE-INTEGRITY-V1.md` §3.7）：

> 署名三态……**同时驱动** `cover-closing__brand` **与** `longshot-boundary-footer__brand`，**两处**格式统一。

本记录把"两处"扩展为"三处"，是对另一主题已定契约的扩容，已经产品负责人确认（见对话记录）后再落地，不是 CAL 分支单方面决定。

## 3. 实现

- `travelogue/render/assemble.py`：新增 `_COVER_OPENING_BRAND_STYLES` 白名单常量 + `showCoverOpeningBrand` context 字段（`showWorksBrand and 风格在白名单`）。
- `templates/visual-journal/partials/cover-opening.hbs`：面板末尾追加 `{{#if showCoverOpeningBrand}}<p class="cover-opening__brand">{{worksBrandLine}}</p>{{/if}}`。
- `templates/visual-journal/journal.css`：基础样式（10px / 大写 / opacity 0.55，比照 `.cover-closing__brand`）+ 4 款风格各自的绝对定位覆盖。

## 4. 踩坑记录：为什么不能"直接追加一个文档流元素"

第一轮试点只加了基础样式（文档流），`band-cut` 视觉正常，但 `veil-footer`／`contact-stamp`／`folio-overlap` 全部出 bug——署名飘到了封面左上角，跟标题完全脱节。

根因：这三款风格的标题/副标题/hook 在 `html[data-layout="web"/"auto"]` 断点下全部用 `position: absolute` 各自钉死坐标（脱离文档流）；新加的 `.cover-opening__brand` 是文档流元素，脱离了同样被搬空的绝对定位兄弟节点后，直接"塌"到了面板自身的（几乎为空的）文档流顶部。`band-cut` 之所以一次性通过，是因为它的面板本身是文档流布局（"纸签"面板一贯的设计），并非普遍规律。

**修复**：改为按每款风格单独写绝对定位覆盖，锚点跟随该风格的标题或 hook 现有坐标（`left`/`right` 同锚点，`bottom` 取更小值即更贴近真实底边），保证署名行落在标题/hook 下方的天然留白区，不管 hook 是 1 行还是 3 行都不会撞上。

## 5. 视觉验证（4 款风格全部通过）

用真实 demo trip 分别渲染 + 截图核对：

| 风格 | 样例 | 结果 |
|---|---|---|
| `band-cut` | 初中毕业照 | ✅ 标题下方一行小号「TRAVELOGUE」，干净 |
| `veil-footer` | 夏睿彤贵州暑假游 | ✅ hook 下方留白区，无重叠 |
| `contact-stamp` | 斯里兰卡见闻录 | ✅ 标题下方，避开右下角 archive/hook 列 |
| `folio-overlap` | 王丹昙华林半日游 | ✅ 纸面栏左下角，未越过骑缝线 |

截图见 `attachments/cover-calligraphy-title-v1-front-cover-identity-line-2026-08-09/`（`band-cut.png` / `veil-footer.png` / `contact-stamp.png` / `folio-overlap.png`）。

## 6. 当前落地状态

- `_COVER_OPENING_BRAND_STYLES = ("band-cut", "veil-footer", "contact-stamp", "folio-overlap")`——4 款艺术字白名单风格默认显示前封回声；白名单外风格（`type-monument` 等未核对绝对定位布局的旧风格）仍不显示，避免盲开出与 §4 同类的 bug。
- 影响范围：所有使用这 4 款风格且 `showWorksBrand` 为真（默认态或自定义态，仅 `worksBrandMode=hidden` 会关闭）的既有 trip，前封会新增一行小号署名回声；无需用户任何操作，无新开关。
- 新增 `tests/unit/render/test_cover_opening_identity_line.py`（9 条），覆盖：4 款风格默认显示、白名单外不显示、`worksBrandMode=hidden` 优先级、自定义署名文案、模板真实渲染有/无标记（含"误改白名单常量"回归防线）。
- 回归：`tests/unit/render` + `tests/unit/domain/test_works_brand_sfi.py` + `tests/unit/cover_engine` 464 passed, 6 skipped；ruff 全绿。

## 7. 后续

若日后要把其它旧风格（`type-monument` / `scroll-head` / `portal-arch` 等）也纳入，需要重复本记录 §4 的绝对定位排查——不能假设"追加进白名单常量就自动生效"，必须先按该风格的标题/hook 坐标写专门的 CSS 覆盖并截图核对，否则会重演飘位 bug。
