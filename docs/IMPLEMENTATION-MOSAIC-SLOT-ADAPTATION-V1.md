# IMPLEMENTATION · 拼图槽位自适应 V1（MSA）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v0.1.0** |
| **对应 PRD** | [PRD-MOSAIC-SLOT-ADAPTATION-V1.md](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md](./ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) |
| **评审** | [msa-mosaic-slot-adaptation-v1-review-2026-07-23.md](./acceptance-records/msa-mosaic-slot-adaptation-v1-review-2026-07-23.md) · Conditional Go |
| **DOC-STATUS** | **active** |
| **状态** | **M0 ✅ · PR-A / M1 ✅**（AC-01～05/05v/05p）；PR-B 未 Kickoff（BLK-06） |
| **分支** | `feat/msa-pr-a` |
| **更新日期** | 2026-07-23 |

> **定位**：把 MSA PRD + 七席展开为可执行任务卡。  
> **铁律**：M0 → PR-A → PR-B → PR-C；**禁止**单 PR 塞满；**禁止**把 MSA 并进 MTSO 转正 KPI。  
> **一句话**：拓扑固定 · 轨道可变 · 高风险可留白；默认 fail-closed 至 M3。

---

## 0. 已锁定决策（实施源）

以 PRD §5 / §6 + 评审 §7 为准。实施高频引用：

| ID | 一句话 |
|----|--------|
| **D-MSA-01** | 舞台 AR / 拓扑稳定；轨道权重与 fit 可变 |
| **D-MSA-02** | `trackOverride` + `slots[].fit` **持久化进 screen**；preview=export=重渲染 |
| **D-MSA-03** | \(r^*_{hero}\) 取窗横峰；**禁止**默认贴舞台 16:9；面积/prominence 不跌破 |
| **D-MSA-05** | 混峰 median 夹逼；整屏一套轨道 |
| **D-MSA-06** | `crop_risk≥θ` 才 contain；`whitespace_max=0.08` |
| **D-MSA-07** | `slot_adaptation.enabled` 默认 **false** 至 M3 |
| **D-MSA-08** | MSA 在模板已选定之后；不改 lifecycle / experiments |
| **D-MSA-09** | 求解失败 → 静态轨 + `msa_solve_miss` |
| **D-MSA-10** | raw 日志字段齐全（见 AC-08） |
| **O-MSA-04** | ✅ 已关：持久化（BLK-02） |

### 0.1 M1 合码挡门（文档已齐 · 代码待落）

| BLK | 要求 | 文档 | 代码 |
|-----|------|------|------|
| **02** | 持久化实例 | ✅ | ✅ PR-A |
| **03** | 峰占比≥0.60 · 容差 0.08 · clamp · wide_peak | ✅ AC §1 | ✅ PR-A |
| **04** | 每 variant 各自求解 | ✅ | ✅ PR-A |
| **05** | 拆 ACCEPTANCE/IMPL | ✅ 本文 | — |
| **07** | main 面积/prominence 硬断言 | ✅ AC-02 | ✅ PR-A |
| **08** | D-10 字段进 AC-08 | ✅ | ☑ PR-A 子集（cropRisk/whitespace 占位至 PR-B） |
| **06** | contain 纸色视觉 | ☐ M2 前 | ☐ PR-B |

---

## 1. PR 切片与退出

| PR | 里程碑 | 任务卡 | 退出（最低） | 风险 |
|----|--------|--------|--------------|------|
| **M0** | 文档 | T-00 | AC-W0-01～03 · BLK-05 | 低 |
| **PR-A** | M1 | T-01～08 | AC-01～05 · 05v · 05p | 中（CSS/variant） |
| **PR-B** | M2 | T-10～14 | AC-06～08 · BLK-06 | 中（留白观感） |
| **PR-C** | M3 | T-20～22 | AC-09～11 · 默认 on 决策 | 狗粮挡 |

**合并规则**：M0 未入库不得开 PR-A；PR-A 未绿不得合 PR-B；PR-B 不得早于 BLK-06 视觉签核。

---

## 2. 任务卡 · M0（本文交付）

### T-MSA-00 · 文档列车落地

| 项 | 内容 |
|----|------|
| **动作** | PRD v0.2.0 入库；七席纪要 + TEMPLATE；拆 ACCEPTANCE/IMPL；DOC-STATUS / README 挂链；PRD §14 BLK-05 勾选 |
| **验收** | AC-MSA-W0-01～03 |
| **估时** | 0.5d |

---

## 3. 任务卡 · PR-A（M1）详述

### T-MSA-01 · 配置壳 `SlotAdaptationConfig`

| 项 | 内容 |
|----|------|
| **动作** | `travelogue/config/mosaic.py`：dataclass + `mosaic_from_dict`；未知键 fail-loud；父 OFF ⇒ 子项无效 |
| **默认** | PRD §5.1 YAML（`enabled: false`） |
| **样例** | `config.yaml.example` 注释块；可选 `docs/config-msa-dogfood.example.yaml` |
| **验收** | 解析往返；父 OFF → effective=false |
| **估时** | 0.5d |

---

### T-MSA-02 · 窗级 AR profile（S-MSA-01）

| 项 | 内容 |
|----|------|
| **动作** | 新建 `travelogue/layout_engine/mosaic/msa_profile.py`：`build_msa_profile(assets) -> MsaProfile` |
| **规则** | 梯子容差 0.08；单峰占比 ≥0.60；否则 wide_peak_fraction；否则 mixed+clamp（ACCEPTANCE §1） |
| **验收** | AC-02/03/04 的 profile 字段 fixture |
| **估时** | 1.0d |

---

### T-MSA-03 · 轨道求解（S-MSA-02 · 白名单族）

| 项 | 内容 |
|----|------|
| **动作** | 新建 `msa_solve.py`：输入拓扑 + \(r^*\) + 面积下限 → `trackOverride`；失败 → miss |
| **M1 族** | 横主 5/6 hero、竖主 1P4L/2P3L、4-hero-sidebar（O-03 开放·会后可缩） |
| **策略** | 闭式/启发式优先；盒约束数值搜索后备；`max_iters` 等来自 cfg |
| **验收** | AC-02～05；面积/prominence 硬断言 |
| **估时** | 2.0–2.5d |

---

### T-MSA-04 · variant 各自求解（BLK-04）

| 项 | 内容 |
|----|------|
| **动作** | 对每个激活 `stage.variants` 调用 solve；写 per-variant override 或回退静态轨 + 分 variant `msa_solve_miss` |
| **铁律** | 禁止只解 web 16:9 |
| **验收** | AC-MSA-05v |
| **估时** | 0.5–1.0d |

---

### T-MSA-05 · 持久化实例 + 渲染接线（BLK-02 · S-MSA-05）

| 项 | 内容 |
|----|------|
| **动作** | solidify / builders / lte_adapter：写入 `layoutGeometry.trackOverride`、`slots[].fit`、`displayAspect`；render/export **只读复用**；禁止改仓库静态 YAML |
| **验收** | AC-MSA-05p；同窗 preview=export fixture |
| **估时** | 1.5d |

---

### T-MSA-06 · 父开关基线一致（AC-01）

| 项 | 内容 |
|----|------|
| **动作** | compose 路径：`enabled=false` 时零侵入（不写 override、不改 fit）；固定 corpus 字节级或逐屏字段一致 |
| **验收** | AC-MSA-01 |
| **估时** | 0.5d |

---

### T-MSA-07 · raw 日志字段（BLK-08）

| 项 | 内容 |
|----|------|
| **动作** | `mosaic/log.py`：扩展 D-MSA-10 字段；PR-A 可先填 profile/track/outcome，cropRisk/whitespace 可占位至 PR-B |
| **铁律** | AC 断言 raw capture |
| **验收** | AC-MSA-08 字段存在性（PR-A 子集）· PR-B 补齐 |
| **估时** | 0.5d |

---

### T-MSA-08 · 单测包 `test_msa_pr_a.py`

| 项 | 内容 |
|----|------|
| **动作** | 合成：6×3:2 · 6×4:3 · 混峰 · solve miss · variant · parent-off |
| **验收** | AC-01～05 / 05v / 05p |
| **估时** | 1.0d |

---

## 4. 任务卡 · PR-B / PR-C（大纲）

| ID | 动作 | 退出 |
|----|------|------|
| **T-MSA-10** | crop_risk 代理 + contain 门 + whitespace 预算 | AC-06 |
| **T-MSA-11** | contain 杂志纸色（BLK-06 视觉签核后合码） | AC-06v |
| **T-MSA-12** | 分配精修：最扁辅槽保护 | AC-07 |
| **T-MSA-13** | 评分项：aspect_fit / crop_risk_penalty / whitespace_penalty | 可开关 |
| **T-MSA-14** | 日志补齐 cropRisk[] / whitespaceRatio | AC-08 全量 |
| **T-MSA-20** | `msa-local-dogfood-GUIDE` + A/B/C 截图清单 | AC-09 |
| **T-MSA-21** | MTSO×MSA 开关矩阵回归 | AC-10 |
| **T-MSA-22** | 盲评记录 + 默认 on 决策（O-05） | AC-11 |

---

## 5. 触点清单

| 触点 | PR |
|------|-----|
| `travelogue/config/mosaic.py` | A |
| `travelogue/layout_engine/mosaic/msa_profile.py`（新） | A |
| `travelogue/layout_engine/mosaic/msa_solve.py`（新） | A |
| `compose.py` / `builders.py` / `lte_adapter.py` | A |
| `travelogue/render/*` | A/B |
| `travelogue/layout_engine/mosaic/log.py` | A/B |
| `tests/unit/layout_engine/test_msa_*.py` | A/B |
| `docs/config-msa-dogfood.example.yaml` | A |
| `docs/acceptance-records/msa-local-dogfood-GUIDE.md` | C |

---

## 6. 风险与回滚（实施）

| 风险 | 缓解 |
|------|------|
| 求解抖动 | 权重盒 + 同窗缓存；失败回退静态 |
| 长图丢 override | 持久化 + 单路径 render/export |
| 只修 web | T-04 / AC-05v |
| 与 MTSO 搅合 | 分字段 · AC-10 · 分文档 |

**回滚**：`slot_adaptation.enabled=false` →（可选）清 screen override → **保持 MTSO/P21 不变**。

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | M0 拆文：PR-A 任务卡详述 · PR-B/C 大纲 · 对齐 BLK-MSA-05 |
