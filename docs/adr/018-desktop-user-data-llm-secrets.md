# ADR-018 · Desktop user_data_dir 与 LLM secrets

| 属性 | 内容 |
|------|------|
| **状态** | **Accepted** |
| **日期** | 2026-07-15 |
| **决策者** | 产品 + 架构（Desktop LLM Setup V1 评审） |
| **影响范围** | `travelogue/paths.py` · `travelogue/llm/user_settings.py` · `/__travelogue/llm/*` · 桌面 launcher |
| **关联** | [PRD-DESKTOP-LLM-SETUP-V1.md](../PRD-DESKTOP-LLM-SETUP-V1.md) · [ADR-004](./004-studio-hub-server.md) · [ADR-008](./008-trip-storage-boundaries.md) |
| **前置** | Phase 2 Studio 单进程（ADR-004）；G-P2-05 stub 主链 |

---

## 背景

打包桌面版实测：无应用内 LLM 配置面时，用户把「缺 Key」感知为「生成失败」。产品采用 **L0 开箱（stub）+ L1 可选自带 Key**。

密钥若写入 `trips/` 或 exe 旁，会与 portable 相册、分享目录混淆，且易被误同步/误提交。需独立 **用户级可写根**，与 trip 工作区分裂。

---

## 决策

### D1 · `user_data_dir()` 合同（冻结）

| 场景 | 路径 |
|------|------|
| 环境变量 | `TRAVELOGUE_USER_DATA`（最高优先） |
| Frozen · Windows | `%LOCALAPPDATA%/TravelogueStudio` |
| Frozen · 其他 | `~/.local/share/TravelogueStudio` |
| 源码开发 | `<repo>/.travelogue-user`（gitignore） |

该目录存放：

| 文件 | 内容 |
|------|------|
| `secrets.json` | provider + api_key（及可选 model/base_url 缓存字段） |
| `config.user.yaml` | 非密钥 overlay（`llm.provider` / model / base_url） |

**禁止**把 API Key 写入 trip JSON、遥测 payload、或 GET status 明文。

### D2 · 与 `trips_dir` 分裂（D-DLLM-11）

| 根 | 职责 |
|----|------|
| **`trips_dir`** | 相册/成稿工作区（可 portable、可旁路 exe） |
| **`user_data_dir`** | 机器级偏好与密钥 |

Installer / Desktop 路径文档必须引用本 ADR 与 PRD §5，**不得**另起冲突路径。

设置 UI **只读**展示两处路径（`userDataDir` + `tripsDir`），避免用户以为「删相册会丢 Key」或相反。

### D3 · 鉴权优先级（冻结）

```text
secrets 注入 env → config.user.yaml llm.* → 系统 / .env → 默认 stub
```

导入主链 **始终 stub 叙述**（D-DLLM-02）；L1 仅经显式「生成杂志感文案」升级文案。

### D4 · 安全底线（V1）

| 项 | 规则 |
|----|------|
| 落盘 | 原子写 `secrets.json` |
| ACL | 写入后 best-effort 限当前用户（Windows `icacls` / 他端 `chmod 600`） |
| API | GET status 仅 `maskedKey`；读失败 → 视为未配置 → stub |
| 远期 | Windows Credential Manager = OQ，非 V1 Must |

### D5 · Studio 仍为单进程

LLM 设置 API 挂在现有 `serve --studio`（ADR-004），**不**新建配置服务或第二端口。

---

## 后果

- Desktop Installer PRD 引用本 ADR，不 soft-fork `user_data` 路径。
- 源码开发 secrets 不进 git（`.travelogue-user/`）。
- Credential Manager / 自动导入走 LLM 仍为非目标。

---

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-15 | 首版 Accepted · Desktop LLM Setup V1 W3 |
