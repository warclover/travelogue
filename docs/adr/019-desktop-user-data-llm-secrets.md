# ADR-019 · Desktop LLM secrets（复用 user_data_dir）

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted** |
| **日期** | 2026-07-15 |
| **决策者** | 产品 + 架构（Desktop LLM Setup V1 评审） |
| **影响范围** | `travelogue/llm/user_settings.py` · `/__travelogue/llm/*` · 桌面 launcher 注入 |
| **关联** | [PRD-DESKTOP-LLM-SETUP-V1.md](../PRD-DESKTOP-LLM-SETUP-V1.md) · [ADR-018](./018-desktop-installer-layout.md) · [ADR-004](./004-studio-hub-server.md) · [ADR-008](./008-trip-storage-boundaries.md) |
| **前置** | ADR-018 冻结 `user_data_dir()`；Phase 2 Studio 单进程（ADR-004）；G-P2-05 stub 主链 |
| **编号说明** | 初稿曾占 018；与 Installer ADR-018 冲突后改为 **019** |

---

## 背景

打包桌面版实测：无应用内 LLM 配置面时，用户把「缺 Key」感知为「生成失败」。产品采用 **L0 开箱（stub）+ L1 可选自带 Key**。

密钥若写入 `trips/` 子树或误进遥测，会与相册分享混淆。密钥应落在 **ADR-018 已定义的 `user_data_dir()`** 下，不另起冲突根路径。

---

## 决策

### D1 · 复用 ADR-018 `user_data_dir()`（冻结）

| 场景 | 路径（与 ADR-018 一致） |
|------|-------------------------|
| 环境变量 | `TRAVELOGUE_USER_DATA`（最高优先） |
| Frozen · 安装模式 | `%LOCALAPPDATA%/Travelogue/` |
| Frozen · 便携模式 | exe 旁（`portable.flag`） |
| 源码开发 | 仓库 `ROOT` |

该目录内存放 LLM 相关：

| 文件 | 内容 |
|------|------|
| `secrets.json` | provider + api_key（及可选 model/base_url 缓存字段） |
| `config.user.yaml` | 非密钥 overlay（`llm.provider` / model / base_url） |

**禁止**把 API Key 写入 trip JSON、遥测 payload、或 GET status 明文。  
**禁止**另建 `%LOCALAPPDATA%/TravelogueStudio` 作为第二用户数据根（与 ADR-018 冲突）。

### D2 · 与 `trips_dir` 语义

| 根 | 职责 |
|----|------|
| **`trips_dir`** | 相册/成稿工作区（默认可为 `user_data_dir()/trips`） |
| **`secrets.json` / `config.user.yaml`** | 机器级写作引擎配置，**不进** trip 包 |

### D3 · 鉴权优先级（冻结）

```text
secrets 注入 env → config.user.yaml llm.* → 系统 / .env → 默认 stub
```

导入主链 **始终 stub 叙述**；L1 仅经显式「生成杂志感文案」升级文案。

### D4 · 安全底线（V1）

| 项 | 规则 |
|----|------|
| 落盘 | 原子写 `secrets.json` |
| ACL | 写入后 best-effort 限当前用户 |
| API | GET status 仅 `maskedKey`；读失败 → stub |
| 远期 | Windows Credential Manager = OQ，非 V1 Must |

### D5 · Studio 仍为单进程

LLM 设置 API 挂在现有 `serve --studio`（ADR-004），**不**新建配置服务或第二端口。

---

## 后果

- Desktop Installer 与 LLM Setup **共用** `user_data_dir`；Installer 文档无需 soft-fork 路径。
- 源码开发时 secrets 可能落在仓库根：须 gitignore `secrets.json` / `config.user.yaml`。
- PRD-DESKTOP-LLM-SETUP 中若仍写 `TravelogueStudio` AppData 名，以 **本文 + ADR-018** 为准修订。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-15 | 初稿（曾编号 018） |
| v1.1 | 2026-07-15 | 与 Installer ADR-018 合并冲突后改 **019**；路径对齐 `%LOCALAPPDATA%/Travelogue` |
