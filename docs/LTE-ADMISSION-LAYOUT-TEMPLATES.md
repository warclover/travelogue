# LTE · 布局模板轻量 Admission 设计说明

| 属性 | 内容 |
|------|------|
| **文档** | LTE-ADMISSION-LAYOUT-TEMPLATES |
| **版本** | W0（设计冻结） |
| **配套 PRD** | [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) §5、§6 |
| **状态** | 设计-only；W3 接线 `templating.admission` |

> Phase 16 **复用**既有 `travelogue/templating/` 治理平台（R-P16-12），**不**另造 `LayoutTemplateAdmin`。  
> 作品级模板 admission（manifest / golden-render）与拼图 layout pattern **分离**；布局模板走独立轻量步骤，注入 LTE §6 几何校验器。

---

## 1. 边界

| 维度 | 作品级模板（既有） | 布局模板 LTE（P16 新增） |
|------|-------------------|-------------------------|
| Registry | `travelogue/templates/registry.py` | `travelogue/layout_templates/templates/*.yaml` |
| Admission 入口 | `templating.admission.run_admission_check` | **`run_layout_template_admission`**（新 hook，W3） |
| 晋升状态机 | 同 5 态 | 同 5 态（`experimental/beta/ga/deprecated/disabled`） |
| 几何变更 | 后台 + GitOps 混合 | **仅 GitOps**（YAML PR + CI + `version++`） |
| 运营调参 | `config_governance` 两人审批 | 同（`base_weight` / rollout / `overrides.disable`） |

---

## 2. 复用清单（不重写）

- **生命周期**：`templating.admin_store.update_template_lifecycle`（乐观锁 If-Match / revision）
- **注册/删除**：布局模板 id 登记到 admin_store 扩展表或独立 index（W3）；物理 YAML 仍 GitOps
- **评审**：`templating.review`（`→ ga` 需人工批准）
- **审计/回滚**：`admin_store.list_audit` / `apply_rollback`
- **RBAC**：`templating.roles`（viewer / template_operator / template_admin）
- **Web**：`studio_handlers.template_admin_handlers` 扩展几何图示 / slotAspect / 探针条

LTE 唯一新增管理侧代码：`LayoutTemplateGeometryHook`（`validator.py`）

- `validate_for_publish(template_id) → ValidationReport`
- `slot_aspect_table(template_id) → list[SlotAspect]`
- `geometry_diff(template_id, va, vb) → GeometryDiff`

---

## 3. 轻量 Admission 步骤（`run_layout_template_admission`）

W3 实现；调用顺序建议：

| Step | 名称 | 内容 | 失败级别 |
|------|------|------|----------|
| S1 | `schema` | JSON Schema + `cli validate` 等价 | error |
| S2 | `registry` | YAML 存在于 `layout_templates/templates/`；id 与文件一致 | error |
| S3 | `geometry_static` | V-P16-01～06、09、12、14（确定性，无截图） | error / warn |
| S4 | `parity_export` | `export_legacy_registry()` 与 legacy 片段一致（W1 起 CI） | error（CI） |
| S5 | `probe_regression` | 合成探针 cover/contain 截图 diff（V-P16-07） | **见 §4 分级** |
| S6 | `guardrails_ga` | 复用 `ga_guardrail_errors` 中通用项（若适用） | error |
| S7 | `review_gate` | `→ ga` 时检查 `templating.review` 已批准 | error |

**跳过规则（相对作品级 admission）**：

- 不跑 trip manifest / golden-render HTML（布局 pattern 无 manifest.json）
- Stack 模板（`kind: stack`）走 §6.4 分支，跳过 3×3 `displayAspect` 阈值，改 per-slot 最小高度探针（warn）

---

## 4. 晋升路径与探针放宽（W0 定稿）

对齐 PRD §5.1 与 IMPLEMENTATION §1.3「5 态对布局偏重」缓解策略。

### 4.1 `experimental → beta`

**必过**：S1–S3 + V-P16-12（max≤9）+ V-P16-14（轨道权重 > 0、rect 不越界）

**放宽**：

- **V-P16-07 探针截图**：跳过（或 CI nightly warn-only）
- **V-P16-13 常规 AR 阶梯**：warn-only（不 block）
- **V-P16-11 parity**：若模板为**新增** id（非逆向迁移），可跳过；逆向模板必须在 W1 parity CI 已绿

**典型场景**：合成探针图在 `probes/` 目录自测通过后，operator 提 PR 改 YAML `status: beta` + admin_store 晋升。

### 4.2 `beta → ga`

**必过**：S1–S4 全绿 + S7 review 批准 + V-P16-13（超容差需人工 sign-off 记录在 review）

**探针**：

- **PR 合并**：V-P16-07 **warn**
- **Release / nightly**：V-P16-07 **error（block）**

### 4.3 `ga → deprecated` / `disabled`

- 走既有 lifecycle；**无需**重跑探针
- `deprecated`：MCS 新 trip 不候选；旧 trip 可渲染
- `disabled`：紧急关停；优先 `config.layout.template_engine.overrides.disable`（R-P16-08）

---

## 5. 与 `templating.admission.run_admission_check` 的关系

```text
template_admin promote(pattern_id, target=beta)
    │
    ├─ if registry_kind == "trip_template"
    │       └─ run_admission_check(template_id)   # 既有
    │
    └─ if registry_kind == "layout_pattern"
            └─ run_layout_template_admission(pattern_id)
                    └─ LayoutTemplateGeometryHook.validate_for_publish()
```

**单向依赖**：LTE hook 只调用 `layout_templates.*`；不 import `render.engine` 除非 S5 探针步骤显式启用。

---

## 6. W0 出口对照（R-P16-01～15 落点）

| 决议 | W0 落点 |
|------|---------|
| R-P16-01 | `travelogue/layout_templates/` 包 |
| R-P16-02 | Schema + `templates/*.yaml` 权威约定 |
| R-P16-07 | `registry.py` 占位 + `registry.cache.json` 路径常量 |
| R-P16-11 | `layout_template.schema.json` + `cli validate` |
| R-P16-12 | 本文 + `LayoutTemplateGeometryHook` 占位 |
| R-P16-13 | Schema `status` enum 5 态 |
| R-P16-14 | `css_gen.py` 占位 + schema `render.*` |
| R-P16-15 | Schema `stage.gap` + `cli solve-tracks` stub + 本文 §4 两人审批引用 |

---

## 7. 后续工作（W1–W3）

- **W1**：parity CI、`export_legacy_registry`；admission S4 可对接
- **W2**：`validate_for_publish` 全量 §6；S3 完整
- **W3**：`run_layout_template_admission` 接入 studio promote 流程；S5 探针脚本 `scripts/lte_probe_regress.py`
