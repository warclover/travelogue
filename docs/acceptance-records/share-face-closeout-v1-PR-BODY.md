# PR · Share-Face Closeout V1 (W0–W2)

**Branch:** `feat/share-face-closeout-v1-w0` → `master`  
**Create URL:** https://github.com/warclover/travelogue/pull/new/feat/share-face-closeout-v1-w0

---

## Summary

- **W0**：stub 假句空槽、体面名（`--`/东澳岛回退）、`vision_warmup` 主句 + 注入可测锁、vision 降级人话 toast
- **W1**：stale 主词「分享图需更新」、Sparse 快速分享默认跳过 G1、FirstSuccess 无 Key 预期、章名禁「续」契约
- **W2**：「媒资」→「照片类型」；合入前补齐 BE `sfc_*` 埋点白名单与 FE `resolveDisplayTitle`

## Test plan

- [x] 本地 pytest（SFC 相关 domain/web 单测）**60 passed**
- [x] 本地 `node --test` title-humanize / import-run-logic / bento-picker **18 passed**
- [ ] **CI**：GitHub Actions 点数已用尽 — **本 PR 以本地套件为准**
- [ ] 手测狗粮 F1–F5：`docs/acceptance-records/share-face-closeout-v1-dogfood-CHECKLIST.md`
- [ ] Merge 后 smoke：脏文件夹名导入 + forceStub 分享面抽检

## Merge notes

- 合入准备：`docs/acceptance-records/share-face-closeout-v1-merge-ready-2026-07-18.md`
- **不**宣布主题完成（AC-SFC-15 仍开）
- 勿带入工作区噪声：`output-recipe*`、MCS/Collage PRD

## Soft gaps (non-blocking)

- `sfc_stub_blanked` / `sfc_stale_label_impression` 仅白名单未发射
- 存量 trip「×日续」无批量迁移（生成器已禁）

## Commits

1. `db7ffcb` feat W0
2. `2f80386` feat W1/W2
3. `46b0c69` fix merge gaps
