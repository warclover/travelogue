# MRS V1 · 狗粮 5 步验收清单（W2 出口）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-MEDIA-REFERENCE-STORAGE-V1.md](../PRD-MEDIA-REFERENCE-STORAGE-V1.md) v0.2.0 |
| **评审** | [media-reference-storage-v1-review-2026-07-15.md](./media-reference-storage-v1-review-2026-07-15.md) §8 |
| **分支** | `feature/media-reference-storage-v1` |
| **状态** | **待手测勾选**（自动化基线见下方） |
| **日期** | 2026-07-16 |

> 合入 `master` 前须本清单 **5/5 手测 ✅**，或登记豁免与复测日期。

---

## 自动化基线（CI / 本地）

```bash
python -m pytest \
  tests/unit/media/test_source_resolve_storage.py \
  tests/unit/export/test_export_no_absolute_paths.py \
  tests/unit/media/test_ingest_pending_assets.py \
  -q
```

| 覆盖 | 对应 AC |
|------|---------|
| 引用/复制 ingest、cleanup、remount、并行引用、incremental 码 | AC-MRS-02/02b/03–05/12–14 部分 |
| zip + 渲染产物无绝对路径 | AC-MRS-08′ |

---

## 手测 5 步（评审纪要 §8）

| # | 步骤 | 期望 | 结果 | 备注 |
|---|------|------|------|------|
| **1** | 默认「导入时复制源文件」= 开 → 导入本机相册 | 有 `trips/{id}/source/*.jpg`；资产有 `sourceRef`；预览可开 | ☐ | |
| **2** | 设置关复制 → **新**导入另一相册 | 无新增 `source/*.jpg`；有 `sourceRef`/`contentSig`；预览可开；步骤 1 的旧 trip `source/` **不动** | ☐ | 向导应出现引用说明 |
| **3** | 设置 → 清理磁盘 → 仅安全清理 | cache 降；`source/` 与预览 WebP 仍在；作品可开 | ☐ | |
| **4** | 引用 trip：移走/改名相册目录 → 点导出长图/分享 | Facade 阻断合同文案；主 CTA「重新指定相册目录」；「稍后」可关；选对目录后可继续。同名但字节变 → 不误关联 | ☐ | |
| **5** | 引用模式导出 zip，全文搜本机路径片段 | zip 内无 `trip.json`、无用户相册绝对路径；解压 HTML/JS 同 | ☐ | 可用步骤 2 的 trip |

---

## 抽查（非挡门，建议同次）

| 项 | 期望 | 结果 |
|----|------|------|
| 设置第三组「存储与磁盘」 | 可见；占用估算有数 | ☐ |
| 向导「更改存储设置」 | 打开设置并滚到存储组 | ☐ |
| 预览作品 storageMode 文字 | 已复制 / 引用 / 混合 | ☐ |
| 书架「磁盘占用较高」 | 仅超阈值出现；点击进设置 | ☐ / N/A |

---

## 签字

| 角色 | 姓名 | 日期 | 结论 |
|------|------|------|------|
| 手测 | | | Go / 豁免 / 打回 |
| 复核 | | | |

## 版本记录

| 日期 | 说明 |
|------|------|
| 2026-07-16 | 初稿：W2 出口狗粮清单 + 自动化基线命令 |
