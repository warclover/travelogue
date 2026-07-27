# MTSO · 本机狗粮 / 短手测指南

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-27（§0 自 P2VF 回写；§0.3 自 Mixed 1L1P / Landscape-2 / L3E / Mixed 1P2L 狗粮回写） |
| 关联 | [PRD MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [ACCEPTANCE](../ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) |
| 正交 | [MSA 狗粮](./msa-local-dogfood-GUIDE.md)（槽位自适应 · 可同开） · [P2VF 评审纪要](./p2vf-portrait-2-variant-family-v1-review-2026-07-27.md) · [Mixed 1L1P](./mixed-1l1p-v1-review-2026-07-27.md) · [Landscape-2 Editorial](./landscape-2-editorial-v1-review-2026-07-27.md) · [Landscape-3 Editorial](./landscape-3-editorial-v1-review-2026-07-27.md) · [Mixed 1P2L](./mixed-1p2l-v1-review-2026-07-27.md) |
| 配置样例 | [`docs/config-mtso-experiments-dogfood.example.yaml`](../config-mtso-experiments-dogfood.example.yaml) · [`docs/config-p2vf-dogfood.example.yaml`](../config-p2vf-dogfood.example.yaml) · [`docs/config-mixed-1l1p-dogfood.example.yaml`](../config-mixed-1l1p-dogfood.example.yaml) · [`docs/config-landscape-2-editorial-dogfood.example.yaml`](../config-landscape-2-editorial-dogfood.example.yaml) · [`docs/config-landscape-3-editorial-dogfood.example.yaml`](../config-landscape-3-editorial-dogfood.example.yaml) · [`docs/config-mixed-1p2l-dogfood.example.yaml`](../config-mixed-1p2l-dogfood.example.yaml) |
| 仓库默认 | `selection_optimization.enabled=false` · `template_experiments.enabled=false`（fail-closed） |

> **不是** Go exit / 转正门槛。目标：验路径不崩、漏斗可读、双 SKU 可见性符合预期。

---

## 0. 实验模板通用接线清单（必过）

> 适用于 **所有** 走 `mosaic.template_experiments`（或等价 cohort 门）的新实验 SKU / 变体家族（MTSO 双 SKU、P2VF gallery/asym、后续同类）。  
> 配置写对了但仍「全是 fill / fallback / 像没上线」时，**先核本清单**，再查算法。

| # | 合同 | 为何会假绿 / 假死 | 怎么验 |
|---|------|-------------------|--------|
| **1** | **`tripId` 贯通排版主路径** | `curate → build_chapters_* → attach_screens_* → picker/MCS` 任一环漏传 `trip`，则 `trip_id=None` → `experimental_members_visible=[]` → 恒 `fallback_fill` / 实验不可见；**config 与 allowlist 完全正确也会死** | 在 picker / admit 入口断言 `trip_id == trip["tripId"]`；狗粮决策日志里不应出现「开关 ON 却 reason=`fallback_fill` 且无可见实验 id」 |
| **2** | **配置对 ≠ 已生效** | 改 `cohort_trip_ids` / allowlist / 家族开关后，旧进程与旧 `index.html` 仍反映上一轮 curate | **重启 Studio/CLI** → 对该 trip **重新 curate** → 再看 HTML；勿只刷新浏览器 |
| **3** | **Schema / telemetry 与新 pattern 同发** | 新 `patternId`、picker 探针字段、MSA/`foodPolicy` 等未进 `schemas/trip.schema.json` 时，布局其实已写出，但 **render validate 失败**，误判为「版式挂了」 | PR 同时改 schema；狗粮先 `cli validate` / render，再截图 |
| **4** | **硬路径 vs 实验 picker 分开验收** | 人物硬 emit（如 `layoutHint=person-pair`）**不走**实验 picker 是规格，不是 bug；拿人像对去验 gallery/asym 会假失败 | 验收表拆两列：硬路径（仍 fill）· 非人像/准入窗（应出现实验 id） |
| **5** | **三处对照，缺一不可** | 只看 config、或只看 HTML、或只看 `trip.json` 会归因错误 | 同时核对：**config**（双开关 + allowlist + `cohort_trip_ids` 含裸 tripId）· **`trip.json`**（`patternId` / picker `reason` / admit 日志）· **`index.html`**（`data-pattern`） |
| **6** | **`append_screen` / emit 传入 `mosaic` 配置** | 只传 `tripId` 不够：cohort 门读 `ctx.app_config.mosaic.template_experiments`；漏传则实验永远不可见 | 与 #1 同测：picker 入口能读到非空 `MosaicConfig` + 正确 allowlist |
| **7** | **家族节奏 / streak 要注册** | 新「成对」pattern 未进 `LANDSCAPE_PAIR_PATTERNS`（或等价集合）+ `max_*_streak` + post-check 时，会连发或漏限流 | 单测 streak；狗粮决策日志出现 `landscape_pair_streak`（或家族对应字段） |

### 0.1 新实验 SKU 上车检查（复制用）

- [ ] `template_experiments.enabled=true` 且 allowlist 含新 id；`cohort_trip_ids` **非空且含本 tripId**（空列表 = 无人可见）
- [ ] 若另有家族开关（如 `layout.portrait_2_variants` / `mixed_1l1p` / `landscape_2_editorial` / `landscape_3_editorial` / `mixed_1p2l`），与 experiments **双开**
- [ ] emit / admit / `append_screen` 传入完整 `trip`（至少含 `tripId`）与 `AppConfig.mosaic`（§0 表 #1/#6）
- [ ] `schemas/trip.schema.json`：`patternId` enum + picker 探针字段（reason 枚举如 `overlap_tie`）已登记
- [ ] 成对家族：rhythm / streak 集合与 post-check 已接线（§0 表 #7）
- [ ] 重启进程 → `curate` → `render` → 三处对照（§0 表 #5）
- [ ] 对照用例含：**实验应可见窗** + **硬路径/关门仍基线**（§0 表 #4）
- [ ] 视觉合同：新 `gridClass` 已 **opt-out 通用 contain-collapse**（§0.3）；`test_asset_version` golden 已 bump

### 0.2 归因速查

| 现象 | 先查 |
|------|------|
| 全册只有 fill / `fallback_fill`，config 已开 | #1 tripId 贯通；#6 mosaic 是否传入；#2 是否未 re-curate |
| `trip.json` 已有新 pattern，render 报 `E_VALIDATE_SCHEMA` | #3 schema |
| 人像对永远 fill，非人像也不出实验 id | 先确认非人像窗是否真的走了 picker；再查 #1/#2 |
| HTML 无新 `data-pattern`，json 也无 | #2 生效链；再查 allowlist / 硬路径分流 |
| patternId 对，但竖/横槽被压扁、不满高、大量留白 | §0.3 contain-collapse / CSS-primary；只需 **re-render**（不必 re-curate） |
| tie 窗口总落 fill，实验权重写了却看不见 overlap | picker 平局池是否被 fill `base_weight` 压过（应用 `overlap_tie` 专池） |
| 双横实验连发过多 | #7 家族 streak |

### 0.3 视觉合同 / CSS 狗粮踩坑（Mixed 1L1P · Landscape-2 · L3E · Mixed 1P2L 回写）

> picker / schema 全绿 **不等于** 版式好看。下列是本轮拼贴家族手测沉淀，后续新 `gridClass` 默认当检查项。
> L3E：固定 16:9（勿沿用 stack `aspect-ratio: auto`）；大槽满高 + 侧栏等分。Mixed 1P2L 镜像：右竖 `row span 2` 满高，与 fill 等宽列比。

| # | 合同 | 假象 | 怎么验 / 修 |
|---|------|------|-------------|
| **V1** | **CSS-primary：用户看到的是 `journal-screens.css`** | YAML `cols/rows/rect` 只文档意图；改 YAML 不改 CSS → 视觉零变化 | 视觉 QA 以 CSS + 截图为准；YAML 注释写明 CSS-primary |
| **V2** | **纯视觉改动：`render` + `assetVersion`，不必 `curate`** | 只硬刷新浏览器仍吃旧 bundle；或误以为要重跑排版 | `python -m travelogue render <trip>`；bump `tests/unit/trip/test_asset_version.py`；确认 `journal.css?v=ls…` 变了 |
| **V3** | **新 pattern 必须 opt-out 通用 contain-collapse** | 全局 `.layout-slot:has(> .layout-slot__img--contain)` 会设 `align-self:start; height:auto`，把「竖槽满高」等合同打穿（Mixed 1L1P 已踩） | 在该长选择器链上加 `:not([data-pattern="…"])`，或对 pattern 写更高优先级 fill 覆盖；用 DevTools 看 computed `align-self` |
| **V4** | **叠压类：V1 无人物遮挡规避 → 几何必须轻叠** | 槽位过大时前景盖住人脸/主体，却无算法换对角或回退 fill | 外缘可贴边（inset=0），但宽高宜控重叠面积（狗粮约屏面 1–2% 量级）；缺 face 信号前不要做「满幅叠压」 |
| **V5** | **测量相对 stage，勿被纸色对角留白误导** | 叠压屏对角三角纸色是设计留白，不是「没贴边」 | Playwright/`getBoundingClientRect`：TL `top/left≈0`，BR `bottom/right≈0` |

---

## 1. 一键配置

复制样例片段进项目根 `config.yaml`（gitignore），填入真实 `cohort_trip_ids`，**重启 Studio/CLI** 后对该 trip **重新 curate**（见 §0 #2）。

建议狗粮同时开：

```yaml
mosaic:
  template_contract:
    enabled: true
    shadow_log: true
  template_experiments:
    enabled: true
    allowlist:
      - screen-mosaic-5-1p4l-portrait-hero
      - screen-mosaic-5-2p3l-portrait-hero-rail
    cohort_trip_ids:
      - your-trip-id-here
  selection_optimization:
    enabled: true
```

---

## 2. 对照场景（必测）

| # | 配置 | 期望 |
|---|------|------|
| A | SO=true + experiments 三元组 | 强竖 1P4L 窗可看见 `1p4l-portrait-hero`；2P3L 窗可看见 `2p3l-portrait-hero-rail`；硬拒 `main-portrait-3land` 时 reason=`mixed_routing:mixed_portrait_is_hero` |
| B | SO=true + experiments OFF | 硬拒 detail 含 `dual_sku_gated`；MCS 失败后 cursor 强竖 → `screen-portrait-1` rescue |
| C | SO=false（嵌套子开关随意） | 与仓库默认路径一致；**无** mixed_routing 硬拒；experimental 仍不可见 |

漏斗断言读 **raw** `drain_mosaic_capture` / 决策日志字段（D-MTSO-11），勿只看展示 Top-3。

---

## 3. 自动化烟测

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_pr_d.py tests/unit/layout_engine/test_mtso_pr_c2_skus.py -q
```

---

## 4. PR-D 仍待手测 / 盲评

- [ ] 代表 trip compare（双阈值 AC-11）
- [ ] 2P3L 三列几何截图签核（辅竖 AR≈0.27 可读）
- [ ] 转正或归档（AC-12）；通过前勿写 `lte_policy`
