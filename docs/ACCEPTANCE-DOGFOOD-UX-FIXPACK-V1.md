# Travelogue · 狗粮修复包 V1 验收记录

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-DOGFOOD-UX-FIXPACK-V1.md](./PRD-DOGFOOD-UX-FIXPACK-V1.md) **v0.2** |
| **实施** | [IMPLEMENTATION-DOGFOOD-UX-FIXPACK-V1.md](./IMPLEMENTATION-DOGFOOD-UX-FIXPACK-V1.md) |
| **分支** | `fix/dogfood-ux-fixpack-v1` |
| **更新日期** | 2026-07-18 |

对照 PRD §9。签字栏：☑ 通过 · ☐ 未测 · ✗ 失败。

---

## AC-DFX-* 签字

| ID | 标准 | 验证方式 | 状态 | 证据 / 备注 |
|----|------|----------|------|-------------|
| **AC-DFX-01** | 选海报→确定→导出 `poster_bric`；`*-poster.png` + sidecar；screens 指纹不变 | pytest + 手测/Playwright | ☑ | e2e `test_ac_dfx_01_poster_export_job_contract`；单元 `test_poster_bric_pack` |
| **AC-DFX-02** | CTA / aria /「当前将导出」即时更新；全平台映射 | Node + Playwright | ☑ | `longshot-export-panel.test.mjs`；e2e `test_ac_dfx_02_confirm_poster_updates_prefs` |
| **AC-DFX-03** | 1272×675 与 `<560` Sheet 确定可点、prefs 写入 | Playwright | ☐ | 手测已过；自动化待补全 |
| **AC-DFX-04** | `gcs_poster_bric=false` 卡隐藏 + API 拒绝 | pytest | ☑ | `E_GCS_POSTER_DISABLED` handler 测 |
| **AC-DFX-05** | 改名后各展示面新名；cover/screens 不变 | Playwright + trip.json | ☐ | 写路径 `apply_intent` 同写已测；全表面 e2e 待补 |
| **AC-DFX-06** | 存量迁移仅保存落盘；幂等 | pytest | ☑ | `test_display_title_rename_migration.py` |
| **AC-DFX-07** | 「一句话」IME + ✓ + 热刷新 | Playwright / 手测 | ☐ | drawers IME + 封面副标题热刷已落地 |
| **AC-DFX-08** | 成功 Dock+toast+reveal；失败重试 | Playwright mock / 手测 | ☐ | Dock/toast/重试已落地 |
| **AC-DFX-09** | 同 job 扩展名唯一；取消无半成品 | pytest | ☑ | `test_longshot_job_format.py` |
| **AC-DFX-10** | 390：QR 可加载 **或** 无能力删位；404 降级 | Playwright | ☑ | 无资产删位：`test_ac_hp22_01` 已改；有资产路径依赖 `miniapp-qr.webp` |
| **AC-DFX-11** | `<768` 预览需更新条 ≤48px | Playwright / CSS | ☐ | compact CSS 已落地 |
| **AC-DFX-12** | 版式 tip 5s / 每 trip / 键版本化 | Playwright | ☐ | `share.js` 已落地 |
| **AC-DFX-13** | 「保存长图」真导出；示例无失败 409/400 | Playwright | ☑ | e2e `test_ac_dfx_13_*`（href/FTUE 合同）；示例先判重手测/现有测 |
| **AC-DFX-14** | 帮助可见标题无「H1 ·」 | DOM / Playwright | ☑ | `help-drawer.js`；e2e 断言 |
| ~~AC-DFX-15~~ | R5.1 Park | — | — | 不验收 |

---

## 补丁（对照评审遗漏）

| 项 | 状态 |
|----|------|
| 书架「分享图已就绪」会话徽标 | ☑ `longshot-ready.js` + shelf badge |
| `userNotes` → 封面副标题 | ☑ `assemble.py` + cover-opening + drawers 热刷 |
| `mobile_gate_qr_error` | ☑ `unsupported.js` + allowlist |
| Playwright AC-01/02/13/14 | ☑ `tests/e2e/test_dogfood_ux_fixpack_playwright.py`（4 passed） |

---

## 签字

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 实现 | | 2026-07-18 | Conditional · 主路径绿；e2e 骨架 01/02/13/14 已绿；03/05/07/08/11/12 仍待 |
| QA | | | |
| 产品 | | | |
