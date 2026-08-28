# 架构治理 V2 · 实施清单（稳定优先切片）

| 属性 | 内容 |
|------|------|
| **状态** | **Done**（M2-A 全量 + M2-B1 已合入；本文件为收工态） |
| **DOC-STATUS** | active |
| **PRD** | [PRD-ARCH-OPTIMIZATION-V2.md](./PRD-ARCH-OPTIMIZATION-V2.md) **v2.1.0** |
| **评审** | [ARCH-OPT-REVIEW-V2-2026-08-11.md](./ARCH-OPT-REVIEW-V2-2026-08-11.md) |
| **目标切片** | **维持稳定可靠**：只做 **M2-A 全量 + M2-B1**；M2-B2/B3、M2-C 全部 Parking Lot |
| **合入** | [#62](https://github.com/warclover/travelogue/pull/62) · merge `a58febad`（2026-08-11） |
| **收工记录** | [acceptance-records/arch-opt-v2-m2a-closeout-2026-08-11.md](./acceptance-records/arch-opt-v2-m2a-closeout-2026-08-11.md) |
| **日期** | 2026-08-11 |

---

## 0. 执行裁决（已确认）

| # | 裁决 | 落地 |
|---|------|------|
| E-01 | 只做 M2-A + M2-B1 | ✅ |
| E-02 | M2-A 期间暂停分层边界功能 PR | ✅（本波遵守） |
| E-03 | A2b 不确定默认按真回归 | ✅（含 L6 相邻 dense 真修） |
| E-04 | A3 不改分支保护 | ✅ 见收工记录 §1 |
| E-05 | A4 正规 `--update-baseline --allow-growth` | ✅ |
| E-06 | A5 前隔离 preview-toolbar 脏文件 | ✅ |

---

## 1. 合入后门禁快照（2026-08-11）

| 门禁 | 状态 |
|------|------|
| import-linter | **绿** · 3 kept |
| `pytest --fast` | **绿** · 4071 passed / 0 failed |
| god-module ratchet | **绿** · 合入快照 curate 1986 / studio_pipeline 1181 · **2026-08-28 只降至 1646 / 1144**（[结案](./acceptance-records/trip-persist-lost-update-closeout-2026-08-28.md)） |
| `tsc:preview-toolbar` | **绿** |
| LSE cross-import | **绿** · 9 / ceiling 9 |
| LSE growth-log 防篡改 | **绿** · 脚本 + CI 步骤（closeout 补上） |

---

## 2. Parking Lot（仍冻结，机会主义）

- M2-B2 文档自动化、M2-B3 flag 台账  
- M2-C1 god-module 扩容拆分、M2-C2 前端扩面、M2-C3 `.trip.lock` / 仓库卫生  
- 分支保护强制化  

开发期可随时从 Parking Lot 抽一项开新分支；**不**与本 Done 切片混提。

---

## 3. 已交付 PR 序列（历史）

| 顺序 | 内容 | tip / 说明 |
|------|------|------------|
| A1 | `domain/place_names` 下沉 | `b1c48c5f` |
| A4+A5 | god-module + tsc | `b524c78f` |
| A2a | conftest `--fast` 顺序 | `050a575d` |
| A2b～A2e | 清红 + EGA/SNR/NAS | `cd1e9e08` + LVP 跟进 |
| B1a | LSE 13→9 降边 | `942bb3ec` |
| B1b/c/d | 防篡改 + growth-log | `c1d823b4` |
| Closeout | A3 留档 + CI 挂 growth-log | 本分支 |

---

## 4. 验收命令白名单

```text
python -c "from importlinter.cli import lint_imports_command; raise SystemExit(lint_imports_command())"
python scripts/lint_csc_god_module_ratchet.py
python scripts/lint_lse_cross_import.py
python scripts/lint_ratchet_growth_log.py
npm run tsc:preview-toolbar
pytest --fast -q
```

❌ `python -m importlinter.cli lint-imports`（失效假绿）

---

## 5. 历史准备材料

开工前快照、A2b 纪律、B1 骨架原文见 git 历史；以本 Done 页 + [收工记录](./acceptance-records/arch-opt-v2-m2a-closeout-2026-08-11.md) 为准。
