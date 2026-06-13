# Integration & Release Sprint · 任务清单

| 属性 | 内容 |
|------|------|
| **代号** | IRS-2026-06 |
| **制定** | 2026-06-13 · 项目负责人建议落地 |
| **原则** | **不增加新功能** · 收口 · 验证 · 还债 · 定规矩 |
| **周期** | 4 周（可按实际顺延，禁止并行开 Phase 23 / 新 LSE / 官网开发） |
| **关联** | [ACCEPTANCE.md](../ACCEPTANCE.md) · [PRD-PHASE22-storage-platform.md](../PRD-PHASE22-storage-platform.md) · [观感提升路线图.md](../观感提升路线图.md) · [IMPLEMENTATION-PHASE22.md](../IMPLEMENTATION-PHASE22.md) |

---

## 执行原则

1. **W1 优先真实验证** — 无 AC-07 反馈前，不启动官网与 Phase 23。
2. **文档 PR 与代码 PR 分离** — Phase 22 文档先入仓；实现走 `phase22/storage-platform` 分支。
3. **每项独立可验收** — 勾选前须附 acceptance-records 路径或命令输出。
4. **算法冻结** — 盲评基线建立前，禁止新 LSE capability / 新排版 Phase。

---

## 总览

| 波次 | 主题 | 出口标准 | 建议 Due |
|------|------|----------|----------|
| **W1** | 真实验证闭环 | 3 条 canonical trip 重跑 + AC-07 反馈 + 盲评基线 | 2026-06-20 |
| **W2** | 发布闸门与文档对齐 | ACCEPTANCE 升级 + 文档入仓 + OQ 闭环 | 2026-06-27 |
| **W3** | Phase 22 W1（写入边界 + 缓存） | ADR-008 Accepted + CacheRegistry + lint | 2026-07-04 |
| **W4** | Phase 22 W3 MVP（render-only 增量） | 改字后 render skip + timing 记录 | 2026-07-11 |

---

## W1 · 真实验证闭环

> **Top 1**：linzhi 长图发微信群，填 AC-07。

| ID | 任务 | Owner | Due | 状态 | 验收 |
|----|------|-------|-----|------|------|
| W1-01 | 拉齐 `master` 与 `origin/master`（推送 pending commit） | 工程 | 2026-06-14 | ☑ | 2026-06-13 push OK（remote up-to-date） |
| W1-02 | 用最新 `master` 全链路重跑 **linzhi** | 工程 | 2026-06-16 | ☑ | 2026-06-13 · ~177s · [linzhi.md](../acceptance-records/linzhi.md) |
| W1-03 | 全链路重跑 **maomi** | 工程 | 2026-06-16 | ◐ | smoke/validate OK · 全链路待 `D:\Photos\maomi` |
| W1-04 | 全链路重跑 **mao** | 工程 | 2026-06-16 | ☐ | 仓库无 `trips/mao/` · 跳过或新建 |
| W1-05 | 跑 `python scripts/quality_gate.py` + P5 smoke | 工程 | 2026-06-16 | ☑ | 2026-06-13 QUALITY GATE OK · e2e smoke OK |
| W1-06 | **AC-07** linzhi 长图发微信群（2× 按章 + 隐藏不准图注） | 产品/发起人 | 2026-06-18 | ☐ | linzhi.md §发群反馈已填 |
| W1-07 | 补齐 AC-03 / AC-05 / AC-06 手测 | 产品 | 2026-06-18 | ☐ | linzhi.md AC 表全 ☑ |
| W1-08 | 建立 **pairwise 盲评基线**（P21 前后或 master vs 上一 tag） | 产品/算法 | 2026-06-20 | ☐ | `acceptance-records/phase18-blind-baseline.json` |
| W1-09 | 盲评结论写入 acceptance-records；若不可感知 → 正式记录「算法冻结」 | 项目负责人 | 2026-06-20 | ☐ | 结论段 + 是否继续调参决策 |

**W1 命令参考：**

```powershell
cd C:\Users\xiafe\Projects\travelogue
python scripts/quality_gate.py
python scripts/e2e_studio_smoke.ps1
# 全链路示例（linzhi 源相册路径按本机调整）
python -m travelogue demo "D:\Photos\林芝" --trip-id linzhi --layout auto
python -m travelogue narrate linzhi
python -m travelogue render linzhi --dual
python -m travelogue export-longshot linzhi
python scripts/phase6_cover_blind_review.py --help
```

---

## W2 · 发布闸门与文档对齐

| ID | 任务 | Owner | Due | 状态 | 验收 |
|----|------|-------|-----|------|------|
| W2-01 | 升级 [ACCEPTANCE.md](../ACCEPTANCE.md)「当前发布闸门」 | 项目负责人 | 2026-06-22 | ☑ | v1.3 · P5+P6+P21 · 2026-06-13 |
| W2-02 | 同步 [docs/README.md](../README.md) 索引（Phase 18–22 · M21） | 文档 | 2026-06-22 | ☑ | 2026-06-13 |
| W2-03 | 提交 Phase 22 文档包（PR 仅 docs） | 工程 | 2026-06-23 | ☑ | commit 2026-06-13 |
| W2-04 | 闭环 OQ-DEMO-ASSETS（或砍 scope 并记录） | 设计/PM | 2026-06-23 | ☐ | [OPEN-QUESTIONS.md](../studio-homepage-v2/OPEN-QUESTIONS.md) → 🟢 |
| W2-05 | 闭环 OQ-TELEMETRY（或推期并记录） | 工程/SRE | 2026-06-23 | ☐ | RUNBOOK-DOGFOOD 可执行 |
| W2-06 | 归档根目录 untracked 截图 → `docs/wireframes/website/` 或 `.gitignore` | 工程 | 2026-06-24 | ☑ | 15 PNG + README · 2026-06-13 |
| W2-07 | 修复 `trips/linzhi` CRLF 假 dirty（`.gitattributes` 或 normalize） | 工程 | 2026-06-24 | ☑ | `.gitattributes` · 2026-06-13 |
| W2-08 | 梳理 stale 远程分支（phase16–21）归档或删除 | 工程 | 2026-06-27 | ☐ | 分支列表 + 决策记录 |

**明确不做（W2 门禁）：**

| 暂停项 | 直至 |
|--------|------|
| [PRD-WEBSITE-MARKETING.md](../PRD-WEBSITE-MARKETING.md) 开发 | W1-06 AC-07 有正面反馈 |
| 新 Phase / 新 LSE capability | W1-09 盲评基线 + 冻结决策 |

---

## W3 · Phase 22 Kickoff · W1（写入边界 + 缓存契约）

> 分支：`phase22/storage-platform` · 详见 [IMPLEMENTATION-PHASE22.md](../IMPLEMENTATION-PHASE22.md) P22-W1。

| ID | 任务 | Owner | Due | 状态 | 验收 |
|----|------|-------|-----|------|------|
| W3-01 | 开分支 `phase22/storage-platform` | 工程 | 2026-06-28 | ☐ | 自 master 切出 |
| W3-02 | ADR-008 → **Accepted** | 架构 | 2026-06-28 | ☐ | [adr/008-trip-storage-boundaries.md](../adr/008-trip-storage-boundaries.md) |
| W3-03 | P22-1b `scripts/lint_trip_json.py` trip 体积/字段 denylist | 工程 | 2026-06-30 | ☐ | CI 或 quality_gate 挂钩 |
| W3-04 | P22-1f–1j `CacheRegistry` + purge + tests | 工程 | 2026-07-02 | ☐ | `test_cache_registry.py` 全绿 |
| W3-05 | P22-1c–1e layoutDecisionLog dual-write / digest | 工程 | 2026-07-02 | ☐ | `test_layout_decision_log_migration.py` |
| W3-06 | P22-1h ingest invalidate hooks | 工程 | 2026-07-03 | ☐ | 重 ingest 后 cluster cache 失效 |
| W3-07 | P22-1i Studio delete → purge | 工程 | 2026-07-03 | ☐ | 删 trip 无 orphan 缓存 |
| W3-08 | W3 PR 合并 + quality_gate | 工程 | 2026-07-04 | ☐ | PR review + gate OK |

---

## W4 · Phase 22 · W3 MVP（render-only 增量）

| ID | 任务 | Owner | Due | 状态 | 验收 |
|----|------|-------|-----|------|------|
| W4-01 | P22-3a–3c `pipeline_fingerprint.py` + stage fingerprints | 工程 | 2026-07-07 | ☐ | fingerprint 单元测试 |
| W4-02 | P22-3d **render-only** incremental skip | 工程 | 2026-07-09 | ☐ | `test_pipeline_incremental.py` |
| W4-03 | P22-3e CLI `--incremental` / `--full` | 工程 | 2026-07-09 | ☐ | CLI-SPEC 同步 |
| W4-04 | P22-3f `RunTraceWriter` → `runs/run-{id}.json` | 工程 | 2026-07-10 | ☐ | 单次 run 可追溯 |
| W4-05 | P22-3i dogfood timing（linzhi 改一字前后） | 产品 | 2026-07-10 | ☐ | `acceptance-records/phase22-incremental-timing.json` |
| W4-06 | W4 PR 合并；更新 ACCEPTANCE-PHASE22 勾选 | 工程 | 2026-07-11 | ☐ | MVP G-P22-04 render-only ☑ |

**W4 成功口径（示例）：**

| 场景 | 期望 |
|------|------|
| linzhi 改 1 条 caption → render | 跳过 ingest/curate/narrate/CLIP；耗时显著低于全链 |
| Studio PATCH 冲突 | 409 + 前端 toast/reload（若 W3-2 revision 已合） |

---

## 延后队列（本 Sprint 不启动）

| ID | 任务 | 触发条件 |
|----|------|----------|
| DEF-01 | P2-5 `ingest.py` / `curate.py` 减负（ADR-010） | Phase 22 W1 合入 + 盲评基线稳定 2 周 |
| DEF-02 | Phase 22 W2 revision 乐观锁 + Studio 409 UX | W3 合入后 |
| DEF-03 | Phase 22 W4 Library 索引（SQLite） | render-only MVP 验证通过 |
| DEF-04 | 官网 landing（PRD-WEBSITE-MARKETING） | AC-07 正面 + exe/pip 下载路径就绪 |
| DEF-05 | Phase 18 BQP WS-1 选片升级 | 盲评基线 + 裁判流程跑通 2 轮 |

---

## 风险与升级

| 风险 | 信号 | 升级动作 |
|------|------|----------|
| AC-07 反馈负面 | 群友不愿转发 / 图注被吐槽 | 暂停 Phase 22；回到 G2 文案 + 选片，不开新 Phase |
| 盲评无差异 | P21 前后 pairwise ≈ 50/50 | W1-09 写「算法冻结」；DEF-01 前禁止 layout 改动 |
| Phase 22  scope 膨胀 | PR 含 narrate skip / PostgreSQL | 砍回 IMPLEMENTATION MVP 范围 |
| 文档 PR 阻塞 W3 | ADR-008 未 Accepted | W3-02 为 W3 编码硬门禁 |

---

## 进度汇总（手动更新）

| 波次 | 完成 / 总数 | 状态 |
|------|-------------|------|
| W1 | 3 / 9 | ◐ 全链路 linzhi ☑ · AC-07/盲评待人工 |
| W2 | 5 / 8 | ◐ 文档/卫生 ☑ · OQ/分支待办 |
| W3 | 0 / 8 | ☐ 未开始 |
| W4 | 0 / 6 | ☐ 未开始 |

**Sprint Done 定义：** W1 全 ☑ + W2-01/02/03 ☑ + W3-08 ☑ + W4-05/06 ☑。

---

## 变更日志

| 日期 | 变更 |
|------|------|
| 2026-06-13 | 初版 · 由项目负责人 4 周建议落地 |
| 2026-06-13 | W1-05/W2-01～03/06/07 执行 · linzhi/maomi smoke 重验 |
