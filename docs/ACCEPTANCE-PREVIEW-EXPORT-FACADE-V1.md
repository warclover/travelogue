# 预览导出门面 V1 · 验收清单

| 属性 | 内容 |
|------|------|
| **对应 PRD** | [PRD-PREVIEW-EXPORT-FACADE-V1.md](./PRD-PREVIEW-EXPORT-FACADE-V1.md) v1.1.0 |
| **实施清单** | [IMPLEMENTATION-PREVIEW-EXPORT-FACADE-V1.md](./IMPLEMENTATION-PREVIEW-EXPORT-FACADE-V1.md) |
| **评审记录** | [preview-export-facade-v1-review-2026-07-11.md](./acceptance-records/preview-export-facade-v1-review-2026-07-11.md) |
| **状态** | **Reliability Go（条件）** · P0.5 收口已合代码 · Theme Complete 待 SF-02 + 种子手测 |
| **日期** | 2026-07-11 |

---

## 1. 里程碑

| 里程碑 | 状态 |
|--------|------|
| M-EXP-1～4 | ✅ 代码落地 + 静态门禁 |
| P0.5（F-EXP-08 / 非 Dock 长图 / 平台成功引导 / error_code） | ✅ |
| M-EXP-5 SF-02 | ⏸ 合入后补签 |

---

## 2. AC-EXP（工程自检 / 静态）

| ID | 期望 | 结果 |
|----|------|------|
| **AC-EXP-01** | 更新并导出 busy「正在更新版面…」 | ✅ 代码路径 |
| **AC-EXP-02** | 续跑 `from=after_layout` | ✅ |
| **AC-EXP-03** | 无 pending 直接导出 | ✅ 不回归 |
| **AC-EXP-04** | rerender 失败清 flag + 分叉文案 | ✅ |
| **AC-EXP-05** | trip 不一致不导出 | ✅ |
| **AC-EXP-06** | TTL 过期不导出 | ✅ |
| **AC-EXP-07** | Modal 标题「导出前先更新一下」 | ✅ |
| **AC-EXP-08** | 仅更新后 `showNextStepHint` | ✅ |
| **AC-EXP-09** | Dock「长图」+ aria 导出长图 | ✅ 精修 V1 已有 |
| **AC-EXP-10** | 脉冲：主钮点击后停；▾ 不停 | ✅ |
| **AC-EXP-11** | 成功「已保存到本机 · 拖进微信群即可」 | ✅ |
| **AC-EXP-12** | 埋点标记存在 | ✅ 静态 |
| **AC-EXP-13** | SF-02 ≥4/5 | ⏸ |
| **AC-EXP-14** | 稍后仍拦截 | ✅ 精修 V1 回归 |

手测（Studio 真机）建议补签：刷新 busy 可见、离开不幽灵、仅更新残留、成功主句层级。

---

## 3. 发布门禁

| 门 | 本轮 |
|----|------|
| **Reliability Go** | **条件 Go**（静态全绿；建议合入前做一轮真机续跑手测） |
| **Theme Complete** | ⏸ SF-02 + 5 人种子 |

---

## 4. 签字栏

| 角色 | 结论 | 签字 |
|------|------|------|
| 工程 | 静态门禁 23 passed | ✅ 2026-07-11 |
| 产品 | Reliability 条件 Go；Theme Complete 待补 | ✅ 2026-07-11 |
| UX（SF-02） | 图标盲测 | ⏸ |
