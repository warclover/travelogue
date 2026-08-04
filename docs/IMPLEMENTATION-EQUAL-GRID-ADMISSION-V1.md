# IMPLEMENTATION · 等权宫准入优化 V1（EGA）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-EQUAL-GRID-ADMISSION-V1.md](./PRD-EQUAL-GRID-ADMISSION-V1.md) **v0.2.0** |
| **评审** | [ega-equal-grid-admission-v1-review-2026-08-04.md](./acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md) · Conditional Go · 可 Kickoff M1 |
| **验收** | [ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md](./ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-04 |

> **原则**：小步 PR；先闸后漏斗再评分；M3 默认不排期。  
> **勾选**：✅ 已合 · ☑ 合同 · ☐ 未做。

---

## 0. 列车

```text
M0 文档/评审
  → M1 PR-A 闸门软化
    → M2 PR-B 六图漏斗 ‖ PR-C 无主次偏置（可同列车两 PR）
      → M3 PR-D MEGC soft demote（延期）
```

---

## 1. 代码锚点（As-Is）

| 区域 | 路径 | EGA 动作 |
|------|------|----------|
| 配置 | `travelogue/config/mosaic.py` | 新增 `EqualGridAdmissionConfig` · `mosaic_from_dict` fail-loud |
| 候选闸 | `travelogue/layout_engine/mosaic/candidates.py` | anti_slice / clone 分支挂 EGA |
| SSG 闸 | `travelogue/layout_engine/mosaic/shot_group_gate.py` | 可选 exempt 参数 |
| slice 判定 | `travelogue/layout_engine/mosaic/clone_detection.py` · `template_prefers_burst` | **不**仅靠改 prefers_burst 结案 |
| 打分 | `travelogue/layout_engine/mosaic/scorer.py` | soft mul · flat bonus · wasted_hero extra |
| 窗漏斗 | `travelogue/layout_engine/mosaic/hook.py` | size=6 keep after precheck fail |
| hero-6 | `travelogue/layout_engine/mosaic/hero_six.py` | **只读**；不改资格公式 |
| legacy MEGC | `travelogue/layout_engine/planner/screen_planner.py` · `megc_gate.py` | 仅 M3 |
| 摘要 | `travelogue/curation/algo_v3_summary.py` | 可选 funnel 拆分 |
| LTE | `layout_templates/templates/screen-landscape-{4,6}.yaml` | 可选加 tag `equal-grid`；非必须 |

---

## 2. PR-A · 闸门软化（M1）

### 2.1 任务清单

| ID | 任务 | 状态 |
|----|------|------|
| **BE-EGA-A01** | `EqualGridAdmissionConfig` + 默认值 + 未知键 fail-loud + 单测 | ✅ |
| **BE-EGA-A02** | `is_ega_equal_grid_pattern(pid, cfg)` 助手 | ✅ |
| **BE-EGA-A03** | `candidates.py`：anti_slice 对 EGA pattern → exempt / soft | ✅ |
| **BE-EGA-A04** | `candidates.py`：clone 硬阈值对 EGA pattern → soft 进 scorer | ✅ |
| **BE-EGA-A05** | reason codes：`R_EGA_CLONE_SOFT`（及可选 slice soft） | ✅ |
| **BE-EGA-A06** | OFF 快照单测 ≡ 基线 | ✅ |
| **BE-EGA-A07** | 锚点狗粮记录（AC-05） | ✅ **A+B** · [ega-dogfood-2026-08-04](./acceptance-records/ega-dogfood-2026-08-04.md) |
| **BE-EGA-A08** | 若触 CSC bool 路径 → 重签（ALG-V3 AC-32） | ✅ 基线 115/69 · +3 bool |

### 2.2 建议单测文件

- `tests/unit/layout_engine/test_ega_pr_a.py`
- `tests/unit/config/test_ega_config.py`（可合并）

### 2.3 合码门

- AC-02/03/04 绿  
- AC-05 狗粮至少填「进池」证据  
- 无 `prefers_burst: true` 作为 L4 唯一补丁合入（D-EGA-05）

---

## 3. PR-B · 六图漏斗（M2）

| ID | 任务 | 状态 |
|----|------|------|
| **BE-EGA-B01** | `hook.py`：`admit_six=false` 时保留 6 in `sizes`（受 `keep_equal_grid_after_hero_precheck_fail`） | ✅ |
| **BE-EGA-B02** | probe log：`egaEqualSixKept` | ✅ |
| **BE-EGA-B03** | size=6 候选：无 admit 时跳过 / 降权 six-hero family，保留 `landscape-6` | ✅ |
| **BE-EGA-B04** | 单测：precheck fail × equal-6 仍 scored | ✅ |
| **BE-EGA-B05** | admit×equal-6 并存矩阵 + AC-08 cross/MEGC 回归单测 | ✅ |
| **BE-EGA-B06** | 狗粮：锚点 L6 评估痕迹 + demo-2019 电影峰 gate_allow | ✅ |

---

## 4. PR-C · 无主次偏置（M2）

| ID | 任务 | 状态 |
|----|------|------|
| **BE-EGA-C01** | 检测 flat / `main_not_window_best` 条件（与现 scorer 字段对齐） | ✅ |
| **BE-EGA-C02** | equal-grid `+flat_window_equal_bonus` | ✅ |
| **BE-EGA-C03** | hero-70 族 `wasted_hero + ega_extra` | ✅ |
| **BE-EGA-C04** | 单测 AC-07；bonus=0 时行为可关 | ✅ |

---

## 5. PR-D · MEGC soft demote（M3 · 延期）

| ID | 任务 | 状态 |
|----|------|------|
| **BE-EGA-D01** | `megc_legacy_demote.soften_penalize_emit` 接线 | ☐ |
| **BE-EGA-D02** | 狗粮 ON/OFF 对比 3:2 L4 | ☐ |
| **BE-EGA-D03** | **禁止**默认改 `allow_peaks` | ☑ 合同 |

### 观测债（SHD · 已收）

| ID | 任务 | 状态 |
|----|------|------|
| **SHD-01** | summary/window 保留 `egaEnabled` / `egaEqualSixKept` / modes | ✅ |
| **SHD-02** | `algoV3.rejectFunnelTop.ega_soft` | ✅ |
| **SHD-03** | LTE tag `equal-grid`（L4+L6） | ✅ |

---

## 6. 配置样例

见 PRD §5。本机临时关闭：

```yaml
mosaic:
  equal_grid_admission:
    enabled: false
```

---

## 7. 回归命令

```powershell
# 单元
python -m pytest tests/unit/layout_engine/test_ega_pr_a.py tests/unit/layout_engine/test_ega_pr_b.py tests/unit/layout_engine/test_ega_pr_c.py -q

# 锚点重排（路径以本机 trips 为准）
python -m travelogue layout trips/demo-0ebda73294 --layout auto --web-layout screens --render --no-validate

# MEGC 回归册
python -m travelogue layout trips/demo-2019 --layout auto --web-layout screens --render --no-validate
```

---

## 8. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.2.4** | 2026-08-04 | 收口：SHD-01/02 观测 · AC-05 A 实册 · 文档对齐 |
| **v0.2.3** | 2026-08-04 | PR-C：flat bonus / wasted hero extra · `test_ega_pr_c` |
| **v0.2.2** | 2026-08-04 | PR-B 收口：admit 矩阵 · AC-08 · 狗粮 BLK-06 |
| **v0.2.1** | 2026-08-04 | PR-B 落地：size=6 keep · `egaEqualSixKept` · L6 注入 · `test_ega_pr_b` |
| **v0.2.0** | 2026-08-04 | 对齐七席 · BLK-03/04 合码门 · D-13 |
| **v0.1.0** | 2026-08-04 | 初稿 · 与 PRD v0.1.0 同步 |
