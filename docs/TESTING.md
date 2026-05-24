# Travelogue · 测试策略

| 属性 | 内容 |
|------|------|
| **文档版本** | v0.1 |
| **原则** | 关键路径必测；不追求高覆盖率 |
| **关联** | `VALIDATION-RULES.md`、`DEFINITION-OF-DONE.md` |
| **更新日期** | 2026-05-22 |

---

## 1. 测试金字塔

```
        ┌─────────────┐
        │ 3× 真实 trip │  AC / 人工
        ├─────────────┤
        │  e2e 脚本    │  CLI 一条龙
        ├─────────────┤
        │  集成测试    │  agent + 临时目录
        ├─────────────┤
        │  单元测试    │  validate / curate 规则
        └─────────────┘
```

---

## 2. Fixtures

| 文件 | 用途 |
|------|------|
| `schemas/fixtures/trip.example.json` | 通用样例 |
| `schemas/fixtures/trip.ingest_ready.json` | Agent 1 输入 |
| `schemas/fixtures/trip.structure_locked.json` | Agent 2 输入 |
| `schemas/fixtures/trip.copy_locked.json` | Agent 3 输入 |

**CI 必跑**（`.github/workflows/ci.yml`）：

```powershell
python -m pytest tests/ -q
python scripts/validate_trip.py schemas/fixtures/trip.example.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.ingest_ready.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.structure_locked.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.copy_locked.json --level all
python scripts/validate_trip.py schemas/fixtures/trip.render_golden.json --level all
python -m travelogue demo verify
```

---

## 3. 单元测试（pytest）

目录：`tests/`

| 模块 | 用例示例 |
|------|----------|
| `test_validate.py` | 超字数、缺 ref、封面视频 → 错误码 |
| `test_validate_limits.py` | VR-L07/L08、VR-M03 |
| `test_curate.py` | 跨天分章、章数 3–5、多 segment 合册 |
| `test_narrate.py` | 规则 stub、禁用词 |
| `test_pipeline_run.py` | 流水线顺序 |

```powershell
pip install pytest jsonschema pyyaml
pytest tests/ -q
```

---

## 4. 集成测试

| 场景 | 做法 |
|------|------|
| ingest | 临时目录 3 张 jpg → assets 存在 |
| render | `copy_locked` fixture 复制到 tmp → index.html 生成 |
| export | zip 内 index.html 可解析 |

使用 `tmp_path` fixture，不提交 `trips/`。

---

## 5. 视觉回归（轻量）

MVP **不强制** Percy；采用：

- [ ] `render` 后人工对照 `golden.html` checklist（`ACCEPTANCE.md` T-01～T-07）  
- [ ] 可选：保存 `tests/snapshots/dom-structure.txt`（仅标签+class 树）

---

## 6. E2E 脚本（目标）

`scripts/e2e_smoke.ps1`（待实现）：

1. `trip new e2e-test --from tests/data/mini_album`  
2. `curate` → `lock structure` → `narrate` → `lock copy`  
3. `render` → `export --confirm-privacy`  
4. 断言 zip 存在  

`tests/data/mini_album/`：3 张 **公版/自制** 小图（<100KB each）。

---

## 7. 手动测试清单（发版前）

- [ ] 微信内置浏览器打开 zip 内 HTML  
- [ ] `<audio>` 播放  
- [ ] 横滑 scroll 不撑破视口  
- [ ] `data-layout=mobile` 强制竖版  

---

## 8. CI（建议）

`.github/workflows/ci.yml`（P1）：

```yaml
# 示意
- pip install jsonschema pytest
- python scripts/validate_trip.py schemas/fixtures/*.json --level all
- pytest tests/
```

---

## 9. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v0.1 | 2026-05-19 | 初稿 |
