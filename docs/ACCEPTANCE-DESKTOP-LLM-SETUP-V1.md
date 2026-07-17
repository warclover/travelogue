# ACCEPTANCE · 桌面首启能力分层与写作引擎配置 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) **v1.1.0** |
| **实施** | [IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md](./IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md) |
| **更新日期** | 2026-07-15 |

## L0 Hardening（W1 · 2026-07-15）

对应 [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md)。

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-L0G-01 | 干净机无 Key；导入至预览 | stub 成稿；无导入失败弹窗 | ☐ |
| AC-L0G-02 | 同上；导出长图 | 成功 | ☐ |
| AC-L0G-03 | 首次引导用户 config | `llm.provider` 为 stub | ☐ |
| AC-L0G-04 | 人为 `E_LLM_AUTH` 失败 | 主 CTA「继续生成本机游记」；非唯一「重试」；**pending 仍保留** | ☐ |
| AC-L0G-05 | 点「继续生成本机游记」 | 进 FirstSuccess/预览；可长图 | ☐ |
| AC-L0G-05b | 失败 → 去配置 → 保存 → Modal「继续生成本机游记」 | 关设置并 forceStub 续跑成功 | ☐ |
| AC-L0G-05c | pending 丢失但书架有 user trip | 显示「打开最近游记预览」可进预览 | ☐ |
| AC-L0G-06 | 无 Key 点「生成杂志感」 | 局部错误；预览/长图仍在 | ☐ |
| AC-L0G-10 | 清 seen；冷启首页 | 能力卡出现；主 CTA「开始导入」 | ☐ |
| AC-L0G-11 | 关卡后仍未配置 | 首页轻状态可见；点升级进设置 | ☐ |
| AC-L0G-11b | 能力卡/banner 进设置并保存 | 出现「开始导入」resume CTA | ☐ |
| AC-L0G-12 | 首次进预览（长图 tip 已见或已过） | stub tip 或工具条「本机文案」归因可见 | ☐ |
| AC-L0G-13 | 导入 Job 进行中 | 不弹能力卡 / 轻状态 | ☐ |

```powershell
python -m pytest tests/unit/web/test_l0_guidance_hardening.py tests/unit/web/test_l0_guidance_hardening_fe.py -q
```

## Reliability Go（W1a）

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-DLLM-01 | 无 Key；导入至预览 | stub 成稿；无整页「生成失败」 | ☐ |
| AC-DLLM-02 | 预览保存长图 | PNG 落盘 / Dock 成功 | ☐ |
| AC-DLLM-04 | 打开更多工具 | 文案「当前为本机文案…」；有「配置写作引擎」 | ☐ |
| AC-DLLM-05 | 未配置调 narrate API | `E_LLM_AUTH`；预览/长图仍可用 | ☐ |
| AC-DLLM-11 | POST settings 后 GET status | `configured`；无完整 Key；`maskedKey` 可有 | ☐ |
| AC-DLLM-15 | frozen/user_data | secrets 在 `%LOCALAPPDATA%/Travelogue`（或便携/覆盖路径） | ☐ |
| AC-DLLM-20 | 日志/遥测抽样 | 无 API Key 明文 | ☐ |
| AC-DLLM-21 | GET status/config | 无完整 Key | ☐ |

## Setup Go（W1a）

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-DLLM-10 | 设置里选服务商+Key → 测试连接 | ping ok 或中文失败原因；状态徽章正确 | ☐ |
| AC-DLLM-12 | ping/就绪后点「生成杂志感文案」 | 按钮可用 | ☐ |
| AC-DLLM-13 | 错误 Key ping | 不标「已就绪」 | ☐ |
| AC-DLLM-14 | 清除配置 | 回 L0；长图仍可用 | ☐ |
| AC-DLLM-05b | 设置空态 | 含 DeepSeek/通义官方申请链接 | ☐ |
| AC-DLLM-06b | 预览点「配置写作引擎」 | 打开同一 Modal（不跳首页） | ☐ |

## First-run Go（W2）

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| AC-DLLM-03 | 能力卡 | 可关；主 CTA 仅开始导入；文内链升级；不强制 Key | ☐ |
| AC-DLLM-06 | 导入 busy | 不弹能力卡 | ☐ |
| AC-DLLM-07 | 帮助 H7 | 抽屉可见「要不要配置 AI 文案」；设置「了解更多」可深链 | ☐ |
| AC-DLLM-08 | 重播引导 | 清能力卡 seen；下次 idle 可再出卡 | ☐ |
| AC-DLLM-30 | N≥3 非技术用户无 Key | 导入→预览→长图；记录是否误以为必须配 Key | ☐ |

## 打包冒烟（W3）

见 [acceptance-records/desktop-llm-setup-v1-packaging-smoke-2026-07-15.md](./acceptance-records/desktop-llm-setup-v1-packaging-smoke-2026-07-15.md)（发布门实机勾选）。

## 写作引擎 API 配置加固（WEA · 指针）

配置面「配得对」增量（服务商隔离 · 保存并测试 · 通义地域）见独立验收，不重复抄表：

| 文档 | 说明 |
|------|------|
| [PRD-WRITING-ENGINE-API-HARDENING-V1.md](./PRD-WRITING-ENGINE-API-HARDENING-V1.md) | PRD **v1.1.0 Conditional Go** |
| [ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md](./ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md) | AC-WEA-* |
| [IMPLEMENTATION-WRITING-ENGINE-API-HARDENING-V1.md](./IMPLEMENTATION-WRITING-ENGINE-API-HARDENING-V1.md) | W0–W2 |
| [acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md](./acceptance-records/writing-engine-api-hardening-v1-review-2026-07-17.md) | 跨职能评审 |

本文件 Setup Go（AC-DLLM-10/13）在 WEA W1 落地后，解释以 **「保存并测试」+ 就绪⇔ping ok** 为准（MF-WEA-01）。

## 自动化

```powershell
python -m pytest tests/unit/web/test_user_llm_settings.py tests/unit/web/test_desktop_llm_setup_w2.py tests/unit/web/test_studio_route_snapshot.py tests/unit/web/test_help_onboarding_v1.py -q
```
