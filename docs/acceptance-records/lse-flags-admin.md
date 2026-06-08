# LSE 能力开关页 · 验收记录

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-智能排版开关页.md](../PRD-智能排版开关页.md) v0.2 |
| **页面** | `http://127.0.0.1:8766/lse-flags-admin` |
| **API** | `GET/PATCH /__travelogue/layout-strategies/capabilities` |
| **自动化** | `pytest tests/test_studio_lse_flags_admin.py` · `tests/test_lse_flags_dogfood.py` |
| **日期** | 2026-06-08 |

## AC 核对

| AC | 说明 | 自动化 |
|----|------|--------|
| AC-1 | 页面 9 能力 + 引擎横幅，无 pace_profile | ✅ |
| AC-2 | GET effective/fromConfig/fromPack + rollout 只读 | ✅ |
| AC-3 | PATCH 写盘 + capability_flags_snapshot | ✅ |
| AC-4 | beat 枚举 + 非法 400 | ✅ |
| AC-5 | engine enabled 写 config | ✅ |
| AC-6 | 引擎关 + 能力开 → 告警条件 | ✅ API；UI 手测 warn-box |
| AC-7 | 403 鉴权 | ✅ |
| AC-8 | PATCH 审计日志 | ✅ |

## 手测清单（dogfood）

- [x] 开启 LSE 引擎 → 重跑 trip curate → `layoutStrategy.capabilityFlags` 更新（`tests/test_lse_flags_dogfood.py`）
- [x] 开启 `saliencyScoring` + `toneHarmony` → mosaic config 接线（同上 + `mosaic_config_from_pack`）
- [x] PATCH 写盘与 `strategy_trace_meta` 一致（同上）
- [ ] 非 loopback 无 internal 时 API 403（浏览器/LAN 手测）
- [ ] 保存后刷新页面，值与磁盘 `config.yaml` 一致（Studio UI 手测）
