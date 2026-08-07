# PRD-COVER-CALLIGRAPHY-TITLE-V1 · W2 白名单扩容（band-cut / contact-stamp）

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-COVER-CALLIGRAPHY-TITLE-V1.md](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md)（**CAL**）§3 D-CAL-20 · §5.4 · §11 W2 |
| **分支** | `feat/cover-calligraphy-title-v1` |
| **覆盖事项** | D-CAL-20 优先顺位①②：`whitelist.py` 改为从 Opening Registry `text_safe_regions` 派生坐标；新开放 `band-cut` / `contact-stamp` 两款白名单风格 |
| **日期** | 2026-08-07 |
| **方式** | 真实 trip（`demo-0ebda73294`，`coverOpeningStyle=band-cut`）跑通 CLI `title-art` → `render` → Playwright 实际渲染核对；`contact-stamp` 因仓内暂无真实样例，用同一份真实照片临时拷贝一份 trip 改 `coverOpeningStyle` 做视觉核对（验证后已删除临时目录，未提交） |
| **结论** | **通过——过程中发现 1 处 CSS 侧白名单未同步的集成缺口，已定位修复** |

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

---

## 2. 视觉核对

### 2.1 band-cut · 真实 trip `demo-0ebda73294`（标题「初中毕业照」）

真实操场毕业照，断带横穿人像下半身（无人脸落入该区域）；标题字压在断带纸底与围栏花纹上，印章落在花纹区域，未遮挡任何人脸，未与 hook 文案（"初中毕业照·1天"，位于断带右侧）重叠——实测两者 DOM 矩形 x 轴无交集。

![band-cut 真实核对](attachments/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07/band-cut-demo-0ebda73294.png)

### 2.2 contact-stamp · 同一张真实照片临时改风格核对

贴纸落在左下角（左块候选），跨在照片底缘与做旧面板衔接处；右下角日戳档案号（"2026.05.27－06.23"）与左侧贴纸 x 轴无交集，互不干扰。

![contact-stamp 临时核对](attachments/cover-calligraphy-title-v1-w2-whitelist-expand-2026-08-07/contact-stamp-synthetic-scratch.png)

---

## 3. 回归测试

- `tests/unit/cover_engine/test_title_art_whitelist.py`：新增/更新 —— `band-cut`/`contact-stamp` 默认白名单断言；新增参数化测试逐一核对 `band-cut`/`contact-stamp`/`folio-overlap` 的 `rect` 与 `get_profile(style_id).text_safe_regions[i]` 完全一致（防止未来再度手搓脱节）；新增 `test_contact_stamp_rect_avoids_hook_region` 断言左右两块不重叠。
- `test_other_styles_are_not_whitelisted` 参数化列表移除已转正的 `band-cut`，补充其它仍下线/非白名单风格覆盖。
- 全量 `tests/unit/cover_engine/` 129 passed；`ruff check` 全绿。

---

## 4. 结论

| 事项 | 结果 |
|------|------|
| `whitelist.py` 矩形改为 registry 派生 | ✅ |
| `band-cut` 开放白名单 | ✅ 真实 trip 核对通过 |
| `contact-stamp` 开放白名单 | ✅ 临时改风格核对通过（仓内暂无真实样例，建议后续遇到真实 contact-stamp trip 时补一次留痕） |
| CSS 侧白名单同步缺口 | ✅ 已发现并修复 |
| `veil-footer` 现有矩形风险（D-CAL-20 优先顺位④） | ⏳ 未处理，本次范围外，见 OQ-CAL-08 |
| `folio-overlap` 开放为默认白名单（优先顺位③） | ⏳ 未处理，矩形已对齐 registry 但仍保持默认关闭 |
