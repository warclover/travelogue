# Phase 16 · 布局模板引擎（LTE）使用说明

| 属性 | 内容 |
|------|------|
| **文档** | GUIDE-PHASE16-layout-template-engine |
| **适用版本** | Phase 16（`p16-2026-06` registry） |
| **配套** | [PRD](./PRD-PHASE16-layout-template-engine.md) · [实施清单](./IMPLEMENTATION-PHASE16.md) · [Admission 设计](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) |
| **读者** | 开发/运维、模板作者、Studio 后台操作者 |

---

## 1. 这是什么

**LTE（Layout Template Engine）** 是 Travelogue Phase 16 引入的**拼图布局模板引擎**，负责：

- 以 YAML 定义拼图 pattern（slot 几何、gridClass、生命周期、评分权重）
- 向 MCS（章内拼图选版）提供候选 pattern 注册表
- 生成/同步 `journal-screens.css` 中的 grid 样式
- 在 Studio 后台展示几何探针、配额告警、曝光指标与调权提案

**LTE 不负责**：选哪些照片、章序、叙事弧、curate 后的 fit 执行——这些仍由 MCS / curate 管线负责。

```
curate → MCS（lte_adapter 读 LTE registry）→ 选 patternId + 照片分配
                                              ↓
                                    journal-screens.css（LTE 生成 grid）
                                              ↓
                                    预览 / 导出 / 长图
```

---

## 2. 快速启用与回退

### 2.1 默认行为

P16 合并后，以下开关**默认开启**（见 `config.yaml.example`）：

```yaml
layout:
  template_engine:
    enabled: true
    read_templates_from_lte: true   # MCS 从 LTE YAML 读 pattern，而非 legacy Python 常量
    exclude_collage_from_mosaic: true
    max_mosaic_slots: 9
    overrides:
      disable: []                   # 紧急零曝光，不改 YAML
```

### 2.2 一键回退到 Phase 15

若线上需临时恢复 P15 行为：

```yaml
layout:
  template_engine:
    read_templates_from_lte: false
```

无需改代码或删 YAML；重启 Studio / 重新 curate 即可。parity 测试与 CI 仍覆盖 LTE 路径。

### 2.3 紧急禁用单个 pattern

不改 Git 中的 YAML，在 `config.yaml` 写入：

```yaml
layout:
  template_engine:
    overrides:
      disable:
        - screen-portrait-3
        - screen-mosaic-5-3portrait-2land-balanced
```

被 disable 的 pattern：**MCS 不选**、**CSS 仍可渲染**（已有 trip 不受影响）。与 `deprecated`（仍可被 MCS 选但降权）和 `disabled`（YAML 生命周期态）不同，详见 §5。

### 2.4 MCS 候选多样性

`lte_policy.yaml` 与 config 均可配置章内多样性（MMR / DPP）：

```yaml
layout:
  template_engine:
    mcs_integration:
      scoring:
        diversity:
          mode: mmr    # off | mmr | dpp
          lambda: 0.65
```

---

## 3. 目录与核心模块

| 路径 | 用途 |
|------|------|
| `travelogue/layout_templates/templates/*.yaml` | 布局模板定义（GitOps 源） |
| `travelogue/layout_templates/lte_policy.yaml` | 配额、统一窗口族、曝光控制器参数 |
| `travelogue/layout_templates/registry.py` | 加载 YAML、active 过滤、配额检查 |
| `travelogue/layout_templates/validator.py` | 几何校验、publish 门禁 |
| `travelogue/curation/mosaic/lte_adapter.py` | MCS ↔ LTE 适配层 |
| `templates/visual-journal/journal-screens.css` | 前端 grid（含 LTE 生成 marker 块） |
| `travelogue/layout_templates/_legacy_generated.py` | export 产物，供 grid_specs 薄引用 |

模板 YAML 命名：`screen-{描述}.yaml`，`templateId` 与文件名一致。

---

## 4. CLI 工作流

入口：

```bash
python -m travelogue.layout_templates.cli <command> [options]
```

### 4.1 validate — 校验模板

```bash
# JSON Schema
python -m travelogue.layout_templates.cli validate

# CI 语义门禁（V-P16-01~14）
python -m travelogue.layout_templates.cli validate --semantic

# 发布门禁（含 sign-off、quota、strict blocks）
python -m travelogue.layout_templates.cli validate --publish
```

PR 修改 YAML 后**必须** `--semantic` 通过；晋升 GA 前需 `--publish` 通过。

### 4.2 export — 生成 CSS

```bash
python -m travelogue.layout_templates.cli export --sync-journal
```

- 输出：`travelogue/layout_templates/journal-screens.generated.css`
- `--sync-journal`：将生成块注入 `templates/visual-journal/journal-screens.css` 的 LTE marker 区间

修改 slot 几何或 gridClass 后，**必须**重新 export 并提交 CSS，否则预览会出现 stale 提示（§9.1）。

### 4.3 docgen — slot 宽高比文档

```bash
python -m travelogue.layout_templates.cli docgen --out docs/templates/slot-aspect
```

为每个 template 生成 Markdown 形式的 slot AR 表，供评审与 Admission 附件使用。

### 4.4 solve-tracks — 逆设计 track 权重

```bash
python -m travelogue.layout_templates.cli solve-tracks screen-portrait-3 --json
```

根据 slot 目标宽高比，推算 stage 的 `cols` / `rows`，用于新模板 authoring。

### 4.4 check-primitives — primitive 与 catalog 一致性

```bash
python -m travelogue.layout_templates.cli check-primitives
```

确保 screen-planner primitive YAML 与 `primitive_catalog.py` 参数化定义一致（CI 门禁）。

---

## 5. 模板生命周期（5 态）

对齐既有 `travelogue/templating/lifecycle.py`，**不**使用 draft/active：

| 状态 | MCS 可选 | CSS 可渲染 | 说明 |
|------|----------|------------|------|
| `experimental` | 否（默认） | 是 | 新注册，待 admission |
| `beta` | 是（灰度） | 是 | 通过 admission，小流量验证 |
| `ga` | 是 | 是 | 正式发布 |
| `deprecated` | 是（降权） | 是 | 旧 trip 保持视觉；新 trip 逐步淘汰 |
| `disabled` | 否 | 是 | 软停用；与 `overrides.disable` 效果类似但走 YAML |

状态变更**仅 GitOps**：改 YAML 的 `status` + `version++`，经 CI validate/publish 后合并。Studio「晋升」按钮会生成 patch 计划，实际写入仍走 Git（或 `--apply` CLI）。

### 5.1 晋升 CLI

```bash
# 查看 promotion 计划（admission 门禁）
python scripts/lte_promote_template.py screen-mosaic-5-2p3l-equal --target beta

# admission 通过后写入 YAML
python scripts/lte_promote_template.py screen-mosaic-5-2p3l-equal --target ga --apply
```

Admission 步骤详见 [LTE-ADMISSION-LAYOUT-TEMPLATES.md](./LTE-ADMISSION-LAYOUT-TEMPLATES.md)（schema → 几何 → 探针 → quota → sign-off 等）。

### 5.2 配额（lte_policy.yaml）

活跃模板数受配额约束，例如：

- 5 图 composite：`max_active_composite: 6`，`max_active_total: 10`
- 9 图 primitive：`max_active_primitive: 2`，`max_active_total: 4`

超出时 `validate --publish` 与 Studio 后台均会告警。

### 5.3 AR Ladder Sign-off

部分 composite 模板（如 hero+4 类）要求 slot 0 填写 `constraints.arLadderSignOff`。未 sign-off 时 `--publish` 失败。Sign-off 表示作者确认 slot 宽高比阶梯与探针结果可接受。

---

## 6. Studio 后台管理

### 6.1 启动与入口

```bash
python -m travelogue studio
# 或指定 trip 文件夹
python -m travelogue studio --pick-folder "D:\Photos\某次旅行"
```

浏览器打开：

- **模板管理总页**：`/templates-admin`
- **布局模板区**：同页下方「布局模板（LTE · internal）」区块

### 6.2 访问控制

布局模板目录在以下情况**可见**：

1. 请求来自 **loopback**（`127.0.0.1` / `localhost`），或
2. `config.yaml` 设置：

```yaml
studio:
  layout_templates_internal: true
```

非 loopback 且未开 internal 时，页面显示提示，布局表格隐藏（作品级模板区仍可用）。

### 6.3 页面功能一览

| 区域 | 功能 |
|------|------|
| **布局模板表格** | templateId、lifecycle、version、gridClass、stage 几何、slot AR 探针条、曝光占比 |
| **配额告警** | 活跃模板超出 `lte_policy` 配额时列表提示 |
| **布局指标** | 近 24h 曝光、候选命中、fallback、win p50、face crop 等 |
| **曝光负债调权提案** | §9.4 控制器生成的 `base_weight` 建议；需双人审批 |
| **待审批配置变更** | 曝光调权 / 路由运行时 patch 的审批队列 |
| **晋升 GA / Beta** | 触发 `promote_layout_template`，返回 admission 结果与 YAML patch 计划 |

布局模板**几何变更不走后台表单**，一律 YAML PR + export CSS + CI。

### 6.4 相关 API（内部）

由 `travelogue/web/studio_handlers/template_admin_handlers.py` 提供，例如：

- `GET /__travelogue/admin/templates` — 列表（含 `layoutPatterns`、`layoutQuotaWarnings`）
- `POST /__travelogue/admin/templates/action` — `promote_layout_template`、曝光提案提交/审批

RBAC 复用 `travelogue/templating/roles`（viewer / template_operator / template_admin）。

---

## 7. 运维与验收脚本

### 7.1 Dogfood 曝光评估（AC-P16-08/15）

```bash
# 生成指标 JSON
python scripts/phase16_template_eval.py \
  --trips-dir tests/fixtures/phase16-dogfood \
  --json-out /tmp/phase16-eval.json

# CI 严格门禁
python scripts/phase16_template_eval.py --strict-ac15
```

读取 `tests/fixtures/phase16-dogfood/{portrait-heavy,landscape-heavy}/trip.json`，统计 pattern 曝光分布、多样性、mixed-layout 比例等，并与 `docs/acceptance-records/phase16-template-eval-baseline.json` 对比。

### 7.2 重生成 dogfood fixture

静态 fixture 与 golden MCS planner 对齐：

```bash
python scripts/phase16_curate_dogfood.py
```

策略见 `docs/acceptance-records/phase16-dogfood-curate-policy.json`。修改 MCS 选版逻辑后应重跑此脚本并更新 baseline。

### 7.3 探针回归

```bash
# 合成几何/saliency 探针
python scripts/lte_probe_regress.py

# Playwright 截图 diff（需安装浏览器）
python scripts/lte_probe_regress.py --screenshot --strict
```

#### 7.3.1 指标语义（务必先读，避免误判）

探针有**两个互补指标**，分工不同，请勿混读。一句话：
`worstProbeDistance` 看「槽形 vs 资产纵横比」，`worstSaliencyRetention` 看「cover 裁切是否丢焦点」。

| 指标 | 含义 | 阈值 | 分工 |
| --- | --- | --- | --- |
| `worstProbeDistance` | 槽位 display aspect 与该槽**角色兼容**的探针纵横比中的最差几何距离 | `> 0.80` 告警 | 槽形与资产比是否匹配 |
| `worstSaliencyRetention` | 资产在 `object-fit: cover` 中心裁切后焦点仍可见的比例 | `< 0.55` 告警 | cover 裁切是否丢焦点 |

**为什么是 role-aware（关键，曾被误读为 88 个布局 bug）**：
一个槽永远只装与其 role 同向的资产（portrait 槽不会收到 16:9），所以几何拟合**只能**对**角色兼容**的探针子集取 max——绝不能对相反极端取 max。
若对**全部**纵横比取最差，存在硬数学下限 `0.4375`（正方形槽到 9:16 与 16:9 等距），因此历史 `0.35` 阈值**几何上不可达**，会无条件点亮每一个槽（88/88），让 `--strict-geometry` 永远无法通过。
修复后的 `worstProbeDistance` 只对 role 兼容的探针取 max，这是**指标语义修正**，不代表「布局变好了」——别把告警数当成布局 bug 数。

**`0.80` 阈值依据**：GA 语料的几何上限是 `0.75`（legacy 反向迁移的 `screen-portrait-3`，三张竖图塞进 9:16 stage，其硬中心裁切已验证焦点安全：saliency retention 1.0）。`0.80` 紧贴该基线之上，构成棘轮：拦截真正新出现的几何回归（槽与角色严重错配），同时接纳既有的有意密集网格。

**saliency 现状与门禁价值**：当前所有出货 `PROBE_PROFILES` 的焦点都接近中心，因此每个真实槽的 retention 都是 `1.0`，`0.55` 阈值目前**不会触发**——它更像是为后续 person-tag / 极端 focal 语料预留的信号位，而非现役门禁。其机制本身有效（见 `tests/test_lte_p4_gaps.py::test_saliency_gate_is_not_a_noop`：偏心 focal 可将 retention 压到 0.55 以下）。**结论**：CI 暂不因 saliency fail，待真实 person/边缘 focal 用例补全后再启用阈值。

> 实现见 `travelogue/layout_templates/probe_regress.py`（`ROLE_PROBE_KEYS`、`GEOMETRY_WARN_THRESHOLD`、`PROBE_PROFILES`）。

### 7.4 CSS 审计

```bash
python scripts/lte_journal_css_audit.py
```

检查 `journal-screens.css` 中 LTE marker **之外**是否出现重复的 `layout-screen__grid--*` 类（CI 以 duplicate 为门禁）。

### 7.5 Legacy export（供 grid_specs 引用）

```bash
python scripts/lte_export_legacy.py
```

将 registry 元组导出到 `_legacy_generated.py`，保持与 P15 常量层的 parity。

---

## 8. 曝光负债调权（§9.4）

运行时调整模板 `base_weight`，**不改 YAML**，需双人审批。

完整流程见 [phase16-exposure-debt-runbook.md](./reports/phase16-exposure-debt-runbook.md)。摘要：

1. **生成提案**：`phase16_template_eval.py --trips-dir ... --propose --operator admin-1`
2. **Studio 提交**：`/templates-admin` →「提交调权提案」
3. **双人审批**：CLI `--approve cfg-id --approver admin-2`（两人均不可与 proposer 相同），或 Studio 审批 UI
4. **生效**：写入 `runtime.layout_template_base_weights`；MCS 经 `lte_adapter.template_base_weight()` 读取
5. **回滚**：反向 propose 或手动 runtime PATCH（同样需审批）

参数（`lte_policy.yaml` → `exposure_control`）：

- `damping: 0.5`
- `min_weight: 0.5`，`max_weight: 2.0`

---

## 9. 故障排查

### 9.1 预览提示「CSS 可能过期 / stale」

**原因**：YAML 或 registry 版本已变，但 `journal-screens.css` 未 re-export。

**处理**：

```bash
python -m travelogue.layout_templates.cli export --sync-journal
```

刷新预览。E2E 覆盖见 `tests/test_lte_studio_playwright.py`（AC-11）。

### 9.2 MCS 选不到某 pattern

检查顺序：

1. YAML `status` 是否为 `ga` / `beta`（`experimental` / `disabled` 不可选）
2. `layout.template_engine.overrides.disable` 是否包含该 id
3. `read_templates_from_lte` 是否为 `true`
4. 窗口大小是否在 `mosaic.enabled_window_sizes` 内
5. Admission / quota 是否通过

### 9.3 validate --publish 失败

常见原因：缺少 sign-off、slot AR 越界、quota 超限、primitive catalog 漂移。阅读 JSON 输出中的 `[code]` 字段，对照 PRD 验收项 V-P16-xx。

### 9.4 与 P15 行为不一致

1. 确认 `read_templates_from_lte` 开关
2. 跑 parity / golden 测试：`tests/_golden/`、`tests/test_lte_*`
3. 对比 `lte_adapter` 与 legacy registry 的 patternId 列表

### 9.5 deprecated pattern 仍出现在旧 trip

**预期行为**：deprecated 仅影响新 curate，不自动迁移已有 trip（PRD NG-P16-07）。需用户主动重排版（规划 P17）。

---

## 10. CI 门禁摘要

`.github/workflows/ci.yml` 中与 P16 相关的主要步骤：

| 步骤 | 命令/条件 |
|------|-----------|
| LTE validate | `cli validate --semantic` |
| primitive drift | `cli check-primitives` |
| CSS audit | `lte_journal_css_audit.py`（duplicate=0） |
| dogfood AC-15 | `phase16_template_eval.py --strict-ac15` |
| collage recall | `--min-recall 0.7` |
| probe / Playwright | `lte_probe_regress.py`、`test_lte_studio_playwright.py`（按 job 配置） |

---

## 11. 新增模板 Checklist

1. 在 `travelogue/layout_templates/templates/` 新增 YAML（`status: experimental`）
2. `cli validate --semantic` → 修几何 / sign-off
3. `cli export --sync-journal` → 提交 CSS
4. `cli docgen` → 更新 slot-aspect 文档（可选）
5. `lte_probe_regress.py` → 探针通过
6. Admission 全绿 → `lte_promote_template.py --target beta --apply`
7. dogfood 曝光验证 → 必要时 `--propose` 调权
8. 晋升 GA → `--target ga --apply`，PR 合并

---

## 12. 延伸阅读

- [PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md) — 需求与验收项
- [DESIGN-PHASE16-layout-template-engine.md](./DESIGN-PHASE16-layout-template-engine.md) — 架构设计
- [IMPLEMENTATION-PHASE16.md](./IMPLEMENTATION-PHASE16.md) — 工程交付状态
- [LTE-ADMISSION-LAYOUT-TEMPLATES.md](./LTE-ADMISSION-LAYOUT-TEMPLATES.md) — Admission 步骤
- [phase16-exposure-debt-runbook.md](./reports/phase16-exposure-debt-runbook.md) — 曝光调权 SOP
