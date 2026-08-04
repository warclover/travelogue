# ACCEPTANCE · 等权宫准入优化 V1（EGA）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-EQUAL-GRID-ADMISSION-V1.md](./PRD-EQUAL-GRID-ADMISSION-V1.md) **v0.2.0** |
| **评审** | [ega-equal-grid-admission-v1-review-2026-08-04.md](./acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md) · **Conditional Go** |
| **实施** | [IMPLEMENTATION-EQUAL-GRID-ADMISSION-V1.md](./IMPLEMENTATION-EQUAL-GRID-ADMISSION-V1.md) |
| **狗粮** | [ega-local-dogfood-GUIDE.md](./acceptance-records/ega-local-dogfood-GUIDE.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-04 |

> **用法**：闸语义以单测为准；成册以锚点重排 + mosaic log 为准。  
> **正交**：EGA ⊥ MEGC 峰闸（M1/M2 不改 `allow_peaks`）；EGA ⊥ MTSO hero-6 资格公式。  
> **勾选**：✅ 已锁 · ☑ 合同已齐待合码 · ☐ 未做。

---

## 0. 编码启动门（M0）

| ID | 检查项 | 结果 |
|----|--------|------|
| **AC-EGA-W0-01** | PRD v0.2.0 + 边界表（SSG/MEGC/MTSO）无冲突 | ✅ |
| **AC-EGA-W0-02** | 本 ACCEPTANCE + IMPLEMENTATION + 狗粮 GUIDE + 评审模板已拆 | ✅ |
| **AC-EGA-W0-03** | 列车 M0→M1→M2→M3；禁单 PR 塞满；M3 默认延期 | ✅ |
| **AC-EGA-W0-04** | 锚点册冻结：`demo-0ebda73294` · 回归 `demo-2019` | ✅ |
| **AC-EGA-W0-05** | 七席 Conditional Go（2026-08-04） | ✅ |
| **AC-EGA-W0-06** | 若新增 mosaic bool 路径：CSC / recipe 重签列入 IMPL（BLK-EGA-03） | ✅ 基线 115 True / 69 False |
| **AC-EGA-W0-07** | D-EGA-13 双口径写入 AC-05；D-EGA-05 合码红线 | ✅ |

---

## 1. 可测常量

| 常量 | 值 | 用途 |
|------|-----|------|
| EGA 默认 patterns | `screen-landscape-4` · `screen-landscape-6` | AC-02～07 |
| anti_slice 默认 | `exempt` | AC-02 |
| clone soft `score_mul` | **0.85** | AC-03 |
| flat bonus | **0.08** | AC-07 |
| wasted_hero_ega_extra | **0.10** | AC-07 |
| 父开关 OFF | 行为 ≡ 合入前基线 | AC-04 |

---

## 2. M1 / PR-A · 闸门软化

| ID | 期望 | 结果 |
|----|------|------|
| **AC-EGA-02** | 合成窗：4×landscape · 同 `shotGroupId` · 紧时间跨度 · EGA on：`landscape-4` **不**出现在 `rejectedTemplates` 且 reason=`shot_group_anti_slice` | ✅ `test_ega_pr_a` |
| **AC-EGA-03** | 合成窗：近景克隆达原硬拒阈值 · EGA on：`landscape-4` 可进 scored 池；`hero-70` 路径对 slice 仍可 hard `near_scene_clone`（对照用例） | ✅ `test_ega_pr_a` + scorer `R_EGA_CLONE_SOFT` |
| **AC-EGA-04** | `equal_grid_admission.enabled=false`：上述合成窗恢复 hard 拒（与基线快照一致） | ✅ |
| **AC-EGA-05** | 锚点 `demo-0ebda73294` 重排（SSG/MEGC on）：**(A)** 成册 ≥1× `screen-landscape-4` **或** **(B)** 原四横窗 L4 进入 top3/scored 且无 hard anti_slice/clone + 比分可解释（D-EGA-13）；书面狗粮；**禁止**仅因「没出 L4」判失败 | ✅ **A+B** · [ega-dogfood-2026-08-04](./acceptance-records/ega-dogfood-2026-08-04.md)（成册 1× L4 · `ch-03-sc-10`） |
| **AC-EGA-10a** | PR-A 单测列入 must-green；未知配置键 fail-loud | ✅ |

```powershell
python -m pytest tests/unit/layout_engine/test_ega_pr_a.py -q
```

---

## 3. M2 / PR-B+C · 六图漏斗 + 无主次偏置

| ID | 期望 | 结果 |
|----|------|------|
| **AC-EGA-06** | 构造 remaining≥6 全横 · hero-6 `admit=false`：`sizes` 仍含 6；存在对 `screen-landscape-6` 的候选评估（log/scored）；不得仅以删除 size=6 结束 | ✅ `test_ega_pr_b` + 锚点六横微探针 |
| **AC-EGA-07** | 合成四横 · 故意压低 hero 分离度 / 触发 `main_not_window_best`：`landscape-4` 分 ≥ `hero-70` 或胜出 | ✅ `test_ega_pr_c` |
| **AC-EGA-08** | 回归：`shot_group_cross` 硬拒仍在；`demo-2019` 电影峰 L4 路径不回退（相对 MEGC 基线） | ✅ `test_ega_pr_b` AC-08 + [狗粮 §AC-08](./acceptance-records/ega-dogfood-2026-08-04.md) |
| **AC-EGA-10b** | PR-B/C 单测 must-green | ✅ `test_ega_pr_b` + `test_ega_pr_c` |

```powershell
python -m pytest tests/unit/layout_engine/test_ega_pr_b.py tests/unit/layout_engine/test_ega_pr_c.py -q
```

---

## 4. M3 / PR-D · MEGC soft demote（延期）

| ID | 期望 | 结果 |
|----|------|------|
| **AC-EGA-09** | 若 Kickoff：`soften_penalize_emit=true` 时 3:2 窗可 emit L4 + 狗粮记录；默认 false 行为不变 | ☐ |

---

## 5. 防假绿

| 禁令 | 说明 |
|------|------|
| 禁止用「关 SSG/MEGC」刷出 L4 冒充 EGA | 狗粮须 EGA on + 父闸 on |
| 禁止只改 HTML/CSS 假装成册出宫格 | 须 trip `patternId` / mosaic log |
| 禁止把 hero-70 计入「等权宫」KPI | KPI 仅 `landscape-4` / `landscape-6` |
| 禁止 M1 宣称「解决 3:2 几何」 | 属 MEGC；EGA 只保证准入 |

---

## 6. 签字栏

| 角色 | 签名 | 日期 |
|------|------|------|
| 产品 | | |
| 算法 | | |
| 开发 | | |
| QA | | |
