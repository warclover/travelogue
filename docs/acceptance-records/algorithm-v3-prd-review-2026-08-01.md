# PRD-ALGORITHM-OPTIMIZATION-V3 · 跨职能深度评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-ALGORITHM-OPTIMIZATION-V3.md](../PRD-ALGORITHM-OPTIMIZATION-V3.md)（**ALG-V3** · 管线加深 · 能力 Auto · 开关诚实） |
| **评审版本** | **v0.1.0 Draft** → Must-Fix 已回写 **v0.2.1**（含 §15 FE 同步矩阵）→ **开发负责人代码复核回写 [v0.3.0](../PRD-ALGORITHM-OPTIMIZATION-V3.md)**（DEV-01～06 · §14 证据台账 · 2026-08-01） |
| **日期** | 2026-08-01 |
| **结论** | **Conditional Go（有条件通过）** · **合同回写完成** · **代码复核完成（v0.3.0）** |
| **编码** | ☑ 文档回写 v0.3　☑ **M0 ACCEPTANCE/IMPL/must-green 已齐**　☑ **可 Kickoff W0（挡门编码）**　☑ 可 Kickoff W1a-1/W1a-2（W0 后串行合入）　☐ W1b/W2 合码（基线+盲评后）　☐ 不批默认开 scoring / decor·mllm 实调 |
| **参评角色（五席）** | 架构 · 算法 · 开发 · 测试/QA · 页面视觉/排版（拼图） |
| **评审方式** | 分席只读 PRD + **对照现网代码核查**（clustering / MCS / narrate / NAS / SearchBudget / TriState） |
| **记录人** | 五席联合纪要（跨职能模拟联评） |
| **本纪要状态** | **已结案 · Conditional Go** · 待 PRD v0.2 回写 Must-Fix |

> **相邻挡门**  
> [NAS](../PRD-NO-AI-SURFACE-V1.md) · [DLLM](../PRD-DESKTOP-LLM-SETUP-V1.md) · [AI-Return](../PRD-AI-RETURN-V1.md) · [AAD](../PRD-ARCH-ALGO-DEEPENING-V1.md) · [SSG](../PRD-SMART-SHOT-GROUPING-V1.md) · [Pipeline Perf](../PRD-PIPELINE-PERF-V1.md) · [FLOW](../FLOW-TRIPOLOGUE-PIPELINE.md)

---

## 0. 会前宣读（主持人）

1. **切口**：聚类→分镜→MCS→拼版加深 + Capability Auto；**不**推倒 MCS/SSG，**不**重开封面 V2。  
2. **产品诉求**：LLM 默认可开、无 Key 跳过；未来释放 AI 面即用。  
3. **勿重开**：NAS 用户面战略；导入默认 stub（DLLM/AIR）；PrefixBeam/LSE/TPC 默认开；AAD Utility/拆 curate 平行重写。  
4. **本场必拍**：Ready vs MayCall；vision auto；clone 条件开；AC 空指针；W1 拆分。

---

## 1. 总评（一句话）

> **五席一致 Conditional Go**：病灶与 W1 方向成立，Surface≠Capability 分层正确；但 v0.1 把「引擎 Ready」与「默认可达面可调用」混写，导致 decor/MLLM `auto` 撞 NAS「用不到」，且 B1 热路径叙事过满、墙钟未接线、Atom 自动放宽与既有 observe-only 冲突、§10 AC 多处空指针——**先回写 Must-Fix 与拆 ACCEPTANCE，再合 W1a；W1b（clone）与 W2 另列车。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **架构** | **Conditional Go** | W1 可开工；须先拆 Ready/MayCall/Import，挂 AIR，墙钟真正接线；勿与 AAD 抢所有权 |
| **算法** | **Conditional Go** | 根因大多准；B1 非默认热路径、A4 冲突 Atom PLAN；假切条 AC 须独立无 vision 语料 |
| **开发** | **Conditional Go** | 可实施；`bool("auto")` 陷阱与 CSC recipe 必挡门；性能等价与 B7 成片变更须拆 PR |
| **测试 / QA** | **Conditional Go** | 方向对；§10 仍是目标句；无 ACCEPTANCE/基线/双路径门禁前不批合码门禁 |
| **页面视觉 / 排版** | **Conditional Go** | Import stub 正确；NAS 期禁暗改文案/成片；补卷轴四问与切条作用域合同 |

**汇总**：**5/5 Conditional Go**。  
- **M0**：可 Kickoff（回写 v0.2 + 拆 ACCEPTANCE/IMPL）。  
- **W1a 合码**：BLK-01/03/04/06/07 + MF 测试挡门关闭前 **不批**「宣称零成片」的整包 W1。  
- **W1b（clone）/ W2**：另 PR；视觉双门 + 基线 JSON。  
- **不批**：NAS 期 decor/mllm 实调默认开；全局默认 `layout.scoring=true`。

### 对齐评分（席位均值 · 主观）

| 维度 | 分（/10） | 说明 |
|------|-----------|------|
| 问题→根因完整度 | **8.2** | P-ALG3-01～08 大体钉住；P-04/06 需修正表述 |
| 与 NAS·DLLM·AAD·SSG 边界 | **6.0** | Surface≠Capability 对，但 Call 权未收紧；AIR/AAD 邻接弱 |
| 工程可开工性 | **7.3** | W0/W1a 清楚；TriState/CSC/墙钟接线欠合同 |
| AC 可测性 / 防假绿 | **5.0** | 空指针多；缺基线与双路径 |
| 拼图 / 卷轴可签核性 | **6.5** | clone 条件开正确；缺盲评四问与节奏门 |

---

## 3. 事实核查（代码核对）

| # | PRD / 假设 | 代码事实 | 会中 |
|---|------------|----------|------|
| **F-01** | HDBSCAN 不消费 `cluster_eps` | `_cluster_labels` 仅 DBSCAN 用 `eps` | ✅ 属实 |
| **F-02** | Import 强制 stub | `resolve_studio_narrate_provider` 恒 `"stub"`；已有 `…_if_ready` 未挂 import | ✅ 属实（可复用 if_ready） |
| **F-03** | NAS Surface 默认 off | `ai_surface_enabled=False`；env dark；PATCH 不能开 Surface | ✅ 属实 |
| **F-04** | clone 硬门默认关 | `NearSceneCloneGateConfig.enabled=False`；软罚仍在 | ✅ 属实 |
| **F-05** | soft-split 固定 6h | `time_soft_split_hours=6.0` | ✅ 属实 |
| **F-06** | scoring 开时墙钟虚设 | `wall_clock_limits_output=False` 且 **LayoutScoringConfig 无该字段、调用方永不传入** | ✅ 属实，**比 PRD 更严重** |
| **F-07** | 每候选重建 `quality_pool` | 仅 `lse_quality_unified=True` 路径；**默认 False** | ⚠ **修正叙事** |
| **F-08** | decor 代码 false / example true | `NarrativeConfig=False`；example L653=`true` | ✅ 属实 |
| **F-09** | Atom observe-only 不自动放宽 | PLAN/注释：`mosaic_share_floor_observe` 永不自动 widen | ⚠ A4 与既有合同冲突 |
| **F-10** | C3「有 mosaic 才枚举 no_mosaic」 | `layout_candidates` **已部分实现** | ⚠ 勿写成新发明 |
| **F-11** | `bool("auto")` 风险 | 现 loader 对 decor/mllm 用 `bool(...)` | ✅ **开发挡门** |
| **F-12** | As-Is stage 表 | 另有 `shot_grouping` / lock / G1 | ⚠ 简化可接受，实施勿漏 |

---

## 4. Must-Fix（BLK · 未关闭不批对应合码）

| ID | 挡门 | 内容 | 建议改法 |
|----|------|------|----------|
| **BLK-01** | M0 / Capability | Ready / MayCall / Import 三态未分；decor·mllm `auto` 撞 NAS「用不到」 | 拆：**Ready**=探测写摘要；**MayCall**=Surface∨dark∨显式旗；**Import**=prefer。NAS 默认 MayCall=false，decor/mllm **不实调** |
| **BLK-02** | M0 / 释放面 | 未挂 [PRD-AI-RETURN-V1](../PRD-AI-RETURN-V1.md)，自建「释放列车」双源 | M4=AIR 前置；ALG-V3 只保证 Ready+摘要 |
| **BLK-03** | W1 · C1 | 墙钟无配置键、未贯通 `SearchBudget` | W0 加键 → loader → `layout_search`/`compose_trip`；AC 断言停扩展 |
| **BLK-04** | W1 · B1 / AC-20 | 默认热路径叙事不诚实 | B1 标 LSE-on；默认路径改以 **拒前 build_screen 早拒** 为主增益；AC-20 分配置报表 |
| **BLK-05** | W3/W4 | D4/B5 抢 AAD-10/21 | 书面所有权：Utility/拆 curate=AAD；ALG-V3 只提接口/观测 |
| **BLK-06** | W0 配置 | bool→TriState + example 真开 | 统一 `normalize_tri_state`；example 先对齐 **false**；CSC/recipe/algorithm_profile 同步 |
| **BLK-07** | W1 拆分 | 性能等价与 B7 成片变更同包 | **W1a**（Ready+性能+C1）/ **W1b**（条件 clone）分 PR |
| **BLK-08** | W2 · A4 | Atom 自动放宽 vs observe-only | 默认禁止自动 widen；仅显式实验旗 + 视觉双门 |
| **BLK-09** | M0 测试 | §10 空指针；无 ACCEPTANCE | 拆 ACCEPTANCE；MF 见下；无基线不批 W1b/W2 质量门 |
| **BLK-10** | 视觉合同 | 缺 NAS 静默 / 切条作用域 / 盲评四问 | 增补 VC-ALG3-01～05（见视觉席） |

### 测试 Must-Fix（并入 BLK-09）

| ID | 要求 |
|----|------|
| **MF-T01** | AC-01/03/10/12/20 禁止仅「成功/下降/不差」 |
| **MF-T02** | M0 入库假切条基线 / MCS 探针 / clustering noise 基线 |
| **MF-T03** | CI 双 job：无 Key 默认面 × inject secrets+mock（零真网） |
| **MF-T04** | `llm.ready`=可解析 ≠ ping ok；书面冻结 |
| **MF-T05** | B7：`cloneGateEffective` + reject_funnel 硬可见 |
| **MF-T06** | AC-21 剔除字段集冻结（对齐 AAD） |
| **MF-T07** | AC-31 与 happy_path/CSC 单源 |
| **MF-T08** | 防假绿禁令 X01–X07 写入 ACCEPTANCE |

---

## 5. Should-Fix（不挡 M0，建议 v0.2 写入）

1. 正文锚到 `resolve_studio_narrate_provider_if_ready`。  
2. 分清 Atom 门 vs clone 门拒因。  
3. P-ALG3-06 改为「二次编码/逐张 look」，W2 加 look batch。  
4. C3 改为「已部分落地；W3 剪 always-on beam 变体」。  
5. `template_experiments` 默认表述与代码 cohort 对齐。  
6. AC-01：NAS 默认不调用时用 `ready=false`，勿每次堆 `llm_not_ready` 噪声。  
7. 节奏 streak 进仪表（视觉 Should）；W3 前至少 log。  
8. OQ-02「仅 fine_craft」须定义 preset/入口否则不可执行。  
9. vision auto 与 Pipeline Perf 共用首跑/大册 P95 退出门。  
10. FLOW As-Is 补 lock/G1 以免实施漏 stage。

---

## 6. 对决策与 OQ 的五席立场（汇总）

| ID | 共识建议 | 备注 |
|----|----------|------|
| **D-ALG3-01** | **赞成（修）** | 复用现有 `TriState`，勿平行枚举 |
| **D-ALG3-02** | **赞成** | 与 `studio_llm_status` 同源；禁 import ping |
| **D-ALG3-03** | **有条件赞成** | Surface≠**Ready** 成立；NAS 期 Surface≠**Call** |
| **D-ALG3-04** | **强烈赞成** | prefer 默认 false；导入 stub |
| **D-ALG3-05** | **赞成** | fail-open；不进用户错误页 |
| **OQ-01** | **A** | NAS 期 import 不自动 LLM |
| **OQ-02** | **C→再 A**（架构/开发）或 **A Conditional**（算法/视觉） | 本波不全局默认 auto；先 cohort/fine_craft 或抬 autoMinPhotos |
| **OQ-03** | **A** | SSG off/empty 或 vision 降级时条件开 |
| **OQ-04** | **A**（或内部 B） | 本波不默认开 scoring |
| **OQ-05** | 文本 Key≠VL；不能则 skip | 禁止「有 DeepSeek 就调 MLLM」 |
| **OQ-06** | **后置 = AIR** | 非 ALG-V3 DoD |

### §5.4 T1–T6 评审勾选建议

| 项 | 建议 |
|----|------|
| **T1** Capability Auto + import stub | **Go**（含 BLK-01 收紧） |
| **T2** vision→auto | **Conditional**（先 C/cohort） |
| **T3** 无 SSG 自动 clone 硬门 | **Go**（W1b） |
| **T4** scoring 本波不默认开 | **Go** |
| **T5** decor/mllm→auto | **改**：Ready 可 auto；**MayCall 默认 false**；example 先对齐 false |
| **T6** 释放 AI 面清单 | **改挂 AIR**，非本算法列车交付 |

---

## 7. 视觉合同（须回写 PRD）

| ID | 条文 |
|----|------|
| **VC-ALG3-01** | 切条作用域：跨组硬拒仅切条/假一条类；合法混拼可跨组（软约束）— 回引 D-SSG-05/17/21 |
| **VC-ALG3-02** | NAS 静默：Surface=off 时 Capability 不改变默认可达**文案与版式胜出**；允许 Ready 摘要 |
| **VC-ALG3-03** | Atom/soft-split 放宽须同时过假切条+跳戏盲评（双门） |
| **VC-ALG3-04** | 连续同模板超阈为质量回归项 |
| **VC-ALG3-05** | 本波禁止因算法增强改 Wait Tips / FirstSuccess / Help 的 AI 话术 |

**盲评四问**：假切条 · 跳戏 · 混拼/过碎 · 节奏。  
**本波**：不需要新线框/COPY 冻结表；释放面时再解冻。

---

## 8. 可 Kickoff / 勿 Kickoff

### 可 Kickoff（M0 回写后）

1. **W0**：algoV3 摘要 schema、`llmReady`/`usedOnImport`、reject funnel、TriState 兼容、example↔代码 decor **false**、防假绿禁令  
2. **W1a**：B2/B3 早拒与去双算、B6 self-heal 限次、C1 墙钟**接线**（scoring 仍默认关）、Capability **Ready**（prefer=false）、snapshot A/B  
3. **观测**：`cluster_noise_ratio`、atom 拒因进 meta（先观察）  
4. **A1 低风险**：旋钮诚实或删死旋钮 + cache fingerprint（单测护栏）

### 勿本波 Kickoff / 另列车

- decor/mllm **实调**默认 auto（未过 BLK-01）  
- 全局 `vision.enabled=auto`（未过 OQ-02）  
- 默认开 `layout.scoring` / PrefixBeam / LSE / TPC  
- A4 Atom 自动放宽  
- W3 惩罚饱和（待 AAD Utility 边界）  
- W4 拆 `run_curate`（归 AAD）  
- 释放 AI 面 UI/COPY（归 AIR）

---

## 9. 里程碑重钉（相对 v0.1）

| 里程碑 | 内容 | Go |
|--------|------|-----|
| **M0** | PRD→v0.2 · ACCEPTANCE/IMPL · OQ/T 拍板 · BLK 回写 | 本文 §4/§6 |
| **M1** | W0+W1a | AC-01/02/04/20计数/21/22/30/31；零成片意图 |
| **M1b** | W1b 条件 clone | AC-10 基线+漏斗+盲评问1/3 |
| **M2** | W2 上游（无自动 widen Atom） | AC-11；vision 决策落地 |
| **M3** | W3 flag+holdback | 四问+scorer_version |
| **M4** | AIR 释放面 | 非 ALG-V3 DoD |

---

## 10. 开发 API 草图（评审采纳方向）

```text
capability_allows(flag: TriState, ready: bool) -> bool
resolve_studio_narrate_provider:
  stub if force_stub ∨ ¬capability_allows ∨ ¬prefer_llm_when_ready
  else resolved provider   # ≡ 今日 if_ready
decor/mllm: MayCall 闸 +（mllm）supports_vision；禁 bool("auto")
prefer_llm_when_ready / capability：默认不进用户 PATCH 白名单
```

人日粗估（开发席）：W0 **4–6**；W1 全包含 B7 **8–12**（宜拆）；W2 **10–15**。

---

## 11. 开放问题（需产品书面拍板）

| ID | 问题 | 评审建议 |
|----|------|----------|
| OQ-01 | NAS 期 import 自动 LLM？ | **A 否** |
| OQ-02 | vision 默认 auto？ | **先 C/cohort，再议 A** |
| OQ-03 | clone 门条件 vs 全局？ | **A 条件** |
| OQ-04 | 本波开 scoring？ | **A 否** |
| OQ-05 | MLLM 凭证模型 | **VL 能力探测，否则 skip** |
| OQ-06 | 释放面是否本列车？ | **后置 AIR** |

另：**T5** 是否接受「Ready=auto、MayCall=false」修正案？ → 五席建议 **接受**。

---

## 12. 修订动作（会后）

- [x] PRD 升 **v0.2.0**：回写 BLK-01～10、VC-ALG3、W1a/W1b、热路径修正、挂 AIR/AAD 所有权  
- [x] PRD 升 **v0.2.1**：增补 §15 FE 同步矩阵  
- [x] PRD 升 **v0.3.0**（开发负责人代码复核 · DEV-01～06）：新增 §14 证据台账；D5 + AC-32 开关清单挡门；`probe_llm_ready()` 只读 + AC-07；§3.2.1 capability 真值表 + AC-06；MCS 重定位（删 B3 / 拆 B2a·B2b / B1 降 W3）+ AC-20 改口径 + X08～X10；W1a 拆 W1a-1/W1a-2；explain 人话升 Must FE-ALG3-05  
- [x] 拆 `ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md`（**AC-21 字段白名单已钉 · §2**）+ `alg3-must-green-nodeids.txt`（collect-only 79）  
- [x] 拆 `IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md`（**W0 挡门优先**，再 W1a-1/W1a-2）  
- [x] 基线占位：`alg3-build-screen-calls-baseline.json` · `alg3-ac21-layout-baseline.json`（`pending_freeze`，编码 W0/W1a-1 回填）  
- [x] 更新 PRD 头表「评审纪要」链接本文  
- [ ] （可选）DOC-STATUS / README 索引  
- [ ] **授权开工 W0 编码**（`feat/alg-v3-w0`）

### 12.1 v0.3.0 代码复核的三条硬结论（供 QA 排期参考）

1. **W0 是挡门，不是暖场**：`iter_bool_paths` 只认 `bool`，C1 新增 bool 或 decor/mllm 转 TriState 都会打穿 `test_bool_counts_match_prd_diagnostic_band`（写死 151/97/54）与 CSC 基线快照。D5 不先落，W1a-2 合入即红。
2. **原 B3 是空包，B1/B2b 不在默认路径**：`compose.pick_best_window` 早已在打分前跳过 `hard_valid=False`；`lse_quality_unified` / `lse_hungarian_assignment` 默认均 `False`。默认路径唯一有量级的性能点是新增静态几何预检（B2a）。
3. **`mosaic_explain` 原文外泄是存量线上缺陷**：SSG 已在默认路径产出 `shot_group_cross` 等 reason，而 `_REJECT_LABELS` 无对应人话，兜底直出英文。与 W1b 无关，W0 必修。  
- [ ] 产品书面确认 §11 OQ / §5.4 T（默认可沿用评审建议） 

---

## 13. 分席详细意见索引

本纪要已吸收五席完整意见。分席原文由评审代理产出，要点已并入 §2–§10；落地以本文 BLK/MF/VC 与产品 OQ 拍板为准。

| 席位 | 代理会话 |
|------|----------|
| 架构 | [架构席评审](3121b37b-c4c9-4377-9337-9f5282215dae) |
| 算法 | [算法席评审](1a4932e7-4d32-4144-90d0-b7cbde35ef75) |
| 开发 | [开发席评审](346978d5-45df-400a-a193-daead47bad4a) |
| 测试 | [测试席评审](53fc813c-8347-416c-87e6-1b6f992099da) |
| 视觉 | [视觉席评审](8ceee84c-8f2c-4427-afbb-809c7804206e) |

---

**一句话收口**：把 ALG-V3 收成「MCS/聚类加深 + 开关诚实 + **就绪探测**」；把「有 Key 就改用户可见结果」严格留给 Surface/AIR/dark——修完 BLK 后 **W1a 可立刻开工**。
