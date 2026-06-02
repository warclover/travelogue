# Phase 9 · 附录 E · Subject 桥接（Wave 3）

| 属性 | 内容 |
|------|------|
| **主文档** | [PRD-PHASE9.md](./PRD-PHASE9.md) |
| **代号** | P9-E |
| **解锁** | [PRD-PHASE10-food-grid.md](./PRD-PHASE10-food-grid.md) |
| **文档版本** | v0.9.1 |
| **更新** | 2026-06-02 |

---

## 1. 目的

`travelogue/curation/subject_tagging.py` 当前 **不读取** CLIP 写入的 `asset.subjectClass`，仅依赖 heuristic `tags` / `subjectBucket`。导致：

- Phase 3 vision 开启后信号 **未被排版消费**；
- Phase 10 food grid 计划中的 `is_mundane_clusterable()` 无法可靠识别 CLIP 标注的 `food`。

Wave 3 以 **最小 diff** 桥接，**不** 扩展 11 类 prompt（属 Phase 8）。

---

## 2. 范围

### In Scope

| ID | 内容 |
|----|------|
| **F-P9-E-01** | `subject_class_for_asset()` 读取优先级：`subjectClass` → `subjectBucket` → tags |
| **F-P9-E-02** | CLIP 8 类 → 4 桶映射（person / landscape / food / general） |
| **F-P9-E-03** | `subject_tags_for_asset()` 追加 `subjectClass` 镜像 tag（可选） |
| **F-P9-E-04** | pytest 覆盖 CLIP 字段优先于 tags |

### Out of Scope

- 扩展 `SUBJECT_CLASSES` 到 11 类（Phase 8）
- 修改 `clip_encoder.py` prompt
- food grid 组屏（Phase 10）

---

## 3. 读取优先级

```python
def subject_class_for_asset(asset: dict) -> str:
    # 1. CLIP / vision 写入（Phase 3 M13）
    clip = str(asset.get("subjectClass") or "").lower().strip()
    if clip:
        return _map_clip_to_bucket(clip)

    # 2. 既有 heuristic（tags · subjectBucket · faces）
    ...
```

### 3.1 CLIP 8 类 → 4 桶

| CLIP `subjectClass` | 桶 |
|---------------------|-----|
| person | person |
| landscape, architecture, street, temple | landscape |
| food | food |
| indoor, mixed | general |

**说明**：indoor/mixed 在 food grid 中 **不** 视为 mundane；Phase 10 可再细调。

### 3.2 置信度（可选 P1）

若 `subjectConfidence < 0.35`（字段存在时），**fallback** 到 heuristic 路径。

---

## 4. 与 Phase 3 约束

**G-P3-C05 单次 forward**：桥接 **只读** 已有 `subjectClass`，不增加 CLIP 调用。

**时序**：

```text
ingest → cull → clustering(CLIP write subjectClass) → curate(subject_tagging read)
```

若 cull 在 clustering **之前**，P1 cull 路由仍用 heuristic；clustering 后 `subjectClass` 供 **curate / Phase 10** 使用。  
**W3 验收**以 curate 路径为主，不强制 cull 必须用 CLIP。

---

## 5. 改动文件

| 文件 | 改动 |
|------|------|
| `travelogue/curation/subject_tagging.py` | 优先级 + `_map_clip_to_bucket()` |
| `tests/test_subject_tagging_bridge.py` | 新文件 |

**预估**：~40 LOC + 测试。

---

## 6. Phase 10 预备接口

Phase 10 将新增（不在 Wave 3 实现）：

```python
def is_mundane_clusterable(asset: dict) -> str | None:
    bucket = subject_class_for_asset(asset)
    if bucket == "food":
        return "food"
    # Phase 10 扩展: signage, ticket, ...
    return None
```

Wave 3 完成后，Phase 10 仅扩展 `is_mundane_clusterable` 与 tags 词表。

---

## 7. 验收

| ID | 条件 |
|----|------|
| **AC-P9-E-01** | `subjectClass=food` + 空 tags → bucket `food` |
| **AC-P9-E-02** | `subjectClass=person` 优先于 tags `landscape` |
| **AC-P9-E-03** | 无 subjectClass 时行为与现网 identical |
| **AC-P9-E-04** | 全 pytest 回归通过 |

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.9.1 | 2026-06-02 | 明确 W3 不依赖 cull ML |
| v0.9.0 | 2026-06-02 | 初稿 |
