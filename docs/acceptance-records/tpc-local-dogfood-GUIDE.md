# TPC · 本机狗粮 / 手测指南（开发期）

| 属性 | 内容 |
|------|------|
| 日期 | 2026-07-18 |
| 关联 | [PRD-TEMPLATE-CONTRACT-V1](../PRD-TEMPLATE-CONTRACT-V1.md) · [缺口清单](./tpc-gap-checklist-2026-07-18.md) · [配置样例](../config-tpc-dogfood.example.yaml) |
| 适用 | **无外部用户** 的开发机手测；**不是**对外默认开 / Go exit |
| 仓库默认 | `mosaic.template_contract.enabled=false` · `features.gcs_poster_bric.enabled=false`（保持 AC-TPC-01） |

---

## 1. 为什么用本机 config，而不是改代码默认

| 做法 | 结果 |
|------|------|
| 改 `TemplateContractConfig.enabled` 默认值 | CI / golden（AC-TPC-01）会挂；「合入」与「默认开」绑死 |
| **本机 `config.yaml` 打开**（gitignore） | Studio/CLI 走 on 路径；仓库与 CI 仍默认 off |

结论：开发期手测 → **只开本机配置**。

---

## 2. 一键配置

示例片段（已提交）：[`docs/config-tpc-dogfood.example.yaml`](../config-tpc-dogfood.example.yaml)

合并进项目根 `config.yaml`（勿提交）：

```yaml
mosaic:
  template_contract:
    enabled: true
    shadow_log: true

features:
  gcs_poster_bric:
    enabled: true
```

验证（仓库根目录）：

```bash
python -c "from travelogue.config import get_config; c=get_config(reload=True); print('contract', c.mosaic.template_contract.enabled); print('poster_bric', c.studio.gcs_poster_bric.enabled)"
```

期望输出：`contract True` · `poster_bric True`（无 `unknown keys` 告警）。

> `gcs_poster_bric` 请写在 **`features:`** 下；写在 `studio:` 下可能触发未知键告警。

改完后 **重启 Studio**（或重新拉起 CLI），再对 trip **重新 curate / 更新版面**，旧 `screens[]` 不会自动切换。

---

## 3. 打开后你会看到什么

### 3.1 Template Contract（`enabled=true`）

- 候选入口走 mix 倒排 + eligibility（AC-TPC-02/03）。
- W3 手写模板（`rollout.percent: 0` + `experimental`）在 contract on 时解锁，例如：
  - `screen-mosaic-4-1l3p-rail`
  - `screen-mosaic-5-2p3l-rail`
  - `screen-mosaic-4-2l2p-weighted`
  - `screen-mosaic-4-hero-70-sidebar`
- `shadow_log=true` 时，窗级决策可带 `windowMix` / `candidateSource` 等字段（便于对照）。

### 3.2 poster_bric（`gcs_poster_bric.enabled=true`）

- Studio 长图导出面板出现 ▾「单屏海报」（文案勿与「九宫格」混淆）。
- 导出写 PNG + sidecar，**不改写** `trip.json` 的 `screens[]`。
- Composer：vendored MIT BRIC（失败回退 shelf）。

---

## 4. 推荐手测路径

### A. 版式 on vs off（核心）

```bash
# 对真实 trip（需 trips/<id>/trip.json）
python scripts/layout_compare.py --trip-dir trips/<id>
```

产出：`.cache/tpc-layout-compare/<tripId>/`（JSON + HTML）。

手记（每行一例）：

```json
{"tripId":"…","tag":"mix_hole|hero70|regressed|ok","note":"自由文本","prefer":"on|off|tie"}
```

路径：`.cache/tpc-layout-compare/<tripId>/dogfood-notes.jsonl`

重点看：

1. 混向窗（2L2P / 1L3P / 2P3L）是否少「硬塞」感  
2. hero-70 侧栏是否过挤 / 留白是否合理  
3. 是否出现明显回归（宁可记 `prefer: off`）

### B. Shadow diff（有本地 golden trip 时）

```bash
python scripts/layout_contract_shadow_diff.py --golden --out docs/acceptance-records/tpc-w1-shadow-diff.json
# 已有成书、不想 re-curate：
python scripts/layout_contract_shadow_diff.py <tripId> --from-existing
```

`--from-existing` 已消化「成书 pattern 无法再 try_order」的 harness 假阳性（`harnessFp`）。

### C. 单屏海报

1. 确认 `poster_bric` 为 true 并重启 Studio  
2. 打开一本 ≥3 张 kept 图的游记  
3. 导出 ▾「单屏海报」→ 检查无重叠、gutter、AR；确认 `screens[]` 未变  

### D. 关回默认 off（对照 / 跑单测前）

```yaml
mosaic:
  template_contract:
    enabled: false
features:
  gcs_poster_bric:
    enabled: false
```

或临时移开 `config.yaml` 中上述键后 `get_config(reload=True)`。

---

## 5. 手测检查清单（签核用）

| # | 项 | 通过？ | 备注 |
|---|----|--------|------|
| F1 | config 验证 `contract=True` | ☐ | |
| F2 | 混向相册 re-curate 后出现 W3 或合理 fallback | ☐ | |
| F3 | `layout_compare` HTML 可读，手记 ≥3 行 | ☐ | |
| F4 | hero-70 / 1L3P 至少各看一本 | ☐ | |
| F5 | poster_bric 导出成功且 screens fingerprint 不变 | ☐ | |
| F6 | 关回 `enabled=false` 后版面回到熟悉 baseline | ☐ | |

---

## 6. 明确不在本指南范围

- 仓库默认改 `true` / 对外 Go  
- AC-TPC-12 BQP 全量签核（需本地 corpus）  
- 正式盲评（D-TPC-10）  
- 删除 `main_eligibility.py`（AC-TPC-04②，狗粮后再做）

---

## 7. 相关路径速查

| 用途 | 路径 |
|------|------|
| 本机配置 | `config.yaml`（gitignore） |
| 示例片段 | `docs/config-tpc-dogfood.example.yaml` |
| 缺口状态 | `docs/acceptance-records/tpc-gap-checklist-2026-07-18.md` |
| P95 实测 | `docs/acceptance-records/tpc-curate-perf.json` |
| compare CLI | `scripts/layout_compare.py` |
| shadow CLI | `scripts/layout_contract_shadow_diff.py` |
| W3 模板包说明 | `docs/acceptance-records/tpc-w3-template-pack-2026-07-18.md` |
