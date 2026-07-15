# Travelogue · 桌面首启能力分层与写作引擎配置 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | **v1.1.0** |
| **状态** | **Conditional Go · Must-Fix 已回写 · W1a 已落地核心面** |
| **主题代号** | 「桌面首启 · 能力分层」— L0 开箱成稿 · L1 可选升级写作引擎 |
| **触发来源** | 2026-07-15 打包 `.exe` 实测：缺 LLM API 配置页/接口，用户感知为「生成失败」；产品讨论采用降级原则 |
| **前置条件** | Phase 2 Studio Hub 可用（`python -m travelogue studio` / M11 `TravelogueStudio.exe`）；主链路 stub narrate 已落地（G-P2-05）；长图导出可用（[PRD-LONGSHOT-2.0.md](./PRD-LONGSHOT-2.0.md) / 导出门面）；[PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) 帮助合同有效（可并行，不阻塞本主题 W0） |
| **关联文档** | [PRD-PHASE2.md](./PRD-PHASE2.md) G-P2-05 · US-P2-08 · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) · [PRD-PREVIEW-REFINE-UX-V1.1.md](./PRD-PREVIEW-REFINE-UX-V1.1.md) §8 · [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) · [ERROR-CODES.md](./ERROR-CODES.md) · [adr/004-studio-hub-server.md](./adr/004-studio-hub-server.md) · README 索引中的 Desktop Installer（实体 PRD **待建**；本文不替代安装包规格） |
| **评审记录** | [acceptance-records/desktop-llm-setup-v1-review-2026-07-15.md](./acceptance-records/desktop-llm-setup-v1-review-2026-07-15.md) |
| **验收** | [ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md](./ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) · 本文 §10 |
| **实施清单** | [IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md](./IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md) |
| **线框** | [wireframes/desktop-llm-setup-v1-wireframe.html](./wireframes/desktop-llm-setup-v1-wireframe.html)（F1–F3/F5） |
| **更新日期** | 2026-07-15 |

> **定位**
>
> 打包桌面版（及同等 Studio 本地体验）已具备 **无 API Key 的完整主链**（导入 → stub 文案 → 预览 → 长图），但 **没有首启能力说明**，也 **没有面向非开发者的写作引擎配置面**。  
> 用户第一次打开 `.exe` 时，容易把「杂志感文案未配置」误读成「整次生成失败」。
>
> **本 PRD 不改算法默认、不强迫配 Key、不做官方代付 LLM。**  
> 它把已有工程能力产品化为：**L0 本机核心开箱可用 + L1 自带 Key 可选升级**，并补齐首启引导、设置页、读写 API、文案归因与验收门。
>
> **与相邻主题的关系**
>
> | 主题 | 解决什么 | 与本文关系 |
> |------|----------|------------|
> | **Phase 2 / Studio Hub** | stub 默认 · 可选 LLM narrate | 本文 **兑现体验合同**，不改默认 provider=stub |
> | **帮助系统 V1** | 首访主链「导入→验货→长图→发群」 | 本文 **不打断主链**；写作引擎为支线升级；复用 ? / seen 合同 |
> | **精修 UX V1.1** | 「生成不可用 · 未配置写作引擎」 | 本文 **改写归因与 CTA**，链到配置 |
> | **Desktop Installer**（待建） | 安装包 / 路径 / 发布门 | 本文定义 **user_data_dir 与密钥落盘合同**；安装 UI 仍归 Installer |
> | **审美 MLLM / 装饰句 LLM** | 可选增强 | 归 **L2 远期**；V1 只暴露写作引擎（杂志感文案） |

> **产品共识（六条铁律）**
>
> 1. **L0 永不因缺 Key 而失败** — 无 API 时主生成必须可成稿、可预览、可出长图。  
> 2. **配置是升级，不是门槛** — 首启可跳过；禁止强制不可跳过的多步「必须填 Key」向导。  
> 3. **失败归因局部化** — 仅「杂志感文案」路径可因缺 Key 禁用/报错；禁止整页/整次导入显示为生成失败。  
> 4. **密钥不出本机、不进遥测** — 不写进 trip、不打日志明文、不进 analytics payload。  
> 5. **非开发者可配完** — 不要求手改 `config.yaml` / `.env` / 系统环境变量（开发者模式可保留）。  
> 6. **与帮助系统同构** — 不做全站 Product Tour；忙碌态（导入/导出中）不弹配置卡。

---

## 0. 读者指南

| 章节 | 必须澄清的问题 |
|------|----------------|
| §0.1 | 能力分层与术语 |
| §1 背景 | As-Is 缺口；用户首启真实路径 |
| §2 目标/非目标 | 范围锁死 |
| §3 体验合同 | 首启场景剧本 + L0/L1 承诺 |
| §4 信息架构 | 触点挂载 · 设置页 · 帮助条目 |
| §5 API 与数据 | user_data · 读写 · ping · 安全 |
| §6 文案与错误 | 归因改写 · ERROR-CODES |
| §7 埋点 | 漏斗可观测（无密钥） |
| §8 非功能 | 安全 · 兼容 · A11Y |
| §9 里程碑 | W0–W3 Go/No-Go |
| §10 验收 | 可执行 AC |
| §11 风险与开放问题 | 默认建议 |
| §12 附录 | 实现锚点 · 首启一览 |
| §13 | 评审审核清单 |

### 0.1 术语与能力分层

| 层级 | 名称 | 用户一句话 | 依赖 |
|------|------|------------|------|
| **L0** | 本机核心 | 「选文件夹就能出杂志卷轴和长图」 | 无外部 LLM API |
| **L1** | 写作引擎升级 | 「配自己的 API Key，文案更像杂志」 | 用户自备 DeepSeek / 通义等兼容 Key |
| **L2** | 增强视觉（非 V1 交付） | 「可选 AI 审美」等 | 另开关；默认关；本文只预留入口位置 |

| 术语 | 定义 |
|------|------|
| **写作引擎** | 用户可见名；对应工程 `llm.provider` ∈ `{deepseek, dashscope}` + 有效 API Key |
| **本机文案 / 规则文案** | `narrate_provider=stub` 产出；默认主链 |
| **杂志感文案** | 预览「更多工具」中可选 LLM 重写；需 L1 |
| **能力卡** | 首启非阻断说明：L0 已可用 / L1 可升级 |
| **user_data_dir** | 用户可写配置根（见 §5.1）；与 `exe_dir` / `_MEIPASS` 分离 |

---

## 1. 背景与问题

### 1.1 产品一句话（本主题前提）

把旅行照片在**本机**自动变成杂志风卷轴 + 可发微信的长图。默认无需注册、**默认不要求 API Key**（G-P2-05）。杂志感 LLM 文案是进阶选项（US-P2-08）。

### 1.2 As-Is（工程已有 vs 体验缺口）

| 层 | 现状 | 文件/锚点 | 缺口 |
|----|------|-----------|------|
| 主 pipeline | 无 Key → 强制 stub，可成稿 | `studio_narrate.resolve_studio_narrate_provider` | 用户不知道「已成功用本机文案」 |
| LLM 状态只读 | `GET /__travelogue/config` → `llmAvailable` / `llmProvider` | `studio_narrate.studio_llm_status` · `config_handlers` | 无写入面 |
| PATCH 白名单 | clustering / vision / layout / studio… | `loader.patch_config_file` | **不含 `llm.*`** |
| 密钥 | 仅 env / `.env`（`api_key_env`） | `llm/client.py` · `env.py` | exe 旁找 `.env` 不友好 |
| 首页设置 | 「导入偏好」popover | `studio-home-v2.html` | 无写作引擎区 |
| 预览 LLM 按钮 | 不可用则 disabled +「生成不可用 · 未配置写作引擎」 | `init-v3.js` · sheet | 像整单失败；无「去配置」 |
| Desktop | launcher 只设 trust；`exe_dir()/trips` | `desktop/launcher.py` · `paths.py` | **无 user_data_dir；无配置 UI** |
| 帮助系统 | 首访教导入/长图/发群 | Help Onboarding V1 | 未覆盖写作引擎支线 |

### 1.3 问题清单（P-DLLM-*）

| ID | 问题 | 用户感知 | 严重度 |
|----|------|----------|--------|
| **P-DLLM-01** | exe 无 LLM 配置页/接口 | 「没法配，生成失败」 | P0 |
| **P-DLLM-02** | 缺 Key 的禁用文案像整次失败 | 放弃主链 | P0 |
| **P-DLLM-03** | 首启未说明 L0 已可用 | 以为必须先配 API | P0 |
| **P-DLLM-04** | frozen 下 config/`.env` 路径脆弱 | 开发者路径也配不通 | P1 |
| **P-DLLM-05** | 配完无法自测连通 | 配错 Key 才在生成时爆 | P1 |
| **P-DLLM-06** | 帮助/设置无「写作引擎」条目 | 回访找不到入口 | P1 |
| **P-DLLM-07** | L0 长图未进打包验收门 | 回归时可能静默坏 | P1 |

### 1.4 核心判断

1. **根因是体验与配置面，不是缺 offline 引擎。** stub + 长图已是 L0。  
2. **正确产品动作**：把 L0 说清楚 + 给 L1 一条非开发者配置路径。  
3. **错误产品动作**：把「填 API Key」做成启动门槛，或另造一套弱化排版。

---

## 2. 目标与非目标

### 2.1 产品目标

| ID | 目标 | 衡量 |
|----|------|------|
| **G-DLLM-01** | 第一次打开应用的用户，**不配 Key** 也能在指引下完成「导入 → 预览 → 长图」 | AC-DLLM-01～03；非技术用户狗粮 |
| **G-DLLM-02** | 愿意升级的用户，**仅在应用内**完成 Provider + Key 配置与连通测试 | AC-DLLM-10～14 |
| **G-DLLM-03** | 任何「缺 Key」失败都表现为 **L1 局部不可用**，并提供「去配置 / 稍后再说」 | AC-DLLM-04～06 |
| **G-DLLM-04** | 密钥只落在 user_data，**永不**出现在遥测与 trip 产物 | AC-DLLM-20 |
| **G-DLLM-05** | 与 Phase 2 / 帮助系统铁律兼容：默认 stub、不强制 tour、忙碌态零打扰 | 评审清单 §13 |

### 2.2 非目标（V1 明确不做）

- 官方代付 / 内置共享 API Key / 云端代理计费  
- 用户账号体系、登录后同步配置  
- 把审美 MLLM、decor_line LLM、多模型路由做成设置主路径（属 L2）  
- 修改 stub 文案算法质量（Copy Optimization 另轨）  
- 完整 Windows 安装器 UI、自动更新（Desktop Installer）  
- 强制用户从 stub 升级到 LLM（导入后自动调 LLM）  
- 在 config PATCH 里开放任意 YAML 自由编辑  
- macOS / Linux 打包（合同可复用；V1 验收以 Windows exe 为准）

### 2.3 成功指标（定性 + 轻量埋点）

| 指标 | 目标（V1 狗粮） |
|------|----------------|
| 无 Key 首访成稿率 | 选夹成功后 ≥95% 到达预览（环境正常机） |
| 无 Key 首访长图率 | 到达预览后，愿意导出的用户可完成长图（功能门：AC 必过） |
| 「误以为必须配 Key」 | 能力卡曝光后，跳过率可接受；配置转化非 KPI 硬门槛 |
| L1 配置成功率 | 进入设置并保存的用户，ping 成功占比可观测 |

---

## 3. 体验合同

### 3.1 首启场景剧本（以「第一次打开 TravelogueStudio.exe」为准）

**Persona A · 分享者（主用户）** — 不愿配 Key  

| 步 | 用户看到/做 | 系统必须 |
|----|-------------|----------|
| 1 | 双击 exe，浏览器打开 Studio 首页 | 服务起来；无终端操作 |
| 2 | 出现 **能力卡**（可关） | 说明 L0 已可用；CTA：`开始导入` / `了解写作引擎` / `关闭` |
| 3 | 选照片文件夹 → 等待 Job | **忙碌态不弹**能力卡/配置（D-DLLM-08） |
| 4 | FirstSuccess → 打开预览 | 文案为 stub；不弹「请先配置 API」 |
| 5 | 保存长图 → 发群指引 | L0 闭环完成 |

**Persona B · 进阶创作者** — 想要杂志感文案  

| 步 | 用户看到/做 | 系统必须 |
|----|-------------|----------|
| 1–2 | 同 A；或在能力卡点「了解写作引擎」 | 进入设置「写作引擎」区，非阻断主链 |
| 3 | 选 Provider → 粘贴 Key →「测试连接」 | ping 成功才标「已就绪」；失败给中文原因 |
| 4 | 保存后导入或对已有 trip 点「生成杂志感文案」 | `llmAvailable=true`；按钮可用 |
| 5 | 仍可随时清空 Key 回到 L0 | 降级即时生效，已有 trip 不删 |

### 3.2 能力承诺表（对外可引用）

| 能力 | L0（无 Key） | L1（已配置且 ping 过/可用） |
|------|--------------|------------------------------|
| 选文件夹导入 | ✅ | ✅ |
| 分章 / 策展 / 排版 / 预览 | ✅ | ✅ |
| 本机（stub）文案 | ✅ 默认 | ✅ 仍可保留为底 |
| 杂志感文案（LLM 重写） | ❌ 入口可点进配置，不假装可用 | ✅ |
| 精修 / 改标题等 | ✅ | ✅ |
| **保存长图 PNG** | ✅ **必保** | ✅ |
| zip / 高级导出 | ✅（若产品已开放） | ✅ |
| 审美 MLLM 等 | ❌（默认关；非 V1） | 非 V1 |

### 3.3 冻结决策（D-DLLM-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-DLLM-01** | **方案 A：能力卡非阻断（CTA 收紧）** | 主按钮仅「开始导入」+关闭；「升级 AI 文案」为文内链（MF-01） |
| **D-DLLM-02** | **L0 默认 stub 不变** | 即使已配 L1，导入主链仍 stub；须明示「需点击生成杂志感」（MF-06） |
| **D-DLLM-03** | **外层「设置」· 内保留「导入偏好」** | 写作引擎/AI 文案为第二组；容器为 Modal（`llm-settings.js`） |
| **D-DLLM-04** | **密钥落盘：user_data 专用 secrets 文件** | 进程内注入 `api_key_env`（MF-03） |
| **D-DLLM-05** | **Provider V1 仅 deepseek / dashscope** | 与 `PROVIDER_PRESETS` 对齐；高级「自定义 base_url」折叠 |
| **D-DLLM-06** | **禁用文案改写** | 「当前为本机文案 · 配置写作引擎后可升级」 |
| **D-DLLM-07** | **帮助抽屉新增 H7「AI 文案」** | H6 已为封面封底；设置空态含获取 Key 外链 + 深链 H7（MF-05） |
| **D-DLLM-08** | **忙碌态零配置打扰** | 与 D-HELP-08 同构 |
| **D-DLLM-09** | **seen 键全局** | `travelogue.desktop.capabilityCard.v1`（W2） |
| **D-DLLM-10** | **开发模式保留 yaml/env** | **鉴权优先级**：secrets 注入 > config.user provider > env/.env > 默认 stub |
| **D-DLLM-11** | **不强制迁移 trips** | 仅配置与密钥进 user_data |
| **D-DLLM-12** | **launcher 确保 user_data** | 启动时 `user_data_dir(ensure=True)` + inject |
| **D-DLLM-13** | **能力卡 vs Help 仲裁** | 同帧只显示能力卡；关闭后本会话不自动弹非关键 Help L1（MF-09） |

### 3.4 与帮助系统的边界

- 首访主链仍以 Help Onboarding 为准（文件夹心智 → 验货 → 长图 → 发群）。  
- 能力卡属于 **L0 认知补丁**，文案预算 ≤ 2 句 + 2 主 CTA；禁止连环气泡。  
- 写作引擎配置属于 **支线**；FirstSuccess 主 CTA 不得改为「去配置 API」。

---

## 4. 信息架构与交互规格

### 4.1 触点矩阵

| ID | 触点 | 触发 | 内容要点 | seen / 门禁 |
|----|------|------|----------|-------------|
| **T-CAP-01** | 首页能力卡 | 首次首页 idle 且未见过；非 busy | 标题：「本机即可出长图」；正文：无需 API 可导入成稿；升级写作引擎可选 | `capabilityCard.v1`；busy 门禁 |
| **T-CAP-02** | 设置 · 写作引擎 | 设置入口；能力卡「了解」；预览 CTA | Provider / Key / 测试 / 状态徽章 | 无 |
| **T-CAP-03** | 预览 LLM 行 | `llmAvailable=false` | 状态：「本机文案 · 可升级写作引擎」+ 按钮「配置写作引擎」 | 无 |
| **T-CAP-04** | 帮助 H7 | `?` 抽屉 / 设置「了解更多」 | 何时需要 Key、怎么配、隐私说明 | 无 |
| **T-CAP-05** | 导入成功轻提示（可选 W2） | FirstSuccess 关闭后首次预览 | 一行：「当前为本机文案」；可关 | `stubHint.v1` |

### 4.2 能力卡规格（F1）

```
┌─────────────────────────────────────────────┐
│  本机即可生成杂志卷轴与长图                    │
│  照片留在你的电脑。不必先配置 AI 接口。         │
│  若需要更强的杂志感文案，可稍后配置自己的 API。 │
│                                             │
│  [ 开始导入 ]                          [ × ] │
│  文内链：升级 AI 文案（可选）→                │
└─────────────────────────────────────────────┘
```

| 规则 | 规格 |
|------|------|
| 出现次数 | 每个安装/用户数据目录 **一次**（seen）；帮助重播可再显 |
| 主 CTA | 「开始导入」→ 聚焦/滚动到导入入口（等同空态主按钮） |
| 次动作 | **文内链**「升级 AI 文案（可选）」→ 打开设置 Modal（非第三按钮） |
| 关闭 | × / Esc 写 seen；不阻断 |
| 禁止 | 倒计时强制跳转；不可关闭；要求先填 Key；三按钮并排 |

### 4.3 设置 · 写作引擎区规格（F2）

首页原「导入偏好」**更名为「设置」**（或保留触发文案「设置」，内含两 Tab/两组：导入偏好 | 写作引擎）。

**写作引擎组字段：**

| 字段 | 控件 | 校验 |
|------|------|------|
| 状态徽章 | `未配置` / `已就绪` / `连接失败` | 来自服务端 status API |
| 服务商 | 单选：DeepSeek / 通义千问（DashScope） | 必选其一才允许保存 Key |
| API Key | password 输入；可「显示」 | 非空才允许「测试连接」 |
| 模型 | 只读默认或高级折叠可选 | 默认用 preset |
| 自定义 API 地址 | 高级折叠 | 可选；空则 preset base_url |
| 测试连接 | 按钮 | 调 ping；展示成功/失败中文 |
| 保存 | 按钮 | 写入 user_data；刷新 `llmAvailable` |
| 清除配置 | 危险次要 | 回到 stub；确认 Modal |

**空态说明（未配置时）：**  
「不配置也可以正常导入、排版和导出长图。配置后可在预览中生成杂志感文案。」

### 4.4 预览工具条规格（F3）

| 状态 | 按钮 | 辅助文案 |
|------|------|----------|
| `llmAvailable=true` | 「生成杂志感文案」可用 | 保持现有确认：「将调用 LLM 重写…」 |
| `llmAvailable=false` | **不要**仅 disabled 无出口；改为次按钮「配置写作引擎」或 disabled 主按钮 + 旁路链接 | **新文案**：「当前为本机文案 · 配置写作引擎后可升级」 |

点击「配置写作引擎」：打开首页设置锚点（`#settings=writing`）或 Studio Modal 内嵌同一表单（实现任选，**同一 API**）。

### 4.5 帮助 H7 规格（F4）

| 段 | 内容 |
|----|------|
| 什么时候需要 | 想要 AI 杂志感文案时；出长图不需要 |
| 怎么配 | 三步：打开设置 → 选服务商 → 粘贴 Key → 测试 |
| 隐私 | Key 只存在本机；照片默认不上传；调用写作引擎时仅发送文案所需摘要 |
| 出问题 | 连接失败常见原因：Key 错、网络、服务商余额 |

> **ID 说明**：现网帮助 H6 已用于「怎么换封面封底」；本主题落地为 **H7**。

---

## 5. 数据、路径与 API 合同

### 5.1 user_data_dir（必须新增）

| 运行态 | `user_data_dir` 默认 |
|--------|----------------------|
| **frozen exe** | `%LOCALAPPDATA%/TravelogueStudio/`（Windows） |
| **源码 / 非 frozen** | 仍可用项目 `ROOT`；但 UI 写入建议同样落到 `user_data_dir`，避免污染仓库（可用 env `TRAVELOGUE_USER_DATA` 覆盖） |

目录内容（V1）：

```text
user_data_dir/
  config.user.yaml      # 可含 llm.provider / model / base_url / api_key_env 名；不含明文 Key 亦可
  secrets.json          # 或 secrets.yaml · 权限收紧 · 含 api_key 明文（本机）
  # trips 仍默认 exe_dir()/trips（D-DLLM-11 不强制迁 trips）
```

| ID | 决策 |
|----|------|
| **D-DLLM-11** | V1 **不强制**迁移 trips 到 AppData；只把 **配置与密钥** 迁到 user_data，降低与现网 portable 行为冲突 |
| **D-DLLM-12** | launcher / `get_config` 启动时把 user_data 纳入加载链（见下） |

### 5.2 配置加载顺序（实现合同）

自高到低合并（后者不覆盖「secrets 已提供的 key」语义以代码为准，但文档冻结意图如下）：

1. 内置默认（`provider=stub`）  
2. 捆绑/旁路只读 `config.yaml`（若有）  
3. `user_data_dir/config.user.yaml`  
4. 环境变量 / `.env`（开发者）  
5. `user_data_dir/secrets.json` 注入运行时 Key（**最高优先级用于鉴权**）

`studio_llm_status`：非 stub 且能 `resolve_llm_runtime` → `llmAvailable=true`。

### 5.3 HTTP API（Studio）

基路径保持 `/__travelogue/`。V1 新增（命名可微调，验收锁语义）：

#### `GET /__travelogue/llm/status`

**响应 200 示例：**

```json
{
  "llmAvailable": false,
  "llmProvider": "stub",
  "tier": "L0",
  "configured": false,
  "maskedKey": null,
  "lastPingOk": null,
  "capabilities": {
    "import": true,
    "layout": true,
    "stubNarrate": true,
    "llmNarrate": false,
    "longshot": true
  }
}
```

规则：

- **永不**返回完整 API Key  
- `maskedKey` 仅如 `sk-***abcd`（有则）  
- `tier`：`L0` \| `L1`  
- 现有 `GET /__travelogue/config` 的 `llmAvailable` **保持兼容**；可额外附 `llmTier`（可选）

#### `POST /__travelogue/llm/settings`

**请求：**

```json
{
  "provider": "deepseek",
  "apiKey": "sk-...",
  "model": null,
  "baseUrl": null
}
```

**行为：**

- 校验 provider ∈ 白名单  
- 写入 secrets + config.user  
- `get_config(reload=True)`  
- 返回与 status 同形（仍无完整 Key）  
- 非法 → 400 + 稳定 error code

#### `POST /__travelogue/llm/ping`

**请求：** 空 body 或 `{ "provider", "apiKey"? }`（若带 Key 则测临时值不强制先保存——**推荐支持**，减少「先保存错误 Key」）

**响应：** `{ "ok": true, "message": "..." }` 或 400/`E_LLM_*`

复用 `travelogue.llm.client.llm_ping`。

#### `DELETE /__travelogue/llm/settings`

清除 user_data 中的写作引擎配置，回到 stub；200 + status。

### 5.4 安全合同

| 规则 | 要求 |
|------|------|
| 日志 | 禁止打印 Key；错误信息打码 |
| 遥测 | 只允 `llm_tier` / `provider` / `ping_ok` 布尔；禁 Key、禁 base_url 若含 token |
| 文件 | secrets 写入后尝试限制 ACL（Windows：当前用户可读） |
| CSRF/本地 | 保持现有 Studio 本机信任模型；不新增公网暴露 |
| 备份 | 文档说明：卸载可能保留 AppData；清除配置入口必有 |

### 5.5 实现锚点（供 IMPLEMENTATION 引用）

| 模块 | 路径 |
|------|------|
| paths | `travelogue/paths.py` 增 `user_data_dir()` |
| launcher | `travelogue/desktop/launcher.py` 启动时确保目录存在 |
| config merge | `travelogue/config/loader.py` / `runtime.py` |
| handlers | 新建 `studio_handlers/llm_settings_handlers.py` 或并入 `config_handlers.py` |
| 路由 | `studio_dispatch.py` |
| 状态 | `studio_narrate.studio_llm_status` 扩展字段 |
| 前端设置 | `studio-home-v2.html` + 对应 JS（新建 `js/llm-settings.js` 建议） |
| 预览 | `preview-toolbar/init-v3.js` · `preview-toolbar-v3-sheet.js` |
| 帮助 | `help-drawer.js` / `help-onboarding.js` 增 H6 |
| 错误文案 | `studio_errors.py` · `ERROR-CODES.md` · `js/constants.js` |

---

## 6. 文案与错误码

### 6.1 用户可见文案（冻结）

| 场景 | 旧（废止作主文案） | 新（V1） |
|------|-------------------|----------|
| 预览 LLM 不可用 | 生成不可用 · 未配置写作引擎 | **当前为本机文案 · 配置写作引擎后可升级** |
| `E_LLM_AUTH` 用户句 | 未配置 LLM API Key，无法生成杂志感文案 | **要生成杂志感文案，请先在设置中配置写作引擎**（可带链） |
| 能力卡标题 | — | **本机即可生成杂志卷轴与长图** |
| 状态 L0 | — | **本机核心** |
| 状态 L1 | — | **写作引擎已就绪** |
| ping 失败 | 技术栈信息 | 映射中文：`Key 无效或无余额` / `网络不通` / `服务商不可用` |

### 6.2 ERROR-CODES 增补

在 [ERROR-CODES.md](./ERROR-CODES.md) 与 `studio_errors.py` 对齐：

| 代码 | 何时 | 用户文案 |
|------|------|----------|
| `E_LLM_AUTH` | 无 Key / Key 被拒 | §6.1 |
| `E_LLM_NETWORK` | 网络 | 保持/微调「网络中断，请重试」 |
| `E_LLM_STUB` | 内部：provider=stub 调 LLM | 不直接给终端用户；UI 应走「未配置」 |
| `E_LLM_PING` | ping 形态异常 | 连接测试失败，请检查 Key 或稍后重试 |

主生成路径 **禁止** 因 stub 抛到导入失败面。

---

## 7. 埋点

事件前缀建议：`desktop_llm_*` 或复用现有 analytics 总线。

| 事件 | 属性（无密钥） | 目的 |
|------|----------------|------|
| `capability_card_show` | — | 曝光 |
| `capability_card_cta` | `cta=import\|configure\|dismiss` | 分流 |
| `llm_settings_open` | `source=card\|settings\|preview\|help` | 入口 |
| `llm_ping` | `ok=bool` · `provider` | 配置质量 |
| `llm_settings_save` | `provider` · `ok=bool` | 转化 |
| `llm_settings_clear` | — | 降级 |
| `llm_narrate_click` | `available=bool` | 与现网对齐 |

**禁止**属性：apiKey、任何 token 子串、完整 base_url 查询串。

---

## 8. 非功能

| 域 | 要求 |
|----|------|
| 性能 | 能力卡不阻塞首屏可交互；settings/ping 超时与 `llm.timeout_sec` 对齐并有取消态 |
| A11Y | 能力卡 `role=dialog`；Esc 关闭；焦点回设置按钮 |
| 兼容 | Windows 10+ · 现网 Chrome/Edge 打开 Studio；源码 `python -m travelogue studio` 同合同 |
| 回归 | 无 Key 狗粮路径列入打包冒烟（§10） |
| i18n | V1 中文主文案；英文非目标 |

---

## 9. 里程碑与 Go/No-Go

| 波次 | 范围 | Go/No-Go |
|------|------|----------|
| **W0** | PRD 评审；线框 F1–F3；确认 D-DLLM-01～12；ERROR-CODES 文案草案 | Conditional Go → 可开 W1 |
| **W1** | user_data_dir + GET/POST/DELETE llm API + ping；设置写作引擎 UI；预览文案改写；无 Key 冒烟 | **无 Key 必出预览+长图** 否则 No-Go |
| **W2** | 能力卡 T-CAP-01；H6；seen/重播；埋点 | 首启狗粮通过 |
| **W3** | 打磨高级 base_url、ACL、帮助深链、打包验收记录 | 可标 V1 Done |

**不阻塞：** Desktop Installer 安装包美化、自动更新、官网 `/install`。

---

## 10. 验收标准（AC）

### 10.1 L0 开箱（P0）

| ID | 给定 | 当 | 则 |
|----|------|-----|-----|
| **AC-DLLM-01** | 干净机器；从未配置 Key；启动 TravelogueStudio.exe（或同等 studio） | 完成导入至预览 | 成功；`narrate` 为 stub；**无**「生成失败」整页误导 |
| **AC-DLLM-02** | 同上，已在预览 | 保存长图 | PNG 落盘；Task Dock/导出门面成功态可见 |
| **AC-DLLM-03** | 同上 | 观察首启 | 能力卡可关闭；关闭后可导入；**不**强制填 Key |
| **AC-DLLM-04** | `llmAvailable=false` | 打开预览更多工具 | 文案为 §6.1 新句；存在「配置写作引擎」出口 |
| **AC-DLLM-05** | 未配置时调用 LLM narrate API | POST 杂志感文案 | 400/`E_LLM_AUTH`；**不影响**已有预览与再次长图 |
| **AC-DLLM-06** | 导入 Job 进行中 | — | **不**弹出能力卡 |

### 10.2 L1 配置（P0/P1）

| ID | 给定 | 当 | 则 |
|----|------|-----|-----|
| **AC-DLLM-10** | 打开设置写作引擎 | 选择 DeepSeek，粘贴有效 Key，测试连接 | ping ok；状态「已就绪」 |
| **AC-DLLM-11** | 测试成功后保存 | 刷新 `GET .../llm/status` 与 `/config` | `llmAvailable=true`；`tier=L1`；响应无完整 Key |
| **AC-DLLM-12** | L1 已就绪 | 预览点「生成杂志感文案」 | 可启动；不再显示未配置禁用主态 |
| **AC-DLLM-13** | 错误 Key | ping | 失败中文原因；不标「已就绪」 |
| **AC-DLLM-14** | 已配置 | 清除配置 | 回 L0；杂志感入口回到可配置态；长图仍可用 |
| **AC-DLLM-15** | frozen | 查看落盘位置 | secrets 在 `%LOCALAPPDATA%/TravelogueStudio/`（或文档声明的 user_data）；**不在** `_MEIPASS` |

### 10.3 安全与埋点

| ID | 要求 |
|----|------|
| **AC-DLLM-20** | 任意成功/失败日志与 analytics 抽样 **不含** API Key 明文 |
| **AC-DLLM-21** | `GET` status/config **不含**完整 Key |
| **AC-DLLM-22** | 能力卡 CTA / ping / save 事件可在本地 analytics 或日志探针中观测（测试环境） |

### 10.4 打包冒烟清单（发布门建议）

发布 Desktop 构建前最少勾选：

- [ ] 无 Key：导入 demo/小相册 → 预览 → 长图  
- [ ] 无 Key：杂志感入口文案正确且可进设置  
- [ ] 有 Key（狗粮 Key）：ping → 保存 → 杂志感文案一轮  
- [ ] 清除配置后恢复 L0  

---

## 11. 风险与开放问题

### 11.1 风险

| 风险 | 缓解 |
|------|------|
| 用户把「本机文案」质量当成产品缺陷 | H6 + 能力卡降低预期；Copy 优化另轨 |
| secrets 明文被同源恶意软件读取 | ACL + 文档；远期 Credential Manager（OQ） |
| 与 portable「一切在 exe 旁」心智冲突 | D-DLLM-11 保留 trips 旁路；设置页展示「配置文件位置」只读路径 |
| 能力卡与 Help L1 抢注意力 | 文案预算限制；busy 同门禁；FirstSuccess 不改主 CTA |
| 自动 LLM 导入（未做）被进阶用户要 | OQ-DLLM-02；V1 明确不做 |

### 11.2 开放问题（OQ）

| ID | 问题 | 默认建议（评审可改） |
|----|------|----------------------|
| **OQ-DLLM-01** | Key 是否进 Windows Credential Manager | V1 明文 secrets + ACL；V1.1 再升 |
| **OQ-DLLM-02** | 配好 L1 后导入是否自动走 LLM | **默认否**；保持显式「生成杂志感文案」 |
| **OQ-DLLM-03** | 能力卡与 Help 首访谁先 | **已关闭** → **D-DLLM-13** |
| **OQ-DLLM-04** | 是否在 FirstSuccess 提写作引擎 | **否**（D 与帮助铁律）；避免打断发群主链 |
| **OQ-DLLM-05** | 自定义 OpenAI 兼容端点 | V1 高级折叠可选；主推两个 preset |
| **OQ-DLLM-06** | Desktop Installer PRD 谁写 user_data | **本文锁合同**；Installer 引用本文 §5，不另起冲突路径 |

---

## 12. 附录

### 12.1 首访一览（分享者 · 无 Key）

```text
打开 exe
  → 能力卡（可关）「本机即可出长图」
  → 开始导入
  → Job（无配置弹窗）
  → FirstSuccess → 预览（stub 文案）
  → 保存长图 → 发群指引
  → （可选）设置里以后再配写作引擎
```

### 12.2 首访一览（进阶 · 要配 Key）

```text
打开 exe
  → 能力卡「配置写作引擎」或稍后「设置」
  → 选服务商 → 粘贴 Key → 测试 → 保存
  → 导入成稿（仍默认 stub）或预览点「生成杂志感文案」
  → 长图导出不受影响
```

### 12.3 与 Phase 2 目标映射

| Phase 2 | 本文 |
|---------|------|
| G-P2-05 默认不依赖 Key | G-DLLM-01 / L0 表 / AC-01～02 |
| US-P2-08 可选杂志感 | L1 / AC-10～12 |
| US-P2-01 双击打开 | 场景剧本 §3.1 |
| Persona A 不愿配 Key | 铁律 1–2 · 能力卡可跳过 |

### 12.4 线框帧清单（W1 前）

| 帧 | 内容 |
|----|------|
| F1 | 能力卡 |
| F2 | 设置 · 写作引擎（空/已就绪/失败） |
| F3 | 预览 LLM 行 L0/L1 |
| F4 | 帮助 H6 |
| F5 | 清除配置确认 Modal |

### 12.5 修订历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | 2026-07-15 | 评审 Conditional Go · 回写 MF-01～10 · D-DLLM-13 · W1a 核心面落地 |
| v1.0.0 | 2026-07-15 | 首版：L0/L1 分层 · 首启能力卡 · user_data 配置 API · 文案归因 · AC |

---

## 13. 评审审核清单

评审请逐条表态（OK / 需改 / 反对）：

- [ ] **铁律**：同意「L0 永不因缺 Key 失败」与「配置非门槛」  
- [ ] **D-DLLM-01**：能力卡非阻断（非强制 wizard）  
- [ ] **D-DLLM-02**：导入默认仍 stub；LLM 仅显式升级  
- [ ] **D-DLLM-03/07**：设置入口 + H6  
- [ ] **D-DLLM-04/11/12**：user_data 存密钥；trips 不强制迁移  
- [ ] **§5 API**：status / settings / ping / delete 语义足够开工  
- [ ] **§6 文案**：同意废止「生成不可用」作主归因  
- [ ] **§10 AC**：无 Key 长图与有 Key ping 均为发布门  
- [ ] **非目标**：不做官方代付 Key、不做自动 LLM 导入  
- [ ] **OQ 默认建议**：可接受或列出必须改的项  

---

**文档结束。** 评审通过后建议拆分：

1. `IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md`（W1–W3 任务票）  
2. `ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md`（从 §10 展开步骤）  
3. `docs/wireframes/desktop-llm-setup-v1-wireframe.html`（F1–F5）  
4. 回写 [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) 附录：增加 H6 / T-CAP 交叉引用  
5. 回写 [ERROR-CODES.md](./ERROR-CODES.md) 用户文案  
