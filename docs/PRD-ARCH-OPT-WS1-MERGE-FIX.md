# Travelogue · 架构优化 WS1 合并修复 PRD

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue（核心管线 + Studio） |
| **文档版本** | **v1.0.0-ARCH-WS1-FIX** |
| **状态** | **In Progress · M-F0～F5 工作区已落地（待提交）** |
| **性质** | **合并阻断修复 PRD**：零 intentional 功能变更；仅修复 WS1 合并前缺陷与门禁漂移 |
| **触发来源** | 2026-07-09 首席测试专家对 `arch/optimization-ws1` 的代码质量审查 |
| **目标分支** | `arch/optimization-ws1` → `master` |
| **关联文档** | [PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) · [ARCH-OPT-STATUS.md](./ARCH-OPT-STATUS.md) · [adr/015-lse-planner-migration.md](./adr/015-lse-planner-migration.md) · [TESTING.md](./TESTING.md) · [QUALITY-GATE.md](./QUALITY-GATE.md) |
| **更新日期** | 2026-07-09 |

---

## 0. 文档说明

### 0.1 定位：这是「合并闸门修复」PRD，不是新功能 PRD

[PRD-ARCH-OPTIMIZATION.md](./PRD-ARCH-OPTIMIZATION.md) WS1 里程碑已于 **2026-07-08** 在状态表标记全部 done，但 2026-07-09 合并前审查发现：

1. **P0 正确性断裂**：LSE batch-4 `feedback` 迁移切分不完整，导致测试收集失败。
2. **P1 门禁漂移**：LSE cross-import 基线 JSON / 文档口径 / 单测期望不一致。
3. **P1 CI 盲区**：cross-import 回归仅在周度 job，PR 路径不可见。
4. **P2 平台脆弱性**：跨进程 CAS 在 Windows `spawn` 下偶发失败；文件锁仍为遗留项。

本 PRD **只覆盖合并阻断与直接相关的门禁修复**。不重开 WS1 范围，不引入 LONGSHOT 2.0，不清理全部预存 `pytest --fast` 失败。

### 0.2 范围承诺

| 承诺 | 说明 |
|------|------|
| **零 intentional 功能变更** | 不改变用户可见功能、API 语义、产物版式 |
| **修复而非重构** | 优先最小 diff；禁止顺手扩大迁移面 |
| **证据驱动** | 每个里程碑交付：代码 + 复现命令输出 + 回滚说明 |
| **工作区隔离** | LONGSHOT 2.0 WIP 必须独立分支；不得混入本修复 PR |

### 0.3 非目标（明确排除）

| # | 排除项 | 理由 |
|---|--------|------|
| OUT-01 | LONGSHOT 2.0 实现 / 文档合入 | 独立 PRD；工作区未跟踪文件不得混入 |
| OUT-02 | 全量 `pytest --fast` ~25–56 预存失败清零 | 状态表已记为背景项；分批 issue |
| OUT-03 | Mosaic shim 退役 / DeprecationWarning 清零 | 属 ADR-015 §3.3 DoD，非合并阻断 |
| OUT-04 | `.trip.lock` 跨进程文件锁落地 | M-A1c 已标注跳过；本 PRD 仅加固测试稳定性（可选） |
| OUT-05 | CacheRegistry（G-ARC-06） | 独立立项 |
| OUT-06 | 一次性迁移脚本归档（`migrate_lse_*` / `split_*`） | 可跟进 chore，不阻塞合并 |

### 0.4 问题总览与优先级

| 优先级 | 编号 | 问题 | 证据锚点 | 合并影响 |
|--------|------|------|----------|----------|
| **P0** | FIX-01 | `record_g1_edit` 未迁入 `layout_contract.feedback`，但 `studio_feedback` 从该模块导入 | `layout_engine/studio_feedback.py:9` · HEAD `layout_contract/feedback.py` 无该符号 · `tests/integration/p17/test_p17_studio_feedback.py` 收集 ImportError | **阻断**：`pytest tests/` 收集失败；`test-integration` 红 |
| **P1** | FIX-02 | LSE cross-import 基线 JSON 仍为 7，实测 ≥8；文档写「7 边 ✅」 | `docs/acceptance-records/lse-cross-import-baseline.json` · `8359c96` scoring adapters · `test_arch_opt_gates.py` 期望 `edges: 8` | **阻断**：周度 job / 单测与文档三方不一致 |
| **P1** | FIX-03 | PR CI 不跑 `lint_lse_cross_import.py` | `.github/workflows/ci.yml` vs `arch-opt-weekly.yml` | 合并窗口内不可见边数回归 |
| **P1** | FIX-04 | `arch_equivalence_check` 在 PR 上 `continue-on-error: true` | `ci.yml` validate job | 等价性回归可静默进主干 |
| **P2** | FIX-05 | Windows 跨进程 CAS 测试偶发失败；无文件锁 | `test_trip_cross_process_update.py` · M-A1c 遗留 | 非 Linux CI 必红，但合并信心不足 |
| **P2** | FIX-06 | `ARCH-OPT-STATUS.md`「可开 PR 合并」表述过时 | 状态表「下一步」 | 文档误导 |

---

## 1. 背景与审查证据

### 1.1 审查快照（2026-07-09）

| 维度 | 数据 |
|------|------|
| 分支 | `arch/optimization-ws1` |
| 相对 `master` | ~892 files · +42k / -27k |
| HEAD（审查时） | `1544b21` |
| import-linter | ✅ 0 豁免 |
| `lint_trip_save_calls` / `lint_test_layout` / `lint_trip_pipeline_mutations` | ✅ |
| `arch_equivalence_check` | ✅（自反性） |
| `tsc:preview-toolbar`（HEAD） | ✅ |
| `lint_lse_cross_import --max-edges 7` | ❌（实测 8） |
| PR fast pytest（忽略 broken collect 文件） | **2147 passed · 56 failed** |
| Trip 核心套件 | 18 passed / 偶发 17+1（跨进程） |

### 1.2 FIX-01 根因（P0）

`scripts/migrate_lse_batch4plus.py` 以 `\ndef record_g1_edit` 为切分点：

- **切分前半** → `layout_contract/feedback.py`（类型、距离、分类、权重）
- **切分后半** → 留在 `curation/feedback.py`（含 `record_g1_edit` + `_chapter_*` helpers）

但消费方已改为：

```python
# travelogue/layout_engine/studio_feedback.py
from travelogue.layout_contract.feedback import record_g1_edit
```

HEAD 上 `layout_contract.feedback` **不导出** `record_g1_edit` → ImportError。

工作区 WIP 已部分修复（函数迁入 kernel + curation 改为 re-export），**尚未 commit**，且可能与 LONGSHOT WIP 混杂。

**受影响测试**：

| 测试 | 现象 |
|------|------|
| `tests/integration/p17/test_p17_studio_feedback.py` | 收集阶段 ImportError（阻断整树 collect） |
| `tests/unit/web/test_feedback.py` | 经 `curation.feedback` 导入时，若 helpers 未在 kernel 且 star-import 不完整 → NameError |

### 1.3 FIX-02 根因（P1）

| 来源 | 边数口径 |
|------|----------|
| batch-6 提交基线 JSON | **7**（仅 curation→layout_engine 白名单） |
| `8359c96` scoring adapters hotfix | 新增 `layout_engine.scoring.* → curation.*` |
| `tests/unit/scripts/test_arch_opt_gates.py` | 期望输出含 **`edges: 8`** |
| `ARCH-OPT-STATUS.md` / ADR-015 叙述 | 仍写 **7** / PRD ≤10 |

`lint_lse_cross_import.py` 默认 ceiling = baseline JSON 的 `totalCrossEdges`。若 JSON 未刷新而代码已 8 边 → 周度 job 红；若只改测试不改 JSON → 文档与门禁分裂。

### 1.4 FIX-03 / FIX-04 CI 盲区

```
PR lint job:     ruff · trip lints · lint-imports · tsc
PR test-pr:      pytest --fast 等价 marker
PR validate:     fixtures · arch_equivalence (warn-only) · demo
Weekly:          lint_lse_cross_import   ← 唯一边数门禁
```

合并当日若未手动跑 weekly 脚本，**FIX-02 对 PR 不可见**。

---

## 2. 目标与成功标准

### 2.1 北极星

> **`arch/optimization-ws1` 可安全合并 `master`：收集不炸、分层门禁绿、文档与基线一致、PR CI 能拦住同类回归。**

### 2.2 成功标准（DoD）

| ID | 标准 | 验证命令 |
|----|------|----------|
| DoD-01 | `pytest tests/ --collect-only -q` 无 ERROR | 同上 |
| DoD-02 | `test_p17_studio_feedback` + `test_feedback` 全绿 | `pytest tests/integration/p17/test_p17_studio_feedback.py tests/unit/web/test_feedback.py -q` |
| DoD-03 | `lint_lse_cross_import.py` exit 0，且输出边数 = baseline JSON | `python scripts/lint_lse_cross_import.py` |
| DoD-04 | `test_lint_lse_cross_import_at_baseline` 绿 | `pytest tests/unit/scripts/test_arch_opt_gates.py -q` |
| DoD-05 | `lint-imports` 仍 0 豁免 | `python -m importlinter.cli lint-imports` |
| DoD-06 | PR CI lint job 含 cross-import 检查 | 审查 `ci.yml` diff |
| DoD-07 | `ARCH-OPT-STATUS.md` / ADR-015 边数口径与 baseline 一致 | 人工 diff |
| DoD-08 | 工作区无 LONGSHOT 未跟踪文件进入本 PR | `git status` 审查 |
| DoD-09 | `arch_equivalence_check` 本地绿 | `python scripts/arch_equivalence_check.py` |

### 2.3 可接受差异

本修复 **无用户可见 DIFF**。开发者可见：

| # | 差异 | 沟通 |
|---|------|------|
| DIFF-F01 | `curation.feedback` 变为纯 re-export（若尚未是） | 开发者；行为不变 |
| DIFF-F02 | baseline JSON 边数 7→8（或文档统一为 8） | 状态表 + ADR 附录 |
| DIFF-F03 | PR CI 新增一步 lint（约数秒） | 无用户影响 |

---

## 3. 设计决策

| # | 决策 | 说明 |
|---|------|------|
| **D-FIX-01** | **`record_g1_edit` 与 `_chapter_*` 归属 `layout_contract.feedback`** | kernel 完整；`curation.feedback` 仅 re-export；与 M-B4a 方向一致 |
| **D-FIX-02** | **接受 scoring adapter 反向边，刷新基线至实测值** | hotfix `8359c96` 为正确性优先；边数仍 ≤ ADR-015 的 ≤10；不在本 PRD 做物理下沉 |
| **D-FIX-03** | **PR CI 硬拦 cross-import ceiling** | `ci.yml` lint job 增加 `python scripts/lint_lse_cross_import.py`；失败阻断 PR |
| **D-FIX-04** | **等价性检查：PR 保持 warn，合并 checklist 强制本地/validate 绿** | 不在本 PRD 将 PR 改为硬拦（成本高）；在合并清单与状态表强制 |
| **D-FIX-05** | **跨进程测试：先标 `xfail`/`skip` 平台条件或提高稳定性，不落地文件锁** | 文件锁属 OUT-04；可选加固见 M-F3 |
| **D-FIX-06** | **修复 PR 与 LONGSHOT 严格分叉** | 本 PR 仅含 FIX-* 文件；LONGSHOT WIP `git stash` / 独立分支 |

---

## 4. 里程碑与工作项

### 4.0 总览

| 里程碑 | 优先级 | 预估 | 依赖 | 产出 |
|--------|--------|------|------|------|
| **M-F0** | P0 | 0.5h | — | 工作区隔离：stash/分叉 LONGSHOT WIP |
| **M-F1** | P0 | 2–4h | M-F0 | feedback kernel 完整迁移 + 测试绿 |
| **M-F2** | P1 | 1–2h | M-F0 | baseline / 文档 / 单测三方对齐 |
| **M-F3** | P1 | 1–2h | M-F2 | CI 补洞 + 合并清单 |
| **M-F4** | P2 | 1–3h | M-F1 | 跨进程测试稳定性（可选） |
| **M-F5** | P1 | 1h | M-F1～F3 | 状态表收口 + 合并 PR 描述 |

**合计**：约 **0.5–1.5 人日**（含可选 M-F4）。

---

### 4.1 M-F0 · 工作区隔离

**目标**：确保修复 diff 不含 LONGSHOT / 无关 WIP。

**步骤**：

1. 将未跟踪/未提交的 LONGSHOT 相关文件移出工作区（独立分支或 stash）。
2. 确认 `git status` 仅保留 FIX 相关路径（或干净后 cherry-pick 修复）。
3. 记录隔离证据到 PR 描述。

**验收**：

- [ ] `git status` 无 `platform_profiles` / `content_splitter` / `longshot-export-panel` 等 LONGSHOT 路径进入本 PR
- [ ] HEAD 可干净检出后单独应用 M-F1～F3

---

### 4.2 M-F1 · feedback kernel 完整迁移（P0）

**目标**：`layout_contract.feedback` 成为 G1 feedback 唯一实现；所有导入路径可解析。

**必迁符号**（自 `curation.feedback` HEAD 实现）：

| 符号 | 目标模块 |
|------|----------|
| `record_g1_edit` | `layout_contract.feedback` |
| `_chapter_asset_sets` | `layout_contract.feedback`（供距离/分类使用） |
| `_chapter_heroes` | 同上 |
| `_screen_patterns` | 同上 |

**`curation/feedback.py` 目标形态**：

```python
"""Compatibility re-export · feedback kernel lives in layout_contract."""
from travelogue.layout_contract.feedback import *  # noqa: F403
from travelogue.layout_contract.feedback import (  # noqa: F401
    _chapter_asset_sets,
    _chapter_heroes,
    _screen_patterns,
)
```

**约束**：

- 不改 `G1EditRecord` 字段语义与 `to_dict` 键名。
- 不改 `g1_edit_distance` / `classify_edit_type` / `edit_weight_for_record` / `filter_edits_for_training` 算法。
- `studio_feedback.py` 保持从 `layout_contract` 导入（无需改回 curation）。

**验收**：

- [ ] DoD-01、DoD-02
- [ ] `from travelogue.layout_contract.feedback import record_g1_edit` 成功
- [ ] `from travelogue.curation.feedback import record_g1_edit` 成功（shim）
- [ ] `lint-imports` 仍绿

**回滚**：还原 `layout_contract/feedback.py` 与 `curation/feedback.py`；或临时改 `studio_feedback` 改回 `curation.feedback`（不推荐，仅紧急）。

---

### 4.3 M-F2 · LSE cross-import 基线对齐（P1）

**目标**：单一事实来源 = `docs/acceptance-records/lse-cross-import-baseline.json`。

**步骤**：

1. 在 **干净 HEAD + M-F1 后** 运行：
   ```bash
   python scripts/lse_cross_import_stats.py
   python scripts/lint_lse_cross_import.py --update-baseline
   ```
   （仅当边数未上升时 `--update-baseline` 才允许；若上升须人工审查。）
2. 确认 `totalCrossEdges` 与 `test_arch_opt_gates.py` 期望一致（当前测试期望 **8**）。
3. 更新文档口径：

| 文档 | 修订 |
|------|------|
| `ARCH-OPT-STATUS.md` LSE 表 | 7 → 实测值；注明含 scoring adapter 反向边 |
| `adr/015` 验证计划 / 附录 | 补「post-hotfix 边数」一行 |
| 本 PRD §1.3 | 以最终 JSON 为准 |

**决策重申（D-FIX-02）**：

- **允许** `layout_engine.scoring.{aesthetic,hero} → curation.*` 作为 intentional adapter 边。
- **禁止** 新增第三类跨包边而不更新 baseline。
- 硬顶仍为 ADR-015：**≤ 10**。若实测 >10，本里程碑升级为「必须物理下沉 scoring」，另开子任务。

**验收**：

- [ ] DoD-03、DoD-04、DoD-07
- [ ] `python scripts/lint_lse_cross_import.py --max-edges 10` 绿
- [ ] baseline JSON 的 `edges` 列表与 `lse_cross_import_stats` 输出一致

**回滚**：还原 baseline JSON + 文档；测试期望同步回退。

---

### 4.4 M-F3 · CI 补洞与合并清单（P1）

#### 4.4.1 CI 变更

在 `.github/workflows/ci.yml` 的 **lint** job，于 `Import layer contract` 步骤之后增加：

```yaml
- name: LSE cross-import ceiling (ADR-015)
  run: python scripts/lint_lse_cross_import.py
```

**说明**：

- 失败即阻断 PR（与 weekly 同脚本）。
- 不替代 weekly；weekly 可保留 stats 刷新或报告。

#### 4.4.2 合并清单（写入 PR 模板或 PR body）

```markdown
## WS1 Merge Gate Checklist
- [ ] M-F1 feedback kernel 已合入本分支
- [ ] `pytest tests/ --collect-only -q` 无 ERROR
- [ ] `python scripts/lint_lse_cross_import.py` 绿
- [ ] `python -m importlinter.cli lint-imports` 绿
- [ ] `python scripts/arch_equivalence_check.py` 绿（本地或 validate job）
- [ ] `npm run tsc:preview-toolbar` 绿
- [ ] 无 LONGSHOT WIP 文件
- [ ] ARCH-OPT-STATUS 边数与 baseline 一致
```

#### 4.4.3 等价性策略（D-FIX-04）

- **本 PRD 不修改** PR 上 `continue-on-error: true`。
- 合并责任人必须在 checklist 勾选本地/validate 等价性绿灯。
- 可选跟进（非本 PRD DoD）：release 分支将等价性升为硬拦。

**验收**：

- [ ] DoD-06
- [ ] 空提交或故意改坏一边后，PR lint 能失败（可用本地脚本模拟）

---

### 4.5 M-F4 · 跨进程 CAS 测试稳定性（P2 · 可选）

**现象**：`test_subprocess_worker_and_main_both_persist` 在 Windows 上偶发 `worker_keys == 0`；同套件另一次可 18/18 通过。

**允许方案（择一）**：

| 方案 | 做法 | 适用 |
|------|------|------|
| A | `@pytest.mark.skipif(sys.platform == "nt", reason="spawn CAS flake")` | 最快；Linux CI 仍覆盖 |
| B | 延长运行窗口 / 提高 `max_retries` / worker 启动 barrier | 保留 Windows 覆盖 |
| C | 仅文档标注 flaky + issue 链接 | 最弱，不推荐单独使用 |

**禁止**：在本里程碑实现 `.trip.lock`（OUT-04）。

**验收**（若执行）：

- [ ] 连续 3 次本地 `pytest tests/integration/trip/test_trip_cross_process_update.py` 行为符合所选方案预期
- [ ] Linux CI integration job 仍覆盖跨进程语义（若 A，则依赖非 Windows runner）

---

### 4.6 M-F5 · 状态收口与合并 PR

**更新 `ARCH-OPT-STATUS.md`**：

1. 「发现问题」节写入 FIX-01～FIX-04 及处置状态。
2. 「下一步」改为：
   - WS1 合并修复 PRD（本文）M-F1～F3 done 后方可合并
   - 背景项保持：预存 fast 失败、CacheRegistry、LONGSHOT
3. LSE 边数表与 baseline 同步。

**合并 PR 要求**：

- Title 建议：`fix(arch): WS1 merge gate — feedback kernel + LSE baseline + CI ceiling`
- Body 嵌入 §4.4.2 checklist + 本 PRD 链接
- 仅含 M-F* 相关 commits；禁止 squash 进 LONGSHOT

**验收**：

- [ ] DoD-08、DoD-09
- [ ] 状态表不再写「WS1 已闭环；可开 PR 合并」而不提本修复闸门

---

## 5. 验收标准（AC）

| AC ID | 描述 | 优先级 | 对应里程碑 |
|-------|------|--------|------------|
| **AC-FIX-01** | `record_g1_edit` 可从 `layout_contract.feedback` 与 `curation.feedback` 导入；`persist_studio_layout_feedback` 可写 sidecar | P0 | M-F1 |
| **AC-FIX-02** | `pytest tests/ --collect-only` 无 ImportError/ERROR | P0 | M-F1 |
| **AC-FIX-03** | baseline JSON `totalCrossEdges` == `lint_lse_cross_import` 实测；单测期望一致；文档一致 | P1 | M-F2 |
| **AC-FIX-04** | `ci.yml` lint job 含 cross-import 步骤且失败阻断 | P1 | M-F3 |
| **AC-FIX-05** | `lint-imports` / `arch_equivalence_check` / `tsc:preview-toolbar` 在修复分支绿 | P1 | M-F5 |
| **AC-FIX-06** | 合并 PR 无 LONGSHOT 路径；状态表已更新闸门表述 | P1 | M-F0/F5 |
| **AC-FIX-07** | （可选）跨进程测试在目标平台稳定或显式 skip | P2 | M-F4 |

---

## 6. 测试计划

### 6.1 必跑（合并前）

```bash
# 收集
python -m pytest tests/ --collect-only -q

# P0 反馈
python -m pytest tests/integration/p17/test_p17_studio_feedback.py tests/unit/web/test_feedback.py -q

# 分层与 LSE
python -m importlinter.cli lint-imports
python scripts/lint_lse_cross_import.py
python -m pytest tests/unit/scripts/test_arch_opt_gates.py -q

# 保存收口与路由
python -m pytest tests/integration/trip/ tests/unit/web/test_studio_route_snapshot.py tests/unit/config/test_config_fail_loud.py -q

# 等价性 + 前端类型
python scripts/arch_equivalence_check.py
npm run tsc:preview-toolbar

# 既有 lint
python scripts/lint_trip_save_calls.py
python scripts/lint_test_layout.py
python scripts/lint_trip_pipeline_mutations.py
```

### 6.2 建议跑（增强信心）

```bash
python -m pytest tests/ -q -m "not e2e and not vision and not playwright_serial and not legacy_homepage" --tb=no
# 记录失败列表；与「预存失败」对照，确认无新增架构相关失败
```

### 6.3 回归对照表

| 失败模式 | 归属 | 本 PRD 是否必须清零 |
|----------|------|---------------------|
| `test_p17_studio_feedback` ImportError | FIX-01 | **是** |
| `test_feedback` NameError | FIX-01 | **是** |
| `test_lint_lse_cross_import_at_baseline` | FIX-02 | **是** |
| `test_trip_cross_process_update` flake | FIX-05 | 可选 |
| `test_asset_version` / `studio_home_v2` / `template_concurrent` 等 | 预存 | **否**（记入背景 issue） |

---

## 7. 风险与回滚

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| WIP 与 LONGSHOT 混提交 | 高 | 审查面爆炸 | M-F0 强制隔离 |
| baseline 刷新掩盖真实回归 | 中 | 边数静默上涨 | `--update-baseline` 仅允许下降或人工审查等值；硬顶 ≤10 |
| star-import 遗漏私有 helpers | 中 | NameError | 显式 re-export `_chapter_*`；跑 `test_feedback` |
| CI 新增步骤拖慢 lint | 低 | 数秒 | 可接受 |
| Windows flake 误判为 P0 | 中 | 延误合并 | M-F4 方案 A + Linux CI 为准 |

**整包回滚**：Revert 本修复 PR；WS1 大分支暂缓合并。不回滚已完成的 WS1 功能里程碑，除非出现数据损坏类问题（本 PRD 范围内预期不会）。

---

## 8. 排期与责任

| 角色 | 职责 |
|------|------|
| 开发 | M-F0～F3 实现；开合并 PR |
| 测试 | 执行 §6.1；签署 AC-FIX-01～06 |
| 架构 | 确认 D-FIX-02（接受 8 边 adapter）与 ADR-015 口径 |
| 产品 | 无用户可见变更；仅知会合入节奏 |

**建议顺序**：M-F0 → M-F1 → M-F2 → M-F3 → M-F5 →（可选 M-F4）→ 合并。

---

## 9. 开放问题

| # | 问题 | 默认裁定 | 需谁确认 |
|---|------|----------|----------|
| Q-F01 | scoring adapter 反向边长期保留还是下沉 `layout_contract`？ | **本 PRD 保留并计入 baseline**；下沉另开债 | 架构 |
| Q-F02 | PR 上 `arch_equivalence_check` 是否升硬拦？ | **否**；checklist 强制 | 测试/发布 |
| Q-F03 | Windows 跨进程测试 skip 是否可接受？ | **可**（方案 A） | 测试 |
| Q-F04 | 预存 56 个 fast 失败是否阻塞合并？ | **否**；另开 tracking issue | 测试负责人 |

---

## 10. 附录

### 10.1 关键文件清单（预期 touch）

```
travelogue/layout_contract/feedback.py
travelogue/curation/feedback.py
docs/acceptance-records/lse-cross-import-baseline.json
docs/ARCH-OPT-STATUS.md
docs/adr/015-lse-planner-migration.md          # 可选附录行
docs/PRD-ARCH-OPT-WS1-MERGE-FIX.md             # 本文
docs/README.md                                 # 索引
.github/workflows/ci.yml
tests/unit/scripts/test_arch_opt_gates.py      # 仅当期望需微调
tests/integration/trip/test_trip_cross_process_update.py  # 仅 M-F4
```

### 10.2 审查命令速查（复现缺陷）

```bash
# FIX-01
python -c "from travelogue.layout_contract.feedback import record_g1_edit"
python -m pytest tests/integration/p17/test_p17_studio_feedback.py --collect-only

# FIX-02
python scripts/lse_cross_import_stats.py
python scripts/lint_lse_cross_import.py --max-edges 7   # 预期失败（若仍为 8 边）
```

### 10.3 与母 PRD 的关系

| 母 PRD 里程碑 | 本修复关系 |
|---------------|------------|
| M-B4a / batch-4 feedback 切分 | **补完遗漏**（FIX-01） |
| M-D1 / batch-6 边数 ≤10 | **维持**；刷新基线（FIX-02） |
| M-B0 CI 门禁 | **加强** cross-import 进 PR（FIX-03） |
| M-A1c 文件锁跳过 | **不重开**；可选测试稳定（FIX-05） |

### 10.4 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-07-09 | 初稿：基于合并前代码质量审查 |
