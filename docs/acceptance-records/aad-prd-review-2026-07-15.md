# PRD-ARCH-ALGO-DEEPENING-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-ARCH-ALGO-DEEPENING-V1.md](../PRD-ARCH-ALGO-DEEPENING-V1.md) |
| **评审版本** | v1.0.0-AAD |
| **日期** | 2026-07-15 |
| **结论** | **有条件通过** → 阻塞项合入 **v1.1.0-AAD** 后方可 Kickoff |
| **参评角色** | 产品 · 测试 · 前后端开发 · 算法 · 架构 |
| **评审方式** | 分席只读评审（对照产线代码 / 既有 PRD / 门禁脚本） |

---

## 1. 全场共识

1. **方向正确**：WS1 后做「基线 → 可改性 → 搜索加深」；OUT 表与 Stable-QH / LCC / FTUE / Algorithm V2 边界清楚。  
2. **「伪 beam」诊断成立**：现行是 VariantRerank（完整贪心计划变体），不是前缀搜索。  
3. **必须分账**：WS-A/B = 工程可信与可改；WS-C = 唯一对外成册质量故事；**默认关合入**，Gate-Q 后再议默认开。  
4. **禁止混入**：模板商城、LSE 上量、拆 ingest、清 media→curation ignore、体验债（QH/LCC/FTUE）。  
5. **Kickoff 前必须消 B0**：公式/章窗分层、CLI 合同范围、等价与 holdback 可测性、边数叙事、WIP 容量——见 §3。

---

## 2. 总体结论（分席）

| 席位 | 结论 | 一句话 |
|------|------|--------|
| **产品** | 有条件通过 | 范围对齐；须补成册收益叙事与盲评产品化，禁止用户面黑话 |
| **测试** | 有条件通过 | WS-A 可测；AC-04/等价脚本语义/holdback/CI 挂名不挂实须重写 |
| **开发** | 有条件通过 | 断言大多准；CLI 只改 cluster 写窄；Utility 须对齐现网；M2 估时偏紧 |
| **算法** | 有条件通过 | WS-A/B 可开；WS-C 须先冻 `(1−w·p)` + 章窗分层；Geo 建议 Parking |
| **架构** | 有条件通过 | 承接 P2-A/ADR-015 对；ADR 链接错；18→≤10 与棘轮 ceiling 须拆开；WIP 对 FTUE |

**汇总**：**有条件通过**。合入下方 BLK 至 PRD **v1.1.0** 并勾选 Kickoff 清单后，方可开工（建议先 M1，再按 WIP 切片）。

---

## 3. 阻塞项（B0 · 必合入 v1.1）

| ID | 议题 | 来源 | 要求 |
|----|------|------|------|
| **BLK-01** | LayoutUtility 公式与章/窗分层 | 算法 / 开发 | 冻结 `utility = soft × Π(1 − clamp(w)·clamp(p))`；**窗级**硬惩罚选屏，**章级** soft 仅跨屏维，硬罚作准入/诊断默认**不进**章级 Π；soft=`clamp01(score_screen_plan.total)` 或书面替代；列 core Π vs post_multipliers |
| **BLK-02** | CLI 路径合同范围 | 开发 / 架构 / 测试 | 不止 `cluster.py`：含 `_helpers._resolve`；冻结「Option 默认 `None`=宽松，显式 `--trips-dir`=沙箱」；pipeline 默认 `Path("trips")` 语义 Kickoff 拍板；AC-03 补自动化负例；Studio/HTTP **永不**走宽松支 |
| **BLK-03** | 等价门禁语义 | 测试 | AC-AAD-12 不得把「自反全绿」写成行为等价；WS-B 用 **curate baseline replay / golden 签名 A/B**；自反仅确定性烟测 |
| **BLK-04** | AC-AAD-04 可执行化 | 测试 | 删除「失败类」空话；改为三目录全绿 **或** must-green nodeids 钉死 |
| **BLK-05** | Holdback 产品+科学协议 | 产品 / 算法 / 测试 | 成册维度卡 + 否决样例；N≥8 且多样性约束（算法建议 N≥12 / ≥3 人或破平）；**平局≠默认开 Go**；记录 schema + acceptance-record 路径；用户面禁用 PrefixBeam 等黑话 |
| **BLK-06** | 边数 18→≤10 叙事与棘轮 | 架构 | As-Is **18**（shim 显式化）→ goal **≤10**；棘轮 ceiling=baseline（只降不升）≠ goal；修 ADR-015 链接为 `015-lse-planner-migration.md`；不重开 M-B4b |
| **BLK-07** | `layout_contract` 准入 | 架构 / 算法 | kernel **仅** `combine_utility` + DTO；soft/硬罚实现留 `layout_engine`；挂 `lint_layout_contract_surface` |
| **BLK-08** | Geo 与审美范围 | 算法 / 产品 | **AAD-23 Geo 联合切分 → Parking**（本波不做默认开/调参）；AAD-22 降为 **lint/allowlist**，不新建 facade |
| **BLK-09** | PrefixBeam 状态键 | 算法 | M0 冻结完整状态元组（含 rhythm 配额字段、streak、chapter/hero、剩余后缀）；增量缓存键与前缀一致 |
| **BLK-10** | WIP / FTUE 容量 | 架构 / 产品 | 写入 G-AAD-WIP；与 FTUE 冲突时体验债优先；默认可先交付 M1+M2(+M3) 切片 |
| **BLK-11** | 产品成功指标分账 | 产品 | 对外成功=成册收益+holdback；边数/壳行数=工程闸门，不作对外故事 |
| **BLK-12** | CI / 剔除字段 / M2 估时 | 测试 / 开发 | 冻 AC-20 剔除字段集；写清哪些 AC 挡 PR；M2 估时改为 **5–8d** 或放宽「壳」度量口径 |

---

## 4. 重要改进（建议 v1.1 写入，不单独阻塞纪要）

1. 成册收益 3～5 条白话（少连续同构屏、脸裁/主槽更稳等）。  
2. M4→M5 顺序锁定；Utility 与 Beam **默认分 PR**。  
3. cur→LE 白名单：优先经 adapter；M3 可分 18→14→≤10。  
4. decisionLog：保留 `score`，新增 `utility`（Q-03）。  
5. AAD-13 media/vision ignore：**Parking**（Q-04）。  
6. PrefixBeam 默认开：另 PR + 白话 release note（Q-01）。  
7. Studio 可不暴露 flag（CLI/config 即可）；若 dogfood 要开关再 expose。  
8. 附录命令补入 QUALITY-GATE / quality_gate 列表（实施期）。

---

## 5. 建议后置（Parking / 不进本波 DoD）

- Geo 联合切分与 α/β 网格（AAD-23）  
- 审美新 facade（仅 lint）  
- AAD-13 清 ignore_imports  
- PrefixBeam **默认开启**  
- preference 学习闭环、场景预设、真 DP、拆 ingest  
- 整本 layout 盲评全自动 harness（本波可人工+模板）

---

## 6. Kickoff 开放题 · 投票汇总

| 题 | 汇总 | 定案（v1.1） |
|----|------|----------------|
| **Q-01** 默认开时机 | 五席同意本波默认关 | **维持**；默认开另 PR |
| **Q-02** holdback N | 产品要多样性；算法要 N↑/人数↑；测试要可冻结清单 | **N≥8 + 多样性约束**；评委开发1+产品1，**平局须第三人破平或记「不劣但不开默认」**；默认开另议 |
| **Q-03** decisionLog | 开发同意 score+utility | **定案**：保留 `score`，加 `utility` |
| **Q-04** AAD-13 | 架构/开发/算法 Parking | **定案 Parking** |
| **Q-05** Geo α/β | 产品/算法反对本波网格 | **定案**：Geo **Parking**；Q-05 关闭 |
| **Q-00**（新增）Utility 公式 | 算法/开发 B0 | **定案**：`(1−w·p)` + 章窗分层（BLK-01） |
| **Q-06**（新增）CLI Option 默认 | 开发 B0 | **定案**：默认 `None`=宽松；显式才沙箱；id 用 ctx 根但不注入 `resolve` 的 `trips_dir` |

---

## 7. 分席要点摘录

### 产品
- 怕「12–20 人日用户零感」；包装三句话：非新功能面 / 两本账 / 对外只讲成册结果。  
- Gate-Q 不过 → 默认永关，用户零成本。

### 测试
- `arch_equivalence_check` 今日=同配置自反；挂名验不了拆分等价。  
- M2/M7 测试成本低估；AC-04 不可操作。

### 开发
- `_helpers._resolve` 与 pipeline 默认 `Path("trips")` 同类沙箱误伤。  
- 现网 mosaic 已是 `1−w·p`；PRD 无权重版会炸 golden。  
- `run_curate` ~755 行；壳 ≤80 可行，3–5d 偏紧。

### 算法
- 章级再乘硬罚=双重计数。  
- 状态键过瘦 → 搜爆或假降级。  
- 审美 facade 与既有 `purpose_overall` 重复。

### 架构
- ADR-015 文件名纠错；TECH-ARCH「7 边」过时。  
- 宽松 CLI ≠ SSRF，但是本地任意 trip.json；Studio 不变量必须 AC。  
- LayoutUtility 整段打分不得进 kernel。

---

## 8. 修订后 Kickoff 门槛

- [ ] PRD 升 **v1.1.0-AAD** 并消化 BLK-01～12  
- [ ] 冻结：CLI 三态、Utility 公式、状态键、AC-04/20、holdback 清单  
- [ ] 书面 WIP：与 FTUE 串行或砍至 M1+(M2|M4)  
- [ ] 架构/算法/测试三方勾选 Ready for Kickoff  

---

## 9. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-15 | 五席评审；结论有条件通过；阻塞项交 v1.1 |
