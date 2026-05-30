# Travelogue · Phase 7 RAW 拦截验收标准

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE7-RAW-GATE.md](./PRD-PHASE7-RAW-GATE.md) |
| **关联实施** | [IMPLEMENTATION-PHASE7-RAW-GATE.md](./IMPLEMENTATION-PHASE7-RAW-GATE.md) |
| **代号** | P7-RAW-GATE |
| **更新日期** | 2026-05-30 |

---

## 1. 验收环境

- Windows 10/11
- `pip install -e ".[dev]"`（HEIC 用例需 `pillow-heif`）
- 启动路径：
  - Studio：`python -m travelogue studio`
  - CLI：`python -m travelogue ...`

---

## 2. 核心验收项（AC-RAW）

| ID | 验收项 | 验收方法 | 通过条件 | 状态 |
|----|--------|----------|----------|------|
| **AC-RAW-01** | RAW-only 阻断 | TC-RAW-01 | 返回 `E_INGEST_RAW_UNSUPPORTED` | ☐ |
| **AC-RAW-02** | RAW+JPG 混合阻断 | TC-RAW-02 | 默认阻断，不进入后续阶段 | ☐ |
| **AC-RAW-03** | 用户提示明确可执行 | TC-RAW-01/02 | 文案包含“先转 JPG 后重试” | ☐ |
| **AC-RAW-04** | 非 RAW 主路径不受影响 | TC-RAW-03/04 | JPG/HEIC 行为与现有一致 | ☐ |
| **AC-RAW-05** | telemetry 完整 | 检查 ingestStats | rawRejectedCount/suffixes/sampleFiles 可读 | ☐ |

---

## 3. 测试用例

### TC-RAW-01 RAW-only

| 项 | 规格 |
|----|------|
| 输入 | 文件夹仅 RAW（例如 `.cr3/.nef` 共 20 张） |
| 步骤 | 触发 Studio 导入 / CLI ingest |
| 期望 | 立即阻断；错误码 `E_INGEST_RAW_UNSUPPORTED`；提示先转 JPG |

### TC-RAW-02 RAW + JPG 混合

| 项 | 规格 |
|----|------|
| 输入 | 10 张 RAW + 20 张 JPG |
| 步骤 | 导入同一文件夹 |
| 期望 | 默认阻断；提示展示 RAW 数量/样例文件/后缀 |

### TC-RAW-03 JPG-only 回归

| 项 | 规格 |
|----|------|
| 输入 | 50 张 JPG |
| 步骤 | 导入并完成主流程 |
| 期望 | 正常通过，不触发 RAW 错误 |

### TC-RAW-04 HEIC 不误伤

| 项 | 规格 |
|----|------|
| 输入 | 20 张 HEIC |
| 步骤 | 导入 |
| 期望 | 不触发 RAW 拦截（若缺 heif 依赖，走现有 HEIC 错误路径） |

---

## 4. 自动化建议

```powershell
python -m pytest tests/test_ingest_raw_gate.py -q
```

建议覆盖断言：
- 错误码
- 错误文案关键字
- telemetry 字段
- 非 RAW 回归

---

## 5. 失败判定与处置

| 失败条件 | 处置动作 |
|----------|----------|
| RAW 文件夹未被阻断 | 阻塞发布，修复后重测 |
| 提示文案缺失“先转 JPG” | 阻塞发布，更新文案 |
| JPG/HEIC 路径被误拦截 | 立即回滚 `ingest.reject_raw=false` 并修复 |
| telemetry 字段缺失 | 补齐统计与日志再放行 |

---

## 6. 签字页

| 角色 | 负责人 | 结论 | 日期 |
|------|--------|------|------|
| 产品负责人 |  | 通过 / 拒绝 |  |
| 工程负责人 |  | 通过 / 拒绝 |  |
| QA 负责人 |  | 通过 / 拒绝 |  |

---

## 7. 变更记录

| 日期 | 说明 |
|------|------|
| 2026-05-30 | 初稿：AC-RAW 与 TC-RAW 用例定义 |

