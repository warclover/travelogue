# Travelogue · Phase 16 实施清单（布局模板引擎 LTE · 融合设计 + 工作量 + 阶段交付）

| 属性 | 内容 |
|------|------|
| **文档** | IMPLEMENTATION-PHASE16 |
| **版本** | v1.0（W1 开工版） |
| **配套 PRD** | [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md)（v0.16.4） |
| **分支** | `phase16/layout-template-engine` |
| **更新日期** | 2026-06-06 |
| **状态** | W0–W4 核心已交付；P0–P2 **第三轮**闭合（dogfood curate 脚本、user 3P+2L golden、stack grid primitive 扩展、V-P16-13 sign-off、CSS audit 去重）；W4 研究项按需 |

> **本文定位**：把 PRD 的设计落成可执行的工程计划——**融合方式、改动文件清单、阶段交付、工作量估算、W1 开工清单**。PRD 讲"做什么/为什么"，本文讲"怎么接、改哪里、要多久、先干哪些"。

---

## 0. 三句话总览

1. **融合策略 = 旁路 + 开关 + parity 护栏**：LTE 与现有 MCS 并行；W3 起 `read_templates_from_lte` 默认 **true**，可用 config 一键回退至 P15。
2. **复用而非重造**：生命周期/审计/RBAC/审批/后台复用既有 `travelogue/templating/` 平台；LTE 只写"拼图几何"本职 + 一层适配。
3. **关键路径 W0–W3 ≈ 6.5–9.5 人周**（单人 1.5–2.5 月；2–3 人并行约 4–6 周）；MVP 切法约 4–5 人周。

---

## 1. 融合设计

### 1.1 旁路并行架构

```
master（持续可跑，行为不变）
  MCS → default_registry()/grid_specs/constants → render → journal-screens.css

phase16 分支引入 LTE（旁路）：
  templates/*.yaml ──导出CI──> legacy 等价物 ──parity 测试──> 现有路径（零变化）
                    └──lte_adapter──> MCS（开关 read_templates_from_lte，默认 false）
                    └──css_gen──────> 生成 CSS（替代手写 grid class）

W3：翻开关 → MCS 仅读 LTE；几何固化进 screens[]；render 自包含
回退：read_templates_from_lte=false + registry_version pin 上一 tag
```

### 1.2 九个融合点（文件级）

| # | 融合点 | 关键文件 | 摩擦 | 改动要点 |
|---|--------|----------|------|----------|
| 1 | MCS 候选 | `travelogue/curation/mosaic/candidates.py` | 🟢低 | `generate_window_candidates(registry=...)` **已支持注入**；新增 `lte_adapter` 产出 registry；`mosaic_pattern_disabled` → LTE `status`+`overrides.disable` |
| 2 | MCS 打分 | `travelogue/curation/mosaic/scorer.py` | 🟢低 | 从 `TemplateDef` 读 `base_weight`/`rhythm`；与 P15 `layout_rhythm` **合并口径**防双惩罚 |
| 3 | 几何 | `mosaic/slot_geometry.py`、`mosaic/grid_specs.py` | 🟡中 | `slot_cell_aspect_ratio` 推广为**加权轨道**；几何迁入 LTE `geometry.py`，保留 thin wrapper；golden 比对 |
| 4 | Registry/常量 | `mosaic/registry.py`、`mosaic/constants.py` | 🟡中 | 逆向生成 YAML（脏数据如实复刻）；导出 CI；**6 类源 parity** |
| 5 | Render + CSS | `render/chapters.py`、`templates/visual-journal/journal-screens.css`（**100 个手写 grid class**） | 🔴中高 | 几何固化进 `screens[]`；`css_gen.py` 生成 CSS；每槽 `aspect-ratio`；触发 render 快照测试 |
| 6 | 复用治理平台 | `travelogue/templating/*`（admission/registry 为**作品级模板专用**） | 🟡中 | admin_store/lifecycle/roles/audit/governance **直接复用**；**新建"布局模板适配层"** 给 pattern 自己的 admission 步骤（注入 §6 校验器） |
| 7 | 媒资层 | `travelogue/curation/media_classify.py` | 🟢低-中 | `MediaClass` 加 `collage`；检测器 v1（独立工作项） |
| 8 | Studio 后台 | `web/studio_handlers/template_admin_handlers.py` | 🟡中 | 扩展几何图示/探针条/slotAspect/exposure_share；为布局模板单独绑定 registry |
| 9 | Config | `travelogue/config/layout.py` | 🟢低 | 加 `layout.template_engine` 配置块 + `max_mosaic_slots` + `exclude_collage_from_mosaic` |

### 1.3 两个必须正视的真相

- **点 6（治理平台复用不是 100% 免费）**：`templating.admission.run_admission_check` 跑的是 manifest/golden-render（作品模板概念），对拼图 pattern 不直接适用。复用的是**生命周期/审计/RBAC/审批 infra**；需为布局模板写独立 admission 步骤，把 LTE §6 几何校验器注入进去。
- **点 5（CSS 生成是新东西也是风险点）**：现有 `journal-screens.css` 有 **100 个手写 grid class**。`css_gen.py` 做成后新模板零手写，但等价校验（V-P16-05/06）与 render 快照回归是主要不确定性。

### 1.4 模块结构（新建 vs 复用）

```
travelogue/layout_templates/          # 新建：仅做"拼图几何"本职
├── __init__.py
├── registry.py          # YAML 加载、photoCount 倒排索引、registry.cache.json + hash 失效
├── geometry.py          # 加权轨道 displayAspect；solve_tracks（按目标 AR 反解权重）
├── validator.py         # §6 全门禁（以 hook 注入 templating.admission）
├── css_gen.py           # YAML → grid-template-*/变量（替代手写）
├── cli.py               # validate | export | docgen | solve-tracks
├── layout_template.schema.json
├── lte_policy.yaml
├── templates/*.yaml
└── probes/              # 合成探针图（含可变轨道用例）

travelogue/curation/mosaic/
├── lte_adapter.py       # 新建：MCS 唯一入口（禁止 MCS 直读 YAML）
└── pattern_catalog.py   # registry.py 改名 / generated re-export（W1）

复用（不新增）：
travelogue/templating/                 # admin_store/lifecycle/roles/review/admission/config_governance/audit
travelogue/web/studio_handlers/template_admin_handlers.py   # 扩展几何展示
```

---

## 2. 阶段交付与工作量

> 假设：1 名熟悉本仓的工程师；估算含测试。🔴 = 最大不确定性来源。

### W0 · 设计冻结（3–5 人日）

| 任务 | 交付 | 人日 |
|------|------|------|
| Schema 冻结 | `layout_template.schema.json`（轨道 `cols/rows`、`gap`、`max≤9`、5 态 status） | 1.5 |
| CLI 骨架 | `python -m travelogue.layout_templates.cli validate`（空实现可跑） | 1.0 |
| 晋升路径 spec | 布局模板的**轻量 admission**步骤定义（对合成探针放宽） | 0.5–1 |
| 出口 | R-P16-01~15 齐备；schema 通过自检 | — |

### W1 · Registry + 逆向 YAML + 导出 CI + parity（8–12 人日）

| 任务 | 交付 | 人日 |
|------|------|------|
| Registry | 加载/索引/`registry.cache.json` + 内容哈希失效；`list_active` p99 <1ms | 2 |
| 逆向 YAML | 一次性脚本从 4 处 legacy 生成 YAML；**脏数据如实复刻**（如 `MAIN_HERO_PLUS_4` name/slot_count 不符） | 1.5 |
| 🔴 Parity | `export_legacy_registry()` + `test_lte_registry_parity.py` 覆盖 **6 类源**（含 `grid-template` 字符串）；护栏 ~90 个 mosaic 测试 | 3–4 |
| 几何 | `geometry.py` 加权轨道 `displayAspect` + `solve_tracks`；golden 比对 | 2 |
| Adapter | `lte_adapter.py` + `candidates.py` 注入；**MCS 仍读 legacy（开关 false）** | 1.5 |
| 出口 | AC-P16-01、02、12、17；master 行为零变化 | — |

### W2 · Validator 全量 + CSS 生成 + 探针（8–12 人日）

| 任务 | 交付 | 人日 |
|------|------|------|
| Validator | V-P16-01~14（重叠/gap/超宽/mix/stack/轨道越界/max9/常规 AR 阶梯） | 3–4 |
| 🔴 CSS 生成 | `css_gen.py`（YAML→CSS，替代 100 手写类）+ V-P16-05/06 深度校验 | 3–4 |
| Docgen | `slotAspect` 表 `docs/templates/slot-aspect/<id>.md` 自动生成 | 1 |
| 探针 | 探针套件（含**可变轨道用例**）+ PR warn CI 分级 | 2–3 |
| 出口 | AC-P16-03、04、07、16 | — |

### W3 · 接 LTE 默认 + 后台 + collage + 几何固化（12–18 人日）

| 任务 | 交付 | 人日 |
|------|------|------|
| 翻开关 | `read_templates_from_lte=true` 默认 + 候选集回归 | 2 |
| 🔴 几何固化 | 固化 `cols/rows/rect/displayAspect` 进 `screens[]`；render 改造；快照回归 | 3–4 |
| 旗舰 + 轨道样板 | `mosaic-5-2p3l-equal` + `hero-3-2-plus-4` 走 `experimental→beta→ga` | 1.5 |
| Telemetry | per-template 指标（基数有界）+ `phase16_template_eval.py` | 2–3 |
| 治理适配 + 后台 | 布局模板 admission 步骤 + `template_admin_handlers` 扩展几何/探针展示 | 3–4 |
| Collage（可并行） | `MediaClass=collage` + 检测器 v1 + 资格过滤 + full-frame + blurred fill | 3–4 |
| 出口 | AC-P16-05、06、08、09、13、14、18 | — |

### W4 · 持续优化（不在关键路径，按需）

primitive 参数化、配额调优、删 legacy 手写常量、§9.4 多样性闭环 + 自动调权（两人审批）、collage 检测精化、P17 预研（生成式合成 / 匈牙利匹配 / 移动端）。出口：AC-P16-15。

**2026-06-06 第二轮闭合（P0–P2）**

| 项 | 交付 |
|----|------|
| AC-15 CI | `phase16_template_eval.py --strict-ac15`（PR warn / push block） |
| AC-08 dashboard | `aggregate_layout_template_metrics` → `metrics.layoutTemplates[]` |
| 指标补全 | `win_score_p50/p90`、`face_crop_proxy_rate` per templateId |
| Studio | 配额告警 + internal 门禁提示 |
| 几何探针 | push 跑 `lte_probe_regress.py --strict-geometry` |
| diversity.mode | `config.yaml.example` · `layout.template_engine.mcs_integration` |

**2026-06-06 第三轮闭合（P1–P2 审计跟进）**

| 项 | 交付 |
|----|------|
| §13.3 user 3P+2L | `tests/_golden/user-3p2l-case/` + MCS 不选 deprecated balanced |
| §13.3 dogfood | `scripts/phase16_curate_dogfood.py` + `phase16-dogfood-curate-policy.json` |
| R-14 stack grid | `primitive_catalog` 扩展 7 类 gridClass；`export --sync-journal` 去重 |
| V-P16-13 | `constraints.arLadderSignOff` schema + publish/admission block |
| CSS audit | 排除 overlay 引用；以 `duplicateGridClassesOutsideMarker` 为门禁 |
| Collage CI | `--min-recall 0.7` 与单测对齐 |
| Playwright E2E | AC-11 stale hint + §13.2 deprecated lifecycle（`test_lte_studio_playwright.py`） |
| Legacy import | `grid_specs.py` 直引 `_legacy_generated` 元组 |

### 2.x 工作量汇总

| 口径 | 估算 |
|------|------|
| 关键路径 W0–W3 | **31–47 人日 ≈ 6.5–9.5 人周**（单人 1.5–2.5 月） |
| 2–3 人并行（几何/render/后台/collage 可拆） | 日历 **4–6 周** |
| 风险系数 | **±30%**：① parity 与 render 快照回归对齐返工；② CSS 生成等价校验；③ collage 精度调优（可降级/独立） |

### 2.y MVP 切法（约 4–5 人周，最快拿核心价值）

**P16-Core = W0 + W1 + W2 + 仅旗舰走晋升 + 几何固化**；推后到 W4/P17：
- collage 检测器（先只留 `MediaClass` 钩子 + Studio 手动改判）
- 多样性闭环 / 自动调权 / 匈牙利匹配
- 移动端 9:16

价值：YAML 唯一源 + parity 等价 + Validator 拦缺陷 + 一个加权轨道新模板上线。

---

## 3. 风险登记（实施视角）

| 风险 | 触发 | 缓解 |
|------|------|------|
| parity 不等价 | 逆向 YAML 漏字段 | 6 类源逐字段 + ~90 测试护栏；分批比对 |
| render 快照大面积变 | 几何固化/CSS 生成改了 DOM | 先保证生成 CSS 与手写**逐字节等价**，再迁移；golden 快照分批 |
| 治理平台耦合 | LTE 绑死 templating 内部实现 | 仅依赖稳定接口（admin_store/admission/roles）；几何 hook 单向注入 |
| 5 态对布局偏重 | admission 流程冗余 | W0 定轻量晋升路径；合成探针放宽 |
| collage 误判 | 检测精度不足 | 保守检测 + 手动改判 + 开关可回退 + 独立工作项不阻断主线 |
| 命名混淆 | `templates`/`templating`/`layout_templates`/`mosaic` 四者 | W1 改名 `pattern_catalog`；adapter 单入口；本文 §1.4 명确边界 |

---

## 4. W1 开工清单（可直接认领）

> 前置：W0 的 `layout_template.schema.json` 与 `cli validate` 骨架已合入分支。

### 4.1 任务卡（建议顺序）

- [x] **T1 包骨架**：建 `travelogue/layout_templates/{__init__,registry,geometry,validator,css_gen,cli}.py` + `templates/`、`probes/`、`lte_policy.yaml`
- [x] **T2 逆向 YAML 脚本**：`scripts/lte_reverse_from_legacy.py`，从 legacy 源生成 `templates/*.yaml`（**如实复刻脏数据**）
- [x] **T3 Registry 加载**：YAML 解析 → `TemplateDef`；`photoCount` 倒排索引；`registry.cache.json` + 内容哈希失效；`list_active(window_size)` p99 <1ms 基准
- [x] **T4 几何**：`geometry.py` 加权轨道 `displayAspect(slot, stage)`；`solve_tracks(targets)`；`slot_aspect_table(id)`
- [x] **T5 导出 + parity**：`scripts/lte_export_legacy.py`（YAML→legacy 片段）；`tests/test_lte_registry_parity.py` 覆盖 **6 类源 + `grid-template` 字符串**
- [x] **T6 Adapter**：`mosaic/lte_adapter.py`；`candidates.py` 用 `registry=` 注入；`read_templates_from_lte` **默认 true（W3）**
- [x] **T7 改名**：`mosaic/pattern_catalog.py` generated re-export；`lte_adapter` 单入口

### 4.2 触碰文件清单（W1）

**新增**：`travelogue/layout_templates/**`、`travelogue/curation/mosaic/lte_adapter.py`、`scripts/lte_reverse_from_legacy.py`、`scripts/lte_export_legacy.py`、`tests/test_lte_registry_parity.py`
**修改**：`travelogue/curation/mosaic/candidates.py`、`travelogue/config/layout.py`、`travelogue/curation/mosaic/registry.py`（改名）
**只读依赖（parity 比对源）**：`mosaic/grid_specs.py`、`mosaic/constants.py`、`mosaic/slot_geometry.py`

### 4.3 W1 验收门（Definition of Done）

1. `python -m travelogue.layout_templates.cli validate` 对全量逆向 YAML 通过。
2. `pytest tests/test_lte_registry_parity.py` 绿（6 类源逐字段等价）。
3. **全量 mosaic 测试（~90 个）零回归**（开关 false 时行为 ≡ 现 P15）。
4. `list_active(window_size)` p99 <1ms；`registry.cache.json` 与 YAML 同步。
5. 对应 AC：**AC-P16-01、02、12、17**。

---

## 5. 关联文档

- 设计与契约：[PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md)
- 前置阶段：[PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md)
- 复用平台：`travelogue/templating/`（生命周期/审计/RBAC/审批）

---

## 6. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-06 | W1 开工版：融合设计（9 融合点）、模块结构、W0–W4 阶段交付与工作量、MVP 切法、风险登记、W1 任务卡 + 触碰文件 + 验收门 |
| v1.1 | 2026-06-06 | 第三轮闭合：§13.3 dogfood/user 3P+2L、primitive 扩展、V-P16-13 sign-off、CSS audit 口径 |
