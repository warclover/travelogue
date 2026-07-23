# ACCEPTANCE · 周审计代码质量修复包 V1（CQA）

| 属性 | 内容 |
|------|------|
| **文档版本** | **v0.1.0** |
| **对应 PRD** | [PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./PRD-CODE-QUALITY-AUDIT-FIXPACK-V1.md) **v0.2** |
| **实施** | [IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md](./IMPLEMENTATION-CODE-QUALITY-AUDIT-FIXPACK-V1.md) |
| **评审** | [acceptance-records/code-quality-audit-fixpack-v1-review-2026-07-23.md](./acceptance-records/code-quality-audit-fixpack-v1-review-2026-07-23.md) · Conditional Go |
| **状态** | **Closed · M1～M3 已落地**（`fix/cqa-m1-hemostasis`） |
| **聚合门禁** | `python scripts/code_quality_audit_fixpack_gate.py`（CI PR required） |
| **更新日期** | 2026-07-23 |

> **用法**：结案以本表勾选为准。PRD §9 为合同源；本文件为执行勾选板。  
> **铁律**：无「理论上测得到」——每条须指向夹具或命令（见 IMPLEMENTATION §4）。

---

## 0. 里程碑出口

| 门 | 必须全绿 | 不等于 |
|----|----------|--------|
| **M0 Go** | ACCEPTANCE + IMPLEMENTATION 存在；PRD v0.2；字母决策已锁 | 已合任何修复码 |
| **M1 Go** | AC-CQA-01～12（含 10b） | 存量上传/force/MSA |
| **M2 Go** | AC-CQA-13～19、21 | 棘轮/聚合 gate |
| **M3 Go / Closed** | AC-CQA-20/22/23 + DOC-01/02 | 公网 IAM / 巨石全拆 |

---

## 1. AC 勾选

### 1.1 M1 · 止血

| ID | 断言 | 夹具 / 命令（钉死后勾） | 状态 |
|----|------|------------------------|------|
| **AC-CQA-01** | LAN 鉴权态下，未认证 `GET /` 响应体与非会话 Cookie **不含**完整管理 token | `tests/unit/web/test_cqa_lan_session.py` | ✅ |
| **AC-CQA-02** | bootstrap→HttpOnly+302；query token **不能**鉴权 API；cookie/header 会话可通 | `test_cqa_lan_session.py`（含 query/API 矩阵） | ✅ |
| **AC-CQA-03** | 两并发 ping 互不串扰；无模块级 `read_user_llm_secrets =` 残留 | ping 单测 + `lint_cqa_contract_grep.py` | ✅ |
| **AC-CQA-04** | `persist=true` + 写盘 `OSError` → 结构化码；`pingOk` 与 `persisted` 可分离 | 同上 | ✅ |
| **AC-CQA-05** | `mode=full` 且 keptN 超阈 → 必出整卷确认 | `longshot.js` + `needsFullExportConfirm` 逻辑 | ✅ |
| **AC-CQA-06** | 「改用按章」→ prefs.`mode`==`chapter` | `tests/js/cqa-export-chapter-contracts.test.mjs` | ✅ |
| **AC-CQA-07** | Escape → Promise settled；确定不双 apply | 同上（Escape / `settled` 守卫） | ✅ |
| **AC-CQA-08** | regen/confirm 终态 = `pollJobUntilDone` 同语义 | 同上 + drawers 源码契约 | ✅ |
| **AC-CQA-09** | job 失败 → 错误可见；可重试；无假成功 | 同上（catch 保持面板 / 无假「已保存」） | ✅ |
| **AC-CQA-10** | 同 trip 连续两次 on-demand：单执行流；asset 合并 | `tests/unit/media/test_derivatives_ondemand_cqa.py` | ✅ |
| **AC-CQA-10b** | on-demand 存活 ⇒ busy | `is_on_demand_alive_for_trip_id` + `is_trip_busy` | ✅ |
| **AC-CQA-11** | trip.json persist = replace | `_persist_trip_json` tmp+replace | ✅ |
| **AC-CQA-12** | 预置孤儿 shotGroup → SSG 重跑后无簇/视频字段清空 | `test_rerun_clears_orphan_shot_group_fields` | ✅ |

### 1.2 M2 · 存量安全 + 契约

| ID | 断言 | 夹具 / 命令 | 状态 |
|----|------|-------------|------|
| **AC-CQA-13** | 上传 `filename=trip.json` / `index.html` → 拒绝且原文件不变 | `tests/unit/export/test_cqa_longshot_upload.py` | ✅ |
| **AC-CQA-14** | 非图像魔数 → 拒绝不落盘 | 同上 | ✅ |
| **AC-CQA-15** | force 覆盖 **demo** → 失败 | `tests/unit/web/test_cqa_force_import_gate.py` | ✅ |
| **AC-CQA-16** | force 在 busy（**含 on-demand**）→ 409；盘不被 rmtree | 同上 | ✅ |
| **AC-CQA-17** | 仓库无 `trackOverrideByVariant` 写入路径 | `lint_cqa_contract_grep.py`（禁 `=` 赋值） | ✅ |
| **AC-CQA-18** | sheet/panel destroy 后无残留 `travelogue:llm-status` 监听 | `tests/js/cqa-llm-status-lifecycle.test.mjs` | ✅ |
| **AC-CQA-19** | 乱序分段齐套后 `current` 指新批次；字段 = QFX schema | `test_maybe_write_after_upload_unordered_segments_complete` | ✅ |
| **AC-CQA-21** | 并发 config PATCH → 完整合法 YAML，无截断 | `tests/unit/config/test_cqa_patch_config_atomic.py` | ✅ |

### 1.3 M3 · 防复发

| ID | 断言 | 夹具 / 命令 | 状态 |
|----|------|-------------|------|
| **AC-CQA-20** | 质量池每窗口 O(1) 构建；候选复用有测锁 | `tests/unit/layout_engine/test_cqa_quality_pool_hoist.py` | ✅ |
| **AC-CQA-22** | hook/longshot 超基线 → lint fail | `scripts/lint_cqa_god_module_ratchet.py` + baseline JSON | ✅ |
| **AC-CQA-23** | 聚合 gate 为 PR required；本包窄 AC 子集绿 | `.github/workflows/ci.yml` + `code_quality_audit_fixpack_gate.py` | ✅ |

### 1.4 结案 DOC

| ID | 断言 | 状态 |
|----|------|------|
| **AC-CQA-DOC-01** | MSA / SSG / DLLM / PDG / SFI / QFX 相关 Acceptance 已注记 CQA 决策 | ✅ |
| **AC-CQA-DOC-02** | IMPLEMENTATION 任务卡勾完；PRD → **Closed**；无平行 SSOT | ✅ |

---

## 2. QFX `longshot-current.json` 零分叉（AC-19 引用）

路径：`{trip_dir}/longshot-current.json`（与 QFX T-06 **同一 schema**，禁止增删必填键）：

```json
{
  "schemaVersion": 1,
  "batchId": "string",
  "createdAt": "ISO-8601",
  "kind": "whole | segmented",
  "files": ["相对 trip 根有序文件名"]
}
```

CQA 只改：**每次上传**在整批文件齐套时写入（不依赖「最后一段最后到达」）。

---

## 3. 负向 / 防假绿清单

| 项 | 要求 |
|----|------|
| LAN | 禁止只用 loopback 绿灯冒充 AC-01 |
| ping | 禁止「单线程顺序 ping 两次」冒充并发 |
| Job | 禁止 mock `regenerateStructure` 立即 resolve 冒充实终态 |
| force | 禁止只测「目录不存在」路径 |
| MSA | AC-17 = **无写入**（锁 B），不是「写了但测没读」 |
| current | 禁止第三套字段名（如 `exportId` 替代 `batchId`） |

---

## 4. 结案指针

- CQA **非长期 SSOT**。Closed 后：会话/ping 条款归 DLLM·Studio 安全面；SSG 清场归 [SSG](./PRD-SMART-SHOT-GROUPING-V1.md)；MSA 删字段归 [MSA](./PRD-MOSAIC-SLOT-ADAPTATION-V1.md)；force/busy 归 [PDG](./PRD-PREVIEW-DELETE-GUARD-V1.md)；current 触发补丁归 [QFX](./PRD-QUALITY-FIXPACK-V1.md) 已 Closed 合同旁注。  
- 门禁入口（M3）：`scripts/code_quality_audit_fixpack_gate.py`。

---

## 5. 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **v0.1.0** | 2026-07-23 | M0 建档：自 PRD v0.2 §9 同步；挂夹具列与防假绿 |
