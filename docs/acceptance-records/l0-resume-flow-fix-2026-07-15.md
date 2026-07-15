# L0 Resume 断点修复 · 手工矩阵记录（T1–T7）

| 属性 | 内容 |
|------|------|
| **日期** | 2026-07-15 |
| **分支** | 当前工作区（L0 Resume Flow Fix） |
| **关联** | [IMPLEMENTATION-DESKTOP-L0-GUIDANCE-HARDENING-V1](../IMPLEMENTATION-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) W3 · [ACCEPTANCE-DESKTOP-LLM-SETUP-V1](../ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) AC-L0G-05* |
| **自动化** | `pytest tests/unit/web/test_l0_guidance_hardening*.py` PASS |
| **手工/模拟** | Playwright 对本机源码 Studio `http://127.0.0.1:8767`（注意：桌面便携包占用 8766 仍为旧包，不含本次修复） |

## 自动化

| 套件 | 结果 |
|------|------|
| `test_l0_guidance_hardening.py` + `test_l0_guidance_hardening_fe.py` | PASS |

## 模拟用户矩阵（Playwright · 2026-07-15）

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| **T1** | 无 Key demo 导入 | stub 成稿；预览 200 | **PASS** `demo-album` preview=200 |
| **T2** | 注入 `E_LLM_AUTH` 失败屏 | 主 CTA「继续生成本机游记」；pending 保留 | **PASS** |
| **T3** | 失败 → 去配置 → 保存 | Modal resume「继续生成本机游记」+ 预览说明 | **PASS** |
| **T4** | 关设置后继续本机可用 | pending 仍在；主按钮可见 | **PASS**（未对假路径真跑导入） |
| **T5** | 无 Key 调 narrate | `E_LLM_AUTH`；预览仍 200 | **PASS** |
| **T6** | 上传路径 continue stub | toast 重选照片 + `forceStubNextUpload` | **PASS** |
| **T7** | card/banner 保存后「开始导入」 | 打开导入向导 | **PASS**（顺带修 `HELP_KEYS`→`HELP_LS` 能力卡崩溃） |

## 额外发现并已修

- `help-onboarding.js` 中能力卡/轻状态仍引用已重命名的 `HELP_KEYS`，导致 `showCapabilityCard` 运行时 `ReferenceError`；已改为 `HELP_LS`。

## 工程修复摘要

1. `pollImport` 失败不再提前 `removeItem(activePending)`
2. LLM 设置保存后按 `source` 显示 resume（继续本机 / 开始导入）
3. 失败屏兜底「打开最近游记预览」
4. 不提供「用 API 重跑导入」（D-DLLM-02 保持）
5. `HELP_KEYS` → `HELP_LS` 能力卡引用修复
