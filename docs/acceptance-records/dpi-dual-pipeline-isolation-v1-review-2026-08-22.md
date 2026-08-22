# PRD-DUAL-PIPELINE-ISOLATION-V1 · 七席评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-DUAL-PIPELINE-ISOLATION-V1.md](../PRD-DUAL-PIPELINE-ISOLATION-V1.md)（**DPI** · 双管线独立迭代）现网 **v0.2.1**（七席审的是 v0.1.0；BLK 回写 v0.2.0；实施勘误 §0.3 升 v0.2.1） |
| **上游合同** | [PFM](../PRD-PORTFOLIO-FOLIO-MODE-V1.md)（身份 / 分叉点 / ISO-01～07，本波不改）· [MSP](../PRD-MAGAZINE-SERIES-PROMOTION-V1.md)（档位与兑现率，本波不碰）· [TSU](../PRD-TEMPLATE-SYSTEM-UPGRADE-V1.md)（`page-*` 几何供货） |
| **前序纪要** | [PFM 八席 2026-08-20](./pfm-portfolio-folio-mode-v1-review-2026-08-20.md) · [MSP 七席+加席 2026-08-21](./msp-magazine-series-promotion-v1-review-2026-08-21.md) |
| **日期** | 2026-08-22 |
| **结论** | **有条件通过（Conditional Go）**。「门禁先行 + 分编译 + builder 分家」的骨架成立，W0 可先行。**BLK-DPI-01～12 回写 v0.2.0 前：不批 W1 开工 · 不批删除 `:not([data-pattern^="page-"])` · 不批「字节级一致」作为出门判据 · 不批在 CI 加重复 pytest 步骤**。 |
| **编码** | ☑ 现状实测（行号级）　☑ OQ 建议　☑ v0.2.0 回写 BLK　☑ v0.2.1 实施勘误　☑ W0 门禁　☑ W1 CSS 分家　☑ W2 渲染/导出分家　☑ W3 FE 收口 |
| **参评角色** | **七席**：产品 · 算法 · 架构 · 开发 · 测试/QA · 视觉/排版 · 用户体验（狗粮手测） |
| **评审方式** | 分席只读 PRD v0.1.0 §0～§14，对照现网代码事实（`render/{context,chapters,assemble,surface,engine}.py`、`layout_templates/{css_gen,validator,cli,registry}.py`、`layout_engine/mosaic/render_check.py`、`layout_engine/render_binding.py`、`export/{longshot,packager,portfolio_pages}.py`、`web/studio_handlers/export_handlers.py`、`scripts/lte_journal_css_audit.py`、`tests/unit/trip/test_asset_version.py`、`tests/unit/layout_engine/test_lte_css_sync.py`、`.github/workflows/ci.yml`、`pyproject.toml`） |
| **本纪要状态** | **已结案 · Conditional Go** · BLK 已回写 v0.2.0 · **实施勘误已落 v0.2.1** · W0 可按 PRD §0.3 开工清单开工 |
| **审查基线** | 零行为变更是本波唯一产品承诺 · 既有 import-linter 契约文本不得改 · 不得为隔离引入新的跨管线耦合 · **「拆得更干净」不等于「隔离更强」：只要产物里还有一个共享哈希，隔离就是名义的** |

---

## 0. 会前宣读（主持人）

1. **切口**：装配层已经硬分叉（mosaic / `editorial_series` 互不 import，import-linter 4 kept）。但读者面仍同居：`journal-screens.css` 5831 行里躺着作品集的 16:9 舞台规则（147–186），游记的 contain 选择器已被追加 `:not([data-pattern^="page-"])`（3846–4030 多处），LTE CSS 编译器为 `page-1-hero-*` 的 gutter 被全局改写（`css_gen.py:153-159`）。方向本场不重开。
2. **已拍（勿重开）**：不加 `layoutEngine` 第三值；不复制 `curate.py`；不做两套 ingest；不拆 `chapters[]`；不改既有 import-linter 契约文本；不引 monorepo。
3. **勿重开**：档位 / 兑现率（归 MSP）；`page-*` 几何设计（归 TSU）；`homepage_entry` 开关（归 PFM W4）。
4. **本场必拍**：「字节级一致」这条出门判据到底成不成立；CSS 分家后 LTE 校验会不会变成空转；三份产物还是两份；CI 预算加不加得起一条重复 pytest；删 `:not()` 的风险由谁兜；窄缝表是不是漏登记了。
5. **本波无 C 端可见变更，故不设典型用户加席。** 但用户体验席保留「已渲染 trip 会不会看到坏页」的否决权——本机产品的 trip 躺在磁盘上，不能只靠文档说「请重渲染」。

---

## 1. 总评（一句话）

> **七席一致 Conditional Go：这份 PRD 最大的优点是它没有把「隔离」写成口号——§1.2 每一条同居事实都带行号，连 `css_gen.py:153-159` 那段「改画册顺手改了游记编译器」的注释都原文引了出来，而且它诚实地承认反向污染已经发生（游记选择器背上了 `:not([data-pattern^="page-"])`），没有拿「装配层已分叉」交差；「门禁先行、W0 零业务代码改动」这个排序也是对的，它让最便宜的一波先挡住误伤。但 v0.1.0 有十二处按原文 Kickoff 会撞墙或会假绿，其中一处是方向级的：（1）`render/context.py:53-69` 的 `_longshot_bundle_version` 把 `JOURNAL_SCREENS_CSS` 连同其余 14 个前端文件一起做 SHA256，结果写进每张 HTML 的 `?v=`——这意味着 §12.2 的「字节级一致」在 W1 物理上不可能达成（我们正是要改那份 CSS），更要命的是：`portfolio-pages.css` 若加入这个哈希列表，改作品集 CSS 会 bump 游记 HTML 的 `?v=`；若不加入，作品集 CSS 改了不刷缓存。两条路都是新的跨管线耦合，而这正是本 PRD 声称要消灭的东西——bundle version 必须按管线分算，这是本场唯一的方向级 Must-Fix；（2）产物是三份不是两份：`layout_templates/cli.py:101` 的 `export --out` 默认写 `journal-screens.generated.css`（3434 行，含全部 `page-*`），§5.1 只列了两个文件；（3）`validate_css_bundle`（`css_gen.py:211-244`）的 parity 是「在 journal CSS 的 marker 区里找同名 grid class，找不到就跳过」——分家后 75 张 `page-*` 全部走进「找不到」分支，LTE 语义校验对作品集**静默降级成空转**，`cli validate --semantic` 照样绿；（4）防重复机制 `lte_grid_classes_outside_marker` 依赖 LTE marker 对，且只在 `journal-screens.css` 上跑（`lte_journal_css_audit.py:43` 默认值、`test_lte_css_sync.py:66`），新文件不给 marker 与审计就会复刻出今天 147–186 这同一类 bug；（5）`tests/unit/trip/test_asset_version.py` 钉着 bundle 哈希金样、附 40 余行 bump 日志，W1 每一步都会打红它，§10.1 漏了；（6）CI 自述「Hobbyist-friendly CI budget」，而 `test-pr` 已经跑全量 fast 套件、把我们要打 mark 的测试全包含了，再加一条 `pytest -m pipeline_isolation` 是纯重复分钟数；（7）`mosaic/render_check.py:15-17` 与 `layout_engine/render_binding.py:10` 两处在**游记侧包内**硬编码共享 CSS 路径，§4.2 窄缝表没登记；（8）AC-DPI-12 凭空钉「`chapters.py` ≤ 120 行」，没量过共享 helper 面，这种数字只会被豁免；（9）D-DPI-10 要删的 `:not()` 长在游记 contain-collapse opt-out 链上，而 `test_asset_version.py` 的 bump 日志 2026-07-27 (h) 记着这条链**曾被 `export --sync-journal` 打断过一次并需要恢复**，删一项而不做渲染几何校验是高风险；（10）没有回滚故事：D-DPI-11 改了 `@import` 关系，磁盘上已渲染的 trip 会加载什么，PRD 只写「文档写明需重渲染」；（11）18 人天零用户价值却没有「什么时候必须做」的门，会变成永久 backlog；（12）只保证了代码隔离，没提夹具 / 金样隔离，两条管线可以通过共享测试数据再耦合回去。另外 OQ-DPI-06 建议的「窄缝 ≤ 12」与 BLK-DPI-07 新增的 2 条窄缝（现表 10 条）刚好顶满，零余量，这个数字要重定。关 BLK 后升 v0.2.0；**W0 可在回写后立即开工，W1 必须等 BLK-01/02/03/04/09 全关**。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **产品** | **Conditional Go** | 「零行为变更」当铁律我签，这是纯工程波唯一诚实的承诺方式。但两件事没闭合：一是这一波 18 人天对用户是零可见价值，PRD 没写「什么时候必须做」——按现在的写法它会一直排在功能后面，而 seam 会继续烂，我要一条硬门：**下一次动到任一管线读者面的功能波开工前，W0 必须已合入**；二是 §13 R-DPI-05 把「被搁置」列成风险却只给了「W0 可单独合入」这一句缓解，没算「不做的代价」。请把已经发生的两处污染（147–186 手写块、`:not()` 链）写成代价证据，我拿它去说服自己排期。 |
| **算法** | **Conditional Go** | 本波不碰打分与选型，mosaic / `editorial_series` 的算法边界我确认已经是硬的（`api.py` 不导出、源码扫描有单测），这块没意见。我要加一条 PRD 完全没提的：**夹具与金样的所有权**。今天 `tests/fixtures/phase16-dogfood` 那批 trip 被 `phase16_template_eval.py`、`phase17_*` 一整排门禁读，作品集侧的夹具在 `tests/unit/layout_engine/fixtures/editorial_series/`。代码分家了，但只要哪天一个游记算法改动重新生成了某份共享 golden、而作品集测试也读它，两条管线就通过测试数据重新耦合——而且这种耦合比 import 更难查，因为 lint 看不见。请补一节「夹具所有权」，规则跟 §4.1 一样：谁的金样谁改，共享夹具进窄缝表。 |
| **架构** | **Conditional Go** | 三层独占 + 窄缝登记制这个模型是对的，比「靠人记住铁律」强一个数量级，`lint_dual_pipeline_ownership.py` 参照 `lint_layout_engine_facade.py` 的 AST + 基线 JSON 写法也是现成先例。但有一处方向级问题必须在 W1 之前解决：**`_longshot_bundle_version` 是一个横跨两条管线的全局内容哈希**。`render/context.py:53-69` 把 `JOURNAL_CSS` 与 `JOURNAL_SCREENS_CSS` 和另外 13 个前端资源一起摘要，产物是每张 HTML 上的 `?v=`。分家后你只有两个选择，而两个都在制造新耦合：把 `portfolio-pages.css` 加进列表 → 改作品集 CSS 会改游记 HTML 的字节；不加 → 作品集 CSS 更新后浏览器吃旧缓存（这个坑 `engine.py:605-607` 的注释已经踩过一次并专门写了 cache-bust 补丁）。正确做法是 bundle version **按管线分算**：游记 HTML 只摘要游记会加载的文件，作品集只摘要自己的。这条不解决，本 PRD 的隔离在产物层面是名义的。另外 §4.2 漏登记两条：`mosaic/render_check.py:15-17` 和 `layout_engine/render_binding.py:10` 都在游记侧包内硬编码 `templates/visual-journal/journal-screens.css` 路径——要么进窄缝表，要么统一走 `travelogue/paths.py`（后者更好，`paths.py` 已经有 `JOURNAL_SCREENS_CSS` 常量，这两处属于历史遗留的重复定义）。 |
| **开发** | **Conditional Go** | 任务表可开工，14.8 + 3.2 的分布合理，W0 单独合入这个设计我很赞成。五处要调：① **产物是三份**——`layout_templates/cli.py:101` 里 `export --out` 缺省落 `journal-screens.generated.css`，`docs/GUIDE-PHASE16` §159 把它写成正式输出，MSP §710 还列了「重生成」。§5.1 只提两个文件，BE-DPI-07 按原文写完会漏掉它，请明确它的归属（我倾向：也分成 `*-journal.generated.css` / `*-portfolio.generated.css`，或者干脆废掉，因为它现在没有运行时消费者）。② **`test_asset_version.py` 会红**——它钉 bundle 哈希金样，注释头 40 余行全是历史 bump 记录，W1 的每一步都会动它；§10.1 必须列进去，并定「一个里程碑一次 bump、附一行原因」的纪律，否则会出现同一波里 bump 四次、日志变噪音。③ **CI 别加重复步骤**——`ci.yml` 开头自述 hobbyist 预算，`test-pr` 跑的是全量 fast 套件，`-m pipeline_isolation` 那批测试本来就在里面，再单跑一遍是白烧分钟。mark 的价值在本地一条命令，不在 CI；CI 侧靠 ownership lint + 已在 fast 套件里的形状断言就够。④ **AC-DPI-12 的 120 行是拍的**——`chapters.py` 现在 526 行，里面 `enrich_screen_tones`、手机展开、screen-spread、folio plan、trip-index 这些是真共享 helper，硬钉行数只会逼出「为了过门再拆一个文件」。改成结构判据。⑤ D-DPI-15 我核过了，`include_zip` / `include_pages` 从 `export_handlers.py:805-812` 一路传到 `portfolio_pages.py:294`，中间 `longshot.py:1108` 只是过一手，收回去是干净的，这条没问题。 |
| **测试 / QA** | **Conditional Go** | §8 是全文我最认可的部分——把「没有一条命令能跑完隔离测试」和「游记形状断言完全缺失」两个洞点出来，还给了反向验证（AC-DPI-04/05 故意加分支要红），这个自觉度在本仓库 PRD 里少见。但有两处会假绿、一处判据不成立：① **假绿之一**：`validate_css_bundle`（`css_gen.py:232-243`）的 parity 逻辑是 `expected = parsed.get(template.render_grid_class)`，然后 `if expected:` 才比对。`page-*` 规则搬出 `journal-screens.css` 之后，这 75 张脸的 `expected` 全是 None，校验**静默跳过**，`cli validate --semantic` 和 `mosaic/render_check.py:50` 都照样绿。必须给 `validate_css_bundle` 加 bundle 来源参数，并补一条 AC：故意把 `portfolio-pages.css` 里某张脸的 `grid-template-columns` 改错一位，`validate --semantic` **必须红**——不红就说明这个门是空的。② **假绿之二**：`lte_grid_classes_outside_marker`（`css_gen.py:409-423`）先找 `LTE_MARKER_START/END`，找不到直接 `return []`。新文件没有 marker 对 → 永远返回空 → 手写规则可以静默盖住生成规则，这**正是今天 147–186 那段的成因**。`portfolio-pages.css` 必须自带 marker 对，并进 `lte_journal_css_audit.py` 与 `test_lte_css_sync.py` 的双文件扫描。③ **判据不成立**：AC-DPI-07/08 的「字节级一致」在 W1 做不到——见架构席，`?v=` 是 CSS 内容哈希，我们正在改 CSS。请改成「把 `?v=<hash>` 归一化成占位符后字节级一致」，并单独用一条 AC 管 `?v=` 本身（分算后游记的 `?v=` 不因作品集 CSS 变化而变）。这样两件事各有判据，不互相掩盖。顺带说，游记渲染我确认是确定性的（`render/` 下无 `datetime.now` / `uuid`），归一化 `?v=` 之后字节比对是可行的。 |
| **视觉 / 排版** | **Conditional Go** | 分编译 + 按身份加载我签，作品集不该继续吃 75 张 `page-*` 之外的 3000 行游记规则，游记更不该反过来。但 D-DPI-10 我要挂条件。要删的那个 `:not([data-pattern^="page-"])` 不是孤立的一项，它长在游记 **contain-collapse opt-out 链**上——同一串选择器里还挂着 `screen-full-frame`、`screen-mosaic-*`、`screen-landscape-4`、`person-pair|triple`、`editorial-4mix` 等十几个 `:not()`，那是一条一条踩坑攒出来的白名单。证据在 `test_asset_version.py` 的 bump 日志里：2026-07-27 (h) 写着「restore contain-collapse opt-out for mixed-1l1p / landscape-3-editorial / person-pair|triple（**export --sync-journal regression**）」——这条链**已经被自动同步打断过一次**，是靠人肉恢复的。所以：AC-DPI-06 的「规则集合等价」是必要条件但不充分，删项前后必须再跑 `lte_probe_regress.py --screenshot --strict`，并针对 bump 日志里点过名的那几个 pattern 补一条 opt-out 清单断言（断言「哪些 pattern 在 contain 时不塌陷」，而不是断言选择器文本）。这条不满足，我不签 W1。 |
| **用户体验 · 狗粮** | **Conditional Go** | 「改一边不需要读另一边」这个目标就是我上周踩的坑的反面——第二章掉回长图那次，根因横跨装配、渲染、CSS 三层，我当时得同时打开六个文件。所以本波我支持。但有一件事 PRD 用一句「文档写明需重渲染」糊过去了，不行：D-DPI-11 改了 `journal.css` 的 `@import` 关系，而 `trips/` 下躺着一堆我已经渲染过的 trip，它们本地各有一份 `journal-screens.css`。W1 合入后我点开旧 trip 的预览，看到的是什么?现网已经有 `layout_templates/css_stale.py` 专门检测 trip 本地 CSS 缺 grid class（AC-P16-11），说明这个坑被踩过。要求：`css_stale.py` 扩到新文件，并且**预览时给出可见提示或自动重渲染**，不能只在 docs 里写一句。另外 AC-DPI-16/17/18 那三条独立迭代烟测是本波真正的验收，我要求留验收记录时**附我这边的手测**：改一张 `page-*` 轨道，我打开游记 demo 肉眼确认没变；反向同理。机器 diff 我信，但这一波的承诺是「以后能安心改」，得有人真的改一次试试。 |

**汇总**：**7/7 Conditional Go**。未回写 Must-Fix 前 **不批 W1 开工** · **不批删除 `:not([data-pattern^="page-"])`** · **不批「字节级一致」作为出门判据** · **不批 CI 新增重复 pytest 步骤**。**W0 在回写 BLK-DPI-06/07/08/12 后可立即开工**（这四条只影响 W0 的门禁与窄缝表，不涉及 CSS）。

**对齐评分**

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→方案因果完整度 | **9** | §1.2 每条同居事实带行号；诚实承认反向污染已发生，未拿「装配层已分叉」交差 |
| 与现网代码对齐 / 防假绿 | **5** | 现状盘点准确，但漏了 bundle 哈希、第三份产物、parity 空转、marker 依赖四处硬事实 |
| 与 PFM / MSP / TSU 边界 | **9** | 非目标表与「归谁」表清楚；「只加契约不改旧契约」沿用 MSP 口径，是本文最稳的一处 |
| 隔离彻底性 | **5** | 代码层设计到位；**产物层留了一个全局哈希**，夹具层完全未覆盖 |
| 工程可开工性 | **7** | W0 可立即开；W1 有三处会撞墙，一处估时偏低（BE-DPI-11 未含 parity 改造） |
| AC 可测性 | **6** | 形状断言与反向验证扎实；「字节级一致」不成立，`chapters.py ≤ 120 行` 是拍的 |
| 回滚 / 已有产物安全 | **3** | 磁盘上已渲染 trip 的加载关系变更只有一句 docs 说明 |

---

## 3. 事实核查（对照现网代码 · 影响结论）

| # | PRD v0.1.0 假设 | 代码事实（2026-08-22） | 会中 |
|---|-----------------|----------------------|------|
| **F-DPI-01** | 每个里程碑可做到游记 / 作品集 HTML **字节级一致**（D-DPI-01 / AC-DPI-07/08） | `render/context.py:53-69` `_BUNDLE_VERSION_PATHS` 含 `JOURNAL_CSS` 与 `JOURNAL_SCREENS_CSS` 等 15 项，SHA256 前若干位写进 HTML 的 `?v=`（`engine.py:598-617` 还专门为 `@import` 补了 cache-bust）。改 CSS 必然改 HTML 字节 | **判据不成立 + 跨管线耦合 · BLK-DPI-01** |
| **F-DPI-02** | 读者面 CSS 产物是两份（§5.1） | 第三份存在：`layout_templates/cli.py:101` `export --out` 缺省写 `travelogue/layout_templates/journal-screens.generated.css`（3434 行，含全部 `page-*`）；`docs/GUIDE-PHASE16-layout-template-engine.md:159` 列为正式输出，MSP §710 列「重生成」 | **漏一份产物 · BLK-DPI-02** |
| **F-DPI-03** | 分家后 LTE 仍能校验 `page-*` 的 CSS 一致性 | `css_gen.py:232-243`：`expected = parsed.get(template.render_grid_class)`，`if expected:` 才比对。搬走后 75 张 `page-*` 的 `expected` 为 None → **静默跳过**；`validator.py:450` 与 `mosaic/render_check.py:50` 均走这条 | **校验空转假绿 · BLK-DPI-03** |
| **F-DPI-04** | 新 CSS 文件可直接沿用现有防重复审计 | `css_gen.py:409-415` `lte_grid_classes_outside_marker` 先找 `LTE_MARKER_START/END`，找不到 `return []`；`lte_journal_css_audit.py:43` 默认只扫 `JOURNAL_SCREENS_CSS`；`test_lte_css_sync.py:66` 同 | **新文件无防重复 · BLK-DPI-04** |
| **F-DPI-05** | §10.1 已列全会红的既有测试 | 漏 `tests/unit/trip/test_asset_version.py`（钉 bundle 哈希金样，注释头 40 余行 bump 日志，L15 明写「Bump only when templates/visual-journal bundle bytes change」）；漏 `tests/unit/layout_engine/test_lte_css_sync.py`（marker / 重复断言） | **漏两处必红 · BLK-DPI-05** |
| **F-DPI-06** | CI 加一条 `pytest -m pipeline_isolation` 是净增保护 | `.github/workflows/ci.yml:1-4` 自述 hobbyist 预算；`test-pr`（L143-155）已跑 `-m "not integration and not e2e ..."` 全量 fast 套件，§8.1 要打 mark 的八个文件全在其中 | **纯重复分钟 · BLK-DPI-06** |
| **F-DPI-07** | §4.2 十条窄缝已覆盖全部跨族接触点 | 漏两处：`layout_engine/mosaic/render_check.py:15-17` 与 `layout_engine/render_binding.py:10` 均在游记侧包内硬编码 `templates/visual-journal/journal-screens.css` 路径，且与 `travelogue/paths.py:263` 的 `JOURNAL_SCREENS_CSS` 常量重复定义 | **窄缝漏登记 · BLK-DPI-07** |
| **F-DPI-08** | `chapters.py` 分家后可压到 ≤120 行（AC-DPI-12） | 现 526 行，含 `enrich_screen_tones` 调用、手机 screens 展开（`mobile_screens`）、screen-spread、folio plan（`resolve_folio_plan`）、trip-index、breath / 高光注入等**双边共享 helper 编排** | **数字无依据 · BLK-DPI-08** |
| **F-DPI-09** | 删 `:not([data-pattern^="page-"])` 只需规则集合等价证明（D-DPI-10 / AC-DPI-06） | 该 `:not()` 位于 `journal-screens.css` 3846–4030 的 contain-collapse opt-out 链（同串含十余个 `:not()`）。`test_asset_version.py` bump 日志 2026-07-27 (h) 记录该链曾被 `export --sync-journal` regression 打断并需人工恢复 | **高风险改动 · BLK-DPI-09** |
| **F-DPI-10** | 已渲染 trip 只需「文档写明需重渲染」（§10.3） | `layout_templates/css_stale.py` 专为「trip 本地 `journal-screens.css` 缺 grid class」而存在（AC-P16-11），说明该坑已踩过；`engine.py:605-607` 的 cache-bust 注释是第二处证据 | **回滚缺失 · BLK-DPI-10** |
| **F-DPI-11** | R-DPI-05 的缓解「W0 可单独合入」足够 | PRD 全文无「何时必须做」的门；`curate.py`（2014 行）已在 `scripts/lint_csc_god_module_ratchet.py` 的 god-module 棘轮内，说明本仓库有「债务不设门就长期存在」的历史 | **无排期门 · BLK-DPI-11** |
| **F-DPI-12** | 隔离 = 代码隔离 | PRD 未覆盖夹具 / 金样。现网 `tests/fixtures/phase16-dogfood` 被 `phase16_template_eval.py`、`phase17_golden_metrics.py` 等多个门读；作品集夹具在 `tests/unit/layout_engine/fixtures/editorial_series/`（MSP BLK-MSP-03 刚处理过一次同名冲突） | **夹具层未隔离 · BLK-DPI-12** |
| **F-DPI-13** | 装配层已真隔离，本波不动 | 复核：`curate.py:1361-1394` 二分；`pyproject.toml:165-177` 契约实跑 4 kept / 0 broken；`registry.py:356-359` `page-*` 出 MCS；`api.py` 不导出 `editorial_series` | **属实 · 保持** |
| **F-DPI-14** | 游记渲染确定性，可做字节比对 | `travelogue/render/**` 无 `datetime.now` / `time.time` / `uuid` / `utcnow`；唯一非确定源是 `?v=` 内容哈希（F-DPI-01） | **属实 · 归一化 `?v=` 后成立** |
| **F-DPI-15** | `include_zip` / `include_pages` 可从 `export_trip_longshot` 收回 | 链路核实：`export_handlers.py:805-812` 决定 → `:902-903` 传入 → `longshot.py:1108-1149` 过一手 → `portfolio_pages.py:294-324` 真正消费。中间层无逻辑 | **属实 · 保持** |
| **F-DPI-16** | 窄缝 ≤ 12 是合适的硬门（OQ-DPI-06 建议） | 现表 10 条；BLK-DPI-07 要求新增 2 条 → 恰好 12，**零余量**，第一次正常演进就会撞门 | **数字需重定 · 并入 BLK-DPI-07** |

---

## 4. Must-Fix（回写 v0.2.0 前不批 W1 开工）

| ID | 挡哪一波 | 要求 |
|----|----------|------|
| **BLK-DPI-01** | **W1（方向级）** | **bundle version 按管线分算。** 现 `_longshot_bundle_version`（`render/context.py:53-69`）是横跨两条管线的全局内容哈希，写进每张 HTML 的 `?v=`（F-DPI-01）。改为按身份计算：游记 HTML 只摘要游记实际加载的文件（`journal.css` + `journal-screens.css` + 游记 JS/CSS），作品集只摘要自己那份（`journal.css` + `portfolio-pages.css` + 共享 JS）。**禁止**把 `portfolio-pages.css` 塞进游记的哈希列表（会让改作品集 CSS 改动游记产物字节），也**禁止**不塞（会吃旧缓存，`engine.py:605-607` 已踩过一次）。同时 D-DPI-01 / AC-DPI-07 / AC-DPI-08 的「字节级一致」改口径为：**把 `?v=<hash>` 归一化为占位符后字节级一致**；另立一条 AC 单管 `?v=` 本身（游记 `?v=` 不因作品集 CSS 变化而变，反之亦然）。新增 D 条目记录此决策。 |
| **BLK-DPI-02** | W1 产物 | **第三份产物要有归属。** `layout_templates/cli.py:101` 的 `export --out` 缺省写 `journal-screens.generated.css`（F-DPI-02），§5.1 只列两份。二选一写死：(a) 一并分成 `journal-screens.generated.css` / `portfolio-pages.generated.css`；(b) 确认其无运行时消费者后**废弃**并同步 `docs/GUIDE-PHASE16-layout-template-engine.md:159`、MSP §710。评审倾向 **(b)**——少一份产物少一处漂移源，但须先跑一遍全库检索确认无人读。§5.1、§5.2、BE-DPI-07 同步。 |
| **BLK-DPI-03** | W1 校验 | **补上 parity 的作品集分支，并用反例证明它不是空的。** `validate_css_bundle`（`css_gen.py:211-244`）在找不到同名 grid class 时静默跳过（F-DPI-03），分家后 75 张 `page-*` 全落该分支。改造：给 `validate_css_bundle` 增 bundle 来源参数（按 template id 前缀选 `journal-screens.css` 或 `portfolio-pages.css`），`validator.py:450` 与 `mosaic/render_check.py:50` 两处调用点同步。**新增 AC**：故意把 `portfolio-pages.css` 中某张脸的 `grid-template-columns` 改错一位，`python -m travelogue.layout_templates.cli validate --semantic` **必须红**；不红即判该门为空。BE-DPI-11 估时相应上调（原 1.2 d 未含此项）。 |
| **BLK-DPI-04** | W1 防重复 | **新文件必须自带 marker 对并进双文件审计。** `lte_grid_classes_outside_marker` 无 marker 即 `return []`（F-DPI-04），`lte_journal_css_audit.py` 默认只扫游记文件。要求：`portfolio-pages.css` 写入 `@lte-generated:start/end` 与 `@portfolio-overlays:start/end` 两对 marker（命名不得复用 `journal-overlays`）；`lte_journal_css_audit.py` 扩为双文件（或新增同构脚本）并保持 `--fail-on-duplicates`；`test_lte_css_sync.py` 的 marker 存在性、`inside/outside` 重复断言复制一份到新文件。**理由**：今天 147–186 那段手写 `page-*` 规则之所以能长期存在且注释还写着「Must stay outside @lte-generated」，正是因为它在审计视野之外——不能把同一个坑复制到新文件。 |
| **BLK-DPI-05** | W1 测试 | **§10.1 补两处必红。** 加 `tests/unit/trip/test_asset_version.py`（钉 bundle 哈希金样，F-DPI-05）与 `tests/unit/layout_engine/test_lte_css_sync.py`（marker / 重复断言）。同时定 bump 纪律：**一个里程碑最多一次 bump，附一行原因**，写进 §10.1；禁止同一波内多次 bump（现注释头已有 40 余行历史记录，再无节制会彻底变噪音）。 |
| **BLK-DPI-06** | **W0** CI | **不在 CI 新增重复 pytest 步骤。** `test-pr` 已跑全量 fast 套件、包含 §8.1 全部八个文件（F-DPI-06），再单跑 `-m pipeline_isolation` 是纯重复分钟数，与 `ci.yml:1-4` 自述的 hobbyist 预算冲突。改为：**marker 保留**（价值在本地一条命令与人工排查），CI 侧的门由 ① `lint` job 的 `lint_dual_pipeline_ownership.py` ② 已在 fast 套件内的形状断言 ③ 双 CSS 漂移门 三者承担。§8.5 CI 接线表按此重写；`pyproject.toml` marker 说明里写清「本 mark 供本地与排查使用，不在 CI 单独成步」。 |
| **BLK-DPI-07** | **W0** 窄缝表 | **补登两条窄缝，并重定窄缝上限。** `mosaic/render_check.py:15-17` 与 `layout_engine/render_binding.py:10` 在游记侧包内硬编码共享 CSS 路径且与 `paths.py:263` 重复定义（F-DPI-07）。**首选处置**：两处改为 `from travelogue.paths import JOURNAL_SCREENS_CSS`，消除重复定义后**不占窄缝额度**（它们只读游记文件，属游记独占）。若本波不改，则必须登记为 S-11 / S-12。同时 OQ-DPI-06 的窄缝上限从 12 改为 **14**（现表 10 + 合理余量 4），并明写「上限是讨论触发器，不是硬性配额；触顶必须开 PRD 复核」（F-DPI-16）。 |
| **BLK-DPI-08** | **W0** 验收 | **AC-DPI-12 改结构判据，去掉行数。** `chapters.py` 现 526 行且含大量双边共享 helper 编排（F-DPI-08），钉 ≤120 行只会逼出为过门而拆的空文件。改为：① `chapters.py` 内除 §4.2 S-04 登记的分发点外**不含** `is_portfolio` 分支；② `chapters.py` 不含任何仅一侧使用的业务逻辑（按符号清单断言：高光注入、长图过滤、呼吸屏、章头、trip-index 必须已迁出到 `journal_chapters.py`；`page-*` / 16:9 / 空章省略必须已迁出到 `portfolio_chapters.py`）；③ `hideChapterChrome` 全库检索为 0（此条保留）。 |
| **BLK-DPI-09** | **W1** 视觉 | **删 `:not()` 前必须过渲染几何门。** 该 `:not([data-pattern^="page-"])` 长在游记 contain-collapse opt-out 链上，该链曾被 `export --sync-journal` regression 打断并需人工恢复（F-DPI-09）。AC-DPI-06 的「规则集合等价」保留为必要条件，另加两条：① 删项前后 `python scripts/lte_probe_regress.py --screenshot --strict` 均绿；② 新增 opt-out 清单断言——断言 `mixed-1l1p` / `landscape-3-editorial` / `person-pair` / `person-triple` / `editorial-4mix` 等 bump 日志点名过的 pattern 在 contain 情形下**不塌陷**（断言渲染几何，不断言选择器文本）。BE-DPI-10 估时从 0.8 上调；两条不满足，视觉席不签 W1。 |
| **BLK-DPI-10** | **W1** 回滚 | **已渲染 trip 要有可见处置，不能只写文档。** D-DPI-11 改变 `@import` 加载关系，磁盘上 `trips/*/` 各有一份旧 `journal-screens.css`（F-DPI-10）。要求：① `layout_templates/css_stale.py` 扩到 `portfolio-pages.css`，并把「缺文件」也算陈旧（现只检缺 grid class）；② 陈旧时**预览侧给可见提示或自动重渲染**，落点与文案在实施时定；③ 新增 AC：拿一份 W1 之前渲染的 trip，不重渲染直接打开预览，断言用户能看到明确提示而不是坏版式。§10.3 从「文档写明」升级为带 AC 的任务项（新增 BE-DPI-18）。 |
| **BLK-DPI-11** | **W0** 排期 | **给「什么时候必须做」一条硬门。** 现 R-DPI-05 只说「W0 可单独合入」（F-DPI-11），本仓库有债务不设门就长期存在的先例（`curate.py` 2014 行已进 god-module 棘轮）。写进 §2.1：**G-DPI-06 —— 下一次动到任一管线读者面（渲染 / CSS / 版式几何）的功能波开工前，W0 必须已合入**；W1–W3 允许延后，但每次延后须在 `docs/ARCH-OPT-STATUS.md` 或本 PRD 状态行记一次。同时 §13 补「不做的代价」实证：`journal-screens.css:147-186` 的越界手写块、3846–4030 的 `:not()` 链、`css_gen.py:153-159` 的编译器全局改写，三处均为**已发生**的污染而非假想风险。 |
| **BLK-DPI-12** | **W0** 夹具 | **新增「夹具与金样所有权」一节。** 现 PRD 只覆盖代码，两条管线可通过共享测试数据重新耦合，且这种耦合 lint 看不见（F-DPI-12）。要求：① 在 §4 增 §4.3，按 §4.1 同样的三列写清游记金样（`tests/fixtures/phase16-dogfood`、`render_golden` 系列等）、作品集夹具（`tests/unit/layout_engine/fixtures/editorial_series/`）与共享夹具；② 共享夹具进窄缝表；③ 规则：**谁的金样谁改；重新生成共享夹具的 PR 必须双边回归**；④ `lint_dual_pipeline_ownership.py` 扫描范围加 `tests/fixtures/**` 与 `tests/**/fixtures/**` 的引用方向。MSP BLK-MSP-03 刚处理过一次夹具同名冲突，可作先例引用。 |

---

## 5. Should-Have（不挡 W1，回写时一并处理）

| ID | 内容 |
|----|------|
| **SHD-DPI-01** | §5.2 的迁移六步建议每步一个提交，且提交信息带步号（`W1-3/6` 之类），便于出问题时精确回退到「改了加载关系但还没删 `:not()`」这种中间态。 |
| **SHD-DPI-02** | `.cursor/rules/dual-pipeline.mdc` 建议同时写进「两条管线各自的入口文件清单」，让 AI 改动时能快速定位落点，而不只是列禁令。 |
| **SHD-DPI-03** | §14「一页速查」建议加一行：改动前先跑 `python scripts/lint_dual_pipeline_ownership.py --explain <file>`，让 lint 能反查「这个文件归谁」，而不是只在越界时报错。 |
| **SHD-DPI-04** | BE-DPI-03 的窄缝基线 JSON 建议复用 `csc-w2a-facade-deep-import-baseline.json` 的 owner + expiry 字段结构，与现网棘轮基线保持同构，便于统一审计。 |
| **SHD-DPI-05** | AC-DPI-16/17/18 三条独立迭代烟测，建议除机器 diff 外附狗粮手测记录（用户体验席主诉）：真改一张轨道、真打开对面的 demo 肉眼确认。 |
| **SHD-DPI-06** | `journal.css` 保持共用（OQ-DPI-01 建议采纳），但建议在实施时给它加一句顶部注释，说明它是**唯一**双管线共享的读者面 CSS，改动须双边回归——防止以后有人往里塞某一侧的专用规则。 |

---

## 6. 开放问题裁决

| ID | 问题 | 会议裁决 |
|----|------|---------|
| **OQ-DPI-01** | `journal.css` 是否分家？ | **不分**（七席一致）。它是壳与变量的单一真相；分了立刻产生两份变量真相。采纳 SHD-DPI-06 加注释防污染。 |
| **OQ-DPI-02** | W2 是否删 `context.py` 的 `page-` 前缀嗅探？ | **不删，只参数化**（架构 + 视觉一致）。理由：BLK-DPI-01 已经要在同一波改 bundle version 的判族逻辑，再叠一处判族改动风险不可控。留待作品集下一次几何迭代确认参数够用后单独处理。 |
| **OQ-DPI-03** | `page-*` 是否要独立槽数上限？ | **归 TSU，本波不定阈值**（一致）。本波只做 `validator.py` 的分族参数化，把 `_dense_freeze_exempt` 的前缀豁免升级为显式族参数，不动数值。 |
| **OQ-DPI-04** | 作品集是否要独立 `reading_profile` 模块？ | **不做**（一致）。`magazine` 档现网已有，`reading_profile.py:392` 一处默认选择属窄缝 S-05，够窄。 |
| **OQ-DPI-05** | 上游若要按身份分策略怎么办？ | **触发时再开 PRD**（一致）。D-DPI-02 作为铁律保留，防止顺手分家。**补充**：算法席要求把「夹具同源」也纳入上游共享的定义（并入 BLK-DPI-12）。 |
| **OQ-DPI-06** | 窄缝数是否设硬门？ | **设，但上限改 14，且定性为讨论触发器而非配额**（开发席主诉，F-DPI-16）。现表 10 条，BLK-DPI-07 若走「改走 `paths.py`」则不增；余量留给正常演进。触顶必须开 PRD 复核，不得静默扩表。 |

---

## 7. 里程碑放行条件（本纪要授权范围）

| 里程碑 | 放行条件 |
|--------|---------|
| **W0** | 回写 **BLK-DPI-06 / 07 / 08 / 11 / 12** 后**即可开工**（这五条只涉门禁、窄缝表、夹具与排期，不动 CSS 与渲染） |
| **W1** | 须 **BLK-DPI-01 / 02 / 03 / 04 / 05 / 09 / 10** 全部回写且 W0 已合入。**BLK-DPI-01 是方向级前置**，它不定，W1 的出门判据无法成立 |
| **W2** | 须 W1 出门门全绿；`chapters.py` 结构判据（BLK-DPI-08 改写后）作为唯一验收 |
| **W3** | 须 W2 合入；FE 侧以 `journalExportPanelSnapshot` 零 diff 为主判据 |

**本纪要不关** AC-DPI-16/17/18（独立迭代烟测须在 W2 之后真跑，含狗粮手测）。**不动** `pyproject.toml` 既有 4 条 import-linter 契约文本。**不批**在本波顺手处理 `curate.py` 或 `context.py` 的整体拆分。
