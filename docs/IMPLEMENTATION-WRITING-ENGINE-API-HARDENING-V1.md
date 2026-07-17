# IMPLEMENTATION · 写作引擎 API 配置加固 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) **v1.1.0** |
| **评审** | [acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md](./acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md) |
| **验收** | [ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md](./ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md) |
| **线框** | [wireframes/writing-engine-api-hardening-v1-wireframe.html](./wireframes/writing-engine-api-hardening-v1-wireframe.html) |
| **更新日期** | 2026-07-17 |
| **范围** | **W0 文档 ✅** · **W1 编码待开**（隔离热修预工作 ✅） · W2 待排 |

---

## W0 · 文档与合同（✅）

| ID | 任务 | 状态 | 锚点 |
|----|------|------|------|
| DOC-01 | PRD v1.1 Conditional Go | ✅ | `PRD-WRITING-ENGINE-API-HARDENING-V1.md` |
| DOC-02 | 跨职能评审纪要 | ✅ | `acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md` |
| DOC-03 | IMPLEMENTATION / ACCEPTANCE | ✅ | 本文 · `ACCEPTANCE-…` |
| DOC-04 | 线框 F1–F4 | ✅ | `wireframes/writing-engine-api-hardening-v1-wireframe.html` |
| DOC-05 | ERROR-CODES 预留扩展码 | ✅ | `ERROR-CODES.md` |
| DOC-06 | README / Desktop LLM ACCEPTANCE 指针 | ✅ | `docs/README.md` · `ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md` |

---

## W1 · P0 编码（待开 · 热修可计入）

### 后端

| ID | 任务 | 状态 | 锚点 / 说明 |
|----|------|------|-------------|
| BE-01 | coerce model/base_url | ✅ 预工作 | `travelogue/util/llm_presets.py` |
| BE-02 | `resolve_llm_runtime` 跨商不串 | ✅ 预工作 | `travelogue/llm/client.py` |
| BE-03 | ping 仅复用同商 secrets | ✅ 预工作 | `llm_settings_handlers.handle_llm_ping` |
| BE-04 | save 时 coerce | ✅ 预工作 | `handle_llm_settings` |
| BE-05 | 单测隔离门禁 | ✅ 预工作 | `test_provider_endpoint_coerce.py` · `test_llm_ping_provider_isolation.py` |
| BE-06 | secrets/overlay 支持 `region`（cn\|intl） | ☐ | `user_settings.py` · handlers；缺省 cn |
| BE-07 | 地域 → base_url 映射 | ☐ | 与 PRD §4.4 冻结表一致 |
| BE-08 | 保存并测试：API 串行或 `save-and-ping` | ☐ | 前端串行亦可；需原子语义验收 |
| BE-09 | 用户文案映射核心错误码 | ☐ | AUTH / ENDPOINT / NETWORK / TIMEOUT / BASE_URL |
| BE-10 | 清除后 env 注入不假绿（MF-WEA-05） | ☐ | `clear_user_llm_secrets` + inject 单测 |
| BE-11 | 自定义 base_url 仅 https | ☐ | handlers 400 + `E_LLM_BASE_URL` |

### 前端

| ID | 任务 | 状态 | 锚点 / 说明 |
|----|------|------|-------------|
| FE-01 | 切换服务商清 foreign base | ✅ 预工作 | `llm-settings.js` `clearForeignBaseUrl` |
| FE-02 | 主按钮「保存并测试」 | ☐ | 保存成功后自动 ping；成功才提示就绪 |
| FE-03 | 通义地域 radio（中国站/国际站） | ☐ | 仅 dashscope 显示 |
| FE-04 | 徽章四态同词 | ☐ | 未配置 / 已保存未验证 / 已就绪 / 连接失败 |
| FE-05 | AI zone meta 同步四态 | ☐ | `settings-panel.js` `applyAiStatus` |
| FE-06 | 脚注隐私+费用句 | ☐ | D-WEA-08 |
| FE-07 | 可行动失败文案（核心） | ☐ | 对接 BE-09 |
| FE-08 | 「仅测试连接」降为次要链（可选） | ☐ | 不挡 W1 冒烟 |

### 契约测试

| ID | 任务 | 状态 |
|----|------|------|
| TE-01 | 现有 coerce/ping 隔离单测进 CI 门 | ✅ 已有文件 |
| TE-02 | region 往返单测 | ☐ |
| TE-03 | https-only base_url 单测 | ☐ |
| TE-04 | FE 契约：保存并测试文案 / 地域控件 marker | ☐ `test_desktop_llm_setup_w2.py` 扩展 |

---

## W2 · P1

| ID | 任务 | 状态 |
|----|------|------|
| BE-12 | 模型列表校验（可选白名单） | ☐ |
| FE-09 | 模型下拉（D-WEA-06） | ☐ |
| FE-10 | 切换服务商覆盖确认（D-WEA-05） | ☐ |
| FE-11 | H7 增补国内/国际、保存并测试、错误自助 | ☐ |
| FE-12 | 成功句简化（隐藏完整 URL） | ☐ |
| BE-13 / FE-13 | QUOTA / RATE / MODEL 文案与码 | ☐ |
| TE-05 | 狗粮记录模板 3 人 | ☐ |

---

## W3 · 不阻塞发版

| ID | 任务 | 状态 |
|----|------|------|
| ARC-01 | 分槽 profile schema 短设计 | ☐ |
| ARC-02 | OS 凭据库调研纪要 | ☐ |

---

## 自动化回归（W1 门）

```powershell
python -m pytest `
  tests/unit/llm/test_provider_endpoint_coerce.py `
  tests/unit/web/test_llm_ping_provider_isolation.py `
  tests/unit/web/test_user_llm_settings.py `
  tests/unit/web/test_desktop_llm_setup_w2.py `
  tests/unit/llm/test_llm_client.py -q
```

实机：见 ACCEPTANCE 手工表 AC-WEA-01/02/04/05。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-17 | 初稿 · W0 关闭 · 热修计入 W1 预工作 |
