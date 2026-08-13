# IMPLEMENTATION · 百炼一体连接 V1（BAI）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-BAILIAN-AI-INTEGRATION-V1.md](./PRD-BAILIAN-AI-INTEGRATION-V1.md) **v0.2.2** |
| **评审** | [acceptance-records/bai-bailian-ai-integration-v1-review-2026-08-13.md](./acceptance-records/bai-bailian-ai-integration-v1-review-2026-08-13.md) |
| **验收** | Kickoff 后拆 [ACCEPTANCE-BAILIAN-AI-INTEGRATION-V1.md](./ACCEPTANCE-BAILIAN-AI-INTEGRATION-V1.md)；本波以 PRD §10 AC-BAI-* 为准 |
| **更新日期** | 2026-08-13 |
| **本刀范围** | **W1b · copy 路由 + OCR + imageReady** |

> **本刀明确不做（留给 W2 / W3）**
>
> - 不切 t2i 默认（仍 `wanx2.1-t2i-plus`）；2.7 / qwen-image 不塞进现网 URL
> - 不做流式 client；思考只走非流式 `enable_thinking`
> - 不把 `qwen3.5-ocr` 设成封面 OCR 默认
> - 不改审美 `qwen-vl-max`
> - 不做帮助 H7、不做线框、不做国际站
> - 不重写 AIR Prompt、封面版式、CAL 路线 B
> - **不**把 `secrets.json` 改写成嵌套 `{dashscope:{…}}`

---

## W1a · 连接面 + 就绪语义（本 PR）

目标：配一次百炼，文案和封面生图都吃这把 Key；DeepSeek-only 用户在 Studio 显示未连接。

### 合同钉（相对 PRD §8 W1 的切片）

| 项 | W1a 做法 |
|----|----------|
| secrets | 保持扁平 `{provider, api_key, model, region, last_ping_ok}`。Studio 活跃 = `provider=dashscope`。旧官方 DeepSeek Key **留盘不删**，不驱动 Studio ping / narrate |
| 用户模型字段 | 磁盘可留 `qwen-plus` 等；**运行时忽略**，走服务端默认（D-BAI-02）。ping 级联成功也不把「已改用」写进 UI |
| 思考 / 型号 | **本刀不做**。ping：短超时文本、关思考（现网 client 本就无 thinking 字段，保持） |
| 分灯 | status 增 `connectionOk`；W1a 与 `copyReady` 等同。禁止单一 `llmAvailable` 点亮封面字体 |
| NAS | 连接 API 已从 `ai_surface` 解耦，**不回退**。narrate 仍受 NAS 门控 |

### 后端

| ID | 任务 | 状态 | 锚点 / 说明 |
|----|------|------|-------------|
| BE-W1a-01 | Studio 就绪只认百炼 Key + `last_ping_ok===true` | ✅ | `ready.studio_llm_status`；DeepSeek-only → 未连接（AC-BAI-04） |
| BE-W1a-02 | POST `/llm/settings` 只接受 `dashscope` | ✅ | `provider=deepseek` → 400（AC-BAI-15） |
| BE-W1a-03 | `inject` 只写 `DASHSCOPE_API_KEY`（有百炼槽时） | ✅ | 不把 secrets 里的官方 DeepSeek 注入 Studio 进程；`.env` 原有 `DEEPSEEK_API_KEY` 不删 |
| BE-W1a-04 | ping 成功文案只说「已连接通义百炼」 | ✅ | 去掉「已自动改用可用模型」；用户面不出现模型 id |
| BE-W1a-05 | 错误文案去「改选模型 / 国际站 / 自定义地址 / DeepSeek」 | ✅ | 额度 COPY-BAI-09；旧 DeepSeek 用户 COPY-BAI-10 |
| BE-W1a-06 | status 增 `connectionOk` / `copyReady` / `hasDashscope` | ✅ | **不下发** `hasDeepseek`；`configured` 对 Studio = 百炼槽 |
| BE-W1a-07 | 保存强制 `region=cn`；忽略客户端模型 / 自定义 URL | ✅ | AC-BAI-17；磁盘旧 intl/custom 不展示、本刀不清 |

### 前端

| ID | 任务 | 状态 | 锚点 / 说明 |
|----|------|------|-------------|
| FE-W1a-01 | 设置 Modal 只留说明 + Key +「保存并测试」 | ✅ | 物理删除 DeepSeek `<select>`、模型下拉、国际站、自定义 URL、DeepSeek 申请链、高级折叠、思考开关 |
| FE-W1a-02 | 标题统一「模型API 配置」 | ✅ | Modal / 首页 zone / Sheet 连接区（COPY-BAI-01） |
| FE-W1a-03 | 首页设置 zone 不用「写作增强」当主名 | ✅ | COPY-BAI-12 |
| FE-W1a-04 | Sheet 连接未连接置顶、已连接折叠 | ✅ | 继承 SAS；文案卡 / 封面字体卡分 CTA |
| FE-W1a-05 | 封面字体未连接走 COPY-BAI-07 | ✅ | 禁止再用单一 `llmAvailable` 点亮封面字体（AC-BAI-09） |

### 契约测试

| ID | 任务 | 状态 |
|----|------|------|
| TE-W1a-01 | AC-BAI-01 DOM：无 DeepSeek option / 模型下拉 / 国际站 / 自定义 URL / 思考开关 | ✅ |
| TE-W1a-02 | AC-BAI-04 DeepSeek-only：Studio `configured`/`connectionOk`/narrate 未连接；磁盘 Key 仍在 | ✅ |
| TE-W1a-03 | AC-BAI-15 POST `provider=deepseek` → 400 | ✅ |
| TE-W1a-04 | ALG-V3 `probe_llm_ready` 仍可用 DeepSeek env/secrets（不误伤 CLI） | ✅ |
| TE-W1a-05 | coerce 单测保留；Studio POST 不再接受 deepseek | ✅ |

### 自动化回归（本刀，非全量 quality_gate）

```powershell
python -m pytest `
  tests/unit/web/test_llm_ping_provider_isolation.py `
  tests/unit/web/test_desktop_llm_setup_w2.py `
  tests/unit/web/test_alg3_llm_ready.py `
  tests/unit/web/test_sas_ai_sheet_wiring.py `
  tests/unit/llm/test_provider_endpoint_coerce.py `
  tests/unit/web/test_user_llm_settings.py `
  tests/unit/web/test_cqa_llm_ping_isolation.py `
  tests/unit/web/test_ai_surface_gate.py -q
```

---

## W1b · copy 路由 + OCR + imageReady

依据：[W0 实机](./acceptance-records/bai-w0-live-probe-2026-08-13.md)

| ID | 任务 | 状态 |
|----|------|------|
| BE-W1b-01 | copy 默认 `deepseek-v4-pro`；级联 Pro → Flash-V4 → Qwen3.7/3.8 → 旧名 | ✅ |
| BE-W1b-02 | V4 文案非流式 `enable_thinking`；JSON 失败当次关思考重试 | ✅ |
| BE-W1b-03 | ping 走 Flash 级联、强制关思考 | ✅ |
| BE-W1b-04 | OCR 默认 `qwen3.7-flash`，链尾 `qwen-vl-plus` | ✅ |
| BE-W1b-05 | `imageReady`：乐观=connectionOk；t2i 401/403/额度后诚实灭灯 | ✅ |
| FE-W1b-01 | Sheet 图像诚实态 COPY-BAI-08 | ✅ |
| FE-W1b-02 | 去掉 `llm_provider_change` / `llm_switch_confirm` 产品路径 | ✅ |
| TE-W1b-01 | coerce 保留 `deepseek-v4-*`；丢掉官方 `deepseek-chat` | ✅ |
| TE-W1b-02 | ping payload 无 thinking 且模型为 Flash | ✅ |
| TE-W1b-03 | imageReady 与 copyReady 可分灯 | ✅ |

```powershell
python -m pytest `
  tests/unit/llm/test_provider_endpoint_coerce.py `
  tests/unit/llm/test_llm_client_retry.py `
  tests/unit/web/test_alg3_llm_ready.py `
  tests/unit/web/test_llm_ping_provider_isolation.py `
  tests/unit/web/test_sas_ai_sheet_wiring.py `
  tests/unit/web/test_desktop_llm_setup_w2.py `
  tests/unit/web/test_user_llm_settings.py -q
```

---

## 后续波次（本文件占位，不在本 PR 编码）

| 波次 | 范围 |
|------|------|
| **W0** | ✅ 2026-08-13 实机：[bai-w0-live-probe-2026-08-13.md](./acceptance-records/bai-w0-live-probe-2026-08-13.md)（AC-BAI-16） |
| **W1b** | ✅ 本刀：copy Pro + 非流式思考；OCR `qwen3.7-flash`；`imageReady` 诚实态；t2i **不切** |
| **W1b 狗粮** | ✅ 2026-08-13 本机走通：[bai-w1b-studio-dogfood-2026-08-13.md](./acceptance-records/bai-w1b-studio-dogfood-2026-08-13.md)（AC-BAI-02/03/06 · SHD-BAI-04） |
| **W2** | 仅对同构的 `wan2.2-t2i-plus` 做字形盲评；2.7 / qwen-image 另立项协议；审美换代 |
| **W3** | 帮助 H7「模型API 配置」+ 真人狗粮 |

### W0 冻结给 W1b 的默认（摘录）

| 槽 | 默认 | 依据 |
|----|------|------|
| copy | `deepseek-v4-pro`（思考开；ping 关） | OQ-BAI-02 / D-BAI-14 绿 |
| vision · OCR | `qwen3.7-flash`（勿用 `qwen3.5-ocr` 当封面默认） | OQ-BAI-04：飞白贴纸 3.5-ocr 两次 false |
| t2i | 仍 `wanx2.1-t2i-plus` | `wan2.2` 同构但未盲评；2.7 / qwen-image 400 不同构 |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-08-13 | W1a 任务卡：连接面 + 就绪语义；明确本刀不做思考/换型号 |
| 2026-08-13 | W1b：copy Pro + 思考；OCR 3.7-flash；imageReady 分灯 |
