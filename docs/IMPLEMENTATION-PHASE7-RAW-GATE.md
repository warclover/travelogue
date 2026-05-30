# Travelogue · Phase 7 RAW 拦截实施清单

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE7-RAW-GATE.md](./PRD-PHASE7-RAW-GATE.md) |
| **关联验收** | [ACCEPTANCE-PHASE7-RAW-GATE.md](./ACCEPTANCE-PHASE7-RAW-GATE.md) |
| **代号** | P7-RAW-GATE |
| **更新日期** | 2026-05-30 |

> **状态图例**：☑ 已落地 · ◑ 部分 · ☐ 未开始

---

## 1. 里程碑总览

| 里程碑 | 主题 | 对应 PRD | 完成标志 | 状态 |
|--------|------|----------|----------|------|
| **RG-M1** | 识别与拦截主逻辑 | §4 §6 | RAW-only / RAW+JPG 阻断通过 | ☑ |
| **RG-M2** | Studio/CLI 体验与错误码 | §5 | 提示文案与错误码一致 | ☑ |
| **RG-M3** | 测试、文档、灰度 | §8 §9 §11 | AC-RAW 全绿 | ☑ |

---

## 2. 任务拆分

### 2.1 RG-M1 · 识别与拦截

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| RG-T1 | RAW-T1 | 增加 RAW 后缀检测函数（统一小写比较） | `travelogue/media/ingest.py` | ☑ |
| RG-T2 | RAW-T1 | 在扫描阶段前置拦截并抛出 `E_INGEST_RAW_UNSUPPORTED` | `travelogue/media/ingest.py` | ☑ |
| RG-T3 | RAW-T2 | 新增配置：`ingest.reject_raw` | `travelogue/config.py` | ☑ |
| RG-T4 | RAW-T2 | 新增配置：`ingest.raw_blocklist_suffixes`、`ingest.raw_detect_sample_limit` | `travelogue/config.py` · `config.yaml.example` | ☑ |
| RG-T5 | §6.2 | 写入 `ingestStats.rawRejected*` telemetry | `travelogue/media/ingest.py` | ☑ |

### 2.2 RG-M2 · 交互与错误映射

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| RG-T6 | D-RAW-03 | Studio 捕获 `E_INGEST_RAW_UNSUPPORTED` 并弹窗 | `travelogue/web/studio_pipeline.py` | ☑ |
| RG-T7 | §5.1 | 统一弹窗文案（含“先转 JPG 再重试”） | `travelogue/web/*` 文案位置 | ☑ |
| RG-T8 | §5.2 | CLI 输出错误码+建议，`--verbose` 展示后缀统计与样例文件 | `travelogue/cli.py` | ☑ |

### 2.3 RG-M3 · 测试与文档

| 任务 ID | PRD | 任务 | 文件/模块 | 状态 |
|---------|-----|------|-----------|------|
| RG-T9 | RAW-T5 | RAW-only 测试（TC-RAW-01） | `tests/test_ingest_raw_gate.py` | ☑ |
| RG-T10 | RAW-T5 | RAW+JPG 混合阻断测试（TC-RAW-02） | `tests/test_ingest_raw_gate.py` | ☑ |
| RG-T11 | RAW-T5 | JPG-only 正常回归（TC-RAW-03） | `tests/test_ingest_raw_gate.py` | ☑ |
| RG-T12 | RAW-T5 | HEIC 不误伤（TC-RAW-04） | `tests/test_ingest_raw_gate.py` | ☑ |
| RG-T13 | RAW-T6 | 更新 FAQ/导入提示文档 | `docs/FAQ-RAW-IMPORT.md` | ☑ |

---

## 3. 建议执行顺序（1 周）

### Day 1-2

```
RG-T1~T5
```

### Day 3

```
RG-T6~T8
```

### Day 4-5

```
RG-T9~T13
```

---

## 4. 发布闸门（实施视角）

| 类别 | 必达项 |
|------|--------|
| 功能 | AC-RAW-01/02/03 |
| 回归 | AC-RAW-04 |
| 可观测 | AC-RAW-05 |

---

## 5. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：RAW 拦截专项任务拆分与节奏建议 |

