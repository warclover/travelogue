# Travelogue · Phase 19 实施清单（精益观感跃迁 LQU · 任务拆解 + 开发准备）

| 属性 | 内容 |
|------|------|
| **文档** | IMPLEMENTATION-PHASE19 |
| **版本** | v0.1 |
| **配套 PRD** | [PRD-PHASE19-lean-quality-uplift.md](./PRD-PHASE19-lean-quality-uplift.md)（v0.2） |
| **分支** | `phase19/lean-quality-uplift` |
| **更新日期** | 2026-06-11 |
| **状态** | **2026-06-11 工程收尾** · 见 [ACCEPTANCE-PHASE19.md](./ACCEPTANCE-PHASE19.md) · 自动化 Gate ✅ · 北极星 / SKU 占比 ❌ |

> **本文定位**：把 PRD 的 R-P19-xx 落成可执行任务、PR 切片、文件级改动清单与 Sprint Gate 检查表。PRD 讲「做什么/为什么」，本文讲「先干什么、改哪里、怎么验、怎么回滚」。

---

## 0. 三句话总览

1. **执行顺序 = 裁判 + 像素 → 减法（零 diff）→ 硬约束 → Schema v2/版式族 → subset**；禁止在 judge 未跑通前合并「观感优化」类 PR。
2. **合并门禁三层**：行为性改动 → judge/盲评；纯重构 → 8 本 screens 签名零 diff；像素/CSS → CI probe + focal 违规 = 0。
3. **12 周 / 6 Sprint**；每 Sprint 2 周；Gate 不达标则回滚该 Sprint 行为改动（见 §6）。

---

## 1. 开发准备清单（Kickoff 前）

### 1.1 环境与分支

| 项 | 动作 | 状态 |
|----|------|------|
| 工作分支 | `git checkout phase19/lean-quality-uplift` | ✅ 已创建并推送远端 |
| Python 环境 | 与 `docs/DEVELOPMENT.md` 一致；`pip install -e ".[dev]"` | 开工前自检 |
| Playwright | judge 截图链路需要；`playwright install chromium` | S1 前 |
| VLM API | `config.yaml` 或环境变量配置（**不入库**）；文档见 §8.1 | S1 前 |
| 本地 HTTP | `python -m travelogue.web.serve` 或现有 Studio 端口；golden trip 可 curate/render | 开工前 |

### 1.2 Golden 样本（8+1 本）

权威清单：`docs/acceptance-records/p19-golden-trips.json`。

开工前确认每本 trip 在本机可：

```powershell
# 示例：川藏线
python -m travelogue.cli curate demo-1506104ebf
python -m travelogue.cli render demo-1506104ebf
```

若 trip 缺失，从 dogfood 同步或标记 `skipReason` 写入 golden manifest。

### 1.3 基线产物目录（S1 第一天创建）

```text
.cache/book-quality/
  baseline/                    # P16 默认路径成稿（HTML + manifest）
  p19/                         # 各 Sprint candidate 输出
  judge/                       # VLM judge JSON 报告
  screens-signatures/          # 8 本 screens 签名（S2 零 diff 门禁）
docs/acceptance-records/
  p19-judge-calibration.json   # 人评校准（从 template 复制）
  p19-sprint-gates.json        # 各 Sprint Gate 结果
```

### 1.4 代码真值速查（避免改错层）

| 能力 | 主入口 | 备注 |
|------|--------|------|
| curate 主编排 | `travelogue/curation/curate.py` | subset 插入点：clustering 后、plan_screens 前 |
| 组屏 | `screen_planner_attach.py` → `layout_engine/adapter.plan_chapter_screens` | LSE 默认关仍走同一 planner |
| MCS 窗口 | `mosaic/hook.py` → `compose.pick_best_window` | silent fallback：`mosaic/search.py` L181 |
| LTE 模板 | `layout_templates/registry.py` + `mosaic/lte_adapter.py` | 三处同源：YAML / `_legacy_generated.py` / `constants.py` |
| 渲染 focal | `render/context.py` → `journal-screens.css` | 硬编码 object-position 为 WP-2 主攻 |
| 节奏状态 | `screen_layout_state.py` + `layout.rhythm` config | 排版规则优化已落地 R-06/V-08 |
| LSE 开关页 | `web/studio_handlers` + `/lse-flags-admin` | S2 降级只读 |

### 1.5 PR 规范（P19 专用）

- 标签：`p19/` + `wp-0`…`wp-5` + `s1`…`s6`
- 描述必填：8 本 judge 胜率（整体 + 5 维度）或「零 diff / docs-only」说明
- **禁止**：仅 proxy 指标改善而无 judge 结果的合并（PRD §7）

---

## 2. 任务总表（R-P19 → 工程任务 ID）

| 工程任务 ID | PRD | 标题 | Sprint | 依赖 |
|-------------|-----|------|--------|------|
| **T-P19-000** | R-001~004 | WP-0 感知裁判 harness | S1 | — |
| **T-P19-010** | R-201~202 | WP-2 像素闭环（CSS + render focal） | S1 | — |
| **T-P19-011** | R-203~204 | WP-2 像素 CI + badcase 样例 | S2 | T-P19-010 |
| **T-P19-020** | R-101 | 模板运行时单一来源（删 legacy 同步链） | S2 | — |
| **T-P19-021** | R-102 | 拓扑逻辑归一（去 pattern_id 硬编码） | S2 | T-P19-020 |
| **T-P19-022** | R-103 | LSE 路线 C 收束 + 开关页只读 | S2 | — |
| **T-P19-023** | R-104~105 | Admission 减负 + rollout 归一 | S2 | T-P19-020 |
| **T-P19-030** | R-301~302,304 | WP-3 硬约束 + 消灭 silent fallback | S3 | T-P19-020 |
| **T-P19-040** | R-401,402,406 | Schema v2 最小集 + css_gen | S4 | T-P19-023 |
| **T-P19-041** | R-403,404 | justified-row + whitespace-hero | S4 | T-P19-040 |
| **T-P19-042** | R-405 | spread + asymmetric-hero SKU | S5 | T-P19-040 |
| **T-P19-043** | R-303 | 章级 DP/beam | S5 | T-P19-030 |
| **T-P19-050** | R-501~505 | subset_planner + highlight 结构绑定 | S5~S6 | — |
| **T-P19-060** | AC 全项 | S6 集成、默认开关、终验 | S6 | 全部 |

---

## 3. Sprint 任务拆解

### S1（W1–2）· 裁判 + 像素闭环

**Gate**：judge 跑通；校准一致率初测 ≥ 70%；focal 违规 = 0；裁切维度 judge 胜率 ≥ 55%。

| 子任务 | 文件/路径 | 交付 |
|--------|-----------|------|
| S1-01 基线成稿包 | `scripts/book_quality_baseline.py`（新） | 8 本 P16 路径 HTML + `manifest.json` → `.cache/book-quality/baseline/` |
| S1-02 屏抽样器 | `travelogue/eval/screen_sampler.py`（新） | tripId+screens 签名种子；≤12 屏/本（DQ-01） |
| S1-03 截图链路 | 复用/扩展 `lse_flags_preview_ablate.py` | Playwright 全页或屏级截图 → PNG 序列 |
| S1-04 VLM judge v0 | `scripts/book_quality_vlm_judge.py` | pairwise + 5 维度 JSON；prompt 锁定 `docs/p19/vlm-judge-prompt-v1.md` |
| S1-05 人评模板 | `docs/acceptance-records/p19-judge-calibration.template.json` | ≥3 人 × 8 本录入 |
| S1-06 focal CSS 清理 | `templates/visual-journal/journal-screens.css`、`journal.css` | 去除 pattern 级 `object-position` 硬编码（R-201） |
| S1-07 render focal 保证 | `travelogue/render/context.py` | 每 slot 输出 `--focal-x/y`；缺失 telemetry（R-202） |
| S1-08 单元测试 | `tests/test_p19_focal_css.py`（新） | grep/解析断言无违规硬编码 |
| S1-09 CI smoke | `tests/test_book_quality_judge_smoke.py` | 2 本 fixture mock VLM |

**建议 PR 切片**：

1. `p19/s1-baseline-harness` — S1-01~05（docs + scripts，无产品行为变更）
2. `p19/s1-focal-pixel` — S1-06~08

---

### S2（W3–4）· 减法 + 像素 CI

**Gate**：8 本 screens 签名零 diff；CI 像素检查上线。

| 子任务 | 文件/路径 | 交付 |
|--------|-----------|------|
| S2-01 screens 签名工具 | `scripts/book_quality_screen_signatures.py` | 8 本 pattern 序列 + slot 摘要 hash |
| S2-02 运行时读 LTE | `mosaic/grid_specs.py`、`mosaic/registry.py` | 删除 `_legacy_generated` 运行时依赖（R-101） |
| S2-03 删除同步链 | `_legacy_generated.py`、`legacy_codegen.py`、`scripts/lte_export_legacy.py` | 合并前零 diff 验证 |
| S2-04 拓扑归一 | `mosaic/builders.py`、`mosaic/scorer.py` | 读模板 constraints 替代 `PATTERN_MOSAIC_5_*` if（R-102） |
| S2-05 LSE 归档 | `layout_engine/_archive/` | shadow/golden_probe/algorithm_lock/weights_audit 移出主 import 路径（R-103） |
| S2-06 开关页只读 | `template_admin_handlers`、lse-flags 模板 | 写 API 移除；只读快照（DQ-04） |
| S2-07 Admission 三步 | `layout_templates/admission.py`、`lte_policy.yaml` | 自动 `photoCount` 归组（R-104） |
| S2-08 Rollout 归一 | `travelogue/config/rollout.py`（新或扩展现有） | 统一 bucket util（R-105） |
| S2-09 像素 probe CI | `layout_templates/probe_screenshot.py`、`.github/workflows/ci.yml` | AR/focal 断言（R-203）；3P+2L badcase（R-204） |
| S2-10 零 diff 测试 | `tests/test_p19_screen_signature_parity.py` | 8 本 golden 对比 |

**建议 PR 切片**（严格顺序）：

1. `p19/s2-signatures-tool` — 门禁工具先行
2. `p19/s2-lte-single-source` — R-101（最大 diff，单独 PR）
3. `p19/s2-lse-archive-readonly` — R-103 + 开关页
4. `p19/s2-admission-rollout` — R-104/105
5. `p19/s2-pixel-ci` — R-203/204

---

### S3（W5–6）· 硬约束

**Gate**：breath/streak 违规 = 0；judge 整体 ≥ 55%；节奏维度 ≥ 60%。

| 子任务 | 文件/路径 | 交付 |
|--------|-----------|------|
| S3-01 去掉 unfiltered fallback | `mosaic/search.py`（L181 等）、`mosaic/compose.py` | reject + 回溯（R-301） |
| S3-02 可行域裁剪 | `mosaic/candidates.py`、`screen_planner_stages.py` | breath/streak 在候选阶段过滤（R-302） |
| S3-03 违规检测脚本 | `scripts/p19_rhythm_audit.py` | 8 本 trip 输出违规报告 |
| S3-04 显式兜底 | `screen_planner_stages.py` | DP 前置：无解 → 单图序列 + telemetry（R-304） |
| S3-05 决策日志 | `mosaic/log.py`、`curation/decision_log` | 全部 reject reason |
| S3-06 回归测试 | `tests/test_p19_hard_constraints.py` | demo-2025-2 类 badcase |

**灰度**：先在 `demo-1506104ebf`、`demo-2025` 2 本验证无解率 < 5% 再扩 8 本。

---

### S4（W7–8）· Schema v2 + justified / whitespace

**Gate**：竖图 trip judge ≥ 60%；新版式占比 ≥ 10%；BSP 3:2 截图过线。

| 子任务 | 文件/路径 | 交付 |
|--------|-----------|------|
| S4-01 Schema v2 | `layout_template.schema.json`、`models.py` | margins/bleed/maxFillRatio/photoCount 区间/9 片解封；16:9+3:2（R-401） |
| S4-02 槽位 AR 约束 | `validator.py`、`geometry.py` | aspectRange、cropPolicy（R-402） |
| S4-03 css_gen token | `css_gen.py` | token → CSS 变量（R-406） |
| S4-04 justified-row | `curation/layout/justified_row.py`（新）、模板 YAML | Flickr 算法 MIT；`kind: justified`（R-403） |
| S4-05 whitespace-hero | `templates/screen-whitespace-hero.yaml` + CSS | maxFillRatio 绑定（R-404） |
| S4-06 BSP 3:2 | `probe_screenshot` + `demo-d66fe642a9` | DQ-05 Gate 截图 |
| S4-07 v1 兼容测试 | `tests/test_lte_schema_v2_compat.py` | 24 个存量模板零迁移加载 |

---

### S5（W9–10）· 设计师 SKU + 章级 DP + subset spike

**Gate**：混排 trip judge ≥ 60%；设计师 SKU ≥ 15%；curate P95 ≤ +15%。

| 子任务 | 文件/路径 | 交付 |
|--------|-----------|------|
| S5-01 spread SKU | `screen-spread-folio.yaml` | 对开双 hero（R-405） |
| S5-02 asymmetric SKU | `screen-asymmetric-hero.yaml` | hero + 侧栏条（R-405） |
| S5-03 章级 DP | `curation/chapter_layout_dp.py`（新） | 窗口切分 × 模板 DP（R-303） |
| S5-04 subset spike | `curation/subset_planner.py` | 单 trip `demo-1506104ebf` 验证（R-501 预研） |
| S5-05 性能 profiling | `scripts/p19_curate_profile.py` | P95 对比 baseline |

---

### S6（W11–12）· subset 集成 + 终验

**Gate（北极星）**：人评盲评胜率 ≥ 60%（≥6/8 本）；「故事更清楚」≥ 60%。

| 子任务 | 文件/路径 | 交付 |
|--------|-----------|------|
| S6-01 subset 并入 curate | `curate.py` | `plan_asset_subset` 插入点（R-501） |
| S6-02 三档硬上限 | `config/curation.py` | −40% / −30% / −25%（R-502、DQ-03） |
| S6-03 highlight 结构绑定 | `highlight_windows.py`、`screen_planner` | 章首 hero（R-504） |
| S6-04 kill switch | `curation.subset.enabled` | 默认关 → Gate 后默认开（R-505） |
| S6-05 `curation.subsetPlan` | `trip.schema.json` | schema minor bump |
| S6-06 终验 | `docs/acceptance-records/p19-final.json` | AC-P19-01~08 |
| S6-07 Runbook | `docs/P19-RUNBOOK.md` | 回滚：`subset off` + 硬约束 off |

---

## 4. 模块结构（P19 结束态）

```text
travelogue/eval/                    # 新建 · WP-0
├── screen_sampler.py
└── vlm_judge.py

travelogue/curation/
├── subset_planner.py               # 新建 · WP-5
├── chapter_layout_dp.py            # 新建 · WP-3
└── layout/justified_row.py         # 新建 · WP-4

travelogue/layout_templates/
├── layout_template.schema.json     # v2 扩展
├── models.py                       # TemplateStage margins 等
├── validator.py                    # v2 规则
├── css_gen.py                      # token 输出
└── templates/
    ├── screen-justified-row.yaml
    ├── screen-whitespace-hero.yaml
    ├── screen-spread-folio.yaml
    └── screen-asymmetric-hero.yaml

travelogue/layout_engine/
├── adapter.py                      # 保留 rhythm/decision log
├── rhythm.py                       # 保留
└── _archive/                       # shadow/golden_probe 等归档

scripts/
├── book_quality_baseline.py
├── book_quality_vlm_judge.py
├── book_quality_screen_signatures.py
├── p19_rhythm_audit.py
└── p19_curate_profile.py

tests/
├── test_p19_focal_css.py
├── test_p19_hard_constraints.py
├── test_p19_screen_signature_parity.py
├── test_lte_schema_v2_compat.py
└── test_book_quality_judge_smoke.py
```

---

## 5. 配置扩展（规划）

```yaml
# config.yaml 拟新增块（S6 前逐项落地）
book_quality:
  vlm_judge:
    enabled: true
    model: ""          # 环境变量优先，不入库
    prompt_version: "v1"
  golden_trip_ids: []  # 默认读 p19-golden-trips.json

curation:
  subset:
    enabled: false     # Gate 前默认关
    tier_small_max_assets: 80
    tier_small_reduction: 0.40
    tier_default_reduction: 0.30
    tier_large_min_assets: 300
    tier_large_reduction: 0.25

layout:
  hard_constraints: true   # S3 后默认 true，可 kill switch
```

实现落点：`travelogue/config/` 对应 dataclass + `schema.json` 一致性测试（沿用 P17 模式）。

---

## 6. Sprint Gate 检查表

复制模板：`docs/acceptance-records/p19-sprint-gates.template.json`。每 Sprint 结束填写并归档。

| Sprint | 必检项 | 通过线 |
|--------|--------|--------|
| S1 | judge 可运行；focal 违规；裁切维度胜率；校准一致率初测 | 见 PRD §5 S1 行 |
| S2 | screens 零 diff；像素 CI green | 8 本签名一致 |
| S3 | rhythm_audit 违规 = 0；judge 整体/节奏 | 见 PRD §5 S3 |
| S4 | 竖图 trip 胜率；新版式占比；BSP 3:2 | 见 PRD §5 S4 |
| S5 | 混排胜率；SKU 占比；curate P95 | ≤ +15% |
| S6 | 人评北极星；subset 指标；AC 全表 | ≥ 60% win · ≥6/8 |

---

## 7. 测试策略

| 层级 | 内容 | 何时 |
|------|------|------|
| Unit | focal CSS、rhythm 违规检测、screen_sampler 可复现、schema v2 缺省兼容 | 各子任务 PR |
| Integration | 8 本 curate 不抛错；screens 签名（S2） | S2+ |
| Regression | judge 报告 diff；proxy 哨兵（不当作合并依据） | 每 PR |
| Human | Sprint Gate 盲评 ≥3 人 | 每 2 周 |
| E2E 像素 | probe_screenshot AR/focal | S2 CI |

---

## 8. 外部依赖与密钥

### 8.1 VLM judge

- API key：**仅环境变量或本地 config**，禁止提交仓库
- Prompt 版本化：`docs/p19/vlm-judge-prompt-v1.md`（S1 创建）
- 换模型须重跑 `p19-judge-calibration.json`（R-P19-002）

### 8.2 justified-layout

- Flickr `justified-layout`（MIT）— S4 引入前完成 license 登记于 `docs/THIRD-PARTY.md`（若尚无则追加）

---

## 9. 风险与 PR 顺序护栏

| 风险 | 护栏 |
|------|------|
| S2 大重构引入行为 diff | **必须先合签名工具**；lte-single-source 单独 PR；合前跑 8 本对比 |
| S3 硬约束导致 curate 失败 | 2 本灰度；兜底率 > 5% 不扩 8 本 |
| S4 schema 破坏旧 trip | v1 缺省等价 + `geometry_diff` 全模板快照 |
| judge 不可信 | 一致率 < 70% 触发重校准；Gate 以人评为准 |

---

## 10. 首周执行序（Day 1–10）

```text
Day 1     确认 8+1 golden trip 可 curate/render；创建 .cache/book-quality/
Day 2–3   T-P19-000：baseline 脚本 + screen_sampler + 人评 template
Day 4–5   T-P19-000：vlm_judge v0（mock 模式先通）
Day 6–7   T-P19-010：journal-screens.css focal 清理 + test_p19_focal_css
Day 8     首轮人评校准（≥3 人抽样 4 本）→ 初测一致率
Day 9–10  S1 Gate 预演；未达标则只合 harness/像素 PR，不进 S2 重构
```

---

## 11. 文档地图

| 文档 | 用途 |
|------|------|
| [PRD-PHASE19-lean-quality-uplift.md](./PRD-PHASE19-lean-quality-uplift.md) | 产品契约 |
| [PRD-PRODUCT-LAYOUT-PRINCIPLES.md](./PRD-PRODUCT-LAYOUT-PRINCIPLES.md) | **阶段后产品纲领**（P-LAY-01～03） |
| **本文** | 工程任务与 Sprint 施工图 |
| `docs/acceptance-records/p19-golden-trips.json` | 8+1 样本清单 |
| `docs/acceptance-records/p19-judge-calibration.template.json` | 人评录入 |
| `docs/acceptance-records/p19-sprint-gates.template.json` | Gate 归档 |
| `docs/P19-RUNBOOK.md` | S6 交付 ✅ |
| `docs/ACCEPTANCE-PHASE19.md` | S6 交付 ✅ |

---

## 12. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-06-11 | 初版：PRD v0.2 任务拆解、S1–S6 子任务、开发准备清单、模块与配置规划 |
| v0.2 | 2026-06-11 | 工程收尾：ACCEPTANCE-PHASE19、p19-final closed_with_deferrals |
