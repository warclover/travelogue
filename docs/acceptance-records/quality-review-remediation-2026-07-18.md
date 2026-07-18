# 质量审查收口 · 2026-07-18（全部必修）

| 属性 | 内容 |
|------|------|
| **触发** | 当日合入（SFC + TPC W1–W4）后的代码质量审查 |
| **范围** | `a677620..HEAD` 生产代码（非纯 PRD 正文） |
| **纪律** | **全部修复**；不得只修 P1 或只写文档不改代码 |
| **PRD 回写** | [TPC v0.2.3 §12](../PRD-TEMPLATE-CONTRACT-V1.md) · [GCS v0.2.1 §12](../PRD-GENERATIVE-COLLAGE-SURFACES-V1.md) · [SFC v1.0.2 §12](../PRD-SHARE-FACE-CLOSEOUT-V1.md) |

## 必修清单

| 优先级 | ID | 条款 | 业主 PRD | 状态 |
|--------|-----|------|----------|------|
| P1 | AC-TPC-15 | 近景 `near_scene_clone` 硬门默认关；仅开关开时硬拒 | TPC §12.1 | ✅ |
| P1 | AC-SFC-13 | trip.json 忙锁回退不丢数据（bak/保留 tmp） | SFC §12.2 | ✅ |
| P1 | AC-GCS-09 | GPL 扫描覆盖**运行时依赖闭包** | GCS §12.1 | ✅ |
| P2 | AC-SFC-12 | displayTitle FE/BE 日期兜底同源 | SFC §12.1 | ✅ |
| P2 | AC-TPC-16 | `shadow_log` 仓库默认 `false` | TPC §12.2 | ✅ |
| P2 | AC-TPC-17 | debt merge 不得用 p50 伪造 corpus p95 | TPC §12.3 | ✅ |
| P2 | AC-TPC-18 | eligibility 归一化单点 | TPC §12.4 | ✅ |
| P2 | — | CAS revision：migrate 口径两端一致 | SFC §12.2 | ✅ |
| P2 | — | candidates 不依赖 scorer 私有 `_` 函数 | TPC §12.1 | ✅ |
| P3 | AC-GCS-11 | vendored 禁 MIP / `round_result=True` 硬失败 | GCS §12.2 | ✅ |
| P3 | AC-GCS-12 | bric 回退打 debug；poster PIL close | GCS §12.2 | ✅ |
| P3 | — | trip 原子写 `newline="\n"` 与回退一致 | SFC §12.2 | ✅ |
| P3 | — | 模板解析失败 warning；阈值入 config/常量 | TPC §12.5 | ✅ |

## 验证命令（收口后）

```bash
pytest tests/unit/layout_engine/test_near_scene_clone_penalty.py tests/unit/layout_engine/test_template_contract_*.py -q
pytest tests/unit/trip/test_trip_service.py tests/unit/domain/test_title_humanize.py tests/js/title-humanize.test.mjs -q
pytest tests/unit/export/test_poster_bric_pack.py -q
python scripts/license_gpl_scan.py --all-installed
```

## 备注

- dogfood 观测仍可显式 `shadow_log: true` / `near_scene_clone_gate.enabled: true`（见 [tpc-local-dogfood-GUIDE](./tpc-local-dogfood-GUIDE.md)）。
- AC-TPC-04② 删除 `main_eligibility.py` **不在本收口**（仍阻塞于狗粮后另 PR）。
