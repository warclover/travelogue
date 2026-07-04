# Travelogue · 拼图 MCS 配置恢复 PRD（Mosaic Config Restore）

| 属性 | 内容 |
|------|------|
| **产品代号** | Travelogue |
| **文档版本** | v0.2.0 |
| **状态** | Draft · 四方评审修订稿（v0.1.0 有条件通过） |
| **特性代号** | **MCR**（Mosaic Config Restore，拼图 MCS 配置恢复） |
| **文档类型** | 缺陷修复 + 配置/注册一致性 PRD（非新模板 SKU） |
| **前置条件** | Phase 15 MCS、Phase 16 LTE、Phase 21 density budget 已上线；URO（Usage Rules）基础设施已 merge（`enabled=false` 默认） |
| **关联文档** | [PRD-PHASE15-photo-mosaic-evolution.md](./PRD-PHASE15-photo-mosaic-evolution.md)、[PRD-PHASE21-mosaic-density-budget.md](./PRD-PHASE21-mosaic-density-budget.md)、[PRD-PHASE16-layout-template-engine.md](./PRD-PHASE16-layout-template-engine.md)、[PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md](./PRD-USAGE-RULES-LAYOUT-OPTIMIZATION.md)、[PHASE15-ROLLOUT.md](./PHASE15-ROLLOUT.md)、`config.yaml.example` |
| **更新日期** | 2026-07-04 |

> **定位**
>
> - **问题**：本地与部分环境 curate 后，用户反馈「五张/六张拼图再也看不见」，与 Phase 15/16 设计预期严重偏离。
> - **根因**：并非 render/CSS 损坏，而是 **项目 `config.yaml` 缺少 `mosaic:` 段** 触发加载器错误默认值，叠加 **`lte_policy.yaml` 与 MCS 注册不同步**、以及 **4 个 composite 模板已 deprecated** 的产品决策。
> - **输出**：恢复与 `config.yaml.example` 一致的 MCS 窗宽能力；修复配置缺段时的 silent wrong default；同步 policy 注册；提供可观测诊断与验收脚本。
> - **铁律**：① **不**在本 PR 恢复已 deprecated 的 mosaic SKU（2p3l-equal 等）除非单独 IG；② **不**修改模板几何/CSS；③ **不**改变 P21 density budget 默认配额逻辑；④ URO `enabled=false` 时 curate 输出与修复前 baseline **允许因窗宽恢复而变化**（属预期修复，非 URO 回归）；⑤ MCR **先于** URO `enabled=true` 上线，避免 URO 盲评基线建立在错误窗宽之上。

---

## 0. 术语澄清（避免「缺少 mosaic 段」歧义）

代码库中 **不存在** LTE 模板 YAML 顶层字段 `mosaic:`（`layout_template.schema.json` 未定义）。实际涉及三层不同含义：

| 层级 | 文件 | 「mosaic 段」指什么 | 本 PRD 是否修改 |
|------|------|---------------------|-----------------|
| **L1 项目配置** | `config.yaml` | 顶层 `mosaic:` 块（`enabled_window_sizes` 等） | ✅ **P0 核心** |
| **L2 策略注册** | `lte_policy.yaml` → `mosaic_unified_groups` | MCS 窗族 pattern 白名单 | ✅ **P0** |
| **L3 模板元数据** | `screen-*.yaml` 的 `_legacy` / `usage` | 逆向迁移与使用说明（**不是** `mosaic:` 键） | ⚪ 文档澄清 only |

下文「缺少 mosaic 段」**默认指 L1**；L2 称「未入组 / 注册 orphan」。

**配置别名（评审补充）**：`loader.py` 中 `layout.mosaic_v2` 与顶层 `mosaic:` 合并时 **顶层优先**（与 Phase 15 ROLLOUT 一致）。

---

## 1. 背景与问题

### 1.1 现象（2026-07 实测）

| 现象 | 典型 trip | 说明 |
|------|-----------|------|
| 全书无 6 槽 hero 拼图 | 多数新 curate trip | `screen-mosaic-5-main-hero-plus-4`、`screen-mosaic-6-main-hero-plus-5` 曝光为 0 |
| 5 槽拼图极少 | `demo-80301df45c`（164 张，113 竖） | 14 个 1P+4L 几何窗口 **全部** 因 12s 连拍失败 |
| 旧 demo 仍有拼图 | `linzhi`、`demo-001` | 历史 curate + deprecated 模板，**不可**与新行为对比 |
| 配置「看起来默认开了 MCS」 | 开发者认知 | `MosaicConfig.enabled` 默认 `true`，但 **窗宽被 silently 缩成仅 5** |

### 1.2 根因链（已验证）

```text
config.yaml 无 mosaic: 段
  └─ mosaic_from_dict({}) 使用 .get(..., [5]) 而非 MosaicConfig 默认值
       └─ enabled_window_sizes = (5,) only
            └─ mosaic_window_size_enabled(6) == False
                 └─ 全部 6 槽 pattern mosaic_pattern_disabled == True
                      └─ hero 拼图 + portrait-6 + landscape-6 永不候选

并行因素（非本 PR P0 范围，但需在 PRD 说明）：
  · MOSAIC_5 正式成员仅 main-portrait-3land；hero-3-2-plus-4 为 policy orphan（靠 extras 兜底）
  · 4 个 5 槽 composite deprecated（2p3l-equal 等）— 新 trip 永不候选
  · P21 density_budget 限制 dense 频次 — 属预期，非 bug
  · 竖图相册几何/连拍门槛 — 属预期，非 bug
```

**评审确认（算法）**：MCR-P-01 为真实 Blocker；`density_budget` 等字段在空 `raw` 时已正确回退 dataclass，**仅 `sizes_raw` 一行存在 bug**，P0-a 禁止过度 refactor。

### 1.3 问题 ID

| ID | 问题 | 严重度 | 类型 |
|----|------|--------|------|
| **MCR-P-01** | 缺 `mosaic:` 时 `enabled_window_sizes` 默认为 `[5]`，与 `MosaicConfig` dataclass / `config.yaml.example` 不一致 | **P0 · Blocker** | 配置加载 bug |
| **MCR-P-02** | 本地/新 clone 环境无 `mosaic:` 段，6/4/9 窗 silent 关闭 | **P0 · Blocker** | 环境配置 |
| **MCR-P-03** | `screen-mosaic-5-hero-3-2-plus-4` 为 ga 但未写入 `MOSAIC_5_PATTERN_IDS` | **P0 · 一致性**（评审升格） | 策略 orphan |
| **MCR-P-04** | `_legacy_generated.py` / `lte_export_legacy.py` 与 policy 手工维护，易再 drift | P0 · 工程债 | 同步机制 |
| **MCR-P-05** | 无 curate 诊断提示「窗宽能力 / 为何无拼图」 | P1 · 可观测 | DX |
| **MCR-P-06** | 10 个模板 `usage.summary` 槽位计数与 `photoCount` 不一致 | P2 · 文档 | 非阻塞 |
| **MCR-P-07** | 用户将「模板缺 mosaic 段」误解为 YAML schema 缺失 | P2 · 文档 | 认知 |

### 1.4 与 URO / P21 的边界

| 模块 | 关系 |
|------|------|
| **URO** | 正交；MCR 恢复窗宽后 URO 规则方有完整候选集可过滤；URO 仍默认 `enabled=false`；**MCR 必须先于 URO enabled=true** |
| **P21 density budget** | 保留；恢复 6 窗 **不等于** 无限堆叠 hero 拼图，仍受 `max_large_mosaic_per_chapter` 等约束 |
| **deprecated 模板** | **不在 MCR 范围**；恢复需单独 PRD（SKU 复活 IG） |

---

## 2. 目标与非目标

### 2.1 目标

| ID | 目标 | 验收口径 | 阶段 |
|----|------|----------|------|
| **G-MCR-01** | 缺省配置下 MCS 窗宽与 `config.yaml.example` 一致 | `enabled_window_sizes == (4,5,6,9)` | P0 |
| **G-MCR-02** | 修复 `mosaic_from_dict` 空 dict 默认值 | 单测 + **`load_config` 集成测**（无 mosaic 段） | P0 |
| **G-MCR-03** | onboarding 强制检查清单（**非**提交 `config.yaml`） | `PHASE15-ROLLOUT.md` + 可选启动 INFO | P0 |
| **G-MCR-04** | `hero-3-2-plus-4` 写入 `MOSAIC_5` + codegen sync | 同 PR 跑 export；**行为等价**，消除 drift | **P0** |
| **G-MCR-05** | 诊断脚本解释「为何无拼图」 | `mosaic_config_diag.py`；`--trip`；**exit 1 当 6 窗 disabled** | P1 |
| **G-MCR-06** | golden landscape re-curate 前后 metrics | `chuanzang-studio` ≥1 hero mosaic + **before/after layoutMetrics** | P0 |

### 2.2 非目标

- **不**恢复 `screen-mosaic-5-2p3l-equal` 等 deprecated composite（除非产品单独立项）。
- **不**放宽 `mixed_proximity_seconds`（12s 连拍）或 `main_ar_guard`（属算法门槛，非配置 bug）。
- **不**修改 P21 `density_budget` 默认配额数字。
- **不**新增 LTE schema 字段 `mosaic:`。
- **不**保证竖图主导相册（如儿童年度册）一定出现 5/6 槽拼图。
- **不**将本 PR 与 URO `enabled=true` 或 AC-URO-BLIND 绑定。
- **不**把「提交本地 `config.yaml`」作为 PR deliverable（已在 .gitignore）。

---

## 3. 评审结论与已拍板决策

### 3.1 四方评审总结（2026-07-04）

| 角色 | 结论 | 关键意见 |
|------|------|----------|
| **算法** | ✅ 通过 | 根因准确；恢复 4/9 窗会增加候选竞争；hero-3-2 入组为 parity 非排版增益 |
| **开发** | ✅ 通过 | P0 估时 0.5～1d；修复为 **全局 behavior fix**；policy 与 codegen **同 PR** |
| **测试** | ⚠️ 有条件通过 | 需 loader 集成测 + re-curate before/after metrics；全量 `test_mosaic_*` |
| **产品** | ✅ 通过 | 修复 ≠ 回到 linzhi 旧版式；需 Release Note 分相册类型预期 |
| **综合** | **有条件通过 → 采纳 Must 项后可进入 P0 开发** | — |

### 3.2 决策 D1～D18（v0.1.0 建议 + 评审修订）

| # | 决策项 | 结论 | 来源 |
|---|--------|------|------|
| **D1** | 空 `mosaic:` 缺段时的窗宽默认 | **`MosaicConfig()` dataclass**；禁止 inline `[5]`；**仅改 `sizes_raw` 一行** | v0.1 + A-05 |
| **D2** | `config.yaml.example` 窗宽 | 维持 **`[4, 5, 6, 9]`** | v0.1 |
| **D3** | 默认启用 8 窗 | **否**（P21；legacy defer 保留） | v0.1 |
| **D4** | `hero-3-2-plus-4` 注册 | **写入 MOSAIC_5** + `lte_export_legacy --sync-python`；**并入 P0 同 PR** | v0.1 + 评审 |
| **D5** | deprecated 4 SKU | **不复活**；Release Note 单列「仍不会出现的历史版式」 | v0.1 + P-01 |
| **D6** | 全量 re-curate | **否**；仅新 curate / replan | v0.1 |
| **D7** | P0-b 交付物 | **`PHASE15-ROLLOUT.md` onboarding 清单**，不提交 `config.yaml` | D-01 |
| **D8** | PR 性质 | 标注 **behavior fix**（无 mosaic 段环境全局变更） | D-02 |
| **D9** | AC-MCR-05 | 附 **before/after `layoutMetrics`** 记录（非 Gate 数值，留档） | T-01 |
| **D10** | AC-MCR-02 | export 后 **`git diff` clean** 或现有 parity 测 | T-03 |
| **D11** | 4 窗恢复副作用 | 接受 `landscape-4` 等与 5/6 窗竞争；**诊断记录 4 窗 exposure**（非 Gate） | A-02 |
| **D12** | 9 窗恢复 | 接受 re-entry MCS；监控 **`dense_collage_count`** | A-03 |
| **D13** | 竖图负例 | `demo-80301df45c` **允许零 mosaic**；FAQ + 未来 Studio 链到 diag | P-04 + AC-MCR-06 |
| **D14** | 启动 log | P2 optional；**非**每次 load 噪声（`--verbose` 或首次 curate） | D-06 |
| **D15** | P1 diag | **`exit 1`** 当 window 6 disabled | T-05 |
| **D16** | CI | P0 merge 前 **`pytest tests/test_mosaic_*.py -q`** 全绿 | T-06 |
| **D17** | URO 顺序 | **MCR P0 先于** URO `enabled=true` | 铁律⑤ |
| **D18** | 排版预期 | 见 §10.2～§10.4；**不承诺** deprecated SKU 视觉回归 | 产品 |

### 3.3 评审 Must / Should / Could

| 优先级 | 项 |
|--------|-----|
| **Must** | D1 修复 + loader 集成单测（G-MCR-02） |
| **Must** | D4 policy + codegen 同 PR（G-MCR-04） |
| **Must** | D7 onboarding 文档（G-MCR-03） |
| **Must** | D9 before/after metrics（G-MCR-06） |
| **Should** | D15 诊断脚本 + exit code（G-MCR-05） |
| **Should** | D5 Release Note |
| **Could** | D11 4 窗 exposure 诊断；D14 启动 INFO |
| **Won't** | deprecated SKU 复活 |

---

## 4. 现状快照（审计基线 · 2026-07-04）

### 4.1 配置层（L1）

| 来源 | `enabled_window_sizes` | 6 窗 |
|------|------------------------|------|
| `MosaicConfig` dataclass 默认 | `(4, 5, 6, 9)` | ✅ |
| `config.yaml.example` | `[4, 5, 6, 9]` | ✅ |
| **`mosaic_from_dict({})` 实际** | **`(5,)`** | ❌ **Bug** |
| 当前本地 `config.yaml`（无 mosaic 段） | `(5,)` | ❌ |

### 4.2 策略注册层（L2）· `mosaic_unified_groups`

| 窗族 | 正式成员 | 备注 |
|------|----------|------|
| MOSAIC_5 | `main-portrait-3land` | 仅 1 个；**缺** `hero-3-2-plus-4`（D4 修复） |
| MOSAIC_6 | `main-hero-plus-4`, `main-hero-plus-5`, `portrait-6`, `landscape-6` | 6 窗恢复后生效 |
| 活跃 orphan | `hero-3-2-plus-4` | extras 兜底；D4 后消除 |
| deprecated（不进 MCS） | `2p3l-equal`, `2portrait-3land-balanced`, `3portrait-2land-balanced`, `main-landscape-2portrait-2land` | status=deprecated |

### 4.3 运行时禁用矩阵（bug 态 · 修复前）

| patternId | slots | `mosaic_pattern_disabled` |
|-----------|-------|---------------------------|
| mosaic-5-main-portrait-3land | 5 | false |
| mosaic-5-hero-3-2-plus-4 | 5 | false |
| mosaic-5-main-hero-plus-4 | 6 | **true** |
| mosaic-6-main-hero-plus-5 | 6 | **true** |
| portrait-6 / landscape-6 | 6 | **true** |
| landscape-4 / portrait-4 等 | 4 | **true** |
| landscape-9 / portrait-9 | 9 | **true** |

---

## 5. 功能规格

### 5.1 P0-a · 修复配置加载默认值（代码）

**文件**：`travelogue/config/mosaic.py` · `mosaic_from_dict`

**现状**：

```python
sizes_raw = raw.get("enabled_window_sizes", raw.get("enabledWindowSizes", [5]))
```

**目标**：

```python
defaults = MosaicConfig()
sizes_raw = raw.get("enabled_window_sizes", raw.get("enabledWindowSizes", defaults.enabled_window_sizes))
```

**规则**：

- 当 `raw` 为空 `{}` 或缺少 `enabled_window_sizes` 键时，未显式字段回退 `MosaicConfig()`（**`density_budget` 等已正确，勿动**）。
- **禁止**在任何代码路径硬编码 `[5]` 作为「空配置」窗宽。
- PR 描述须标注 **behavior fix**（D8）。

**测试**：`tests/test_mosaic_config_defaults.py`（新增）

- `test_empty_dict_matches_dataclass_defaults`
- `test_partial_dict_merges_defaults`
- `test_load_config_without_mosaic_section`（集成：`load_config` 无 mosaic 段时窗宽 = dataclass）

**回归**：`pytest tests/test_mosaic_*.py -q`（D16）

### 5.2 P0-b · Onboarding 与文档（非 config 提交）

**交付物**（**非** git 跟踪的 `config.yaml`）：

| 文件 | 内容 |
|------|------|
| `PHASE15-ROLLOUT.md` | 新 clone 检查清单：确认 `mosaic:` 或依赖 P0-a 修复后 dataclass 默认 |
| `config.yaml.example` | 核对完整（已具备，无需改） |

**开发者本地**：可按 example 自行追加 `mosaic:` 段；修复 P0-a 后 **即使缺段** 行为亦正确。

**可选 P2（D14）**：`load_config` 在 `--verbose` 或首次 curate 时 INFO「using MosaicConfig defaults」。

### 5.3 P0-c · 策略注册同步（policy + codegen · 同 PR 硬门禁）

**文件**：`travelogue/layout_templates/lte_policy.yaml`

```yaml
  MOSAIC_5_PATTERN_IDS:
    - screen-mosaic-5-main-portrait-3land
    - screen-mosaic-5-hero-3-2-plus-4   # MCR · D4 · 行为等价，消除 orphan
```

**同 PR 必须执行**：

```bash
python scripts/lte_export_legacy.py --sync-python
pytest tests/test_lte_p0_p1_p2_closure.py tests/test_mosaic_*.py -q
git diff --exit-code travelogue/curation/mosaic/_legacy_generated.py
```

**约束**：顺序 `main-portrait-3land` 在前；extras 兜底保留但 **不应再依赖** hero-3-2。

### 5.4 P1 · 诊断工具

**新增**：`scripts/mosaic_config_diag.py`

**能力**：

- 打印 `enabled_window_sizes`、各窗 `mosaic_pattern_disabled`、policy MOSAIC_* 成员、deprecated 列表
- `--trip trips/foo`：统计 1P+4L 窗口、连拍失败数等
- **`--strict`** 或默认：**exit 1** 当 window 6 disabled（D15）
- 可选 `--compare-baseline path.json`：对比两次 curate 的 layoutMetrics（D9）

### 5.5 P2 · 文档与 usage 一致性

| 项 | 动作 |
|----|------|
| MCR-P-07 | `GUIDE-PHASE16-layout-template-engine.md` 增补「三层 mosaic 含义」 |
| MCR-P-06 | `check_usage_consistency.py`；mosaic 族 summary 修正（独立小 PR） |
| Release Note | §10.4 模板 |

---

## 6. 验收标准

### 6.1 自动化（Gate）

| AC | 描述 | 命令 |
|----|------|------|
| **AC-MCR-01** | 空 dict 默认窗宽 = dataclass | `pytest tests/test_mosaic_config_defaults.py -q` |
| **AC-MCR-02** | policy 与 generated 一致 | export sync 后 `git diff` clean 或 parity 测 |
| **AC-MCR-03** | 无回归 URO baseline | `pytest tests/test_usage_rules_baseline.py -q` |
| **AC-MCR-04** | MCS 6 窗候选可生成 | `pytest tests/test_mosaic_density_budget.py tests/test_mosaic_compose_deterministic.py tests/test_mosaic_hook_probe.py -q` |
| **AC-MCR-09** | 全量 mosaic 测回归 | `pytest tests/test_mosaic_*.py -q` |

### 6.2 行为验收（手动 / 脚本）

| AC | 场景 | 通过条件 |
|----|------|----------|
| **AC-MCR-05** | `chuanzang-studio` re-curate | ≥1 hero mosaic 屏；**附 before/after `layoutMetrics` JSON**（D9） |
| **AC-MCR-06** | `demo-80301df45c` re-curate | **允许**仍无 mosaic；diag 解释 fail_time / 竖图占比 |
| **AC-MCR-07** | `mosaic_config_diag --strict` | exit 0；`window 6 enabled: True` |
| **AC-MCR-08** | `mosaic.density_budget.enabled=false` | 回滚验证 P15 窗行为 |
| **AC-MCR-10** | 4 窗 exposure（诊断，非 Gate） | re-curate 后 decision log 可出现 4 窗 candidate（记录即可） |

**AC-MCR-05 执行约束（T-04）**：使用固定 `config.yaml.example` 副本或 pinned config snapshot，避免 aesthetic 漂移。

### 6.3 非验收（避免误判）

- 不要求所有 trip 一定含 5/6 槽拼图。
- 不要求 deprecated 模板重新出现。
- 不要求 URO on/off 盲评在本 PR 通过。
- 不要求 `layoutMetrics.dense_collage_count` 达到 P21 上限（仅监控方向）。

---

## 7. 实施计划

| 阶段 | 内容 | 估时 | 依赖 |
|------|------|------|------|
| **P0-a** | `mosaic_from_dict` + 单测 + loader 集成测 | 0.5d | — |
| **P0-b** | `PHASE15-ROLLOUT.md` onboarding | 0.25d | P0-a |
| **P0-c** | `lte_policy.yaml` + export sync（**同 PR**） | 0.5d | P0-a |
| **P0 验收** | AC-MCR-05/06/09 + metrics 留档 | 0.5d | P0-a～c |
| **P1** | `mosaic_config_diag.py` + strict exit | 0.5d | P0 |
| **P2** | usage summary + 指南 + Release Note | 1d | 可选 |

**PR 拆分（修订）**：

1. **PR-1（MCR P0）**：P0-a + P0-c + 测试 + AC-MCR-09 — **Must merge 独立**
2. **PR-2（MCR P0-b + P1）**：onboarding + diag — **Should 紧随其后**
3. **PR-3（MCR P2）**：文档 / usage / Release Note

---

## 8. 回滚

| 开关 | 效果 |
|------|------|
| `mosaic.enabled: false` | 整段回退 legacy planner |
| `mosaic.enabled_window_sizes: [5]` | 仅 5 窗（**不推荐**；临时 workaround） |
| `mosaic.density_budget.enabled: false` | P21 配额 off |
| Git revert PR-1 | 恢复 bug 行为（**禁止**作为长期方案） |

---

## 9. 风险与缓解

| 风险 | 缓解 |
|------|------|
| 恢复 6 窗后 dense 屏变多 | P21 配额仍生效；D12 监控 `layoutMetrics.dense_collage_count` |
| 恢复 4 窗与 5/6 窗竞争资产 | D11 诊断 4 窗 exposure；`window_order` 仍 5→4→6→9 |
| 恢复 9 窗大网格 | 九宫配额 + dense 预算；D12 |
| 全局 behavior fix 影响 CI/clone | D16 全量 `test_mosaic_*`；AC-MCR-01 集成测 |
| 与 URO enabled=true 叠加 | D17 MCR 先上；URO 单独 AC-URO-BLIND |
| policy/codegen drift | AC-MCR-02 进 CI |
| 用户期望 deprecated SKU 回归 | D5 Release Note §10.4 |
| 竖图用户「修了仍无拼图」 | D13 FAQ + diag + Studio 未来提示 |

---

## 10. 附录

### 10.1 相关代码索引

| 模块 | 路径 |
|------|------|
| 配置加载 | `travelogue/config/mosaic.py`, `loader.py`（含 `layout.mosaic_v2` 合并） |
| 窗宽 gate | `travelogue/curation/mosaic/runtime.py` · `mosaic_window_size_enabled` |
| pattern 禁用 | `travelogue/curation/mosaic/lte_adapter.py` · `mosaic_pattern_disabled` |
| 候选注册 | `travelogue/curation/mosaic/pattern_catalog.py` · `patterns_for_window_size` |
| Policy 源 | `travelogue/layout_templates/lte_policy.yaml` |
| Generated | `travelogue/curation/mosaic/_legacy_generated.py` |
| Dense 配额 | `travelogue/curation/screen_layout_state.py` · `dense_collage_limits_for_trip` |

### 10.2 修复前后对比（机制层）

| 维度 | bug 态（修复前） | 修复后 |
|------|----------------|--------|
| `enabled_window_sizes` | `(5,)` | `(4,5,6,9)` |
| 6 槽 hero mosaic 候选 | **不可能** | 有几何 + hero 时 **可能** |
| 4 槽 MCS（2×2 等） | **不可能** | **可能** |
| 9 槽 MCS | **不可能** | 受九宫配额 **可能** |
| 5 槽（main-portrait / hero-3-2） | 可能 | **基本不变** |
| deprecated 5 槽 composite | 不可能 | **仍不可能** |
| P21 dense 上限（164 张） | 理论 5 屏，实际难触达 | 上限仍 **5 屏**，更易触达 |
| 章内大拼图 | 0 | ≤ **1 屏/章** |

### 10.3 排版效果影响（评审共识 · 新 curate）

假设 P0+P1 完成，URO `enabled=false`，P21 默认开启。

#### 分相册类型

| 相册类型 | 代表 trip | 修复前 | 修复后（预期） | 用户体感 |
|----------|-----------|--------|----------------|----------|
| 横图为主 + 连拍 | chuanzang-studio、demo-318 | 偶有 5 槽；**无 6 槽 hero** | **1～3 屏** hero 拼图 | 杂志感 **明显恢复** |
| 横竖混合 | demo-2025-2 | 历史 curate 不均 | hero mosaic **可预期** | 拼图 **不再随机消失** |
| 竖图主导 | demo-80301df45c | portrait-1/2/3 | **仍几乎无 mosaic** | **非 bug**（D13） |
| 小册（&lt;50 张） | maomi | dense 上限 1 | 变化 **很小** | — |
| vs 历史 linzhi | linzhi 旧 HTML | 含 **2p3l-equal** | **不会出现** 2p3l-equal | 需 Release Note（D5） |

#### 定量估算（非 Gate）

| 指标 | bug 态 | 修复后（估算） |
|------|--------|----------------|
| 含任意 `screen-mosaic-*` 的 trip 占比 | ~10% | **~25～35%**（横图类） |
| 含 6 槽 hero mosaic 的 trip | **~0%** | **~10～15%**（≥100 张 landscape 主导） |
| 竖图主导 trip mosaic 曝光 | ~0% | **仍 ~0%** |

#### 版式结构示例（横图章）

```text
修复前：  landscape-1 → portrait-3 → full-frame → portrait-2 …
修复后：  landscape-1 → mosaic-6-hero-plus-5 → breath → portrait-3 …
          或 landscape-4 → mosaic-5-main-portrait-3land（连拍段）
```

**节奏**：P21 禁止连续 dense；不会满屏网格。  
**视觉**：恢复 hero + tile collage；**不**恢复 2p3l-equal 双竖旗舰。

#### URO 叠加展望（本 PR 不含）

日后 `usage_rules.enabled=true` 可能再过滤 hero mosaic，实际曝光 **略低于** MCR 修复态。

### 10.4 Release Note 要点（产品 · D5）

**标题建议**：拼图 MCS 配置恢复 — 横图游记 hero 拼图重新可用

**必须包含**：

1. 需 **重新 curate / replan** 才生效；旧 `index.html` 不变。
2. **仍不会出现**的历史版式：`2p3l-equal`、`3portrait-2land-balanced` 等 deprecated SKU。
3. 竖图为主相册可能 **仍无** 五/六张拼图 — 属内容门槛，非故障。
4. 横图为主相册预期出现 **主 hero + 配图** 拼图，密度受 P21 配额约束。

### 10.5 FAQ

**Q：为什么 LTE YAML 没有 `mosaic:` 字段？**  
A：拼图能力由 **项目级** `config.yaml` 的 `mosaic:` 与 **策略级** `lte_policy.yaml` 控制；模板只有 `usage`/`constraints`/`scoring`。

**Q：修复后为什么还是没有 2 竖 3 横那种拼图？**  
A：`screen-mosaic-5-2p3l-equal` 已 **deprecated**，不在 MCR 范围；需产品单独 IG。

**Q：需要和 URO 一起上线吗？**  
A：不需要；且 **MCR 应先于 URO enabled=true**（D17）。

**Q：修了 config 为什么儿童相册还是没有拼图？**  
A：见 AC-MCR-06 / §10.3 竖图主导行；运行 `mosaic_config_diag.py --trip ...` 查看连拍/配比原因。

---

## 11. 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1.0 | 2026-07-04 | 初稿：配置审计与 trip 实测 |
| v0.2.0 | 2026-07-04 | 合并算法/开发/测试/产品四方评审：D7～D18、Must 项、验收增补、§10.3 排版影响、Release Note |
