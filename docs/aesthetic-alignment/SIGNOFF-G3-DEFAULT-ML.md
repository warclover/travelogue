# G3 · 默认开启分层审美校准 Sign-off

> **状态**：**待联签**（文档就绪 · **未改代码默认**）  
> PRD：[PRD-STRATIFIED-CURATION.md](../PRD-STRATIFIED-CURATION.md) DS-6 · [PRD-AESTHETIC-ALIGNMENT.md](../PRD-AESTHETIC-ALIGNMENT.md) §8  
> 前置冻结：[SIGNOFF-PILOT-FREEZE.v3.md](./SIGNOFF-PILOT-FREEZE.v3.md)  
> 配置快照：[aesthetic-pilot-config.freeze.v3.yaml](../acceptance-records/aesthetic-pilot-config.freeze.v3.yaml)  
> 机器可读：[aesthetic-g3-signoff.v3.json](../acceptance-records/aesthetic-g3-signoff.v3.json)

---

## 1. 目标

将 **`AppConfig.aesthetic` 代码默认** 从 rules-only（`ml_calibrate: false`）切换为 **分层精选 pilot 冻结配置**（`ml_calibrate: true` + stratum blend + album-relative + moment-only MLLM 等），使新 trip / 未显式配置 `config.yaml` 的环境默认走 AC-SC 验收路径。

**本 signoff 不包含**：

- 自动开启 MLLM（仍依赖 `DASHSCOPE_API_KEY` 与 `mllm.enabled`）
- 修改已冻结语料或 pairwise canonical 轮次
- 撤销东澳 AC-SC-03 product waiver

---

## 2. 门禁对照（AC-SC → G3）

| 门禁 | G3 要求 | 当前状态 | 证据 |
|------|---------|----------|------|
| **AC-SC-00** | 分层 min-n | ✅ | [aesthetic-stratified-signoff.v3.json](../acceptance-records/aesthetic-stratified-signoff.v3.json) |
| **AC-SC-01** | 每层 blend Δ SRCC | ✅ | person Δ=+0.133 · landscape Δ=+0.128 |
| **AC-SC-02** | 加权 Δ ≥ 0.10 | ✅ | weighted Δ=0.131 |
| **AC-SC-03** | ≥3 本 pairwise ≥60% | ✅（含 waiver） | 2/3 strict + 东澳 waiver · [purpose-pairwise-signoff.v3.json](../acceptance-records/purpose-pairwise-signoff.v3.json) |
| **AC-SC-04** | albumProfile | ✅ | 三本 dogfood |
| **AC-SC-05/06** | 继承 AA 开关 | ✅ | fail-open · 回滚路径 |
| **pooled SRCC** | 健康检查 | ⚠️ 未达旧 AC-AA-02 | **不阻塞 G3**（PRD-SC DS-5） |
| **P3 缺陷率** | AC-PC-D proxy | 📋 脚本就绪 | [aesthetic_portrait_defect_signoff.py](../../scripts/aesthetic_portrait_defect_signoff.py) · 待本机 dogfood baseline |

**结论**：分层主门禁已关；G3 改默认的 **产品风险** 集中在东澳 waiver 与 pooled 健康检查，已在 §4 记录。

---

## 3. 批准后将变更的默认值

权威来源：[aesthetic-pilot-config.freeze.v3.yaml](../acceptance-records/aesthetic-pilot-config.freeze.v3.yaml)

| 字段 | 当前 `AppConfig` 默认 | G3 目标默认 |
|------|----------------------|-------------|
| `aesthetic.enabled` | `true` | `true`（不变） |
| `aesthetic.ml_calibrate` | **`false`** | **`true`** |
| `aesthetic.use_stratum_blend` | `false` | `true` |
| `aesthetic.stratum_blend_only` | `()` | `[landscape, person]` |
| `aesthetic.stratum_blend_only_by_purpose.hero` | `{}` | `hero: [landscape]` |
| `aesthetic.stratum_blends` | 内置常数 | merged v3 推荐值 |
| `aesthetic.use_album_relative` | `false` | `true` |
| `aesthetic.portrait_lite_enabled` | `false` | `true` |
| `aesthetic.mllm.enabled` | `false` | **`false`**（仍 opt-in） |
| `aesthetic.mllm.shortlist_purposes` | 多 purpose | **`[moment]`** |

**代码触点**（联签通过后执行，**本 PR 仅文档**）：

- `travelogue/config/aesthetic.py` · `AestheticConfig` dataclass 默认值
- `docs/config-pa.example.yaml` · 注释与示例对齐
- `tests/` · 依赖 rules-only 默认的用例改为显式 `ml_calibrate=False` 或更新期望

---

## 4. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 东澳整本 pairwise 50% | waiver 已归档；G3 后监控 cover/hero 人工抽检 |
| 无 pyiqa / GPU | fail-open：learned 缺失时保持 rules overall |
| MLLM 成本 | 默认仍 `mllm.enabled: false`；G2 手动开 |
| 旧 trip 无 portrait 块 | P3 降权门控 `gate_changes_on_signal` |
| 回滚 | `ml_calibrate: false` + recurate（见 ROLLOUT） |

---

## 5. 放量步骤（联签后）

1. 合并 G3 代码默认 PR（单独 PR，引用本 signoff）。
2. CI：`pytest tests/test_aesthetic_* tests/test_album_profile*` 全绿。
3. 三本 dogfood **recurate** → 对比 cover/hero/moment 与冻结前 snapshot。
4. 跑缺陷率 signoff，确认 ≤ baseline（若已有 baseline）。
5. 更新 [aesthetic-alignment-rollout-log.json](../acceptance-records/aesthetic-alignment-rollout-log.json) · `G3-default-on.status` → `passed`。
6. 新用户：仅需 `pip install -e ".[cull-ml]"` + 可选 MLLM key。

---

## 6. 回滚

```yaml
aesthetic:
  ml_calibrate: false
  use_stratum_blend: false
  use_album_relative: false
  mllm:
    enabled: false
```

recurate 目标 trip → `quality.aesthetic.source` 回到 `rules`。

---

## 7. 联签

| 角色 | 姓名 | 日期 | 决定 |
|------|------|------|------|
| 产品 | | | ☐ 批准 G3 改默认 ☐ 推迟 |
| 算法 | | | ☐ 接受东澳 waiver 进入 G3 ☐ 需补测 |
| 工程 | | | ☐ 批准实施窗口 |

**生效条件**：上表三栏勾选「批准」+ G3 代码 PR 合并。

---

## 8. 修订记录

| 日期 | 说明 |
|------|------|
| 2026-06-18 | 初版：AC-SC 全矩阵 + pilot 冻结后 G3 单列 signoff 草案 |
