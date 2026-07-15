# 打包冒烟记录 · Desktop LLM Setup V1

| 属性 | 内容 |
|------|------|
| **对应** | [PRD-DESKTOP-LLM-SETUP-V1.md](../PRD-DESKTOP-LLM-SETUP-V1.md) §10.4 · [ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md](../ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) |
| **ADR** | [018-desktop-user-data-llm-secrets.md](../adr/018-desktop-user-data-llm-secrets.md) |
| **模板日期** | 2026-07-15 |
| **状态** | ⏳ 待填（人工 / 发布门） |

> 发布 Desktop 构建前最少勾选下列项。狗粮 AC-DLLM-30（N≥3）另表，不替代本清单。

---

## 构建信息（填写）

| 项 | 值 |
|----|-----|
| 构建号 / 提交 | |
| 产物路径 | |
| OS | Windows 10/11 |
| 执行人 | |
| 日期 | |

---

## 冒烟清单（PRD §10.4）

| # | 步骤 | 期望 | 结果 |
|---|------|------|------|
| S1 | **无 Key**：导入 demo/小相册 → 预览 | stub 成稿；无整页「生成失败」 | ☐ |
| S2 | **无 Key**：预览 → 保存长图 | PNG 落盘 / Dock 成功 | ☐ |
| S3 | **无 Key**：更多工具 · 杂志感入口 | 文案「当前为本机文案…」；可点「配置写作引擎」 | ☐ |
| S4 | 设置 Modal：空态含 DeepSeek/通义申请链接；只读路径可见 `userDataDir` 与 `tripsDir` | ☐ |
| S5 | **有 Key（狗粮）**：选服务商 → 粘贴 Key → 测试连接 | ping ok 或中文失败原因；徽章正确 | ☐ |
| S6 | 保存后点「生成杂志感文案」 | 一轮升级成功；**不会**自动在导入时重写 | ☐ |
| S7 | **清除配置** | 回 L0；长图仍可用 | ☐ |
| S8 | 首启能力卡（清 seen 或新 profile） | 可关；主 CTA「开始导入」；文内链升级可选 | ☐ |

---

## 安全抽查

| # | 检查 | 结果 |
|---|------|------|
| K1 | `%LOCALAPPDATA%/TravelogueStudio/secrets.json`（或覆盖路径）存在且非空 Key 时，日志/遥测抽样无明文 Key | ☐ |
| K2 | `GET /__travelogue/llm/status` 无完整 Key，仅 `maskedKey` | ☐ |

---

## 结论

| 项 | 填写 |
|----|------|
| Go / No-Go | |
| 阻塞项 | |
| 备注 | |

---

## 修订

| 日期 | 说明 |
|------|------|
| 2026-07-15 | W3 建模板；实机勾选待发布门填写 |
