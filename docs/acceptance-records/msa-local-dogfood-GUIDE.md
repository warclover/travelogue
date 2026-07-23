# MSA · 本机狗粮 / 短手测指南

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-23 |
| 关联 | [PRD MSA](../PRD-MOSAIC-SLOT-ADAPTATION-V1.md) · [ACCEPTANCE](../ACCEPTANCE-MOSAIC-SLOT-ADAPTATION-V1.md) |
| 配置样例 | [`docs/config-msa-dogfood.example.yaml`](../config-msa-dogfood.example.yaml) |
| 相邻 | [MTSO 狗粮](./mtso-local-dogfood-GUIDE.md)（正交 · 可同开） |
| 仓库默认 | `slot_adaptation.enabled=false`（fail-closed 至 AC-11 决策） |

> **目标**：三类画像 on/off 对照截图 + 主体完整性盲评；**不是**自动转正门槛。  
> 漏斗断言读 raw mosaic log（`msaProfile` / `trackOverride` / `msaOutcome` / `cropRisk`），勿只看预览观感。

---

## 1. 一键配置

复制样例进项目根 `config.yaml`（gitignore），**重启后对该 trip 重新 curate**。

建议对照矩阵（同一 trip 跑两次）：

| 轮次 | MSA | MTSO SO | experiments | 用途 |
|------|-----|---------|-------------|------|
| **Off** | false | 任意（建议 false） | false | 基线截图 |
| **On** | true | true（可选） | 按需 | 自适应截图 |

```yaml
mosaic:
  slot_adaptation:
    enabled: true   # Off 轮改为 false
  # 可选：与 MTSO 同开做正交回归（AC-10）
  selection_optimization:
    enabled: true
  template_experiments:
    enabled: false
```

---

## 2. 三类画像语料（必测）

| 画像 | 语料建议 | 关注 |
|------|----------|------|
| **A 全单反** | 横图多为 3:2（≈3000×2000） | 主槽贴 ~1.50；地平线/脚不被砍 |
| **B 全手机** | 横图多为 4:3 | 主槽贴 ~1.33；少「宽银幕条」感 |
| **C 混排** | 同窗混 3:2 + 4:3 | `landPeak=mixed`；**整屏一套轨道**；气质统一 |

合成窗可用自动化（`test_msa_pr_a`）；实册至少各 1 个 chapter 截图。

---

## 3. 对照截图清单（on / off）

每个画像各留 **Off** 与 **On** 两张（同屏同资产序）：

| # | 文件名建议 | 检查 |
|---|------------|------|
| A0 | `msa-persona-a-off.png` | 基线扁槽 cover |
| A1 | `msa-persona-a-on.png` | 主槽更高；可选 contain 纸色 |
| B0 / B1 | `msa-persona-b-*.png` | 同上 |
| C0 / C1 | `msa-persona-c-*.png` | 混峰不「每图各打各的」 |

---

## 4. 盲评三问（AC-09）

评分人：**不看** on/off 标签，成对打乱后答：

1. **主体完整性**：地平线 / 头顶 / 脚是否更完整？（优 / 平 / 差）  
2. **杂志感**：留白是否像装裱而非贴图板？（优 / 平 / 差）  
3. **气质统一**（仅 C）：整页是否一种气质？（优 / 平 / 差）

**通过线（产品建议）**：A/B 主体完整性 On ≥ Off；C 气质统一 On ≥ Off；且 **无** 朝向硬门 / dense 红线回退（与 Off 对照日志）。

记录模板：[msa-blind-review-TEMPLATE.md](./msa-blind-review-TEMPLATE.md)

---

## 5. 自动化烟测

```powershell
python -m pytest tests/unit/layout_engine/test_msa_pr_a.py tests/unit/layout_engine/test_msa_pr_b.py tests/unit/layout_engine/test_msa_pr_c.py -q
```

---

## 6. 默认 on 决策（AC-11 / O-05）

- 盲评未签核前：**保持** `slot_adaptation.enabled` 仓库默认 **false**。  
- 签核后写日期版决策记录，再改默认（另 PR，勿塞进功能 PR）。  
- 现状见：[msa-default-on-decision-2026-07-23.md](./msa-default-on-decision-2026-07-23.md)
