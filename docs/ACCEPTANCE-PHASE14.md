# Phase 14 验收入口（双模式导入）

| 属性 | 内容 |
|------|------|
| PRD | [PRD-PHASE14.md](./PRD-PHASE14.md) v0.14.1 |
| 实施 | [IMPLEMENTATION-PHASE14.md](./IMPLEMENTATION-PHASE14.md) |
| 线框 | [archive/import-sheet/studio-import-sheet-v2-dual-mode.html](./archive/import-sheet/studio-import-sheet-v2-dual-mode.html)（已归档） |
| 状态 | In Progress |

---

## 验收范围

Phase 14 仅验收以下目标：

1. 导入入口双模式：`快速分享 / 精细制作`
2. 精细模式新增字段：`dateRange`、`travelNotes`
3. 成功页分流：快速主 CTA 长图，精细主 CTA 卷轴
4. 弹窗放大与低分辨率可用性
5. 不损升级：旧请求/旧 trip 兼容

---

## 自动化验收（建议顺序）

```bash
pytest tests/test_studio_entry.py tests/test_studio_intent.py tests/test_studio_preview_m16.py -q
pytest tests/test_studio_chrome.py tests/test_studio_stages.py -q
pytest tests/test_template_router.py tests/test_render.py -q
```

> 注：若现有测试文件不覆盖 Phase 14 新行为，请在 M14.4 增补对应测试后再作为发布门槛。

---

## 手工验收清单（AC 对应）

| AC ID | 场景 | 步骤 | 预期 |
|-------|------|------|------|
| AC-P14-01 | 默认模式 | 打开首页，点“制作我的游记” | Sheet 默认选中“快速分享” |
| AC-P14-02 | 精细字段完整 | 切到“精细制作” | 可见名称/地点/日期/编辑一句话/见闻感悟/精选与素材目录 |
| AC-P14-03 | 命名替换 | 全流程文案检查 | 无“懒人版/专业版”残留 |
| AC-P14-04 | 按钮文案 | 精细模式提交按钮 | 文案为“开始制作（专业）” |
| AC-P14-05 | 成功页分流 | 分别跑快速/精细各一次 | 快速主 CTA=保存长图；精细主 CTA=卷轴预览 |
| AC-P14-06 | 日期兜底 | 精细模式不填日期导入 | 仍可成功，使用 EXIF 或空值兜底 |
| AC-P14-07 | travelNotes 消费 | 填写见闻感悟导入后查看 trip | `intent.travelNotes` 落盘；narrate brief可见 |
| AC-P14-08 | 快速路径不回归 | 快速模式全流程 | 体验与 Phase 5 等价或更优 |
| AC-P14-09 | 弹窗尺寸升级 | 1440×900 下打开 Sheet | 宽度 >=560px，首屏信息不拥挤 |
| AC-P14-10 | 草稿保留 | 填写精细字段 -> 切 tab -> 关闭重开 | 输入不丢失 |
| AC-P14-11 | 日期校验 | 填 start>end 提交 | 阻断提交并提示“开始日期不能晚于结束日期” |
| AC-P14-12 | 禁自动跳转 | 精细模式成功页等待 | 不自动跳预览，仅主 CTA 高亮引导 |

---

## 兼容性验收（不损升级）

### C1 旧请求兼容

请求仅包含旧字段：

```json
{
  "albumPath": "D:\\Photos\\Kyoto2025",
  "title": "Kyoto2025",
  "place": "旅途"
}
```

预期：

- 返回 202 + `jobId`
- 导入成功
- `trip.json` 无新增字段也不报错

### C2 旧 trip 兼容

前置：使用历史无 `intent.dateRange/travelNotes` 的 trip。  
预期：可正常打开预览、可保存长图、可再次导入生成新 trip。

### C3 fail-open

人为构造 `travelNotes/dateRange` 非法值（前端绕过）。  
预期：后端不崩；字段忽略或清洗；主流程继续。

---

## 视口与交互可用性

| 视口 | 必测项 | 通过标准 |
|------|--------|----------|
| 1920×1080 | 双模式完整流程 | 可提交，无布局错位 |
| 1440×900 | 精细模式长表单 | 无关键字段遮挡 |
| 1366×768 | 低分辨率提交 | 主 CTA 始终可达 |
| 1280×720 | 极限桌面窗口 | 可滚动完成提交 |

---

## 失败与回退验收

### R1 导入失败重试

步骤：构造失败（如非法路径）-> 回到 Sheet -> 修正后重试。  
预期：mode 与已填字段保留，不需重填。

### R2 成功页预览不可用回退

步骤：模拟 preview 资源缺失。  
预期：精细模式主 CTA 自动降级为“保存长图”并给出提示。

### R3 回退开关验证（开发联调）

| 开关 | 期望行为 |
|------|----------|
| `studio.import_dual_mode_enabled=false` | 退回单模式入口 |
| `studio.success_refined_default_enabled=false` | 退回旧成功页 CTA 逻辑 |
| `studio.import_sheet_large_enabled=false` | 退回原弹窗尺寸 |

---

## 验收输出物

验收完成需提交：

1. `docs/acceptance-records/phase14-manual-signoff.md`（手工验收记录）
2. `docs/acceptance-records/phase14-test-summary.json`（自动化结果摘要）
3. 截图 4 张：
   - 快速模式 Sheet
   - 精细模式 Sheet（含新增字段）
   - 快速成功页
   - 精细成功页

---

## 结论门槛

Phase 14 可视为“可合并”需同时满足：

1. AC-P14-01 ~ AC-P14-12 全通过  
2. 兼容性 C1/C2/C3 全通过  
3. 视口可用性四档全通过  
4. 失败与回退 R1/R2/R3 全通过

