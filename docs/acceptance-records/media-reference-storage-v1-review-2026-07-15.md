# PRD-MEDIA-REFERENCE-STORAGE-V1 · 跨职能评审纪要

| 属性 | 内容 |
|------|------|
| **文档** | [PRD-MEDIA-REFERENCE-STORAGE-V1.md](../PRD-MEDIA-REFERENCE-STORAGE-V1.md) |
| **评审版本** | **v0.1.0 Draft** |
| **日期** | 2026-07-15 |
| **结论** | **有条件通过（Conditional Go）** · **Must-Fix 已回写 [PRD v0.2.0](../PRD-MEDIA-REFERENCE-STORAGE-V1.md)** · **可 Kickoff W0**（W1 待 IMPLEMENTATION） |
| **跟进** | 2026-07-15：PRD v0.2.0 消化 BLK-01～12 + OQ 决议 |
| **参评角色** | 架构 · 开发 · 产品 · 算法/视觉管线 · 测试 |
| **评审方式** | 分席只读评审（对照 PRD + 现网代码 / ADR-008 / Phase22 / schema / ingest·reexport·CLIP·export） |
| **记录人** | 联合纪要（分席合成） |

---

## 1. 总评（一句话）

> **方向正确：默认拷贝 + 开关引用 + 一键清理，比一刀切方案 A 更可交付；阻塞不在愿景，而在合同未钉死与现网地基空白——schema 仍强制 `sourceFile`、并行 ingest 另有一条无条件写 `source/` 的路径、reexport/CLIP 解析合同分裂、默认 WebP 收窄夹带画质风险、清理与导出门面/设置容器未合流。修完 Must-Fix 后可开 W0→W1。**

---

## 2. 分席表决

| 席位 | 表决 | 一句话 |
|------|------|--------|
| **架构** | Conditional Go | 分期策略合理；schema / 并行 ingest / CacheRegistry / revision 未入合同则不可 Kickoff |
| **开发** | Conditional Go | 决策清晰，但零 config/schema/API 地基；并行二次解码与 incremental 重放是隐藏雷区 |
| **产品** | Conditional Go | 混合策略站得住；文案/字段自相矛盾、设置第三组与 DLLM 容器、导出阻断与 Facade 未合流 |
| **算法** | Conditional Go | 混合方向对；`sourceRef` 进 reexport/CLIP 前不得开工，否则静默降质 |
| **测试** | Conditional Go | AC 表可读；引用模式零覆盖 + schema/reexport 冲突会导致假绿 |

**汇总**：**五席一致 Conditional Go**。未回写 Must-Fix 前 **不批无条件 Go / 不标 Ready for Kickoff W1**。

---

## 3. 全场共识

1. **混合策略优于纯 A**：默认不惊吓、开关管「以后导入」、清理单独止血——四条铁律可裁决。  
2. **V1 不改「默认复制」**：保护 `F-ING-02` 与狗粮习惯；「默认仍膨胀」用占用可见性 + V1.1 引导，而非本波次硬切。  
3. **复制模式也应预写 `sourceRef`（OQ-MRS-01 → 是）**：否则深度清理后旧 trip 无法挂载，清理价值大打折扣。  
4. **默认收窄 `webp_widths` 不是纯省盘**：与 `render/context.py`、裁剪 `max(widths)`、长图画质耦合；须单独决策，不宜夹带。  
5. **双 ingest 路径必须同改**：串行 `ingest.py` + 并行 `ingest_worker`/`ingest_parallel`；只改一处会出现「开关形同虚设」。  
6. **引用失效必须可感知**：CLIP 静默 heuristic、reexport 硬抛旧码——均违反铁律 4。

---

## 4. Must-Fix（阻塞 Kickoff · 合入 v0.2）

| ID | 议题 | 来源席位 | 要求 |
|----|------|----------|------|
| **BLK-01** | **schema：`sourceFile` required 与引用模式冲突** | 架构 / 开发 / 测试 | §5 明确：`sourceFile` 是否移出 required、`sourceRef` `$def`、schema 版本策略、fixtures/`validate_trip` 同步；禁止「实施时再说」。 |
| **BLK-02** | **并行 ingest 全路径合同** | 架构 / 开发 | §6 必须点名 `ingest_worker.py` / `ingest_parallel.py`；`copy_source_files=false` 时禁止无条件 `save_jpeg`；解决主进程二次打开 `source/{id}.jpg` 做 mediaClass/美学的耦合（worker 回传特征或改读 `sourceRef`）。 |
| **BLK-03** | **incremental / pending-assets 重放** | 开发 | 引用模式下不得静默丢弃重放资产；写清读路径与失败码。 |
| **BLK-04** | **统一 Resolve 合同（D-MRS-09）** | 开发 / 算法 / 测试 | `reexport` 与 CLIP `_resolve_asset_path` 同一顺序：`source/` → `sourceRef` → 可观测失败（映射 `E_MEDIA_SOURCE_MISSING`）；禁止 CLIP 静默 heuristic 顶替而不提示。 |
| **BLK-05** | **默认 WebP 收窄单独拍板** | 产品 / 架构 / 算法 | 消解与铁律 1「默认与今日一致」的冲突：要么移出本 PRD 默认变更，要么正文声明为**第二默认变更点**并加画质 AC；同步 `_PREFERRED_SRC_WIDTHS` / 裁剪基准解耦结论。 |
| **BLK-06** | **清理写入治理** | 架构 | 深度清理写 trip 须声明 `bump_revision`、是否经 `TripService` CAS；与后台可取消任务的竞态写入矩阵一行。裁定：复用/补齐 `CacheRegistry`，还是本 PRD 临时扫描（避免第二套「唯一来源」）。 |
| **BLK-07** | **字段权威统一** | 产品 / 架构 | §4.2 `sourceMaterialized` vs §5.2 `media.storageMode` 二选一；`mixed` 深度清理粒度（trip 级 vs asset 级）钉死；ADR-008 白名单回写 `media.*` / `sourceRef`。 |
| **BLK-08** | **设置容器与导出门面合流** | 产品 | 「存储与磁盘」如何改 DLLM「两 Tab」契约、谁改、哪一波次；导出阻断 Modal 插入 Facade 优先级栈哪一层、主/次按钮与「稍后」逃生。 |
| **BLK-09** | **深度清理冻结文案 + Demo 例外 AC** | 产品 / 测试 | 二次确认唯一字符串；AC-MRS-09 可测；附录 B 回写 `F-ING-02a/b` 责任人与时机。 |
| **BLK-10** | **contentSig 挂载失败分级** | 算法 / 测试 | 区分「目录找不到」vs「同名但字节变了（云优化/转码）」；禁止无效重试死循环；挂载匹配性能预算（大相册进度）。 |
| **BLK-11** | **错误码与 zip 泄漏护栏** | 测试 / 架构 | `E_MEDIA_*` 进 ERROR-CODES（勿引用不存在的 `E_REEXPORT_SOURCE` 文档神话）；AC-MRS-08 对渲染产物全文搜绝对路径做自动化断言。 |
| **BLK-12** | **铁律 3 文案笔误** | 产品 | 「清理不可不可逆坑用户」订正为可读句。 |

---

## 5. Should-Fix（建议 v0.2 合入，不单独挡 Kickoff）

1. 占用超阈值时设置页/书架**非阻断角标**（V1 可见性，不全推 V1.1）。  
2. 安全清理分项展示：`.cluster-cache`（本地重算）vs 美学 MLLM cache（可能计费/更贵）。  
3. 清理后进聚类显示「正在重建场景缓存」；引用未挂载时提示降级评分。  
4. 多 trip 共享同一 albumRoot 的**批量 remount**（换盘场景）。  
5. 「引用 → 重新物化 source」反向故事（深度清理后悔路径）。  
6. SHARING 路径 B（HTML 完整游记）在 source 缺失时的独立判定一句。  
7. 书架徽标可 P1；trip 详情/设置内**纯文字存储模式**提前到 W1。  
8. 埋点 `storage_*` 尽早上线，服务 V1.1 默认策略数据。  
9. 桌面正式版隐藏「开发 scratch」清理项。  
10. 开发估时：W1≈11 PD、W2≈11 PD；W1a 先 `parallel_ingest=false` 验证再攻并行。

---

## 6. OQ 拍板汇总

| OQ | 决议 |
|----|------|
| **OQ-MRS-01** | **是** — 复制模式强制预写 `sourceRef`；§6.1「建议」改「必须」；存量尽力补写（路径可能已失效亦记录） |
| **OQ-MRS-02** | **暂缓默认勾选删大档** — 先解决 reexport/`sourceRef` 与渲染宽度耦合；与 D-MRS-04 档位收窄**分开决策**；若日后清理大档，仅删「高于当前有效配置且可验证可再生」的历史文件 |
| **OQ-MRS-03** | **书架徽标 P1**；W1 至少在设置/详情纯文字展示存储模式（含 mixed） |

**追加拍板（评审新增）**

| 项 | 决议 |
|----|------|
| 默认 `webp_widths` 收窄 | **不夹带进 W1 默认变更**（见 BLK-05）；W1 可保留配置能力，默认值变更单独立项或与画质 AC 同批 |
| 引用模式 `sourceFile` | 缺省为 **省略/`null`**（非空串）；schema 同步（BLK-01） |
| CLIP 高保真 prefer source | **必须接 `sourceRef`**；不得静默 heuristic（BLK-04） |

---

## 7. 分席要点摘要

### 7.1 架构

- CacheRegistry 未落地却被清理假设依赖 → 须裁定补齐或临时扫描。  
- 清理写 Document 未入 revision 矩阵。  
- F-ING-02 须拆判据，避免与 AC-MRS 两套口径。

### 7.2 开发

- 断言：`copy_source_files` / cleanup API / `sourceRef` **均不存在**；checkpoint 基于 `album_root` **已对齐**（正向）。  
- 雷区：并行二次解码、incremental 静默丢数、schema+ADR 双重约束被低估。  
- 切片：W1a 串行 → W1b 并行 → W1c 安全清理 → W2 remount/深度清理/导出阻断。

### 7.3 产品

- 导出阻断须合流 Facade；设置第三组须改 DLLM 合同。  
- mixed 透明度与「物化回来」故事缺口。  
- V1 保留默认拷贝 + 加强占用可见性；V1.1 用可跳过的存储偏好二选一，忌静默改默认。

### 7.4 算法

- reexport / CLIP 现网无 `sourceRef`；CLIP miss → heuristic 静默降质。  
- contentSig = size+MD5，对云优化/转码 100% miss。  
- 清 `.cluster-cache` → 下次 full refresh；须提示等待。

### 7.5 测试

- 引用模式零自动化；建议矩阵：模式×(ingest/reexport/export/清理/remount)。  
- 狗粮 5 步：基线复制 → 关开关新导入 → 安全清理 → 移相册导出阻断/挂载 → zip 搜绝对路径。  
- 路径/泄漏必须自动化；文案惊吓感必须手测。

---

## 8. 建议狗粮门禁（W2 出口 · 人手）

1. 默认开：导入后有 `source/`，预览正常。  
2. 关复制：新导入无 `source/*.jpg`，预览正常；旧 trip 不动。  
3. 安全清理：cache 降、作品仍可开。  
4. 移走引用相册 → 导出出现合同文案 → 重新指定目录可继续。  
5. zip/渲染产物无本机绝对路径。

---

## 9. 下一步

| 顺序 | 动作 | 责任建议 | 状态 |
|------|------|----------|------|
| 1 | PRD 回写 v0.2（消化 BLK-01～12 + OQ 决议） | 产品 + 架构 | ✅ v0.2.0 |
| 2 | 必要时补 ADR-008 附录或短 ADR（`sourceRef` / `media.*` Document 边界） | 架构 | 待办 · W0 |
| 3 | `IMPLEMENTATION-MEDIA-REFERENCE-STORAGE-V1.md`（含并行 ingest 技术小节） | 开发 | 待办 · W0 |
| 4 | `ACCEPTANCE.md` 拆 `F-ING-02a/b` + ERROR-CODES | 测试 + 产品 | 待办 · W0 |
| 5 | W0 线框：设置「存储与磁盘」+ 清理确认 + 导出阻断 + remount | 产品 / 交互 | 待办 · W0 |

---

## 附录 · 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| 本纪要 | 2026-07-15 | 五席首次评审 · Conditional Go |
| 跟进 | 2026-07-15 | Must-Fix 已回写 PRD v0.2.0 · 可 Kickoff W0 |
