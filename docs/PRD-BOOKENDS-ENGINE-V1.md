# Travelogue · Bookends Engine V1 产品需求文档（封面–封底引擎）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v0.2.1-BOOKENDS-V1** |
| **状态** | Draft · **v0.2.1 已合入开发负责人执行决议** · ADR-017 / IMPLEMENTATION 已起草 · 可开 B1 |
| **评审纪要** | [acceptance-records/bookends-prd-review-2026-07-13.md](./acceptance-records/bookends-prd-review-2026-07-13.md)（对 v0.1 **有条件通过**） |
| **实施清单** | [IMPLEMENTATION-BOOKENDS-ENGINE-V1.md](./IMPLEMENTATION-BOOKENDS-ENGINE-V1.md) |
| **ADR** | [adr/017-bookends-engine.md](./adr/017-bookends-engine.md) |
| **Phase 代号** | 「Bookends Engine V1」— 将封面选片、开屏样式、封底选片收敛为可升级引擎，并补齐 **封面↔封底成对约束** |
| **前置条件** | Cover Styles V6 M1+M2 代码门禁通过；`cover_scoring_v2` / `pick_cover_asset_id` 可用；`domain/closing_view.py` + `cover-closing.hbs` 可用；schema 含 `coverOpeningStyle` / `coverByLayout` / `coverJointLocked` |
| **交付形态** | **引擎内核（Python）+ Studio「封面与封底」面板 + 渲染契约**；小程序仅消费 Decision（本 Phase 不新建小程序页） |
| **关联文档** | [PRD-COVER-STYLES-V6.md](./PRD-COVER-STYLES-V6.md)、[cover-selection-plan.md](./cover-selection-plan.md)、[PRD-ALGORITHM-OPTIMIZATION-V2.md](./PRD-ALGORITHM-OPTIMIZATION-V2.md)、[CHARTER.md](./CHARTER.md)、[DATA-MODEL.md](./DATA-MODEL.md) |
| **承接关系** | 兑现 V6 Closing PRD；本文为原 `PRD-COVER-CLOSING-V1` 超集 |
| **验收** | [ACCEPTANCE-BOOKENDS-ENGINE-V1.md](./ACCEPTANCE-BOOKENDS-ENGINE-V1.md)（B1 起维护） |
| **更新日期** | 2026-07-13 |

> **定位**
>
> 游记的「第一眼」与「最后一眼」决定杂志感是否成立。V6 已解决 Opening 五款皮肤 + 图×样式联合选型；封底仍是独立启发式。本 PRD 将两端收束为 **Bookends Engine**（工程师名；**对用户称「封面与封底」**）。
>
> **战略原则（已拍板 · v0.2）**
>
> 1. **扩展现有 `cover_engine`，不另起平行引擎包。**  
> 2. **Opening 质量默认保持 v2 行为**；V1 增值在 **API 收口 + Closing 升级 + Pairing**。  
> 3. **规则为主**；MLLM / VL **默认关闭**。  
> 4. **完整 Admin 不做**；Studio 做用户向换图/换版。  
> 5. **与 Screen Planner / MCS 解耦**：只管封面与封底，不管正文屏拓扑。  
> 6. **Closing 两阶段解析（R-BE-08）**：Opening @ curate；Closing @ **唯一挂点**（§4.5.1）。  
> 7. **B1 仅 facade**（R-BE-07）：禁止 B1 大搬家 `joint.py`；行为金样零回归。  
> 8. **压字硬闸分期**（R-BE-15）：B1 默认 off（可打标）；B2a/B2 默认 on。  
> 9. **B2 拆分**（R-BE-16）：**B2a** 引擎+挂点（自动成书价值）；**B2b** Studio 合页面板。  
> 10. **无封底图 DOM**（R-BE-17）：保留 Colophon 文案区，去掉封底大图 + 弱提示。  
> 11. **双轨封板**（R-BE-18）：工程封板=自动化 AC；产品封板=盲评（可并行/限期 waiver）。

### 变更摘要

| 版本 | 要点 |
|------|------|
| **v0.2.0** | 合入跨职能评审 BLK-01..07 |
| **v0.2.1** | 开发负责人决议：唯一挂点、锁粒度、压字分期、B2a/B2b、OQ-BE-07 DOM、双轨封板 |

---

## 0. PRD 必须说清楚的内容（读者指南）

| 章节 | 必须澄清的问题 |
|------|----------------|
| §1 背景 | 为何现在做、与 V6 / 盲评关系 |
| §2 目标/非目标 | 范围锁死；B1 vs B2 门禁区分 |
| §3 角色契约 | 好封面/好封底；极小册；成对硬/软规则 |
| §4 架构与相位 | 两阶段挂点（**必读**） |
| §5 数据模型 | Decision、锁字段、confidence |
| §6 算法 | Opening 压字、Closing、Pairing、信号源 |
| §7 前后端 | Studio 流程/级联/文案；API |
| §8 后台管理 | 不做 Admin |
| §9–§11 | 配置、NFR、AC |
| §12–§15 | 里程碑、风险、决议、盲评 |

---

## 1. 背景与问题陈述

### 1.1 As-Is

| 能力 | 现状 | 问题 |
|------|------|------|
| **封面选片** | `pick_cover_asset_id` + `cover_scoring_v2` | 与引擎边界不清；盲评 signoff 未闭合 |
| **开屏样式** | `cover_engine` + `joint.py`（V6） | 成熟；仅管 Opening |
| **封底选片** | `domain/closing_view.py`（含「无候选可回退封面」） | 无成对契约；与 PAIR-H1 目标冲突 |
| **封底样式** | 单一 `cover-closing.hbs` | `closing_family` 预留未用 |
| **Studio** | 可换 Opening 样式 | 封底几乎不可见、不可换；无合页预览 |
| **Admin** | 无 | V6 已明确非 P0 |

### 1.2 要解决的问题（P-BE-*）

| ID | 问题 | V1 处理 |
|----|------|---------|
| **P-BE-01** | 逻辑散落三处 | B1 facade → B2 真正收口 |
| **P-BE-02** | 无成对约束 | B2 Pairing |
| **P-BE-03** | 缺角色硬契约 | §3 |
| **P-BE-04** | 压字未反哺选片 | §6.1：**B2a** 硬闸 + AC-BE-14；B1 仅打标 |
| **P-BE-05** | mobile/web 分裂 | V1 封底仅 web/auto；Studio 折叠明示 mobile |
| **P-BE-06** | 缺稳定 API | `resolve_opening` / `resolve_closing` / `resolve_bookends` |

### 1.3 核心判断

> **Bookends = Opening（封面图×开屏样式）+ Closing（封底图×封底样式）+ Pairing。**  
> 用户可感知跃迁在 **B2**；**B1 只做门面与零回归**，单独不可封板。

### 1.4 与章程 / 既有 PRD

| 文档 | 关系 |
|------|------|
| CHARTER | local-first；无账号；属成书质量 |
| PRD-COVER-STYLES-V6 | Opening Registry / joint 继续有效；B1 不重排 joint 包结构 |
| cover-selection-plan | 质量优先；盲评用 `scoreRankedTop3` |
| PRD-PHASE23 | 见 §14.2 互斥顺序 |
| 美学 MLLM | 默认不参与；`_mllm_cover_logit_boost` 标遗留（R-BE-11） |

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量 | 门禁阶段 |
|----|------|------|----------|
| **G-BE-01** | 调用方经 `cover_engine.api` 完成书衣决策（兼容期可 re-export） | 代码审查 | **B2**（非 B1） |
| **G-BE-02** | 硬去重 + 成对约束生效 | 单测 + ≥10 trip | B2 |
| **G-BE-03** | Studio「封面与封底」可查看/更换 + 人话 explain | UX 验收 | B2（Opening 说明可 B1） |
| **G-BE-04** | Opening 金样 / V6 **行为不回归** | pytest + 金样 | **B1** |
| **G-BE-05** | 封面 A 率 ≥ 基线；封底收束偏好 ≥60% | §14.1 盲评 | V1 封板 |
| **G-BE-06** | `bookendsLocked` 生效；无 force 不静默重写 | 单测 | B1 Opening 锁 / B2 含封底 |
| **G-BE-07** | resolve 耗时有基线记录；目标 P95 ≤ 现网 +20% | telemetry | 记录自 B1；门禁可后置 |

### 2.2 非目标（V1）

| 类别 | 非目标 |
|------|--------|
| **Admin** | 完整样式 CMS、拖拽改 text_safe_regions |
| **正文** | 章内 hero、MCS、Screen pattern |
| **文案** | hook / epilogue LLM（归 narrate） |
| **皮肤** | Opening 五款镜像封底；V1 封底样式切换 UI |
| **默认 MLLM** | 不开 cover/closing 视觉大模型 |
| **小程序新页** | 不做小程序封面实验室 |
| **B1 大搬家** | 禁止将 `joint.py` 等重排作为 B1 必达 |

---

## 3. 角色契约

### 3.1 封面（Opening · 对用户称「封面」）

**一句话**：代表「这一趟旅行第一眼是什么」，且 **能安全承载书名**。

| 维度 | 要求 |
|------|------|
| **代表性** | 与 `albumProfile` / 主导 stratum 同族优先 |
| **可读性（硬）** | 活动开屏样式的 `text_safe_regions` 内：人脸中心不得落入字区；字区边缘能量过高则 **不得进质量 Top1**（§6.1） |
| **质量** | 清晰、合格画幅；继承 v2 闸口 |
| **布局** | mobile 竖池 / web 横池；`coverByLayout` 可分置；不足时任意图兜底（`orientationFallback`，UX-BE-09） |
| **时间** | 不强制最早拍摄 |

### 3.2 封底（Closing · 对用户称「封底」）

**一句话**：提供「收束 / 回望」，不是第二次高潮。

| 维度 | 要求 |
|------|------|
| **去重** | ≠ 任何 layout 封面 id |
| **对比** | 与封面在「是否有人 / 景别 / 色温或饱和」至少错开一维 |
| **情绪** | 低饱和/远景/空镜/暮色加分（**有上限**，防死黑糊片）；高对比大场面降权 |
| **位置** | 优先未进正文屏；末两屏出现降权（**仅 Closing 阶段有 screens 后计算**） |
| **时间** | 后段软信号 |
| **压字** | epilogue / THE END 安全区：V1 用下半 luma 适中作软分；不替代 Opening 压字硬闸 |

### 3.3 成对禁忌（硬）

| ID | 规则 | 信号源 |
|----|------|--------|
| **PAIR-H1** | 封面与封底 assetId 不得相同 | id 相等 |
| **PAIR-H2** | 同连拍/近复不得成对 | ① 同 burst 组 id（ingest 若有）；② 否则 `takenAt` 差 ≤ `pairing.near_dup_seconds`（默认 3s）且画幅相近；③ **无**稳定 `contentSig` 字段时 **不**启用 pHash 硬拒（避免死规则） |
| **PAIR-H3** | 封面为人像大头时，封底不得再选同主体近景人脸 | `faces` 存在且封面人脸框面积 ≥ 阈值；封底亦有大脸 → 剔除 |

### 3.4 成对偏好（软）

| ID | 规则 |
|----|------|
| **PAIR-S1** | 封面人物 → 封底偏空景/离开的路 |
| **PAIR-S2** | 封面大风景 → 封底可细节或夜色 |
| **PAIR-S3** | 饱和度/平均亮度差异落在配置区间 |

软规则 **不对用户 Toast**；仅进入折叠「为什么选这张」。

### 3.5 极小册 / 无封底候选（R-BE-09 · 拍板）

当 PAIR-H* 过滤后 **无合法封底候选**：

| 决策 | 行为 |
|------|------|
| **采用** | `closing_asset_id = None`；**DOM：保留 Colophon 文案（epilogue / THE END），去掉封底大图**；预览弱提示（R-BE-17）；`degraded=true`；explain 人话：「可选照片太少，已省略封底图，避免与封面重复。」 |
| **禁止** | 复用封面 id（废除现网 `_resolve_closing_allow_cover` 成功路径） |
| **测试** | 改写 `test_resolve_closing_falls_back_to_cover_when_only_cover_exists` → 断言 `None` + degraded |
| **NFR** | fail-open 指「引擎异常时回退旧 heuristic **但须剥离 cover 回退**」或回退到 `closing=None`（§10） |

---

## 4. 系统架构

### 4.1 逻辑架构

```
ingest → curate ──(1) resolve_opening──► 写封面/样式/锁(opening)
              ↓
           layout / MCS（正文屏）
              ↓
     (2) resolve_closing + pairing ──► 写封底/explain/锁(closing)
              ↓
           narrate → render（读持久字段；无 force 不重算）
```

对外 API：

- `resolve_opening(trip, layout, …)`  
- `resolve_closing(trip, layout, …)` — **要求 screens 已存在**（或显式传入占用集）  
- `resolve_bookends(...)` — 编排：若无 screens 则只做 opening 并返回 `closing_pending=true`；若有 screens 则两端都做  

### 4.2 包结构

```
travelogue/cover_engine/
  api.py                 # resolve_opening / resolve_closing / resolve_bookends / repick_*
  types.py               # BookendsDecision
  catalog.py / registry.py
  opening/               # B2+ 再物理迁入；B1 以 adapter/re-export 为主
    quality.py           # → cover_scoring_v2
  closing/
    gate.py / scorer.py  # 自 domain/closing_view 升级
  pairing/
    policy.py / explain.py
  telemetry.py
```

**B1 约束**：`joint.py` **保持现路径**；`api` 调用现网函数。物理迁入属 B2 清理，不挡门禁。

兼容期：`domain/closing_view.py`、`pick_cover_asset_id` thin re-export → api。

### 4.3 与周边边界

| 系统 | 做 | 不做 |
|------|----|------|
| **curate** | 调 `resolve_opening`；**不**在无 screens 时写死最终 closing | 内联打分 |
| **layout** | 可读封面排除 id | 选封底 |
| **layout 完成后 hook / render 前** | 调 `resolve_closing`（若未锁 closing） | — |
| **render** | 读持久字段 | 无 force 不重算 |
| **narrate** | 可读 Decision | 改图 |

### 4.4 布局意图（R-BE-10）

| layout | 封面 | 封底 |
|--------|------|------|
| **mobile** | 选图；样式可占位 veil | **`mobile_closing: false`**：不持久化、不渲染独立封底；Studio 文案「V1 封底仅网页成书」 |
| **web / auto** | 图×样式联合 | 选图 + `colophon-default`；主验收面 |
| **longshot** | 现网 | **保持现网**（多为无 closing DOM） |

### 4.5 Closing 相位（R-BE-08 · BLK-01 拍板）

**采用方案 A · 两阶段：**

| 阶段 | 时机 | 写入 |
|------|------|------|
| **Opening** | curate 内（`resolve_opening`） | 封面字段 + opening explain；可 lock opening |
| **Closing** | **唯一挂点**见 §4.5.1 | `closingAssetId`（可为 null）+ pairing explain；lock closing |

若用户在 Studio 于 layout 前打开面板：封底区显示「排版完成后自动选择」；允许「预览候选」但不最终 lock closing，直至 `resolve_closing` 成功。

**禁止方案 B**（本 V1）：单次 curate 原子 resolve 且依赖 unused_bonus。

### 4.5.1 Closing 唯一挂点（R-BE-19 · 代码级 · 必遵）

为避免 curate / layout / assemble 三处各算一次，V1 **只允许**下列调用点写入持久 `closingAssetId`：

| 场景 | 唯一允许的调用点 | 行为 |
|------|------------------|------|
| **完整 `run_trip`** | `orchestrator` **layout stage 成功末尾**（若 curate 内已 `apply_layout`，则在该次 layout 成功返回后立刻调用） | `resolve_closing` → 落盘；未锁 closing 才写 |
| **`from_stage=render` 且缺字段** | `render/assemble.py` **组装 cover-closing 之前** | 键**缺失**且 closing 未锁 → 补算并回填；键为 **`null`**（显式无图）→ **不**重算 |
| **Studio 只读预览** | bento / 预览路径 | **只读**持久字段；缺且未锁时可临时 resolve **默认不写 trip** |

**禁止**：curate 无 screens 时写最终 closing；在 `moment_scoring` 内旁路持久化 closing。

权威伪代码见 [ADR-017](./adr/017-bookends-engine.md)。

---

## 5. 数据模型

### 5.1 `BookendsDecision`

```python
@dataclass(frozen=True)
class BookendsLockState:
    opening: bool = False
    closing: bool = False

    @property
    def all_locked(self) -> bool:
        return self.opening and self.closing


@dataclass(frozen=True)
class BookendsDecision:
    cover_asset_id: str
    cover_by_layout: dict[str, str]
    cover_opening_style: str
    closing_asset_id: str | None
    closing_style_id: str | None
    closing_pending: bool
    confidence: float
    low_confidence: bool
    degraded: bool
    lock: BookendsLockState
    locked: bool                          # == lock.all_locked
    explain: dict[str, Any]
    scoring_versions: dict[str, str]
    telemetry: dict[str, Any]
```

### 5.2 trip.json 写入

| 字段 | 动作 |
|------|------|
| `coverAssetId` / `curation.coverByLayout` | Opening 阶段写 |
| `meta.coverOpeningStyle` | Opening 阶段写 |
| `curation.bookendsLock` | **粒度锁** `{ "opening": bool, "closing": bool }`（R-BE-20） |
| `curation.bookendsLocked` | **派生** `opening && closing` |
| `curation.coverJointLocked` | **镜像** `bookendsLock.opening`（V6 兼容） |
| `curation.closingAssetId` | Closing 写；可为 JSON `null`（显式无图） |
| `meta.coverClosingStyle` | 有图时默认 `colophon-default` |
| `curation.bookendsExplain` | 含 `userOneLiner` |
| `curation.bookendsVersions` | 版本戳 |
| `curation.closingUserPicked` | 用户手选封底 |

**显式 null vs 缺省**：键缺失 = 尚未 resolve；键为 `null` = 已 resolve 无图。assemble 不得把显式 null 当缺失而重算。

### 5.3 锁定语义（R-BE-12 / R-BE-20）

- 粒度真相源：`bookendsLock.opening` / `.closing`。  
- `bookendsLocked := opening && closing`。  
- `coverJointLocked := bookendsLock.opening`（旧 trip 仅有 joint 锁时回填 opening）。  
- `repick-opening` / `repick-closing` 可分别只动对应侧锁；`restore-auto` 清两侧后全量重算。  
- 无 force：curate 不改已锁 opening；挂点不改已锁 closing。

### 5.4 confidence 定义

```
opening_conf = 1.0 - joint_low_confidence_penalty   # V6 low_confidence → 最多扣至 0.45
closing_conf = 0.0 if closing is None and degraded else (
               0.55 if degraded else 0.85)
confidence = 0.6 * opening_conf + 0.4 * closing_conf
             # closing_pending 时仅用 opening_conf
low_confidence = confidence < 0.55 or joint.low_confidence
```

---

## 6. 算法需求

### 6.1 Opening（B1 行为对齐；压字分期 R-BE-15）

| 项 | 要求 |
|----|------|
| 闸口 / 质量 / joint | 对齐现网；B1 adapter |
| 低置信 | fallback veil-footer + Top1；hash 仅 tie-break |
| **压字** | **B1** 默认 `opening_hard_gate=false`：可打「不适压字」标，**不改 Top1**（保零回归）。**B2a 起** 默认 `true`：字区撞脸/高边缘 → 移出 Top1；AC-BE-14 绑 B2a |
| MLLM | 默认不 blend；金样 shortlist 不得含 cover；boost 遗留（R-BE-11） |

### 6.2 Closing Scorer v1（B2 · post-layout）

| 因子 | 方向 | 说明 |
|------|------|------|
| `unused_bonus` | + | 未进正文屏 |
| `not_last_screens_penalty` | − | 末两屏 |
| `low_saturation` | + | **有上限** |
| `evening_tags` | + | 有上限 |
| `landscape_for_web` | + | AR |
| `recency_soft` | + | 后段 |
| `pairing_contrast` | + | PAIR-S* |
| `pairing_hard_violations` | 剔除 | PAIR-H* |
| `title_safe_closing` | + | 软 |
| `dead_black_penalty` | − | 过暗过空 |

### 6.3 Pairing Policy v1

1. 读取已锁 Opening（或刚 resolve 的 Opening）。  
2. 构建候选（排除封面 ids + moment `exclude_ids`）。  
3. 过滤 PAIR-H*。  
4. ClosingScorer + PAIR-S*。  
5. 无候选 → §3.5（`None` + degraded）。  
6. **禁止**回退到封面 id。

### 6.4 Closing 样式

| id | V1 |
|----|-----|
| `colophon-default` | 唯一用户可见样式；**不做切换 UI** |
| `colophon-quiet` | B3 |

`closing_family`：V1 **只读不强制映射**。

### 6.5 可选插件

默认 `opening_vl_rerank` / `closing_vl_rerank` = false；失败 fail-open。

### 6.6 Peak Moment 互斥顺序（§14.2）

1. Opening 先于 moment 签名锁定（curate 前段）。  
2. Moment 选型读取封面排除集。  
3. Closing 读取 `exclude_ids`（含 moment 签名若已定）+ 封面集。  
4. 若 moment 在 closing 之后重算：须触发 soft warning，不自动抢已锁封底（除非 force）。

---

## 7. 前后端任务拆分

### 7.2.0 用户文案词表（R-BE-13 · BLK-06）

| 对用户 | 禁止对用户 |
|--------|------------|
| 封面、封底、版式、第一眼、收束、恢复自动挑选、手机封面可能不同、网页成书 | Bookends、Opening、Closing、Pairing、书衣、resolve、Joint、degraded、locked（可用「已按你的选择固定」） |

面板标题：**「封面与封底」**；副文案：「游记的第一眼与最后一眼」。

### 7.1 后端 / 引擎

| ID | 任务 | Phase | 优先级 |
|----|------|-------|--------|
| **BE-BE-01** | ADR-017（含两阶段相位、锁、极小册） | B0 | P0 |
| **BE-BE-02** | `BookendsDecision` + confidence | B1 | P0 |
| **BE-BE-03** | `api.resolve_opening` / `resolve_closing` / `resolve_bookends` | B1 facade | P0 |
| **BE-BE-04** | curate → resolve_opening；re-export | B1 | P0 |
| **BE-BE-05** | §4.5.1 挂点：`resolve_closing` + 持久化 | **B2a** | P0 |
| **BE-BE-06** | Pairing + 改写 cover 回退单测 | **B2a** | P0 |
| **BE-BE-07** | schema：`bookendsLock` / `bookendsLocked` / `closingAssetId`… | B1 | P0 |
| **BE-BE-08** | telemetry | B1 | P1 |
| **BE-BE-09** | `bookends.*` 配置（含 `opening_hard_gate` 默认 false） | B1 | P0 |
| **BE-BE-10** | V6 / v2 行为回归 | B1 | P0 |
| **BE-BE-11** | 盲评导出脚本（成对刺激物） | B0–B1 | P1 |
| **BE-BE-12** | Opening 压字硬闸（改 Top1） | **B2a** | P0 |
| **BE-BE-13** | VL 插件接口 | B3 | P2 |
| **BE-BE-14** | Colophon 无图 DOM（R-BE-17） | **B2a** | P0 |

### 7.2 Studio 前端

| ID | 任务 | Phase | 优先级 |
|----|------|-------|--------|
| **FE-BE-01** | Opening：图+版式名+人话一句（只读可 B1） | B1 / **B2b** | P1/P0 |
| **FE-BE-02** | 封底区 + 收束一句；pending 态 | **B2b** | P0 |
| **FE-BE-03** | 换封面 Top3（灰标可 B1 只读）+ lock | **B2b** | P0 |
| **FE-BE-04** | 换封底候选 + `closingUserPicked` | **B2b** | P0 |
| **FE-BE-05** | 换版式经 api（V6） | B1 保持现网 / **B2b** 经 bookends | P1 |
| **FE-BE-06** | 折叠「手机封面」+「封底仅网页」 | **B2b** | P0 |
| **FE-BE-07** | 低置信/弱收束状态条 | **B2b** | P0 |
| **FE-BE-08** | 「恢复自动挑选」二次确认 | **B2b** | P0 |
| **FE-BE-09** | **合页预览** | **B2b** | P0 |
| **FE-BE-10** | **不做**封底样式切换器 | **B2b** | P0 |

#### 7.2.1 换封面 → 封底级联（R-BE-14 · BLK-04）

```
用户应用新封面
  → 校验 PAIR-H*（相对当前封底）
        ├─ 通过：保留封底；刷新 opening explain；lock
        └─ 冲突：
              ├─ closingUserPicked == false → 自动 resolve_closing；Toast「已为你重选封底」
              └─ closingUserPicked == true  → 模态：「封底与新封面冲突，需要重选封底」
                                              [重选] [取消换封面]
换 Opening 版式（重荐图）：同换封面级联规则。
恢复自动挑选：unlock + resolve_opening +（若有 screens）resolve_closing；确认文案写明将覆盖手选。
```

API：

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/trips/{id}/bookends` | Decision + userOneLiner |
| POST | `/api/trips/{id}/bookends/resolve-opening` | force? |
| POST | `/api/trips/{id}/bookends/resolve-closing` | force?；无 screens → 409 |
| POST | `/api/trips/{id}/bookends/repick-opening` | assetId? styleId?；触发级联 |
| POST | `/api/trips/{id}/bookends/repick-closing` | assetId?；设 userPicked |
| POST | `/api/trips/{id}/bookends/restore-auto` | 二次确认后 force 全量 |

### 7.3 渲染

| ID | 任务 | Phase |
|----|------|-------|
| **RE-BE-01** | 读 `closingAssetId`；`null` → 无大图 + 留 Colophon（R-BE-17） | **B2a** |
| **RE-BE-02** | `data-cover-closing` hook（预备） | B3 |
| **RE-BE-03** | 有图默认样式不回归金样 | B1 / B2a |
| **RE-BE-04** | §4.5.1 挂点接入 orchestrator | **B2a** |

### 7.4 小程序

| ID | 任务 | 范围 |
|----|------|------|
| **MP-BE-01** | Worker 同 api | 随 Miniapp |
| **MP-BE-02** | UI 换封面封底 | Out of V1 |
| **MP-BE-03** | VL 默认关 | 随 Miniapp |

### 7.5 设计 / 内容（B0 加重）

| ID | 任务 | Phase |
|----|------|-------|
| **DE-BE-01** | ≥6 组成对正反例（B0 Go/No-Go 附件） | **B0** |
| **DE-BE-02** | 「封面与封底」面板线框（合页+词表） | B0–B1 |
| **DE-BE-03** | 盲评操作手册（§14.1） | **B0** |
| **DE-BE-04** | 主路径 degraded：预览弱提示文案（无封底图时） | B2 |

### 7.6 用户主路径（自动成书）

```
成册 → resolve_opening → layout → resolve_closing
  → Web 预览：封面 … 封底（或无图+弱提示）
  → 从不进 Studio 的用户依赖自动成对质量（Studio 为例外路径）
```

---

## 8. 是否需要后台管理界面

### 8.1 决策（已拍板）

| 方案 | V1 |
|------|-----|
| 完整 Admin CMS | **不做** |
| Registry + config 启停 | **做** |
| Studio「封面与封底」面板 | **做**（杂志编辑台，非缩水 Admin） |
| 内部实验室 | 可选 B3 |

### 8.2 理由

样式量少；profile 变更走代码评审；产品化的是作者换首尾图。

---

## 9. 配置与可观测

```yaml
bookends:
  enabled: true
  pairing_version: v1          # off | v1
  opening_quality_version: v2
  closing_scorer_version: v1
  lock_after_resolve: true
  mobile_closing: false        # R-BE-10
  pairing:
    require_hard: true
    soft_weight: 0.35
    near_dup_seconds: 3
  title_safe:
    opening_hard_gate: false   # B1 默认；B2a 起改为 true（R-BE-15）
  plugins:
    opening_vl_rerank: false
    closing_vl_rerank: false
  telemetry: true
```

Telemetry 最低集：`openingStyle` · `closingStyle` · `closingPending` · `lowConfidence` · `degraded` · `pairingHardFiltered` · `resolveOpeningMs` · `resolveClosingMs` · `versions`  

写入：`curation.bookendsTelemetry`（IMPLEMENTATION 可镜像 timings）。

---

## 10. 非功能需求

| ID | 需求 |
|----|------|
| **NFR-BE-01** | B1：V6 / cover_scoring_v2 **行为**测试全绿（允许新增 api 包装测） |
| **NFR-BE-02** | 引擎异常 fail-open：Opening→现网 pick；Closing→**`None` 或旧 heuristic 但禁止 cover 回退**；不阻断成书 |
| **NFR-BE-03** | 默认无新增云 API 成本 |
| **NFR-BE-04** | 旧 trip 缺字段：opening 兼容；closing 在 post-layout 补算 |
| **NFR-BE-05** | Registry 启停线程安全同 V6 |

**行为变更声明**：废除「无候选复用封面」；相关单测必须改写（非回归绿，属故意变更）。

---

## 11. 验收标准（AC）

### 11.1 引擎与兼容

| ID | 判据 |
|----|------|
| **AC-BE-01** | `resolve_opening` / `resolve_bookends`（pending）对 web fixture 返回合法 Decision |
| **AC-BE-02** | B1 Opening 金样与迁移前一致（仅允许文档化 tie-break） |
| **AC-BE-03** | 无 force 时二次 curate 不改已锁 opening |
| **AC-BE-04** | re-export 与 api 等价 |
| **AC-BE-05** | 无 screens 时 `resolve_closing` → 明确错误/pending，不写假 unused 分 |

### 11.2 Pairing / Closing

| ID | 判据 |
|----|------|
| **AC-BE-10** | 有候选时 PAIR-H1：封面≠封底 |
| **AC-BE-11** | 仅封面可用：`closing_asset_id is None` 且 `degraded`；**绝不**回退封面 |
| **AC-BE-12** | post-layout 后：同等条件下偏好 unused |
| **AC-BE-13** | 人像大头封面 → 封底避同主体近景（fixture） |
| **AC-BE-14** | Opening 压字硬闸：字区撞脸 fixture **不得**为 Top1 | **B2a 门禁**（B1 不测改序） |

### 11.3 Studio

| ID | 判据 |
|----|------|
| **AC-BE-20** | 面板标题「封面与封底」；合页预览；人话一句 |
| **AC-BE-21** | 可换封底并持久化；`closingUserPicked=true` |
| **AC-BE-22** | 恢复自动挑选经确认后重算 |
| **AC-BE-23** | 换封面冲突手选封底时出现确认模态 |
| **AC-BE-24** | 无封底样式切换器（V1） |
| **AC-BE-25** | 折叠区展示 mobile 封面缩略 + 封底仅网页说明 |

### 11.4 渲染

| ID | 判据 |
|----|------|
| **AC-BE-30** | web+epilogue 且有 closing 图时封底出现 |
| **AC-BE-31** | `closingAssetId` 与渲染一致；`None` 无封底图 |
| **AC-BE-32** | longshot 行为与现网一致 |

### 11.5 人工（§14.1）

| ID | 判据 |
|----|------|
| **AC-BE-40** | ≥10 本：封面 A 率 ≥ **冻结基线**（B0 导出旧系统结果） |
| **AC-BE-41** | ≥10 本：封底收束偏好 ≥60% vs 旧 heuristic（刺激物含封面缩略） |
| **AC-BE-42** | 封面盲评附属：抽样标题压字可读截图无严重糊字 |

---

## 12. 里程碑与 Go/No-Go

| Phase | 交付 | Go/No-Go |
|-------|------|----------|
| **B0** | ADR-017 + IMPLEMENTATION；金样 trip 列表；盲评脚本/清单可并行 | 契约可编码 |
| **B1** | api facade；`resolve_opening`；`bookendsLock` schema；**压字硬闸默认 off**；**不**大搬家；**不做**完整 Studio 面板 | AC-BE-01..05、02；**不含** AC-BE-14 |
| **B2a** | `resolve_closing`+Pairing+挂点；废除 cover 回退；Colophon 无图 DOM；压字硬闸默认 on | AC-BE-10..14、30..32；自动成书 dogfood |
| **B2b** | Studio「封面与封底」合页+级联+恢复自动 | AC-BE-20..25 |
| **B3** | colophon-quiet / 实验室 / VL | 可选 |

**双轨封板（R-BE-18）**

| 轨道 | 定义 |
|------|------|
| **工程封板** | B1 + B2a 自动化 AC 全绿即可 merge 主路径；可宣传「内部 dogfood」 |
| **产品封板** | + B2b（若承诺面板）+ AC-BE-40/41 或 **限期书面 waiver**；再对外宣传「封底升级」 |

B2a 与 B2b **可先后合入**；优先 B2a（自动成书用户占多数）。

---

## 13. 风险与开放问题

### 13.1 风险

| 风险 | 缓解 |
|------|------|
| 只搬家无体感 | B2a 必达；B1 不工程封板 |
| 相位错误 | §4.5.1 唯一挂点 |
| 压字闸破坏零回归 | R-BE-15 分期 |
| 封底过暗 | dead_black_penalty + 换图 |
| mobile/web 投诉 | R-BE-10 + B2b 折叠 |
| 盲评拖进度 | R-BE-18 双轨 |

### 13.2 开放问题状态

| ID | 状态 | 决议 |
|----|------|------|
| **OQ-BE-01** | **关闭** | → R-BE-20 `bookendsLock` + 派生 `bookendsLocked` |
| **OQ-BE-02** | **关闭** | longshot 保持现网 |
| **OQ-BE-03** | **关闭** | → R-BE-10 |
| **OQ-BE-04** | **关闭** | → R-BE-11 |
| **OQ-BE-05** | **关闭** | 第二样式不进 V1 |
| **OQ-BE-06** | **关闭** | 盲评清单 B0；不堵 B1 |
| **OQ-BE-07** | **关闭** | → R-BE-17 留 Colophon 去大图 + 弱提示 |

---

## 14. 补充专题

### 14.1 盲评协议（B0 必交付）

**手册要点（DE-BE-03）：**

1. **封面**：`scoreRankedTop3`；A 率定义同 cover-selection-plan；禁止用多样性 `coverCandidates`。  
2. **封底**：左右随机「旧 heuristic vs Bookends」；**必须同屏显示该本封面缩略**；题干：「哪边封底更有收束/回望（不是更好看）」。  
3. 评委 ≥3；相册 ≥10；记录 degraded / 是否人像封面；平票记弃权。  
4. **基线**：B0 用现网脚本导出旧 closing 结果并冻结，供 AC-BE-40/41。  
5. 附属：抽样 Opening 标题压字截图（AC-BE-42）。

### 14.2 Peak Moment

见 §6.6；explain 计 `excludedByMoment`。

### 14.3 错误码

| Code | 含义 |
|------|------|
| `E_BOOKENDS_CLOSING_PENDING` | 无 screens，closing 未就绪 |
| `E_BOOKENDS_NO_CLOSING_CANDIDATE` | 硬过滤后无候选 → None+degraded |
| `E_BOOKENDS_LOW_CONFIDENCE` | 低置信 |
| `E_BOOKENDS_LOCKED` | 无 force 拒绝重写 |

### 14.4 安全与隐私

不上传原图（除非用户开 VL）；local-first。

### 14.5 文档清单

本 PRD v0.2 → ADR-017 → IMPLEMENTATION → ACCEPTANCE → 盲评手册与正反例附件。

### 14.6 后续（非本 PRD）

mobile 竖版 Opening 2 套；Admin（仅样式爆炸时）；小程序精修页；Opening quality v3。

---

## 15. 决议摘要

| 决议 | 结论 | 评审 |
|------|------|------|
| **R-BE-01** 扩展 `cover_engine` | **是** | ☑ 跨职能同意 |
| **R-BE-02** 增值=Closing+Pairing | **是** | ☑ |
| **R-BE-03** 完整 Admin 不做 | **是** | ☑ |
| **R-BE-04** Studio「封面与封底」面板 | **是**（合页+词表+级联） | ☑ 有条件 → v0.2 已合入 |
| **R-BE-05** MLLM/VL 默认关 | **是** | ☑ |
| **R-BE-06** 兑现 V6 Closing | **是** | ☑ |
| **R-BE-07** B1=facade 零行为回归 | **是**（非大搬家） | ☑ |
| **R-BE-08** Closing 两阶段相位 | **是（方案 A）** | ☑ v0.2 拍板 |
| **R-BE-09** 极小册 closing=None | **是**（禁复用封面） | ☑ |
| **R-BE-10** mobile_closing=false | **是** | ☑ |
| **R-BE-11** mllm cover boost 遗留 | **是** | ☑ |
| **R-BE-12** 锁字段 | **是** → v0.2.1 升为粒度 `bookendsLock`（R-BE-20） | ☑ |
| **R-BE-13** 用户文案词表 | **是** | ☑ |
| **R-BE-14** 换封面级联规则 | **是** | ☑ |
| **R-BE-15** 压字硬闸 B1 off / B2a on | **是** | ☑ v0.2.1 |
| **R-BE-16** B2 拆 B2a 引擎 / B2b Studio | **是** | ☑ v0.2.1 |
| **R-BE-17** 无图保留 Colophon | **是** | ☑ v0.2.1 |
| **R-BE-18** 工程/产品双轨封板 | **是** | ☑ v0.2.1 |
| **R-BE-19** Closing 唯一挂点表 | **是** | ☑ v0.2.1 |
| **R-BE-20** `bookendsLock.{opening,closing}` | **是** | ☑ v0.2.1 |

---

## 附录 A · 与 V6 / 现网映射

| 现网 | Bookends V1 |
|------|-------------|
| `meta.coverOpeningStyle` | 同左 |
| `coverAssetId` / `coverByLayout` | Opening 阶段 |
| `coverJointLocked` | 镜像 ← `bookendsLock.opening` |
| `resolve_closing_asset_id` + cover 回退 | Closing scorer；**删除 cover 回退成功路径** |
| `closing_family` | 只读软提示 |
| assemble 内 closing resolve | 仅作「缺字段补算」；主写入在 layout 末挂点 |

## 附录 B · 用户故事

| ID | 作为… | 我想要… | 以便… |
|----|--------|---------|--------|
| US-BE-01 | 旅行者 | 预览即见合适封面与安静封底 | 杂志感完整 |
| US-BE-02 | 进阶用户 | 在「封面与封底」合页里换图并固定 | 保留控制感 |
| US-BE-03 | 开发者 | 对接 `resolve_opening` / `resolve_closing` | 升级 scorer 不改调用方 |
| US-BE-04 | 副业运营者 | 默认不增加云 API 成本 | 控制毛利 |
| US-BE-05 | 旅行者（从不进 Studio） | 自动成对足够好 | 例外才精修 |

## 附录 C · 成对正反例清单（DE-BE-01 最低 6 组）

B0 附件须含图例，至少覆盖：

1. 人像封面 × 空景/道路封底（正）  
2. 大风景封面 × 夜色/细节封底（正）  
3. 同 id 首尾（反 · H1）  
4. 同脸大头连用（反 · H3）  
5. 双高潮大场面（反 · 情绪）  
6. 极小册仅 1 张合格图 → 无封底大图 + Colophon + 弱提示（正 · R-BE-09/17）

## 附录 D · 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-13 | 初稿 |
| v0.2.0 | 2026-07-13 | 合入跨职能评审 BLK-01..07；R-BE-08..14 |
| v0.2.1 | 2026-07-13 | 开发负责人执行决议：§4.5.1 挂点、R-BE-15..20、B2a/B2b、双轨封板 |

---

*v0.2.1 为实施母文档。按 B0→B1→B2a→B2b 推进；B1 禁止以包结构重排代替行为交付。*
