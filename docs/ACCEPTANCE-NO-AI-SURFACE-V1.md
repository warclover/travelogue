# ACCEPTANCE · 当前版无 AI 面与主线打磨 V1（NAS）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-NO-AI-SURFACE-V1.md](./PRD-NO-AI-SURFACE-V1.md) **v0.2.1** |
| **实施** | [IMPLEMENTATION-NO-AI-SURFACE-V1.md](./IMPLEMENTATION-NO-AI-SURFACE-V1.md) **v0.2.1** |
| **评审** | [acceptance-records/no-ai-surface-v1-review-2026-07-22.md](./acceptance-records/no-ai-surface-v1-review-2026-07-22.md) · Conditional Go · MF 已回写 |
| **收口记录** | [acceptance-records/no-ai-surface-v1-e2e-doc-closeout-2026-07-22.md](./acceptance-records/no-ai-surface-v1-e2e-doc-closeout-2026-07-22.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-07-22 |

> **用法**：默认面用例在 `aiSurfaceEnabled=false`（干净安装）下执行；带 **〔dark〕** 的用例须 `TRAVELOGUE_AI_SURFACE=1`（或 config 等价）且与默认面禁词审计 **分 job**。  
> **V1 Done** = 无 AI 面 + 主链狗粮；不含排版/长图深度打磨。  
> **本期 KPI 指针（PRD §2.3）**：OUT-01 出图完成 · OUT-02 零 AI 岔路 · OUT-03 失败归因干净 · OUT-04 分享话术干净 · OUT-05 底座未腐（暗合 AC-NAS-07 / 08 / 失败面 / 分享路径 / AC-NAS-09）。  
> **下期解冻**：见 PRD **§14**；本表不验收 AI-Return。  
> **勾选图例**：✅ 自动化/静态已锁 · ☑ 工程已对齐待手测/狗粮 · ☐ 未做。

---

## 0. 编码启动门（W0）

| ID | 检查项 | 结果 |
|----|--------|------|
| AC-NAS-W0-01 | PRD ≥ **v0.2.1** 且 MF-NAS-01～10 已落 §5/§10；§5.5 / §14 可读 | ✅ |
| AC-NAS-W0-02 | 本 ACCEPTANCE 勾选表可用 | ✅ |
| AC-NAS-W0-03 | 附录 C 扫描语义（默认可达面 / nas-allow / 分波）已签字 | ✅ |

---

## 1. W1 · 门控 + 首页侧 + BE 硬拒绝

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| **AC-NAS-01** | 清 localStorage；冷启 Studio | **无**能力卡 | ✅ e2e |
| **AC-NAS-02** | 打开设置 | 无「AI 文案」「写作引擎」zone/CTA；总述=COPY-NAS-SET-DESC | ✅ e2e |
| **AC-NAS-03** | 打开帮助 | 无 H7；H0 无「AI 文案」句 | ✅ e2e |
| **AC-NAS-04** | 完成一次导入至 FirstSuccess | 下一句 **精确等于**「画册已做好，可预览与导出长图。」 | ✅ e2e + 静态 |
| **AC-NAS-08a** | 跑默认可达面禁词审计（**W1 分区**：首页/设置/帮助/成功/失败） | 命中 = 0（nas-allow 除外） | ✅ `studio_no_ai_surface_audit --wave w1` |
| **AC-NAS-13** | 门控 off；磁盘可有 Key；`POST /__travelogue/narrate` | HTTP **403**；`error=E_AI_SURFACE_DISABLED`；message 中性无禁词 | ✅ unit + e2e |
| **AC-NAS-15** | 带 `?llmSetup=1`（及既有 deeplink）打开；并从失败/banner 等路径调 `openLlmSettings` | **不弹**写作引擎 Modal | ✅ e2e |
| **AC-NAS-16** | 帮助「重播引导」后 idle | 仍无能力卡、无 stub tip、无 home stub banner | ✅ e2e |
| **AC-NAS-17a** | ~~门控 off：settings/ping → 403~~ **已由 SAS D-SAS-07 废止（2026-08）** | **现行**：关闸仍可 `POST/DELETE settings` 与 `POST ping`（预配 Key）；烧模型仍 403。验收见 `test_ai_surface_gate.py`「allowed_when_surface_off」 | ✅ unit（SAS） |
| **AC-NAS-17c** | ~~门控 off：`GET /llm/status` → 403~~ **已由 SAS D-SAS-07 废止（2026-08）** | **现行**：关闸可读 status（含 readiness / maskedKey）；`GET /config` 仍剥离 llm*（AC-NAS-17d 不变） | ✅ unit（SAS） |
| **AC-NAS-17d** | 门控 off：`GET /__travelogue/config` | **200**；含 `aiSurfaceEnabled:false`；**无** `llmAvailable`/`llmProvider`/`tripsDir`（D-NAS-17b · [QFX](./PRD-QUALITY-FIXPACK-V1.md) AC-QFX-27 · IMPLEMENTATION BE-NAS-04） | ✅ unit（QFX PR-A） |
| **AC-NAS-M7** | （可选）导入失败面 | 无「去配置写作引擎」；焦点不落配置钮 | ✅ 静态/L0G FE |
| **AC-NAS-M8** | （可选）失败续跑 CTA 若仍显示 | 文案为「继续生成游记」或整组隐藏 | ✅ 静态/L0G FE |

```powershell
python -m pytest tests/unit/web/test_ai_surface_gate.py tests/unit/web/test_studio_no_ai_surface_audit.py -q
python scripts/studio_no_ai_surface_audit.py --wave w1
python -m pytest tests/e2e/test_studio_no_ai_surface_playwright.py -q
```

---

## 2. W2 · 预览切断 + 主链狗粮 + 全量禁词

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| **AC-NAS-05** | 预览 → 精修 →「这本 / 整本信息」 | 无「重新生成文案」、无 llm-setup / llm-expect | ✅ e2e |
| **AC-NAS-06** | 观察 Task Dock | 无「AI 文案已就绪」、无「重新生成文案」钮 | ✅ e2e |
| **AC-NAS-14** | 精修抽屉；保存编辑；乱点 Dock | 无「按新感觉重写这段」；toast 无「重新生成文案」；network **0×** `POST /narrate` | ✅ e2e network |
| **AC-NAS-07** | 导入 → 预览 → **纯照片长图** | 导出成功；主链无 AI 引导 | ☑ 沿用既有长图 e2e；整链狗粮手测 |
| **AC-NAS-11** | 导入 Importing 态 | Wait Tips 可出现；**无**能力卡抢帧 | ☑ 能力卡硬关 + Wait Tips 既有 e2e |
| **AC-NAS-08b** | 默认可达面禁词审计（**全量** `templates/studio`） | 命中 = 0 | ✅ `--wave w2`（关键路径扩面；注释剥离） |
| **AC-NAS-FLIP** | 翻转清单单测（见 §5）默认面 job | 全绿；dark 断言不在此 job | ✅ 见 §5 |

```powershell
python scripts/studio_no_ai_surface_audit.py --wave w2
python -m pytest tests/unit/web/test_ai_surface_gate.py tests/e2e/test_studio_no_ai_surface_playwright.py -q
```

---

## 3. W3 · Dark 回归 + 有 Key 仍藏

| ID | 步骤 | 期望 | 结果 |
|----|------|------|------|
| **AC-NAS-09** 〔dark〕 | `TRAVELOGUE_AI_SURFACE=1`；打开设置 → 保存并测试 → 预览 Sheet/抽屉 narrate | 可配可 ping；可触发 narrate；**能力卡仍不出现** | ☑ dark 月度冒烟（手测） |
| **AC-NAS-10** | 关 switch 冷启；磁盘保留 secrets | UI 无入口；`POST /narrate` 仍 403 | ✅ unit（403）+ 默认面 e2e |
| **AC-NAS-12** | 默认面完整会话 | spy：无强制 `openLlmSettings`；analytics/日志抽样无 Key 明文 | ☑ e2e 覆盖 deeplink；会话抽样手测 |
| **AC-NAS-17b** 〔dark〕 | dark job 单独跑；**不**跑默认面 AC-08 | AC-NAS-09 绿 | ☑ |
| **AC-NAS-DOC** | ERROR-CODES 含 `E_AI_SURFACE_DISABLED`；DLLM/WEA/SFI/Help/CSC 用户面 superseded 注记 | 文档指针齐全 | ✅ DOC-NAS-02 |

---

## 4. 前端冒烟（≤10 步 · 狗粮）

| # | 步骤 | 期望 | 结果 |
|---|------|------|------|
| S1 | 干净首访 | 无能力卡 / stub banner | ✅ |
| S2 | 设置 | 无 AI zone；中性总述 | ✅ |
| S3 | 帮助 → 重播 | 无 H7；重播后仍无卡/tip/banner | ✅ |
| S4 | `?llmSetup=1` | 不弹 Modal | ✅ |
| S5 | 导入 → FirstSuccess | = COPY-NAS-FS-01 | ✅ |
| S6 | 预览精修这本 + 抽屉 | 无 llm 行；无「按新感觉重写」 | ✅ |
| S7 | Dock + network | 无 AI 就绪；**0× /narrate** | ✅ |
| S8 | 纯照片长图 | 成功 | ☑ |
| S9 | 默认可达禁词审计 | 0 命中 | ✅ |
| S10 〔dark〕 | ON 可配可 narrate；能力卡仍无；OFF 有 Key 仍藏 | 通过 | ☑ |

---

## 5. 单测翻转清单（MF-NAS-06）

默认面改为「禁止出现」或拆至 dark 附录的既有测试（实现时逐项勾选）：

| 文件 | 处置 | 结果 |
|------|------|------|
| `tests/unit/web/test_desktop_llm_setup_w2.py` | 拆 `*_nas_default` / `*_ai_surface_dark` | ✅ 内容已对齐（命名未强制拆文件） |
| `tests/unit/web/test_l0_guidance_hardening_fe.py` | 默认面废止配置 CTA / 能力卡升级串；dark 附录可留 | ✅ |
| `tests/unit/web/test_preview_toolbar_v3.py` | 默认面无杂志感/按新感觉重写；dark 附录 | ✅ |
| `tests/unit/web/test_sfi_dock_arbitration.py` | 默认面 Dock 无「重新生成文案」；dark 附录 | ✅ |
| `tests/unit/web/test_ux_trust_v1.py` | 设置总述去「AI 文案（可选）」 | ✅ |
| `tests/unit/web/test_studio_home_v2.py` / settings accordion | AI zone 默认不可见 | ✅ |
| e2e settings observability（若锁 AI zone） | 对齐 NAS | ✅ 默认面断言 zone hidden |

**禁止**：只删断言导致 dark 回归失守。

---

## 6. Dark-switch 回归包（提纲）

| # | 步骤 | 期望 | 结果 |
|---|------|------|------|
| D1 | dark ON → 设置 | AI zone + 配置/管理写作引擎可见 | ☑ |
| D2 | 保存并测试 | ping 可用；无 Key 进遥测 | ☑ |
| D3 | Sheet「重新生成文案」 | 可见可点 | ☑ |
| D4 | 抽屉「按新感觉重写」 | 可见；可 `/narrate` | ☑ |
| D5 | 能力卡 | **仍不 show** | ☑（代码硬关） |
| D6 | 关 switch + 已有 secrets | 入口全隐；narrate 403 | ✅ 默认面门闩 |
| D7 | deeplink | ON 可开 / OFF 忽略 | ✅ OFF e2e |

---

## 7. 与 DLLM / WEA 验收关系

| 文档 | NAS 下地位 |
|------|------------|
| [ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md](./ACCEPTANCE-DESKTOP-LLM-SETUP-V1.md) | **用户面 superseded**；工程/dark 回归见上表 D1–D7 |
| [ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md](./ACCEPTANCE-WRITING-ENGINE-API-HARDENING-V1.md) | 仅 dark ON 下执行 |
| 本文件 | **当前版本默认面现行验收** |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.2 | 2026-07-22 | e2e/DOC 收口：勾选自动化项；DOC-NAS-02；settings observability 对齐 |
| v0.1.1 | 2026-07-22 | 对齐 PRD **v0.2.1**：OUT-01～05 / §14 指针；W0 门槛升至 v0.2.1；**AC-NAS-17a 含 ping 403** · 增 17c（status 可保留） |
| v0.1.0 | 2026-07-22 | 初稿：AC-NAS-01～17 + W0 门 + 翻转清单 + dark 包（对齐 PRD v0.2.0） |
