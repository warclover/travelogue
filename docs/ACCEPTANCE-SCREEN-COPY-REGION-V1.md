# ACCEPTANCE · 屏级文案区 V1（SCR）

| 属性 | 内容 |
|------|------|
| **PRD** | [PRD-SCREEN-COPY-REGION-V1.md](./PRD-SCREEN-COPY-REGION-V1.md) **v0.2.0** |
| **评审** | [scr-screen-copy-region-v1-review-2026-08-04.md](./acceptance-records/scr-screen-copy-region-v1-review-2026-08-04.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-04 |

> 合同级 AC；编号与 PRD §9 对齐。M1 Done 宣称前：AC-SCR-01～10 + **06b** 须绿，且 BLK-SCR-03～06 关闭。

---

## M1 必修

| ID | 断言 | 测法 | 状态 |
|----|------|------|------|
| **AC-SCR-01** | 无 `textRegions` 的 pattern：DOM 无 SCR 节点 | fixture / 渲染快照 | ⏳ |
| **AC-SCR-02** | 有 region 且 copy 空：读者态无可见节点、无常驻虚线 | DOM + 截图 | ⏳ |
| **AC-SCR-03** | draft 聚焦空 region 出现占位；失焦且空则隐藏 | e2e / 手测 | ⏳ |
| **AC-SCR-04** | 写入 kicker/body 立即持久化；`*Source=user` | save-copy + trip.json | ⏳ |
| **AC-SCR-05** | 清空后读者态空隐；导出无假句残影 | 导出 HTML/长图 | ⏳ |
| **AC-SCR-06** | 默认 longshot **含**非空 L1 文本块 | 长图 DOM / 截图 | ⏳ |
| **AC-SCR-06b** | `screen-landscape-1` 声明 textRegions；可写、读者可见、长图可见 | 狗粮 + 单测 | ⏳ |
| **AC-SCR-07** | `photos` / `wechat_moments`：L1 折叠 | 平台导出 | ⏳ |
| **AC-SCR-08** | 全书无 SCR：导出成功、不阻断 | e2e | ⏳ |
| **AC-SCR-09** | Share 模式不可编 SCR | share DOM | ⏳ |
| **AC-SCR-10** | overlay 开启前后槽 bbox 差 = **0 px** | 几何断言 | ⏳ |

## M2

| ID | 断言 | 状态 |
|----|------|------|
| **AC-SCR-11** | L4/L6 CI：禁止非空 textRegions | ⏳ |
| **AC-SCR-12** | Dock「本页文字」可进空屏焦点 | ⏳ |
| **AC-SCR-13** | Web 与长图 L1 显隐一致（同 copyDisplay） | ⏳ |
| **AC-SCR-14** | SCR 编辑不置 `layoutPending` | ⏳ |

## M3（延期）

| ID | 断言 | 状态 |
|----|------|------|
| **AC-SCR-15** | AI 候选不自动写入 | ⏸ |
| **AC-SCR-16** | L3 默认不写 `screens[].copy` | ⏸ |
| **AC-SCR-17** | absorb 空扩 / 有字占 gap | ⏸ |

---

## 防假绿

1. **禁止**仅以「4mix enrich 已抽函数」宣称 M1 Done（须 AC-06b）。  
2. **禁止**仅测 web scroll 宣称「导出含字」（须 AC-06 长图）。  
3. Moments 无图内字 = **预期通过**，不算 AC-06 失败。
