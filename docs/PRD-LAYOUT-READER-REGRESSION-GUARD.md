# Travelogue · 读者排版回归守护 PRD（Layout Reader Regression Guard）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.1** |
| **状态** | **有条件通过 · 评审收敛 + 落地核实（2026-07-05）** |
| **特性代号** | **LRG**（Layout Reader Regression Guard，读者排版回归守护） |
| **文档类型** | Phase 16 后续 · 读者可见排版可靠性 + dogfood 验收闭环 PRD |
| **前置条件** | Phase 16 LTE `export --sync-journal` 已上线；Phase 15 MCS、P21 density budget、P23 peak/moment、P5 folio lite 已落地；2026-07-05 热修 commit `22c1767` 已恢复 ticket 章节 / EXIF / mosaic-5 contain overlay |
| **关联文档** | [DESIGN-PHASE16-layout-template-engine.md](./DESIGN-PHASE16-layout-template-engine.md)、[PRD-EXPERIENCE.md](./PRD-EXPERIENCE.md)、[PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md)、[PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md)、[PRD-MOSAIC-CONFIG-RESTORE.md](./PRD-MOSAIC-CONFIG-RESTORE.md)、[PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md)、[ROADMAP-PHASE18-BOOK-QUALITY.md](./ROADMAP-PHASE18-BOOK-QUALITY.md)、[MCR-RELEASE-NOTE.md](./MCR-RELEASE-NOTE.md)、[ADR-014](./adr/014-mosaic-proximity-window-order.md) |
| **更新日期** | 2026-07-05 |

> **定位**
>
> - **问题**：Phase 16 引入 `export --sync-journal` 后，`journal-screens.css` 中 **`@journal-overlays:end` 之后的手写 overlay 会被静默截断**；章节票根、EXIF 脚注、mosaic contain 等读者可见样式曾整段丢失，单测一度 FAIL 仍可 merge，用户反馈「以前正常、现在错乱」。
> - **输出**：① 建立 overlay **不可丢失** 工程门禁；② 固定 dogfood 相册 **re-curate + render + 目视** 验收流水线；③ 在数据层面对 **拼图连拍门槛 / window_order** 做产品化决策并留档；④ 为 URO `enabled=true` 提供**不建立在坏排版基线之上**的前置条件。
> - **铁律**：① 所有读者可见、非 LTE 生成的 layout 样式 **只能** 维护在 `templates/visual-journal/journal-screens-overlays.css`；② **`export --sync-journal` 不得在没有 overlay 回归绿灯的情况下单独 merge**；③ 本 PRD **不**新增模板 SKU、**不**改 MCS 打分公式（拼图策略仅调 config 默认值并 dogfood 验证）；④ URO `enabled=true` **不得**作为本 PRD 的 merge 门禁（归属 AC-URO-BLIND）。

---

## 0. 术语与范围

| 术语 | 含义 |
|------|------|
| **Overlay CSS** | `journal-screens-overlays.css` 内容；经 sync 注入 `journal-screens.css` 的 `@journal-overlays:start…end` 块 |
| **LTE 生成 CSS** | YAML → `@lte-generated:start…end` 块；槽位 grid 拓扑权威 |
| **读者可见排版** | 章节分隔条、EXIF 脚注、folio plate _meta、moment 标签、mosaic contain _stage 等非纯 grid 规则 |
| **Dogfood trip** | 固定 2～3 本相册，用于每次 layout 变更后的 before/after 对比 |
| **trip bundle** | render 输出目录内 `index.html` + `journal.css` + `journal-screens.css` 及 cache-bust 版本 |
| **Type-A 变更** | overlay CSS / LTE sync / 读者可见样式（走 §3.3.2 Type-A 路径） |
| **Type-B 变更** | curate 算法 / config 默认值 / MCS 窗宽（走 §3.3.2 Type-B 路径） |

**配置术语对照（避免与 ingest 混淆）**：

| 配置项 | 默认 | 作用阶段 | 含义 |
|--------|------|----------|------|
| `layout.mixed_proximity_seconds` | **900** | **curate / 组屏** | 混排/拼图窗口内 `takenAt` 最大跨度 |
| `ingest.burst_seconds` | **3** | **ingest** | 近重复/连拍 ingest 去重 |

**本 PRD 范围外**：URO 盲评（AC-URO-BLIND）、新模板 SKU、mobile legacy `items[]` 引擎、全站 Percy 级视觉 CI。

---

## 1. 背景与问题

### 1.1 2026-07 事故摘要（已热修，机制未闭环）

| 症状 | 用户体感 | 根因（已验证） | 热修 commit |
|------|----------|----------------|-------------|
| 章节标题/副标/进度/pull quote 纵向堆叠、巨型字 | 「章节标题变乱」 | `.chapter-separator--ticket` overlay **整段缺失**；legacy `.chapter-separator__title` 误作用于 ticket | `22c1767` |
| EXIF 黑条变正文流、48px 字 | 「EXIF 展示变了」 | `.moment-exif-bar` / slot flex overlay **整段缺失** | `22c1767` |
| 5 格拼图底行横图被裁切 | 「拼图错位/遮挡」 | mosaic-5 contain 时 screen 仍锁 16:9；overlay 缺 stage collapse 规则 | `22c1767` |
| 5/6 格拼图偏少 | 「拼图变少」 | **独立问题**：`mixed_proximity_seconds` 过严 + P21 density + `window_order`；与 overlay 无关但需 dogfood 决策 | config 默认 900s（同 commit 批次） |

**共性根因链**：

```text
Phase 16 · export --sync-journal
  └─ _truncate_trailing_legacy_after_overlays()
       └─ 删除 @journal-overlays:end 之后一切手写 CSS
            └─ 票根 / EXIF / 部分 reading-experience 规则曾写在 marker 外
                 └─ 后续「恢复」只写回 legacy 全幅 chapter-separator，漏 ticket-stub + P23
                      └─ test_reading_experience 曾 FAIL 仍被 merge → 静默回归
```

### 1.2 问题 ID

| ID | 问题 | 严重度 | 类型 |
|----|------|--------|------|
| **LRG-P-01** | overlay 写在 marker 外或被 sync 截断，**无 CI 阻断** | **P0 · Blocker** | 工程机制 |
| **LRG-P-02** | 关键读者样式丢失时，**HTML 仍正常渲染**（无报错），仅视觉错乱 | **P0** | 可观测性 |
| **LRG-P-03** | dogfood 相册无固定 **re-curate + render + 指标** 验收表 | **P0** | 流程 |
| **LRG-P-04** | `trips/*/journal-screens.css` 与 template 双轨；linzhi 曾作「权威副本」 | P1 | 工程债 |
| **LRG-P-05** | Studio 预览 CSS cache-bust 不足，用户看到旧 bundle | P1 | DX |
| **LRG-P-06** | `body { font-size: 48px }` 在 web layout 下 cascade，overlay 缺失时灾难性放大 | **P1** | 样式债 |
| **LRG-P-07** | `chapterMeta` 回退相册名，与章节标题语义重复 | **P1 · 体验** | 数据/文案 |
| **LRG-P-08** | `mixed_proximity_seconds` / `window_order` 调参无书面决策与 trip 级对比 | P1 · 产品 | 拼图策略 |
| **LRG-P-09** | URO 启用路径与排版基线未解耦 | P1 | 发布策略 |

### 1.3 与相邻模块边界

| 模块 | 关系 |
|------|------|
| **Phase 16 LTE** | grid CSS 权威在 YAML；**读者 overlay 权威在 overlays 源文件** — 本 PRD 补治理，不改 LTE 数据模型 |
| **MCR** | 拼图 **窗宽能力**；LRG 管 **渲染后读者可见**；二者 dogfood 可同一 trip，验收项分开 |
| **URO** | 正交；**须 LRG P0 绿灯后** 再推进 `usage_rules.enabled=true` 盲评 |
| **P21 density budget** | 保留；LRG 仅要求 dogfood 记录 dense 屏数量变化 |
| **P23 moment/EXIF** | overlay 规则归属 LRG 关键 selector 清单 |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-LRG-01** | overlay **不可丢失** | CI 必过：`test_lte_css_sync`（含 ticket / exif / mosaic-5 contain）+ `test_reading_experience` | **P0** |
| **G-LRG-02** | `export --sync-journal` 与 overlay 测试 **同一 CI job** | 改 `journal-screens-overlays.css` 或 `css_gen.py` 的 PR 必跑 sync + pytest | **P0** |
| **G-LRG-03** | 维护 **Overlay 关键 Selector 清单**（§3.2.2） | 清单内 selector 均存在于 `@journal-overlays` 块；缺则测试 FAIL | **P0** |
| **G-LRG-04** | 3 本 dogfood trip 固定验收流水线 | 每次 layout 相关 merge 附 dogfood 对比 JSON；**baseline 入库** `docs/acceptance-records/lrg-dogfood.<trip-id>.json` | **P0** |
| **G-LRG-05** | `demo-815dc906d3` 达到 **可演示态** | re-curate + render 后：屏数一致、章节 ticket 正常、EXIF 13px 黑条、mosaic-5 无底行裁切；**`trip.json` 屏数 = `index.html` 中 `.layout-screen` 数** | **P0** |
| **G-LRG-06** | 拼图策略 **书面决策** | ADR-014：`mixed_proximity_seconds` 默认值 + 是否调整 `window_order`；**W1 文档截止** | **P1** |
| **G-LRG-07** | 轻量视觉/计算样式回归 | Playwright：≥1 屏 computed style 断言或 golden 截图 diff（可选阈值） | **P1** |
| **G-LRG-08** | Studio 预览 bundle 版本可感知 | render 后 `journal.css` import 带 `?v=`；Studio 可选「样式过期」提示 | **P1** |
| **G-LRG-09** | `chapterMeta` 语义优化 | 无 `dividerPlace` 时不展示相册全名（或降级为地点缩写） | **P1** ↑ |
| **G-LRG-10** | web layout 下 root typography 重置 | `data-layout=web` 时 body 字号不回退 48px 灾难链 | **P1** ↑ |

> **v0.2.0 变更**：G-LRG-09 / G-LRG-10 自 P2 升为 **P1**（跨职能评审裁定）。

### 2.2 非目标

- **不**在本 PRD 默认开启 URO（`usage_rules.enabled` 仍为 `false`）。
- **不**恢复 deprecated mosaic SKU（2p3l-equal 等）。
- **不**要求全站 Percy / Chromatic 级像素 CI。
- **不**修改 ingest EXIF 提取逻辑（仅管 **展示** CSS/HTML）。
- **不**承诺 6 格 hero 拼图在所有相册出现（几何 + density + 连拍门槛仍适用）。

---

## 3. 总体方案

### 3.1 设计原则

```text
LTE YAML          →  grid 拓扑（@lte-generated）
overlays.css      →  读者可见行为（@journal-overlays）  ← 唯一手写入口
export --sync     →  合并二者；截断 marker 外内容（T-LRG-12 fail-fast）
CI                →  sync 后立即 pytest；FAIL = 不可 merge
Dogfood           →  Type-A（overlay）与 Type-B（curate）分路径验收
```

### 3.2 工程门禁（P0）

#### 3.2.1 CI 落点：扩展现有 `validate` job（**v0.2.1 修正**，不新建平行 job）

> **修正说明**：v0.2.0 曾提议新建 `layout-overlay-guard` CI job。经核实 `.github/workflows/ci.yml` 的 `validate` job 中 **"LTE journal CSS sync drift"** 步骤已实现 §步骤1+3（`export --sync-journal` + `git diff --exit-code journal-screens.css`），且 `test_lte_css_sync.py` / `test_reading_experience.py` 均为 `@pytest.mark.unit`，已被 `test-pr` job 的默认 `pytest tests/ -q -m "not integration and not e2e..."` 覆盖、**每个 PR 已在跑**。新建平行 job 会与既有步骤重复维护、逐渐漂移。因此 **T-LRG-01 改为「审计并强化现有步骤」**，不新增 job：

| 落点 | 现状 | v0.2.1 要求 |
|------|------|-------------|
| `validate` job · "LTE journal CSS sync drift" 步骤 | 已跑 export + git diff | **T-LRG-12** fail-fast 检测直接加进这一步（复用同一步骤，不拆分） |
| `test-pr` job · 默认 pytest | 已覆盖 `test_lte_css_sync.py` / `test_reading_experience.py` | 新增 overlay selector 测试（§3.2.2 新增项）默认继承同一路径，**无需额外配置** |
| 分支保护（GitHub 仓库设置） | **未核实**（本机无 `gh` CLI / 无 GitHub 访问权限，无法远程核对 required status checks） | **T-LRG-13**：工程需登录 GitHub 仓库设置，确认 `validate`（至少含上述步骤）已被设为 **required status check**；这是本次事故「测试 FAIL 仍可 merge」的直接根因，优先级高于新增任何 CI 步骤 |

**PR-warn / release-block 双段式约定**（沿用仓库既有惯例，见 `ci.yml` 内 Phase16/17 各步骤写法）：新增的 T-LRG-12 fail-fast 与 AC-LRG-03 负向测试均应遵循「PR 上 `continue-on-error: true` 观察期 → 转正后 release-block 严格模式」的两步上线节奏，而非一次性 hard fail，降低误报阻塞面。

**触发条件**（沿用 `validate` job 现有全量触发，不单独设条件路径）：PR 触及 `journal-screens-overlays.css`、`css_gen.py`、`layout_templates/**`、`journal-screens.css`。

#### 3.2.2 Overlay 关键 Selector 清单（权威）

| 分组 | 必选 substring / selector | 关联读者能力 |
|------|---------------------------|--------------|
| **Ticket 章节** | `chapter-separator--ticket[data-block`、`.chapter-separator__ticket-left`、`grid-template-columns: auto 1px` | 票根章节分隔 |
| **EXIF 脚注** | `.moment-exif-bar`、`background: #0a0a0a`、`.layout-slot:has(.moment-exif-bar)` | P23 池内 EXIF |
| **Folio plate** | `.folio-plate-meta--top`、`position: absolute` | Plate · NN 标 |
| **Mosaic contain** | `screen-mosaic-5-main-portrait-3land"]:has(.layout-slot__img--contain`、`aspect-ratio: unset` | 5 格竖槽不裁底行 |
| **Breath / snap** | `[data-snap="proximity"]`、`.breath-pause-screen` | 阅读体验基线 |

清单维护于 `tests/test_lte_css_sync.py`（已实现部分）+ 本文档 §3.2.2；新增读者 block 须同步增测。

#### 3.2.3 Export fail-fast（T-LRG-12 · v0.2.0 必改，落点已在 v0.2.1 明确）

`css_gen._truncate_trailing_legacy_after_overlays()` 在截断前检测 `@journal-overlays:end` 之后是否存在 **非空白、非注释** CSS：

| 模式 | 行为 | 适用 |
|------|------|------|
| **默认（CI / strict）** | **exit 1** + stderr 列出被截断 selector 预览 | **加入 `validate` job 现有 "LTE journal CSS sync drift" 步骤**（§3.2.1）、本地 `export --sync-journal` |
| **warn-only** | stderr WARNING，仍截断 | 本地迁移过渡期（`--warn-trailing-legacy`）；上线首周 PR 侧建议先走 `continue-on-error: true` 观察，无误报后转严格 |

**验收**：故意在 marker 外追加规则 → export **必须非零退出**。

**实现约束（AC-LRG-03 / T-LRG-11 负向测试）**：负向测试须在 **内存字符串或临时文件拷贝** 上做删除/追加模拟，**不得**对仓库内真实 `journal-screens-overlays.css` / `journal-screens.css` 做写入-还原式操作，避免并发 CI 或测试失败中断时把源文件留在破损状态。

#### 3.2.4 贡献者约束（写入 CONTRIBUTING 或 Phase 16 DESIGN 补丁）

1. **禁止**在 `journal-screens.css` 的 `@journal-overlays:end` 之后追加手写规则。
2. **禁止**仅改 `trips/*/journal-screens.css` 而不改 template overlays（trip 副本由 render 覆盖）。
3. `export --sync-journal` 后必须跑 overlay 测试再 commit。

### 3.3 Dogfood 验收流水线（P0）

#### 3.3.1 固定相册

| Trip ID | 角色 | 覆盖点 |
|---------|------|--------|
| `demo-815dc906d3` | 连拍/拼图边界 · 竖图占比高 | 5 格 burst、mosaic-5 contain、112↔140 屏同步 |
| `linzhi` | 历史稳定基线 · folio 完整 | ticket + EXIF + 多章 |
| `demo-80301df45c`（或 MCR 文档指定横图 trip） | 横图 hero 拼图 | 6 格 / hero-plus 曝光 |

> **v0.2.1 核实**：已用 shell 直接核对 `trips/demo-815dc906d3/` 与 `trips/demo-80301df45c/`，两者均存在且含完整渲染产物（`trip.json`、`index.html`、`journal-screens.css` 等），可直接用于 T-LRG-04。`linzhi` 为长期维护相册，无需核实。

#### 3.3.2 验收路径：Type-A vs Type-B（v0.2.0 必改）

| 路径 | 触发变更 | 必跑步骤 | PR 附件 |
|------|----------|----------|---------|
| **Type-A** | overlay CSS、LTE YAML、sync/css_gen、读者 HTML 模板 | export → pytest → **3 trip render**（可 skip re-curate） | §5.2 目视 + **375/768 截图**（见 §5.2） |
| **Type-B** | `mixed_proximity`、`window_order`、MCS、P21 density、URO config | **re-curate** → render → `lrg_dogfood_report.py` | dogfood JSON delta + ADR-014 引用 |
| **Type-A+B** | 同 PR 含 overlay 与 curate | 两路径 **并集** | 合并附件 |

#### 3.3.3 单次验收步骤

```bash
# 1. re-curate（Type-B 必跑；Type-A 可选）
python scripts/mcr_eval_recurate.py <trip-id>   # 或 Studio curate

# 2. render（写 index.html + CSS bundle）
python -m travelogue.cli render trips/<trip-id>/trip.json

# 3. 指标采集
python scripts/lrg_dogfood_report.py --trip trips/<trip-id> --out .cache/lrg-dogfood/<trip-id>.json

# 4. 与 baseline 对比（入库路径）
diff docs/acceptance-records/lrg-dogfood.<trip-id>.json .cache/lrg-dogfood/<trip-id>.json

# 5. 目视 checklist（§5.2）
```

#### 3.3.4 `lrg_dogfood_report.py` JSON Schema（P0 交付 · v0.2.0 扩展）

**必填字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `tripId` | string | |
| `screenCount` | int | `trip.json` 屏数 |
| `htmlLayoutScreenCount` | int | `index.html` 中 `.layout-screen` 数；**须与 screenCount 相等**（G-LRG-05） |
| `patternHistogram` | object | pattern → count |
| `mosaicDecisionSummary` | object | window 4/5/6 成功/失败计数 |
| `momentExifBarCount` | int | |
| `chapterSeparatorTicketCount` | int | |
| **`burstPassRate`** | float | 1P+4L / 1P+5L 窗口 burst 通过率 |
| **`windowExposure`** | object | `{ "4": n, "5": n, "6": n, "9": n }` 各窗宽尝试/成功曝光 |

**Baseline 入库路径（v0.2.1 修正）**：`docs/acceptance-records/lrg-dogfood.<trip-id>.json`（**非** `tests/fixtures/lrg/`，**非**仅 `.cache/` gitignore）。

> **修正说明**：`docs/acceptance-records/` 是仓库既有的「per-trip 验收基线/eval 快照」权威存放位置（357+ 个 `<eval-name>.<trip-id>[.variant].json` 文件，例如 `phase16-template-eval-baseline.json`、`aesthetic-*.<trip-id>.json`），LRG 的 dogfood baseline 应沿用该惯例，命名为 `lrg-dogfood.<trip-id>.json`。
>
> **与 `tests/fixtures/phase16-dogfood/` 的边界**（避免混淆）：
> - `tests/fixtures/phase16-dogfood/*/trip.json` 是**渲染前**的策展结构固定样本，供 `phase16_template_eval.py` 等脚本做**纯统计**（pattern 曝光率、多样性），**不含**渲染产物。
> - LRG 需要的是**渲染后**产物（`index.html` / `journal-screens.css`）上的读者可见断言（overlay selector、EXIF 计算样式、屏数一致性），因此 dogfood 对象是 `trips/<trip-id>/` 下的**真实 trip**（`demo-815dc906d3`、`linzhi`、`demo-80301df45c`，已核实三者均存在且含完整渲染产物），而非新建 fixture 相册。
> - 两套目录**不合并**，职责不同；本文档不再使用 `tests/fixtures/lrg/` 这一命名。

更新 baseline 须 PR 说明 + §5.2 签字。

#### 3.3.5 回归对比维度

| 维度 | 阈值 | 说明 |
|------|------|------|
| `screenCount` | 与 baseline **差 ≤ 5%** 或 PR 说明 | 防 silent skip |
| `htmlLayoutScreenCount` | **= screenCount** | G-LRG-05 |
| `main-portrait-3land` / `landscape-4` / `mosaic-6` 计数 | PR 附 delta 表 | Type-B 必解释 |
| `burstPassRate` / `windowExposure` | PR 附 delta | Type-B / ADR |
| Playwright computed | EXIF `fontSize ≤ 14px`、背景 `#0a0a0a`；ticket title `≤ 24px` | 防 overlay 丢失 |
| 目视 | §5.2 checklist 全绿 | 发布前 |

### 3.4 拼图策略决策（P1 · ADR-014 · W1 截止）

**不在 LRG 代码库内改算法**，仅要求 **默认值变更须 dogfood + ADR**。

| 决策项 | 当前默认（2026-07-05） | 待决问题 | 建议验证 |
|--------|------------------------|----------|----------|
| `layout.mixed_proximity_seconds` | `900`（15min） | 是否过松导致无关照片成组？ | 3 trip `burstPassRate` + 目视 |
| `mosaic.density_budget.window_order` | **`(5, 4, 6, 9)`**（`travelogue/config/mosaic.py` 权威） | 4 先于 6 是否压制 hero 6 格？ | demo-815dc906d3 `windowExposure` |
| URO `enabled` | `false` | 何时开启盲评？ | **G-LRG-01～05 全绿后** |

**文档**： [ADR-014-mosaic-proximity-window-order.md](./adr/014-mosaic-proximity-window-order.md) — **LRG-W1 结束前须填决议并合并**（非 W2）。

### 3.5 Studio 预览一致性（P1）

| 项 | 方案 |
|----|------|
| CSS cache-bust | 已有 render 写 `journal-screens.css?v=`；LRG 要求 **每次 render 递增 bundle version** |
| stale 提示 | Studio trip-preview 对比 trip `assetVersion` / css mtime，不一致则 banner「请重新渲染」 |
| 开发 DX | 文档说明：改 overlays 后需 `render` 或复制 template css，**非**仅 refresh |

### 3.6 章节 meta 与 typography（P1）

参见 [PRD-CHAPTER-NAMING.md](./PRD-CHAPTER-NAMING.md)：

- `dividerPlace` / `daySpan` **优先**作 `chapterMeta`；
- 相册 `meta.title` **不再**作为 ticket 副标默认展示（**G-LRG-09**）；
- 实施点：`travelogue/render/screen_tone.py` · `_chapter_meta_line`。
- **G-LRG-10**：`data-layout=web` 下重置 body 字号，阻断 48px cascade。

### 3.7 发布说明模板（Layout 相关 PR）

PR description **须**包含（可复制）：

```markdown
## LRG 验收
- [ ] 变更类型：Type-A / Type-B / A+B
- [ ] CI `validate` job（含 LTE journal CSS sync drift 强化步骤）绿
- [ ] Dogfood JSON 附件 / baseline diff
- [ ] §5.2 目视（trip: ___）
- [ ] 375px / 768px 截图（Type-A 必附）
- [ ] ADR-014 引用（Type-B 必附）
```

---

## 4. 验收标准（Acceptance Criteria）

### 4.1 P0 Gate（LRG 特性可发布）

| AC | 描述 | 验证 |
|----|------|------|
| **AC-LRG-01** | CI `validate` job（LTE journal CSS sync drift 强化步骤）绿，且已确认为 required status check | GitHub Actions / 本地等价 + T-LRG-13 |
| **AC-LRG-02** | Overlay 清单 §3.2.2 全项有单测 | `test_lte_css_sync` + `test_reading_experience` |
| **AC-LRG-03** | 故意删除 ticket 规则 → CI **必须 FAIL** | **自动化负向 pytest**（`test_overlay_ticket_removal_fails_guard` 或等价）；禁止仅 manual drill |
| **AC-LRG-04** | 3 本 dogfood baseline JSON **入库** | `docs/acceptance-records/lrg-dogfood.*.json` + `lrg_dogfood_report.py` |
| **AC-LRG-05** | `demo-815dc906d3` 目视 checklist 全绿；屏数 HTML = trip.json | §5.2 签字 + `htmlLayoutScreenCount` |
| **AC-LRG-06** | IMPLEMENTATION 文档 §1 行「overlay 只写 overlays.css」 | 文档 PR |
| **AC-LRG-12** | export marker 外非空 CSS → **非零退出** | T-LRG-12 + 单测 |

### 4.2 P1 Gate

| AC | 描述 |
|----|------|
| **AC-LRG-07** | ADR-014 合并并引用 dogfood `burstPassRate` / `windowExposure` |
| **AC-LRG-08** | Playwright 至少 2 个 computed-style 断言进 CI（EXIF + ticket） |
| **AC-LRG-09** | Studio stale CSS banner 或等价机制 |
| **AC-LRG-10** | web layout body 字号不再 48px cascade（**G-LRG-10**） |
| **AC-LRG-11** | chapterMeta 不重复相册名（dogfood 目视 · **G-LRG-09**） |

### 4.3 P2 Gate

（v0.2.0 后无 P2 项；原 G-LRG-09/10 已升 P1。）

---

## 5. 测试与验收清单

### 5.1 自动化（已有 + 待增）

| 测试 | 状态 | LRG 要求 |
|------|------|----------|
| `test_chapter_ticket_centers_pull_not_index` | ✅ 已有 | CI 必跑 |
| `test_chapter_ticket_stub_rules_in_overlays` | ✅ 已有 | CI 必跑 |
| `test_moment_exif_bar_rules_in_overlays` | ✅ 已有 | CI 必跑 |
| `test_mosaic_5_main_portrait_3land_contain_collapses_stage` | ✅ 已有 | CI 必跑 |
| `test_bsp_moment_playwright` | ✅ 已有 | 纳入 optional nightly |
| `test_overlay_ticket_removal_fails_guard`（负向） | ❌ 待建 | **AC-LRG-03** |
| `test_export_fails_on_trailing_legacy_css` | ❌ 待建 | **AC-LRG-12 / T-LRG-12** |
| `scripts/lrg_dogfood_report.py` | ❌ 待建 | P0 交付 |
| CI sync + diff check | ❌ 待建 | P0 交付 |
| `docs/acceptance-records/lrg-dogfood.*.json` baseline | ❌ 待建 | P0 交付 |

### 5.2 目视 Checklist（每本 dogfood trip）

**通用（全宽 desktop，≥1280px）**

- [ ] 章首页 **ticket 票根**：序号 | 竖线 | 标题横排；pull quote 居中叠层；`03 / NN` 在右上
- [ ] 副标字号 **明显小于** 标题（非 48px）
- [ ] 高光池图片 **底部黑条 EXIF**（≈11–13px，单行 ellipsis）
- [ ] Plate 屏 **Plate · NN** 角标可见、不挡脸
- [ ] 任意 `main-portrait-3land` 屏 **底行 3 张横图完整可见**
- [ ] 全书 scroll 无大面积文字重叠/裁切

**响应式断点（v0.2.0 必改 · Type-A PR 必附截图）**

| 断点 | 宽度 | 必查项 |
|------|------|--------|
| **Mobile** | **375px** | ticket 不纵向堆叠；EXIF 黑条仍在槽底；章节标题可读 |
| **Tablet** | **768px** | mosaic-5 底行无裁切；folio 角标不溢出 |

**PR 要求**：Type-A 变更须在 PR 附 **375px + 768px** 各 ≥1 张截图（章首页 + 含 EXIF 或 mosaic-5 屏）。

---

## 6. 实施计划

### 6.1 里程碑

| 里程碑 | 内容 | 目标日期（建议） |
|--------|------|------------------|
| **LRG-W0** | 扩展 `validate` job fail-fast + **T-LRG-13 分支保护核实** + 负向 pytest + 文档约束 | **5 工作日** |
| **LRG-W1** | `lrg_dogfood_report.py` + baseline 入库 + demo 可演示 + **ADR-014 决议** | +1 周 |
| **LRG-W2** | Playwright computed CI + Studio stale + G-LRG-09/10 实现 | +2 周 |

### 6.2 任务分解

| ID | 任务 | 优先级 | 负责建议 |
|----|------|--------|----------|
| T-LRG-01 | **（v0.2.1 改写）** 审计并强化现有 `validate` job "LTE journal CSS sync drift" 步骤，**不新建**平行 job | P0 | 工程 |
| T-LRG-02 | CONTRIBUTING / DESIGN-PHASE16 §overlay 补丁 | P0 | 工程 |
| T-LRG-03 | 实现 `scripts/lrg_dogfood_report.py`（含 burst/window 字段） | P0 | 工程 + QA |
| T-LRG-04 | demo-815dc906d3 全 pipeline + §5.2 签字 | P0 | QA |
| T-LRG-05 | 采集 3 trip baseline → **`docs/acceptance-records/lrg-dogfood.*.json`** | P0 | QA |
| **T-LRG-13** | 核实/配置 GitHub 分支保护，将 `validate` job 设为 required status check（无 `gh` CLI 权限，需工程手动确认） | **P0** | 工程 / repo admin |
| **T-LRG-12** | export marker 外 CSS **fail-fast** + 单测 | **P0** | 工程 |
| T-LRG-06 | 填写并合并 ADR-014 | P1 · **W1 截止** | 产品 + 算法 |
| T-LRG-07 | Playwright computed style CI | P1 | 工程 |
| T-LRG-08 | Studio CSS stale banner | P1 | Studio |
| T-LRG-09 | `_chapter_meta_line` 语义优化 | **P1** | 策展/渲染 |
| T-LRG-10 | web `body` 字号重置 | **P1** | 设计/前端 |
| T-LRG-11 | 自动化负向 overlay 删除测试 | P0 | 工程 |

### 6.3 依赖与顺序

```text
22c1767 热修（已合并）
  → LRG-W0 CI 门禁 + T-LRG-12 fail-fast（5 工作日）
       → LRG-W1 dogfood baseline 入库 + ADR-014 决议
            → LRG-W2 G-LRG-09/10 + Playwright + Studio
                 → URO enabled=true 盲评排期（ROADMAP Phase 18）
```

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| overlay 清单不全，仍漏新 block | 回归再现 | 清单随 PR 增量维护；目视 checklist |
| dogfood trip 不可复现用户相册 | 决策偏差 | 每季度轮换第 3 本 trip |
| `mixed_proximity` 900s 过松 | 拼图语义差 | ADR-014 + 相册级 override 文档化 |
| CI sync diff 误报（未 commit generated） | 开发者摩擦 | 文档明确：改 overlays 须 commit sync 后 css |
| 双轨 trip css 再次分叉 | linzhi 式 drift | render 强制覆盖；禁止 hand-edit trip css |
| baseline JSON 仅放 .cache | 无法 CI 对比 | **v0.2.1**：强制入库 `docs/acceptance-records/lrg-dogfood.*.json` |
| CI 检查存在但未设为 required，FAIL 仍可 merge（本次事故实际根因） | 门禁形同虚设 | **T-LRG-13**：核实/配置分支保护 required status checks |
| 新增 CI job 与既有 `validate` job 步骤重复维护 | 逐渐漂移、双份真相 | **v0.2.1**：不新建 job，扩展现有 "LTE journal CSS sync drift" 步骤（§3.2.1） |

---

## 8. 成功指标（上线后 30 天）

| 指标 | 目标 |
|------|------|
| overlay 相关生产/ dogfood **视觉 P0 事故** | **0** |
| `validate` job（overlay 相关强化步骤）CI 失败拦截 merge 数 | 捕获 ≥1 次 intentional 拦截（证明有效） |
| dogfood trip 验收 **每次 layout PR** 附件率 | ≥ 90% |
| 用户反馈「章节/EXIF 错乱」类 ticket | 较 2026-07 归零 |

---

## 9. 附录

### A. 2026-07-05 已交付热修（不在 LRG 范围重复实施）

- 恢复 ticket-stub chapter separator overlay
- 恢复 P23 moment EXIF overlay
- mosaic-5 main-portrait-3land contain stage collapse
- `mixed_proximity_seconds` 默认 900s；URO 默认 off；tiebreak 实现

### B. 参考命令

```bash
pytest tests/test_lte_css_sync.py tests/test_reading_experience.py tests/test_moment_render.py -q
python -m travelogue.layout_templates.cli export --sync-journal
python scripts/mosaic_config_diag.py --trip trips/demo-815dc906d3
python scripts/lrg_dogfood_report.py --trip trips/demo-815dc906d3 --out docs/acceptance-records/lrg-dogfood.demo-815dc906d3.json
```

### C. 文档修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-05 | 初稿：基于 2026-07 排版回归事故与项目总监下一步分析 |
| v0.2.0 | 2026-07-05 | **跨职能评审收敛**：8 条必改（T-LRG-12、Type-A/B、baseline 入库、G-LRG-05 屏数一致、375/768 截图、ADR W1、dogfood schema 扩展、AC-LRG-03 自动化）；G-LRG-09/10 升 P1；W0→5 工作日；ADR-014 模板 |
| **v0.2.1** | **2026-07-05** | **落地核实修正**（对照现有代码/CI 复核后调整，非新增评审意见）：① 撤销新建 `layout-overlay-guard` job 提议，改为扩展现有 `validate` job "LTE journal CSS sync drift" 步骤（避免与既有 CI 重复维护）；② 新增 T-LRG-13：核实/配置分支保护 required status checks（本次事故真实根因是「FAIL 仍可 merge」而非「无 CI」）；③ baseline 存放路径由 `tests/fixtures/lrg/` 改为 `docs/acceptance-records/lrg-dogfood.<trip-id>.json`，对齐仓库既有 357+ 文件的 per-trip 验收基线惯例，并明确与 `tests/fixtures/phase16-dogfood/`（渲染前策展统计样本，职责不同）不合并；④ 核实 `demo-815dc906d3` / `demo-80301df45c` 均已存在且含完整渲染产物，T-LRG-04 无阻塞 |

### D. v0.2.0 必改清单（评审裁定）

| # | 项 | 落点 |
|---|-----|------|
| 1 | export marker 外非空 CSS → fail | §3.2.3 · T-LRG-12 · AC-LRG-12 |
| 2 | Type-A / Type-B 验收分路径 | §3.3.2 |
| 3 | dogfood baseline JSON 入库 | §3.3.4 · G-LRG-04 · T-LRG-05 |
| 4 | trip.json 屏数 = HTML layout-screen 数 | G-LRG-05 · schema `htmlLayoutScreenCount` |
| 5 | 375/768 断点 + PR 截图 | §5.2 |
| 6 | ADR W1 文档截止 | §3.4 · T-LRG-06 |
| 7 | `burstPassRate` + `windowExposure` | §3.3.4 |
| 8 | AC-LRG-03 负向测试自动化 | §4.1 · T-LRG-11 |

---

**评审签字**

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 产品 | （待填） | 2026-07-05 | **有条件通过** |
| 工程 | （待填） | 2026-07-05 | **有条件通过** |
| 算法/排版 | （待填） | 2026-07-05 | **有条件通过** |
| QA | （待填） | 2026-07-05 | **有条件通过** |

**条件**：v0.2.0 必改清单 §D 全项纳入 W0–W1 实施；G-LRG-09/10 纳入 W2 P1 交付。
