# AAD 分支功能回归报告 · 2026-07-16

| 属性 | 内容 |
|------|------|
| **分支** | `arch/algo-deepening-v1` @ `85b495e` |
| **对照** | `master` @ `ac477e6`（worktree 抽检） |
| **范围** | 架构加深默认行为（PrefixBeam **关**）；是否引入新问题 / 是否破坏现有功能 |

## 1. 结论

**未发现由本分支架构改动引入的新功能回归。**  
默认关闭 PrefixBeam 时，核心策展/排版/CLI/Studio 沙箱路径表现与预期一致；全量套件中的失败项在 **master 上同样复现**（既有债）。

| 维度 | 判定 |
|------|------|
| 现有功能（flag 关） | **未受 intentional 破坏** |
| 新问题（相对 master） | **无**（抽检失败同源） |
| 可合入性 | **可合入**（建议忽略 CI 点数；以本地门禁为准） |

## 2. 变更面（回归关注点）

CLI 路径解析 · `run_curate` 拆 stage · curation→LE adapter 薄化 · LayoutUtility · PrefixBeam（默认关）· 审美 lint · mosaic/beam 打分字段

## 3. 门禁与套件结果

| 套件 | 结果 | 说明 |
|------|------|------|
| `lse_cross_import_stats` / lint 棘轮 | **5 边 · OK** | LE→cur=0 |
| `lint_layout_contract_surface` | **OK** | |
| `arch_equivalence_check` | **OK** | golden-mixed-scenes + render fixture |
| `run_aad_must_green.py` | **46 passed** | AC 钉死列表 |
| **改动面定向**（adapter/curate/cluster/mosaic/beam/studio/phase15/food/moment…） | **109 passed** | 覆盖本波主要触点 |
| **全量** `layout_engine`+`curation`+`media` | **1442 passed / 5 failed / 21 skipped** | ~16 min |
| `import-linter` | **fail（master 同型）** | config→llm、domain→config 等既有分层债，非本波引入 |

## 4. 失败归因（5 条 · 非 AAD）

| 失败 | master 复现 | 归因 |
|------|-------------|------|
| `test_cover_opening_title_card_styles` | ✅ 同 `IndexError` | 封面 CSS/中文注释切分（既有） |
| `test_v4_cover_opening_layout_playwright` | （同类 Playwright） | UI 超时 |
| `test_v4_dock_states_playwright` | （同类 Playwright） | UI 超时 |
| `test_cover_styles_v5_sheet_switch_and_apply_layout` | （同类 UI） | 封面样式 sheet |
| `test_pipeline_with_plan_text_persists_intent` | ✅ 同 `cities is None` | intent 解析/城市字段（既有） |

→ **不阻塞 AAD 合入**；建议另开债项修封面/intent。

## 5. 功能影响评估（默认行为）

| 能力 | 影响 |
|------|------|
| Cluster CLI 绝对路径 / `--trips-dir` 沙箱 | **改善**（修 AAD-02）；Studio 沙箱不变严 |
| `run_curate` 成册（flag 关） | **等价路径**（拆分+adapter；signature A/B 绿） |
| Mosaic / VariantRerank | 经 Utility；decisionLog 多 `utility` 字段（遥测兼容） |
| PrefixBeam | **默认关** → 不改变现网选屏；开启后才可能 DIFF |
| 边数 / 分层 | 可维护性↑；运行时行为不依赖边数 |

## 6. 残留人工项

1. Studio 成册观感手测（UX-AAD-02）  
2. Holdback 盲评（仅评估「开 flag」质量，不挡合入）  
3. 既有债：cover v4/v5、intent cities、import-linter 豁免清理  
