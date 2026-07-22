# ADR-007 · 原生 Curate 聚类层

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **active**（登记见 [DOC-STATUS.md](../DOC-STATUS.md)） |
| **状态** | Accepted（v0.2 · 2026-05-28） |
| **日期** | 2026-05-28 |
| **决策者** | Travelogue 产品/技术 |
| **关联 PRD** | [PRD-PHASE3.md](../PRD-PHASE3.md) v0.3.1 |
| **替代** | [ADR-006](./006-media-engines-integration.md)（Superseded） |

---

## 背景

Phase 3 原方案（ADR-006）通过 Docker 集成 Recasa + PhotoMapAI，提供「素材洞察工作台」。评审后明确 **产品目标收窄为 Curate 阶段的分组与排版增强**，不需要独立洞察 UI、用户精选、或双引擎运维。

Recasa / PhotoMapAI 的核心价值在于 **算法**（geo event 规则、CLIP 聚类），而非其完整相册应用。

v0.3.1 架构评审进一步确认：聚类层必须在 **分段权威链、排版约束优先级、默认 config、确定性、增量 cache** 上与 curate/layout 契约对齐，避免 invisible 增强引入 silent regression。

---

## 决策

### 1. 集成形态

在 `travelogue/` 内实现 **ClusteringLayer**（ingest 后、curate 前），于 **import subprocess** 内执行，**不** 启动外部 HTTP 服务或 Docker 容器，**不** 与 Studio 父进程共享 PyTorch。

### 2. 算法借鉴（非依赖）

| 能力 | 实现 | 参考 |
|------|------|------|
| geo/time 段 | `curation/geo_events.py` | Recasa event_detector 思路 · MIT |
| scene 簇 | `curation/scene_clusters.py` + `vision/` | PhotoMapAI CLIP+聚类思路 · MIT |

### 3. 两档交付

- **P3-Lite（M12）**：geo_events + curate §8.1 + decision_log + incremental cache  
- **P3-Full（M13）**：+ CLIP scene clusters；与 [智能排版V2.md](../智能排版V2.md) Layer 1.5 **合并里程碑**

### 4. 默认 config（v0.3.1）

| 键 | 出厂默认 | 理由 |
|----|----------|------|
| `clustering.enabled` | **`auto`** | 无 GPS 相册不白等 geo；有 GPS 时自动 P3-Lite |
| `vision.enabled` | **`false`** | 避免无收益 CPU 耗时；大册由 `vision.auto` 阈值开启 |

失败 **fail-open** 降级，不阻断 pipeline（§PRD 4.4）。

### 5. 分段权威链（P0）

存在三套分段逻辑，消费顺序固定：

1. `clustering.enabled=false` → Phase 2（`time_segments` / `group_assets_by_day`）  
2. `enabled` 且 GPS 覆盖率 ≥ `autoGpsMinRatio` → **geo_events** 为章 hints 主输入  
3. GPS 不足 / geo 空 → **time_segments**（`segmentMode=date_fallback`）  
4. `segmentCurateMode: date_fallback` → 强制忽略 geo segments  

**章 cap（3–5）** 最后施加，不反向改写 geo/time 原始边界。

### 6. 语义信号分工

| 信号 | 用途 |
|------|------|
| **`sceneClusterId`** | 段内 **run_aware** 屏序、组屏局部聚合（M13） |
| **`subjectClass`** | layout 评分、章 pattern；**不** 单独驱动屏序 |
| **单次 CLIP forward** | embedding + 可选 subjectClass；禁止双跑 CLIP（G-P3-C05） |

### 7. 排版约束优先级（P0）

`burstGroupId` 完整性 **>** cluster run **>** 纯 `takenAt` 时间序（G-P3-C09）。

### 8. Agent 边界

- **curate**：消费 clustering hints；负责 merge/cap/fallback  
- **narrate**：只读 curate 产出；**不**重跑 geo/CLIP、**不**改章/屏序  
- **render**：契约不变（MVP 冻结）

### 9. 增量 cache

CLIP embeddings 存 `trips/{id}/.cluster-cache/`；增量 ingest 按 asset 变化比例失效/重算（F-CLU-CACHE-*）。`structure_locked` 后追加素材不改章边界。

### 10. 确定性

`clustering.deterministic=true`（默认）：固定 seed、CPU 路径；同 fixture 双跑 hash 一致（G-P3-C08 · M12 必验）。

### 11. 用户路径

**与 Phase 2 相同**；聚类 invisible；可选 `stageHint`；无洞察工作台。

### 12. 废止

- ADR-006 全部部署档位（compose、setup-engines、Path A/B 洞察）  
- 「素材洞察工作台」移出 v0.3 roadmap（Future 另立项）  
- `curation.insights.*` 不再写入；load 时 strip（不迁移为 clustering）

---

## 后果

### 正面

- 无 Docker 安装墙；G-P2-01 不受影响  
- 与排版 vision 单线建设  
- 测试不依赖外部容器  
- auto/false 默认降低小册等待与误开 CLIP 风险  
- 确定性 + burst guard 可 CI 回归  

### 负面

- 自维护 CLIP 管道与模型版本  
- 无现成地图/洞察 UI（非本 Phase 目标）  
- 增量 cache 规则增加实现与测试面  
- DBSCAN 全 trip 重跑在增量场景仍有 CPU 成本  

---

## Re-review 触发条件

下列任一成立时，**必须** 重新评审本 ADR（或召开 Phase 3 架构 review），并更新 PRD / IMPLEMENTATION：

| # | 触发条件 | 可能动作 |
|---|----------|----------|
| **R1** | 重新引入 **外部 HTTP/Docker 引擎**（Recasa/PhotoMapAI 或同类） | 新 ADR 或 revert ADR-007 |
| **R2** | CLIP 选型变更（PyTorch ↔ ONNX ↔ 其他模型）且 **破坏** G-P3-C08 确定性 | 更新 §10 + 黄金 hash |
| **R3** | 新增 **用户可见洞察 UI** 或 selection manifest | 独立 PRD；可能 Future ADR |
| **R4** | curate 章 cap **3–5** 硬约束放宽或移除 | 重审 §5、§8.1 与 MVP 契约 |
| **R5** | `burstGroupId` 优先级让位于 cluster run，导致 **AC-P3-C09** 失败 | 重审 §7 或关闭 run_aware |
| **R6** | 增量 cache 策略变更（如 DBSCAN 改为增量聚类） | 更新 F-CLU-CACHE + 测试 |
| **R7** | ClusteringLayer **移出** import subprocess（如独立 daemon/云 API） | 重审 §1、隐私、G-P3-C06 |
| **R8** | M12-0 Spike **No-Go**（geo golden <70% 且不可调） | 仅 ship P3-Lite 或推迟 P3-Full |
| **R9** | 默认 config 改为 `enabled=true` / `vision.enabled=true` | 需 PF-P3 + G-P2-01 再验 |

**例行 review**：M13 完成（P3-Full ship）后 30 天内做一次轻量 retrospective；无触发项则 ADR 保持 Accepted。

---

## 参考

- [PRD-PHASE3.md](../PRD-PHASE3.md) v0.3.1  
- [IMPLEMENTATION-PHASE3.md](../IMPLEMENTATION-PHASE3.md) v0.3.1  
- [ACCEPTANCE-PHASE3.md](../ACCEPTANCE-PHASE3.md) v0.3.1  
- [智能排版V2.md](../智能排版V2.md)  
- [Recasa](https://github.com/yonie/recasa) · [PhotoMapAI](https://github.com/lstein/PhotoMapAI)

---

## 修订记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.1 | 2026-05-28 | 初版：原生 ClusteringLayer；废止 ADR-006 |
| v0.2 | 2026-05-28 | 对齐 PRD v0.3.1：默认 config、分段权威链、burst 优先级、deterministic、cache、narrate 边界；**Re-review triggers** |
