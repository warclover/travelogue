# LSE 能力开关页 · 验收记录

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-智能排版开关页.md](../PRD-智能排版开关页.md) v0.2 |
| **页面** | `http://127.0.0.1:8766/lse-flags-admin` |
| **API** | `GET/PATCH /__travelogue/layout-strategies/capabilities` |
| **自动化** | `pytest tests/test_studio_lse_flags_admin.py` · `tests/test_lse_flags_dogfood.py` |
| **日期** | 2026-06-08 |
| **处置结论** | [P17-LSE-处置建议.md](../P17-LSE-处置建议.md) · v1.0 保留代码、默认关闭 |
| **观感路线** | [观感提升路线图.md](../观感提升路线图.md) · P0–P4 优先级 |

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

## 真实 trip 对比 · linzhi（2026-06-08）

脚本：`python scripts/lse_flags_curate_compare.py linzhi`  
报告：`.cache/lse-flags-compare/linzhi/compare_report.json`

| 维度 | baseline（LSE 关） | caps_full（LSE 开 + 全能力） |
|------|-------------------|------------------------------|
| 资产 / 屏数 | 232 / 55 | 232 / 55 |
| capabilityFlags | 无 | 9 项全 true |
| toneContinuity 权重 | 0 | 0.07 |
| 屏级差异 | — | **1/55（1.82%）** |
| 唯一 pattern 变化 | 屏 #33：`screen-landscape-6` | → `screen-mosaic-6-main-hero-plus-5` |
| patternDiversity | 0.164 | 0.182 ↑ |
| subjectRunScore | 0.806 | 0.751 ↓ |
| aspectPatternMatchRate | 0.959 | 0.959 = |

结论：开关已生效（runtime + capabilityFlags 明确不同），但 **linzhi 成稿几乎不变**——能力主要改 mosaic 打分/节拍软乘子，在已有 beam 路径上只推动 1 屏版式升级；要更大观感差异需配合引擎默认上量 + 权重/选片升级。
