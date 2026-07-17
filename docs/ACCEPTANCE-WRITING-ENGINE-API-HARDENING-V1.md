# ACCEPTANCE · 写作引擎 API 配置加固 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) **v1.1.0** |
| **实施** | [IMPLEMENTATION-WRITING-ENGINE-API-HARDENING-V1.md](./IMPLEMENTATION-WRITING-ENGINE-API-HARDENING-V1.md) |
| **评审** | [acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md](./acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md) |
| **线框** | [wireframes/writing-engine-api-hardening-v1-wireframe.html](./wireframes/writing-engine-api-hardening-v1-wireframe.html) |
| **更新日期** | 2026-07-17 |

> **就绪定义（MF-WEA-01）**：徽章「已就绪」**当且仅当** `last_ping_ok === true`（且已配置有效 provider+Key）。仅保存未 ping、或 ping 失败 → 不得显示「已就绪」。

---

## W0 · 文档门（✅ 2026-07-17）

| ID | 检查 | 结果 |
|----|------|------|
| AC-WEA-DOC-01 | PRD v1.1 + 评审 Conditional Go | ✅ |
| AC-WEA-DOC-02 | IMPLEMENTATION / ACCEPTANCE / 线框 / README 索引 | ✅ |
| AC-WEA-DOC-03 | ERROR-CODES 预留扩展码 | ✅ |

---

## W1 · 自动化

| ID | 命令 / 断言 | 结果 |
|----|-------------|------|
| AC-WEA-T01 | `pytest` coerce + ping isolation + user settings + desktop llm w2 + llm client | ✅ 27 passed |
| AC-WEA-T02 | 粘滞 DeepSeek overlay 下 resolve/ping dashscope → qwen-plus + 百炼 host | ✅ |
| AC-WEA-T03 | save dashscope 误带 deepseek model/URL → overlay 无残留 | ✅ |
| AC-WEA-T04 | region=intl → intl base_url | ✅ |
| AC-WEA-T05 | http:// 自定义 base → 400 `E_LLM_BASE_URL` | ✅ |

```powershell
python -m pytest `
  tests/unit/llm/test_provider_endpoint_coerce.py `
  tests/unit/web/test_llm_ping_provider_isolation.py `
  tests/unit/web/test_user_llm_settings.py `
  tests/unit/web/test_desktop_llm_setup_w2.py `
  tests/unit/llm/test_llm_client.py -q
```

---

## W1 · 手工 / 实机（MF-WEA-04）

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| **AC-WEA-01** | 先存 DeepSeek 合法配置 → 改通义 + 百炼中国站 Key → **保存并测试** | host/model 为通义系；成功→已就绪，或可行动失败（非 DeepSeek 模型错） | ☐ |
| **AC-WEA-02** | 通义就绪后改回 DeepSeek 合法 Key → 保存并测试 | 可就绪；不串百炼 URL | ☐ |
| **AC-WEA-03** | 非法 Key 保存并测试 | 徽章=连接失败；**≠**已就绪；Key 仍可保留便于重试 | ☐ |
| **AC-WEA-04** | 合法 Key 一点「保存并测试」 | 一次操作后就绪或明确失败 | ☐ |
| **AC-WEA-05** | 通义选国际站 + 对应 Key | 走 intl 域名（或可行动「地域不匹配」） | ☐ |
| **AC-WEA-06** | 高级填 `http://…` | 拒绝并提示仅 https | ☐ |
| **AC-WEA-07** | 清除配置 | 未配置；预览恢复「配置写作引擎」 | ☐ |
| **AC-WEA-08** | 已有 DeepSeek 时存通义 | 确认框；取消不写 | ☐ 实机（FE 契约已有） |
| **AC-WEA-09** | Modal 脚注 | 含本机 Key + 费用结算 | ✅ 代码契约 |
| **AC-WEA-10** | H7 | 含国内/国际与保存并测试 | ✅ 代码契约 |
| **AC-WEA-11** | 设置 AI zone meta | 与 Modal 徽章同词 | ✅ 代码契约 |

**狗粮记录**：用模板填写 → [writing-engine-api-hardening-v1-dogfood-TEMPLATE.md](./acceptance-records/writing-engine-api-hardening-v1-dogfood-TEMPLATE.md)

| 人 | DeepSeek | 通义中国站 | 备注 |
|----|----------|------------|------|
| | ☐ | ☐ | |

> **MF-WEA-04**：AC-WEA-01/02/04/05 须真 Key 冒烟后勾选；自动化不能代替。

---

## W2 · 增补

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-WEA-12 | 模型下拉改 qwen-turbo 后保存并测试 | overlay/secrets model 更新 | ✅ 单测 `test_save_model_qwen_turbo`；实机可选 |
| AC-WEA-13 | 切换确认取消 | secrets.provider 仍为原商 | ☐ 实机 |
| AC-WEA-14 | 401 / 超时文案抽检 | 符合 PRD §4.7 方向 | ✅ 文案表已落地；实机抽检可选 |
| AC-WEA-T06 | 仅测试 `persist=false` 不改 last_ping_ok/region | ✅ 单测 |
| AC-WEA-T07 | FE：模型下拉 / 覆盖确认 / 埋点 marker | ✅ |

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-17 | 初稿 · W0 关闭 · W1/W2 AC 表 |
| 2026-07-17 | W1 自动化 AC-WEA-T01～T05 勾选（手工 AC-WEA-01～07/09/11 仍待实机） |
| 2026-07-17 | W1 收口 + W2 编码：脚注/H7/meta 契约勾选；狗粮模板；实机 AC 仍开 |
