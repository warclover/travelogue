# Share-Face Closeout V1 · 合入准备（2026-07-18）

| 属性 | 内容 |
|------|------|
| **分支** | `feat/share-face-closeout-v1-w0` |
| **相对 master** | 含 W0+W1+W2 工程 + PRD/线框/AC/狗粮清单 |
| **GitHub Actions** | **不可用**（点数用尽）→ 以**本地 pytest / node --test** 为准 |
| **宣布主题完成** | **否**（AC-SFC-15 狗粮 N≥5 仍开） |

---

## 1. PRD 对照结论

### 必须项（挡工程合入）— 已齐

| 波次 | 项 | 状态 |
|------|----|------|
| W0 | 假句空槽 · 体面名 · vision_warmup · 降级 notice | ✅ |
| W1 | stale「分享图需更新」· Sparse G1 · FirstSuccess 无 Key · 章名禁「续」生成 | ✅ |
| W2 | 「媒资」→「照片类型」 | ✅ |
| Doc | 线框 F1–F5 · ACCEPTANCE · 相邻脚注 · OQ 关闭 | ✅ |

### 建议项 / 软缺口 — 不挡合入

| 项 | 状态 | 说明 |
|----|------|------|
| `sfc_stub_blanked` / `sfc_stale_label_impression` 发射 | ⏳ | 白名单已齐；发射可后续补 |
| 仓库内 demo-album 成片清洗物 | n/a | 生成路径已护栏；本地旧 trip 需重导 |
| 存量章名「×日续」JSON 迁移 | ⏳ | 生成器已禁；旧文件可能残留 |
| AC-SFC-NR-01/02 本主题重验 | ⏳ | SFC 未改 recipe/按章导出；风险低 |
| AC-SFC-15 真人狗粮 | ⏳ | **宣布完成**挡门，非 merge 挡门 |

### 合入前已补（本记录同期）

- BE `ALLOWED_STUDIO_HOMEPAGE_EVENTS` 补齐 `sfc_*`（此前 FE 打点会被 400）
- FE `resolveDisplayTitle` 与导入标题同源
- 「预览产物已过期」→ 人话「预览需更新…」

---

## 2. 本地验收命令（替代 CI）

```powershell
cd C:\Users\xiafe\Projects\travelogue
python -m pytest `
  tests/unit/domain/test_share_face_copy.py `
  tests/unit/domain/test_title_humanize.py `
  tests/unit/domain/test_stage_hints_sfc.py `
  tests/unit/domain/test_sparse_g1.py `
  tests/unit/curation/test_cluster_m14.py `
  tests/unit/web/test_sfc_w1_contracts.py `
  tests/unit/web/test_ftue_telemetry.py `
  tests/unit/web/test_ftue_w1_contracts.py `
  tests/unit/web/test_ftue_w2_contracts.py `
  tests/unit/web/test_help_onboarding_v1.py `
  tests/unit/web/test_studio_subprocess.py `
  -q

node --test `
  tests/js/title-humanize.test.mjs `
  tests/js/import-run-logic.test.mjs `
  tests/js/bento-preview-picker-logic.test.mjs
```

合入前建议再跑一轮（可选）：

```powershell
python -m pytest tests/unit/web -q --tb=line
```

---

## 3. 合入步骤建议

1. 确认工作区无无关噪声（`output-recipe*` / MCS PRD 勿带入）。
2. 本地命令绿。
3. 开 PR → **squash 或 merge commit 均可**；PR 正文注明 **CI skipped: Actions minutes exhausted · local suite green**。
4. Merge 后本地 smoke：Studio 导入脏名文件夹 + forceStub 示例抽检。
5. 狗粮清单另排场次，再宣布主题完成。
