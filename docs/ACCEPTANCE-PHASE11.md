# Travelogue · Phase 11 验收标准

| 属性 | 内容 |
|------|------|
| **关联 PRD** | [PRD-PHASE11-copy-optimization.md](./PRD-PHASE11-copy-optimization.md) v0.11.0 |
| **关联实施** | [IMPLEMENTATION-PHASE11.md](./IMPLEMENTATION-PHASE11.md) |
| **代号** | P11-LiteCopy |
| **更新日期** | 2026-06-02 |
| **状态** | Planned |

---

## 1. 验收环境

- `pip install -e ".[dev]"`；
- 启动方式：`python -m travelogue studio` 或 CLI narrate 路径；
- 验收 fixture：现有 trip fixture + 新增 P11 章节文案 fixture。

---

## 2. 功能验收（W1 · 必过）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P11-01** | 每章最多 1 条 `decorLine` 且长度 <=30 | `pytest tests/test_phase11_decor_line.py -v` |
| **AC-P11-02** | 低置信度可留空，不强凑句 | `pytest tests/test_phase11_decor_line.py::test_decor_line_allow_empty -v` |
| **AC-P11-03** | copy-toggle 与 photos-only 无回归 | `pytest tests/test_phase11_copy_toggle_regression.py -v` |
| **AC-P11-04** | 盲评样本中 ≥80% 判定“不喧宾夺主” | `docs/acceptance-records/phase11-copy.json` |
| **AC-P11-05** | 关闭开关后回退到 Phase 10 行为 | 配置切换 + 回归测试 |
| **AC-P11-06** | narrate/render/schema 回归全绿 | `pytest tests/test_narrate.py tests/test_validate.py -v` |

---

## 3. 意图锚点验收（W2 · 必过）

| ID | 条件 | 验证方式 |
|----|------|----------|
| **AC-P11-07** | 有 `copyIntent` 的章节，主观贴合度高于无锚点基线 | 离线评测脚本 + 盲评记录 |
| **AC-P11-08** | `mood/focus` 仅允许枚举值，`note<=30` | schema + validator 单测 |
| **AC-P11-09** | 意图输入为可选，不阻塞导出流程 | Studio 流程回归 |
| **AC-P11-10** | 用户编辑字段保护有效（edited 不被覆盖） | narrate 回归测试 |

---

## 4. 非回归（NR-P11）

| ID | 条件 |
|----|------|
| **NR-P11-01** | `hook/lead/caption/epilogue` 原有字段行为不退化 |
| **NR-P11-02** | `travelogue demo verify` 通过 |
| **NR-P11-03** | `decorLine/copyIntent` 缺失时兼容旧 trip（仅按空处理） |
| **NR-P11-04** | 纯照片模式仍隐藏全部文案（含 `decorLine`） |

---

## 5. 指标验收（W3 · 灰度）

| 指标 | 目标 |
|------|------|
| `decor_line_fill_rate` | 60%~85% |
| `decor_line_hide_rate` | 不高于现网基线 +10% |
| `decor_line_generic_warn` | 持续下降 |
| `decor_line_intent_adoption` | 持续提升（不设硬门槛） |
| `decor_line_intent_lift` | 正向提升 |

---

## 6. 建议验收命令

```bash
pytest tests/test_phase11_decor_line.py tests/test_phase11_copy_toggle_regression.py -v
pytest tests/test_narrate.py tests/test_validate.py tests/test_studio_server.py -v
python scripts/phase11_copy_acceptance.py --write docs/acceptance-records/phase11-copy.json
python -m travelogue demo verify
```

---

## 7. 发布闸门（G-P11）

满足以下条件方可从 Planned 进入灰度：

1. §2 AC-P11-01/02/03/05/06 通过；
2. §3 AC-P11-08/09/10 通过；
3. NR-P11-01~04 通过；
4. 盲评记录已写入 `docs/acceptance-records/phase11-copy.json`。

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.11.0 | 2026-06-02 | 初稿：P11 功能/意图锚点/灰度验收标准 |
