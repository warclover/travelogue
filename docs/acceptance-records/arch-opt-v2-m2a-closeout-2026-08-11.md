# Arch Opt V2 · 稳定切片收工记录（M2-A + M2-B1）

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | active |
| **日期** | 2026-08-11 |
| **PRD** | [PRD-ARCH-OPTIMIZATION-V2.md](../PRD-ARCH-OPTIMIZATION-V2.md) v2.1.0 |
| **实施清单** | [IMPLEMENTATION-ARCH-OPTIMIZATION-V2.md](../IMPLEMENTATION-ARCH-OPTIMIZATION-V2.md) |
| **合入** | [#62](https://github.com/warclover/travelogue/pull/62) → `master` @ `a58febad` |
| **切片** | **仅 M2-A 全量 + M2-B1**；M2-B2/B3、M2-C 仍 Parking Lot |

---

## 1. M2-A3 · 合入路径核实结论（ARC2-04）

1. **`62f744d9` 不是 merge commit**：`git cat-file` / `git log` 显示单一 parent、作者直推 `master`，无对应 PR merge。
2. **CI 对此类 push 是事后可见性，不是合并前阻断**：`.github/workflows/ci.yml` 头部声明 hobbyist-friendly budget；`push` 到 master 会跑 lint，但不构成「必须绿才能落地」的分支保护。
3. **定性**：符合项目既定个人开发工作方式，**不是意外绕过漏洞**；本波**不**引入强制 branch protection。
4. **处置**：分层违例本身已由 M2-A1 修复；后续依赖门禁脚本 +（本收工补上的）growth-log CI 步骤防回潮，而非改 GitHub 保护规则。
5. **无法在仓库内核实的项**：GitHub 后台「当时 Actions 是否失败却被忽略」属人工后台项；与上列 1–3 结论不冲突，记「无需再查」。

---

## 2. 本波完成对照

| 项 | 结果 |
|----|------|
| A1 place_names 下沉 | Done · import-linter 3 kept |
| A2a `--fast` marker 顺序 | Done · p17 不再误收集 |
| A2b～A2e 清红 | Done · `pytest --fast` **4071 passed / 0 failed** |
| A4 god-module / A5 tsc | Done |
| B1a 降边 | Done · LSE **13 → 9**（`layoutEngineToCuration` 6 → 2） |
| B1b/c/d 防篡改 + growth 路径 + 单测 | Done · 脚本与 `test_arch_opt_gates` 正反例 |

**本收工补丁（相对 #62）**：

- CI / weekly workflow 接入 `python scripts/lint_ratchet_growth_log.py`（AC2-05 闭环）
- 本文件落档 A3
- 实施清单状态改为 Done

---

## 3. 本地验收命令（白名单）

```text
python -c "from importlinter.cli import lint_imports_command; raise SystemExit(lint_imports_command())"
python scripts/lint_csc_god_module_ratchet.py
python scripts/lint_lse_cross_import.py
python scripts/lint_ratchet_growth_log.py
npm run tsc:preview-toolbar
pytest --fast -q
```

勿用：`python -m importlinter.cli lint-imports`（假绿）。

---

## 4. Parking Lot（明确不做）

M2-B2 文档自动化 · M2-B3 flag 台账 · M2-C1/C2/C3（god-module 扩容、前端扩面、trip.lock/仓库卫生）。
