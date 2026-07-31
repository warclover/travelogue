# 拼图聚类升级方案 · Cluster-Boundary-First V1（已审定稿）

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-31 |
| 状态 | **已审定稿 · 实现中**（分支 `feat/cluster-boundary-first-v1`） |
| 实现 | W0–W2 统一门 + page packs；默认 `atom.enabled=false`；狗粮见 [config-cluster-boundary-first-dogfood.example.yaml](./config-cluster-boundary-first-dogfood.example.yaml)。**W3 look 未做**。 |
| 评审 | [REVIEW-CLUSTER-BOUNDARY-FIRST-MOSAIC-V1-2026-07-31.md](./REVIEW-CLUSTER-BOUNDARY-FIRST-MOSAIC-V1-2026-07-31.md) · 总裁决：**有条件通过**（条件已并入本文 §3 / §9） |
| 目标 | 让拼图选片稳定输出 **80 分**：大部分屏在逻辑上说得通，杜绝明显跨界混装 |
| 证据 | [MCS vs 人类代理对照](./acceptance-records/mcs-vs-human-proxy-clusters-demo-49cbe46479-2026-07-31.md) · [人工 11 例标注](./acceptance-records/mcs-human-cluster-labels-demo-49cbe46479-2026-07-31.json) |
| 关联 | [MTSO 狗粮指南](./acceptance-records/mtso-local-dogfood-GUIDE.md) · PRD-SMART-SHOT-GROUPING-V1 |

---

## 0. TL;DR

1. 本轮 11 例人工标注 **全部是聚类边界错**，没有一例是「缺模板」。
2. 实测发现 **SSG 跨 shotGroup 硬拒当前不生效**（配置对象传错，`MosaicConfig` 没有 `shot_grouping`），等于产品一直在裸奔。
3. 更大的漏洞在 **非 MCS 路径**：本册 61 次 MCS 决策只有 5 次成窗，绝大多数 `portrait-3 / landscape-3 / portrait-2` 由 legacy / 尾部合并产出，**完全不过任何簇门**。
4. 方案主张：**先修边界，再谈模板与权重**；接受「合并不足」，不接受「跨界混装」。
5. 验收从「像不像唯一正确拼法」改为 **脏屏数 / 灾难屏 / 碎度护栏**，配 11 例回归（合并类不加 Go）。
6. **审定修正**：Scene Atom **不强制**同 `sceneClusterId`（改半硬）；类别跳变 W1 软；稀缺模板去掉 300s hard；W1 暂关三列等分实验默认曝光；**#11 为已知残差**（等 look）。

---

## 1. 现状实测（demo-49cbe46479）

### 1.1 三条产屏路径，只有一条有簇门

| 路径 | 产出示例 | 是否过 SSG 簇门 |
|------|----------|----------------|
| MCS 窗口（`mosaic/candidates.py`） | bookends、3P2L、landscape-4 | 代码里有，**实际失效**（见 1.2） |
| Legacy 章内规划（`planner/screen_planner_stages.py`） | portrait-3、landscape-3-asym、portrait-2 | **无** |
| 尾部/carry 合并（`planner/screen_planner_attach.py`） | 零散竖图凑 2–3 张 | **无** |

本册 `mosaicDecisionLog`：`events=61 · winners=5 · fallbacks=56`。也就是说 **用户看到的绝大多数拼图不由 MCS 决定**，只给 MCS 加约束收益有限。

### 1.2 P0 缺陷：跨组硬拒是死代码

`candidates.py` 调用：

```
ssg_cross_group_hard_reject_active(cfg)   # cfg 是 MosaicConfig
```

而 `shot_group_gate.ssg_hard_reject_active` 读的是 `cfg.shot_grouping`（属于 `AppConfig`）。本机实测：

- `hasattr(MosaicConfig, 'shot_grouping') == False`
- `ssg_cross_group_hard_reject_active(cfg.mosaic) == False`
- `ssg_cross_group_hard_reject_active(app_cfg) == True`

结论：**D-SSG-05/21/22 的两个硬拒（跨组 + 同组假切条）从未在真实排版中触发**。它「静默 fail-close 成不生效」，且不打日志，`rejectFunnel` 里也看不到。

这直接解释标注 #1：bookends 窗（`asset-079/081/082/080`）跨 `sg-scene-0c` 与 `sg-scene-0d`，理应被拒，却成为赢家。

### 1.3 边界信号现状

| 信号 | 现状 | 可用性 |
|------|------|--------|
| `shotGroupId`（场景组） | 覆盖 100%，本册 9 组（4–61 张） | **可用，主锚** |
| `sceneClusterId`（L1 簇） | 本册 `-1` 占 **56%**；有效 id 可区分同组内跳场景 | **半硬副锚**（见 §3 P1） |
| `semanticTag.category` | person / street / landscape 等 | W1 **软**信号 |
| 服装（look 组） | 本册 `lookGroupCount=0`、`lookEncoded=0` | **本期不可用**（W3） |
| `burstGroupId` | 过细，三连拍常跨多 id | **不可当硬边界** |
| `takenAt` | 完整 | 必要；屏内跨度硬拒 |

### 1.4 典型坏例的机制归因

| 标注 | 屏 | 真实机制 |
|------|-----|---------|
| #1 | `ch-01-sc-25` bookends | MCS 跨组，硬拒失效 |
| #4 | `ch-01-sc-32` portrait-3 = 13:18 / 16:10 / 23:31 | **跨 10 小时**，尾部/carry 合并无时间与簇约束 |
| #10 尾 | `ch-03-sc-08` 含 `asset-159` | 同 shotGroup 但 `sceneClusterId` 与 `semanticTag` 都变 |
| #8 / #10 | 廊柱系列、海滩系列被切成 2–3 屏 | 游标按固定窗宽硬切，不认系列 |
| #2 / #4 | 整屏无逻辑 | 为凑满 3 槽从池子里抓图 |
| #11 | `ch-03-sc-11` | 同 sg、近时、换装换光；**无 look 信号 → W1 已知残差** |

### 1.5 审定量化摘要（demo-49cbe46479）

同 shotGroup 相邻间隔：p50=156s，p75=406s，p90=1499s。

| 判据 | atoms | 单张 | ≥3 供给 |
|------|-------|------|---------|
| 强制同 sc + 600s（草案原文） | 58 | 29 | 12 |
| **审定：sg + 半硬 sc + 600s** | ≈49–58 | ≈22–29 | ≈12–13 |
| 类别硬切 | 90 | 54 | 14（过碎，否决） |

---

## 2. 目标与非目标

### 2.1 80 分合同

- **硬底线**：同屏不得出现人类一眼判「不是一组」的照片（换装 / 换地 / 跨小时）。
- **可接受**：同一系列被拆成多屏，只要每屏自洽。
- **可接受**：结尾剩几张被合理硬拼（须同 atom；跨 atom 只出单图）。
- **可接受（本期）**：#11 类「同组近时、换装换光」在无 look 前可能残留。
- **不追求**：与人心中唯一拼法一致。

### 2.2 非目标

- 不做全局最优聚类 / 不引入需要调参的整册优化。
- 不在本期依赖服装模型（look 作为 W3 / P3）。
- 不新增模板 SKU；**W1 期间三列等分实验 SKU 默认不曝光**（归因隔离，见 §9）。

---

## 3. 升级方案（四层，按优先级）· 已审定

### P0 · 让已有门真正生效（修复类）· 批准立即做

| # | 项 | 审定说明 |
|---|----|----------|
| P0-1 | **policy 值对象注入** | **不要**把整个 `AppConfig` 塞进 `generate_window_candidates`。在 hook / planner 入口从 `AppConfig` 解析一次 `ShotGroupMosaicPolicy`（或等价），显式传入。禁止再从 `MosaicConfig` 取 `shot_grouping` |
| P0-2 | fail-loud | 门开关解析不到时打 warning 并计数，而不是静默 False |
| P0-3 | 漏斗可见 | `rejectFunnel` 必须能出现 `shot_group_cross` / `shot_group_anti_slice`；狗粮以「能看到拒绝」为通过条件 |
| P0-4 | 调用链回归 | 单测必须覆盖 **真实 `MosaicConfig` 调用路径**（现有测用带 `shot_grouping` 的假对象，抓不到本缺陷） |

**预期**：修掉 #1 类跨组拼图；零新算法风险。

### P1 · 边界原子（Scene Atom）——本期核心 · 审定定义

**放置**：`layout_engine` **planner memory only**（对齐 `coarse_segments`：不持久化为 trip.json SSOT）。

**统一门**：抽成纯函数（`asset_ids + assets_map + AtomPolicy`）→ MCS / legacy / attach **同一调用**，禁止三处复制。

#### 审定 atom 定义（连续序列同时满足）

```
硬：
  1. 同 shotGroupId
  2. 相邻 takenAt 间隔 ≤ T_atom（默认 600s；可调至 900s，见 §9）
  3. 任一拟成屏窗口：成员 takenAt 跨度 < 2h（灭 #4 类跨小时硬拼）

半硬 sceneClusterId：
  4. 两侧皆为有效 id（非 -1 / 非缺失）→ 必须相同
  5. -1（或缺失）不阻断「同 sg + 时间近」合并（保供给）
  6. 有效 id 与 -1 不得混在同一 atom / 同一多槽屏（救 #3）

软（W1 只惩罚 / 打分，不硬拒）：
  7. semanticTag.category 跳变（person↔street/landscape 等）
```

**明确不进入硬边界**：`burstGroupId`、look（本期不可用）。

#### 规则

| # | 规则 | 覆盖 / 说明 |
|---|------|-------------|
| P1-1 | **任何 ≥2 槽的屏，成员必须来自同一 atom** | #1 #5 #6 #7；#3 靠半硬 sc；#9 靠跨度/间隔 |
| P1-2 | atom 内不足以填满模板 → **降级**（3→2→1），禁止跨 atom 借图 | #2 #4 |
| P1-3 | 约束对 **MCS + legacy + 尾部/carry** 同样生效 | 统一门 |
| P1-4 | 尾部残图只能与 **同 atom** 合并；跨 atom → 单图（可配 breath） | #4 |
| P1-5 | **#11 为 W1 已知残差**：同 sg、gap&lt;T_atom、无有效 sc 差分、无 look → 不设 Go 必过；记入局限，交 W3 | 审定量化已验算漏网 |

#### 层级关系（审定）

```
coarse segment（时间/城市，禁跨段开窗）
  ⊇ shotGroup（SSG 场景组）
    ⊇ scene atom（本方案页级边界，planner memory）
      → page pack / 模板窗（P2）
```

### P2 · 系列先合并，再按容量切页 · W2

当前是「游标切 N 张 → 找模板」。改为：

```
atom → page packs
  若 atom 大小 ≤ 契约容量：一屏
  若更大：按容量切成多页，页间连续、同 atom、保时间序
  切页时优先朝向组合能命中现有模板；避免同构图复读（近景克隆门继续）
```

覆盖 #8 / #10（加分，**不进 W1 Go**）。

### P3 · 打分与增强 · W3

- 服装 look 组作为 atom **细分**（`lookGroupCount>0` 才启用）——主攻 #11 类。
- 人脸集合 Jaccard 软加分（合影 vs 独照不硬拼）。
- burst 仅用于槽位排序与近景克隆惩罚，**不参与边界判定**。
- 稀缺强模板（bookends / center-rails / landscape-6）准入（审定）：
  - **同 atom** + 朝向契约匹配 + 质量门槛
  - span 用 **600–900s soft**，**禁止** 300s hard（否则几乎不出）

---

## 4. 触点清单（实现时的文件级预估，不含代码）

| 文件 | 变更性质 |
|------|---------|
| `travelogue/layout_engine/mosaic/candidates.py` | P0：policy 注入 + 漏斗；P1：atom 门 |
| `travelogue/layout_engine/mosaic/shot_group_gate.py` | policy / atom 判定入口 |
| 新增 `travelogue/layout_engine/planner/scene_atoms.py` | atom 构建（审定定义） |
| `travelogue/layout_engine/planner/screen_planner_stages.py` | legacy 多槽过统一门；不足降级 |
| `travelogue/layout_engine/planner/screen_planner_attach.py` | 尾部/carry 同源门 |
| `travelogue/layout_engine/mosaic/legacy.py` 等 | **补漏**：凡产 ≥2 槽屏处均过统一门 |
| `travelogue/layout_engine/mosaic/coarse_segments.py` | 文档/注释：atom ⊆ segment |
| `travelogue/config/shot_grouping.py` | `AtomPolicy` 配置项 |
| `tests/unit/layout_engine/test_shot_group_gate.py` | MosaicConfig 调用链回归 |

`schemas/trip.schema.json`：仅当新增**持久化** telemetry 字段时才改；atom 本身不入 trip SSOT。

---

## 5. 配置（审定默认值）

```yaml
shot_grouping:
  mosaic:
    slice_cross_group_hard_reject: true      # 已存在，P0 须真正生效
    same_group_anti_slice: true
    atom:
      enabled: true                          # 总开关；false = 回退现行为
      max_gap_seconds: 600                   # T_atom；狗粮可试 900
      max_window_span_seconds: 7200          # 屏内跨度硬拒（2h）
      scene_cluster_mode: compatible         # 半硬：见 §3；禁止 force_same
      # force_same = 草案原文（已否决，过碎）
      category_jump_is_hard: false           # W1 软；观察后再升
      strong_template_max_span_seconds: null # 不用 300 hard；靠同 atom + 契约
      strong_template_span_soft_seconds: 900
      allow_tail_cross_atom: false
      mosaic_share_floor_observe: 0.70       # 相对基线多槽屏占比观察护栏（非自动放宽）
```

W1 dogfood 期间：三列等分实验 SKU **不进默认 allowlist / cohort 关闭**（见 §9-5）。

---

## 6. 验收（80 分合同的量化）· 审定

### 6.1 指标

| 指标 | 定义 | 目标 |
|------|------|------|
| **脏屏数 / 册** | 人工或代理判定含跨 atom 成员的多槽屏数 | **0～1** |
| **灾难屏数 / 册** | 成员分属 ≥3 个 atom，或整屏无叙事 | **0** |
| **跨 2h 屏** | 屏内 takenAt 跨度 > 2h | **0** |
| **污染率** | 跨 atom 多槽屏 / 全部多槽屏 | **&lt; 5%**（辅指标） |
| **多槽屏占比** | 相对 W0 基线 | **观察护栏**：降幅不宜 &gt; ~30%；超标告警，**不自动**放开跨 atom |
| 合并度 | 同 atom 被拆成的平均屏数 | 只观察，不设 Go |
| 降级率 | 因不足降为 pair/单图 | 允许上升 |

### 6.2 回归用例（11 例）

| 集合 | 要求 |
|------|------|
| 污染必过 | #1 #3 #5 #6 #7 #9：**污染成员不得同屏** |
| 灾难必过 | #2 #4：**不得再成该脏屏**（降级 pair/单图可接受） |
| **已知残差** | **#11**：W1 **不设必过**；记入报告 |
| 加分非 Go | #8 #10 合并改善 |

### 6.3 跨相册抗过拟合

同一套参数在 **≥3 本不同风格 trip** 上：脏屏数 / 灾难屏达标；任一本污染率 &gt; 5% 且无解释 → 视为过拟合。

---

## 7. 分阶段落地 · 审定

| 阶段 | 内容 | 出口 |
|------|------|------|
| **W0** | P0 policy 注入 + 漏斗 + MosaicConfig 调用链测 + 基线指标 | `rejectFunnel` 可见 `shot_group_cross`；#1 类可修 |
| **W1** | P1 审定 atom 门（MCS + legacy + attach）；实验 SKU 默认关闭 | §6 指标 + 污染/灾难回归；#11 可残留 |
| **W2** | P2 系列切页 | #8/#10 改善；W1 指标不回退 |
| **W3** | P3 look / 人脸 | 攻坚 #11；不阻塞前序 |

每阶段独立可回滚（`atom.enabled`）。**W1 未达标不做 W2**。

建议 PR 粒度：W0 单独 → W1a（MCS+legacy）→ W1b（尾部+跨 2h）→ W2。

---

## 8. 风险与取舍 · 审定

| 风险 | 说明 | 缓解 |
|------|------|------|
| 版面变碎 | atom 门减少多槽 | 碎度观察护栏；W2 切页回收系列；**不**为凑密度跨 atom |
| #11 残留 | 无 look | 明示已知残差；W3 |
| #3 回潮 | 半硬 sc 实现错误时 | 单测锁定「有效 id 与 -1 不得混」 |
| 新模板更难出现 | 实验 SKU W1 关闭 | 边界稳定后再开；准入靠同 atom 而非 300s |
| 参数过拟合本册 | 600/900 | §6.3 三册抽检 |
| golden / 视觉回归红 | 屏结构变化 | 开关默认 off，cohort 开 dogfood |

---

## 9. 已裁决（评审合议 · 2026-07-31）

| # | 问题 | 裁决 | 理由 |
|---|------|------|------|
| 1 | atom 是否强制同 `sceneClusterId` | **否 → 半硬（`scene_cluster_mode: compatible`）** | 本册 `-1` 占 56%；强制过碎。有效 id 彼此必须相同；`-1` 不与非 `-1` 混 |
| 2 | 类别跳变硬/软 | **W1 软**；观察后可升硬 | 助 #10/#11，但硬切 atoms→90、单张 54，过碎 |
| 3 | `T_atom` | **默认 600s**；狗粮可试 **900s** | p75=406、p90=1499；用碎度护栏校准，暂不自适应 |
| 4 | #8/#10 合并是否进 W1 Go | **不进** | 符合 80 分；属 W2 加分 |
| 5 | W1 是否暂关三列等分实验 SKU | **是** | 边界与模板同时变无法归因；先验边界 |

**附加裁决**

- 稀缺模板：**禁止** `strong_template_max_span_seconds: 300` hard。
- P0 修法：传 **policy 值对象**，不整包 `AppConfig` 入 candidates。
- Atom：**不**写入 trip.json SSOT。
- **#11**：W1 **已知残差**，不阻断 Go。

---

## 10. 开工门槛（自审定稿起）

1. 本文 §3 / §9 为实现唯一依据（取代草案原文 atom 定义）。
2. **先合 W0**，再开 W1。
3. W1 合入前：统一门覆盖三条路径 + §6 回归（含 #11 残差声明）+ 实验 SKU 默认关闭。
