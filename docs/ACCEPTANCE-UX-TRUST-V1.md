# 信任闭环 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-UX-TRUST-V1.md](./PRD-UX-TRUST-V1.md) v1.1.0 |
| **实施清单** | [IMPLEMENTATION-UX-TRUST-V1.md](./IMPLEMENTATION-UX-TRUST-V1.md) |
| **评审记录** | [ux-trust-v1-review-2026-07-11.md](./acceptance-records/ux-trust-v1-review-2026-07-11.md) |
| **状态** | Draft · 代码补齐断服/Share 保存/附录 D 单测 · 待真机补签 |
| **日期** | 2026-07-11 |

---

## 1. 三道门

| 门禁 | 条件 | 本轮 |
|------|------|------|
| **Reliability Go** | STALE 静音、续跑 platform、C1～C3、UX-P5-80-01 | ⏸ 真机 |
| **Shell / Share Go** | 默认控件=0；share 零工程 +「保存图片」 | ⏸ 真机 + 静态 |
| **Theme Complete** | 门禁 + 写路径 + P1 话术 + 敢发复测 | ⏸ |

---

## 2. 禁止选择器清单（INSPECT-06 / AC-TRU-08）

默认 `data-preview-refine="off"` 或 `data-preview-share="on"` 时，下列须 **不可见且不可点**（`hidden` / `display:none` + `pointer-events:none` / `disabled`）：

| 选择器 | 说明 |
|--------|------|
| `.preview-toolbar__featured-star` | ★ 精选 |
| `.preview-toolbar__collage-ctrl` | 拼图/媒资改判 |
| `.folio-plate-meta` | Plate 工程元信息 |

Share 另禁：精修 Dock、平台 ▾、`[data-editable]` 进编辑、常驻「可编辑」提示。

---

## 3. AC 骨架（Given / When / Then）

### P0 · 验货壳 / Share

| ID | Given | When | Then | 方法 |
|----|-------|------|------|------|
| **AC-TRU-08** | Studio 预览 `data-preview-refine=off` | 未开精修 | 禁止选择器 visible=0 且不可点 | DOM + 手测 |
| **AC-TRU-09** | 同上 | 打开精修 Sheet | 控件可见可点；关闭后再藏 | 手测 |
| **AC-TRU-10** | refine=off | 查看版心 | 无 `.folio-plate-meta` 可见 | DOM |
| **AC-TRU-13** | `?share=1` | 打开 | 无精修/★/可编辑提示 | 手测 |
| **AC-TRU-13b** | share | 顶栏 | 返回 + 放映 + **「保存图片」**；无平台 ▾ | 静态 + 手测 |
| **AC-TRU-13c** | share 会话 | 路由抖动 / 重入 | 不复活编辑壳 | 手测 |
| **AC-TRU-13d** | Studio vs share | 顶栏并排 | 创作者 Dock ≠ share 最小条 | 手测/截图 |
| **AC-TRU-14** | share | 版心 | 无 Plate | DOM |
| **AC-TRU-15** | 精修「这本」 | 导航 | URL 不含误加 `share=1` | 手测 |

### P0 · stale / 续跑

| ID | Given | When | Then | 方法 |
|----|-------|------|------|------|
| **AC-TRU-11** | 导出成功 | 60s 内 / 成功态未关 | 无「产物过期」主警告 | 手测 N≥3 |
| **AC-TRU-12** | 导出成功 | 看成功条 | 发群引导主句在 | 手测 |
| **AC-TRU-04** | layoutPending | 更新并导出 | busy 文案可见 | 手测 |
| **AC-TRU-05** | 续跑疑似跳首页 | 探针记录 | 未定位前不挡 Reliability | 探针 |
| **AC-TRU-06** | 导出/轮询中断服 | 失败反馈 | 主句含「长图还没有导出」+「回到预览」；清 flag | 静态 + 手测 |
| **AC-TRU-07** | 选小红书 + pending | 更新并导出 | start `platform=xiaohongshu` | 埋点/手测 |
| **AC-TRU-07b** | TTL / trip 不一致 / 离开 | 回预览 | 不幽灵导出 | 回归 Facade |
| **AC-TRU-C2** | pending | 点长图 | Modal 拦截，无静默旧图 | 回归 |
| **AC-TRU-80** | 零精修 | 点长图 | 可导出 | UX-P5-80-01 |

### P0 · 门禁 / 写路径

| ID | Given | When | Then | 方法 |
|----|-------|------|------|------|
| **AC-TRU-01** | 标题命中附录 D 正例 | 点长图（无 pending） | 出门禁 | 表驱动单测 + 手测 |
| **AC-TRU-01b** | `京都三日` / `A+B 旅行手记` 等负例 | 点长图 | 不出门禁 | 表驱动单测 |
| **AC-TRU-02** | 门禁「改标题并导出」 | 输入新名 | 封面/`document.title`/落盘一致 | 手测 |
| **AC-TRU-03** | 门禁 | 「暂时不改」 | 导出成功 + bypass 埋点 + 成功态回声标题 | 手测 |
| **AC-TRU-03b** | 严重档空标题 | 首次无 bypass；取消后再点 | 第二次出现 bypass（COPY-06b） | 手测 |
| **AC-TRU-16** | 精修封面标题 | 改名保存 | 落盘且不升 stale | 手测 |
| **AC-TRU-16b** | pending + 脏标题 | 点长图 | 先 layout Modal，完成后再门禁 | 手测 |

### 埋点

| 事件 | 断言 |
|------|------|
| `copy_gate_shown` / `fix` / `bypass` | 门禁路径触发 |
| `stale_warned_within_60s_of_success` | `suppressed: true` 或业务上主警告=0 |
| `longshot_export_start.platform` | 续跑保持 |
| `longshot_success_share_hint_shown` | 成功态 |
| `longshot_export_fail.error_code=disconnect` | 断服路径 |

### P1 · 图说 / 平台话术

| ID | Given | When | Then | 方法 |
|----|-------|------|------|------|
| **AC-TRU-17** | 精修「这本」改名 | 保存 | ≤1s 反映封面/`document.title` | 手测（可与 AC-16 合并） |
| **AC-TRU-18** | 精修 | 双击或「这页」改图说 | 立即生效且不置 pending | 手测（沿用既有路径） |
| **AC-TRU-19** | 选朋友圈 | 导出中 | 进度含「朋友圈」 | 静态/手测 |
| **AC-TRU-20** | 选小红书 | 导出成功 | 成功主句点名小红书/3:4 | 静态/手测 |
| **AC-TRU-21** | 任一平台 | 导出结束 | 必有成功结论条（非进度消失即结束） | 手测 |

### P2 · 首页降噪

| ID | Given | When | Then | 方法 |
|----|-------|------|------|------|
| **AC-TRU-22** | 打开 Studio 首页 HTML | 扫用户可见文案 / aria-label | 无「Bento」；有「导入偏好」副文案「下次导入…」 | 静态单测 |
| **AC-TRU-23** | 同上 | 看主 CTA | 文案仍为「开始制作我的游记」 | 静态单测 |

---

## 4. 故障注入 runbook

| 场景 | 步骤 | 期望 |
|------|------|------|
| rerender fail | mock `/rerender` 500 后「更新并导出」 | 「版面没有更新成功，长图尚未开始」；清 flag |
| 断服 | 续跑中停 Studio / mock fetch 失败 | 文案含「服务已停止，长图还没有导出」+「回到预览」；清 exportAfterLayout |
| 跳首页 | 探针：记录是否复现 | 未定位前不挡 Reliability Go |

---

## 5. No-Go

1. 静默旧导出  
2. 默认 ★/拼图可点  
3. share 可编辑或 Plate 可见  
4. 成功 60s 内过期主警告  
5. 改标题并导出不落盘仍成功  

---

## 6. 签字栏

| 角色 | 结论 | 签字 |
|------|------|------|
| 工程 | 代码 + 单元测试（含附录 D 表驱动） | ⏸ |
| 产品 | Shell/Reliability 条件 Go | ⏸ |
| QA | 真机 AC 补签 | ⏸ |
