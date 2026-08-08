# Route C W0.5b 冲质量 · 落地与 Spike 状态

| 属性 | 内容 |
|------|------|
| **日期** | 2026-08-08 |
| **目标** | 冲 AC-CAL-11（OCR≥90%）· 方案 1A+2A |
| **关联** | [W0.5 基线](cover-calligraphy-title-v1-w05-route-c-spike-2026-08-08.md) · [失败图审计](cover-calligraphy-title-v1-route-c-w05b-audit-2026-08-08.md) |

## 1. 已落地（代码）

| 项 | 位置 | 说明 |
|----|------|------|
| 失败图人工审计 | `cover-calligraphy-title-v1-route-c-w05b-audit-2026-08-08.md` | 11 失败中 9=`glyph_wrong`，1=`ambiguous`，1=`ocr_false_reject` → **不放松 OCR 门禁** |
| Prompt v2 | `style_registry.py` | 默认 `prompt_version=v2`；强化逐字准确 / 禁增删 / 标点保留；负向词加错字类 |
| OCR 失败重试 1 次 | `engine.py` + `TitleArtConfig.route_c_max_attempts=2` | 仅 `E_CAL_C_OCR_MISMATCH` 重试；其它失败立即 B |
| 风险规则 | `risk_rules.py` | 标点 / 叠字（同字≥2）→ 未调 API 直接 B |
| 配置接线 | `title_art.py` / Studio handler / CLI | `model_name`、`prompt_version`、`route_c_max_attempts`、`ocr_verify` 传入引擎 |
| Spike 矩阵脚本 | `scripts/title_art_route_c_w05b_spike.py` | E1 重试 · E2 v1/v2 · E3 风险桶；支持 `--dry-run` |

## 2. 真实 API Spike 状态

本机执行时 **未设置 `DASHSCOPE_API_KEY`**，无法完成本轮真实矩阵调用。

已完成：

```text
python scripts/title_art_route_c_w05b_spike.py --dry-run --prompt-version both --samples 2
```

干跑分配摘要（28 标题 × 2 pv × 2 samples = 112 行）：

| 桶 | 行数 |
|----|-----:|
| 策略跳过（生僻字 + 标点/叠字） | 52 |
| 可尝试（dry-run 未真正生成） | 60 |

干跑报告：[`cover-calligraphy-title-v1-route-c-w05b-spike-2026-08-08.md`](cover-calligraphy-title-v1-route-c-w05b-spike-2026-08-08.md)

### 补跑命令（有 Key 后）

```powershell
$env:DASHSCOPE_API_KEY = "sk-..."
# 推荐：生产同款策略（跳过风险桶）+ v2 + 1 次重试
python scripts/title_art_route_c_w05b_spike.py --prompt-version v2 --retries 1 --samples 2
# 对照：v1 vs v2（费用约翻倍）
python scripts/title_art_route_c_w05b_spike.py --prompt-version both --retries 1 --samples 2
```

成功标准（AC-CAL-11）：报告里 **`after_retry_rate` ≥ 0.90** 且 `attempted` ≥ 20。

## 3. 门禁结论（当前）

| 项 | 结论 |
|----|------|
| **AC-CAL-11** | ❌ 仍未用本轮真实数据翻盘；基线保持 57.7%。代码已就绪，待 Key 补跑 |
| **`route_c_enabled` 默认** | 维持 **`false`**（OQ-CAL-06） |
| **显式高级项** | 配置可开，但产品文案须标明「可能静默回退路线 B」；**不得**在未达标前暗示默认可用 |
| **下一杠杆** | 若补跑后 `after_retry_rate` 仍明显 <90%，开 W0.6 vendor bakeoff（即梦/混元）工单——本轮未扩集成 |

## 4. 单测

`tests/unit/cover_engine/` 相关：风险规则 / 重试 / model+prompt 透传 / style v2 — 已通过。
