# IMPLEMENTATION · 完工表面积收敛 CSC V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) v0.2.2 |
| **DOC-STATUS** | **active**（登记见 [DOC-STATUS.md](./DOC-STATUS.md)） |
| **分支** | `feat/csc-w0-recipe` |
| **状态** | **W0–W3 + 合同补齐** · CI 棘轮已挂；ACCEPTANCE 已拆；W1 测评三题桌面/静态 Pass；实机狗粮勾选可选 |
| **根治** | [csc-root-cause-cure-2026-07-22.md](./acceptance-records/csc-root-cause-cure-2026-07-22.md) |
| **验收** | [ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md](./ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md) |
| **更新日期** | 2026-07-22 |

---

## 0. 实施原则（摘自 PRD）

1. **先可见，后挂载，再减法** — 禁止首波批量关 True / 一键开 False。  
2. **SFI 未合入不影响 CSC** — 从 `master`（已含 CSC 文档）开分支实施。  
3. **与 AAD WIP** — 不抢 `curate.py` 大拆；本波只做 Recipe / 基线 / 后续 facade。  
4. 每 PR：**代码 + 证据 + 回滚说明**。

---

## 1. 波次任务卡

### W0 · Recipe 初稿 + 基线（切片 A）

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W0-01 | `happy_path_recipe.py` 只读快照 API | **Done** |
| CSC-W0-02 | 基线 JSON `csc-w0-baseline-happy-path-recipe.json` | **Done** |
| CSC-W0-03 | 单测锁定快照 + Danger 防火墙仍为 False | **Done** |
| CSC-W0-04 | Danger/Research 种子分档（代码常量） | **Done** · 续标见 [csc-w0-bool-tier-review.md](./acceptance-records/csc-w0-bool-tier-review.md)（33 pending） |
| CSC-W0-05 | 设置面库存表（FE） | **Done** · [csc-w0-settings-surface-inventory.md](./acceptance-records/csc-w0-settings-surface-inventory.md) |
| CSC-W0-06 | L0/L1 键表草案 | **Done** · [csc-w0-l0-l1-keys.md](./acceptance-records/csc-w0-l0-l1-keys.md) · `L1_RESULT_KEYS`（3≤10） |
| CSC-W0-07 | 对照集命令写入本节 | **Done** · 见下方 |
| CSC-W0-08 | DIFF 空表 | **Done** · [csc-w0-diff-empty.md](./acceptance-records/csc-w0-diff-empty.md) |
| CSC-W0-09 | 测评数字（L1 点击 ≤2） | **Done** · 写入 ACCEPTANCE |
| CSC-W0-10 | 祖父条款清单 | **Done** · [csc-w0-grandfather-clauses.md](./acceptance-records/csc-w0-grandfather-clauses.md) |
| CSC-W0-11 | cli vs studio 差异 | **Done** · [csc-w0-cli-vs-studio-profile.md](./acceptance-records/csc-w0-cli-vs-studio-profile.md) |

**验证**

```powershell
python -m pytest tests/unit/orchestrator/test_happy_path_recipe.py -q
```

**对照集（行为未变时的回归尺子 · CSC-W0-07）**

```powershell
# Recipe / 默认面合同
python -m pytest tests/unit/orchestrator/test_happy_path_recipe.py -q

# 编排薄面不回归
python -m pytest tests/unit/orchestrator/test_orchestrator_studio_profile.py -q

# 布局引擎快路径（有意改版式前必跑；本波应全绿）
python -m pytest tests/unit/layout_engine -q --maxfail=5

# 可选：配置 PATCH/expose 烟测
python -m pytest tests/unit/web/test_studio_config.py -q --maxfail=3
```

**回滚**：还原 `happy_path_recipe.py`、基线 JSON、库存/键表 md 与单测；运行时无挂载点，无行为回滚面。

### W1 · Recipe 挂载 + UI 派生

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W1-01 | 主路径宣告 `recipe_id=studio_default`（GET config → `happyPath.recipeId`） | **Done**（零管线行为变更） |
| CSC-W1-02 | `l1_keys` ≤10；`studio_config_expose` 增加 `happyPath`（旧字段保留） | **Done** |
| CSC-W1-03 | 设置常用/高级分层（文案 + `data-csc-tier`） | **Done**（轻改；未删控件） |
| CSC-W1-04 | Happy Path 用户短文（无黑话） | **Done** · [csc-w1-happy-path-user-copy.md](./acceptance-records/csc-w1-happy-path-user-copy.md) |
| CSC-W1-05 | 测评三题手测记录 | **Done** · [csc-w1-dogfood-three-questions-2026-07-22.md](./acceptance-records/csc-w1-dogfood-three-questions-2026-07-22.md) |
| CSC-W1-06 | 短文挂帮助/设置（F-CSC-3） | **Done** · 帮助 **H0** + 设置链 |

### W2a · facade

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W2a-01 | `layout_engine/api.py` + 包级 `__all__` | **Done** |
| CSC-W2a-02 | `scripts/lint_layout_engine_facade.py` + baseline（只降不升） | **Done** |
| CSC-W2a-03 | 调用点改经 facade（services/layout · curate · web replan/pipeline） | **Done** |
| CSC-W2a-04 | 清零 planner/mosaic 深 import（curation/services/web） | **Done** · baseline count=0 |

**验证**

```powershell
python scripts/lint_layout_engine_facade.py
python -m pytest tests/unit/layout_engine/test_public_api.py tests/unit/orchestrator/test_happy_path_recipe.py -q
```

### W2b/c · 棘轮

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W2b-01 | `lint_csc_god_module_ratchet.py` 钉 `curate.py` / `studio_pipeline.py` 行数 ceiling | **Done** |
| CSC-W2b-02 | 与 AAD 对齐的 curate 大拆 | **Parking**（本分支不做；只禁净增） |
| CSC-W2c-01 | pipeline 机会主义抽取 | **Parking**（棘轮已拦膨胀） |

**验证**

```powershell
python scripts/lint_csc_god_module_ratchet.py
```

> 有意加行须同 PR 带 `--allow-growth` 更新 baseline，并在 PR 说明理由。

### W3a · 结构化债务表

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W3a-01 | 债务扫描（legacy 文件名 + `shim →` docstring） | **Done** · 24 条 |
| CSC-W3a-02 | `lint_csc_debt_table.py` ceiling（只降不升） | **Done** |
| CSC-W3a-03 | 人读表 `csc-w3-debt-table.md` | **Done** |
| CSC-W3a-04 | 按批删除无调用 shim | **Parking**（下批；本波只钉 ceiling） |

**验证**

```powershell
python scripts/lint_csc_debt_table.py
```

### W3b · 配置分层

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W3b-01 | `config.user.example.yaml`（L0 + L1≤10） | **Done** |
| CSC-W3b-02 | `config.yaml.example` 标为 research/全量面 | **Done** |
| CSC-W3b-03 | 分层说明 md | **Done** · [csc-w3-config-surface-split.md](./acceptance-records/csc-w3-config-surface-split.md) |

### W3c · 文档状态示范

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W3c-01 | [DOC-STATUS.md](./DOC-STATUS.md) 状态机 + 入口 | **Done** |
| CSC-W3c-02 | ≥5 篇示范标注 | **Done**（含 ACCEPTANCE · 现行导读） |

### 合同补齐（对照 PRD 缺口）

| ID | 任务 | 状态 |
|----|------|------|
| CSC-GAP-01 | 拆 ACCEPTANCE | **Done** |
| CSC-GAP-02 | CI 挂 facade / god / debt / recipe baseline | **Done** · `.github/workflows/ci.yml` |
| CSC-GAP-03 | AC-CSC-05 薄边界表 | **Done** · ACCEPTANCE §1.1 |
| CSC-GAP-04 | D-CSC-06 现行导读 | **Done** · DOC-STATUS |

**验证（合同补齐）**

```powershell
python scripts/lint_layout_engine_facade.py
python scripts/lint_csc_god_module_ratchet.py
python scripts/lint_csc_debt_table.py
python scripts/lint_csc_recipe_baseline.py
python -m pytest tests/unit/orchestrator/test_happy_path_recipe.py -q
```

---

## 2. 产物路径

| 产物 | 路径 |
|------|------|
| Recipe 模块 | `travelogue/orchestrator/happy_path_recipe.py` |
| W0 基线 | `docs/acceptance-records/csc-w0-baseline-happy-path-recipe.json` |
| 设置库存 | `docs/acceptance-records/csc-w0-settings-surface-inventory.md` |
| L0/L1 键表 | `docs/acceptance-records/csc-w0-l0-l1-keys.md` |
| 单测 | `tests/unit/orchestrator/test_happy_path_recipe.py` |
| Facade API | `travelogue/layout_engine/api.py` |
| Facade lint | `scripts/lint_layout_engine_facade.py` |
| Facade baseline | `docs/acceptance-records/csc-w2a-facade-deep-import-baseline.json`（**0** 边） |
| God-module ratchet | `scripts/lint_csc_god_module_ratchet.py` |
| God-module baseline | `docs/acceptance-records/csc-w2b-god-module-ratchet-baseline.json` |
| 债务表 lint | `scripts/lint_csc_debt_table.py` |
| 债务表 baseline | `docs/acceptance-records/csc-w3-debt-table-baseline.json`（**24**） |
| 债务表（人读） | `docs/acceptance-records/csc-w3-debt-table.md` |
| 用户档 example | `config.user.example.yaml` |
| 配置分层说明 | `docs/acceptance-records/csc-w3-config-surface-split.md` |
| 文档状态入口 | `docs/DOC-STATUS.md` |
| 验收合同 | `docs/ACCEPTANCE-COMPLETION-SURFACE-CONVERGENCE-V1.md` |
| Recipe baseline lint | `scripts/lint_csc_recipe_baseline.py` |
| 祖父条款 | `docs/acceptance-records/csc-w0-grandfather-clauses.json` |
| 四档续标 | `docs/acceptance-records/csc-w0-bool-tier-review.json` |
| DIFF 空表 | `docs/acceptance-records/csc-w0-diff-empty.md` |
| cli vs studio | `docs/acceptance-records/csc-w0-cli-vs-studio-profile.md` |
| 测评三题 | `docs/acceptance-records/csc-w1-dogfood-three-questions-2026-07-22.md` |

**更新基线（仅在有意变更默认 / L1 名单时）**

```powershell
python -c "import json; from pathlib import Path; from travelogue.orchestrator.happy_path_recipe import studio_default_recipe as r; d=r(); keys=('recipe_id','schema_version','orchestration','counts','appconfig_bools','danger_must_stay_false','l0_ops_roots','l1_keys','advanced_settings_keys'); g={k:d[k] for k in keys}; g['layout_exit']={k:d['layout_exit'][k] for k in ('studio_export_layout','web_layout_engine_config')}; Path('docs/acceptance-records/csc-w0-baseline-happy-path-recipe.json').write_text(json.dumps(g,indent=2,ensure_ascii=False)+chr(10),encoding='utf-8')"
```

---

## 3. 合并策略备忘

| 主题 | 决议 |
|------|------|
| SFI `feat/share-face-integrity-w0` | **暂不合 master**（AC-12 盲评未闭合） |
| CSC 文档 | **已合 master**（`docs/csc-prd-v0.2.2` → merge） |
| 本实施分支 | 从含 CSC 文档的 `master` 开出 `feat/csc-w0-recipe` |
