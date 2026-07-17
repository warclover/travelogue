# IMPLEMENTATION · 写作引擎 API 配置加固 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) **v1.1.0** |
| **评审** | [acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md](./acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md) |
| **验收** | [ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md](./ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md) |
| **线框** | [wireframes/writing-engine-api-hardening-v1-wireframe.html](./wireframes/writing-engine-api-hardening-v1-wireframe.html) |
| **更新日期** | 2026-07-17 |
| **范围** | **W0 文档 ✅** · **W1 编码 ✅**（隔离热修 + 保存并测试 · 地域 · https · 文案） · W2 待排 |

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

## W1 · P0 编码（✅ 2026-07-17）

### 后端

| ID | 任务 | 状态 | 锚点 / 说明 |
|----|------|------|-------------|
| BE-01 | coerce model/base_url | ✅ | `travelogue/util/llm_presets.py` |
| BE-02 | `resolve_llm_runtime` 跨商不串 | ✅ | `travelogue/llm/client.py` |
| BE-03 | ping 仅复用同商 secrets | ✅ | `llm_settings_handlers.handle_llm_ping` |
| BE-04 | save 时 coerce | ✅ | `handle_llm_settings` |
| BE-05 | 单测隔离门禁 | ✅ | `test_provider_endpoint_coerce.py` · `test_llm_ping_provider_isolation.py` |
| BE-06 | secrets/overlay 支持 `region`（cn\|intl） | ✅ | `user_settings.py` · handlers；缺省 cn |
| BE-07 | 地域 → base_url 映射 | ✅ | `DASHSCOPE_REGION_BASE_URLS` / `preset_base_url` |
| BE-08 | 保存并测试：API 串行或 `save-and-ping` | ✅ | FE 串行 save→ping |
| BE-09 | 用户文案映射核心错误码 | ✅ | handlers `_SETTINGS_MESSAGES` + `studio_errors` |
| BE-10 | 清除后 env 注入不假绿（MF-WEA-05） | ✅ | `clear_injected_llm_environ` |
| BE-11 | 自定义 base_url 仅 https | ✅ | `validate_custom_base_url` → 400 |

### 前端

| ID | 任务 | 状态 | 锚点 / 说明 |
|----|------|------|-------------|
| FE-01 | 切换服务商清 foreign base | ✅ | `llm-settings.js` `clearForeignBaseUrl` |
| FE-02 | 主按钮「保存并测试」 | ✅ | `#studio-llm-save-ping` |
| FE-03 | 通义地域 radio（中国站/国际站） | ✅ | `#studio-llm-region-wrap` |
| FE-04 | 徽章四态同词 | ✅ | 含 `is-warn` |
| FE-05 | AI zone meta 同步四态 | ✅ | `settings-panel.js` `applyAiStatus` |
| FE-06 | 脚注隐私+费用句 | ✅ | D-WEA-08 标准句 |
| FE-07 | 可行动失败文案（核心） | ✅ | `SETTINGS_ERR` |
| FE-08 | 「仅测试连接」降为次要链（可选） | ✅ | 文案链 |

### 契约测试

| ID | 任务 | 状态 |
|----|------|------|
| TE-01 | 现有 coerce/ping 隔离单测进 CI 门 | ✅ |
| TE-02 | region 往返单测 | ✅ |
| TE-03 | https-only base_url 单测 | ✅ |
| TE-04 | FE 契约：保存并测试文案 / 地域控件 marker | ✅ `test_wea_w1_save_and_ping_region_footnote_markers` |

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
| 2026-07-17 | W1 编码合入：region · 保存并测试 · https · 文案 · 单测门 27 passed |
