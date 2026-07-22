# ADR-006 · Recasa × PhotoMapAI 媒体引擎集成

| 属性 | 内容 |
|------|------|
| **DOC-STATUS** | **superseded**（继任 [ADR-007](./007-native-clustering.md) · 登记见 [DOC-STATUS.md](../DOC-STATUS.md)） |
| **状态** | **Superseded**（2026-05-28 · 见 [ADR-007](./007-native-clustering.md)） |
| **日期** | 2026-05-27 |
| **决策者** | Travelogue 产品/技术 |
| **关联 PRD** | [PRD-PHASE3.md](../PRD-PHASE3.md) v0.2.4 |
| **历史** | v0.2（双容器 + setup-engines 基线） → **v0.3**（追加 Path A 默认 + 编辑保留 + 容器路径映射 + 遥测分离） |

---

## 背景

Phase 3 需要在 ingest 之前/之后提供 **行程段（时间+地点）** 与 **场景主题（CLIP 聚类）** 洞察。Recasa 与 PhotoMapAI 均为独立开源应用。

Phase 2 承诺 **零命令线**；Phase 3 不得要求用户每次手动配置 Docker + pip + 双端口，更**不得**强制用户在体验产品价值前先安装 2GB Docker Desktop。

---

## 决策

### 0. 用户路径默认 · Path A 先快后精（v0.3 追加）

| 路径 | 行为 | 默认 |
|------|------|------|
| **Path A** | 选文件夹 → **直接 Phase 2 pipeline** → preview → 不满意时 **回流** 洞察精选 → reingest | ✅ **默认** |
| **Path B** | 选文件夹 → 洞察 → 精选 → pipeline | 设置 `insights.beforePipeline=true` 开启 |

**理由**：

1. 不牺牲 Phase 2 的 G-P2-01「20 分钟到长图」承诺  
2. 把 Docker 安装墙推后到「用户感知到洞察价值时」，降低转化漏斗断裂  
3. 5 人可用性测试（G5）验证：≥3/5 应能在 preview 自然发现「重新精选」入口

### 1. 集成形态

**Python 编排层 + HTTP API + 共享只读照片目录**；Travelogue Studio 为唯一用户入口。

### 2. 部署档位（默认 A）

| 档位 | 内容 |
|------|------|
| **A · Full Stack（默认）** | 单 `docker-compose.engines.yml`：**Recasa + PhotoMapAI 双容器**；父目录挂载 + scanSubpath |
| **B · Lite** | 仅 Recasa；无主题簇 |
| **C · Dev** | Recasa 容器 + host PhotoMapAI |

**拒绝** v0.1 默认「Recasa Docker + PhotoMap host pip」作为产品主路径——运维负担过高。

### 3. 用户安装路径

1. **触发**：Path A 用户在 preview 主动点「素材洞察」时（**非**选文件夹时）  
2. 首次：Studio **安装向导**（调用 `setup-engines.ps1 -DetectOnly` → 确认 → `-Install`）  
3. 日常：Studio **「启动分析服务」** → `travelogue engines up`  
4. 维护者：`travelogue engines status`

### 4. Orchestrator

- Recasa scan 与 PhotoMapAI index **并行**  
- `engines up` 时 **模型预下载 / warmup**  
- join 使用 **canonical path**（**容器→host 反向映射** + `resolve` + `normcase`）；commit 前 **路径对账**  
- 对账失败 **阻断 commit**（不 silent basename 匹配）

### 5. 编辑保留 · 回流 reingest（v0.3 追加）

Path A 的 preview 回流意味着 reingest 后必须 **保留** 用户已通过 `save-copy` 编辑的文案：

- 按 `assetId`（hash 稳定）优先合并；章序号 fallback  
- 章结构大变（章数差 >1 或 >30% 素材置换）时显式确认  
- **依赖 M12-0 SP-09** 验证 `assetId` 在 reingest 后的稳定性

### 6. 遥测分离 · 不入 trip.json（v0.3 追加）

行为度量（`editCount` / `sessionDurationSec` / `usedRecommendOnly` / `openedInsightsUi`）落 **`~/.travelogue/telemetry/insights-events.jsonl`**，**不写入** `trip.json`。理由：

- 用户分享/备份 trip 时不外泄使用习惯  
- 隐私可控（Studio 设置可关闭遥测）  
- Phase 4 小程序分享 schema 不必新增 strip 字段

### 7. 降级

引擎不可用 → 跳过 insights；Phase 2 pipeline 不变（NR-P3-01）。Path A 下用户根本未触达引擎，零回归风险。

### 8. M12-0

编码前 **API + 数据流 Spike**：实测 pin 版本端点、产出 golden fixtures、验证 **容器↔host 路径映射（SP-07）**、**多 photosRoots bind（SP-08）**、**save-copy/assetId 数据流（SP-09）**。

---

## 拒绝的方案

| 方案 | 原因 |
|------|------|
| monolith 合并源码 | 维护、依赖冲突 |
| 库内 import 双 FastAPI | 端口/生命周期冲突 |
| 默认 host PhotoMapAI | 违背零命令线；venv 分裂 |
| iframe 双引擎完整 UI 为主流程 | 体验分裂 |
| **Path B 默认（选文件夹即强制洞察）** | 时间-价值失衡（首次 47–65 分钟）；Docker 安装墙位于漏斗前段 |
| **遥测写入 trip.json** | 用户分享 trip 时外泄行为；schema 兼容复杂 |
| **裸字符串路径比较（host vs container）** | join 静默丢图；Windows/Linux 大小写差异 |

---

## 后果

### 正面

- **Path A 默认** → Phase 2 用户旅程零侵扰；Docker 安装墙仅对 **主动选择洞察** 的用户出现  
- pin 镜像 + client 层可应对上游变更  
- Lite 档位覆盖低配置机器  
- 遥测分离 → 用户隐私 + schema 稳定 + Phase 4 分享免改造

### 负面

- Docker Desktop 仍是 Windows 硬依赖（Full Stack；仅洞察用户触达）  
- 需维护 compose 与 PhotoMap 容器镜像  
- CI 默认不跑真引擎（nightly optional）  
- 回流 reingest 的 **编辑保留** 引入新的合并复杂度（依赖 SP-09）

---

## 何时重审（Re-review triggers）

出现下列 **任一** 事件时，应重新评估本 ADR（至少更新 PRD §4.3 Spike 清单与 pin 版本）：

| 触发事件 | 可能影响 |
|----------|----------|
| Recasa 或 PhotoMapAI **major 版本**发布（breaking API / 默认行为变更） | client 层、compose 镜像 pin、join 语义 |
| PhotoMapAI **官方 Docker 镜像**发布或维护者推荐容器化部署 | 档位 C 必要性下降；compose 构建策略 |
| Recasa **内建 CLIP/语义聚类**（或等价「主题簇」能力） | 双引擎依赖是否可降为 Lite 默认 |
| Docker Desktop / WSL2 / NVIDIA Container Toolkit **平台能力变更** | GPU passthrough、§7.4.3 CPU 降级路径 |
| M12-0 Spike **No-Go**（SP-01 父目录 scan / SP-05 容器维护契约 / **SP-07 容器路径映射** / **SP-09 assetId 稳定性** 任一失败） | 默认档位 A → B/C；Orchestrator 分支；编辑保留策略改 plan B |
| **G5 可用性测试 No-Go** 后补测仍未达 ≥3/5 | preview 发现层文案重设计；可能需要更显式的入口（顶部 banner 等） |
| Phase 2 G-P2-01 时间承诺被破坏 | NR-P3-01 失败时立即 rollback Phase 3，回归 Path A 跳过逻辑 |

**流程**：产品/技术 review → 更新 ADR 版本与 PRD → 必要时新开 Spike 子项 → 再进入下一里程碑编码。

---

## 参考

- [Recasa](https://github.com/yonie/recasa)
- [PhotoMapAI](https://github.com/lstein/PhotoMapAI)
