# PRD-STABLE-QUALITY-HARDENING-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-STABLE-QUALITY-HARDENING-V1.md](../PRD-STABLE-QUALITY-HARDENING-V1.md) |
| **评审版本** | v1.0.0-STABLE-QH |
| **日期** | 2026-07-15 |
| **结论** | **有条件通过** → **v1.1.0 已合入 BLK-01..08**（[PRD v1.1](../PRD-STABLE-QUALITY-HARDENING-V1.md) · Ready for Kickoff） |
| **参评角色** | 架构 · 开发 · 产品 · UI/UX · 用户体验 · 典型用户代表 |
| **评审方式** | 分席只读评审（对照产线代码 / 既有 PRD 真相源） |
| **v1.1 跟进** | 2026-07-15 已升 [PRD-STABLE-QUALITY-HARDENING-V1.md](../PRD-STABLE-QUALITY-HARDENING-V1.md) **v1.1.0**（§3 R-QH-* · §7 设计全文） |

---

## 1. 全场共识

1. **方向正确**：稳定期还债、零 intentional 新功能、假红与真用户损分层清楚；首发 **M1+M2** 再 **M3** 节奏合理。  
2. **真痛点对齐**：取消半成品、清点假进度、旁路上传静默丢偏好、schema 导致导出失败——六席均认为应优先。  
3. **Kickoff 三件事倾向一致**（详见 §6）：  
   - 文案合同 **采纳 L0 现行句**（不回滚）  
   - 取消策略 **A · 自动清理**（须带硬谓词）  
   - 用户词 **「长图可更新」唯一**（废除用户面「长图待更新」）  
4. **禁止混入**：LONGSHOT 2.0、LSE 上量、Phase22 全量、`expectedRevision` 进首发、章节命名全案、可打断长图导出运行时。  
5. **假红清完 ≠ 体验完成**：对外沟通须强调 **M3 才是信任止血**；不可只交 CI 绿。

---

## 2. 总体结论（分席）

| 席位 | 结论 | 一句话 |
|------|------|--------|
| **架构** | 有条件通过 | 归因对；schema 漏键 + featuredDetected 与 disk-intent 冲突 + 裸取消删除须进 v1.1 |
| **开发** | 有条件通过 | 可落地；M3/M4 估时偏乐观；取消无钩子、schema 须扫描补齐 |
| **产品** | 有条件通过 | 须正式 supersede Help/UX-Trust 合同；收紧 M4/M6 越界项 |
| **UI/UX** | 有条件通过 | 词表须含预览「已过期」；设置描述不可提 AI 却无入口；角标主 CTA 矩阵 |
| **用户体验** | 有条件通过 | 旁路 AC 须验成册结果；清点缺超时态；dogfood 不够用 |
| **典型用户** | 有条件支持 | 在意取消/假进度/导出；怕只刷绿灯、黑话漏到脸上 |

**汇总**：**有条件通过**。阻塞项已于 **2026-07-15** 合入 PRD **v1.1.0** → 可 Kickoff 开工（仍须勾选 PRD §12.2 开工门槛）。

---

## 3. 阻塞项（B0 · 必合入 v1.1）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **Schema 字段清单不完整** | 架构 / 开发 | 不以 PRD 五列表施工；用真实管线产物 + fixture **扫描**补齐。至少含：`meta.coverClosingStyle`、`curation.bookendsExplain` / `bookendsVersions` / `bookendsSoftWarnings` / `coverOrientationByLayout` / **`bookendsDegraded`** / **`closingUserPicked`**。`bookendsSoftWarnings` 锁结构化形状 `{code,message,layout}`，禁止含糊 `additionalProperties:true`。 |
| **BLK-02** | **`featuredDetected` 与 disk-intent 优先冲突** | 架构 / 开发 | 根因：`merge_pipeline_persist` 在 disk 已有 intent 时不覆盖 → apply 后只改内存 → sync 冲掉。v1.1 须写死：**intent flush / `folders` 深合并**策略，禁止「修一下 merge」空转。 |
| **BLK-03** | **取消策略拍板 + 硬谓词** | 全场 | **定案 A（自动清理）**。硬谓词：未达 **previewable**（须书面定义，建议：无法打开合法卷轴预览 / pipeline 未达可预览态）、无用户有效 PATCH、走既有 `purge_trip`（勿手搓 rmtree）、库索引 reconcile、并发写锁。确认框人话：「未完成草稿将删除」。 |
| **BLK-04** | **文案合同正式 supersede** | 产品 / UI | Help V1 FirstSuccess 副文案、UX-Trust F-TRU-HOME-02 设置描述，由本 PRD **正式修订 supersede**；禁止只改测。新句仍满足 Help：验货 + 『长图』、不推精修。 |
| **BLK-05** | **「长图可更新」全链路词表** | UI / 产品 / 用户 | 用户面废除「长图待更新」；**预览 Dock「长图已过期」改为同族主词**（副文可保留「内容有更新…」）；Help H3 跟齐。角标降噪矩阵可随 M4，但词表统一为 P0。 |
| **BLK-06** | **设置描述 vs AI 入口一致性** | UI / UX | `#v2-settings-desc` 提「AI 文案升级」则 Popover **须有入口**；否则改句不承诺 AI（候选：「导入与分析偏好；AI 文案可在能力卡中升级」）。禁止裸采纳现行句。 |
| **BLK-07** | **旁路上传 AC 升到结果可感知** | UX / 用户 / 开发 | 不止 FormData；成册后标题/模板/密度/地点与 Wizard 一致；至少一条 dogfood「精细 + 手动模板 + 自定义标题」。 |
| **BLK-08** | **清点态机补超时/降级** | UX | 不止成败；保留/恢复「照片较多，制作时将自动清点」类诚实态；AC 覆盖失败 **与** 超时。 |

---

## 4. 重要改进项（建议 v1.1 合入，不阻塞 Kickoff 纪要本身）

1. **M3 时间盒承诺**：假红清完后**下一合并窗必须含 M3**（QH-03/04/05），防只交绿测。  
2. **估时修正**：M0 → 0.5–1d；M3 → 3–4d；M4 瘦身（章节命名全案、真长图打断移出）。  
3. **QH-07**：本波仅 **诚实文案**「导出开始后无法取消」；可协作取消另立。  
4. **QH-13 / expectedRevision**：从 P1 主表移除，仅留归档债指针（Phase22/ADR-008）。  
5. **HELP / HTML 双源**：FirstSuccess 文案以 JS `HELP_COPY` 为 SSOT。  
6. **dogfood 扩写**：UX-QH-05～08（清点、取消不变量、stub 封面、慢安抚+a11y）。  
7. **实验项**：G1/beam 折叠；用户面去代号。  
8. **Bookends 文档**：§5.2 补漏列字段，避免再次漂移。  
9. **上传 temp 清理**：并入 QH-05。  
10. **CI flake**：F03/F04 marker 与 F15/F16 对齐；勿堵 PR 快测。

---

## 5. 建议后置（不进本 PRD 主交付）

- 长图 Job 真协作取消  
- 取消方案 B（未完成书架态 / 断点续跑）  
- 章节命名完整模板体系  
- `expectedRevision` / Windows CAS / CacheRegistry  
- 新 M4 全页线框（用扩展文案表 + 角标矩阵即可）  
- 观感路线图大杠杆（选片 / pairwise）  

---

## 6. Kickoff 三件事 · 投票汇总

| 决议 | 汇总 | 说明 |
|------|------|------|
| **文案合同采纳 L0 现行句** | **同意** | 六席一致；须走 BLK-04 正式 supersede |
| **取消 A vs B** | **同意 A（约束版）** | 架构反对「裸 A」；开发/产品/UX/用户赞成带硬谓词的 A |
| **「长图可更新」唯一用户词** | **同意** | UI 追加：预览「已过期」须同族化（BLK-05） |
| **首发 PR = M1+M2** | **同意** | 附加：下一窗必含 M3；BLK-01..03 进 v1.1 后才写 M1 代码 |

---

## 7. 分席要点摘录

### 架构
- Schema 半截货：`bookendsLock` 已有，explain/versions/closing 等仍缺。  
- `featuredDetected` 是 HTTP-owned intent 与「disk intent 永胜」的真张力。  
- 取消删目录无谓词 = 架构否决。

### 开发
- 上传旁路、清点假进度代码证据确凿。  
- 长图 cancel 仅查状态位，无打断 → 诚实文案优先。  
- 本地裸跑 `tests/unit/web` 仍吃 Playwright 噪音。

### 产品
- Help↔L0 双合同必须追认合法化，不能只改测。  
- 防「引擎/契约叙事」盖过可感知修复；M3 是用户价值主修复。

### UI/UX
- 设置「提 AI 无入口」比旧描述更伤信任。  
- 角标「二选一」过粗，要主 CTA 矩阵。  
- M4 不需新线框，需扩展文案表。

### 用户体验
- 静默失效必须用**结果态**验收。  
- 取消确认框须说清 A/B 真实后果。  
- Import Failed 与 FirstSuccess 同级 a11y。

### 典型用户代表
- 最在意：取消干净、清点别撒谎、导出别挂。  
- 怕：只刷绿灯；系统半成品话漏到封面；角标继续吵。  
- 听不懂但怕漏脸：schema、G1、beam、stub。

---

## 8. 下一步（执行顺序）

| 序 | 动作 | Owner 建议 |
|----|------|------------|
| 1 | 合入阻塞项 → **PRD v1.1** | 产品 + 架构 |
| 2 | Kickoff 纪要勾选 BLK-01..08 + 三决议 | 全员 |
| 3 | 开分支 `fix/stable-quality-hardening-v1`，PR1 = M1+M2 | 开发 |
| 4 | PR2 = M3（QH-03/04/05） | 开发 + UX 验收 |
| 5 | PR3 = 瘦身 M4 + dogfood 记录 | UI/UX + 用户代表 |

---

## 9. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-15 | 六席评审纪要初版；结论有条件通过 |
