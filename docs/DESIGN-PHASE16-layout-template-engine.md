# Travelogue · Phase 16 设计说明（布局模板引擎 LTE）

| 属性 | 内容 |
|------|------|
| **文档** | DESIGN-PHASE16-layout-template-engine |
| **版本** | v1.0（实施对照 PRD v0.16.4） |
| **配套** | [PRD-PHASE16](./PRD-PHASE16-layout-template-engine.md) · [IMPLEMENTATION-PHASE16](./IMPLEMENTATION-PHASE16.md) · [LTE-ADMISSION](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) |
| **状态** | 与 W3 实现对齐 |

> **定位**：PRD 讲产品目标与验收；本文讲 **工程形态**——模块边界、数据流、与 P15 MCS / 既有 templating 平台如何接。

---

## 1. 架构总览

```
templates/*.yaml  ──registry──> LayoutTemplateEngine
       │                              │
       ├── css_gen ──> journal-screens.css (@lte-generated)
       ├── validator ──> admission / render_check
       ├── geometry ──> slotAspect / solidify screens[]
       └── export ──> legacy parity (grid_specs / constants)

lte_adapter ──> mosaic_registry() ──> MCS candidates / scorer
                     │
                     └── pattern_catalog (generated re-export)

templating/*  ──复用──> lifecycle / review / RBAC / audit
layout_admin  ──GitOps──> promotion.py + Studio handlers
```

**原则**：YAML 为模板几何唯一源（R-P16-14）；MCS 禁止直读 YAML，只经 `lte_adapter`。

---

## 2. 模块职责

| 模块 | 路径 | 职责 |
|------|------|------|
| Registry | `layout_templates/registry.py` | 加载 YAML、索引、quota、`registry.cache.json` |
| Geometry | `geometry.py` · `geometry_solidify.py` | displayAspect、curate 固化进 `screens[]` |
| Validator | `validator.py` | §6 门禁；`LayoutTemplateGeometryHook` 注入 admission |
| CSS-Gen | `css_gen.py` | YAML→grid CSS；overlay 见 `journal-screens-overlays.css` |
| Probe | `probe_regress.py` · `probe_screenshot.py` | 几何 warn + 截图 release block |
| Adapter | `curation/mosaic/lte_adapter.py` | MCS 唯一 LTE 入口 |
| Lifecycle | `promotion.py` · `layout_admin.py` | experimental→ga + review_gate |

---

## 3. 与 Phase 15 MCS 的接口

1. **候选**：`generate_window_candidates(registry=mosaic_registry())`；`deprecated`/`disabled`/`overrides.disable` 过滤。
2. **打分**：`scorer` 读 YAML `scoring.base_weight` / `rhythm`；§9.4 多样性经 `diversity.py`（MMR/DPP）。
3. **日志**：`MosaicWindowLog` → `mosaicDecisionLog`；debug 级字段（含 `rejectedTemplates`）汇入 `layoutDecisionLog`。
4. **Collage**：`media_classify` → `collage`；MCS 排除 + full-frame 路由；Studio 手动改判。

---

## 4. CSS 分层（R-P16-14）

| 层 | 文件 | 来源 |
|----|------|------|
| 基础舞台 | `journal-screens.css` 头部 | 手写（1col 等） |
| 模板 grid | `@lte-generated` 块 | **100% YAML 导出** |
| 行为 overlay | `@journal-overlays` 块 | `journal-screens-overlays.css`（data-pattern / layout-hint） |

`cli export --sync-journal` 替换 generated 块并截断 marker 后的 legacy grid 重复。

### 4.1 Overlay 贡献者约束（LRG T-LRG-02 · 详见 [PRD-LAYOUT-READER-REGRESSION-GUARD §3.2.4](./PRD-LAYOUT-READER-REGRESSION-GUARD.md#324-贡献者约束写入-contributing-或-phase-16-design-补丁)）

2026-07 曾发生章节票根 / EXIF / mosaic-5 contain overlay 因 `export --sync-journal` 静默截断而丢失，`test_reading_experience` FAIL 仍被 merge 的事故（详见 PRD §1.1）。为避免复发，任何触碰 `journal-screens.css` / `journal-screens-overlays.css` / `css_gen.py` 的改动**必须**遵守：

1. **禁止**在 `journal-screens.css` 的 `@journal-overlays:end` 之后追加手写规则——该区域会被 `export --sync-journal` 静默截断（`css_gen._truncate_trailing_legacy_after_overlays`，T-LRG-12 起默认 strict fail-fast，非零退出）。读者可见、非 LTE 生成的样式**只能**写在 `templates/visual-journal/journal-screens-overlays.css`（`@journal-overlays:start…end` 之前的手写内容会在下次 sync 时被合并/覆盖）。
2. **禁止**只改 `trips/*/journal-screens.css` 而不改 template overlays（`journal-screens-overlays.css`）——trip 目录下的 CSS 副本是 render 产物，下一次 render 会被无条件覆盖，双轨修改必然漂移（LRG-P-04）。
3. `export --sync-journal` 后必须跑：

   ```bash
   pytest tests/test_lte_css_sync.py tests/test_reading_experience.py -q
   ```

   确认全绿再 `git add` / commit 生成后的 `journal-screens.css`；CI `validate` job 的 "LTE journal CSS sync drift" 步骤会重跑同一 sync 并 `git diff --exit-code` 校验，本地先跑可避免 PR 反复往返。

---

## 5. 生命周期与准入

见 [LTE-ADMISSION-LAYOUT-TEMPLATES.md](./LTE-ADMISSION-LAYOUT-TEMPLATES.md)。

- **beta**：geometry_static + probe warn
- **ga**：+ review_gate + 截图 diff（CI strict）
- **deprecated**：旧 trip 可渲染；新 curate 不候选

---

## 6. 测试与 CI 护栏

- `test_lte_registry_parity.py` — 6 类 legacy 源等价
- `lte_probe_regress.py --screenshot --strict` — release block
- `collage_detect_eval.py` — 标注集 precision/recall
- `phase16_template_eval.py` — dogfood 曝光 / 多样性

---

## 7. W4 / P17 未决

- legacy Python 常量进一步 generated 化
- §9.4 曝光负债 + 两人审批闭环
- P17：匈牙利匹配 / 生成式 composite（见 `p17_research.py` stub）

---

*本文档为 AC-P16-10 可选设计说明；细节以 PRD 与 IMPLEMENTATION 为准。*
