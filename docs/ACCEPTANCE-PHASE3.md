# Travelogue · Phase 3 验收标准

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.3.5 |
| **权威 PRD** | [PRD-PHASE3.md](./PRD-PHASE3.md) v0.3.3 Kickoff |
| **完成定义** | AC-P3-C01～C09 + NR-P3-01/02/03 + UX-P3-01～07；M12-0 Go + M12 + M13 Done |
| **更新日期** | 2026-05-28 |

---

## 1. 验收原则

1. **用户旅程**：与 Phase 2 **相同**（选文件夹 → pipeline → preview → 长图）；**无**独立洞察屏、**无** Docker setup。  
2. **受测相册**：≥3 套 golden（见 `tests/fixtures/clustering/`）+ ≥1 次真实旅行（150–400 张，含 GPS）。  
3. **对比基线**：同一 trip、同一 config，**clustering off** 为 Phase 2 回归对照（**§3 NR-P3-01**）。  
4. **NR-P3-02**：每个 Phase 3 PR 合并前全量 pytest 0 失败（vision marker 可 CI optional）。  
5. **Kickoff**：**G4（M12-0 Go）未签字 → 不合并 M12 功能 PR**（PRD §13.0）。

---

## 2. 发布闸门（产品目标 ↔ PRD §2.1）

| ID | 标准 | 里程碑 | 通过 |
|----|------|--------|------|
| **AC-P3-C01** | 3 套有 GPS golden：geo segments 边界 **一致率 ≥70%** 或 matrix §3.5 签字 | M12 | ✅ [phase3-m12-0-spike.json](./acceptance-records/phase3-m12-0-spike.json) |
| **AC-P3-C02** | P3-Full：`subject_run_score` **≥** Phase 2 baseline（I-G2 不劣化） | M13 | ✅ `test_layout_golden.py` |
| **AC-P3-C03** | `time_inversion_rate` **≤** Phase 2 baseline | M13 | ✅ `test_layout_golden.py` · I-G1 |
| **AC-P3-C04** | `clustering.enabled=false` 双跑 **documented equivalent**（§3） | M12 | ✅ `test_clustering_regression.py` |
| **AC-P3-C05** | 400 张 CPU · P3-Full 聚类 **≤8 分钟** | M13 | ✅ [phase3-m13-bench.json](./acceptance-records/phase3-m13-bench.json) warm **40.3s** |
| **AC-P3-C06** | 无 GPS trip：正常成稿；`segmentMode=date_fallback` | M12 | ✅ `test_clustering_spike.py` · golden-no-gps |
| **AC-P3-C07** | curate 输出 **3–5 章**；8+ events 时合并正确 | M12 | ✅ I-G2 / layout golden |
| **AC-P3-C08** | 同 fixture 双跑：`curation.clustering` hash **一致** | M12 | ✅ `test_clustering_deterministic.py` |
| **AC-P3-C09** | P3-Full：`burst_integrity_violations` **≤ baseline**；`aspect_pattern_match_rate` ≥ baseline | **M13** | ✅ I-G2（CI fixture burst=0；本地 mao/linzhi 容差） |

---

## 3. NR-P3-01 · documented equivalent（PRD §12.1）

**配置**：`clustering.enabled=false`，`vision.enabled=false`（或 skip ClusteringLayer）。

### 3.1 必须一致

| 比较项 | 规则 |
|--------|------|
| `chapters[].assetIds` | 集合相等（顺序可比） |
| `screens[].assetIds` | per-chapter 屏序一致 |
| `time_inversion_rate` | ≤ Phase 2 baseline |
| `burst_integrity_violations` | 与 baseline 相同（通常为 0） |

### 3.2 允许差异（ignore）

| 字段 | 说明 |
|------|------|
| `curation.clustering` | absent 或空 |
| `asset.eventId` / `sceneClusterId` / `clusterSource` | 不写入 |
| `decision_log.json` | 可无或仅 `cluster_skip` |
| 章 title 文案 | 结构 ID 一致即可 |

### 3.3 验证

| 方式 | 命令 / 说明 |
|------|-------------|
| 自动化 | `pytest tests/test_clustering_regression.py -q` |
| Fixture | mao / maomi / linzhi（≥1 套 M12 必跑） |
| CLI（可选） | `python scripts/diff_curate.py golden-mixed-scenes --fixture` |

| ID | 标准 | 通过 |
|----|------|------|
| **NR-P3-01** | §3.1/3.2 满足 | ✅ `test_clustering_regression.py` |
| **NR-P3-02** | 全量 pytest 0 失败 | ✅ CI / 本地（`@vision` optional） |
| **NR-P3-03** | Phase 3 trip 在 clustering off 下可编辑、export-longshot | ✅ `test_phase3_serve_regression.py` |

---

## 4. 性能闸门

| ID | 标准 | 条件 | 通过 |
|----|------|------|------|
| **PF-P3-01** | P3-Lite geo_events | 400 张 | ≤ **60s** CPU | ✅ [phase3-m13-bench-geo.json](./acceptance-records/phase3-m13-bench-geo.json) |
| **PF-P3-02** | P3-Full CLIP+cluster | 400 张 · 模型已缓存 | ≤ **8 min** CPU | ✅ warm **40.3s** · clip |
| **PF-P3-03** | 端到端 pipeline | 含 P3-Full · 150 张 | 仍满足 **G-P2-01**（≤20min 含人工） | ✅ 合成 150 张 **154.7s** · [record](./acceptance-records/phase3-pf-p3-03-e2e.json) |
| **PF-P3-04** | Phase 2 基线不变 | clustering off | ingest→preview ≤ **3 min** stub | ✅ NR-P3-01 回归 |

---

## 5. 算法与数据（M12-0 / M12 / M12.5）

| ID | 标准 | 验证 | 里程碑 | 通过 |
|----|------|------|--------|------|
| **AL-P3-01** | [clustering-algorithm-matrix.md](./spikes/clustering-algorithm-matrix.md) **Go** | 产品/技术签字 | M12-0 | ✅ v0.4 |
| **AL-P3-02** | `curation.clustering` 写入且 validate L1 通过 | schema test | M12 | ✅ `test_trip_schema_clustering.py` |
| **AL-P3-03** | `asset.eventId` 与 segments 一致 | unit join test | M12 | ✅ `test_trip_schema_clustering.py` |
| **AL-P3-04** | vision extra 未装 → 降级 P3-Lite，不 crash | 干净 venv | M13 | ✅ `test_layout_golden.py` |
| **AL-P3-05** | 损坏 cache → 自动重算 | 删 `.cluster-cache` | M12 | ✅ `test_cluster_cache.py` + stageHint |
| **AL-P3-06** | 双跑确定性（SP-C05） | 同 fixture 两次 hash 一致 | M12 | ✅ `test_clustering_deterministic.py` |
| **AL-P3-07** | 增量 ingest 10%/30% cache 边界 | F-CLU-CACHE-02/03 | **M12.5** | ✅ [phase3-m12-5-cache.json](./acceptance-records/phase3-m12-5-cache.json) |
| **AL-P3-08** | `decision_log` 含 segment/merge/fallback（§9.6） | M12 必验 | M12 | ✅ `test_cluster_cache.py` |

---

## 6. 排版质量（M13 · 对齐智能排版 V2）

| ID | 标准 | 参考 | 通过 |
|----|------|------|------|
| **LY-P3-01** | mao / maomi / linzhi 黄金样本 **I-G1** 不劣化 | [智能排版V2.md](./智能排版V2.md) | ✅ 本地 optional · I-G2 report |
| **LY-P3-02** | 同上 **I-G2** subject_run 提升 | 同上 · **I-G2 报告模板** M13 交付 | ✅ [phase3-m13-ig2.json](./acceptance-records/phase3-m13-ig2.json) |
| **LY-P3-03** | `aspect_pattern_match_rate` ≥ 95% | PRD-LAYOUT | ✅ CI fixture · `test_layout_golden.py` |
| **LY-P3-04** | `sceneClusterMode: off` 回归 Phase 2 段内序 | config A/B | ✅ `test_layout_golden.py` |
| **LY-P3-05** | burst 完整性：连拍 **不可拆屏**（G-P3-C09） | 黄金样本 | ✅ I-G2 ≤ baseline |

---

## 7. Studio UX（无新页面 · PRD §6.4）

| ID | 标准 | 里程碑 | 通过 |
|----|------|--------|------|
| **UX-P3-01** | Job 仍为 **4 stage** | M12 | ✅ `test_studio_ux_p3.py` |
| **UX-P3-02** | ingest `stageHint` 符合 §6.4.2 | M12/M13 | ✅ pipeline + clustering hints |
| **UX-P3-03** | D′ 高级折叠 + **§9.5 config API** 持久化 | M12/M13 | ✅ `test_studio_config_p3.py` |
| **UX-P3-04** | vision/geo 降级 **无** 阻断模态 | M12/M13 | ✅ Toast · `test_studio_ux_p3.py` |
| **UX-P3-05** | T+30s 慢提示 | M12 | ✅ `studio.js` · `test_studio_ux_p3.py` |
| **UX-P3-06** | T+3min / T+8min 慢提示（P3-Full） | M13 | ✅ `studio.js` · `test_studio_ux_p3.py` |
| **UX-P3-07** | 预览 toolbar **无** 聚类新控件 | M13 | ✅ `test_studio_ux_p3.py` |
| **UX-P3-08** | vision 超时可选 Toast | M14 | ✅ |
| **UX-P3-09** | p3 slot **保持空** | M12 | ✅ |
| **UX-P3-10** | 「为什么这样分章」折叠 | M14 | ✅ |

---

## 8. 功能矩阵（PRD F-CLU-* 摘要）

| ID | 要点 | 里程碑 |
|----|------|--------|
| F-CLU-GEO-01～06 | geo_events 全链路 | M12 |
| F-CLU-SCE-01～07 | scene_clusters + cache + 单次 forward | M13 |
| F-CLU-CUR-01～05 | curate + decision_log + burst 优先级 | M12/M13 |
| F-CLU-CACHE-01～03 | 增量 ingest | **M12.5** |
| F-CLU-CACHE-04 | pendingAssets（locked-state 写入 + `cluster process-pending`） | **M14** |
| F-CLU-CACHE-05 | 损坏 cache 重算 | M12 |
| F-CLU-STU-01～10 | Studio §6.4 | M12/M13/M14 |

---

## 9. 里程碑增量

| 项 | M12-0 | M12 | M12.5 | M13 | M14 |
|----|-------|-----|-------|-----|-----|
| geo_events | golden | ship | — | — | — |
| curate §8.1 | 设计 | ship | — | tune | — |
| scene_clusters | 参数 | — | — | ship | — |
| vision extra | 选型 | stub | — | full | — |
| layout run_aware | — | — | — | ship | — |
| decision_log | — | ship | — | extend | — |
| incremental cache | 设计 | CACHE-05 | ship 01～03 | tune | CLI |
| Studio UX §6.4 | 设计 | hint+高级+API | — | 慢提示 | 分段说明 |
| NR-P3-01 pytest | — | ship | — | — | — |

---

## 10. 废止项（v0.2 不再验收）

- AC-P3-01～13（洞察屏、engines、preview 回流等）
- AC-M12-SETUP（setup-engines）
- G5 洞察入口 5 人测试

---

## 11. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.3.0 | 2026-05-28 | 原生 Curate 聚类验收 |
| v0.3.1 | 2026-05-28 | AC-P3-C08/C09、F-CLU-CACHE、decision_log M12 |
| v0.3.2 | 2026-05-28 | UX-P3-01～10、§6.4 对齐 |
| v0.3.3 | 2026-05-28 | **§3 NR-P3-01 等价表**、M12/M12.5 切割、C09→M13、Kickoff 闸门 |
| v0.3.4 | 2026-05-28 | schema clustering、I-G1/LY-P3 测试、400 bench geo、subjectClass 单次 forward |
| v0.3.5 | 2026-05-28 | UX-P3-01～07 测试、PF-P3-03 e2e、wireframe hint、diff-curate CLI |
