# 架构治理 V2 · 实施准备清单（稳定优先切片）

| 属性 | 内容 |
|------|------|
| **状态** | **active · 实施前准备**（尚未开工写码） |
| **PRD** | [PRD-ARCH-OPTIMIZATION-V2.md](./PRD-ARCH-OPTIMIZATION-V2.md) **v2.1.0** |
| **评审** | [ARCH-OPT-REVIEW-V2-2026-08-11.md](./ARCH-OPT-REVIEW-V2-2026-08-11.md) |
| **目标切片** | **维持稳定可靠**：只做 **M2-A 全量 + M2-B1**；M2-B2/B3、M2-C 全部 Parking Lot（机会主义，本清单不排期） |
| **负责人视角** | 落地负责人建议书（开工前决策 + PR 切分 + 验收命令 + 冻结规则） |
| **日期** | 2026-08-11 |

---

## 0. 执行裁决（给产品/作者确认）

| # | 裁决 | 建议默认 | 需要你拍板？ |
|---|------|----------|--------------|
| E-01 | 本波范围是否只做 M2-A + M2-B1 | **是**。其余 PRD 章节保留为 backlog，不进本波 PR | 建议确认 |
| E-02 | M2-A 期间是否暂停触及 `curation`/`layout_engine`/`services` 分层边界的功能 PR | **是**（对齐 PRD §3 执行约束）。本地未提交的功能改动先 stash/另开分支 | 建议确认 |
| E-03 | A2b（18 个 layout_engine 失败）遇到「EGA 预期副作用 vs 真回归」不确定时 | **默认按真回归处理**，不得批量 bump golden；需算法侧口头/文档确认后才允许 `GOLDEN-BUMP-JUSTIFICATION:` | 建议确认（算法角色） |
| E-04 | A3「直接 push master」是否整改分支保护 | **本波不做**。记为既定 hobbyist 工作方式；仅在验收记录里写明 | 可不拍板，按此执行 |
| E-05 | A4 `curate.py` +12 行优先裁剪还是刷新基线 | **优先看 diff 是否可裁**；不可裁则走正规 `--update-baseline --allow-growth` 并写清增量来源（禁止手改 JSON） | 可不拍板，按此执行 |
| E-06 | 开工前是否先处理 `preview-toolbar` 工作区脏文件 | **是**。当前 `chapter-panel.js`、`dock.css` 有未提交修改，会干扰 A5 | **需要你处理或授权我 stash/另分支隔离** |

---

## 1. 开工前现状快照（2026-08-11 复测）

| 门禁 | 状态 | 说明 |
|------|------|------|
| import-linter | **红** | `chapter_titles → narrative_validate` L159/L316 |
| `pytest --fast` | **红** | 上次全量 41 failed / 4247 passed（实施 Day0 须重跑基线） |
| god-module ratchet | **红** | `curate.py` 1986 > 1974 |
| `tsc:preview-toolbar` | **红** | 14 errors / exit 2 |
| LSE cross-import | **绿（贴顶）** | 13 / ceiling 13（防篡改尚未落地） |
| 引入提交 `62f744d9` | 直接 push | 单 parent，非 merge；A3 可记「既定方式」无需改保护 |

**工作区风险**：`templates/studio/preview-toolbar/chapter-panel.js`、`dock.css` 已有本地修改 → A5 前必须隔离。

---

## 2. 本波不做（Parking Lot）

明确冻结，避免范围蠕变：

- M2-B2 文档自动化、M2-B3 flag 台账
- M2-C1 god-module 扩容拆分、M2-C2 前端扩面、M2-C3 `.trip.lock` 审计/仓库卫生
- 任何 intentional 功能改动、config 默认值翻转、分支保护强制化

---

## 3. PR 切分（建议 5 个小 PR，可独立回滚）

原则：**一 PR 一类红灯 / 一类机制**；先恢复信号可信，再加防篡改。

| 顺序 | PR 代号 | 内容 | 预估 | 合并门槛（本地必跑） | 回滚 |
|------|---------|------|------|----------------------|------|
| 1 | **PR-A1** | M2-A1：`domain/place_names.py` 下沉 + re-export + `chapter_titles` 改引用；补 2～3 个直接单测 | 0.5d | `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` → 0 broken；`pytest tests/unit/scripts/test_arch_opt_gates.py tests/unit/validate/test_narrative_validate.py tests/unit/curation/test_chapter_titles_pmx.py -q` | revert PR |
| 2 | **PR-A4+A5** | M2-A4 god-module 超限处置 + M2-A5 tsc 14 处（可同 PR 若都小；否则拆） | 0.5～1d | `python scripts/lint_csc_god_module_ratchet.py`；`npm run tsc:preview-toolbar` | revert；基线刷新须留 PR 说明 |
| 3 | **PR-A2a** | 仅修 `tests/conftest.py` marker 顺序 | 0.25d | `pytest --fast --collect-only -q tests/integration/p17` → 0 collected；另加一条 regression 单测防再早退 | revert |
| 4 | **PR-A2b+…** | A2b～A2e：清红 41 failed（**最大风险 PR**） | 1.5～2d | `pytest --fast -q` → 0 failed；凡改 golden 必须含 `GOLDEN-BUMP-JUSTIFICATION:` + EGA/其它 PRD 条款引用 | 按文件粒度 revert；禁止与功能 PR 混提 |
| 5 | **PR-B1** | M2-B1：先 4 条零风险降边（13→9）→ 基线防篡改校验 → `--allow-growth --tracking-issue --due-date` + growth-log + 单测 | 2～3d | `python scripts/lint_lse_cross_import.py`；手改 baseline JSON 的负例 CI/单测失败；正规路径可更新 | revert；降边与防篡改可再拆成 B1a/B1b |

**A3**：不单独开功能 PR，在 **PR-A1 或收工记录** 中写 5 行核实结论即可。

---

## 4. Day-0 检查清单（写码前打勾）

- [ ] 确认 E-01～E-06 裁决（尤其 E-06 脏文件）
- [ ] 从干净 HEAD 开分支：`arch/opt-v2-m2a`（勿在脏 preview-toolbar 上直接改）
- [ ] 重跑并贴结果到分支 README/PR 草稿：  
  - import-linter（正确命令，见上）  
  - `python scripts/lint_csc_god_module_ratchet.py`  
  - `npm run tsc:preview-toolbar`  
  - `pytest --fast -q`（全量，约 20min；作为 A2 基线）
- [ ] 准备 A2b 对照材料打开在侧：  
  - `docs/PRD-EQUAL-GRID-ADMISSION-V1.md`  
  - `docs/acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md`
- [ ] 约定验证命令白名单（避免假阳性）：  
  - ✅ `lint-imports`（需 `pip install -e ".[dev]"`）或 `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"`  
  - ❌ `python -m importlinter.cli lint-imports`（失效）

---

## 5. A2b 操作纪律（稳定优先的核心护栏）

对每个失败用例只允许三条出路之一，并在 PR 描述用表格登记：

| 分类 | 条件 | 允许动作 |
|------|------|----------|
| **误收集** | A2a 修完后消失 | 不改产品代码 |
| **EGA 预期副作用** | 对照 EGA 评审纪要可引用具体条款，且 revert 候选 commit 可复现「改前绿/改后红」 | 改断言/golden + `GOLDEN-BUMP-JUSTIFICATION:` |
| **真回归 / 不确定** | 无法定位到单一意图变更，或与 EGA 条款不符 | **修产品/测试逻辑，禁止先 bump**；不确定则停下来问算法 |

禁止：18 个失败「一把梭」重签基线。

---

## 6. M2-B1 落地骨架（A 全绿后再做）

建议实现顺序（不可颠倒）：

1. **B1a 降边**：`ltn_isolation.py` / `ltn_weekly.py` 改指 `layout_contract.burst` / `layout_contract.orientations` → 跑 `lint_lse_cross_import.py` 期望 ~9 → 正规 `--update-baseline`（下降允许）刷新基线。  
2. **B1b 防篡改**：CI/脚本「重算 edges ≡ committed baseline」；手改 JSON 必失败。  
3. **B1c 增长路径**：为 LSE 脚本**新增**（非改造已有）`--allow-growth --tracking-issue --due-date` + growth-log；`tracking_issue` 仅接受仓库内可 grep 锚点（建议 `docs/ARCH-OPT-P2-BACKLOG.md`）。  
4. **B1d 单测**：对齐 `tests/unit/scripts/test_arch_opt_gates.py` 正反例。

本波 **不做** growth-log 的复杂到期日运营流程以外的 B2/B3。

---

## 7. 风险与止损

| 风险 | 止损 |
|------|------|
| A2b 误伤排版语义 | 任何 golden bump 可单独 revert；不确定即停 |
| A5 与本地 preview-toolbar 脏改冲突 | 开工前隔离；A5 只做类型修复，不夹带 UX |
| B1 降边「以为零风险」实际行为差 | 降边 PR 仅改 import 路径；跑既有 mosaic/ltn 相关单测；行为 diff 则立刻回退 |
| 范围蠕变到 M2-C | 本清单 E-01；新 PR 描述必须写「本波切片：M2-A/B1」 |
| 门禁假绿 | 只用 §4 白名单命令验收 |

---

## 8. 落地负责人建议（结论）

1. **先确认 E-06**：处理或授权隔离 `preview-toolbar` 脏文件，否则不要开 A5。  
2. **按 §3 顺序开工**：A1 → A4/A5 → A2a → A2b（最重）→ B1；不要并行开结构重构。  
3. **把「稳定」定义为「四门禁 + pytest --fast 全绿」**，而不是「功能感觉正常」——本波唯一成功标准即此。  
4. **A2b 是唯一高风险项**：预留算法确认窗口；若你暂时无法确认 EGA 条款，可先合 A1/A2a/A4/A5，**A2b 单独挂起**，也不要为了赶绿强行 bump。  
5. **B1 价值在防回潮**：A 做完后一周内做完 B1，否则本月「止血→回潮」模式大概率再演一次。  
6. **不建议**本波引入分支保护或 flag 台账——与 hobbyist 节奏不匹配，收益低于干扰成本。

---

## 9. 下一步（等你一句）

请回复以下之一即可开工：

- **「按准备清单开工」** → 我按 PR-A1 起分支实施  
- **「先处理脏文件再开工」** → 我只协助隔离/整理 preview-toolbar 未提交改动  
- **「A2b 暂缓，先做 A1/A4/A5/A2a」** → 采用更保守切片  
- 或修正 E-01～E-06 任一默认裁决
