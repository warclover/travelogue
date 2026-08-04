# Travelogue · 等权宫准入优化 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio |
| **文档版本** | **v0.2.0** |
| **状态** | **Conditional Go · 可 Kickoff M0 / M1（PR-A）**（[七席](./acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md) · M2 待 BLK · M3 延期） |
| **DOC-STATUS** | **active** |
| **主题代号** | 「等权宫准入优化 V1」— **EGA**（Equal-Grid Admission） |
| **触发来源** | 2026-08-04 实册调查 · `demo-0ebda73294`（初中毕业照）：横图充足却 **0×** `screen-landscape-4` / `screen-landscape-6`；四横窗被 SSG/clone 硬拒后改走 `screen-mosaic-4-hero-70-sidebar`；六图窗 `six_hero_precheck` 失败后整窗放弃 |
| **审查基线** | [SSG](./PRD-SMART-SHOT-GROUPING-V1.md) · [MEGC](./PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) · [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [ALG-V3](./PRD-ALGORITHM-OPTIMIZATION-V3.md) · [6 张拼图](./PRD-6张拼图优化.md) · [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) · [LVP](./PRD-LAYOUT-VIBE-PICKER-V1.md) |
| **关联文档** | [ACCEPTANCE](./ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md) · [IMPLEMENTATION](./IMPLEMENTATION-EQUAL-GRID-ADMISSION-V1.md) · [狗粮 GUIDE](./acceptance-records/ega-local-dogfood-GUIDE.md) |
| **评审纪要** | [ega-equal-grid-admission-v1-review-2026-08-04.md](./acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md)（结案）· [模板](./acceptance-records/ega-equal-grid-admission-v1-review-TEMPLATE.md) |
| **更新日期** | 2026-08-04 |

> **v0.2.0 相对 v0.1.0（七席回写 · 2026-08-04）**
>
> 1. **Conditional Go**：可 Kickoff M0；可 Kickoff M1（PR-A，合码前关 BLK-EGA-03/04）；M2 挡 BLK-EGA-06；**M3 默认延期**。  
> 2. **OQ-01～04 关闭**：anti-slice=exempt · clone soft `0.85` · M3 延期 · 不改 `flat_six_grid`。  
> 3. **新增 D-EGA-13**：G-06/AC-05 **双口径**（胜出 ∨ 进池可比分）。  
> 4. **D-EGA-05 升合码红线**：禁止 `prefers_burst` 捷径结案。  
> 5. **F-08～F-11** 写入审查事实（3:2+MEGC demote、L6∉MEGC patterns、AC 已拆、prefers_burst 污染）。

> **定位**
>
> MEGC 解决了「等权宫 **怎么画才不裁**」与「非电影峰 **该不该硬发**」。  
> SSG / ALG-V3 解决了「同分镜假切条 / 近景克隆 **不该乱拼**」。  
> 两套闸叠在一起后，**同场景、质量均匀的全横 burst** 反而失去等权宫机会——被当成「假切条」硬拒，或在 hero-6 资格失败后连 size=6 一起放弃。  
> 本主题 **不强制** 出四宫/六宫，只修复 **误伤与漏评**，让等权宫在「无明确主次、全横、可凝聚」时能与 hero 模板公平竞争。

> **一句话目标**：**同分镜全横 burst 不再被闸门提前清场；hero-6 失败不等于六图窗作废；无主次时等权宫可自然胜出。**

> **完成定义**

| 门 | 含义 | 不等于 |
|----|------|--------|
| **M0 Go** | 决策表锁定 · 与 SSG/MEGC/MTSO 边界切清 · AC/IMPL 拆文 · 锚点册冻结 | 改默认 GA 权重堆 SKU · 关 SSG/MEGC |
| **M1 Go** | PR-A：等权全横对 anti-slice / near_scene_clone **软化**；锚点册可出 ≥1× `landscape-4` 或可解释为何仍选 hero | 关掉 clone 闸 · 强制 4L→L4 |
| **M2 Go** | PR-B：hero-6 precheck 失败后仍评估 `screen-landscape-6`；PR-C：无主次评分偏向等权 | 强制六宫密度 · 重写 MTSO lifecycle |
| **M3 Go** | PR-D：MEGC 3:2 soft 路径可观测盲评；默认 on/off 另决策 | 默认把 `three_two` 塞进 `allow_peaks` 不盲评 |

---

## 0. 读者指南与边界

### 0.1 与相邻主题

| 主题 | 关系 | 本主题做什么 |
|------|------|--------------|
| [SSG](./PRD-SMART-SHOT-GROUPING-V1.md) | **修补消费方** | 保留「假切条」精神；**收窄**等权全横对 `shot_group_anti_slice` / slice 作用域的误伤 |
| [ALG-V3](./PRD-ALGORITHM-OPTIMIZATION-V3.md) | **继承** | 不重开 clone 闸政治；对 **equal-grid 标签** 改软闸 / 阈值 |
| [MEGC](./PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) | **互补 · 不推翻** | 不废除电影峰闸；M3 仅讨论 3:2 **soft 路径**与观测，默认 allow_peaks 变更须盲评 |
| [MTSO](./PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) | **正交** | 不改 six-hero **资格公式**；只改「资格失败后的候选漏斗」 |
| [6 张拼图](./PRD-6张拼图优化.md) | **下游受益** | hero+5 仍走原路径；本主题补等权六宫漏评 |
| [LVP](./PRD-LAYOUT-VIBE-PICKER-V1.md) | **可选映射** | V1 **不**新增用户 vibe；开关走 LSE/config，不绑 LVP 文案 |
| [P15 MCS](./PRD-PHASE15-photo-mosaic-evolution.md) | **插入点** | `candidates.py` 拒因 · `scorer.py` 无主次偏置 · `hook.py` size=6 漏斗 |

### 0.2 非目标

| ID | 非目标 | 理由 |
|----|--------|------|
| **N-EGA-01** | 强制「有 4 横必出 landscape-4」 | 破坏杂志主次；与用户「不要强制」一致 |
| **N-EGA-02** | 关闭 SSG / MEGC / near_scene_clone 父开关 | 回归假切条与裁切债 |
| **N-EGA-03** | 新建平行等权 YAML / SoftCollage | 组合爆炸；LTE 已有 L4/L6 |
| **N-EGA-04** | 用 MSA `trackOverride`「修好」等权槽 AR | MEGC 数学结论：不可能 |
| **N-EGA-05** | V1 用户面 vibe / 设置文案 | 属 LVP；本主题算法侧 |
| **N-EGA-06** | 默认把 `three_two`/`four_three` 加入 MEGC `allow_peaks` | 须 M3 盲评另决策 |
| **N-EGA-07** | 重写分镜聚类 / shotGroup 产线 | 只改 mosaic 消费闸 |
| **N-EGA-08** | 为毕业照等活动册写专用路由 | 用通用「等权全横」合同覆盖 |

### 0.3 术语

| 术语 | 定义 |
|------|------|
| **等权宫** | 无主次、等面积网格：`screen-landscape-4`（2×2）· `screen-landscape-6`（3×2）；LTE tags 含 `equal-4` / `equal-grid` |
| **加权四拼** | 有主次：`screen-mosaic-4-hero-70-sidebar` 等 |
| **slice 模板** | SSG：`prefers_burst is not True` → `is_slice_pattern`；现网 L4/L6 因未标 `prefers_burst` 被当成 slice |
| **假切条** | 同分镜紧时间窗被切成「一条故事的碎条」观感；**等权并置**不是假切条的典型形态 |
| **无主次窗** | MCS 出现 `R_MAIN_NOT_WINDOW_BEST` / hero 分离度弱 / 清晰度接近 |
| **EGA 软化** | 硬拒 → 软罚或豁免；候选仍进池，由 scorer 与 MEGC 决定胜负 |

### 0.4 代码与实机事实（2026-08-04 · `demo-0ebda73294`）

| ID | 事实 |
|----|------|
| **F-01** | 成册：`landscape-4`=0 · `landscape-6`=0 · `mosaic-4-hero-70-sidebar`=2 · `landscape-3`=4 · 大量 `landscape-1` |
| **F-02** | 两屏四横（`ch-03-sc-11` / `ch-03-sc-13`）资产全 ~**3:2**，同 `shotGroupId=sg-scene-0` |
| **F-03** | MCS 拒因：`near_scene_clone`×1 · `shot_group_anti_slice`×2（`algoV3.rejectFunnelTop` 一致） |
| **F-04** | `screen-landscape-4`：`prefers_burst=None` → `is_slice_pattern=True`；`hero-70`：`prefers_burst=true` → **豁免** anti-slice |
| **F-05** | size=6 尝试全部 `fallbackReason=six_hero_precheck`，随后 `mcs_all_sizes_failed` → legacy |
| **F-06** | MEGC 默认 `allow_peaks=("sixteen_nine",)`；legacy 对非电影峰 L4 走 `should_block_legacy_equal_grid` → demote 到 3/1 |
| **F-07** | 持久化 `mosaicDecisionLog` 为 summary 级；细拒因在 raw / 本趟 log 条目的 `rejectedTemplates` |
| **F-08** | 即便 L4 进 MCS 池，legacy 对 3:2 仍可能 MEGC demote→3/1（七席）→ **D-EGA-13 双口径** |
| **F-09** | `screen-landscape-6` **不在** MEGC 默认 `patterns` → PR-B 与峰闸解耦 |
| **F-10** | AC/IMPL/GUIDE 在 v0.1 已拆 → BLK-EGA-02 关闭 |
| **F-11** | L4 标 `prefers_burst: true` 会污染 SSG slice → D-EGA-05 合码红线 |

```text
候选拒漏斗（现状 · 示意）
pattern_disabled → try_order → atom → shot_group_cross → shot_group_anti_slice
  → near_scene_clone → build_screen → …
等权 L4 在 anti_slice / clone 被硬清场 → 仅 hero-70 进 top3
```

---

## 1. 问题

1. **语义倒置**：同分镜、质量均匀的四横「等权并置」被当成假切条硬拒；有主次的 hero 侧栏反而因 `prefers_burst: true` 豁免。  
2. **六图漏评**：`six_hero_precheck` 失败只应挡住 **hero-6 族**，不应让 size=6 整窗放弃，导致 `landscape-6` 从未比分。  
3. **无主次仍强行主次**：多次 `R_MAIN_NOT_WINDOW_BEST` 仍选 hero-70，等权宫没有评分托底。  
4. **3:2 债与准入债叠加**：即便过了 SSG，MEGC/legacy 仍把 3:2 四宫降成三横——这是 **几何合同**，本主题 M1/M2 **不推翻**；M3 另开观测与盲评。

---

## 2. 目标

| ID | 目标 |
|----|------|
| **G-01** | 等权全横（L4/L6）在「同分镜紧窗」下 **可进候选池**（软罚可，硬拒默认关） |
| **G-02** | `near_scene_clone` 对等权全横默认 **软罚**；hero+窄条切条模板保持硬拒阈值 |
| **G-03** | hero-6 资格失败后，size=6 仍评估 `screen-landscape-6`（及既有非 hero-6 六图模板若在 try_order） |
| **G-04** | 无主次窗：等权宫相对 hero 模板 **可竞争胜出**（非强制） |
| **G-05** | 全程可观测：拒因 / 软罚 / `ega*` 日志字段；`algoV3` 或 mosaic log 可区分 EGA 路径 |
| **G-06** | 锚点册重排（SSG/MEGC 保持 on）：**≥1 屏等权宫**，**或** 原四横窗 L4 进池/top3 且无 hard anti_slice/clone + 比分可解释（D-EGA-13） |

---

## 3. 已拍板决策（七席锁定 · v0.2.0）

| ID | 决策 | 备注 |
|----|------|------|
| **D-EGA-01** | **不强制** 出宫格；只修误伤与漏评 | 产品底线 |
| **D-EGA-02** | 引入模板族标签 **`equal_grid_pure_landscape`**：默认仅 `screen-landscape-4` · `screen-landscape-6` | 代码 frozenset + 可配置覆盖；**禁止**用「一切 2×2」扩大 |
| **D-EGA-03** | 对该族：`shot_group_anti_slice` **豁免硬拒**；可选 soft 默认 **关** | hero/加权切条模板 **不变** · OQ-01 关闭 |
| **D-EGA-04** | 对该族：`near_scene_clone` 达原硬拒阈值 → **软罚** `score_mul=0.85`（`R_EGA_CLONE_SOFT`）；hero+tile slice 仍硬拒 | OQ-02 关闭 |
| **D-EGA-05** | **合码红线**：**禁止**仅靠给 L4 标 `prefers_burst: true` 结案（污染 SSG slice） | BLK-EGA-04 |
| **D-EGA-06** | `six_hero_precheck` 失败 → **不**从 `sizes` 移除 6；仅 `allow_six_hero=false`；继续评估 `landscape-6` | MTSO hero-6 资格公式不改 |
| **D-EGA-07** | 无主次偏置：`main_not_window_best` / 低 hero_separation → equal-grid **bonus** · hero-70 **wasted_hero 加强** | PR-C · 见 §5 |
| **D-EGA-08** | M1/M2 **不**修改 MEGC `allow_peaks`；3:2 仍可被 MEGC/legacy demote——EGA 保证「进池可比分」 | M3 延期 |
| **D-EGA-09** | 父开关 `mosaic.equal_grid_admission.enabled` 默认 **true**；false ≡ 现网 | fail-loud 未知键 |
| **D-EGA-10** | 不新增用户 vibe；不改 NAS/LVP 文案 | — |
| **D-EGA-11** | 混向等权（2L2P 等）**不在**豁免范围 | MEGC D-06 |
| **D-EGA-12** | 跨 `shotGroupId` 的 slice 硬拒（`shot_group_cross`）**保留** | 不放宽跨组假一条 |
| **D-EGA-13** | **G-06 / AC-05 双口径**：成册 ≥1× L4 **或** 原四横窗 L4 进池/top3 且无 hard anti_slice/clone + 比分可解释 → 均算准入成功 | 防 3:2+MEGC demote 假红（F-08） |

### 3.1 OQ 关闭结论（七席）

| ID | 结论 |
|----|------|
| **OQ-01** | ✅ **exempt** 硬拒；soft 可选默认关 |
| **OQ-02** | ✅ clone soft **`score_mul=0.85`** |
| **OQ-03** | ✅ **M3 延期**；先看 MCS 准入是否够 |
| **OQ-04** | ✅ **不改** `flat_six_grid` 罚 |

---

## 4. 方案分轨

### 4.1 PR-A · 闸门软化（M1 · P0）

**改什么**

| 模块 | 动作 |
|------|------|
| `config/mosaic.py` | 新增 `EqualGridAdmissionConfig`（见 §5） |
| `mosaic/candidates.py` | anti_slice / clone 分支：若 pattern ∈ equal_grid_pure_landscape 且 EGA on → 跳过硬拒或改软罚 |
| `mosaic/shot_group_gate.py` | 可选：`hard_reject_same_shot_group_anti_slice(..., equal_grid_exempt=)` |
| `mosaic/scorer.py` | 应用 clone soft mul；打 `R_EGA_CLONE_SOFT` / `R_EGA_SLICE_SOFT` |
| `curation/algo_v3_summary.py` | rejectFunnel 区分 `shot_group` hard vs `ega_soft`（可选） |

**不变**

- hero-70 / 其他 `prefers_burst: true` 行为  
- 跨组 `shot_group_cross`  
- MEGC 峰闸  

**锚点期望（`demo-0ebda73294`）**

- 至少 1 个原四横窗：`landscape-4` **进入 top3 或胜出**；若仍败给 hero-70，log 须有可比分数（非硬拒清空）

### 4.2 PR-B · 六图漏斗修复（M2 · P0）

**改什么**

| 模块 | 动作 |
|------|------|
| `mosaic/hook.py` | `admit_six=false` 时：**保留** size 6 在 `sizes`；probe log 增加 `egaEqualSixKept=true` |
| `mosaic/candidates.py` / try_order | size=6 且非 allow_six_hero 时，排除或降权 hero-6 族，**保留** `screen-landscape-6` |
| `mosaic/lifecycle.py` | 确认 six_hero_family 归一不影响 equal-6 |

**锚点期望**

- 存在 remaining≥6 的全横段时：出现 ≥0 次对 `landscape-6` 的 **正式打分**（非仅 precheck probe）；胜出非必须

### 4.3 PR-C · 无主次评分偏置（M2 · P1）

**改什么**

| 模块 | 动作 |
|------|------|
| `mosaic/scorer.py` | 无主次检测 → equal-grid `+ega_flat_bonus`；hero-70 族加强 `wasted_hero` |
| 配置 | `flat_window_equal_bonus` · `wasted_hero_ega_extra` |

**锚点期望**

- 原 `R_MAIN_NOT_WINDOW_BEST` 且四横窗：等权宫胜出率相对 PR-A-only **不下降**；目标至少 1 屏 L4（与 PR-A 联合狗粮）

### 4.4 PR-D · MEGC 3:2 观测与可选 soft demote（M3 · 延期默认）

**范围（仅当七席批准 Kickoff M3）**

- legacy `should_block_legacy_equal_grid` 对 `gate_penalize`：**可配置**改为「仍 emit L4 + 乘分」而非 demote 到 3  
- **默认保持现网 demote**；狗粮对比 ON/OFF  
- **禁止**本 PR 默认改 `allow_peaks`

---

## 5. 配置合同

```yaml
mosaic:
  equal_grid_admission:
    enabled: true                    # 父开关；false = 现网
    patterns:                        # 可覆盖；默认见代码
      - screen-landscape-4
      - screen-landscape-6
    anti_slice:
      mode: exempt                   # exempt | soft_penalty | hard (legacy)；七席锁定默认 exempt
      score_mul: 0.90                # 仅 soft_penalty 且显式开启时
    near_scene_clone:
      mode: soft_penalty             # soft_penalty | hard (legacy)；七席锁定 0.85
      score_mul: 0.85
    size6:
      keep_equal_grid_after_hero_precheck_fail: true
    scoring:
      flat_window_equal_bonus: 0.08  # 无主次时加给 equal-grid
      wasted_hero_ega_extra: 0.10    # 无主次时额外罚 hero 族
    # M3 only · 默认不生效
    megc_legacy_demote:
      soften_penalize_emit: false
```

**Fail-loud**：`equal_grid_admission` 未知键拒绝启动（对齐 mosaic 其它子树）。  
**CSC / happy_path_recipe**：新增 bool 路径须走 ALG-V3 **AC-32** 重签流程（IMPL 列清单）。

---

## 6. 可观测性

| 字段 / 事件 | 含义 |
|-------------|------|
| `egaEnabled` | 本窗是否 EGA on |
| `egaAntiSliceMode` / `egaCloneMode` | 实际模式 |
| `rejectedTemplates[].reason` | 不再对 L4 报 hard `shot_group_anti_slice`（改为 soft reason 或 scorer code） |
| `winnerReasonCodes` | 可含 `R_EGA_FLAT_BONUS` · `R_EGA_CLONE_SOFT` |
| `six_hero_precheck` probe | 增 `egaEqualSixKept` |
| `algoV3.rejectFunnelTop` | 可选拆 `ega_soft` 计数 |

持久化 summary log 至少保留：pattern 胜负 · rejected reason 枚举 · EGA 父开关有效值。

---

## 7. 里程碑与人日（估）

| 门 | 内容 | 估 |
|----|------|-----|
| **M0** | 七席 · 本文定稿 · AC/IMPL · 锚点冻结 | 0.5–1d |
| **M1 / PR-A** | 闸门软化 + 单测 + 锚点狗粮 | 1.5–2.5d |
| **M2 / PR-B+C** | 六图漏斗 + 无主次偏置 + 回归 | 1.5–2.5d |
| **M3 / PR-D** | 可选 · MEGC soft demote 狗粮 | 1–2d（延期） |

**禁止**：单 PR 塞满 M1–M3。

---

## 8. 验收摘要

完整表见 [ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md](./ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md)。

| ID | 门 | 断言 |
|----|----|------|
| **AC-EGA-01** | M0 | PRD + AC + IMPL 齐；边界表无冲突 |
| **AC-EGA-02** | M1 | 合成「同分镜·4×3:2 横」：L4 **不被** `shot_group_anti_slice` 硬拒 |
| **AC-EGA-03** | M1 | 同上窗：clone 达阈值时 L4 **软罚可进池**；hero+tile 仍可硬拒 |
| **AC-EGA-04** | M1 | `enabled=false` 行为 ≡ 现网基线单测 |
| **AC-EGA-05** | M1 | 锚点册重排：`rejectedTemplates` 对 L4 无 hard anti_slice/clone；或胜出 ≥1× L4 |
| **AC-EGA-06** | M2 | hero-6 precheck fail 时 size=6 仍尝试；log 含对 `landscape-6` 的评估或明确 skip 理由 ≠「整窗 size 删除」 |
| **AC-EGA-07** | M2 | 无主次四横合成窗：equal-grid 分 ≥ hero-70（或胜出） |
| **AC-EGA-08** | M2 | 回归：跨组分镜切条硬拒仍在；16:9 电影峰 L4 不回退 |
| **AC-EGA-09** | M3 | （可选）soft demote 狗粮记录入库 |
| **AC-EGA-10** | M1–M2 | must-green 单测列表绿；CSC 若触 flag 则重签 |

### 8.1 盲评四问（狗粮）

1. 等权四宫是否「该有的有」——同场景均匀横图并置是否自然？  
2. 是否出现假切条回潮（同分镜被切碎）？  
3. 有明确主图的窗是否仍能选出 hero？  
4. 3:2 四宫观感是否可接受（若出现）——裁切 / 信箱 / 节奏？

---

## 9. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 假切条回潮 | 豁免范围仅 pure landscape equal-grid；跨组硬拒保留；狗粮对照 |
| 密度过高（过多 L4/L6） | 无主次 bonus 可调；P21 dense 配额不放宽；可关 scoring 子开关 |
| MEGC 仍 demote 3:2 → 「修了闸仍无 L4」 | G-06 允许「进池但败给 MEGC」并书面解释；M3 再议 |
| CSC / recipe 爆炸 | IMPL 列 flag 路径；AC-32 流程 |
| 与 MTSO six-hero 竞态 | PR-B 单测：admit 与 equal-6 并存矩阵 |

**回滚**：`mosaic.equal_grid_admission.enabled: false`（D-EGA-09）。

---

## 10. 锚点与对照册

| 册 | 用途 |
|----|------|
| **`trips/demo-0ebda73294`** | 主锚点（毕业照 · 同分镜 3:2 四横） |
| `trips/demo-2019` | MEGC 回归（电影峰 L4 不回退） |
| 合成 unit fixtures | AC-02/03/07 |

重排命令（实施后写入 IMPL 精确旗）：

```powershell
python -m travelogue layout trips/demo-0ebda73294 --layout auto --web-layout screens --render --no-validate
```

---

## 11. 开放阻断（七席后 · 合码门）

完整表见 [评审纪要 §5](./acceptance-records/ega-equal-grid-admission-v1-review-2026-08-04.md)。

| ID | 状态 | 挡 |
|----|------|-----|
| **BLK-EGA-01** | ✅ 本版回写 | M0 |
| **BLK-EGA-02** | ✅ AC/IMPL 已齐 | M0 |
| **BLK-EGA-03** | ✅ CSC/recipe 重签（115/69） | M1 合码 |
| **BLK-EGA-04** | ✅ 白名单单测 + 禁 prefers_burst 捷径 | M1 合码 |
| **BLK-EGA-05** | ✅ 锚点狗粮双口径 **A+B**（成册 1× L4） | M1 Done 宣称 |
| **BLK-EGA-06** | ✅ 跨组单测 + demo-2019 电影峰 gate_allow | M2 / PR-B |

---

## 12. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.2.1** | 2026-08-04 | BLK-03～06 关闭状态回写；PR-B 收口 |
| **v0.2.0** | 2026-08-04 | 七席 Conditional Go · D/OQ 锁定 · D-13 · M3 延期 |
| **v0.1.0** | 2026-08-04 | 初稿 · 基于 `demo-0ebda73294` 调查与优化建议落地为可执行合同 |
