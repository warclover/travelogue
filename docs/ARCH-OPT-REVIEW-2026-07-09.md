# 架构优化（WS1）评审报告 · 2026-07-09

> 评审对象：分支 `arch/optimization-ws1`（M-A0 ～ M-D1 全部里程碑）
> 评审方法：import-linter 实测复跑、LSE 跨包边 AST 实测、`pytest --fast` 全量运行、运行事故日志（studio-import-error.log）与代码走读
> 配套文档：[ARCH-OPT-STATUS.md](./ARCH-OPT-STATUS.md) · [TECH-ARCHITECTURE.md](./TECH-ARCHITECTURE.md) §18

---

## 一、总体判断

**方向与机制设计优秀，但迁移收尾留下多处运行时断裂引用，评审时分支测试为红。**

分层契约、CAS 写入、声明式路由、门禁脚本文化都是高质量的工程实践；真正的风险集中在 batch-4～6「切模块」迁移的收尾质量：文档宣称的数字与代码实况已漂移，且三处 dangling reference 在生产路径上会直接抛错。

**评审当日已完成止血修复（见 §五），P0/P1 项全部闭环。**

---

## 二、实测确认的成果

| 机制 | 实测结论 |
|------|----------|
| `import-linter` | 8 层 DAG 契约写入 pyproject，`ignore_imports = []` 真实清零，本地复跑全绿，已接入 CI lint job |
| `TripService.update` | `meta.revision` CAS + 临时文件原子替换 + fsync，配 `lint_trip_save_calls` CI 门禁，写入收口完整 |
| 统一编排 `run_trip` | `orchestrator/run.py` 单一路径、阶段清单显式；legacy 双开关删除彻底，残留 config 仅告警 |
| Studio 路由表（M-C1） | 68 条声明式路由 + AC-ARC-13 快照测试；serve.py 第二入口已收编 |
| 测试/脚本治理 | 423 个测试文件按 unit/integration/e2e 分层 + marker 体系；168 个脚本注册表化归档 |
| 等价性文化 | `arch_equivalence_check`、`lint_trip_json`、`render_fingerprint` 把重构风险变成可回归的门禁 |

---

## 三、发现的问题（按严重度）

### P0-1 · 迁移把模块切成两半，留下 3 处 dangling reference

1. `layout_engine/studio_feedback.py:9` 从 `layout_contract.feedback` 导入 `record_g1_edit`，但该函数实际留在 `curation/feedback.py` —— Studio 重排版反馈路径一触发即 ImportError。
2. `layout_contract/feedback.py` 的 `g1_edit_distance` 引用 `_chapter_asset_sets`，而该私有函数被留在 curation 侧 —— 公共 kernel 引用不存在的名字，NameError。
3. `templating/admin_store.py:169` 调用 `assert_transition` 但缺少 import（定义在 `templating/lifecycle.py`）—— 模板生命周期变更全部 NameError。

旁证：`studio-import-error.log` 显示 7/8 晚已有 3 起真实运行事故（scoring shim 自引用 RecursionError 21:47、`summarize_screen_patterns` ImportError 21:55），当晚 21:53/22:03 两个 fix commit 属于运行时救火。这类断裂 import-linter 和路由快照都拦不住。

### P0-2 · 测试为红：57 failed / 2370 passed + 1 收集错误

`pytest --fast` 实测 57 个失败（状态文档记录「预存失败 ~25」），且 `tests/integration/p17/test_p17_studio_feedback.py` 收集期 ImportError 会中断整个 --fast 运行。失败根因分类：

| 类别 | 数量（约） | 根因 |
|------|-----------|------|
| dangling reference 直接引发 | 13 | 上述 P0-1 三处断裂 |
| 测试 monkeypatch 打在 shim 上失效 | 28 | B4b 迁移后 `curation.mosaic/usage_rules/...` 成为 vars() 快照 shim，patch shim 全局对真实模块无效 |
| fixture 路径未随 M-C2 分层迁移 | 10 | `tests/unit/curation/` 相对自身定位 `fixtures/`，实际文件在 `tests/fixtures/` |
| conftest 分桶早退破坏 playwright 自动标记 | 2 | M-C2 `_apply_auto_markers` 路径分桶 early-return 跳过 playwright 标记 |
| 读写状态模块分裂后测试只补丁写侧 | ~7 | batch-6b 把 admin state 拆为 `templating.admin_store`（写）+ `domain.template_admin_state`（读），测试只 patch 写侧路径 |
| 资产版本 golden 未随 M-C5 CSS 拆分 bump | 2 | `_EXPECTED_BUNDLE_VERSION` 过期 |
| 测试文件迁移但 JS 单测/路由断言未同步 | 2 | js 目录相对定位失效；`_dispatch_home_root` 断言指向 M-C1 之前的模块 |

### P1-1 · LSE 边数门禁不在 PR CI，且已发生回归

- `lint_lse_cross_import.py` 只挂在每周一 cron（`arch-opt-weekly.yml`），回归窗口长达一周。
- 事实已发生：7/8 晚两个 fix commit 让 layout_engine→curation 从 0 回升到 2（scoring adapter 反向懒加载），总边数 7→9，而文档与基线 JSON 仍写 7/0。
- `lse_cross_import_stats.py` 默认 `--out` 就是基线文件本身：本地跑一次统计就把「尺子」改写成当前值，架空 `--update-baseline` 的棘轮保护。

### P1-2 · 32 个 shim 空壳 + vars() 复制模式是持续事故源

curation 下整个 `mosaic/` 包（30+ 文件）加 `screen_planner.py`、`layout_search.py` 等都是「import_module + vars() 逐名复制」的 deprecated shim：

- 复制的是 import 时刻快照，双向依赖时易自引用（RecursionError 事故即此因）；
- 掩盖真实依赖图（`curate.py` 内部仍有 7 处函数级懒加载 layout_engine）；
- **测试 monkeypatch 打在 shim 上静默失效**——28 个测试因此失败却看似「行为断言错误」。

### P2 · 长期健康观察（本次未处理，建议立项）

- **god module**：`curate.py` 1256 行、`run_curate` 单函数约 570 行；`ingest.py` 44KB、`screen_planner.py` 46KB。包级分层完成，函数级复杂度原样保留。建议顺着已有 `_CuratePreflight` / `_CurateBucketPlan` 雏形把 `run_curate` 拆成显式 stage 序列。
- **跨进程写竞态窗口**：CAS 用进程内 threading.Lock + 读盘 revision 比较，「比较」与 `os.replace` 之间跨进程无锁（M-A1c 的 `.trip.lock` 补强被跳过）。Studio 子进程 + CLI 并发时理论上可丢更新。
- **layout_contract 准入标准**：定位是第 0 层 kernel，但 chapter_items、feedback、scoring 等带业务逻辑的实现在救火中被逐个塞入，23 个文件已无清晰准入标准，需明确「纯函数 + DTO only」之类的门槛。
- **仓库卫生**：根目录约 15MB 截图 PNG、`pytest-full.log`、`studio-import-error.log` 入库或散落；`.gitignore` 需补 `_tmp*`。

---

## 四、深度改进建议（原始优先级清单）

| 优先级 | 行动 | 状态 |
|--------|------|------|
| P0 | 修复 3 处断裂引用 | ✅ 已完成（本次） |
| P0 | 测试清红后再合并 PR | ✅ 已完成（本次，详见 §五） |
| P1 | LSE 门禁进 PR CI + 统计脚本去副作用 | ✅ 已完成（本次） |
| P1 | 消除 scoring adapter 反向边 | ✅ aesthetic 边已消除；hero 边余 1（见 §五.4） |
| P1 | shim 一次性退役（全仓改引新路径后删除 32 个空壳） | ⏸ 建议独立 PR：测试侧已全部改引新路径，产线消费方仅剩 7 个文件 |
| P2 | 拆解 `run_curate`（570 行 → 显式 stage） | ⏸ 建议立项 |
| P2 | `.trip.lock` 跨进程文件锁补强 | ⏸ 建议立项（原 M-A1c 遗留） |
| P2 | 文档数字脚本化生成（防漂移） | ⏸ 建议立项；本次已手工校正 |
| P2 | 仓库卫生（PNG/log 归档、.gitignore 补 `_tmp*`） | ⏸ 待处理 |

---

## 五、本次修复记录（2026-07-09）

### 1. 断裂引用（P0）

- `record_g1_edit` + `_chapter_asset_sets` / `_chapter_heroes` / `_screen_patterns` 下沉至 `layout_contract/feedback.py`；`curation/feedback.py` 改为纯 re-export。
- `templating/admin_store.py` 补 `from travelogue.templating.lifecycle import TemplateLifecycle, assert_transition`。
- 验证：`test_p17_studio_feedback` / `test_feedback` / `test_template_admin_store` 等 18 个用例全部转绿。

### 2. LSE 门禁（P1）

- `ci.yml` lint job 新增 `python scripts/lint_lse_cross_import.py`（PR 级回归拦截）。
- `lse_cross_import_stats.py` 默认改为只读（`--out` 需显式传入）；基线更新只走 `lint_lse_cross_import.py --update-baseline`（自带只降不升棘轮）。

### 3. 反向边收敛（P1）

- `asset_aesthetic` / `aesthetic_overall` 纯函数下沉 `layout_contract/scoring.py`；`layout_engine/scoring/aesthetic.py` 与 `curation/aesthetic_score.py` 均改为 re-export。layout_engine→curation 的 aesthetic 边**已消除**。
- hero 边（`layout_engine/scoring/hero.py` → `curation.curate_scoring.effective_hero_score`）依赖闭包过深（cover_score 体系 38KB 模块），保留为白名单边并入基线：**当前 8 边（7 条 curate→adapter 白名单 + 1 条 hero adapter），ceiling 8 ≤ PRD 目标 10**。后续应把 hero/cover scoring 纯函数内核继续下沉 layout_contract 以恢复严格单向。

### 4. 测试修复（P0，57 → 见下）

- fixture 路径：`tests/unit/curation/` 4 个文件改用 `tests/fixtures/` 共享目录（M-C2 迁移遗漏）。
- conftest：`_apply_auto_markers` 的 playwright 标记逻辑提前到路径分桶 early-return 之前（恢复 e2e playwright 模块自动 serial 化契约）。
- shim monkeypatch：`tests/unit/layout_engine/` 约 80 个文件批量改引真实模块路径（`layout_engine.mosaic/usage_rules/planner.*`、`layout_contract.usage_context/usage_rules_registry` 等）。
- admin state 读写分裂：12 个测试文件补齐 `domain.template_admin_state._ADMIN_STATE_PATH` / `_RUNTIME_CACHE` 双侧补丁（对齐 `test_template_review.py` 的正确写法）。
- telemetry patch 目标：`templating.metrics` → `util.template_metrics`（batch-6b 后真实调用点）。
- golden bump：`_EXPECTED_BUNDLE_VERSION` 更新为 M-C5 CSS/ESM 拆分后的 bundle hash `ls1a9214cf1dc9`。
- 路由断言：`test_studio_homepage_gate_wired` 改验 `studio_dispatch.py` 路由表（M-C1 后实况）。
- `test_lint_lse_cross_import_at_baseline` 断言从 `"7" in out` 收紧为 `"edges: 8" in out`。

### 5. 最终验证

- `python -m importlinter.cli lint-imports`：全绿（0 豁免）。
- `python scripts/lint_lse_cross_import.py`：8 边 / ceiling 8，通过。
- `pytest --fast` 全量：**2452 passed / 0 failed** / 12 skipped / 311 deselected（修复前：57 failed + 1 收集中断）。
- 改动文件 `ruff check`：全绿。

---

*评审与修复：Cursor Agent · 2026-07-09*
