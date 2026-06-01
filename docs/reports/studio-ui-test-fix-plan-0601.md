# Studio UI 测试修复方案

**日期**: 2026-06-01
**失败总数**: 38 条（实际分为 3 类根因 + 1 类环境不稳定）

---

## 分类总览

| 类别 | 根因 | 测试数 | 确定性 |
|------|------|:------:|:------:|
| **A. CURATE_TOO_FEW** | `fd2206a` 新增 `min_megapixels=0.8` 过滤器淘汰了测试 fixture 图片 | 18 | ✅ 确定必现 |
| **B. JS 字符串断言过期** | 测试断言 `options.highlight` 但代码已重构为内联 `{ highlight: i === 0 }` | 1 | ✅ 确定必现 |
| **C. Playwright 环境不稳定** | 全量运行时失败，独立运行全部通过（18/18） | 18 | ❌ 不稳定 |
| **D. user_tier 字段值变更** | `importSource` 期望 `material` 实际为 `featured`，全量运行失败、单独通过 | 1 | ❌ 不稳定 |

---

## 类别 A：CURATE_TOO_FEW（18 条）

### 根因链

```
fd2206a 改动 partition_low_resolution_assets()
  → 新增 min_megapixels=0.8 兆像素硬底线
  → _relative_low_res_ids() 用 megapixels 做批内相对过滤
  → 测试 fixture 用 PIL 生成 900×700 = 0.63 MP 的图片
  → 0.63 < 0.8 (min_megapixels) → 全部被标记为低分辨率排除
  → layout_eligible_assets() 返回空列表
  → < MIN_CURATE_ASSETS(4) → CurateError("E_CURATE_TOO_FEW")
```

### 涉及测试（全部因同一错误失败）

| 文件 | 测试 |
|------|------|
| test_intent_plan.py | `test_pipeline_with_plan_text_persists_intent`, `test_pipeline_with_bad_plan_still_succeeds` |
| test_studio_chrome.py | `test_studio_chrome_on_index_not_longshot`, `test_studio_trips_list` |
| test_studio_g1.py | `test_g1_mode_b_stops_at_structure_draft`, `test_g1_mode_a_reaches_rendered` |
| test_studio_homepage_m12.py | `test_studio_trips_api_limit_and_total` |
| test_studio_intent.py | `test_pipeline_default_place_passes_schema`, `test_pipeline_persists_intent_and_passes_schema` |
| test_studio_intent_telemetry.py | `test_pipeline_writes_studio_intent_telemetry` |
| test_studio_m10.py | `test_studio_trips_includes_preview_path`, `test_studio_export_zip` |
| test_studio_nr_p2_02.py | `test_non_studio_serve_no_preview_toolbar` |
| test_studio_server.py | `test_studio_import_job`, `test_studio_demo_exists_409`, `test_studio_longshot_job` |
| test_studio_ux_p3.py | `test_ux_p3_01_import_job_reports_four_stages` |
| test_studio_security.py | `test_studio_reveal_accepts_trip_rel_path` |

### 修复方案（三选一）

#### 方案 A1（推荐）：提升 fixture 图片分辨率

**思路**：让测试图片满足生产级过滤阈值，而不是绕过过滤器。

**改动**：
- 各测试文件中的 `_distinct_album()` / `_make_album()` helper，将 `Image.new("RGB", (900, 700))` 改为 `Image.new("RGB", (1600, 1200))`（1.92 MP > 0.8）
- 影响约 6 处 helper 函数（分布在 6 个测试文件中）

**优点**：测试验证的是真实阈值；不降低过滤标准
**缺点**：fixture 图片稍大，但 PIL 内存生成几乎无开销
**风险**：低

#### 方案 A2：测试专用 config 覆盖

**思路**：为测试提供 `low_res_min_megapixels=0` 的 AppConfig，绕过过滤器。

**改动**：
- 在 `run_studio_pipeline()` 调用处传入 `app_config=AppConfig(ingest=IngestConfig(low_res_min_megapixels=0.0))`
- 或在 `tests/conftest.py` 添加 fixture 级别的 config 注入

**优点**：不动 fixture
**缺点**：测试不验证生产阈值逻辑；每个调用点都要加
**风险**：中——可能掩盖真实的过滤回归

#### 方案 A3：降低生产阈值

**思路**：`min_megapixels` 从 0.8 降到 0.5，让 0.63 MP 的图片通过。

**改动**：`travelogue/config.py` 第 76 行 `low_res_min_megapixels: float = 0.8` → `0.5`

**优点**：改动最小
**缺点**：降低了生产过滤灵敏度，可能放行真正低分辨率的图片
**风险**：高——影响产品行为

---

## 类别 B：JS 字符串断言过期（1 条）

### 根因

`test_studio_homepage_m12.py:85` 断言 `"options.highlight" in js`，但代码在重构中已将 `options.highlight` 模式改为内联参数 `{ highlight: i === 0 }`（见 `templates/studio/js/render.js:462`）。

### 修复方案

更新断言为当前代码中实际存在的字符串：

```python
# 旧
assert "options.highlight" in js
# 新 — 匹配 render.js 中的实际用法
assert "renderTripCard" in js and "highlight" in js
```

或者更精确地匹配内联用法：

```python
assert "{ highlight:" in js or "highlight:" in js
```

**改动**：仅 `tests/test_studio_homepage_m12.py` 第 85 行
**风险**：低

---

## 类别 C：Playwright 环境不稳定（18 条）

### 现象

| 运行方式 | 结果 |
|----------|------|
| 全量 `pytest tests/` | 18 条 Playwright 失败 |
| 单独 `pytest tests/test_studio_p9_qa_playwright.py tests/test_studio_p10_layout_playwright.py` | **18 条全部通过** |

失败集中在：
- **P9** (11 条): `no_horizontal_overflow` 多宽度参数化、`empty_keyboard_and_sheet`、`returning_skip_link_target`、`sheet_pick_button_clickable`
- **P10** (7 条): `importing_layout_tier`、`capabilities_attr`、`wide_success_overlay`、`compact_failure_overlay`、`resize_import_stage_copy`

### 可能原因

1. **端口冲突**：全量运行时前面的 HTTP ���务器测试（`test_studio_server.py` 等）启动的服务未完全关闭，Playwright 测试复用同一端口
2. **浏览器进程残留**：前序 Playwright 相关测试（如 `test_studio_chrome.py`）未正确关闭浏览器上下文
3. **时序竞争**：全量运行下 Playwright 启动更慢，超时阈值不足

### 修复方案

#### 方案 C1（推荐）：增加 Playwright 测试隔离

1. **确保每个 Playwright 测试使用独立端口**：在 `conftest.py` 或各测试文件中用 `_free_port()` 动态分配，避免端口复用
2. **添加 `@pytest.mark.serial`**：将 Playwright 测试标记为串行运行，避免并发资源竞争
3. **添加 fixture 级别的浏览器 teardown**：确保 `browser.close()` 和 `context.close()` 在 fixture teardown 中被调用

#### 方案 C2：调大超时 + 重试

在 `pytest.ini` 或 `conftest.py` 中对 Playwright 标记的测试增加超时和重试：

```ini
[pytest]
addopts = --timeout=60
```

或用 `pytest-rerunfailures`：
```bash
pytest --reruns=2 --reruns-delay=5 -m playwright
```

**优点**：简单
**缺点**：治标不治本，掩盖真实竞争问题

---

## 类别 D：user_tier 字段值变更（1 条）

### 现象

- 全量运行失败：`assert 'featured' == 'material'`（期望 `material`，实际 `featured`）
- 单独运行通过

### 根因分析

`test_cross_folder_dedupe_preserves_material_import_source` 检查 `importSource` 字段值为 `material`。近期提交可能将双文件夹模式下的 `importSource` 从 `"material"` 改为 `"featured"`（与 intent 层的 `featuredDetected` 语义对齐）。单独运行通过说明测试依赖其他测试创建的状态——即**测试隔离不足**。

### 修复方案

1. **确认字段语义变更**：检查 `travelogue/services/` 或 `travelogue/curation/` 中 `importSource` 的赋值逻辑，确认 `"featured"` 是否为新的正确值
2. **如果 `"featured"` 是正确值**：更新断言为 `assert source == "featured"`
3. **如果 `"material"` 仍是正确值**：说明是全量运行时的状态泄漏，需在测试中添加 `tmp_path` 隔离或 `trip` 清理

---

## 推荐执行顺序

| 步骤 | 类别 | 方案 | 预计改动量 | 修复测试数 |
|:----:|:----:|------|:----------:|:----------:|
| 1 | A | A1: fixture 提升到 1600×1200 | 6 处 helper | 18 |
| 2 | B | 更新 JS 字符串断言 | 1 行 | 1 |
| 3 | C | C1: Playwright 端口隔离 + serial 标记 | conftest + 2 文件 | 18 (不稳定性) |
| 4 | D | 确认 importSource 语义后更新断言 | 1 行 | 1 |

**步骤 1+2 即可恢复 19/38 条确定性失败，CI 核心管线恢复全绿。**
步骤 3-4 解决不稳定测试，提升 CI 可信度。
