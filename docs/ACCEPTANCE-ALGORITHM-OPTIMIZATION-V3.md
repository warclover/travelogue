# ACCEPTANCE · 算法与布局管线优化 V3（ALG-V3）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-ALGORITHM-OPTIMIZATION-V3.md](./PRD-ALGORITHM-OPTIMIZATION-V3.md) **v0.3.2** |
| **评审纪要** | [acceptance-records/algorithm-v3-prd-review-2026-08-01.md](./acceptance-records/algorithm-v3-prd-review-2026-08-01.md) |
| **实施清单** | [IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md](./IMPLEMENTATION-ALGORITHM-OPTIMIZATION-V3.md) |
| **Must-green** | [acceptance-records/alg3-must-green-nodeids.txt](./acceptance-records/alg3-must-green-nodeids.txt) |
| **产品锁** | [acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md](./acceptance-records/alg3-product-lock-a5-c4-fc-portrait-2026-08-02.md) **已锁** |
| **结案** | [acceptance-records/alg3-v3-wave-closeout-2026-08-02.md](./acceptance-records/alg3-v3-wave-closeout-2026-08-02.md) |
| **状态** | **Done · 本波关闭**（W0～W3 · 产品锁 · W1b Pass · A4 Pass 持平·不抬默认） |
| **更新日期** | 2026-08-02 |

> **验收原则（承 PRD §10.4 / X01～X10）**
>
> 1. 默认路径不成片意图（W0 / W1a-1 / W1a-2）；成片变更仅从 W1b 起，须基线 JSON + 盲评。  
> 2. 性能门用**计数探针**（`buildScreenCalls`），禁用远程 CI 绝对毫秒。  
> 3. Ready 探测**只读**；NAS 期默认可达面零 outbound LLM。  
> 4. 任何新增/改型开关必须同 PR 重签 CSC 基线（AC-32）。  
> 5. AC-21 **不得**在字段白名单未定义时判绿（本节 §2 已钉死）。

---

## 1. 里程碑 × AC 门禁

| 里程碑 | 波次 | 必须绿 | 备注 |
|--------|------|--------|------|
| **M0** | 文档 | 本文 + IMPL + must-green 指针 + §2 白名单 | 本文件交付即关闭 |
| **M0.5** | **W0 挡门** | AC-30 · AC-31 · **AC-32** · **AC-07**（探测合同落地）· **FE-ALG3-05** · `buildScreenCalls` 基线冻结 | **不做完禁止合 W1a-2** |
| **M1a** | **W1a-1 性能** | **AC-20** · **AC-21** | 零新配置键；零成片意图 |
| **M1c** | **W1a-2 合同** | AC-01/02/04/05a/**06**/07/22/30/32 · FE-ALG3-01/02/04 | 默认路径 chapters **字节级一致**（相对合入前） |
| **M1b** | W1b | AC-10 · funnel · 盲评问1/3 · FE-ALG3-S03 | **明确成片变更** |
| **M2+** | W2/W3 | AC-11/12 · 四问 · scorer_version | 见 PRD §6 |

---

## 2. AC-21 字段白名单（W0 已定义 · 不得空指针）

> **问题**：PRD AC-21 要求「`patternId`+`slots` 剔除字段白名单后等价」，但未列白名单 → 无法判绿。  
> **证据**：现有 mosaic golden（`tests/_golden/mosaic-*/expected.layout.json`）只冻结 `patternId` + `slotAssetIds`；`displayAspect`/`rect`/`layoutGeometry` 由 `solidify_screen_geometry` / MSA 后写，属派生或遥测。

### 2.1 等价投影（**必须一致**）

对每趟产出的 `trip.chapters[*].screens[*]`，按章序、屏序投影为：

```json
{
  "patternId": "<string>",
  "slotAssetIds": ["<assetId>", "..."]
}
```

当 slot 上存在非空 `role` 时，**附加**同序 `slotRoles: [role|null, ...]`（缺省角色填 `null`，长度必须等于 `slotAssetIds`）。

> **判定**：投影后的 JSON（稳定序列化：键序固定、无多余空白）与冻结基线逐屏相等。  
> **禁止**：仅同配置自反双跑冒充通过（X03）；须对照 **W0/W1a-1 前冻结的 baseline JSON** 或 **A/B 两实现**。

### 2.2 剔除字段（比较前删除 · **白名单**）

下列字段**不进入** AC-21 等价投影（即使存在于 screen/slot/log）：

| 字段 / 路径 | 理由 |
|-------------|------|
| `layoutGeometry`（整块） | 几何/MSA 遥测；默认路径 MSA 关时仍可能写入固态几何元数据，易与版式胜出正交 |
| `slots[*].rect` | solidify 派生；AC-21 核心是「谁进哪一屏」，非像素几何回归（几何另挂扩展检查） |
| `slots[*].displayAspect` | 同上；**见 §2.3 扩展检查**（不挡 AC-21 主门） |
| `slots[*].cropFocal` / `cropSafety` / `cropContain` | 人像安全裁切遥测 |
| `screenId` | 可能重编号 |
| `score` / `reasons` / `penalties` / `feature_summary` | 竞选内部态 |
| `slotAssignmentFallback` | 仅决策日志 / feature_summary；非成片结构 |
| `candidateSource` | 仅 `mosaicDecisionLog` / shadow；非成片结构 |
| `mosaicDecisionLog` / `algoV3` / `layoutSearchBudget` / timings | 摘要与漏斗；**允许** W0/W1a-2 新增，不得单独触发「版式不等价」 |
| 任意以 `_` 开头的内部键 | 调试 |

### 2.3 扩展检查（推荐同测收录 · **不替代**主门）

| 检查 | 何时 | 规则 |
|------|------|------|
| **E21-fit** | 默认配置（MSA off） | 同序 `slots[*].fit` 与基线一致（缺省视为 `"cover"`） |
| **E21-aspect** | 同上且基线屏含 `displayAspect` | 同序 `displayAspect` 绝对差 ≤ `1e-4` |
| **E21-byte-default** | **仅 W1a-2** | 默认配置下合入前后 `chapters` 经 §2.1 投影后相等；另允许对「未投影的整表」做可选字节对照（须先剥 §2.2） |

MSA / LSE 开启的语料**不**用默认 AC-21 主门；另建 cohort 夹具（W3）。

### 2.4 基线资产路径（W0 冻结 · 编码期填写哈希）

| 资产 | 路径 | 状态 |
|------|------|------|
| 版式投影基线（AC-21） | `docs/acceptance-records/alg3-ac21-layout-baseline.json` | ☑ 2026-08-01 冻结（B2a-on · `_alg3_corpus`） |
| `buildScreenCalls` 基线（AC-20） | `docs/acceptance-records/alg3-build-screen-calls-baseline.json` | ☑ 2026-08-01 冻结（W0=9 含 probe · B2a-on=8） |
| CSC happy-path 快照 | `docs/acceptance-records/csc-w0-baseline-happy-path-recipe.json` | ✅ 已有；**AC-32 改动时同 PR 更新** |
| mosaic golden（回归锚） | `tests/_golden/mosaic-*` | ✅ 已有；W1a-1 不得无故改 expected |

**`alg3-build-screen-calls-baseline.json` schema（冻结前定稿）**：

```json
{
  "schemaVersion": 1,
  "status": "frozen",
  "frozenAt": "YYYY-MM-DD",
  "corpusId": "alg3-default-mcs-v1",
  "configNote": "…",
  "windows": [{"windowKey": "…", "buildScreenCalls": 0}],
  "totalBuildScreenCalls": 0,
  "b2aOnBuildScreenCalls": 0
}
```

> **语料说明（2026-08-01 · 债务修复）**：AC-20/21 主窗仍用 `tests/unit/layout_engine/_alg3_corpus.py` 的 `_CORPUS_WINDOWS`。签名路由常把错配 SKU 滤掉，主窗 alone 可能 **0 下降**；AC-20 **必须**计入 `run_ac20_mismatch_probe`（强制 ordering + 定静几何失败）→ 冻结 **W0=9 / B2a-on=8**，CI 门为严格 `<`。
---

## 3. AC 矩阵（合同级 · nodeid 在编码期补全）

### 3.1 Capability / Surface / Ready

| ID | 断言 | 夹具要点 | 计划 nodeid / 证据 | 波次 |
|----|------|----------|-------------------|------|
| **AC-01** | 无 Key：零 outbound LLM；import 成功；无用户错误页；`ready=false`·`usedOnImport=false` | spy/mock HTTP；清 secrets | `test_alg3_w1a2_contracts.py::test_ac01_*` | W1a-2 |
| **AC-02** | 有 Key + prefer=false：import stub；`ready=true`·`usedOnImport=false`·`mayCall=false` | inject secrets + mock resolve；非 ping | `test_alg3_w1a2_contracts.py::test_ac02_*` | W1a-2 |
| **AC-03** | prefer=true 且 MayCall 允许：可走 LLM；401/超时→stub | **dark/mock**；非默认 CI | dogfood / dark job | 后置 |
| **AC-04** | Surface=off：无 AI 入口；有 Key 亦然 | NAS AC + 本回归 | 指针 [ACCEPTANCE-NO-AI-SURFACE-V1](./ACCEPTANCE-NO-AI-SURFACE-V1.md) | W1a-2 |
| **AC-05a** | decor：MayCall=false → 不实调 | 契约 | `test_alg3_w1a2_contracts.py::test_ac05a_*` | W1a-2 |
| **AC-05b** | mllm：无 VL 或 MayCall=false → skip | `supports_vision` | 待建 / W3 | 后置 |
| **AC-06** | `capability=true` 无凭证 → `ready=false` + `llm_no_key` + 导入成稿；`auto` 无凭证**不**写 `llm_no_key` | 清 secrets；auto/true 两跑 | `test_alg3_w1a2_contracts.py::test_ac06_*` | W1a-2 |
| **AC-07** | `probe_llm_ready()` 前后 `os.environ` 无差异；零网络 | environ 快照 + outbound spy | 待建（W0 可先合同测） | **W0** |

### 3.2 质量

| ID | 断言 | 夹具要点 | 波次 |
|----|------|----------|------|
| **AC-10** | 无 vision/SSG：条件 clone vs off；切条类假切条窗率相对↓≥40% 或 funnel+盲评问1≥平 | 冻结 corpus；**不得**用「SSG 已绿」代替；nodeid=`test_alg3_w1b_clone_gate.py` | W1b |
| **AC-11** | fixture 噪声比 ≤ 基线+0.03；改 HDBSCAN 消费参数须 cache fingerprint 变；死旋钮 `cluster_eps`（hdbscan 下）不改 fingerprint | meta；nodeid=`test_alg3_w2_a1_ac11.py` · 基线=`alg3-ac11-noise-baseline.json` | W2 |
| **AC-12** | Atom **实验旗** `experimental_relax` on：`atom_boundary` funnel↓≥25% 且 multi-slot share≥`mosaic_share_floor_observe`；旗默认关；**X04** 禁仅 funnel；盲评问1+2 另记 | nodeid=`test_alg3_w2_a4_atom_experimental.py`；observe floor **永不**自动 widen | W2 实验 |

### 3.3 性能 / 稳定性 / 工程

| ID | 断言 | 夹具要点 | 波次 |
|----|------|----------|------|
| **AC-20** | 固定语料 `algoV3.buildScreenCalls`（或探针等价字段）**总数**较 §2.4 基线下降且有数；CI 用计数门；墙钟 ≥10% 仅本机记录 | **禁**「拒前 build_screen ↓」自证（X08）；nodeid=`test_alg3_ac20_ac21.py::test_ac20_*` | W1a-1 |
| **AC-21** | §2.1 投影与基线逐屏等价 | 白名单=§2.2；非自反双跑；nodeid=`test_alg3_ac20_ac21.py::test_ac21_*` | W1a-1 |
| **AC-22** | scoring cohort 开 + 硬截断：`timedOut∧wallClockExceeded`；evaluations 不再增长；chapters 合法非空；**且**默认配置投影与合入前一致 | `test_alg3_ac22_wall_clock.py` | W1a-2 |
| **AC-30** | §7.1 必填键（含 `buildScreenCalls`）；无 Key / SSG empty 两场景值分化 | schema；nodeid=`test_ac30_no_key_vs_ssg_empty_values_diverge` | W0 |
| **AC-31** | §5.3 实验旗默认关；与 happy_path/CSC 单源 | 快照 | W0 |
| **AC-32** | 新增/改型开关：同 PR 更新 recipe 快照与三计数；TriState 进 `tristate_flags` 不消失；Research/Danger 集合不丢项 | `test_happy_path_recipe.py` · CSC JSON | **W0 挡门** |

### 3.4 防假绿（执行检查单）

| ID | 禁令 | 审查时问句 |
|----|------|------------|
| X01 | 禁止「import 成功」单独过 AC-01/03 | 有无 outbound spy？ |
| X02 | 禁止无 outbound spy 声称未调 LLM | 同上 |
| X03 | 禁止自反双跑冒充 AC-21 | 基线文件路径？哈希？ |
| X04 | 禁止仅 funnel↓ 过 AC-12 | 盲评？share？ |
| X05 | 禁止远程 CI 绝对毫秒过 AC-20 | 门是计数还是 ms？ |
| X06 | 禁止 default job 跑 prefer=true 真网 | CI 矩阵？ |
| X07 | 禁止摘要「键存在即过」 | 场景值是否分化？ |
| X08 | 禁止「拒前 build_screen↓」过 AC-20 | 用的是 `buildScreenCalls` 总数吗？ |
| X09 | 禁止改 baseline 后无解释过 AC-32 | PR 描述有逐键增量说明吗？ |
| X10 | 禁止无 environ 快照声称只读探测 | AC-07 证据？ |

---

## 4. FE 范围（指针 PRD §15）

| ID | 要求 | 波次 | 结果 |
|----|------|------|------|
| **FE-ALG3-01** | 禁止为 Ready/MayCall 解冻 AI 区 / Wait Tips「升级」 | 全程 | ☑ |
| **FE-ALG3-02** | 禁止向普通用户暴露 prefer/capability/clone/algoV3 营销 | 全程 | ☑ |
| **FE-ALG3-04** | prefer/capability 不进用户 PATCH 白名单；前端不加控件 | W1a-2 | ☑ |
| **FE-ALG3-05** | `mosaic_explain` 人话覆盖 PRD 所列 reason；抽屉无原始英文 reason | **W0** | ☑ |
| **FE-ALG3-S02** | 智能排版 hint「搜索可能按时长提前结束」 | W1a-2 后 / 本 PR | ☑ |
| **FE-ALG3-S03** | algorithmStale / longshotStale /「更新并导出」回归 | W1b/W2 | ☑ |
| **FE-ALG3-S04** | 「场景分析」hint / H0 与 OQ-02 对齐（默认关；禁全局自动营销） | W2 / OQ-02 | ☑ |

**OQ-02（选项 C）**：`vision.enabled` 默认 `false`；仅 `vision.cohort_trip_ids` opt-in；nodeid=`test_alg3_oq02_vision_cohort.py`。**禁止**把全局默认改成 `auto`。

---

## 5. 盲评（W1b+）

四问：1 假切条 · 2 跳戏 · 3 混拼/过碎 · 4 节奏。  
- **模板**：[alg3-blind-review-TEMPLATE.md](./acceptance-records/alg3-blind-review-TEMPLATE.md)（含 `alg3Wave` / `cloneGateOn`）  
- **亦可**复用 [ssg-blind-review-TEMPLATE.md](./acceptance-records/ssg-blind-review-TEMPLATE.md) 并手填同上字段  
- **W1b 人评**：[alg3-w1b-blind-review-2026-08-02.md](./acceptance-records/alg3-w1b-blind-review-2026-08-02.md)（**Pass** · 2026-08-02；旧链 [PENDING 跳转](./acceptance-records/alg3-w1b-blind-review-PENDING.md)）  
语料：混导密连拍、换装同地、横竖混拼、小册、无 vision 对照；含窄屏长图。

| 门 | 标准 |
|----|------|
| W1b | 问1 On≥Off；问3 混拼不差 |
| W2 | 问1+2 ≥基线；问3 不差 |
| W3 | 问4 ≥基线；streak 超阈↓ |

---

## 6. Must-green 命令

```powershell
# 回归锚（编码前即可跑；W0/W1a 合入不得无故变红）
python -m pytest (Get-Content docs/acceptance-records/alg3-must-green-nodeids.txt | Where-Object { $_ -and $_ -notmatch '^\s*#' }) -q
```

编码期新增的 `test_alg3_*.py` 合入后**追加**到 nodeids 文件（同 PR）。

---

## 7. 基线冻结检查单（W0 出口）

| # | 项 | 状态 |
|---|-----|------|
| 1 | §2 AC-21 白名单已写入本文（无需再议字段集合） | ☑ 2026-08-01 |
| 2 | `iter_flag_paths` / `tristate_flags` 设计与 AC-32 夹具写进 IMPL | ☑ 见 IMPL D5 |
| 3 | `probe_llm_ready` 只读合同与 AC-07 夹具写进 IMPL | ☑ 见 IMPL |
| 4 | FE-ALG3-05 人话表终稿（中文文案）写入 IMPL 或本文件附录 | ☑ 本文件 §8 + mosaic_explain |
| 5 | `alg3-build-screen-calls-baseline.json` 冻结 | ☑ 2026-08-01 · **W0 total=9（含 mismatch probe）· B2a-on=8** |
| 6 | `alg3-ac21-layout-baseline.json` 冻结 | ☑ 2026-08-01 · B2a-on |
| 7 | CSC 基线：若 W0 已改 recipe 结构，同 PR 更新三计数 | ☑ 现网 **174/110/64**（含 W2-A3） |

---

## 8. 附录 · FE-ALG3-05 人话目标表（文案可在 W0 PR 微调用词）

| reason 键 | 目标中文人话（草案） |
|-----------|----------------------|
| `atom_boundary` | 跨场景原子边界，不宜拼在同一窗 |
| `shot_group_cross` | 跨分镜硬边界，拼在一起会像切条 |
| `shot_group_anti_slice` | 同分镜过密，该模板易呈切条感 |
| `near_scene_clone` | 同场景过近/近似连拍，未做成切条拼图 |
| `main_ar_mismatch` | 主图画幅与主槽不匹配 |
| `sidebar_min_short_side` | 侧栏短边过窄，版式不成立 |
| `contract:mix_miss` | 横竖混排未命中可用模板合同 |
| `mixed_portrait_is_hero` | 竖图更适合主图，当前模板已排除 |

验收：上述 reason 出现在 `rejectedTemplates` 时，`build_mosaic_explain` 的 details **不得**整段回落为原始英文 `reason` 字符串。
