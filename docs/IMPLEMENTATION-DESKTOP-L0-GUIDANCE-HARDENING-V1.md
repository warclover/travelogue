# IMPLEMENTATION · 无 Key 主路径加固与首启预期管理 V1

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md](./PRD-DESKTOP-L0-GUIDANCE-HARDENING-V1.md) **v1.0.0** |
| **更新日期** | 2026-07-15 |
| **范围** | **W1 P0 ✅** + **W2 P1 ✅** + **W2.1 缺口收口 ✅** + **W3 Resume 断点修复 ✅** |

## W1 落地对照

| ID | 状态 | 锚点 |
|----|------|------|
| BE-01 | ✅ | `resolve_studio_narrate_provider` 导入恒 stub；`studio_pipeline` / `studio_g1` |
| BE-02 | ✅ | 同上 + `tests/unit/web/test_l0_guidance_hardening.py` |
| BE-03 | ✅ | pipeline / g1：`E_LLM_AUTH` 降级 stub + warn 日志 |
| BE-04 | ✅ | `ensure_user_data_layout` → `_force_bootstrap_llm_provider_stub` |
| BE-06 | ✅ | `job_error_payload` / `demo_error_payload` → `recoverableWithStub` |
| BE-08 | ✅ | import payload `forceStub` → worker → `run_studio_pipeline(force_stub=…)` |
| FE-01 | ✅ | `capability-card.js` COPY-L0G 正文 |
| FE-03～06 | ✅ | `import-failed.js` + `studio-home-v2.html` T-FAIL-01 |
| FE-09 | ✅ | `constants.js` / `errors.js` |

## W2 落地对照

| ID | 状态 | 锚点 |
|----|------|------|
| BE-05 | ✅ | `config.yaml.example` 默认 `provider: stub` |
| BE-07 | ✅ | `run_studio_llm_narrate` 无凭证只抛局部错误；单测断言 trip 不变 |
| BE-09 | ✅ | `studio_errors` / ERROR-CODES = COPY-L0G-09 |
| FE-02 | ✅ | `home-stub-banner.js` T-CAP-06；bootstrap 接线 |
| FE-07 | ✅ | COPY-L0G-07 + MF-06 定稿句 + 失败「去检查配置」 |
| FE-08 | ✅ | `maybeShowStubNarrateTip` + `stubHint.v1`；init-v3 调度 |
| FE-10 | ✅ | 轻状态不与能力卡同帧；能力卡未见过则不出条 |
| FE-11 | ✅ | `home_stub_banner_*` / T-CAP-05 / import_fail_* / `capability_card_cta.action` |

## W2.1 缺口收口

| 缺口 | 状态 | 锚点 |
|------|------|------|
| 导入/FirstSuccess/Idle 同步隐藏轻状态 | ✅ | `syncHomeStubBanner` in import-run / first-success / bootstrap / import-failed |
| 预览 narrate 失败「去检查配置」 | ✅ | `preview-toolbar/core.js` → `openLlmSettings` |
| COPY-L0G-12 设置空态统一 | ✅ | `llm-settings.js` Modal + 旁注 |
| MF-06 已配置未点生成定稿句 | ✅ | `preview-toolbar-v3-sheet.js` |
| 上传路径 forceStub 续跑 | ✅ | `SS.forceStubNextUpload` + upload form |
| BE-03 warn 日志 | ✅ | `studio_pipeline` / `studio_g1` |
| 埋点 `action` 字段 | ✅ | `capability_card_cta` |

## W3 · Resume 断点修复（2026-07-15）

| 项 | 状态 | 锚点 |
|----|------|------|
| 失败保留 `SS.activePending` | ✅ | `import-run.js` pollImport；仅 success/cancel/dismiss 清除 |
| 设置保存后 resume CTA | ✅ | `llm-settings.js`：`import_fail`→继续本机；`card`/`home_banner`→开始导入 |
| 失败屏文案 + 最近游记兜底 | ✅ | `import-failed.js` + `v2-failure-open-recent` |
| 上传重选 toast 写清 | ✅ | `continueWithStub` upload 分支 |
| FirstSuccess 本机文案轻提示 | ✅ | `HELP_COPY.firstSuccessNext` |
| FE 单测扩展 | ✅ | `test_l0_guidance_hardening_fe.py` |

## 自动化

```powershell
python -m pytest tests/unit/web/test_l0_guidance_hardening.py tests/unit/web/test_l0_guidance_hardening_fe.py tests/unit/web/test_desktop_llm_setup_w2.py tests/unit/web/test_preview_toolbar_v3.py tests/unit/desktop/test_runtime_paths_0b.py -q
```
