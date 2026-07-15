# IMPLEMENTATION · 桌面首启能力分层与写作引擎配置 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) **v1.1.0** |
| **评审** | [acceptance-records/desktop-llm-setup-v1-review-2026-07-15.md](./acceptance-records/desktop-llm-setup-v1-review-2026-07-15.md) |
| **验收** | [ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md](./ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) |
| **更新日期** | 2026-07-15 |

## 切拍

| 波次 | 范围 | 状态 |
|------|------|------|
| **W0** | PRD v1.1 回写 · 线框 F1–F3/F5 · MF 消化 | ✅ |
| **W1a** | user_data · `/llm/*` API · 注入 · 设置 Modal · 预览文案/出口 · 单测 | ✅ 核心已合入 |
| **W1b / W2** | 能力卡 T-CAP-01 · H7 · seen/重播 · D-DLLM-13 | ✅ |
| **W3** | ACL 打磨 · 打包冒烟记录 · 短 ADR | ⏳ |

## W1a 落点清单

| ID | 任务 | 路径 | 状态 |
|----|------|------|------|
| I-01 | `user_data_dir()` | `travelogue/paths.py` | ✅ |
| I-02 | secrets 读写 · overlay · inject · readiness | `travelogue/llm/user_settings.py` | ✅ |
| I-03 | `resolve_llm_runtime` secrets 回退 | `travelogue/llm/client.py` | ✅ |
| I-04 | `load_config` 合并 config.user.yaml | `travelogue/config/loader.py` | ✅ |
| I-05 | `studio_llm_status` 认 secrets provider | `travelogue/web/studio_narrate.py` | ✅ |
| I-06 | handlers status/settings/ping | `travelogue/web/studio_handlers/llm_settings_handlers.py` | ✅ |
| I-07 | 路由注册 | `studio_handlers/paths.py` · `studio_dispatch.py` | ✅ |
| I-08 | launcher 建目录 + inject | `travelogue/desktop/launcher.py` | ✅ |
| I-09 | 前端 Modal 组件 | `templates/studio/js/llm-settings.js` | ✅ |
| I-10 | 首页设置入口 | `homepage-v2/bootstrap.js` | ✅ |
| I-11 | 预览文案 + 配置出口 + 事件刷新 | `preview-toolbar-v3-sheet.js` · `init-v3.js` | ✅ |
| I-12 | 埋点白名单 | `analytics.js` · `studio_homepage_telemetry.py` | ✅ |
| I-13 | 错误文案 | `studio_errors.py` · `constants.js` · `errors.js` | ✅ |
| I-14 | 单测 | `tests/unit/web/test_user_llm_settings.py` | ✅ |
| I-15 | 路由快照 | `studio_route_snapshot.json` | ✅ |

## W2 落点清单

| ID | 任务 | 路径 | 状态 |
|----|------|------|------|
| I-20 | 首页能力卡（MF-01 CTA）· seen · busy 门禁 | `templates/studio/js/capability-card.js` · `bootstrap.js` | ✅ |
| I-21 | 帮助 **H7**（AI 文案；H6 已为封面封底）+ 重播清能力卡 | `help-onboarding.js` · `llm-settings.js` | ✅ |
| I-22 | D-DLLM-13 本会话压制首页非关键 Help L1 | `markCapabilityCardSuppressHelpL1` | ✅ |
| I-23 | 狗粮 AC-DLLM-30（N≥3） | ACCEPTANCE 勾选 | ⏳ 人工 |

> **命名说明**：PRD 初稿写 H6「写作引擎」，现网 H6 已用于封面封底 → 落地为 **H7**。

## 鉴权优先级（冻结）

`secrets 注入 env` → `config.user.yaml llm.*` → 系统/`.env` → 默认 `stub`
