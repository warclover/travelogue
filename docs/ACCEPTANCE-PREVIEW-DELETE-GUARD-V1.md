# Travelogue · 预览中删除护栏 V1 · 验收记录

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-PREVIEW-DELETE-GUARD-V1.md](./PRD-PREVIEW-DELETE-GUARD-V1.md) **v0.2** |
| **IMPLEMENTATION** | [IMPLEMENTATION-PREVIEW-DELETE-GUARD-V1.md](./IMPLEMENTATION-PREVIEW-DELETE-GUARD-V1.md) |
| **验收日** | 2026-07-23 |
| **状态** | **M1+M2+缺口补齐自动验收绿 · 主题可 Done（真机大图 WebP 可补签字）** |

---

## AC 签字栏

| ID | 标准摘要 | 验证 | 结果 |
|----|----------|------|------|
| **AC-PDG-01** | 预览中删除强确认：标题 + `当前首页预览` + `切回示例作品` | `test_ac_pdg_01_previewing_delete_strong_confirm` | ☑ |
| **AC-PDG-02** | 非预览通用文案；无 `切回示例` | `test_ac_pdg_02_non_preview_delete_generic_copy` | ☑ |
| **AC-PDG-03** | DELETE 调用瞬间 preference 空、select=`""`、demo-flag=2 | `test_ac_pdg_03_04_05_disconnect_before_delete`（延迟 DELETE + fetch 采样） | ☑ |
| **AC-PDG-04** | 成功 toast 含切回示例；摘卡；设置可点 | 同上 | ☑ |
| **AC-PDG-05** | `aria-busy` + DELETE 网络次数=1（防重入） | 同上 | ☑ |
| **AC-PDG-06a** | 409：示例保持、preference 空、卡片仍在 | `test_ac_pdg_06a_delete_409_keeps_demo` | ☑ |
| **AC-PDG-06b** | 500 + JSON message：展示该 message；示例态保持 | `test_ac_pdg_06b_delete_500_json_message` | ☑ |
| **AC-PDG-06c** | 500 非 JSON → toast「删除失败，请重试」 | `test_ac_pdg_06c_delete_500_empty_body` | ☑ |
| **AC-PDG-07** | on-demand 协调下删除不挂起（＜5s） | `test_ac_pdg_07_delete_joins_on_demand_barrier` + `test_ac_pdg_07_volume_many_files_delete_under_budget` | ☑ |
| **AC-PDG-08** | deleting 时静态 GET 404 | `test_delete_while_deleting_flag_blocks_static` | ☑ |
| **AC-PDG-08b** | 首页预览 + 独立页打开资源 → 删除后首页可交互；资源 404 | `test_ac_pdg_08b_preview_page_open_while_delete` | ☑ |
| **AC-PDG-09** | 冷启动：回示例 + storage null + pageerror=0 | `test_ac_d14_04_deleted_trip_fallback` | ☑ |
| **AC-PDG-10** | 热删后硬刷新仍示例；storage null；设置可点 | `test_ac_pdg_10_refresh_stays_demo` | ☑ |

---

## 后端套件

`tests/unit/web/test_studio_trip_delete.py`：**11 passed**（2026-07-23）

含：正常删除、demo 403、404、listed 名、busy 409、deleting 静态 404、rename 失败 `E_TRIP_DELETE_FAILED`、sweep 墓碑、列表隐藏 `_deleting-*`、on-demand barrier、多文件耗时。

## Playwright

`tests/e2e/test_studio_home_v2_ac_playwright.py -k "ac_pdg or ac_d14_04"`：**9 passed**（2026-07-23；含 01/02/03-05/06a/06b/06c/08b/09/10）

---

## 邻接回写

| 文档 | 状态 |
|------|------|
| Homepage v2 §6.8.4 热删除行 | ☑ |
| DATA-CONTRACT 热路径 / 204 语义 | ☑ |

---

## 残留

| 项 | 说明 |
|----|------|
| Windows 真机 ≥20 张多档 WebP | 假文件体积测已绿；真图签字可选补 |

---

## CQA 邻接回写（2026-07-23）

| 项 | 说明 |
|----|------|
| busy ⊇ on-demand | `JobStore.is_trip_busy` 含 on-demand 存活（AC-CQA-10b） |
| force 导入 | HTTP `force=true` 复用 `begin_trip_delete` + tombstone，禁裸 `rmtree`（AC-CQA-15/16） |
| 详情 | [ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./ACCEPTANCE-CODE-QUALITY-AUDIT-FIXPACK-V1.md) |
