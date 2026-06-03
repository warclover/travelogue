# Phase 13 · G8 创建页人工走查清单

| 属性 | 内容 |
|------|------|
| 适用 | P13.1 发布前 Studio 首页 v2 |
| 更新 | 2026-06-03 |

## 前置

- [x] `travelogue serve --studio` 已启动（loopback）— 自动化走查自建服务
- [x] `config.yaml` 中 `template_router.enabled: true` — 默认配置
- [x] 浏览器打开 `/`（studio-home-v2）— 自动化 GET `/` 校验 DOM
- [x] 治理台：`http://127.0.0.1:8766/templates-admin` — 自动化 GET 200

## 创建页 · 智能模式（AC-P13-01 / 14）

- [x] API/页面默认 smart（`phase13_g8_walkthrough_automated.py` G8-01）
- [x] `#v2-template-hint` 切换 manual 后文案变化（Playwright G8-08）
- [x] FirstSuccess `templateFeedbackMessage`（Playwright G8-09 / harness）

## 创建页 · 手动模式

- [x] 下拉仅 healthy 模板（G8-02）
- [ ] 手动选 `visual-journal` 创建成功（需真实导入）
- [x] event-recap 未放量时不出现（当前 consumer 仅 vj）

## 异常态（AC-P13-14）

- [x] LAN 权限拒绝 UI（`templates-admin?simulateLanDeny=1` + Playwright G8-10）
- [x] 回退文案存在于 `first-success.js`（G8-06 静态检查）

## 项目详情 / 预览

- [x] 书架 `templateSourceLabel`（fixture `multi-templates` + G8-11）
- [x] 预览栏模板 PATCH（G8-11b · `g8-preview` trip）

## 埋点

- [x] `template_selector_impression` / `studio-event`（G8-05/07）
- [x] `template_smart_result_shown` / `template_fallback_shown`（G8-06）

## 签字

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 产品 | | | ☐ Pass ☐ Fail |
| 前端 | | | ☐ Pass ☐ Fail |

备注：
