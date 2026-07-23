# ACCEPTANCE · 拼图槽位自适应 V1（MSA）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) **v0.2.0** |
| **实施** | [IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md](./IMPLEMENTATION-MOSAIC-SLOT-ADAPTATION-V1.md) |
| **评审** | [msa-mosaic-slot-adaptation-v1-review-2026-07-23.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md) · Conditional Go |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-07-23 |

> **用法**：AC 断言以 **raw** mosaic capture / 单测为准（D-MSA-10），禁止只读展示层。  
> **正交**：MSA ⊥ [MTSO](./ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md)；不把选型 KPI 并进本表。  
> **勾选**：✅ 自动化已锁 · ☑ 合同/文档已齐待合码 · ☐ 未做。

---

## 0. 编码启动门（M0）

| ID | 检查项 | 结果 |
|----|--------|------|
| **AC-MSA-W0-01** | PRD v0.2.0 + 七席 Conditional Go | ✅ |
| **AC-MSA-W0-02** | 本 ACCEPTANCE + IMPLEMENTATION 已拆（BLK-MSA-05） | ✅ |
| **AC-MSA-W0-03** | 列车：M0 → PR-A(M1) → PR-B(M2) → PR-C(M3)；禁单 PR 塞满 | ✅ |
| **AC-MSA-W0-04** | M1 合码前合同：持久化 · 峰阈值 · variant 各自求解 · 面积硬门 · 日志字段（BLK-02～04/07/08） | ✅ PR-A 代码+单测 |
| **AC-MSA-W0-05** | M2 合码前：contain 杂志纸色最低视觉合同（BLK-06） | ✅ [msa-contain-visual-contract-BLK06](./acceptance-records/msa-contain-visual-contract-BLK06.md) |

---

## 1. 可测常量（峰判定 · 七席冻结）

| 常量 | 值 | 用途 |
|------|-----|------|
| 梯子容差 | **0.08** | 横图 \(r\) → 最近梯子 |
| 单峰占比 | **≥ 0.60** | 判定 `landPeak` 单一峰 |
| `wide_peak_fraction` | **0.50**（默认） | 否则切 `sixteen_nine` / 电影轨 |
| `hero_target_clamp` | **\[1.30, 1.60\]** | `mixed` 时 median 夹逼 |
| `whitespace_max` | **0.08**（O-01 暂定） | 整页非影像面积硬门 |
| 主槽 AR 容差 | **±0.08** | AC-02 / AC-03 断言 |

---

## 2. M1 / PR-A · profile + 白名单求解 + 持久化

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MSA-01** | `slot_adaptation.enabled=false` 时固定 corpus 与基线逐屏一致（patternId、asset 序、静态几何）；嵌套子开关无效 | ✅ `test_msa_pr_a` |
| **AC-MSA-02** | 全单反横窗 fixture：求解后主槽 \(|r-1.50|≤0.08\)；main 面积/prominence **不跌破**模板声明下限 | ✅ |
| **AC-MSA-03** | 全手机 4:3 横窗：主槽贴 \(1.33±0.08\) | ✅ |
| **AC-MSA-04** | 混峰窗：`landPeak=mixed`，\(r^*\) 落在 clamp 内；整屏**单一** `trackOverride` | ✅ |
| **AC-MSA-05** | 求解失败 → 静态轨道 + `msa_solve_miss`；无空屏、不改拓扑 | ✅ |
| **AC-MSA-05v** | 每个激活 `stage.variants` **各自求解**；某 variant miss → 该 variant 回退静态轨并分 variant 打点；禁止只优化 web 16:9 | ✅ |
| **AC-MSA-05p** | screen 持久化 `layoutGeometry.trackOverride` + `slots[].fit`（及实渲 `displayAspect`）；preview / 长图导出 / 重渲染复用同一实例 | ✅ |

```powershell
python -m pytest tests/unit/layout_engine/test_msa_pr_a.py -q
```

---

## 3. M2 / PR-B · crop_risk · 分配 · 评分

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MSA-06** | 高 `crop_risk` 槽 → `contain`；整页 `whitespace_ratio ≤ whitespace_max`；超预算禁 contain 或重求解 | ✅ `test_msa_pr_b` |
| **AC-MSA-06v** | contain 底色 = 杂志纸色（默认）；无装饰相框/贴纸（BLK-06）；禁 blur-fill | ✅ |
| **AC-MSA-07** | 窗内最扁辅槽不接收 crop_risk 最高横图（分配约束单测） | ✅ |
| **AC-MSA-08** | raw 日志含 D-MSA-10 全字段：`msaProfile` · `rHeroTarget` · `trackOverride` · `slotFits` · `cropRisk[]` · `whitespaceRatio` · `msaOutcome` | ✅ |

```powershell
python -m pytest tests/unit/layout_engine/test_msa_pr_b.py -q
```

---

## 4. M3 / PR-C · 狗粮 · 盲评 · 默认 on

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MSA-09** | 三类画像狗粮：盲评「主体完整性」优于基线；无朝向 / dense 红线回退 | ☑ GUIDE+模板已齐 · ☐ 实册盲评签核 |
| **AC-MSA-10** | MTSO 开关组合回归：MSA ON/OFF × `template_experiments` / `selection_optimization` 不交叉破坏 lifecycle | ✅ `test_msa_pr_c` |
| **AC-MSA-11** | 默认 `enabled=true` 决策前：独立盲评记录；不通过则保持默认 off（O-05） | ✅ [决策 hold off](./acceptance-records/msa-default-on-decision-2026-07-23.md) |

手测入口：[msa-local-dogfood-GUIDE.md](./acceptance-records/msa-local-dogfood-GUIDE.md) · 盲评模板：[msa-blind-review-TEMPLATE.md](./acceptance-records/msa-blind-review-TEMPLATE.md)

```powershell
python -m pytest tests/unit/layout_engine/test_msa_pr_c.py -q
```

---

## 5. 非目标回归（防漂移）

| ID | 期望 | 结果 |
|----|------|------|
| **AC-MSA-N01** | 舞台 AR 仍为既有 16:9 / mobile 变体契约；不因 MSA 改舞台 | ✅ `test_msa_pr_c` |
| **AC-MSA-N02** | 不新增平行模板库；不改槽位数 / 主从拓扑 | ✅ |
| **AC-MSA-N03** | 不放宽朝向硬门；不把 MSA 指标并进 MTSO 转正漏斗 | ✅ AC-10 矩阵 |

---

## 6. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | M0 拆文：AC-01～11 + variant/persist 子项；对齐 PRD v0.2.0 / BLK-MSA-05 |
| **v0.2.0** | 2026-07-23 | PR-A/B 勾选 AC-01～08；PR-C：AC-10/11/N* · AC-09 待实册盲评 |
| **v0.2.1** | 2026-07-23 | gap-close：竖主白名单 · 电影轨 fixture · 评分升权 · 同实例幂等（`test_msa_gap_close`） |
