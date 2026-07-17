# Travelogue · 写作引擎 API 配置加固 V1 产品需求文档（PRD）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue Studio（桌面打包 / 本机 Studio） |
| **文档版本** | **v1.1.0** |
| **状态** | **Conditional Go · Must-Fix 已回写 · 可开 W1** |
| **主题代号** | 「写作引擎配得对 · 换得清 · 测得通」 |
| **触发来源** | 2026-07-17 实测：通义百炼（DashScope）配置失败、DeepSeek 正常；根因为跨服务商沿用 DeepSeek 的 `model` / `base_url`。对照行业实践做设置面周全加固。 |
| **基线 PRD** | [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) **v1.1.0**（L0/L1 · Modal · secrets · ping） |
| **相邻加固** | [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md)（无 Key 主路径 · 不重叠本主题） |
| **关联** | [adr/019-desktop-user-data-llm-secrets.md](./adr/019-desktop-user-data-llm-secrets.md) · [ERROR-CODES.md](./ERROR-CODES.md) · [PRD-HELP-ONBOARDING-V1.md](./PRD-HELP-ONBOARDING-V1.md) H7 · 首页设置手风琴（AI 文案 zone → Modal） |
| **评审记录** | [acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md](./acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md) |
| **验收** | [ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md](./ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md) · 本文 §10 · [ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md](./ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) 指针专节 |
| **实施清单** | [IMPLEMENTATION-WRITING-ENGINE-API-HARDENING-V1.md](./IMPLEMENTATION-WRITING-ENGINE-API-HARDENING-V1.md) |
| **线框** | [wireframes/writing-engine-api-hardening-v1-wireframe.html](./wireframes/writing-engine-api-hardening-v1-wireframe.html) |
| **更新日期** | 2026-07-17 |

> **定位**
>
> Desktop LLM Setup V1 已交付「能配」：Modal、Key 落盘、测试连接、预览入口。  
> 本主题解决「**配得对**」：服务商隔离、保存即验证、通义地域、可行动错误、切换不踩坑。  
> **不改** L0 stub 默认、不做官方代付、不强迫填 Key、不扩展到第三家云厂商（除非评审另批）。
>
> **与基线关系**
>
> | 主题 | 解决什么 | 本文 |
> |------|----------|------|
> | Desktop LLM Setup V1 | 有配置面 · secrets · L0/L1 铁律 | **继承**；本文修订交互与解析合同 |
> | L0 Guidance Hardening | 无 Key 不死循环 | **不重叠**；本文只碰「已进入配置面」之后 |
> | 首页设置手风琴 | AI zone → Modal（D-DLLM-03） | **容器不变**；Modal 内字段与状态机加固 |

> **产品共识（本主题四条）**
>
> 1. **一家一配置** — DeepSeek 与通义的 Key / model / endpoint 不得串用；切换服务商不得静默沿用另一家默认值。  
> 2. **就绪必须可证** — 「已就绪」只在连通性验证通过后出现；仅保存未测不得冒充可用。  
> 3. **错误可行动** — 失败文案指向下一步（换 Key、换地域、查余额、改地址），禁止笼统「连接失败」了事。  
> 4. **密钥不出本机** — 继承 D-DLLM 铁律：不进 trip、不进明文日志、不进 analytics。

---

## 0. 读者指南

| 章节 | 澄清什么 |
|------|----------|
| §1 | 实测痛点 · As-Is · 行业对照 |
| §2 | 目标 / 非目标 |
| §3 | 体验合同与冻结决策（D-WEA-*） |
| §4 | Modal / 状态机 / 文案规格 |
| §5 | 后端解析与 API 合同 |
| §6 | 安全与隐私 |
| §7 | 埋点 |
| §8 | 非功能 |
| §9 | 里程碑 W0–W3 |
| §10 | 验收 AC |
| §11 | 风险与开放问题 |
| §12 | 附录（锚点 · 错误矩阵） |

### 0.1 术语

| 术语 | 定义 |
|------|------|
| **写作引擎** | 用户可见名；`llm.provider` ∈ `{deepseek, dashscope}` + 有效 Key |
| **服务商槽（profile）** | 某一 `provider` 下的 Key / model / base_url / last_ping 集合 |
| **就绪（已就绪）** | secrets 已配置 **且** 最近一次 ping 成功（`last_ping_ok=true`） |
| **已保存未验证** | 已有 Key，但未 ping 或 ping 结果过期/未知 |
| **中国站 / 国际站** | 通义百炼地域；对应不同官方 `base_url`，Key 与 endpoint 必须同属一站 |
| **coerce** | 解析时丢弃「另一家服务商的默认 model/URL」，回落到当前 preset |

---

## 1. 背景与问题

### 1.1 实测路径（2026-07-17）

```
设置 → AI 文案 → 配置写作引擎
  → 选「通义千问（DashScope）」
  → 粘贴阿里百炼 API Key
  → 测试连接 / 保存
  → 失败或行为异常
对比：同一流程选 DeepSeek → 成功
```

**根因（已定位并部分热修）**：ping / `resolve_llm_runtime` 在切换服务商时回落到 `config` 中残留的 DeepSeek `model`（如 `deepseek-chat`）与 `base_url`（如 `api.deepseek.com`），导致通义 Key 打到错误 host 或错误模型名。

热修方向（已合入代码、待本 PRD 收口验收）：

- `coerce_model_for_provider` / `coerce_base_url_for_provider`
- ping 仅复用**同一服务商** secrets；禁止回落跨商 `base_cfg.llm.*`
- 前端切换服务商时清除另一家默认 API 地址

本 PRD 在热修之上，补齐**产品级周全合同**（保存即测、地域、错误矩阵、切换策略等）。

### 1.2 As-Is（配置面）

| 项 | 现状 | 缺口 |
|----|------|------|
| 服务商 | DeepSeek / 通义 二选一 | 单槽覆盖；切换易丢另一家 Key |
| Key | password · 显示切换 · mask | 形态提示弱 |
| 高级 base_url | 可选自定义 | 通义国内/国际发现性差 |
| 模型 | 仅 preset 默认，UI 不可选 | 无法选 qwen-turbo 等 |
| 主操作 | 测试连接 · 保存 · 清除 并列 | 「只保存不测」易假就绪 |
| 状态 | 未配置 / 已就绪 / 连接失败（+ 已保存未验证） | zone meta 与 Modal 未强制同词 |
| 错误 | 偏通用 | 缺 401/余额/地域 可行动文案 |
| 脚注 | 导入仍 stub · 预览升级 | 缺费用/隐私一句 |

### 1.3 问题清单（P-WEA-*）

| ID | 问题 | 严重度 |
|----|------|--------|
| **P-WEA-01** | 跨服务商串用 model/base_url | P0（已热修，须验收锁死） |
| **P-WEA-02** | 保存与测试分离 → 假「已配置」 | P0 |
| **P-WEA-03** | 通义地域/endpoint 不显式 | P1 |
| **P-WEA-04** | 失败文案不可行动 | P1 |
| **P-WEA-05** | 切换服务商静默覆盖另一家 Key | P1 |
| **P-WEA-06** | 模型不可见、不可选 | P2 |
| **P-WEA-07** | 三主按钮并列认知负担 | P2 |
| **P-WEA-08** | 费用/隐私说明不足 | P2 |

### 1.4 行业对照 → 本主题取舍

| 行业常见做法 | 本产品取舍（V1） |
|--------------|------------------|
| Save = validate + persist | **采纳**：保存并测试（或保存时自动 ping） |
| Per-provider profile | **分两阶段**：V1 切换确认；V1.1+ 分槽 |
| 模型下拉 + 自定义 | **采纳轻量版**：常用模型下拉；高级可自定义 |
| OAuth / 设备码 | **不做**（两家仍以 API Key 为主） |
| 应用内查余额 | **不做** |
| OS 凭据库存 Key | **V2 候选**；V1 维持 secrets.json + ACL |
| 官方代付 / BYOK 混合 | **非目标**（继承 Desktop LLM） |

---

## 2. 目标与非目标

### 2.1 目标

1. **配通义与配 DeepSeek 同等可靠**：任意一家独立配置、测试、保存后可标「已就绪」。  
2. **状态诚实**：徽章/zone meta/预览入口对「未验证」「失败」「就绪」语义一致。  
3. **切换可预期**：换服务商不静默串 endpoint；覆盖 Key 前有确认（或分槽）。  
4. **失败可自助**：常见错误有中文下一步，无需查日志。  
5. **继承 L0 铁律**：本主题任何改动不得迫使导入主链依赖 Key。

### 2.2 非目标

| 不做 | 原因 |
|------|------|
| 官方代付 LLM / 账号体系 | Desktop LLM 非目标 |
| 新增第三家默认厂商（OpenAI 等） | 范围锁；高级自定义 URL 已覆盖兼容端点 |
| 审美 MLLM / 装饰句配置面 | L2 |
| Keychain / Credential Manager | V2 |
| 帮助系统重做 | 仅增补 H7 段落 |
| 改首页手风琴 IA | AI zone → Modal 不变 |

---

## 3. 体验合同与冻结决策

### 3.1 用户可见承诺

| 场景 | 承诺 |
|------|------|
| 首次配 DeepSeek | 选服务商 → 贴 Key → **保存并测试** → 见「已就绪」或可行动失败 |
| 首次配通义 | 同上；并可选 **中国站 / 国际站**（默认中国站） |
| 从 DeepSeek 改通义 | 不得再用 DeepSeek 的 model/URL；覆盖 Key 前确认（V1）或保留分槽（V1.1） |
| 仅点保存未测（若过渡期仍分按钮） | 状态为「已保存未验证」，**不得**显示「已就绪」 |
| 清除配置 | 回 L0；徽章「未配置」；预览回到「配置写作引擎」 |

### 3.2 冻结决策（D-WEA-*）

| ID | 决策 | 说明 |
|----|------|------|
| **D-WEA-01** | **服务商隔离强制** | ping / save / resolve 必须 coerce；跨商默认 model/URL 一律丢弃 |
| **D-WEA-02** | **保存并测试为默认主路径** | 主按钮文案「保存并测试」；成功 → 已就绪；失败 → 不写 last_ping_ok=true（Key 可暂存见 D-WEA-03） |
| **D-WEA-03** | **失败时 Key 可保留为草稿** | ping 失败仍可保留已输入 Key 于 secrets（或仅内存+提示再存）；**禁止**标已就绪 |
| **D-WEA-04** | **通义暴露中国站 / 国际站** | 映射官方兼容 endpoint；自定义 URL 仍在高级 |
| **D-WEA-05** | **V1 切换策略 = 确认覆盖** | 单槽；切换服务商且已有另一家配置时 Modal 确认；V1.1 评估分槽 |
| **D-WEA-06** | **模型轻量可选** | 每家 2–4 个常用模型 +「默认」；高级可自定义模型名 |
| **D-WEA-07** | **错误矩阵进 ERROR-CODES / 用户文案表** | 见 §12.2 |
| **D-WEA-08** | **脚注补隐私与费用一句** | Key 本机；调用费用由服务商账户结算 |
| **D-WEA-09** | **Provider 集合不变** | 仍仅 `deepseek` \| `dashscope`（D-DLLM-05） |
| **D-WEA-10** | **导入主链仍 stub** | 继承 D-DLLM-02；本主题不改 narrate 默认 |

### 3.3 默认包（评审已拍板 · 2026-07-17）

| 包 | 决议 |
|----|------|
| **D-WEA-01～04、07～10** | **采纳 · W1** |
| **D-WEA-05 确认覆盖** | **采纳 · W2**（非分槽；分槽 → V1.1 候选） |
| **D-WEA-06 模型下拉** | **采纳 · W2** |
| **O-WEA-01 失败仍落盘 Key** | **采纳**（标连接失败，不标就绪） |

---

## 4. 信息架构与交互规格

### 4.1 触点（继承，不新增入口）

| 触点 | 变化 |
|------|------|
| 设置 → AI 文案 zone → CTA | meta 文案与 Modal 徽章同词（未配置 / 已保存未验证 / 已就绪 / 连接失败） |
| Modal `llm-settings.js` | 字段与主按钮按本文重排 |
| 预览「配置写作引擎」 | 无新入口；打开同一 Modal |
| 失败屏「去配置」 | 仍直接 Modal（⑤A）；不经手风琴 |
| H7 | 增补：通义国内/国际、保存并测试、常见错误 |

### 4.2 Modal 信息架构（To-Be）

```
┌─ AI 文案（可选）─────────────────────────────────┐
│ 徽章：未配置 | 已保存未验证 | 已就绪 | 连接失败     │
│ 说明：不配也能导入…（保持）                        │
│                                                  │
│ 服务商    [ DeepSeek ▼ ]                         │
│ （通义时）地域  (•) 中国站  ( ) 国际站              │
│ 模型      [ 默认（qwen-plus）▼ ]  · 高级可自定义   │
│ API Key   [ ******** ] [显示]                    │
│ 获取 Key：官方链（随服务商变）                      │
│ ▸ 高级：自定义 API 地址 / 自定义模型名               │
│                                                  │
│ 消息区：成功简句 或 可行动失败                       │
│                                                  │
│ [ 保存并测试 ]     [ 清除配置… ]                   │
│ （次要）仅测试连接 — 可选保留为文案链                │
│                                                  │
│ 脚注：Key 仅存本机；调用费用由服务商结算；            │
│       导入仍本机文案；预览可升级杂志感。              │
└──────────────────────────────────────────────────┘
```

### 4.3 主按钮与状态机

| 用户动作 | 系统行为 | 徽章 |
|----------|----------|------|
| 打开 Modal | 拉 status；按当前 provider 填表（不串商） | 现状 |
| 改服务商 | coerce 清空对方默认 URL；若已有他商 Key → 确认 | 不变直至保存 |
| **保存并测试** | 写 secrets + overlay → ping → 更新 last_ping_ok | 成功→已就绪；失败→连接失败 |
| 仅测试（若保留） | 可用表单 Key 或已存 Key ping；不强制写盘 | 同 ping 结果 |
| 清除 | 确认 → 删 secrets/overlay → stub | 未配置 |

**禁止**：仅写入 Key 未 ping 成功却显示「已就绪」。

### 4.4 通义地域（D-WEA-04）

| 选项 | base_url（冻结） |
|------|------------------|
| 中国站（默认） | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| 国际站 | `https://dashscope-intl.aliyuncs.com/compatible-mode/v1` |

- 仅当服务商 = dashscope 时显示地域。  
- 高级「自定义 API 地址」非空时：**覆盖**地域预设，并在 UI 提示「已使用自定义地址」。  
- DeepSeek 不显示地域（仅高级自定义）。

### 4.5 模型列表（D-WEA-06 · W2）

| 服务商 | 默认 | 可选（V1 建议集） |
|--------|------|-------------------|
| deepseek | `deepseek-chat` | `deepseek-chat`、`deepseek-reasoner`（若产品确认可用） |
| dashscope | `qwen-plus` | `qwen-plus`、`qwen-turbo`、`qwen-max` |

高级：自定义模型名（字符串）；空则用默认。

### 4.6 切换确认（D-WEA-05 · V1）

当 `secrets.provider` 存在且 ≠ 当前选择，用户点击「保存并测试」时：

```
将改用「通义千问」，并覆盖本机已保存的 DeepSeek 配置。
此 Key 不会上传；仅存在本机。

[ 取消 ]  [ 覆盖并继续 ]
```

V1.1 若做分槽：取消覆盖文案，改为「保存到通义配置」且 DeepSeek 槽保留。

### 4.7 成功/失败文案原则

| 类型 | 用户可见 |
|------|----------|
| 成功 | 「已连通 · 通义千问 · qwen-plus」（技术 URL 可折叠/次行） |
| Key 无效 | 「Key 无效或已失效。请回控制台重新创建并粘贴。」 |
| 地域不匹配 | 「当前地域与 Key 不匹配。请改选中国站/国际站，或检查 Key 归属。」 |
| 模型不存在 | 「模型不可用。请改选列表中的模型，或在高级中填写控制台可见的模型名。」 |
| 余额/配额 | 「服务商返回余额或配额不足。请到控制台充值或检查限流。」 |
| 网络/超时 | 「无法连接服务商。请检查网络后重试。」 |
| 429 | 「服务商繁忙，请稍后重试。」 |

---

## 5. 后端与数据合同

### 5.1 解析铁律（D-WEA-01）

| 规则 | 说明 |
|------|------|
| R1 | `provider` 决定 preset（model / base_url / api_key_env） |
| R2 | 另一家 `default_model` / `default base_url` **不得**作为当前商回落值 |
| R3 | secrets 的 model/base_url **仅当** `secrets.provider == 当前 provider` 时可用 |
| R4 | ping 请求体未带 model/base 时，用当前商 preset + 地域，**禁止** `base_cfg.llm.model` 跨商回落 |
| R5 | 保存时写入的 overlay 必须含当前商 `provider` + coerce 后的 model；base_url 仅在自定义或国际站时写入 |

### 5.2 API（沿用路径，扩展语义）

| 方法 | 路径 | 变更 |
|------|------|------|
| GET | `/__travelogue/llm/status` | 增加可选字段：`region`（dashscope）、`model`、`readiness` 枚举稳定 |
| POST | `/__travelogue/llm/settings` | 接受 `region`（可选）；保存后**可**由服务端串 ping，或前端接续调 ping（实现二选一，验收看终态） |
| POST | `/__travelogue/llm/ping` | 接受 `region`；coerce 强制；响应 `message` 用用户文案表 |
| DELETE | `/__travelogue/llm/settings` | 清除后 env 注入不得残留可用他商 Key 影响 resolve |

建议新增（可选，W2）：

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/__travelogue/llm/settings/save-and-ping` | 原子「保存并测试」，减少前端竞态 |

### 5.3 数据形（secrets / overlay）

```jsonc
// secrets.json（示意）
{
  "provider": "dashscope",
  "api_key": "…",
  "model": "qwen-plus",
  "base_url": null,          // 中国站默认可不写
  "region": "cn",            // cn | intl · dashscope only
  "last_ping_ok": true
}
```

```yaml
# config.user.yaml（示意）
llm:
  provider: dashscope
  model: qwen-plus
  api_key_env: DASHSCOPE_API_KEY
  # base_url: 仅国际站或自定义时出现
```

**分槽（V1.1 候选，不阻塞 V1）：**

```jsonc
{
  "active_provider": "dashscope",
  "profiles": {
    "deepseek": { "api_key": "…", "model": "deepseek-chat", "last_ping_ok": true },
    "dashscope": { "api_key": "…", "model": "qwen-plus", "region": "cn", "last_ping_ok": true }
  }
}
```

### 5.4 单测门禁（工程）

| 用例 | 断言 |
|------|------|
| 粘滞 DeepSeek overlay 下 ping dashscope | runtime.model=`qwen-plus`，host=百炼兼容域 |
| 保存 dashscope 时 body 误带 deepseek URL/model | overlay 无 deepseek 残留 |
| 中国站 / 国际站 | resolve 的 base_url 分别为两站官方值 |
| 清除后 | `llmAvailable=false`，resolve stub/不可用 |

---

## 6. 安全与隐私

| 要求 | 规格 |
|------|------|
| Key 存储 | 维持 ADR-019；V1 不强制 Keychain |
| 日志 | 禁止明文 Key；错误信息截断 |
| 埋点 | 仅 provider / ok / error_code / region；**无** Key、无 base_url 全串（可 hash 或只记 host 类别：preset_cn / preset_intl / custom） |
| 剪贴板 | 不自动读写；用户粘贴即可 |
| HTTPS | 自定义 base_url **仅允许 https**（W1） |

脚注标准句（D-WEA-08）：

> API Key 只保存在你的电脑。调用写作引擎时，请求发往你选择的服务商，费用由该账户结算。导入与长图默认不依赖此项配置。

---

## 7. 埋点

| 事件 | 属性（允许） | 用途 |
|------|--------------|------|
| `llm_settings_open` | source | 漏斗 |
| `llm_provider_change` | from, to | 切换行为 |
| `llm_save_and_ping` | provider, region?, ok, error_code? | 主路径 |
| `llm_ping` | provider, region?, ok, error_code? | 兼容旧事件 |
| `llm_settings_clear` | ok | 清除 |
| `llm_switch_confirm` | action: continue\|cancel | 覆盖确认 |

禁止：api_key、masked 以外的密钥片段、完整自定义 URL 含 query。

---

## 8. 非功能

| 项 | 规格 |
|----|------|
| Ping 超时 | 沿用现网 timeout；超时文案走网络类 |
| A11Y | Modal 焦点陷阱、Esc、标签关联保持；地域用 radio |
| 兼容 | 旧 secrets 无 `region` → 视作 `cn` |
| 性能 | 打开 Modal 一次 status；保存并测试串行 save→ping |

---

## 9. 里程碑

| 波次 | 范围 | Go/No-Go |
|------|------|----------|
| **W0** | 合同：本文评审；错误矩阵初稿；线框；IMPLEMENTATION/ACCEPTANCE | ✅ 2026-07-17 Conditional Go |
| **W1** | P0：隔离验收锁死 · 保存并测试 · 通义地域 · https 校验 · 可行动错误（核心码） · 脚注 | 通义/DeepSeek 实机各 1 条 Key 冒烟 · **可开编码** |
| **W2** | 模型下拉 · 切换确认 · H7 增补 · zone meta 同词 · save-and-ping 可选原子 API | 狗粮 3 人 |
| **W3** | （可选）分槽 profile · OS 凭据库调研纪要 | 不阻塞发版 |

**已完成可计入 W1 预工作**：coerce 热修 + 单测 `test_provider_endpoint_coerce` / `test_llm_ping_provider_isolation`（须纳入 §10 回归命令）。

---

## 10. 验收（AC-WEA-*）

### 10.1 功能

| ID | 验收项 | 操作 | 期望 |
|----|--------|------|------|
| **AC-WEA-01** | 跨商不串 | 先存 DeepSeek，再改通义 + 百炼 Key → 保存并测试 | 请求 host 为百炼兼容域；model 为 qwen 系；成功或可行动失败（非 DeepSeek 404/模型错） |
| **AC-WEA-02** | DeepSeek 回归 | 通义就绪后改回 DeepSeek 合法 Key | 可就绪；不串百炼 URL |
| **AC-WEA-03** | 就绪定义 | 只保存（若过渡）或 ping 失败 | 徽章 ≠ 已就绪 |
| **AC-WEA-04** | 保存并测试 | 合法 Key | 一次主按钮后就绪或明确失败 |
| **AC-WEA-05** | 通义国际站 | 选国际站 + 对应 Key | base 为 intl 域名 |
| **AC-WEA-06** | 自定义 URL | 高级填 https 自定义 | 覆盖地域；http 拒绝 |
| **AC-WEA-07** | 清除 | 清除确认 | 未配置；预览恢复配置 CTA |
| **AC-WEA-08** | 切换确认 | 已有 DeepSeek 时存通义 | 见确认框；取消不写 |

### 10.2 回归命令（建议）

```bash
python -m pytest tests/unit/llm/test_provider_endpoint_coerce.py \
  tests/unit/web/test_llm_ping_provider_isolation.py \
  tests/unit/web/test_user_llm_settings.py \
  tests/unit/web/test_desktop_llm_setup_w2.py -q
```

实机：DeepSeek + 通义中国站各一条「保存并测试」手工记录（附截图）。

### 10.3 文案抽检

| ID | 检查 |
|----|------|
| **AC-WEA-09** | Modal 脚注含本机 Key + 费用结算句 |
| **AC-WEA-10** | H7 含通义国内/国际与「保存并测试」 |
| **AC-WEA-11** | 设置 AI zone meta 与 Modal 徽章同词 |

---

## 11. 风险与开放问题

| ID | 问题 | 默认建议 |
|----|------|----------|
| **O-WEA-01** | ping 失败是否仍落盘 Key？ | **落盘 + 连接失败**（方便改地域重试）；不标就绪 |
| **O-WEA-02** | V1 分槽还是确认覆盖？ | **确认覆盖**；分槽进 V1.1 |
| **O-WEA-03** | `deepseek-reasoner` 是否进列表？ | W2 前用真 Key 探活再定 |
| **O-WEA-04** | 是否提供原子 save-and-ping API？ | 前端串行即可；竞态多再加 API |
| **O-WEA-05** | 国际站是否默认展示？ | 展示二选一，默认中国站 |

---

## 12. 附录

### 12.1 实现锚点（As-Is）

| 区域 | 路径 |
|------|------|
| Modal UI | `templates/studio/js/llm-settings.js` |
| 设置 AI zone | `templates/studio/studio-home-v2.html` · `homepage-v2/settings-panel.js` |
| Ping/Save | `travelogue/web/studio_handlers/llm_settings_handlers.py` |
| Runtime | `travelogue/llm/client.py` · `travelogue/util/llm_presets.py` |
| Secrets | `travelogue/llm/user_settings.py` · ADR-019 |
| 单测 | `tests/unit/llm/test_provider_endpoint_coerce.py` · `tests/unit/web/test_llm_ping_provider_isolation.py` |

### 12.2 错误矩阵（初稿 · 映射实现时补 code）

| 用户场景 | 建议 error 语义 | 用户文案方向 |
|----------|-----------------|--------------|
| 401 / invalid key | `E_LLM_AUTH` | Key 无效或失效 |
| 模型不存在 | `E_LLM_MODEL`（若无则扩展） | 换模型 |
| 地域/endpoint 错 | `E_LLM_ENDPOINT` | 换中国站/国际站 |
| 余额/配额 | `E_LLM_QUOTA` | 控制台充值 |
| 429 | `E_LLM_RATE` | 稍后重试 |
| 超时/网络 | `E_LLM_TIMEOUT` / `E_LLM_NETWORK` | 查网络 |
| 非 https 自定义 | `E_LLM_BASE_URL` | 仅支持 https |

具体码表落地时回写 [ERROR-CODES.md](./ERROR-CODES.md)。

### 12.3 与 Desktop LLM Setup 决策对照

| 基线 | 本文 |
|------|------|
| D-DLLM-02 导入仍 stub | **保持** D-WEA-10 |
| D-DLLM-03 Modal | **保持**；内字段加固 |
| D-DLLM-04 secrets 落盘 | **保持**；可增 region |
| D-DLLM-05 仅两家 + 自定义 URL | **保持**；通义地域为 preset 选择，非第三家 |
| 测试 / 保存分按钮 | **修订为** 保存并测试（D-WEA-02） |

### 12.4 评审清单（2026-07-17 已勾选）

- [x] 采纳默认包 D-WEA-01～04、07～10  
- [x] D-WEA-05：确认覆盖（分槽不进本波）  
- [x] D-WEA-06：W2 做模型下拉  
- [x] O-WEA-01：失败仍落盘 Key  
- [x] 独立线框 HTML  
- [x] ACCEPTANCE-WEA 独立文档 + Desktop LLM ACCEPTANCE 指针专节  

**Must-Fix（挡 W1 完工，不挡开工）**：见评审纪要 MF-WEA-01～05（就绪定义 · 地域冻结表 · ERROR-CODES · 双 Key 冒烟 · 清除后 env）。

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1.0 | 2026-07-17 | Conditional Go；§3.3/§9/§12.4 回写拍板；链 IMPLEMENTATION/ACCEPTANCE/线框/评审 |
| v1.0.0 | 2026-07-17 | 初稿：基于通义串配置实测 + 行业实践对照；含 D-WEA-* 与 W0–W3 |
