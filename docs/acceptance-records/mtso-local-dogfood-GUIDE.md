# MTSO · 本机狗粮 / 短手测指南

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-23 |
| 关联 | [PRD MTSO](../PRD-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) · [ACCEPTANCE](../ACCEPTANCE-MOSAIC-TEMPLATE-SELECTION-OPTIMIZATION-V1.md) |
| 正交 | [MSA 狗粮](./msa-local-dogfood-GUIDE.md)（槽位自适应 · 可同开） |
| 配置样例 | [`docs/config-mtso-experiments-dogfood.example.yaml`](../config-mtso-experiments-dogfood.example.yaml) |
| 仓库默认 | `selection_optimization.enabled=false` · `template_experiments.enabled=false`（fail-closed） |

> **不是** Go exit / 转正门槛。目标：验路径不崩、漏斗可读、双 SKU 可见性符合预期。

---

## 1. 一键配置

复制样例片段进项目根 `config.yaml`（gitignore），填入真实 `cohort_trip_ids`，**重启 Studio/CLI** 后对该 trip **重新 curate**。

建议狗粮同时开：

```yaml
mosaic:
  template_contract:
    enabled: true
    shadow_log: true
  template_experiments:
    enabled: true
    allowlist:
      - screen-mosaic-5-1p4l-portrait-hero
      - screen-mosaic-5-2p3l-portrait-hero-rail
    cohort_trip_ids:
      - your-trip-id-here
  selection_optimization:
    enabled: true
```

---

## 2. 对照场景（必测）

| # | 配置 | 期望 |
|---|------|------|
| A | SO=true + experiments 三元组 | 强竖 1P4L 窗可看见 `1p4l-portrait-hero`；2P3L 窗可看见 `2p3l-portrait-hero-rail`；硬拒 `main-portrait-3land` 时 reason=`mixed_routing:mixed_portrait_is_hero` |
| B | SO=true + experiments OFF | 硬拒 detail 含 `dual_sku_gated`；MCS 失败后 cursor 强竖 → `screen-portrait-1` rescue |
| C | SO=false（嵌套子开关随意） | 与仓库默认路径一致；**无** mixed_routing 硬拒；experimental 仍不可见 |

漏斗断言读 **raw** `drain_mosaic_capture` / 决策日志字段（D-MTSO-11），勿只看展示 Top-3。

---

## 3. 自动化烟测

```powershell
python -m pytest tests/unit/layout_engine/test_mtso_pr_d.py tests/unit/layout_engine/test_mtso_pr_c2_skus.py -q
```

---

## 4. PR-D 仍待手测 / 盲评

- [ ] 代表 trip compare（双阈值 AC-11）
- [ ] 2P3L 三列几何截图签核（辅竖 AR≈0.27 可读）
- [ ] 转正或归档（AC-12）；通过前勿写 `lte_policy`
