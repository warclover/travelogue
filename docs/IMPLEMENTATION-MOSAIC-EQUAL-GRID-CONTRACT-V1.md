# IMPLEMENTATION · 等权拼图几何合同 V1（MEGC）

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./PRD-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) **v0.2.0** |
| **验收** | [ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md](./ACCEPTANCE-MOSAIC-EQUAL-GRID-CONTRACT-V1.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-03 |

> **列车**：M0 文档 ✅ → **PR-A (M1 CSS)** ✅ → **PR-B (M2 选型闸)** ✅ → **PR-B2（legacy/classic 自愈）** ✅ → **默认 on**（[决策 2026-08-03](./acceptance-records/megc-default-on-decision-2026-08-03.md)）→ **PR-C (M3)** 默认延期。  
> **紧急例外**：PR-A 可在父开关前以 `fix_stage_css` hotfix 合入（O-05 · 七席允许）。

---

## 0. M0 · 文档与边界

| 任务 | 状态 | 说明 |
|------|------|------|
| PRD / ACCEPTANCE / IMPL / 评审模板 | ✅ | |
| 七席评审纪要 · Conditional Go | ✅ | [2026-07-31](./acceptance-records/megc-equal-grid-contract-v1-review-2026-07-31.md) |
| PRD 回写 v0.2.0 | ✅ | D/O 锁定 · D-11 · M3 延期 |
| DOC-STATUS + README | ✅ | |

---

## 1. PR-A / M1 · 渲染舞台合同（优先）

### 1.1 代码触点

| 区域 | 路径 | 动作 |
|------|------|------|
| Web 屏 CSS | `templates/visual-journal/journal-screens.css` | 收窄/推翻 `--2x2/--3x2:has(contain)→rows:auto;height:auto` 对 **固定 16:9 舞台** pattern 的影响 |
| 布局同步 | trips 内 `journal-screens.css` 若为拷贝 | 按仓库惯例同步或单一源 |
| 纸色 contain | 已有 MSA BLK-06 | 复用，不另起底色方言 |

### 1.2 建议实现策略

1. **白名单固定舞台 pattern**（至少）：`screen-landscape-4`、`screen-portrait-2-landscape-2`、以及任何 `layout-screen--16x9` + `--2x2/--3x2` 且非 portrait-intrinsic 的屏。  
2. 对这些 pattern：**强制**  
   - grid：`align-items: stretch`；`height: 100%`；`grid-template-rows: repeat(N, 1fr)`  
   - screen：保持 `aspect-ratio: 16/9`（或 `--screen-aspect`）；`overflow: hidden` 仅裁预期内容，不得依赖「先撑破再裁」  
3. contain 槽：格内 letterbox + 纸色；**槽盒子仍填满格子**。  
4. **显式排除**：`screen-portrait-2`、`screen-portrait-3`、`screen-portrait-4`、`screen-landscape-2`、`screen-landscape-3`、`screen-mosaic-*`（后者已有保护，加回归即可）。

### 1.3 测试

| 测试 | 断言 |
|------|------|
| 单元或 Playwright | AC-MEGC-01 |
| 回归 | AC-MEGC-02 · AC-MEGC-03 |
| 锚点 | `demo-2019` `data-asset-ids="asset-086,asset-088,asset-089,asset-091"` 强制 contain 后测高 |

### 1.4 BLK-02 名单（PR-A 合码签字）

| 类别 | Pattern |
|------|---------|
| **INCLUDE（固定 16:9 · contain 不释舞台）** | `screen-landscape-4`、`screen-portrait-2-landscape-2` |
| **EXCLUDE（保持 intrinsic / 已有保护）** | `screen-portrait-2`、`screen-portrait-3`、`screen-portrait-4`、`screen-landscape-2`、`screen-landscape-3`、`screen-mosaic-*` |
| **CSS 手段** | 1) 从通用 `--2x2:has(contain)→rows:auto` 与 generic contain 槽规则中 `:not()` 排除 INCLUDE；2) INCLUDE 正写 stretch/`minmax(0,1fr)` + 格内 letterbox |

### 1.5 完成定义

- [x] CSS 合入（`templates/visual-journal/journal-screens.css` · MEGC PR-A）  
- [x] AC-01～03 守卫单测（`test_lte_css_sync` · MEGC）  
- [x] Playwright 几何断言 `demo-2019` ch-02 plate（086/088 contain）：`gridH ≤ stageH + 1px`  
- [x] demo-2019 实机截图收口（2026-08-03 · `deltaGrid=0` · [狗粮](./acceptance-records/megc-dogfood-2026-08-03.md)）  
- [ ] 无误伤竖拼/栈屏的视觉签字（可用截图 diff）

---

## 2. PR-B / M2 · 选型闸

### 2.1 代码触点

| 区域 | 路径（预期） | 动作 |
|------|----------------|------|
| 配置 | `travelogue/config/mosaic.py` | 增加 `EqualGridContractConfig`；挂 `MosaicConfig.equal_grid_contract` |
| Profile | 复用 `msa_profile.build_msa_profile` | 勿复制峰算法 |
| 闸 | `layout_engine/mosaic/megc_gate.py` | 纯函数：profile → decision |
| 打分/候选 | `scorer.py` soft mul · `candidates.py` 混向硬拒 | SUP-01/02 |
| 应用点 | compose 写 `megc*` 日志 | 读窗资产 → peak → 闸 |
| 日志 | `layout_engine/mosaic/log.py` | `megcEnabled` / `megcOutcome` / `megcLandPeak` / `megcPatternId` |
| 例配 | `docs/config-megc-dogfood.example.yaml` | 本机狗粮样例（默认勿开） |

### 2.2 算法要点

```text
if pattern not in MEGC.patterns: skip
profile = build_msa_profile(window)   # MSA parent OFF 仍可算峰（BLK-07）
if landPeak in allow_peaks: allow
elif landPeak == mixed and landMedianR >= allow_mixed_median_min: allow
elif mixed_orient (D-06): hard reject in candidates
elif mode == soft: score *= score_mul   # SUP-01 · 默认 0.62；禁止加法 penalty
elif mode == hard_reject: reject in candidates
on no alternative after hard reject: soft-reemit + megcGateFallback（SUP-03）
```

**挂点（SUP-MEGC-02）**

1. `candidates.py`：混向等权硬拒；`mode=hard_reject` 时纯横等权亦硬拒  
2. `scorer.py`：纯横等权 soft `score_mul`（hard 回退再 emit 时同样乘）  
3. **PR-B2** `legacy.py` / `append_legacy_window`：**以及**经典 `_plan_one_screen`（`_emit_landscape_grid_with_megc`）— 直构无 scorer → soft/`gate_penalize` 与 hard 一律 **拒发/降级**（L4→L3/L1）；电影峰 `gate_allow` 仍 emit 并 stamp `megc*`  
4. `builders._finalize_mosaic_screen`：MCS 路径 stamp `megcEnabled/Outcome/LandPeak`（不在此拒）

### 2.3 测试

| 测试 | 断言 |
|------|------|
| `test_megc_pr_b.py` | AC-04～08 |
| 合成窗 | 4×3:2 vs 4×16:9 |
| 混向 | 2L2P + 3:2 峰 |

### 2.4 完成定义

- [x] 配置 + 闸 + 日志  
- [x] AC-04～08 绿  
- [x] demo-2019 闸语义 + 16:9 放行狗粮（[2026-08-03](./acceptance-records/megc-dogfood-2026-08-03.md)）；**3:2 胜出率标定未闭环**（re-layout 大量 `plannerPath=legacy`）  
- [x] planner/legacy finalize 自愈挂 MEGC（PR-B2 · `should_block_legacy_equal_grid` · soft 亦拒发）  
- [x] 产品默认 on（[决策](./acceptance-records/megc-default-on-decision-2026-08-03.md) · `EqualGridContractConfig.enabled=True`）

---

## 3. PR-C / M3 · P-释 / P-函

### 3.1 P-释（优先若需要）

| 触点 | 动作 |
|------|------|
| render context | 等权 + 窄峰 + 开关 → 输出 `data-megc-release-stage` 或 class |
| CSS | 该标记下 `aspect-ratio: auto`；格 `--slot-aspect` ≈ \(r^*\) |
| trip JSON | 持久化 `layoutGeometry.megcReleaseStage` + 目标 AR，保证导出一致 |

### 3.2 P-函（备选）

| 触点 | 动作 |
|------|------|
| 外层舞台 | 16:9 盒 + 整页拼图 contain |
| whitespace | 计入与 MSA 相同预算字段 |

### 3.3 完成定义

- [ ] AC-09/09b 绿（启用的那条）  
- [ ] AC-10 盲评纪要  
- [ ] 默认 on 决策文档（可 hold）

---

## 4. 明确不做（实施禁令）

| 禁令 | 理由 |
|------|------|
| 给 `landscape-4` 写 `solve_track_override` 让四格变 1.50 | D-MEGC-00 |
| 新建「landscape-4-3x2」平行 YAML 应付单反 | N-02 |
| 放宽 `portrait_forbidden_in_wide_slots` | N-05 |
| 在 PR-A 夹带选型闸 | 列车纪律 |

---

## 5. 建议工时（粗估）

| PR | 粗估 |
|----|------|
| PR-A | 0.5～1.5 d（CSS + 回归） |
| PR-B | 2～4 d（配置 + 闸 + 测） |
| PR-C | 2～5 d（择一路径 + 导出对齐 + 盲评） |

---

## 6. 依赖

| 依赖 | 说明 |
|------|------|
| MSA profile API | 稳定复用；MSA 父 OFF 时 profile 仍应可只读计算（或 MEGC 内联调用同一函数） |
| MTSO/MCS 打分扩展点 | soft penalty 挂钩 |
| BLK-06 纸色 | contain 视觉 |
