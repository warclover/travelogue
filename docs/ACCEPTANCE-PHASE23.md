# Travelogue · Phase 23 验收标准

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE23-peak-moment.md](./PRD-PHASE23-peak-moment.md) v0.23.3 |
| **评审纪要** | [phase23-peak-moment-prd-review-2026-06-14.md](./acceptance-records/phase23-peak-moment-prd-review-2026-06-14.md) |
| **代号** | P23 · 最佳时刻（P23.1 池内 solo + EXIF） |
| **更新日期** | 2026-06-14 |

---

## 1. 验收环境

- Windows 10/11 · Chrome/Edge 最新稳定版
- `pip install -e ".[dev]"` · Playwright（渲染断言）
- 启动：`python -m travelogue studio` 或 `start-studio.bat`
- **Golden trips**：
  - `demo-d66fe642a9`（仙本那 · ≥20 张 · 风景为主）
  - 一册 ≤15 张小册 fixture
  - 一册 featured 精选导入 fixture
- 视口：**P0** 1440×960@2x（与 BSP 一致）

---

## 2. Tier 0 · 必过（阻塞发布）

| ID | 描述 | 步骤 | 通过 |
|----|------|------|------|
| **AC-P23-01** | 全册唯一签名屏 | curate → render web · `[data-role="moment"]` 计数 **= 1** · 无 `[data-block="moment-screen"]` | ☐ |
| **AC-P23-02** | 签名与封面互斥 | `momentAssetId` vs `coverAssetId` / `coverByLayout` | **不相等** |
| **AC-P23-02b** | 签名属于池 | `momentAssetId` ∈ `curation.momentPoolIds` | ☐ |
| **AC-P23-03** | EXIF 脚注形态 | 签名/池内屏 `.moment-exif-bar` 单行 · slot 内非 overlay 压图 | ☐ |
| **AC-P23-04** | 脚注字体 | computed `font-family` 含 mono 栈 · `font-size` ≤13px | ☐ |
| **AC-P23-05** | 签名角标 | 仅 `data-role="moment"` 屏含 `.layout-screen__moment-label`「决定性瞬间」 | ☐ |
| **AC-P23-06** | Reader 可见脚注 | `reader_immersive` · `.moment-exif-bar` visible（池内默认全显示） | ☐ |
| **AC-P23-07** | 正文无 EXIF | 非池内 `layout-screen` 无 `.moment-exif-bar` | ☐ |
| **AC-P23-08** | 字段落盘 | `momentPoolIds` + `momentAssetId` + `momentSecondaryIds`；`momentExplain` ≥1 | ☐ |
| **AC-P23-23** | 池大小公式 | 仙本那册 `len(momentPoolIds)` = clamp(round(n×5%),1,5) | ☐ |
| **AC-P23-24** | 签名唯一叙事锚点 | 仅 1 个 `data-role="moment"`；池内其余为 `data-role="peak"` | ☐ |
| **AC-P23-30** | 池内全员 EXIF（P23.1） | `pool_exif: true` 时 · `len(momentPoolIds)` 个 `.moment-exif-bar` · 仅 1 个 `data-role="moment"` | ☐ |
| **AC-P23-31** | performance 保留 solo | `performance` profile · 无 EXIF · 池内仍 `data-role` solo 屏 | ☐ |

---

## 3. Tier 1 · 质量门槛

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P23-09** | 三图位分离（仙本那） | `coverAssetId` · `momentAssetId` · closing 解析值 **三者互异** |
| **AC-P23-10** | 小册默认跳过 | ≤15 张 trip · 无 `momentPoolIds` · 无 `data-role="moment"` |
| **AC-P23-11** | EXIF 缺失降级 | 无相机 EXIF 的池内图仍 solo；无空占位脚注 · 无「undefined」 |
| **AC-P23-12** | 脚注段数门槛 | 有效段 &lt;2 时：隐藏 `.moment-exif-bar` |
| **AC-P23-13** | 人物安全 fit | moment/peak 人物图 · img 使用 `contain` 或 blur-fill · 人脸未裁切 |
| **AC-P23-14** | 动效预算 | moment/peak 屏 breath 抬升 ≤8px（Reader）· 屏缝 overlap ≤2px |
| **AC-P23-15** | ingest exif 子对象 | 含 EXIF 的 RAW/JPEG 样本 · `assets[].exif.model` 非空 |
| **AC-P23-21** | 脚注对比度 | `.moment-exif-bar` 黑底区 WCAG 3:1 |
| **AC-P23-22** | 竖图 moment | 竖图 fixture · `screen-portrait-1` · 人物 contain 安全 |

### 3.1 盲评（AC-P23-16 · M1/M2 分期）

| 项 | 规格 |
|----|------|
| **问句（冻结）** | 「这一张最能代表这趟旅行的决定性瞬间吗？」（是/否）— 仅评 **签名** `momentAssetId` |
| **池覆盖（M2）** | 用户心中 top-5 ∩ `momentPoolIds` ≥ **3** |
| **排序依据** | 盲评 B 类用池内 `peak_moment_score` 序；**不得**用 `momentCandidates` 多样性序 |
| **M1 样本** | ≥5 册 · 含仙本那 · ≥20 张/册 |
| **M1 通过** | 签名是率 ≥ **50%** |
| **M2 样本** | +3 册 hold-out（未参与调参） |
| **M2 通过** | 签名是率 ≥ **60%** 且池覆盖 ≥3/5 |
| **记录** | `docs/acceptance-records/phase23-moment-blind-review.json` |

---

## 4. Tier 2 · Studio / 运营

| ID | 描述 | 通过 |
|----|------|------|
| **AC-P23-17** | Studio 换图 | PATCH `momentAssetId` → 重渲染 · 页面更新 |
| **AC-P23-18** | 池条带展示 | Studio 可见 `momentPoolIds` 全池 + 签名标记 + `hasExif` + explain |
| **AC-P23-25** | secondary 加权 | **仅** `pool_solo: false` 时 peak 章 hero 优先命中 `momentSecondaryIds` |
| **AC-P23-19** | 配置关闭 | `curate.moment.enabled: false` → 无 moment/peak 屏 · 无报错 |
| **AC-P23-20** | closing 软避 | moment 与 closing 相同时 · `curation.momentCollision: closing` 写入 |

---

## 5. 自动化测试（CI）

| 测试文件 | 覆盖 |
|----------|------|
| `tests/test_peak_moment_scoring.py` | `build_moment_pool` · clamp · finalize peak solo · `effective_secondary_boost` |
| `tests/test_moment_render.py` | inline EXIF · 池内 role 分层 · performance solo · 配置回退 · 英文角标 |
| `tests/test_ingest_exif_camera.py` | `assets[].exif` 字段 |
| `tests/test_bsp_moment_playwright.py` | AC-P23-01/03/30/31 DOM 断言 |

---

## 6. 回归清单

- [ ] 封面盲评路径不受影响（`cover-selection-plan` AC 仍过）
- [ ] `cover-closing` epilogue 仍正常渲染
- [ ] `reader_immersive` 仍隐藏 `folio-plate-meta`
- [ ] longshot 导出体积无异常膨胀（moment/peak 屏 excluded）
- [ ] `validate_trip` 对旧 trip 无 moment 字段仍通过

---

## 7. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.23.3 | 2026-06-14 | P23.1：池内 solo + EXIF · AC 改 inline 契约 · AC-P23-30/31 |
| v0.23.2 | 2026-06-14 | 双层模型：pool/secondary AC · 池覆盖率盲评 |
| v0.23.1 | 2026-06-14 | 评审闭合：M1/M2 盲评分期 · AC-P23-21/22 |
| v0.23.0 | 2026-06-14 | 初版验收 · 对齐 PRD v0.23.0 |
