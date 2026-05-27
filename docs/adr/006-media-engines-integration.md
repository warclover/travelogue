# ADR-006 · Recasa × PhotoMapAI 媒体引擎集成

| 属性 | 内容 |
|------|------|
| **状态** | Accepted（v0.2 · 2026-05-27） |
| **日期** | 2026-05-27 |
| **决策者** | Travelogue 产品/技术 |
| **关联 PRD** | [PRD-PHASE3.md](../PRD-PHASE3.md) v0.2.1 |

---

## 背景

Phase 3 需要在 ingest 之前提供 **行程段（时间+地点）** 与 **场景主题（CLIP 聚类）** 洞察。Recasa 与 PhotoMapAI 均为独立开源应用。

Phase 2 承诺 **零命令线**；Phase 3 不得要求用户每次手动配置 Docker + pip + 双端口。

---

## 决策

### 1. 集成形态

**Python 编排层 + HTTP API + 共享只读照片目录**；Travelogue Studio 为唯一用户入口。

### 2. 部署档位（默认 A）

| 档位 | 内容 |
|------|------|
| **A · Full Stack（默认）** | 单 `docker-compose.engines.yml`：**Recasa + PhotoMapAI 双容器** |
| **B · Lite** | 仅 Recasa；无主题簇 |
| **C · Dev** | Recasa 容器 + host PhotoMapAI |

**拒绝** v0.1 默认「Recasa Docker + PhotoMap host pip」作为产品主路径——运维负担过高。

### 3. 用户安装路径

1. 首次：`scripts/setup-engines.ps1`（或 Studio **安装向导**）  
2. 日常：Studio **「启动分析服务」** → `travelogue engines up`  
3. 维护者：`travelogue engines status`

### 4. Orchestrator

- Recasa scan 与 PhotoMapAI index **并行**  
- `engines up` 时 **模型预下载 / warmup**  
- join 使用 **canonical path**（`resolve` + `normcase`）；commit 前 **路径对账**  
- 对账失败 **阻断 commit**（不 silent basename 匹配）

### 5. 降级

引擎不可用 → 跳过 insights；Phase 2 pipeline 不变（NR-P3-01）。

### 6. M12-0

编码前 **API Spike**：实测 pin 版本端点，产出 golden fixtures。

---

## 拒绝的方案

| 方案 | 原因 |
|------|------|
| monolith 合并源码 | 维护、依赖冲突 |
| 库内 import 双 FastAPI | 端口/生命周期冲突 |
| 默认 host PhotoMapAI | 违背零命令线；venv 分裂 |
| iframe 双引擎完整 UI 为主流程 | 体验分裂 |

---

## 后果

### 正面

- 一次性 setup 后，用户路径仍接近 Phase 2  
- pin 镜像 + client 层可应对上游变更  
- Lite 档位覆盖低配置机器

### 负面

- Docker Desktop 仍是 Windows 硬依赖（Full Stack）  
- 需维护 compose 与 PhotoMap 容器镜像  
- CI 默认不跑真引擎（nightly optional）

---

## 何时重审（Re-review triggers）

出现下列 **任一** 事件时，应重新评估本 ADR（至少更新 PRD §4.3 Spike 清单与 pin 版本）：

| 触发事件 | 可能影响 |
|----------|----------|
| Recasa 或 PhotoMapAI **major 版本**发布（breaking API / 默认行为变更） | client 层、compose 镜像 pin、join 语义 |
| PhotoMapAI **官方 Docker 镜像**发布或维护者推荐容器化部署 | 档位 C 必要性下降；compose 构建策略 |
| Recasa **内建 CLIP/语义聚类**（或等价「主题簇」能力） | 双引擎依赖是否可降为 Lite 默认 |
| Docker Desktop / WSL2 / NVIDIA Container Toolkit **平台能力变更** | GPU passthrough、§7.4.3 CPU 降级路径 |
| M12-0 Spike **No-Go**（如 SP-01 父目录 scan 不可行、SP-06 PhotoMap 容器不可行） | 默认档位 A → B/C；Orchestrator 分支 |

**流程**：产品/技术 review → 更新 ADR 版本与 PRD → 必要时新开 Spike 子项 → 再进入下一里程碑编码。

---

## 参考

- [Recasa](https://github.com/yonie/recasa)
- [PhotoMapAI](https://github.com/lstein/PhotoMapAI)
