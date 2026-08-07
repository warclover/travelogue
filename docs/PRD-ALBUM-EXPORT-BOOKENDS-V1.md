# PRD-ALBUM-EXPORT-BOOKENDS-V1 · 画册导出封面/封底页

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | v0.2 |
| **状态** | Implemented（Stage 1–3 已落地；真材视觉核对见版本记录） |
| **模块代号** | ABE（Album Bookends Export · 画册导出封面/封底页） |
| **前置条件** | [PRD-EXPORT-CARD-COMPOSE-V1.md](./PRD-EXPORT-CARD-COMPOSE-V1.md)（小红书/公众号/画册共享的 CardGrouper→CardTemplateSelector→CardRenderer 管线）· [PRD-BOOKENDS-ENGINE-V1.md](./PRD-BOOKENDS-ENGINE-V1.md)（Web 端封面/封底引擎，`coverAssetId`/`curation.closingAssetId` 数据来源） |
| **关联文档** | [PRD-BATCH-EXPORT-MULTISELECT-V1.md](./PRD-BATCH-EXPORT-MULTISELECT-V1.md)（画册照片池上限 250 张的最新决策，与本 PRD 的候选池排除逻辑衔接） |
| **更新日期** | 2026-08-07 |

---

## 1. 背景与问题

用户反馈（2026-08-06）：游记的 Web 预览和微信长图导出都有封面（图+标题）和封底（图+"N天·M张照片"统计），但**画册模式导出完全没有**——画册的 3:4 拼贴跨页从第一页开始就是正文照片，缺少书籍应有的"开卷/合卷"仪式感。

现状核实（`travelogue/export/collage_pack.py`）：

- 画册（`album_spread`）与小红书/公众号共享同一套纯 Pillow 拼贴管线（`CardGrouper → CardTemplateSelector → CardRenderer`），**没有任何封面/封底页的概念**——所有 3:4 Card 都来自同一个"精选照片池"，包括本该承担封面/封底职责的那两张照片（`trip.coverAssetId` / `trip.curation.closingAssetId`），它们目前只是被当作普通正文照片，混入拼贴模板。
- Web 预览 / 微信长图走的是完全独立的 HTML/CSS/Playwright 管线（`.cover-opening` / `.cover-closing`，`colophon-default` 票根样式），与画册的 Pillow 管线**没有代码复用关系**，样式手法不能直接搬过来。
- 小红书/公众号/单张海报**不需要**封面封底（用户已明确排除），只有画册这一个"实体成册"心智的出口需要。

---

## 2. 目标 / 非目标

| 编号 | 目标 | 说明 |
|------|------|------|
| G-ABE-01 | 画册导出新增一张独立的"封面页"（封面图 + 标题/副标题） | 位置固定在整本画册的第一页 |
| G-ABE-02 | 画册导出新增一张独立的"封底页"（封底图，票根风格极简落款，**不含**天数/地点/张数统计） | 位置固定在整本画册的最后一页 |
| G-ABE-03 | 封面/封底所用的两张照片，不得在画册正文中重复出现 | 从正文候选池中剔除这两张 asset id |
| G-ABE-04 | 仅影响 `album_spread` 一个分支，小红书/公众号/单张海报零改动 | 用户已明确排除这三者的封面封底需求 |
| G-ABE-05 | 封面/封底渲染异常或素材缺失时优雅降级，绝不阻断整本画册导出 | 与既有 Bookends 引擎"宁可省略不凑"的产品哲学一致 |

| 编号 | 非目标 | 说明 |
|------|--------|------|
| NG-ABE-01 | 不跨层复用 Web 端 `.cover-opening`/`.cover-closing` 的 HTML/CSS 渲染代码 | 画册走纯 Pillow 管线，两套渲染引擎不同源；本 PRD 只复用**视觉手法**（渐变遮罩 + CJK 字体栈），代码原生实现在 export 层 |
| NG-ABE-02 | 不新增任何 `trip.json` 数据字段 | 封面/封底所需数据（`coverAssetId`/`curation.closingAssetId`/`meta.title`/`meta.subtitle`/`meta.hook`）均已存在，直接读取 |
| NG-ABE-03 | 不做票根撕边的精细纹理（圆点齐洞） | v1 用等距虚线模拟撕边，视觉样式留作后续迭代（见 OQ-ABE-01） |
| NG-ABE-04 | 不影响小红书/公众号/单张海报的照片池、页数、渲染逻辑 | 排除逻辑只作用于 `album_spread` 分支内部 |

---

## 3. 数据来源（已实测核对，`demo-49cbe46479`）

```json
// trip.json 顶层
"coverAssetId": "asset-068"
"curation": { "closingAssetId": "asset-247" }
"meta": {
  "title": "……",
  "subtitle": "",
  "hook": "…… · 11天"
}
```

- **封面照片**：`trip.coverAssetId`（必然存在，Bookends 引擎保证）。
- **封面文案**：`meta.title`（大字）+ 副标题按 `subtitle → hook → 无` 优先级兜底（小字，`subtitle` 当前多为空字符串，故实践中常退回 `hook`）。
- **封底照片**：`trip.curation.closingAssetId`（**可能为 `None`**——Bookends 引擎的 `resolve_closing` 在候选不足时会主动判定"宁可省略"，见 `travelogue/cover_engine/api.py`）。
- **封底文案**：不读统计字段，只取游记标题（小字落款）+ 固定的"THE END"风格品牌落款。

---

## 4. 方案设计

### 4.1 拍板决策

| 编号 | 决策 | 说明 |
|------|------|------|
| D-ABE-01 | 封面页 = `coverAssetId` 对应照片，全出血裁剪进单卡画布 + 底部渐变遮罩 + `meta.title`（大字）+ 副标题（`subtitle`→`hook`→无，小字） | 视觉手法参考 `travelogue/render/preview.py` 的 `render_preview_jpg`（渐变遮罩 + `msyh.ttc`/`simhei.ttf` 兜底字体栈），但**不 import** `travelogue.render.*`，在 export 层原生重写一份轻量实现（对应 NG-ABE-01） |
| D-ABE-02 | 封底页 = `closingAssetId` 对应照片 + 游记标题小字落款 + "THE END" 品牌落款 + Pillow 等距虚线模拟撕边，**不含**天数/地点/张数统计 | 用户 2026-08-06 明确排除统计数字；票根意象保留极简落款+装饰虚线，不做圆点齐洞纹理（v1 收窄，见 OQ-ABE-01） |
| D-ABE-03 | `closingAssetId` 为 `None`（Bookends 引擎判定候选不足、主动省略）时，画册**跳过封底页**，正常导出，不阻断、不假造照片 | 与既有票根引擎"宁可省略不凑"的产品哲学一致；封面页理论上 `coverAssetId` 必然存在，若极端情况下文件不可读同样优雅跳过（退回现状：该照片留在正文池，不做剔除） |
| D-ABE-04 | 封面/封底都是**单卡宽度**独立页（`card_wh`），不跨页；封面固定为整本第 1 页，封底固定为整本最后 1 页，正文跨页排版逻辑不变 | 画幅与画册奇数张时的"孤卡半页"完全一致，保证全书页面宽度统一 |
| D-ABE-05 | 从画册正文候选池中剔除 `coverAssetId`/`closingAssetId` 这两张，**仅在 `album_spread` 分支内**生效 | `_poster_candidate_pairs` 返回的 pairs 是小红书/公众号/画册共享的上游数据，剔除操作只对画册分支内部过滤后的子集生效，不改变共享上游、不影响其余两个平台（对应 G-ABE-04） |
| D-ABE-06 | 新建独立模块 `travelogue/export/card_bookends.py`，提供 `render_cover_card()` / `render_closing_card()`，自带一份轻量 `_load_font()` 字体加载 helper | 不引入 export 层→render 层的反向依赖（对应 NG-ABE-01） |
| D-ABE-07 | 封面/封底渲染过程中任何异常（字体加载失败、图片损坏等）均捕获并跳过该页，绝不让整本画册导出失败 | 对应 G-ABE-05；与既有 `export_collage_pack` 的容错风格一致（渲染失败 → `writer.rollback()` + 抛 `LongshotExportError`，但**仅**限于正文渲染本身失败；封面/封底是"加分项"，失败不应拖累主体 |

### 4.2 页面结构与页序

```
第 1 页          第 2..N-1 页                最后 1 页
┌─────────┐   ┌───────┬───────┐   ...   ┌─────────┐
│  封面页  │   │ 正文Card│ 正文Card│         │  封底页  │
│ 图+标题  │   │ (跨页拼贴，逻辑不变)   │         │ 图+落款  │
└─────────┘   └───────┴───────┘         └─────────┘
   单卡宽度      现有跨页排版不变              单卡宽度
```

`pages_render` 组装顺序：

```python
pages_render = (
    ([cover_bytes] if cover_bytes else [])
    + body_pages          # 现有 CardGrouper → render_spread 逐跨页结果，不变
    + ([closing_bytes] if closing_bytes else [])
)
```

`PlatformExportWriter` 按现有逐页编号规则写盘（页 1..N），封面/封底天然落在编号首尾，与印刷装订顺序预期一致，**无需改动 writer 层**。

### 4.3 正文候选池排除（伪代码）

```python
# 仅在 pid == "album_spread" 分支内新增
cover_id = str(trip.get("coverAssetId") or "")
closing_id = str(trip.get("curation", {}).get("closingAssetId") or "")
exclude_ids = {aid for aid in (cover_id, closing_id) if aid}

body_pairs = [(p, a) for p, a in pairs if str(a.get("id") or "") not in exclude_ids]
body_paths = [p for p, _ in body_pairs]
# body_paths 替代原 paths 传入 _album_target_per_card / plan_cards
```

- `asset_lookup` 仍用原始（未过滤）的 `dict(pairs).get`，供正文 Card 渲染时按需查资产元数据；封面/封底自己单独按 id 查路径，不依赖这份 lookup。
- `_album_target_per_card(len(body_paths), ...)` 用**排除后**的正文数量计算目标张数/页数，保证"自动页数"估算不因这两张照片被抽走而产生偏差。

### 4.4 渲染实现要点（`card_bookends.py`）

- **封面**：photo cover-crop 铺满 `card_wh` → 底部渐变遮罩（黑色 alpha 从画布中线到底部线性递增，参考 `preview.py` 的 `ImageDraw` 逐行遮罩写法）→ `meta.title`（大字，居左下）→ 副标题（`subtitle`/`hook`，小字，标题下方）。
- **封底**：photo cover-crop 铺满 `card_wh` → 顶部或底部窄条压一层半透明底色 → 小字落款区：游记标题（极小字号）+ "THE END" 品牌标（更小字号，弱化处理）→ 画布边缘一条等距虚线（`draw.line` 循环画短横线段，间隔均匀）模拟票根撕边。
- CJK 字体栈复用 `preview.py` 同款兜底顺序：`msyh.ttc` → `msyhbd.ttc` → `simhei.ttf` → `NotoSerifSC-Regular.otf` → Pillow 默认字体（跨平台安全网，最差情况仍可渲染，只是字体退化为默认）。

### 4.5 `user_hint` / 页数文案

正文 `user_hint` 追加封面/封底说明，例如：

```
已生成 12 张画册页面（含封面 1 张 + 正文跨页拼贴 + 封底 1 张）
```

`page_count`/`target_page_count` 均按 `len(pages_render)` 计算，自然包含封面/封底，无需额外字段。

---

## 5. 与既有系统的关系

| 现有组件 | 影响 |
|----------|------|
| `export_collage_pack`（`travelogue/export/collage_pack.py`） | 仅 `album_spread` 分支新增：读取 `coverAssetId`/`closingAssetId` → 过滤正文池 → 渲染并拼装 `pages_render` 首尾。`xiaohongshu`/`wechat_official` 分支零改动 |
| `CardGrouper`/`plan_cards`/`CardRenderer` | **不改**——正文跨页排版逻辑完全复用现状，只是输入的照片池少了两张 |
| `_poster_candidate_pairs`（`poster_bric_pack.py`） | **不改**——仍返回完整候选池；过滤发生在 `collage_pack.py` 内部消费侧 |
| `PlatformExportWriter` | **不改**——仍按顺序写编号页，封面/封底天然落在首尾 |
| `travelogue/render/preview.py` | **不改，不被 import**——仅作为视觉手法参考，`card_bookends.py` 是独立实现 |
| Bookends 引擎（`cover_engine/api.py`） | **不改**——本 PRD 只读取其已产出的 `coverAssetId`/`closingAssetId`，不介入其决策逻辑 |

---

## 6. 验收标准

| 编号 | 内容 |
|------|------|
| AC-ABE-01 | 画册导出的第 1 页是封面页（封面图 + 标题 + 副标题/hook），画幅为单卡宽度 |
| AC-ABE-02 | 画册导出的最后 1 页是封底页（封底图 + 标题小字落款 + "THE END"品牌落款 + 虚线撕边），**不含**天数/地点/张数统计文字 |
| AC-ABE-03 | 封面/封底所用的两张照片，在画册正文的任意跨页中都不重复出现 |
| AC-ABE-04 | `closingAssetId` 为空的游记，画册导出仍正常完成，只是没有封底页，不报错、不阻断 |
| AC-ABE-05 | 小红书/公众号/单张海报三个平台的导出结果（页数/照片池/文件名）在本次改动前后完全一致（回归） |
| AC-ABE-06 | 封面/封底渲染过程中人为注入异常（如 mock 图片路径不存在），画册导出仍能正常完成，只是跳过对应页，不抛出 `LongshotExportError` |
| AC-ABE-07 | 画册"自动页数"估算（`_album_target_per_card`）按排除封面/封底后的正文照片数计算，不因这两张被抽走而产生偏差 |

---

## 7. 分阶段计划

1. **Stage 1**：新建 `travelogue/export/card_bookends.py`（`render_cover_card`/`render_closing_card` + 字体加载 helper），单测覆盖：有图有文案 / 无副标题 / 素材缺失异常捕获三种场景。
2. **Stage 2**：`collage_pack.py` 的 `album_spread` 分支接入——正文池排除逻辑 + `pages_render` 首尾拼装 + `user_hint` 文案更新。单测覆盖 AC-ABE-01～04/07。
3. **Stage 3**：回归验证小红书/公众号/单张海报三平台零变化（AC-ABE-05），真实素材（`demo-49cbe46479`）走一遍画册导出人工核对封面/封底视觉效果。

---

## 8. 开放问题

| 编号 | 问题 | 备注 |
|------|------|------|
| OQ-ABE-01 | 封底票根撕边是否需要升级为圆点齐洞纹理（细节感更强） | v1 明确用等距虚线（用户 2026-08-06 确认），留待真实素材视觉验证后再评估是否迭代 |
| OQ-ABE-02 | 封面/封底是否需要支持用户手动更换（而非固定读 `coverAssetId`/`closingAssetId`） | v1 不做，直接跟随 Bookends 引擎的既有决策；若后续用户反馈需要独立于 Web 封面单独选图，需另开 PRD |
| OQ-ABE-03 | `coverAssetId` 理论上必然存在，但若该素材恰好被后续编辑标记为 `culled`/`excluded`，是否仍应作为封面 | v1 直接信任 `coverAssetId` 字段值，不重新校验其 `layoutEligible` 等状态；若已被剔除但文件仍可读，按现状渲染，一致性问题留给 Bookends 引擎自身维护 |

---

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.2 | 2026-08-07 | 落地：`card_bookends.py` + `collage_pack` album 分支接入；AC-ABE-01～07 单测齐全；真材核对 `demo-album` / `demo-49cbe46479`（封面首页、封底末页、正文排除） |
| v0.1 | 2026-08-06 | 初稿：基于当日讨论（画册缺封面封底 → 拍板方案）落笔，明确复用手法而非跨层复用代码、封底排除统计文字改用极简落款+虚线撕边、`closingAssetId` 缺失时优雅跳过。尚未实施，等待排期 |
