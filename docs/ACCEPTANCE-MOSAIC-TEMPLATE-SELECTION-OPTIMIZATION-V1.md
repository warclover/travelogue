# ACCEPTANCE · 拼图模板选型与使用优化 V1（MTSO）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) **v0.2.0** |
| **实施** | [IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md](./IMPLEMENTATION-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) |
| **评审** | [mtso-mosaic-template-selection-v1-review-2026-07-23.md](./acceptance-records/mtso-mosaic-template-selection-v1-review-2026-07-23.md) · Conditional Go |
| **可行性** | [mtso-dev-feasibility-2026-07-23.md](./acceptance-records/mtso-dev-feasibility-2026-07-23.md) · SUP 已认可 |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-07-23 |

> **用法**：AC 断言以 **raw** `drain_mosaic_capture` / 单测为准（D-MTSO-11），禁止只读展示 Top-3。  
> **勾选**：✅ 自动化已锁 · ☑ 工程对齐待狗粮 · ☐ 未做。

---

## 0. 编码启动门

| ID | 检查项 | 结果 |
|----|--------|------|
| AC-MTSO-W0-01 | PRD v0.2.0 + SUP-01～10 产品认可 | ✅ |
| AC-MTSO-W0-02 | 本 ACCEPTANCE 已拆（SUP-10 / BLK-08） | ✅ |
| AC-MTSO-W0-03 | PR 列车：A → B → C1 → C2 → D | ✅ |

---

## 1. M1 / PR-A · 生命周期

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MTSO-01** | TPC ON + experiments OFF → experimental 不可见；deprecated 永不可见 | ✅ `test_mtso_lifecycle_a` |
| **AC-MTSO-02** | equal/rail 在 candidate / fallback / self-heal / legacy 负例 | ✅ |
| **AC-MTSO-03** | 六图窗 raw 漏斗字段可归类 | ✅ schema + funnel stage |

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_lifecycle_a.py tests/unit/layout_engine/test_template_contract_w3.py -q
```

---

## 2. M2 / PR-B · 六图机会

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MTSO-04** | admit fixture：`effectiveWindowOrder` 前缀 `6,5,4` 且至少尝试 size=6 | ✅ `test_mtso_pr_b_c1` |
| **AC-MTSO-05** | 非结构合格：无 `structurally_qualified_six` 重排 | ✅ |
| **AC-MTSO-06** | dense/相邻/large/segment 红线违规=0 | ✅ 合成 chapter 不变量 |
| **AC-MTSO-11a** | 漏斗字段含 opportunity / quotaSnapshot / qualifyReason / outcome | ✅ 字段 |
| **AC-MTSO-13** | 六图家族 large 配额按 family 去重；emit tie-break → canonical | ✅ |
| SUP-03 | MTSO ON 跳过旧 `hero_reserve` 过滤；armed 不挡无关 cursor | ✅ |
| SUP-05 | size6 尝试失败 → opportunity **released** | ✅ |
| D-10 | `_order_hero_six` 稳定原因码透传 qualify | ✅ |

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_pr_b_c1.py -q
```

---

## 3. M2 / PR-C1 · 混向硬拒

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MTSO-07** | 强竖硬拒横主竖辅；横强可落横主竖辅；不可 usage undo | ✅ |
| SUP-06 | 父开关 ON 即硬拒，不依赖 `usage_rules.enabled` | ✅ |
| Rescue | MCS 全失败 + 强竖 cursor → `screen-portrait-1` | ✅ |
| D-MTSO-03 gap | 相对最强横 gap≥阈值 亦硬拒（非窗绝对最大时仍可触发） | ✅ |
| S-MTSO-02 YAML | `whenNotToUse` 点名 `mixed_portrait_is_hero` 且与硬拒同 fixture | ✅ |

---

## 4. M2 / PR-C2 · 竖主 SKU（O-1 合同冻结）

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MTSO-08** | 两 SKU：`status=experimental`；主槽面积≥0.55；主从≥3:1；不进 `MOSAIC_5_PATTERN_IDS` / `lte_policy` | ✅ `test_mtso_pr_c2_skus` |
| **AC-MTSO-09** | 签名 miss / 空交集 → `signature_fallback` 保留先验集；无静默空候选 | ✅ |
| Ordering | 1P4L 竖 main 置首；2P3L 最强竖为 main | ✅ |
| Lifecycle | 无三元组不可见；allowlist+cohort 可见 | ✅ |
| O-1 | 1P4L 左满高竖合同冻结；截图签核 → PR-D | ✅ 合同 / ☐ 截图 |
| PR-D 几何 | 2P3L 三列：辅竖满高可读（AR&lt;1），非横宽条 | ✅ `test_prd_2p3l_aux_slot_is_portrait_readable` |

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_pr_c2_skus.py -q
```

---

## 5. M3 / PR-D（进行中）

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MTSO-10** | `selection_optimization=false` 时嵌套子开关无效；与 parent-off 基线一致 | ✅ 合成窗 `test_mtso_pr_d` |
| **AC-MTSO-11** | 狗粮双阈值 + deprecated leak=0 | ☐ 手测 · [mtso-local-dogfood-GUIDE](./acceptance-records/mtso-local-dogfood-GUIDE.md) |
| **AC-MTSO-12** | 盲评 / 转正或归档 | ☐ |
| 狗粮烟测 | experiments 三元组 admit 竖主 SKU | ✅ `test_dogfood_experiments_admits_portrait_hero_sku` |

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_pr_d.py -q
```
