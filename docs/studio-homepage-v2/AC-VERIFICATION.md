# Studio 首页 v2 · 验收标准与验证方式

> PRD §16 扩展列 · M20-h 测试计划输入。

| ID | Then | 验证方式 | 工具 / 备注 |
|----|------|----------|-------------|
| AC-HP2-01 | 5/5 被试 10s 内复述卷轴+长图 | **人工 · 可用性** | M20-h 后专用窗口；需可点 dogfood build |
| AC-HP2-02 | 16:9/9:16 均有 demo-flag | **自动** | DOM：`[data-demo-flag]` ×2 visible |
| AC-HP2-03 | 示例同一 trip 素材 | **人工 + 自动** | manifest 同源 hash；视觉 diff 可选 |
| AC-HP2-04 | 屏数 = 封面+章+尾声 | **自动** | dots.count === manifest.pages.length |
| AC-HP2-05 | spread 每次 1 页；dots 一致 | **自动** | scroll step 单测 + aria-current |
| AC-HP2-06 | 轻点/⤢ Lightbox；不进 editor | **自动 + 人工** | ⤢ click → dialog；无 `/index.html` 导航 |
| AC-HP2-07 | 横拖不误触 Lightbox | **自动** | pointer move > DRAG_THRESHOLD → no open |
| AC-HP2-08 | 奇数尾页左对齐留白 | **自动 + 人工** | 末 index 右槽 empty；截图 |
| AC-HP2-09 | carousel 首尾 clamp 不 wrap | **自动** | index 边界单测；prev/next disabled |
| AC-HP2-10 | 主 CTA → Import UI（默认 Wizard `#v2-wizard-root`；flag off 为 Sheet）；路径仅在导入 UI 内 | **自动** | e2e click CTA → wizard/sheet visible；无 path 在 Bento |
| AC-HP2-11 | trips≥1 → Bento **与**书架区同屏；Loading 无错误态闪屏 | **自动** | harness multi；`#v2-frame` visible + `#v2-shelf` visible |
| AC-HP2-12 | iPad 1024 横屏 Bento；无 768 堆叠 | **人工 + 自动** | viewport 1024×768；grid 2-col |
| AC-HP2-13 | 手机访问 → Unsupported | **自动** | viewport 390；CMP-HP2-15 visible |
| AC-HP2-14 | iPad 竖屏 → 旋转提示 | **自动** | viewport 768×1024 portrait |
| AC-HP2-15 | Importing 取消无半成品 | **自动** | cancel → trips 无新 slug |
| AC-HP2-16 | 刷新 activeJobId 续 poll | **自动** | reload harness + sessionStorage |
| AC-HP2-17 | 冷启动 Importing 静帧背景 | **自动 + 人工** | harness `importing-cold`；bg 无 Ken Burns |
| AC-HP2-18 | FirstSuccess 背景 = Bento + 书架区 | **自动 + 人工** | harness first-success + multi；frame + shelf visible |
| AC-HP2-19 | carousel 键盘 ←/→ | **自动** | a11y keyboard test |
| AC-HP2-20 | 对比度 AA | **自动** | axe-core 或 computed contrast |
| AC-HP2-21 | 触控 ≥44px | **自动** | bounding box min dimension |
| AC-HP2-22 | assets 失败不白屏 | **自动** | `studioAssetsFail=1` → CTA 仍可见 |
| AC-HP2-23 | flag 回滚；Import 中禁切换 | **自动** | FEATURE-FLAG 用例 |
| AC-HP2-24 | Sheet focus trap · Esc · 焦点归还 | **自动** | tab trap + Esc e2e |
| AC-HP2-25 | `homepage_view` 仅在 state 确定后 | **自动** | mock analytics 调用序 |

### D-14 · 预览画册选择器（§6.8.9）

| ID | Then | 验证方式 | 工具 / 备注 |
|----|------|----------|-------------|
| AC-D14-01 | 无 preference → 示例 + demo-flag ×2 | **自动** | `test_ac_hp2_02_demo_flags` · `test_ac_d14_06` |
| AC-D14-02 | 选用户画册 B → 切 B + demo-flag 隐藏 | **自动** | `test_ac_d14_01` · `test_ac_hp2_bento_tab_mine` |
| AC-D14-03 | 选 B 后硬刷新仍 B | **自动** | `test_ac_d14_03_persist_refresh` · localStorage |
| AC-D14-04 | preference 已删 trip → 示例 + toast | **自动** | `test_ac_d14_04_deleted_trip_fallback` |
| AC-D14-05 | bento-preview 404 → 占位 + 仍选 B | **自动** | `bentoPreview404=` harness · `test_ac_d14_05` |
| AC-D14-06 | 无用户画册 → 仅示例 / disabled | **自动** | `test_ac_d14_06_no_user_trips_combobox_disabled` |
| AC-D14-07 | B algorithmStale → stale bar 绑定 B | **自动** | `single-algorithm-stale` · `test_ac_d14_07` |
| AC-D14-08 | curate 完成 → 刷新 B manifest | **自动** | `studioCurate=succeed` · `test_ac_d14_08` |

### M20-j · holdback / 门控（扩展）

| ID | Then | 验证方式 | 工具 / 备注 |
|----|------|----------|-------------|
| M20-j-01 | auto 10% 进组 UA → 302 `/v2` | **自动** | `test_studio_home_gate_auto_treatment_redirects` |
| M20-j-02 | auto 10% 对照组 → 200 classic @ `/` | **自动** | `test_studio_home_gate_auto_control_stays_classic` |
| M20-j-03 | yaml `percent` 无 env 时生效 | **自动** | `test_studio_home_gate_auto_yaml_percent_redirects` |
| M20-j-04 | redirect 后进组报 `experiment_exposure` | **自动** | Playwright · `bucket_id` 与 cookie 一致 |
| M20-j-05 | 对照组 classic 报 `experiment_exposure` | **自动** | Playwright · `variant=classic` + `bucket_id` |
| M20-j-06 | gate off 忽略 `homepageVariant` 键 | **自动** | Playwright · 预置 sessionStorage 无报错 |

**图例**：自动 = CI 可无人值守；人工 = QA 走查；可用性 = 招募被试（AC-01 挂 M20-h 后窗口）。
