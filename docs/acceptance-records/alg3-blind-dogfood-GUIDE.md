# ALG-V3 · W1b / W2-A4 本机盲评狗粮指南

| 属性 | 内容 |
|------|------|
| 日期 | 2026-08-02 |
| 配置样例 | [config-alg3-blind-dogfood.example.yaml](../config-alg3-blind-dogfood.example.yaml) |
| 记录模板 | [alg3-blind-review-TEMPLATE.md](./alg3-blind-review-TEMPLATE.md) |
| 脚手架 | [W1b Pass 2026-08-02](./alg3-w1b-blind-review-2026-08-02.md) · [A4 PENDING](./alg3-w2-a4-blind-review-PENDING.md) |
| 验收 | [ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md](../ACCEPTANCE-ALGORITHM-OPTIMIZATION-V3.md) §5 |

> **目标**：成对 On/Off 截图 + 四问人评。自动化 AC-10 / AC-12 **不**代替本指南。  
> **不挡编码**；挡 **M1b 宣称** / **A4 抬默认 on**。

---

## 1. 准备

1. 把样例 knobs 拷进根目录 `config.yaml`（gitignore）。  
2. **重启** Studio（只留一个 8766 实例）。  
3. 选语料（同一 `tripId` 跑两臂）：
   - 无 vision、密连拍步行段（假切条高发）
   - 横竖混拼同场景
   - （可选）窄屏长图导出
4. 截图目录建议：`docs/acceptance-records/attachments/alg3-blind-2026-08-02/`  
   命名：`w1b-pairN-{off|on}.png` · `a4-pairN-{off|on}.png`

```powershell
python -m travelogue studio run <tripId> --until layout
```

---

## 2. W1b 对照（条件 clone）

| 臂 | `mosaic.near_scene_clone_gate` |
|----|--------------------------------|
| **Off** | `enabled: false` · `conditional: false` |
| **On** | `enabled: false` · `conditional: true`（现网默认） |

关注：问1 假切条 · 问3 混拼。  
漏斗：`curation.algoV3.cloneGateEffective` · `rejectFunnelTop.near_scene_clone`

---

## 3. W2-A4 对照（Atom experimental_relax）

| 臂 | `shotGrouping.mosaic.atom.experimental_relax` |
|----|-----------------------------------------------|
| **Off** | `false`（仓库默认） |
| **On** | `true`（仅实验臂） |

关注：问1 · 问2；问3 可 N/A。  
**禁止**仅凭 funnel↓ 宣称 AC-12 过门（X04）。

---

## 4. 评分与结案

打乱 On/Off 标签后按模板四问打分。

| 门 | 通过线 |
|----|--------|
| W1b | 问1 On≥Off；问3 混拼不差于 Off |
| W2-A4 | 问1+2 On≥Off；问3 不差（可 N/A） |

填脚手架结论 → Pass / Conditional / Fail，并链截图路径。

---

## 5. 本机复现脚本（可选）

```powershell
# 单臂 layout + render + 快照 algoV3/HTML
python scripts/alg3_blind_dogfood_arm.py w1b-off docs/acceptance-records/attachments/alg3-blind-2026-08-02/cfg-w1b-off.yaml
python scripts/alg3_blind_dogfood_arm.py w1b-on  docs/acceptance-records/attachments/alg3-blind-2026-08-02/cfg-w1b-on.yaml

# 截图（需 Studio 8766 已起）
python scripts/alg3_blind_dogfood_shots.py
python scripts/alg3_blind_dogfood_crop.py
```

2026-08-02 已对 `demo-3ee2727aea` 产出 pair1 材料，见 PENDING 页内链。
