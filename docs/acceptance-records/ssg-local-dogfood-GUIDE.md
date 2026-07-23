# SSG · 本机狗粮 / 短手测指南

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-23 |
| 关联 | [PRD SSG](../PRD-SMART-SHOT-GROUPING-V1.md) · [ACCEPTANCE](../ACCEPTANCE-SMART-SHOT-GROUPING-V1.md) |
| 配置样例 | [`docs/config-ssg-dogfood.example.yaml`](../config-ssg-dogfood.example.yaml) |
| 仓库默认 | `shotGrouping.enabled=auto` · **vision 默认 off**（见默认 on 决策） |

> **目标**：混导 + 换装对照截图与盲评记录；自动化数值门见 pytest，**不是**自动转正门槛。

---

## 1. 一键配置

复制样例进项目根 `config.yaml`（gitignore），**重启**后对 trip：

```powershell
# 有 sceneCluster 后单独重跑分镜
python -m travelogue cluster reshotgroup <tripIdOrPath>
# 或整轨（含 clustering）
python -m travelogue studio run <tripId> --until structure
```

对照矩阵：

| 轮次 | shotGrouping | look | vision | 用途 |
|------|--------------|------|--------|------|
| **Off** | false | — | 任意 | 基线：易出现假切条 / 无造型拆 |
| **Scene** | true | false | true | M1：场景分镜 + 切条门 |
| **Look** | true | true | true | M2：同景点换装拆组 |

---

## 2. 语料（必测）

| 画像 | 语料 | 关注 |
|------|------|------|
| **混导** | ≥2 场景同导入（可扩 `tests/fixtures/clustering/golden-mixed-scenes`） | 同场景同组率；跨 softSplit 拆组 |
| **换装** | 同地 ≥3 造型（实拍；合成见 `outfit-change-synthetic`） | look 边界；勿用 GPS 粘合 |
| **切条风险** | 同场景连拍密时间窗 | Off 易假切条；On 应硬拒同组紧窗 |

---

## 3. 对照截图清单

| # | 文件名建议 | 检查 |
|---|------------|------|
| M0 | `ssg-mixed-off.png` | 基线假切条 / 乱序 |
| M1 | `ssg-mixed-scene.png` | 同场景成组；切条类不跨组 |
| L0 | `ssg-outfit-off.png` | 换装仍粘在同一 scene |
| L1 | `ssg-outfit-look.png` | ≥2 个 `kind=look` 边界 |

漏斗断言（可选）：`curation.shotGrouping.stats` · `pipeline.timings.shotGroupingMs`。

---

## 4. 盲评三问

评分人：**不看** on/off 标签，成对打乱后答：

1. **假切条**：同场景是否不再被拆成「一条切开」？（优 / 平 / 差）  
2. **换装**：同景点换装是否分开成组？（优 / 平 / 差）  
3. **混拼**：合法杂志混拼是否被误杀？（优 / 平 / 差 · 仅混拼窗）

**通过线（产品建议）**：1+2 的 On ≥ Off；3 不差于 Off。

记录模板：[ssg-blind-review-TEMPLATE.md](./ssg-blind-review-TEMPLATE.md)

---

## 5. 自动化烟测

```powershell
python -m pytest tests/unit/curation/test_shot_grouping.py tests/unit/curation/test_look_split.py tests/unit/curation/test_look_threshold_calibration.py tests/unit/curation/test_look_cache_and_toggles.py tests/unit/layout_engine/test_shot_group_gate.py -q
```

---

## 6. 默认 on 决策

见 [ssg-default-on-decision-2026-07-23.md](./ssg-default-on-decision-2026-07-23.md)。  
盲评未签核前：**不**把 vision / shotGrouping 仓库默认改为强制 true。
