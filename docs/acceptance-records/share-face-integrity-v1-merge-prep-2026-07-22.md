# SFI · 合入准备 · 2026-07-22

| 属性 | 内容 |
|------|------|
| **分支** | `feat/share-face-integrity-w0` |
| **基线** | `origin/master` @ `b483105`（含 CSC #16） |
| **动作** | merge master → SFI；解冲突；修 CSC facade；抬高 curate 棘轮 |
| **状态** | **工程合入准备就绪** · AC-12 产品盲评席位仍未签 |

---

## 1. 已完成

| 项 | 结果 |
|----|------|
| merge `origin/master` | Done · 冲突仅 CSC 文档 + README |
| 冲突决议 | CSC 文档取 master；README 保留 FTT/SFI + CSC 现行索引 |
| facade | `web/rerender.py` 深 import → `layout_engine.api`（lint = 0） |
| god-module | `curate.py` **1830→1940**（SFI 增量；`--allow-growth` 更新 baseline） |
| 烟测单测 | `sfi` / Recipe / public_api 相关 **45 passed** |

## 2. 仍开放（产品）

| 项 | 状态 |
|----|------|
| AC-SFI-12 盲评 N≥3/5 | **未签** · 见 [ac12-blind](./share-face-integrity-v1-ac12-blind-2026-07-21.md)（脚本半门已过：11.3%→3.0%） |
| 工程自测产品勾选 | 见 [eng-smoke](./share-face-integrity-v1-eng-smoke-2026-07-21.md) |

> 若产品接受「脚本半门 + 工程自测」先合、盲评后补签：可在 PR 注明 waiver。否则等 AC-12 席位填完再 merge。

## 3. 建议合并命令（CI 不可用时）

```powershell
# PR 开好后
gh pr merge <N> --merge
```

本地核对：

```powershell
python scripts/lint_layout_engine_facade.py
python scripts/lint_csc_god_module_ratchet.py
python scripts/lint_csc_debt_table.py
python scripts/lint_csc_recipe_baseline.py
python -m pytest tests/unit -q -k "sfi or happy_path or public_api" --maxfail=10
```
