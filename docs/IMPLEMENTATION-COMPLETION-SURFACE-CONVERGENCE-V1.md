# IMPLEMENTATION · 完工表面积收敛 CSC V1

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md](./PRD-COMPLETION-SURFACE-CONVERGENCE-V1.md) v0.2.2 |
| **分支** | `feat/csc-w0-recipe` |
| **状态** | **W0 Done · W1 进行中** · expose 已宣告 `happyPath`；设置 UI 已标 L1/Advanced 分层 |
| **根治** | [csc-root-cause-cure-2026-07-22.md](./acceptance-records/csc-root-cause-cure-2026-07-22.md) |
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
| CSC-W0-04 | Danger/Research 种子分档（代码常量） | **Done**（人审续标四档全表） |
| CSC-W0-05 | 设置面库存表（FE） | **Done** · [csc-w0-settings-surface-inventory.md](./acceptance-records/csc-w0-settings-surface-inventory.md) |
| CSC-W0-06 | L0/L1 键表草案 | **Done** · [csc-w0-l0-l1-keys.md](./acceptance-records/csc-w0-l0-l1-keys.md) · `L1_RESULT_KEYS`（3≤10） |
| CSC-W0-07 | 对照集命令写入本节 | **Done** · 见下方 |

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
| CSC-W1-05 | 测评三题手测记录 | Pending |

### W2a · facade（未开工）

| ID | 任务 | 状态 |
|----|------|------|
| CSC-W2a-01 | `layout_engine/api.py` + `__all__` | Pending |
| CSC-W2a-02 | 禁深 import CI | Pending |

### W2b/c · 棘轮（未开工）

对齐 AAD；`curate` / `studio_pipeline` 禁堆料。

### W3 · 清退（未开工）

债务表 ceiling · L1≤10 用户档 · 文档状态示范。

---

## 2. 产物路径

| 产物 | 路径 |
|------|------|
| Recipe 模块 | `travelogue/orchestrator/happy_path_recipe.py` |
| W0 基线 | `docs/acceptance-records/csc-w0-baseline-happy-path-recipe.json` |
| 设置库存 | `docs/acceptance-records/csc-w0-settings-surface-inventory.md` |
| L0/L1 键表 | `docs/acceptance-records/csc-w0-l0-l1-keys.md` |
| 单测 | `tests/unit/orchestrator/test_happy_path_recipe.py` |

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
