# Route C W0.5b 冲质量 · 真实 Spike 结论

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-08 |
| **脚本** | `scripts/title_art_route_c_w05b_spike.py --prompt-version v2 --retries 1 --samples 2` |
| **模型** | `wanx2.1-t2i-plus`（默认） |
| **原始报告** | [`cover-calligraphy-title-v1-route-c-w05b-spike-2026-08-08.md`](cover-calligraphy-title-v1-route-c-w05b-spike-2026-08-08.md) / `.json` |
| **附件图** | [`attachments/cover-calligraphy-title-v1-route-c-w05b-spike-2026-08-08/`](attachments/cover-calligraphy-title-v1-route-c-w05b-spike-2026-08-08/) |
| **前置** | [失败审计](cover-calligraphy-title-v1-route-c-w05b-audit-2026-08-08.md) · [代码落地](cover-calligraphy-title-v1-route-c-w05b-landing-2026-08-08.md) |

## 1. 汇总

| 指标 | 数值 |
|------|------|
| 总行数（标题×采样） | 56 |
| 策略跳过（生僻字 + 标点/叠字） | 26 |
| **实际尝试** | **30**（≥20） |
| 首次 OCR 通过率 | **83.3%**（25/30） |
| **≤1 次重试后通过率** | **90.0%**（27/30） |
| AC-CAL-11（≥90%，尝试子集） | **达标** |

相对 W0.5 全量单次 57.7%：提升来自 **Prompt v2 + 风险/生僻字短路 + OCR 失败重试 1 次** 的组合，不是放宽门禁。

## 2. 仍失败的 3 行（重试后）

| 标题 | 风格 | 说明 |
|------|------|------|
| 厦门老城区 | loose-running-script | 同标题 2 次采样：1 次双失败（增字/错字），1 次首次即过 → 非确定性 |
| 重走318国道 | casual-handwritten | 两次采样均双失败（数字段附近乱写） |

数字混排（尤其「国道」类）仍是弱点；失败会被 D-CAL-19 拦住并静默回退路线 B。

## 3. 门禁决策

| 项 | 结论 |
|----|------|
| **AC-CAL-11** | ✅ **在 W0.5b 协议下通过**：评测对象 =「预筛+风险规则后允许尝试的子集」+「允许 ≤1 次 OCR 重试」。与 W0.5 裸跑全量单次 57.7% 的口径不同，须在 PRD 写明 |
| **`route_c_enabled` 默认值** | 仍保持 **`false`**（OQ-CAL-06：不自动升默认主路径） |
| **显式高级项** | **允许**产品/运营在配置里打开 `route_c_enabled=true`；UI 须标明「可能静默回退默认书法贴纸（路线 B）」 |
| **Vendor bakeoff** | 本轮不启动；数字混排若成主诉再开 |

## 4. 安全提醒

API Key 曾出现在历史对话中，建议在百炼控制台轮换；测试后勿把 Key 写入仓库或 `.env` 提交。
