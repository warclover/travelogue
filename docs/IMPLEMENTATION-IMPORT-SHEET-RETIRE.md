# Import Sheet 退役 · 清理任务清单

| 属性 | 内容 |
|------|------|
| **承接** | [IMPLEMENTATION-IMPORT-WIZARD-A1.md](./IMPLEMENTATION-IMPORT-WIZARD-A1.md) **IW-G-04** |
| **基线** | Wizard 为唯一导入入口；Sheet DOM/CSS/JS **已删除**；线框 **已归档** |
| **状态** | **Done · P0～P4** |
| **更新日期** | 2026-07-12 |

---

## 0. 目标

Wizard 为唯一导入 UI；旧 Bottom Sheet 物理删除并归档线框。

**不做（本单）**：方案 B、Lightbox、拖拽文件夹；`import_start.surface` 改名（另开单）。

---

## 1. 阶段

| 阶段 | 目标 | 出口 |
|------|------|------|
| **P0** | 测试/文档对齐默认 Wizard | ✅ |
| **P1** | DS-01 薄编排层 | ✅ |
| **P2** | 去掉 flag / AC-IW-11 | ✅ |
| **P3** | 物理删除 Sheet DOM/CSS/JS | ✅ |
| **P4** | 线框/PRD 归档 | ✅ |

---

## 2～4. 任务（摘要）

P0～P2 见历史版本。

### P3

| ID | 任务 | 状态 |
|----|------|------|
| RET-3a | 删除 `#v2-sheet-root` DOM + `import-sheet.css` + `import-sheet.js` / `import-flags.js` | ✅ |
| RET-3b | `import-entry.js` 直接加载 Wizard；`openImportSheet` 保留别名 | ✅ |
| RET-3c | F1-07/08 → Wizard；G8-08 → Wizard 模板 hint；DS-08 删除 | ✅ |

### P4

| ID | 任务 | 状态 |
|----|------|------|
| RET-4a | 线框归档至 `docs/archive/import-sheet/` + README 索引 | ✅ |

归档文件：

- `studio-import-sheet-v1.html`
- `studio-import-sheet-v2-dual-mode.html`
- `import-modal-compare-v1.html`

现行线框仍在 `docs/wireframes/`：`import-wizard-v3.html` · `import-wizard-a1.html`。

---

## 5. 铁律（仍有效）

- 开始制作出口：`startV2Import` / `startV2UploadImport`（`import-run.js`）
- `import_start.surface` 仍为 `v2_sheet`（埋点兼容；改名另开单）
- 生产 CTA 一律经 `import-entry.js` → Wizard

---

## 6. 版本历史

| 版本 | 说明 |
|------|------|
| **v1.0** | 承接 IW-G-04；P0～P4 拆解 |
| **v1.1** | P0 + P1 |
| **v1.2** | P2：移除 flag / AC-IW-11 |
| **v1.3** | P3：物理删除 Sheet；专测迁 Wizard |
| **v1.4** | P4：线框归档；清单 Done |
