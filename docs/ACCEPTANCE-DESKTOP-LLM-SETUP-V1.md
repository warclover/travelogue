# ACCEPTANCE · 桌面首启能力分层与写作引擎配置 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-DESKTOP-LLM-SETUP-V1.md](./PRD-DESKTOP-LLM-SETUP-V1.md) **v1.1.0** |
| **实施** | [IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md](./IMPLEMENTATION-DESKTOP-LLM-SETUP-V1.md) |
| **更新日期** | 2026-07-15 |

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

## 自动化

```powershell
python -m pytest tests/unit/web/test_user_llm_settings.py tests/unit/web/test_desktop_llm_setup_w2.py tests/unit/web/test_studio_route_snapshot.py tests/unit/web/test_help_onboarding_v1.py -q
```
