# D-CAL-28 · 代码质量审计收口（换封面指纹 / CAS 外计算 / 死代码清理）

**日期**：2026-08-09  
**状态**：已落地  
**关联**：[PRD-COVER-CALLIGRAPHY-TITLE-V1](../PRD-COVER-CALLIGRAPHY-TITLE-V1.md) · 分支质量审计（feat/cover-calligraphy-title-v1）

## 1. 起因

产品负责人要求对大型分支做代码质量审计后「Fix all，但需谨慎」——每条先核实上下游与根因，确认确实需要再修。

## 2. 核实结论（修 / 不修）

| 审计项 | 核实 | 处置 |
|---|---|---|
| 换封面不置 stale | **成立**：`mark_title_art_stale` 文档写封面变更，实际只接 title/style；`apply_joint_pick` / curate 等写 `coverAssetId` 未接 | **修**：指纹 + 展示门禁 + joint 主动 stale |
| Route C 在 CAS mutator 内 | **成立**：更关键的是**持跨进程锁期间跑分钟级网络**；重放放大是次要风险 | **修**：计算移出 `update` |
| 注释写 4 款实为 10 款 | **成立**（扩展时已核对，注释过期） | **修**注释 |
| render_b 衬底死代码 | **成立**：无调用、无测试 | **删** |
| 两种 `None` 语义 | **成立**：CLI 已区分，handler 混用；缓存命中返回 `None` | **修**：缓存命中返回结果对象 |
| whitelist 导入期硬失败 | 风险真实但已有 region 一致性测；补契约测即可 | **补测**，不改 fail 策略 |
| 下载无 scheme/体积上限 | 纵深防御缺口 | **修** |
| `_is_han` 重复 | 低风险 DRY | **修** |
| seal 字段 / 孤儿 PNG / 字库 LFS | 兼容或已拍板延后 | **不修** |

## 3. 根因方案（换封面）

不依赖「每个写点都记得调 mark_stale」：

1. 生成时落库 `meta.titleArt.coverAssetId`（当时的 `trip.coverAssetId`）
2. 展示层 `_resolve_title_art_src`：有指纹且 ≠ 当前 → 不叠加（缺字段的历史数据兼容放行）
3. 缓存短路：封面/风格指纹不一致 → 强制重算；命中则返回已有 `TitleArtResult`（`None` 仅表 fail-open）
4. `apply_joint_pick` 在 `coverAssetId` 实际变化时主动 `mark_title_art_stale`

## 4. 根因方案（CAS）

`handle_post_resolve_title_art`：`deepcopy` 快照上跑 `resolve_title_art`（含写 PNG / Route C），`mutator` 只写入算好的 `meta.titleArt` 字典。单测钉死调用顺序 `resolve → update`。

## 5. 其它落地

- 删除 `render_b` 三套 backdrop 与空 `_BACKDROP_RENDERERS`
- Route C `_download_image`：仅 `https` + 20MB 硬上限
- `risk_rules` 复用 `char_frequency._is_han`
- 白名单 registry 契约单测

## 6. 测试

相关子集 **142 passed**；ruff 全绿。
