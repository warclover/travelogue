# Travelogue · 双管线独立迭代 V1（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.1** |
| **状态** | **有条件通过（Conditional Go）** · 七席 BLK 已回写 · **实施勘误已落** · **W0 / W1 / W2 / W3 已合入** |
| **DOC-STATUS** | active |
| **评审** | [七席纪要 2026-08-22](./acceptance-records/dpi-dual-pipeline-isolation-v1-review-2026-08-22.md)（v0.2.0 · 7/7 Conditional Go） |
| **实施勘误** | 2026-08-22 开发负责人对照现网回写（本节 §0.3）。**不重开七席已拍的产品方向**；只改「按原文开工会当天红」的落点与出门口径 |
| **特性代号** | **DPI**（Dual Pipeline Isolation） |
| **文档类型** | 工程隔离合同（不含用户可见功能） |
| **触发来源** | 2026-08-22 双管线独立性核查：装配层已硬分叉，但渲染壳 / CSS / LTE 编译器 / 导出入口仍同居一处；PFM 为锁 16:9 已改过游记侧的 contain 选择器与 LTE CSS 编译器 |
| **上游合同** | [PRD-PORTFOLIO-FOLIO-MODE-V1.md](./PRD-PORTFOLIO-FOLIO-MODE-V1.md)（**PFM**）· [PRD-MAGAZINE-SERIES-PROMOTION-V1.md](./PRD-MAGAZINE-SERIES-PROMOTION-V1.md)（**MSP**）· [PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md](./PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（**TSU**） |
| **不废止** | PFM 的身份字段、分叉点、导出形态、ISO-01～07 一律不改；本文只加护栏与分家，不改任何产品行为 |
| **不改** | 用户可见行为（游记与作品集成品逐字一致）· `layoutEngine` 枚举 · `trip.studio.edition` 语义 · 上游 ingest/cull/cluster/开章共用 |
| **更新日期** | 2026-08-22 |

> **一句话目标**：让「游记（web 长图 / 微信长图）」与「作品集（画册）」两条管线以后各自迭代时，**改一边不需要读另一边的代码，也不可能静默改坏另一边的成品**；靠的是所有权边界 + 机器门禁 + 分编译，而不是靠人记住铁律。
>
> **产品铁律**
>
> 1. **零行为变更。** 本波是纯工程波。CI 出门门是**形状断言 + `render_fingerprint` 字段级**（D-DPI-01）。归一化字节比对是 W1 之后的本地/狗粮核对，不进 `test-pr` 硬门。
> 2. **共享到「照片和章边界」为止。** ingest / cull / cluster / SSG / 开章 / 封面继续共用；**「怎么铺到纸上」必须分家**。共享的定义含**测试夹具**（§4.3）。
> 3. **产物层也要隔离。** 只要成品里还留着一个横跨两条管线的共享哈希，隔离就是名义的（D-DPI-16）。
> 4. **不拆已经对的东西。** 不加 `layoutEngine` 第三值（PFM D-PFM-04）、不复制 `curate.py`、不做两套 ingest、不把 `chapters[]` 拆开。
> 5. **门禁先行。** W0 一行业务代码都不搬，先把「改坏对方」变成 CI 红灯。没有门禁的重构等于换一种方式漂。
> 6. **窄缝要有名字。** 允许两边共同触碰的文件是**有限的、列举出来的**；碰窄缝的 PR 必须双边回归。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §0 | 术语、禁用标识符、**v0.2.1 实施勘误** |
| §1 | 现状实测：哪些已经真隔离、哪些还同居（含行号级事实） |
| §2 | 目标 / 非目标 / 与 PFM 的边界 |
| §3 | 已拍板决策 D-DPI-01～17 |
| §4 | 所有权地图：三层独占 + 窄缝清单 + 夹具所有权 |
| §5 | CSS / LTE 分编译（本波最大一块） |
| §6 | 渲染 builder 分家 |
| §7 | 导出入口改纯分发 |
| §8 | 隔离门禁（新增 CI 与测试包） |
| §9 | 前端任务 |
| §10 | 会被改红的既有测试、文档与产物 |
| §11 | 任务表与里程碑（含七席放行条件；**W0 开工清单以 §0.3 为准**） |
| §12 | 验收 AC-DPI-01～24 |
| §13 | 风险 R-DPI-* · OQ 裁决 · **不做的代价（实证）** |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **游记管线** | `edition=journal`（缺省）。装配走 `compose_trip`（mosaic），版式为 `screen-*`。两个读者面：**web 长图**（`exportLayout=web/auto`）与**微信长图**（`exportLayout=longshot`） |
| **作品集管线** | `edition=portfolio`。装配走 `compose_portfolio_trip`（`editorial_series`），版式为 `page-*`，16:9 纸面 |
| **窄缝（seam）** | 两条管线都会经过、且**必须**共用的极少数文件或函数。窄缝是登记制，不是默认 |
| **分家（split）** | 把同一文件里的双管线分支拆成两个入口，各自独占一份实现 |
| **分编译（split codegen）** | LTE 把 `screen-*` 与 `page-*` 编译进**两份**产物 CSS，读者面按身份只加载其中一份 |
| **形状断言（shape assertion）** | 断言渲染 HTML 里该有/不该有哪些 `data-block` / `data-pattern` / `data-edition` 节点，而不是比像素 |
| **缓存指纹（`?v=`）** | `render/context.py` `_longshot_bundle_version` 对前端资源做 SHA256 后写进 HTML 资源 URL 的版本参数。**现为全局单一哈希，本波要按管线分算**（D-DPI-16） |
| **归一化字节比对** | 把 HTML 里的 `?v=<hash>` 替换成固定占位符后再做字节级 diff。**本地/狗粮核对用，不进 `test-pr` 硬门**（D-DPI-01） |
| **棘轮（ratchet）** | lint 把现网已有命中写入 grandfather 基线，只拦**新增**越界。W0 所有权 lint 必须是棘轮，不能按最终态 fail-closed |

### 0.2 禁用标识符（沿用 PFM D-PFM-01）

`folio`、`surface` 已各有四义 / 一义，**本波不得**复用为隔离相关的字段名、文件名或函数名。本波新增标识符统一用 `journal_*` / `portfolio_*` 前缀。

### 0.3 实施勘误（v0.2.1 · 2026-08-22）

对照现网代码回写。七席已拍的方向（分编译、指纹分算、门禁先行、`journal.css` 不分家、不删 `page-` 前缀嗅探）**不重开**。本表改的是「按 v0.2.0 原文开工会当天红、或门会空转」的落点。后文合同以本表为准。

| ID | v0.2.0 原文 | 现网事实 | v0.2.1 合同 |
|----|-------------|---------|-------------|
| **IE-DPI-01** | §8.3 所有权 lint 按最终态 fail-closed：表外出现 `is_portfolio` / `page-` 即红 | `chapters.py` 10 处、`surface.py:91-102`、`output_recipe/resolve.py`、Studio handlers、`journal-screens.css` 满篇 `page-*` 都还没搬走 | **W0 做成棘轮**：现有命中进 grandfather（owner + expiry）；只拦新增。W0 **不扫 CSS 文本**里的 `page-`（W1 步 2 之后再开）。`config/edition.py`、`export/portfolio_*.py`、`web/studio_*` 进允许清单 |
| **IE-DPI-02** | §4.3 把 `trip.render_golden.json` 标成游记独占；AC-DPI-22 禁作品集读它 | `test_portfolio_body_copy.py`、`test_editorial_ac_regression.py`、`test_reading_profile.py:140` 都是克隆这份 golden 再注入 `edition=portfolio` | **改为共享基线**。游记独占只留 `tests/fixtures/phase16-dogfood/**`；作品集独占只留 `tests/unit/layout_engine/fixtures/editorial_series/**`。跨身份复用 golden 合法；重新生成共享夹具才要求双边回归 |
| **IE-DPI-03** | BE-DPI-06 / §8.5 在 W0 接 `export --sync-portfolio` | `cli.py:99-119` 无该旗标，也无 `portfolio-pages.css` | **W0 只接 ownership lint**。双漂移门与 BE-DPI-07 同一提交进 W1 |
| **IE-DPI-04** | BE-DPI-04 在 W0 为还不存在的 `journal_chapters` / `portfolio_chapters` 加 import-linter 空壳 | `lint-imports` 要求模块可导入；空壳会被 ownership lint 扫到，W2 还要再改路径 | **契约跟 W2 拆文件同一提交加**。W0 只保证既有 4 条契约文本零 diff |
| **IE-DPI-05** | AC-DPI-08 钉 `trips/demo-81d3442e92` | 该 demo 不在 git；`trips/` 无入库 trip | 作品集出门门改走 **golden + 注入 `edition=portfolio` + `tmp_path` 渲染**（与 `test_portfolio_body_copy.py` 同构）。本地 demo 只做狗粮，不当 CI 硬门 |
| **IE-DPI-06** | §11.2 写 BE-DPI-21 必须最先；§5.2 把它放在第 4 步 | 指纹分算的「作品集 `?v=` 必变」需要 `portfolio-pages.css` 先存在 | **跟 §5.2**：先有新文件 → 再分算哈希 → 再切加载。只改**拷贝后**的 `journal.css` `@import`，不改仓库源文件第 7 行 |
| **IE-DPI-07** | BE-DPI-18 扩 `css_stale.py` 的 grid class 扫描，缺文件算陈旧 | `_screens_use_solid_geometry` 为真则永不算陈旧；CSS 文件缺失也 `return False`。P16 之后几何固化是常态 | 陈旧信号改成**加载关系**：游记 `@import` 须指向 `journal-screens.css`；作品集须指向 `portfolio-pages.css` 且文件存在。缺 / 指错 → 陈旧 |
| **IE-DPI-08** | AC-DPI-07/08/20 把整页字节 diff 与 Playwright 截图当出门硬门 | 现网渲染测试是形状断言；`test-pr` 排除 `playwright_serial` | **CI 硬门 = 形状 + `render_fingerprint` + CSS 文件名/`@import` 目标**。归一化字节比对、`--screenshot --strict` 留本地 / nightly / 狗粮，不挡 merge |
| **IE-DPI-09** | D-DPI-13 `chapters.py` 留薄分发；S-04 / AC-DPI-12 又说唯一分发在 `assemble.py` | 两处都留 `if` 会立刻占两条窄缝，调用方要猜进哪扇门 | **`assemble.py` 只留那一处 `if`。** `chapters.py` 变为游记 builder 的稳定导入名（re-export），不留第二处分发。`surface.py` 的 `portfolio_body` W2 迁进 `portfolio_chapters`，W0 进 grandfather |
| **IE-DPI-10** | §8.2 W0 形状断言含「CSS 加载文件名」 | `portfolio-pages.css` W1 才出现 | W0 只断言 edition / pattern / chapter-header。**CSS 文件名断言跟 FE-DPI-05 进 W1** |

**W0 开工清单（本版）**：BE-DPI-01 / 02 / 03 / 05 / 06（仅 ownership lint）/ 19、FE-DPI-04。**不进 W0**：`--sync-portfolio`、import-linter 空壳、扫 CSS `page-`、夹具方向误伤 golden。

---

## 1. 现状实测盘点（2026-08-22 实跑，非估计）

### 1.1 已经真隔离的部分（**不要重做**）

| 层 | 现状 | 证据 |
|----|------|------|
| 身份 | `trip.studio.edition`，缺省即游记；游记不写该字段 | `travelogue/config/edition.py:89` `is_portfolio_trip`；`is_portfolio_trip({}) is False` |
| 装配分叉 | `curate.py` 在 `compose_trip` 之前二分；作品集失败硬报，禁止静默掉回 | `travelogue/curation/curate.py:1361-1394` |
| 包边界 | mosaic / `layout_templates` **禁止** import `editorial_series` | `pyproject.toml:165-177` 契约「PFM editorial_series isolation (D-U-15 / ISO-05)」· 实跑 **4 kept / 0 broken** |
| 门面 | `layout_engine/api.py` 不导出 `editorial_series`；mosaic 源码无 `slot_match` / `fill_groups` | `tests/unit/layout_engine/test_editorial_slot_match.py:258`、`test_editorial_fill.py:298-303` |
| 选型核 | `page-*` 被排除出 MCS 候选 | `travelogue/layout_templates/registry.py:356-359` |
| 指纹 | 游记 `render_fingerprint` 不含 `edition` / 旗标 | `tests/unit/layout_engine/test_pfm_render_fingerprint.py` |
| 导出旁路 | 作品集不进 Output Recipe 意图矩阵；游记逐字不变 | `travelogue/export/output_recipe/resolve.py:82-121` |
| 换种分享 | 作品集 × 微信群走 kept 竖条，禁止 flatten `page-*` | `travelogue/export/longshot.py:1170-1183`（ISO-04） |

**结论：装配层是硬分叉，`mosaic/` 与 `compose_trip` 相对 master 零 diff。** 本 PRD 不动这一层。

### 1.2 仍然同居的部分（本波要处置）

#### (a) CSS 同居在一份文件里 —— 最大风险

`templates/visual-journal/journal-screens.css` 共 **5831 行**，三段结构：

| 行区间 | 内容 | 谁在写 |
|--------|------|--------|
| 1–187 | 手写头部。**含 PFM 的 `page-*` 16:9 舞台规则（147–186）与 `html[data-edition="portfolio"] .chapter`（184–186）** | 作品集写在了游记文件里 |
| 188–3624 | `@lte-generated` 块（YAML→CSS 权威） | **`screen-*` 与 75 张 `page-*` 混编** |
| 3626–5831 | `@journal-overlays` 块 | 游记手写覆盖 |

`templates/visual-journal/journal-screens-overlays.css`（2204 行）经检索**无** `page-*` / `data-edition` 规则。

第 147–149 行的注释已经把问题写在脸上：

```
/* PFM · page-* magazine stage: 16:9 one screen. Gutters live in YAML tracks
 * (atelier faces.js); journal --rhythm-l0-gap must not shrink those cells.
 * Must stay outside @lte-generated so sync does not drop it. */
```

**更严重的是反向污染已经发生**：为了让 `page-*` 锁住 16:9，游记侧的 contain 选择器被追加了 `:not([data-pattern^="page-"])`。该 `:not()` 出现在 `journal-screens.css` 的 **3846–4030** 等多处长选择器上。今天靠 `screen-*` 仍命中原规则而无害，但**每一条游记选择器都已经背上了作品集的负担**。

#### (b) LTE CSS 编译器已被作品集改写

`travelogue/layout_templates/css_gen.py:153-159`：

```
    # Always emit slot placement. 1-slot journal primitives used a 1×1 stage
    # (auto-place filled the only cell). page-1-hero-* keep gutter tracks, so
    # skipping placement parks the photo in the top-left margin (~6% cell).
```

原逻辑是「1 槽 primitive 不输出 slot placement」（游记语义）。为了 `page-1-hero-*` 的 gutter 轨道，改成一律输出。**游记 1 槽模板目前碰巧仍是 1×1 舞台，所以没炸。** 同一提交还放宽了 `validate_css_bundle` 的覆盖校验条件（`multi_track`），以及 `validator.py` 的密页冻结豁免（`_dense_freeze_exempt`，`page-*` 前缀直接放行 R-A3 冻结）。

**这是典型的「改画册，动到游记编译器」。** 以后任一边改 primitive 或密页策略，都会静默影响对方。

#### (c) 渲染层堆了约十处身份分支

`travelogue/render/chapters.py`（526 行）里 `is_portfolio` 出现在 **70 / 74–75 / 125 / 135 / 175 / 271 / 353 / 446 / 476 / 506** —— 覆盖高光注入、卷轴呼吸屏、强制 screens、藏章头、trip-index、folio 计划。另有：

| 文件 | 行 | 分支 |
|------|----|------|
| `render/surface.py` | 91–102 | `portfolio_body` → `strip_narrative_copy` |
| `render/assemble.py` | 436–439 | 戳 `data-edition="portfolio"` |
| `render/context.py` | 816–824 | `is_page_face` → 16:9 舞台，不继承游记 viewport-fit |
| `render/reading_profile.py` | 392–395 | 作品集默认 `magazine` |
| `templates/visual-journal/partials/chapter.hbs` | 1 / 3 / 26 | `hideChapterChrome` 包住整段章头 |

再迭代两次，「改游记长图」就必须先读懂作品集例外。

#### (d) 导出入口在膨胀

`export_trip_longshot`（`travelogue/export/longshot.py:1105`）已经为作品集加了两个参数（`include_zip`、`include_pages`）与两处身份分支，`LongshotExportResult` 也加了 `skipped_pages` / `share_zip` 两个作品集专用字段。这个函数名义上是「微信长图」。

#### (e) 没有所有权与门禁

- 仓库**无** `.cursor/rules/`、**无** `CODEOWNERS`、**无** `AGENTS.md`
- 现有隔离测试散落在 8 个文件里，**没有任何一条命令能一次跑完**
- `pyproject.toml:41-50` 的 10 个 pytest marker 里**没有**隔离 mark
- **完全缺失**：游记 web 与游记微信长图的 HTML 形状断言。上次核查是靠临时探针脚本才确认章头与 `media-card` 仍在
- **夹具层完全未隔离**：`tests/fixtures/phase16-dogfood` 被 `phase16_template_eval.py`、`phase17_golden_metrics.py` 等多个门读；作品集夹具在 `tests/unit/layout_engine/fixtures/editorial_series/`。两条管线可以通过共享测试数据重新耦合，而这种耦合 **lint 看不见**（MSP BLK-MSP-03 刚处理过一次夹具同名冲突）

#### 未登记的窄缝

`layout_engine/mosaic/render_check.py:15-17` 与 `layout_engine/render_binding.py:10` 都在**游记侧包内**硬编码 `templates/visual-journal/journal-screens.css` 路径，且与 `travelogue/paths.py:263` 的 `JOURNAL_SCREENS_CSS` 常量重复定义。处置见 §4.2 说明。

#### (f) 产物加载不分身份

`travelogue/render/engine.py:599` 只拷两份 CSS（`journal.css` + `journal-screens.css`），`journal.css` 内 `@import` 带 cache-bust；`export/packager.py:178-181` 同样两份。**作品集 trip 也会拿到全部 `screen-*` 规则；游记 trip 也会拿到全部 75 张 `page-*` 规则。**

#### (g) 缓存指纹是一个横跨两条管线的全局哈希 —— **最深的一处耦合**

`travelogue/render/context.py:53-69`：

```python
_BUNDLE_VERSION_PATHS = (
    JOURNAL_CSS,
    JOURNAL_SCREENS_CSS,
    BREATH_JS, ...          # 共 15 项
)
```

`_longshot_bundle_version` 把这 15 个文件的字节一起做 SHA256，取前若干位写进**每张 HTML** 的 `?v=`。`engine.py:605-617` 还专门为 `journal.css` 里的静态 `@import` 补了一次 cache-bust 重写，注释写明「否则浏览器会一直吃旧的 `journal-screens.css`」——说明这个坑已经踩过。

两个后果：

1. **「字节级一致」物理上不可能**：本波正是要改 `journal-screens.css`，改了哈希就变，HTML 字节必然变。
2. **分家后两条路都在造新耦合**：`portfolio-pages.css` 加进这个列表 → 改作品集 CSS 会 bump 游记 HTML 的字节；不加进去 → 作品集 CSS 更新后浏览器吃旧缓存。

处置见 **D-DPI-16**。这是本波唯一的方向级前置项。

#### (h) 产物是三份，不是两份

`travelogue/layout_templates/cli.py:101`：`export --out` 缺省落 `travelogue/layout_templates/journal-screens.generated.css`（3434 行，**含全部 `page-*`**）。`docs/GUIDE-PHASE16-layout-template-engine.md:159` 把它列为正式输出，MSP §710 列「重生成」。处置见 **D-DPI-17**。

#### (i) LTE 的 CSS 一致性校验会在分家后静默空转

`css_gen.py:232-243`：

```python
    expected = parsed.get(template.render_grid_class)
    if expected:
        ...  # 只有在 journal CSS 里找到同名 grid class 才比对
```

`page-*` 规则一旦搬出 `journal-screens.css`，这 75 张脸的 `expected` 全为 `None` → **校验被静默跳过**，而 `validator.py:450` 与 `mosaic/render_check.py:50` 两个调用点都走这条。`cli validate --semantic` 会照样绿。

#### (j) 防重复机制依赖 marker，新文件天生在审计视野之外

`css_gen.py:409-415` 的 `lte_grid_classes_outside_marker` 先找 `LTE_MARKER_START/END`，**找不到直接 `return []`**；`scripts/lte_journal_css_audit.py:43` 默认只扫 `journal-screens.css`；`tests/unit/layout_engine/test_lte_css_sync.py:66` 同。

**今天 147–186 那段越界手写块之所以能长期存在、注释还大方写着「Must stay outside @lte-generated」，正是因为它在审计视野之外。** 不能把同一个坑复制到新文件。

---

## 2. 目标 / 非目标

### 2.1 目标

| 序 | 目标 |
|----|------|
| **G-DPI-01** | 改一边的版式 / 几何 / 读者面，**不需要打开**另一边的文件 |
| **G-DPI-02** | 误伤对方在 **PR 阶段红灯**，而不是狗粮时才被用户发现 |
| **G-DPI-03** | 每条管线的读者面产物**只加载自己的 CSS** |
| **G-DPI-04** | LTE 对两族版式**分别编译、分别校验**，一族的策略变更不落到另一族 |
| **G-DPI-05** | 窄缝清单是**可枚举、可审计**的，且随代码演进由机器校对 |
| **G-DPI-06** | **下一次动到任一管线读者面（渲染 / CSS / 版式几何）的功能波开工前，W0 必须已合入。** W1–W3 允许延后，但每次延后须在本 PRD 状态行记一次 |
| **G-DPI-07** | 两条管线的**成品产物**互不影响：改一边的 CSS 不改另一边 HTML 的任何字节（含缓存指纹） |

### 2.2 非目标（本波明确不做）

| 序 | 非目标 | 原因 |
|----|--------|------|
| **N-DPI-01** | 新增 `layoutEngine` 第三个值 | PFM D-PFM-04 / BLK-PFM-02 已否；产出同构 `screens[]` |
| **N-DPI-02** | 复制 `curate.py` 或做两套 ingest / cull / cluster | 上游共用是 PFM D-PFM-03 的设计，不是债 |
| **N-DPI-03** | 重切 `chapters[]` 或改章边界 | PFM D-PFM-14；读者面藏章头已足够 |
| **N-DPI-04** | 任何用户可见行为变更（含选档、兑现率、文案、页数芯片） | 本波是纯工程波；兑现率归 MSP |
| **N-DPI-05** | 松绑或改写现有 import-linter 契约文本 | MSP BLK-MSP-01 明令；本波只**新增**契约 |
| **N-DPI-06** | 运行时读 `docs/templates/reserve/` | ISO-05 不变 |
| **N-DPI-07** | 拆 `render/context.py`（1414 行）整体 | 只处置 `is_page_face` 一处窄缝，全拆是另一波 |
| **N-DPI-08** | 拆分 `curate.py`（2014 行，已在 god-module 棘轮内） | 分叉点只有一处 `if`，不构成隔离风险 |
| **N-DPI-09** | 给作品集复制一整套 `templates/visual-journal/` | 壳同构是 PFM 的设计；只分 partial 与 CSS |
| **N-DPI-10** | 引入 monorepo / 多包 / 独立仓 | 单人项目，收益远小于代价 |

### 2.3 与 PFM / MSP / TSU 的边界

| 主题 | 归谁 |
|------|------|
| 身份字段、分叉点、导出形态、ISO-01～07 | **PFM**（本文不改，只加机器校验） |
| 档位、页序兑现率、`photo_span` / `capacity` | **MSP**（本文不碰） |
| `page-*` 几何设计、`/series-editor` | **TSU**（本文只管编译与加载分家） |
| 所有权、门禁、分编译、builder 分家 | **本文 DPI** |

---

## 3. 已拍板决策

> 七席已签 v0.2.0。**v0.2.1 实施勘误（§0.3）覆盖落点与出门口径**；产品方向以 D 表为准，实施不得自行改判。

### 3.1 原则

| ID | 决策 |
|----|------|
| **D-DPI-01** | **零行为变更铁律（v0.2.1 · IE-DPI-08）。** CI 出门门是：① §8.2 形状断言；② `render_fingerprint` 字段级（AC-DPI-09）；③ W1 起加上 CSS 文件名 / `@import` 目标（AC-DPI-14）。<br>归一化 `?v=` 后的整页字节比对、Playwright 截图是 **W1 之后的本地 / nightly / 狗粮核对**，**不进 `test-pr` 硬门**。缓存指纹本身由 **D-DPI-16 / AC-DPI-18** 单独立判据。<br>CSS 允许「拆成两份」的结构性 diff，但游记 `screen-*` **有效规则集合**必须等价（AC-DPI-06）。 |
| **D-DPI-02** | **共享边界固定在「照片与章边界」。** 上游（ingest / cull / cluster / SSG / 开章 / 封面 CAL·ABE / Studio 壳 / 预览服务器）**继续共用且不得分家**；下游（版式、几何、读者面 CSS、导出成品）**必须分家**。<br>「共享」的定义**含测试夹具与金样**（§4.3）：代码分家了，但两条管线仍可通过共享测试数据重新耦合，而这种耦合 lint 看不见 |
| **D-DPI-03** | **窄缝登记制。** 允许双管线共同触碰的文件与函数写进 `docs/dual-pipeline-ownership.md` 的窄缝表，由 `scripts/lint_dual_pipeline_ownership.py` 校验。**表外文件不得含双管线分支**。<br>窄缝上限 **14 条**（现表 10 条 + 余量）。上限是**讨论触发器，不是配额**：触顶必须开 PRD 复核，不得静默扩表 |
| **D-DPI-04** | **门禁先行（v0.2.1）。** W0 不搬业务逻辑，只落：marker、形状断言、**棘轮型** ownership lint、所有权文档、FE 面板快照、BE-DPI-19 改 import 来源。<br>**W0 明确不做**：`--sync-portfolio`（IE-DPI-03）、import-linter 空壳（IE-DPI-04）、扫 CSS `page-`（IE-DPI-01）。W1 起才动 CSS / 加载关系 |
| **D-DPI-05** | **只加契约，不改旧契约。** 新增 import-linter 契约与 lint 脚本；`pyproject.toml` 既有 4 条契约文本**零 diff**（沿用 MSP AC-MSP-25 口径） |

### 3.2 所有权

| ID | 决策 |
|----|------|
| **D-DPI-06** | **三层独占。** 装配 / 模板 / 读者面 CSS 三层各自独占（§4.1）。游记 PR 不得改 `editorial_series/`、`page-*.yaml`、作品集 CSS 包；作品集 PR 不得改 `mosaic/`、`screen-*.yaml`、游记 CSS 包 |
| **D-DPI-07** | **规则落两处。** `.cursor/rules/dual-pipeline.mdc`（给 AI 与本人）+ `docs/dual-pipeline-ownership.md`（给机器与评审）。**不引入 CODEOWNERS**（单人仓无评审人可指派，形式主义） |

### 3.3 CSS 与 LTE

| ID | 决策 |
|----|------|
| **D-DPI-08** | **分编译两份产物。** LTE `export` 按 id 前缀分流：`screen-*` → `journal-screens.css` 的 `@lte-generated` 块（现状不变）；`page-*` → **新文件** `templates/visual-journal/portfolio-pages.css`。游记文件里**一张 `page-*` 规则都不留** |
| **D-DPI-09** | **手写规则跟着搬。** 现 `journal-screens.css:147-186` 的 `page-*` 舞台规则与 `html[data-edition="portfolio"] .chapter` 迁入 `portfolio-pages.css` 的手写头部 |
| **D-DPI-10** | **游记选择器卸下负担。** `page-*` 规则搬走后，删除游记 contain 选择器上的 `:not([data-pattern^="page-"])`。删除前后必须证明游记 `screen-*` 有效规则集合等价（AC-DPI-06） |
| **D-DPI-11** | **按身份加载（v0.2.1 · IE-DPI-06）。** 作品集 trip 产物加载 `journal.css` + `portfolio-pages.css`；游记 trip 加载 `journal.css` + `journal-screens.css`。<br>**只改拷贝后的** `journal.css` `@import` 文件名与 `?v=`（`engine.py:605-617` 已有 cache-bust 重写）。**禁止**改仓库源 `templates/visual-journal/journal.css` 第 7 行。zip 打包同步（`packager.py`） |
| **D-DPI-12** | **编译策略分族。** `css_gen.py` 的 slot placement 策略、`validate_css_bundle` 覆盖校验、`validator.py` 密页冻结，按 `screen-*` / `page-*` **分族参数化**，不再用「一律输出」这种全局改写。游记族恢复改动前语义（1 槽 1×1 primitive 不输出 placement），并用回归证明产物零 diff。<br>`page-*` 的槽数**阈值本波不动**（归 TSU）：只把 `_dense_freeze_exempt` 的前缀豁免升级为显式族参数，数值不变 |
| **D-DPI-16** | **缓存指纹按管线分算（方向级 · BLK-DPI-01）。** `_longshot_bundle_version`（`render/context.py:53-69`）现为横跨两条管线的全局哈希。改为按身份计算：游记 HTML 只摘要游记实际加载的文件（`journal.css` + `journal-screens.css` + 游记 JS/CSS）；作品集只摘要自己那份（`journal.css` + `portfolio-pages.css` + 共享 JS）。<br>**禁止**把 `portfolio-pages.css` 塞进游记哈希列表（改作品集会动游记产物字节）；**也禁止**不塞（作品集 CSS 更新后吃旧缓存，`engine.py:605-607` 已踩过一次）。<br>本条是 **W1 的前置**：不定它，W1 的出门判据无法成立 |
| **D-DPI-17** | **第三份产物废弃（优先）或分家。** `layout_templates/cli.py:101` 的 `export --out` 缺省产物 `journal-screens.generated.css` 含全部 `page-*`。**优先方案**：全库检索确认无运行时消费者后**废弃**，并同步 `docs/GUIDE-PHASE16-layout-template-engine.md:159` 与 MSP §710。<br>若检索发现仍有消费者，则退回分家方案（`*-journal.generated.css` / `*-portfolio.generated.css`）。少一份产物少一处漂移源 |

### 3.4 渲染与导出

| ID | 决策 |
|----|------|
| **D-DPI-13** | **两个 builder（v0.2.1 · IE-DPI-09）。** 拆成 `journal_chapters.py` 与 `portfolio_chapters.py`。**唯一分发点在 `assemble.py`**（S-04 那一处 `if`）。`chapters.py` 变为游记 builder 的稳定导入名（re-export `build_chapters_render_context`），**不留第二处 `if is_portfolio_trip`**。`surface.py` 的 `portfolio_body` 一并迁进 `portfolio_chapters` |
| **D-DPI-14** | **partial 分家。** 新增 `partials/chapter-portfolio.hbs`（无章头分支）；`chapter.hbs` 恢复到 PFM 之前的形状（去掉 `hideChapterChrome` 与 `chapter--folio-body`）。模板选择由 builder 决定 |
| **D-DPI-15** | **导出改纯分发。** 新增 `travelogue/export/dispatch.py`：按 `(platform, edition)` 选 writer。`export_trip_longshot` 收回成「只做微信群竖条」，**移除** `include_zip` / `include_pages` 参数与两处身份分支；`LongshotExportResult` 的 `skipped_pages` / `share_zip` 迁到作品集自己的结果类型。CLI / Studio handler 改调 dispatch |

---

## 4. 所有权地图

### 4.1 三层独占

| 层 | 游记独占 | 作品集独占 | 共用（不分家） |
|----|----------|-----------|---------------|
| **上游** | — | — | `ingest/`、`curation/photo_cull.py`、聚类、SSG、开章、`cover_engine/` |
| **装配** | `layout_engine/mosaic/**`、`layout_engine/api.py`、`compose_trip` | `layout_engine/editorial_series/**` | — |
| **模板** | `layout_templates/templates/screen-*.yaml`、mosaic 活跃集 | `layout_templates/templates/page-*.yaml`、`editorial_series/series/*.yaml` | LTE 校验框架（分族参数化后） |
| **读者面 Python** | `render/journal_chapters.py` | `render/portfolio_chapters.py` | `render/assemble.py`（薄分发）、`render/surface.py` |
| **读者面模板** | `partials/chapter.hbs` | `partials/chapter-portfolio.hbs` | `layout-screen.hbs`、`media-card.hbs` 等原子 partial |
| **读者面 CSS** | `journal-screens.css`、`journal-screens-overlays.css` | `portfolio-pages.css` | `journal.css`（壳与变量） |
| **导出** | `export/longshot.py`（微信竖条）、`platform_longshot.py`、`collage_pack.py` | `export/portfolio_pages.py`、`portfolio_wechat.py` | `export/dispatch.py`、`packager.py` |
| **前端** | 游记 Dock / 六平台面板 | `portfolio-*-logic.js` | `dock.js` 分发、`features.js` 卡片壳 |

### 4.2 窄缝清单（**唯一**允许含双管线分支的地方）

| 窄缝 | 文件 : 位置 | 允许的分支形态 |
|------|------------|---------------|
| **S-01 装配分叉** | `curation/curate.py:1361` | 一处 `if is_portfolio_trip(trip)` 二选一调用 |
| **S-02 呼吸屏门** | `curation/curate.py:1845` | 一处 `if not is_portfolio_trip(trip)` |
| **S-03 高光门** | `curation/moment_scoring.py:604` | 一处早退 |
| **S-04 渲染分发** | `render/assemble.py` | 一处二选一调 builder + 一处 `data-edition` 戳记 |
| **S-05 阅读档** | `render/reading_profile.py:392` | 一处默认 profile 选择 |
| **S-06 舞台** | `render/context.py:816` | 一处 `is_page_face` 分支（等 §6.3 收敛后可撤） |
| **S-07 导出分发** | `export/dispatch.py` | 按 `(platform, edition)` 的分发表 |
| **S-08 校验** | `services/validate.py:76` | 一处 `patternId` 语义放行 |
| **S-09 FE 分发** | `templates/studio/preview-toolbar/dock.js` | 一处 `data-edition` 挂载 + 一处面板分发 |
| **S-10 LTE 分族** | `layout_templates/css_gen.py`、`validator.py` | 按 id 前缀取族参数（**不得**含具体版式 id 硬编码） |

**上限 14 条**（D-DPI-03）。现 10 条，余量 4。Studio 壳与身份模块**不占额度**（见允许清单）。

**允许清单（不算越界，不占窄缝额度）**

| 路径 | 理由 |
|------|------|
| `travelogue/config/edition.py` | 身份定义本身 |
| `travelogue/export/portfolio_*.py` | 作品集独占实现 |
| `travelogue/web/studio_*.py`、`web/studio_handlers/**` | Studio 壳，D-DPI-02 明文共用 |
| `travelogue/cli/render_cmds.py` | 调用点；W2 迁到 dispatch 后从允许清单拿掉身份分支 |

**规则（v0.2.1 · IE-DPI-01）**：W0 lint 是**棘轮**——现有命中进 `dpi-seam-baseline.json` 的 `grandfather`（owner + expiry），只拦新增。W0 **不扫 CSS 文本**里的 `page-`。改窄缝或改 grandfather 的 PR → 必跑双边隔离包（§8）。

**W2 必须从 grandfather 删掉的项**：`render/chapters.py` 全部 `is_portfolio`、`render/surface.py` 的 `portfolio_body`、`export/longshot.py` 的身份分支（迁到 S-07）。

#### 两处待处置的重复定义（评审 BLK-DPI-07）

`layout_engine/mosaic/render_check.py:15-17` 与 `layout_engine/render_binding.py:10` 在游记侧包内硬编码共享 CSS 路径，且与 `travelogue/paths.py:263` 的 `JOURNAL_SCREENS_CSS` 常量重复定义。

**处置（首选）**：两处改为 `from travelogue.paths import JOURNAL_SCREENS_CSS`。它们只读游记文件（`render_check.py:30` 已过滤 `startswith("screen-")`），属游记独占，消除重复定义后**不占窄缝额度**。若本波不改，则须登记为 S-11 / S-12（额度降至 12/14）。

### 4.3 夹具与金样所有权（评审 BLK-DPI-12 新增）

代码分家不等于隔离完成。两条管线仍可通过**共享测试数据**重新耦合，而这种耦合 import-linter 与 ownership lint 都看不见。

| 类别 | 游记独占 | 作品集独占 | 共享（身份中立） |
|------|----------|-----------|-----------------|
| **trip 夹具** | `tests/fixtures/phase16-dogfood/**` | `tests/unit/layout_engine/fixtures/editorial_series/**` | **`schemas/fixtures/trip.render_golden.json`**、`trip.linzhi_screens.json`、`trip.example.json` |
| **金样指标** | `docs/acceptance-records/phase9-eval-baseline.json`、P16/P17 golden metrics | 作品集 `sequenceFulfillment` 基线 | — |
| **棘轮基线** | LSE / god-module / facade 基线 | — | `dpi-seam-baseline.json`（本波新增） |

**规则（v0.2.1 · IE-DPI-02）**：

1. **谁的金样谁改。** 游记 PR 不得重新生成作品集独占夹具，反之亦然。
2. **重新生成共享夹具的 PR 必须双边回归。**
3. 跨身份**克隆** `trip.render_golden.json` 再注入 `edition` 是现网标准写法，**合法**，AC-DPI-22 不得判红。
4. 夹具方向门只拦「作品集测试读 `phase16-dogfood`」与「游记测试读 `editorial_series` 夹具」。

先例：MSP **BLK-MSP-03** 处理过一次 `magazine-8-standard` 夹具与真书同名冲突，两本会在排障时长期互相冒充。夹具冲突的排查成本高于代码冲突。

---

## 5. CSS / LTE 分编译

### 5.1 目标态

```
templates/visual-journal/
  journal.css                     壳 + 变量 + 字体（唯一双管线共享的读者面 CSS）
                                  @import 由渲染侧按身份注入；顶部须加共享声明注释
  journal-screens.css             游记：手写头部 + @lte-generated(screen-*) + @journal-overlays
  journal-screens-overlays.css    游记手写覆盖（现状不变）
  portfolio-pages.css             作品集：手写头部(16:9 舞台 + data-edition)                    ← 新增
                                  + @lte-generated(page-*) + @portfolio-overlays

travelogue/layout_templates/
  journal-screens.generated.css   第三份产物 → 优先废弃（D-DPI-17）
```

**`portfolio-pages.css` 必须自带两对 marker**（`@lte-generated:start/end` 与 `@portfolio-overlays:start/end`）。marker 名**不得**复用 `journal-overlays`。理由：`lte_grid_classes_outside_marker` 无 marker 即 `return []`（§1.2(j)），没有 marker 的新文件天生在防重复审计视野之外——那正是今天 147–186 越界块的成因。

### 5.2 迁移步骤（每步一个提交，提交信息带步号 `W1-n/7`）

| 步 | 动作 | 等价证明 |
|----|------|---------|
| 1 | `css_gen` 按前缀分流，新增 `--target journal\|portfolio` 与 `--sync-portfolio`；新文件写入两对 marker | 两份产物并集 == 迁移前 `@lte-generated` 块的规则集合 |
| 2 | 手写 `page-*` 规则（147–186）迁入 `portfolio-pages.css` 手写头部 | 规则集合逐条对照 |
| 3 | **`validate_css_bundle` 加 bundle 来源参数**（按 id 前缀选文件）；`validator.py:450`、`mosaic/render_check.py:50` 同步 | **反例证明**：改错 `portfolio-pages.css` 一位轨道 → `validate --semantic` 必红 |
| 4 | **缓存指纹按管线分算**（D-DPI-16） | 改作品集 CSS，游记 HTML 的 `?v=` 不变；反之亦然 |
| 5 | 渲染侧按身份注入 `@import` + 拷贝对应文件；`packager.py` zip 同步；`css_stale.py` 扩到新文件 | 归一化 `?v=` 后游记产物零 diff；zip 清单断言；旧 trip 有可见提示 |
| 6 | 删除游记选择器上的 `:not([data-pattern^="page-"])` | AC-DPI-06 规则集合等价 **+ AC-DPI-20 渲染几何门**（见 §5.3） |
| 7 | `css_gen` / `validator` 分族参数化，游记族恢复原语义 | 游记 `@lte-generated` 块字节级零 diff |

**步 3、4 必须早于步 5。** 否则加载关系已改而校验仍空转、指纹仍全局，中间态无法验证。

**步 6、7 各自单独一个提交。** 步 7 是唯一会改游记编译产物的一步，需要 `git diff --exit-code` 证明产物没变。

### 5.3 步 6 的额外门（评审 BLK-DPI-09）

要删的 `:not([data-pattern^="page-"])` **不是孤立一项**。它长在游记 **contain-collapse opt-out 链**上——同串选择器还挂着 `screen-full-frame`、`screen-mosaic-*`、`screen-landscape-4`、`person-pair|triple`、`editorial-4mix` 等十余个 `:not()`，是一条一条踩坑攒出来的白名单。

**这条链已经被自动同步打断过一次。** 证据在 `tests/unit/trip/test_asset_version.py` 的 bump 日志：

```
# Re-bumped 2026-07-27 (h): restore contain-collapse opt-out for mixed-1l1p /
# landscape-3-editorial / person-pair|triple (export --sync-journal regression).
```

因此「规则集合等价」（AC-DPI-06）是**必要但不充分**条件。步 6 另加两道门：

1. **CI / PR 出门**：新增 opt-out 清单断言（AC-DPI-20）——断言 bump 日志点名过的 `mixed-1l1p` / `landscape-3-editorial` / `person-pair` / `person-triple` / `editorial-4mix` 在 contain 情形下**不塌陷**（渲染几何或选择器命中，不比 PNG）
2. **本地 / nightly / 狗粮**：删项前后 `python scripts/lte_probe_regress.py --screenshot --strict` 均绿。不挡 merge（IE-DPI-08）

### 5.4 CI 门禁改造

现有两处门（`test-pr` 与 `validate`）只看 `journal-screens.css`：

```yaml
python -m travelogue.layout_templates.cli export --sync-journal
git diff --exit-code templates/visual-journal/journal-screens.css
```

改为**两条独立门**，任一漂移都红：

```yaml
python -m travelogue.layout_templates.cli export --sync-journal
git diff --exit-code templates/visual-journal/journal-screens.css
python -m travelogue.layout_templates.cli export --sync-portfolio
git diff --exit-code templates/visual-journal/portfolio-pages.css
```

同时 `scripts/lte_journal_css_audit.py --fail-on-duplicates` 需扩到新文件（或新增同构脚本），并**新增断言**：`journal-screens.css` 内不出现 `page-`；`portfolio-pages.css` 内不出现 `screen-`。

`tests/unit/layout_engine/test_lte_css_sync.py` 的三类断言（marker 存在性、`inside` 含生成类、`outside` 无重复）须复制一份到新文件。

---

## 6. 渲染 builder 分家

### 6.1 拆法

`render/chapters.py`（526 行）现有 `build_chapter_contexts(...)`。拆成：

| 新文件 | 内容 | 来源 |
|--------|------|------|
| `render/journal_chapters.py` | 高光注入、长图过滤、呼吸屏、章头、票根分隔、trip-index、folio 计划、items 降级 | 现有实现去掉全部 `is_portfolio` 分支的**假分支** |
| `render/portfolio_chapters.py` | `page-*` 屏、16:9、藏章头、空章省略、纯图、无 trip-index | 现有实现取 `is_portfolio` 为真的路径 |
| `render/chapters.py` | 游记 builder 的稳定导入名（re-export，无身份 `if`） | IE-DPI-09 |

`assemble.py` 只留这一处分发（IE-DPI-09）：

```python
if is_portfolio_trip(trip):
    chapters_out = build_portfolio_chapters(...)
else:
    chapters_out = build_journal_chapters(...)
```

`chapters.py` **不再**含 `if is_portfolio_trip`。它只 re-export `build_chapters_render_context = build_journal_chapters`，避免既有 import 断裂。`surface.py` 的 `portfolio_body` 迁进 `portfolio_chapters`（W0 先入 grandfather）。

### 6.2 partial 分家

- 新增 `partials/chapter-portfolio.hbs`：无 divider / 无 chapter-header / 无 chapter-separator / 无 decor / 无 lead，直接 `{{#each screens}}`
- `chapter.hbs` **恢复**到 PFM 之前形状（移除 `hideChapterChrome` 与 `chapter--folio-body`）
- `hideChapterChrome` 字段从 `ChapterRenderContext`（`render/context_types.py:259`）移除

### 6.3 舞台收敛（S-06）

`render/context.py:816` 的 `is_page_face` 目前靠 `patternId.startswith("page-")` 判族。分家后 builder 已知身份，可以**显式传 stage 参数**（`stageAspect` / `viewportFit`），把前缀嗅探撤掉。

**本波只做到「参数可传」；是否删掉前缀嗅探留一次观察期**（见 OQ-DPI-02），避免同时改两处判族逻辑。

---

## 7. 导出入口纯分发

### 7.1 目标态

```
export/dispatch.py            按 (platform, edition) 选 writer；唯一入口
  ├─ journal  × wechat_chat      → longshot.export_trip_longshot   （只做竖条）
  ├─ journal  × 六平台            → platform_longshot / collage_pack / photo_grid_pack / poster_bric
  ├─ portfolio × portfolio_pages → portfolio_pages.export_portfolio_bundle
  └─ portfolio × wechat_chat     → portfolio_wechat.export_portfolio_wechat_from_kept  (ISO-04)
```

### 7.2 要收回的东西

| 项 | 现状 | 目标 |
|----|------|------|
| `export_trip_longshot(include_zip=, include_pages=)` | 作品集专用参数长在游记函数上 | 移除；由 `portfolio_pages` 自己的签名承担 |
| `LongshotExportResult.skipped_pages` / `.share_zip` | 作品集字段长在游记结果类型上 | 迁到 `PortfolioBundleResult` |
| `longshot.py:1135` / `:1170-1183` 身份分支 | 两处 `if` 在游记函数体内 | 上移到 `dispatch.py` |

调用点同步：`cli/render_cmds.py:591`、`web/studio_handlers/export_handlers.py:702/759/838`。

---

## 8. 隔离门禁

### 8.1 新增 pytest marker 与测试包

`pyproject.toml` `markers` 增一条：

```
"pipeline_isolation: dual-pipeline isolation contract (DPI); local one-shot selector for
 humans and triage — NOT a separate CI step (already inside the fast suite)",
```

本地一条命令跑完：

```bash
python -m pytest -m pipeline_isolation -q
```

**这个 mark 不进 CI 单独成步**（评审 BLK-DPI-06）。`ci.yml:1-4` 自述 hobbyist 预算，而 `test-pr`（L143-155）已跑全量 fast 套件、把下表八个文件全部包含在内；再单跑一遍是纯重复分钟数。mark 的价值在本地与排障，不在 CI。

纳入该 mark 的现有测试（**只加 mark，不改断言**）：

| 文件 | 覆盖 |
|------|------|
| `tests/unit/layout_engine/test_editorial_slot_match.py::test_journal_mosaic_does_not_import_portfolio_slot_match` | 源码不含跨族 import |
| `tests/unit/layout_engine/test_editorial_fill.py`（`fill_groups` / `editorial_series.fill` 扫描） | 同上 |
| `tests/unit/layout_engine/test_pfm_render_fingerprint.py` | ISO-01 指纹字段级 |
| `tests/unit/export/test_portfolio_export_isolation.py` | OR 旁路 / 平台登记 |
| `tests/unit/export/test_pfm_collage_isolation.py` | ISO-02 卡序 |
| `tests/unit/render/test_reading_profile.py`（127 / 140） | `data-edition` 戳记有无 |
| `tests/unit/config/test_edition.py` | 缺省即游记 |
| `tests/unit/web/test_portfolio_pipeline.py` | schema / 入口隔离 |

### 8.2 新增形状断言（**当前最大缺口**）

新增 `tests/unit/render/test_dual_pipeline_shape.py`，用游记 golden 夹具与作品集夹具，断言 HTML 形状（不比像素）：

| AC | 面 | 必须有 | 必须无 |
|----|----|--------|--------|
| 游记 web | `export_layout=web` | `data-block="chapter-header"`、`data-block="layout-screen"`、`data-pattern^="screen-"` | `data-edition="portfolio"`、`data-pattern^="page-"` |
| 游记长图 | `export_layout=longshot` | `data-layout="longshot"`、`data-block="media-card"`、`data-block="chapter-header"` | `data-block="layout-screen"`、`data-edition="portfolio"`、`page-` |
| 作品集 web | `edition=portfolio` | `data-edition="portfolio"`、`data-pattern^="page-"` | `data-block="chapter-header"`、`chapter-separator`、`divider-place` |

作品集面用 **golden + 注入 `edition=portfolio`**（IE-DPI-05），不要读本地 `trips/demo-*`。

**CSS 文件名 / `@import` 目标**（原第四组）推迟到 **W1**，与 FE-DPI-05 同期（IE-DPI-10）。W0 形状断言只覆盖上表三行。

### 8.3 新增所有权 lint（v0.2.1 · 棘轮）

`scripts/lint_dual_pipeline_ownership.py`（模式参照 `scripts/lint_layout_engine_facade.py` 的 AST + grandfather JSON）：

1. 扫 `travelogue/**/*.py`（**W0 不扫** `templates/**/*.css`）
2. 命中跨族标记（`is_portfolio_trip` / `is_portfolio` 分支、`hideChapterChrome`、`editorial_series` import、`slot_match` import）
3. 命中若在 §4.2 窄缝表或允许清单 → 通过
4. 命中若在 `docs/acceptance-records/dpi-seam-baseline.json` 的 `grandfather` → 通过（须有 owner + expiry）
5. **其余新增命中 → 红灯**
6. 夹具方向（IE-DPI-02）：只拦「作品集测试读 `phase16-dogfood`」与「游记测试读 `editorial_series` 夹具」；读 `trip.render_golden.json` 合法

W1 步 2 之后另开 CSS 扫描：`journal-screens.css` 不得再出现 `page-` 规则（AC-DPI-05）。

### 8.4 新增 import-linter 契约（只加不改 · **W2**）

| 契约 | 内容 | 何时加 |
|------|------|--------|
| **DPI journal render isolation** | `travelogue.render.journal_chapters` 不得 import `editorial_series` / `portfolio_pages` / `portfolio_wechat` | **W2** 与拆文件同一提交（IE-DPI-04） |
| **DPI portfolio render isolation** | `travelogue.render.portfolio_chapters` 不得 import `mosaic` / `longshot_filter` / `moment_scoring` | **W2** 同上 |

W0 **不加**这两条，也不建空壳模块。W0 只保证既有 4 条契约文本零 diff。

### 8.5 CI 接线

**不新增重复 pytest 步骤。** 接线按里程碑拆开：

| 何时 | job | 步骤 | 承担什么 |
|------|-----|------|---------|
| **W0** | `lint` | `python scripts/lint_dual_pipeline_ownership.py` | 棘轮：拦新增越界 |
| **W0** | `lint` | `lint-imports`（已有，不改契约文本） | 既有包边界 |
| **W0** | `test-pr` | （无新增步骤）形状断言已在 fast 套件 | 三面 HTML 形状 |
| **W1** | `test-pr` / `validate` | `export --sync-portfolio` + `git diff --exit-code portfolio-pages.css` | 作品集 CSS 漂移（与 BE-DPI-07 同提交） |
| **W1** | `validate` | `lte_journal_css_audit.py` 扩双文件 | 双份产物无交叉前缀 |

---

## 9. 前端任务

### 9.1 现状

| 文件 | 行数 / 命中 | 问题 |
|------|-----------|------|
| `preview-toolbar/dock.js` | 463 行 · 41 处 | 在 `documentElement` 上挂/摘 `data-edition`，并混着两边的角标、Banner、CTA |
| `js/portfolio-export-logic.js` | 199 行 · 36 处 | 已独立，保持 |
| `js/portfolio-edition-logic.js` | 22 处 | 已独立，保持 |
| `preview-toolbar/features.js` | 57 处 | `data-edition-card` 卡片壳与作品集档位芯片混排 |
| `preview-toolbar/longshot.js` | 20 处 | 长图面板里含作品集 edition 判断 |
| `homepage-v2/import-wizard.js` | 55 处 | 导入向导双身份（**属于 PFM 设计，不分家**） |

JS 测试入口：`npm run test:js` → `scripts/run-js-tests.mjs` 扫 `tests/js/*.test.mjs`；类型门 `npm run tsc:preview-toolbar`。已有 `journalExportPanelSnapshot`（`tests/js/longshot-export-panel.test.mjs:189`）做游记面板零 diff —— **这是本波 FE 的样板**。

### 9.2 FE 任务

| ID | 任务 | 落点 | 估时(d) | 里程碑 |
|----|------|------|--------|-------|
| **FE-DPI-01** | `dock.js` 收成**纯分发**：`data-edition` 挂载 + 调 `journalDockLogic` / `portfolioDockLogic`；两边的角标 / Banner / CTA 各回各家 | `preview-toolbar/dock.js`、新增 `js/journal-dock-logic.js` | 0.8 | W3 |
| **FE-DPI-02** | `longshot.js` 中的 edition 判断上移到 dock 分发；长图面板恢复「只管游记竖条」 | `preview-toolbar/longshot.js` | 0.5 | W3 |
| **FE-DPI-03** | `features.js` 的 `data-edition-card` 只留卡片壳；作品集档位芯片迁入 `portfolio-edition-logic.js` | `preview-toolbar/features.js` | 0.6 | W3 |
| **FE-DPI-04** | 新增 `tests/js/dual-pipeline-panel.test.mjs`：**游记面板快照**（沿用 `journalExportPanelSnapshot`）在作品集逻辑变更下零 diff；反向亦然 | `tests/js/` | 0.6 | W0 |
| **FE-DPI-05** | 预览壳按身份加载 CSS：作品集页面 `<link>` / `@import` 指向 `portfolio-pages.css` | `templates/studio/` + `render/engine.py` 协同 | 0.4 | W1 |
| **FE-DPI-06** | `tsc:preview-toolbar` 保持绿；新增 logic 模块补 jsdoc 类型 | `preview-toolbar/jsconfig.json` | 0.3 | W3 |

**FE-DPI-04 排在 W0**：它是「FE 改一边不影响另一边」的机器证明，必须在动 FE 代码之前就位。

---

## 10. 会被改红的既有测试、文档与产物

### 10.1 测试

| 文件 | 为什么红 | 处置 |
|------|---------|------|
| `tests/unit/render/test_portfolio_body_copy.py` | 断言 `hideChapterChrome` 与 context 省略 | 改断言新 builder 的输出；语义不变 |
| `tests/unit/layout_engine/test_editorial_series.py:779` | `assert all(ch.get("hideChapterChrome") ...)` | 字段被移除；改断言渲染结果无章头节点 |
| `tests/unit/layout_engine/test_lte_registry_parity.py` | 分编译后产物路径变化 | 扩到两份产物 |
| LTE CSS 相关（`lte_journal_css_audit` / `ltn_active_set_gate` / `ltn_geometry_audit`） | 新文件未登记 | 扩扫描范围 |
| `tests/unit/export/test_portfolio_pages.py`、长图相关 | `export_trip_longshot` 签名收窄 | 改调 `dispatch` |
| `tests/js/longshot-export-panel.test.mjs` | dock 分发重构 | 保留快照断言，改注入点 |
| **`tests/unit/trip/test_asset_version.py`** | **钉 bundle 哈希金样**（L15 明写「Bump only when templates/visual-journal bundle bytes change」）。W1 每一步都会动它 | 见下方 bump 纪律 |
| **`tests/unit/layout_engine/test_lte_css_sync.py`** | marker 存在性 / `outside` 无重复断言，只覆盖游记文件 | 复制一份到 `portfolio-pages.css` |

**bump 纪律（评审 BLK-DPI-05）**：`test_asset_version.py` 的注释头已积累 40 余行历史 bump 记录。本波规定 **一个里程碑最多一次 bump，附一行原因**，禁止同一波内多次 bump——否则该日志会彻底变成噪音，失去「哪次改动动了 shipped bytes」的追溯价值。

### 10.2 文档

| 文档 | 回写 |
|------|------|
| `docs/TECH-ARCHITECTURE.md` §18 | 新增 DPI 两条契约、新 lint、双 CSS 产物 |
| `docs/PRD-PORTFOLIO-FOLIO-MODE-V1.md` | ISO 表加一行指向本文（**不改 ISO-01～07 原文**） |
| `docs/IMPLEMENTATION-PORTFOLIO-FOLIO-MODE-V1.md` | §2.2 隔离回归补 DPI 门禁 |
| `README.md:147` 分层段 | 补 DPI 契约 |
| 新增 `docs/dual-pipeline-ownership.md` | §4 所有权与窄缝表的权威副本 |
| 新增 `.cursor/rules/dual-pipeline.mdc` | 给 AI / 本人的一页规则 |

### 10.3 已渲染 trip 的处置（评审 BLK-DPI-10 · 从「写文档」升级为带 AC 的任务）

D-DPI-11 改变 `@import` 加载关系，而 `trips/` 下躺着大量已渲染 trip，各自本地有一份旧 `journal-screens.css`。**不能只在文档里写一句「请重渲染」**——本机产品的 trip 就在磁盘上，用户随时会点开。

现网 `layout_templates/css_stale.py` 专为「trip 本地 CSS 缺 grid class」而存在（AC-P16-11），说明这个坑已经踩过；`engine.py:605-607` 的 cache-bust 补丁是第二处证据。

要求（BE-DPI-18 · IE-DPI-07）：

现网 `trip_layout_css_stale` 在几何固化（`_screens_use_solid_geometry`）或 CSS 文件缺失时直接 `return False`，扩 grid class 扫描救不了已渲染 trip。

1. 陈旧信号改成**加载关系**：游记产物的 `journal.css` `@import` 须指向 `journal-screens.css`；作品集须指向 `portfolio-pages.css` 且该文件存在。缺文件 / 指错文件 → 陈旧
2. 陈旧时**预览侧给可见提示或自动重渲染**（落点与文案实施时定）
3. AC-DPI-24：用一份**夹具级**「W1 之前」产物（`tmp_path` 里放旧 `@import`，不要依赖本地 `trips/demo-*`），不重渲染直接走预览陈旧检测，断言给出明确提示而**不是坏版式**

---

## 11. 任务表与里程碑

### 11.1 后端任务

| ID | 任务 | 落点 | 估时(d) | 里程碑 |
|----|------|------|--------|-------|
| **BE-DPI-01** | 新增 `pipeline_isolation` marker；给 §8.1 八个既有测试打 mark | `pyproject.toml`、`tests/**` | 0.3 | **W0** |
| **BE-DPI-02** | 新增 `test_dual_pipeline_shape.py`（§8.2 **三组**形状断言；作品集走 golden 注入；不含 CSS 文件名） | `tests/unit/render/` | 1.0 | **W0** |
| **BE-DPI-03** | 新增棘轮型 `lint_dual_pipeline_ownership.py` + grandfather 基线（不扫 CSS；夹具方向按 IE-DPI-02） | `scripts/`、`docs/acceptance-records/` | 0.8 | **W0** |
| **BE-DPI-04** | 新增两条 import-linter 契约（**与拆文件同一提交，不建空壳**） | `pyproject.toml` | 0.2 | **W2** |
| **BE-DPI-05** | 写 `docs/dual-pipeline-ownership.md`（含 §4.3 夹具所有权）+ `.cursor/rules/dual-pipeline.mdc` | `docs/`、`.cursor/` | 0.5 | **W0** |
| **BE-DPI-06** | CI 接线 W0：只加 ownership lint；**不接** `--sync-portfolio` | `.github/workflows/ci.yml` | 0.2 | **W0** |
| **BE-DPI-06b** | CI 接线 W1：`--sync-portfolio` 漂移门 + 双文件审计（与 BE-DPI-07 同提交） | `.github/workflows/ci.yml` | 0.2 | **W1** |
| **BE-DPI-19** | `render_check.py` / `render_binding.py` 改用 `paths.JOURNAL_SCREENS_CSS`，消除重复定义 | `layout_engine/` | 0.2 | **W0** |
| **BE-DPI-07** | `css_gen` 按前缀分流 + `--target` / `--sync-portfolio` + 新文件两对 marker | `layout_templates/css_gen.py`、`cli.py` | 1.4 | W1 |
| **BE-DPI-08** | 手写 `page-*` 规则迁入 `portfolio-pages.css` | `templates/visual-journal/` | 0.5 | W1 |
| **BE-DPI-20** | **`validate_css_bundle` 加 bundle 来源参数**；两处调用点同步；反例测试 | `layout_templates/`、`layout_engine/mosaic/render_check.py` | 1.0 | W1 |
| **BE-DPI-21** | **缓存指纹按管线分算**（D-DPI-16）；`test_asset_version` 改造 | `render/context.py`、`tests/unit/trip/` | 1.2 | W1 |
| **BE-DPI-22** | 第三份产物废弃或分家（D-DPI-17）+ 文档同步 | `layout_templates/cli.py`、`docs/` | 0.4 | W1 |
| **BE-DPI-09** | 渲染 / zip 按身份加载 CSS | `render/engine.py`、`export/packager.py` | 0.8 | W1 |
| **BE-DPI-18** | 陈旧信号改为加载关系（IE-DPI-07）+ 预览可见提示 | `layout_templates/css_stale.py`、`web/` | 0.8 | W1 |
| **BE-DPI-10** | 删除游记 `:not([data-pattern^="page-"])` + 规则集合等价脚本 + **opt-out 清单断言**（§5.3） | `journal-screens.css`、`scripts/`、`tests/` | 1.4 | W1 |
| **BE-DPI-11** | `css_gen` / `validator` 分族参数化；游记族恢复原语义 | `layout_templates/` | 1.2 | W1 |
| **BE-DPI-12** | 拆 `journal_chapters.py` / `portfolio_chapters.py`；`assemble.py` 唯一分发；`chapters.py` 变 re-export；收 `surface.py` 的 `portfolio_body` | `render/` | 2.0 | W2 |
| **BE-DPI-13** | 新增 `chapter-portfolio.hbs`；`chapter.hbs` 回滚形状；移除 `hideChapterChrome` 字段 | `templates/visual-journal/partials/`、`render/context_types.py` | 0.8 | W2 |
| **BE-DPI-14** | `render/context.py` 舞台参数化（保留前缀嗅探，见 OQ-DPI-02） | `render/context.py` | 0.6 | W2 |
| **BE-DPI-15** | 新增 `export/dispatch.py`；`export_trip_longshot` 收窄；结果类型分家 | `export/` | 1.5 | W2 |
| **BE-DPI-16** | 调用点迁移（CLI / studio handlers） | `cli/render_cmds.py`、`web/studio_handlers/export_handlers.py` | 0.6 | W2 |
| **BE-DPI-17** | 既有测试与文档回写（§10） | `tests/**`、`docs/**` | 1.5 | W3 |

后端合计 ≈ **19.1 d**，前端 ≈ **3.2 d**，全波 ≈ **22.3 d**。

按里程碑：**W0 ≈ 3.6 d** · **W1 ≈ 9.3 d** · **W2 ≈ 5.7 d** · **W3 ≈ 3.7 d**。

> v0.2.1 把 W0 从 4.5 d 收到 3.6 d：ownership lint 改棘轮、CI 不接还不存在的 `--sync-portfolio`、import-linter 空壳挪到 W2。**W0 必须能单独合入且当天绿。** W1 仍是最重的一波；内部次序跟 §5.2（先有新文件，再分算指纹，再切加载），不再写「BE-DPI-21 必须最先」。

### 11.2 里程碑

| 里程碑 | 内容 | 出门硬门 |
|--------|------|---------|
| **W0 · 门禁** | BE-DPI-01 / 02 / 03 / 05 / 06 / 19、FE-DPI-04。**零业务逻辑改动**（BE-DPI-19 仅换 import 来源） | 隔离包可一条命令跑完且全绿 · **棘轮** ownership lint 绿（grandfather 覆盖现网命中，新增必红）· 三面形状断言绿 · CI **只**加了 ownership lint、**未**接 `--sync-portfolio`、**未**新增重复 pytest · 两处重复定义已消除 · 既有 4 条契约文本零 diff |
| **W1 · CSS 与产物分家** | BE-DPI-07、06b、08、20、21、22、09、18、10、11、FE-DPI-05 | 两份产物规则集合并集 == 迁移前 · 游记 `@lte-generated` 块零 diff · 双漂移门绿 · **`?v=` 分算生效**（AC-DPI-18）· parity 反例必红 · opt-out 清单断言绿 · 加载关系陈旧检测生效。截图 / 整页字节 diff **不挡 merge** |
| **W2 · 渲染与导出分家** | BE-DPI-12～16、04 | 三面形状断言仍绿 · 两条新 import-linter 契约绿 · AC-DPI-12 结构判据绿 · `assemble.py` 仅一处身份 `if` · 窄缝数不增 |
| **W3 · FE 与收口** | FE-DPI-01～03、06、BE-DPI-17 | 游记面板快照零 diff · `tsc` 绿 · `npm run test:js` 绿 · 文档回写完成 |

**W0 必须独立合入**，且按 G-DPI-06 是下一次读者面功能波的前置。它必须**当天能绿**，否则这条硬门是空话。

**W1 不可与 W0 并行。** W1 内部次序跟 §5.2：先有 `portfolio-pages.css` → 再分算指纹 → 再切加载。W1–W3 顺序不可交换。

### 11.3 放行条件（七席授权范围）

| 里程碑 | 放行前必须已关 |
|--------|--------------|
| **W0** | 七席 BLK 已回写；§0.3 实施勘误已落 → **现即可按 W0 开工清单开工** |
| **W1** | BLK-DPI-01 / 02 / 03 / 04 / 05 / 09 / 10 + W0 已合入。**BLK-DPI-01 是方向级前置** |
| **W2** | W1 出门门全绿 |
| **W3** | W2 已合入 |

---

## 12. 验收

### 12.1 门禁类

| ID | 验收 |
|----|------|
| **AC-DPI-01** | `python -m pytest -m pipeline_isolation -q` 全绿，且至少覆盖 §8.1 八个既有文件 + §8.2 新形状断言 |
| **AC-DPI-02** | `python scripts/lint_dual_pipeline_ownership.py` 绿；基线含 §4.2 十条窄缝 + grandfather 覆盖现网历史命中（每条有 owner + expiry）；`render_check.py` / `render_binding.py` 两处重复定义已消除且不占额度 |
| **AC-DPI-03** | W0：`lint-imports` 全绿且 **既有 4 条契约文本零 diff**。W2：新增 2 条契约 KEPT（IE-DPI-04） |
| **AC-DPI-04** | 在窄缝、允许清单、grandfather **之外**任意文件人为加一处 `is_portfolio` 分支 → 所有权 lint **必红**（反向验证，须留反例记录） |
| **AC-DPI-05** | **W1 步 2 之后**：人为把一张 `page-*` 规则写进 `journal-screens.css` → CSS 审计 **必红**。W0 不跑此条 |
| **AC-DPI-19** | **parity 反例必红**：把 `portfolio-pages.css` 中某张脸的 `grid-template-columns` 改错一位 → `python -m travelogue.layout_templates.cli validate --semantic` **必红**。不红即判该门为空（防 §1.2(i) 的空转假绿） |
| **AC-DPI-21** | **新文件防重复生效**：在 `portfolio-pages.css` 的 marker **外**手写一条与生成规则同名的 `.layout-screen__grid--page-*` → 审计 **必红**（防复刻 147–186 那类越界块） |
| **AC-DPI-22** | **夹具方向门（IE-DPI-02）**：作品集测试读 `phase16-dogfood`、或游记测试读 `editorial_series` 夹具 → 必红。读 `trip.render_golden.json` **不红** |

### 12.2 等价类（零行为变更）

| ID | 验收 |
|----|------|
| **AC-DPI-06** | 游记 `screen-*` 有效 CSS 规则集合在 W1 前后等价（按选择器 × 声明比对，允许选择器文本因删 `:not()` 而变，但命中集合与声明必须一致）。**必要但不充分**，须与 AC-DPI-20 同时满足（§5.3） |
| **AC-DPI-24** | 拿一份 W1 之前渲染的 trip，**不重渲染**直接打开预览 → 用户看到明确的「需重新生成」提示或自动重渲染，**不是坏版式**（§10.3） |
| **AC-DPI-07** | 游记 golden 夹具的 web / 长图：**形状断言 + `render_fingerprint` 字段级**在每个里程碑前后保持。归一化整页字节 diff 是本地/狗粮核对，不进 `test-pr` |
| **AC-DPI-08** | 作品集面用 **golden + 注入 `edition=portfolio`**（IE-DPI-05）：形状断言（有 `data-edition="portfolio"` / `page-*`，无章头）在每个里程碑前后保持。不依赖 `trips/demo-*` |
| **AC-DPI-09** | 游记 `render_fingerprint` 字段级不变（沿用 ISO-01 口径） |
| **AC-DPI-10** | `export --sync-journal` 与 `export --sync-portfolio` 双漂移门均绿；两份产物无交叉前缀 |
| **AC-DPI-18** | **缓存指纹分算生效**：只改 `portfolio-pages.css` → 游记 HTML 的 `?v=` **不变**、作品集 HTML 的 `?v=` **必变**；只改 `journal-screens.css` → 反之。两向都要断言 |
| **AC-DPI-20** | **contain-collapse opt-out 未被打断**：`mixed-1l1p` / `landscape-3-editorial` / `person-pair` / `person-triple` / `editorial-4mix` 在 contain 情形下不塌陷（断言渲染几何 / 选择器命中，**不比 PNG**）。`lte_probe_regress.py --screenshot --strict` 留本地 / nightly / 狗粮，**不挡 merge**（IE-DPI-08） |

### 12.3 分家类

| ID | 验收 |
|----|------|
| **AC-DPI-11** | `render/journal_chapters.py` 源码不出现 `portfolio` / `page-` / `editorial_series`；`render/portfolio_chapters.py` 不出现 `mosaic` / `longshot_filter` / `moment_scoring` |
| **AC-DPI-12** | **结构判据（不钉行数 · IE-DPI-09）**：① **`assemble.py` 仅一处** `is_portfolio_trip` 分发；`chapters.py` 不含 `is_portfolio` 分支（只允许 re-export）；② 符号清单：高光注入 / 长图过滤 / 呼吸屏 / 章头 / trip-index 在 `journal_chapters.py`；`page-*` / 16:9 / 空章省略 / `portfolio_body` 在 `portfolio_chapters.py`；③ `hideChapterChrome` 全库检索为 0 |
| **AC-DPI-13** | `export_trip_longshot` 签名不含 `include_zip` / `include_pages`；`LongshotExportResult` 不含 `skipped_pages` / `share_zip` |
| **AC-DPI-14** | 游记 trip 产物目录**不含** `portfolio-pages.css`；作品集 trip 产物目录**不含** `journal-screens.css` 里的 `page-*` 规则（且加载了 `portfolio-pages.css`） |
| **AC-DPI-15** | `dock.js` 中 `is_portfolio` / `data-edition` 相关分支 ≤ 2 处（挂载 + 面板分发） |

### 12.4 独立迭代烟测（本波真正的产品验收）

| ID | 验收 |
|----|------|
| **AC-DPI-16** | **模拟游记迭代**：改一张 `screen-*` 的 YAML 轨道 → 只需跑游记侧回归；作品集 HTML **原始字节**零 diff（含 `?v=`，此处不归一化——指纹分算后必须真零） |
| **AC-DPI-17** | **模拟作品集迭代**：改一张 `page-*` 的 YAML 轨道 → 只需跑作品集侧回归；游记 web / 长图 HTML **原始字节**零 diff |
| **AC-DPI-23** | **模拟误伤**：故意在作品集分支里改游记 contain 选择器 → 门禁在 PR 阶段红灯（不靠人 review） |

**AC-DPI-16 / 17 / 23 必须留验收记录**（`docs/acceptance-records/dpi-dual-pipeline-isolation-v1-*.md`），含实跑命令与 diff 输出。没有这三条，本波等于没验收。

注意 AC-DPI-16/17 用的是**原始字节**（不归一化 `?v=`），且须在指纹分算 + 加载分家都落地之后、用**最小夹具**做，不要拿整本本地 demo。这是 G-DPI-07 的直接判据。**留验收记录即可，不进 `test-pr` 作为每 PR 必跑项**（IE-DPI-08）。

**用户体验席附加要求（SHD-DPI-05）**：三条烟测除机器 diff 外，须附狗粮手测记录——真改一张轨道、真打开对面的 demo 肉眼确认。这一波承诺的是「以后能安心改」，得有人真的改一次试试。

---

## 13. 风险与开放问题

### 13.1 风险

| ID | 风险 | 缓解 |
|----|------|------|
| **R-DPI-01** | CSS 分家时静默丢规则，游记版式在某些屏下崩 | AC-DPI-06 规则集合比对 + 三面形状断言 + AC-DPI-09 指纹字段级；截图门留本地/狗粮 |
| **R-DPI-02** | D-DPI-12 恢复游记编译语义时踩到「碰巧没炸」的 1 槽 primitive | 步 6 单独提交 + `git diff --exit-code` 产物证明；发现差异立即回退该步 |
| **R-DPI-03** | builder 分家时把某个游记特性（呼吸屏 / trip-index / folio 计划）漏在作品集分支里 | AC-DPI-07/08 形状断言双向保持；分家用「先复制两份、再各自删假分支」，不用「重写」 |
| **R-DPI-04** | 所有权 lint 过严，正常开发被误红 | 窄缝基线可改（带 owner + 理由），但**新增窄缝必须写理由**；lint 报错信息给出「加基线」的具体命令 |
| **R-DPI-05** | 本波耗约 22 人天却无用户可见收益，被搁置 | **G-DPI-06 硬门**：下一次读者面功能波开工前 W0 必须已合入。W0 现约 3.6 d 且必须当天能绿。**并附「不做的代价」实证**（见 §13.3） |
| **R-DPI-06** | 两份 CSS 导致 `journal.css` 变量在作品集侧缺失 | `journal.css` 保持共用（壳与变量），只分族规则；FE-DPI-05 断言变量可达；顶部加共享声明注释防以后被塞专用规则（SHD-DPI-06） |
| **R-DPI-07** | 已渲染 trip 加载旧 CSS 造成用户看到坏页 | 升级为带 AC 的任务（BE-DPI-18 / AC-DPI-24 见 §10.3）：`css_stale.py` 扩新文件 + 缺文件算陈旧 + **预览侧可见提示**。不接受「文档写明」 |
| **R-DPI-08** | 指纹分算实现错误，导致某一侧长期吃旧缓存（比坏版式更难发现） | AC-DPI-18 双向断言；`engine.py:605-607` 已有的 `@import` cache-bust 逻辑必须一并按身份改，不能只改哈希列表 |
| **R-DPI-09** | 两条管线通过共享测试夹具重新耦合，而 lint 看不见 | §4.3 夹具所有权 + AC-DPI-22 方向门；`lint_dual_pipeline_ownership.py` 扫 `tests/**/fixtures/**` 引用方向 |
| **R-DPI-10** | W1 九人天跨七个提交，中途中断留下半分家的中间态 | §5.2 每步一提交且带步号 `W1-n/7`（SHD-DPI-01）；步 3、4 必须早于步 5，保证任一中间态可验证 |

### 13.2 开放问题（**七席已裁决 · 全部关闭**）

| ID | 问题 | 裁决 |
|----|------|------|
| **OQ-DPI-01** | `journal.css`（壳）是否也要分家？ | **不分**（七席一致）。它是壳与变量的单一真相；分了立刻产生两份变量真相。采纳 SHD-DPI-06：顶部加共享声明注释，防以后被塞某一侧专用规则 |
| **OQ-DPI-02** | `render/context.py` 的 `page-` 前缀嗅探是否在 W2 一并删除？ | **不删，只参数化**（架构 + 视觉一致）。理由：D-DPI-16 已要在同一波改 bundle version 的判族逻辑，再叠一处判族改动风险不可控。留待作品集下一次几何迭代确认参数够用后单独处理 |
| **OQ-DPI-03** | `page-*` 是否需要自己的槽数上限？ | **归 TSU，本波不定阈值**。只把 `_dense_freeze_exempt` 的前缀豁免升级为显式族参数，数值不变（已并入 D-DPI-12） |
| **OQ-DPI-04** | 是否给作品集独立的 `reading_profile` 模块？ | **不做**。`magazine` 档现网已有，`reading_profile.py:392` 一处默认选择属窄缝 S-05，够窄 |
| **OQ-DPI-05** | 上游（cull / cluster）以后若要按身份分策略怎么办？ | **触发时再开 PRD**。D-DPI-02 作为铁律保留。**算法席补充**：「上游共享」的定义须含夹具同源 → 已落 §4.3 |
| **OQ-DPI-06** | 窄缝数量上限要不要设硬门？ | **设，上限 14，定性为讨论触发器而非配额**。v0.1.0 建议的 12 与 BLK-DPI-07 新增的 2 条恰好顶满、零余量（评审 F-DPI-16）。若两处重复定义按首选方案改走 `paths.py` 则不增，余量留给正常演进 |

### 13.3 不做的代价（实证 · 非假想）

产品席要求把「不做会怎样」写成已发生的事实，而不是风险描述。以下三处**都不是预测**：

| 已发生 | 位置 | 说明 |
|--------|------|------|
| 作品集规则写进了游记文件 | `journal-screens.css:147-186` | 注释自己写着「Must stay outside @lte-generated so sync does not drop it」——绕过了 LTE 权威区 |
| 游记选择器背上了作品集负担 | `journal-screens.css:3846-4030` 多处 | contain 链上被追加 `:not([data-pattern^="page-"])` |
| 游记编译器被作品集全局改写 | `css_gen.py:153-159` + `validate_css_bundle` 的 `multi_track` 放宽 | 「1 槽 primitive 不输出 placement」这条游记语义被改成「一律输出」；游记 1 槽模板**碰巧**仍是 1×1 才没炸 |

三处都发生在 PFM **一波之内**。在没有门禁的情况下，一波功能就能污染三处——这是 G-DPI-06 硬门的排期依据。

---

## 14. 一页速查（实施时贴墙）

**共享到哪：** 照片、EXIF、cull、聚类、开章、封面、Studio 壳、预览服务器、`journal.css` 变量、身份中立夹具。

**必须分家：** 版式选型、几何、读者面 CSS、章头与文案、导出成品、**缓存指纹**、**金样夹具**。

**改代码前问四句：**

1. 这个文件在 §4.1 里属于谁？不属于我这边 → 不改。（`lint_dual_pipeline_ownership.py --explain <file>` 可反查）
2. 我要加的分支在 §4.2 窄缝表里吗？不在 → 换落点，别加 `if`。
3. 我读的夹具在 §4.3 里属于谁？不属于我这边 → 换夹具。
4. 我改的东西对方会加载吗？会 → 跑 `pytest -m pipeline_isolation` + 双漂移门。

**四条不许碰：** 游记 MCS / `score_aspect_match` / 游记 `fit: cover` 合同；作品集 `slot_match` / 16:9 纸面；游记长图 flatten `page-*`；运行时读 `docs/templates/reserve/`。

**两条本波新增的不许：** 把 `portfolio-pages.css` 塞进游记的 bundle 哈希列表（D-DPI-16）；在没有 marker 的 CSS 文件里手写 grid 规则（§5.1）。
