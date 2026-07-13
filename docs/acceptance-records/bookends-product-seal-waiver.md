# Bookends 产品封板 · 限期 Waiver 模板（R-BE-18）

| 属性 | 内容 |
|------|------|
| **关联** | [PRD-BOOKENDS-ENGINE-V1.md](../PRD-BOOKENDS-ENGINE-V1.md) §12 · [ACCEPTANCE-BOOKENDS-ENGINE-V1.md](../ACCEPTANCE-BOOKENDS-ENGINE-V1.md) |
| **工程封板** | 不依赖本文件（B1+B2a 自动化 AC 已绿即可） |
| **状态** | **草稿 · 待签字**（本地无 ≥10 本真实相册时启用） |

---

## 适用范围

当以下条件暂无法满足时，可用本 waiver **限期**宣称「内部 dogfood / 工程封板」，**不得**对外宣传「封底升级 / 产品封板」：

- AC-BE-40 封面 A 率 ≥ 冻结基线
- AC-BE-41 封底收束偏好 ≥60%
- AC-BE-42 压字可读抽样
- Studio AC-BE-20..25 **手工**走查（半自动单测除外）

---

## 已具备证据（勾选）

- [x] 工程封板自动化 AC（AC-BE-01..05、10..14、30..32）
- [x] B2b 半自动（`test_bookends_studio_ac_b2b`）
- [x] 盲评手册 + 导出脚本骨架
- [x] DE-BE-01 正反例图例附件
- [ ] ≥10 本真实相册清单（`bookends-closing-albums.json` tripDir）
- [ ] 旧 closing 基线冻结导出
- [ ] 评委 ≥3 盲评记录

---

## Waiver 正文（签字区）

| 字段 | 填写 |
|------|------|
| **原因** | 本地暂无齐套真实 trip / 盲评资源不足 |
| **有效期** | ____ 年 __ 月 __ 日 至 ____ 年 __ 月 __ 日（建议 ≤30 天） |
| **仍禁止对外话术** | 「封底升级」「成对质量已产品封板」 |
| **到期动作** | 补齐相册 → 跑 `scripts/bookends_closing_blind_export.py` → 更新 ACCEPTANCE AC-BE-40..42；或延长本 waiver |
| **产品签字** | |
| **工程签字** | |
| **日期** | |

---

## 恢复产品封板检查单

1. 填满 `docs/acceptance-records/bookends-closing-albums.json` 的 `tripDir`（≥10）
2. 导出旧 vs Bookends 成对刺激物并冻结 signoff
3. Studio 手工走查 AC-BE-20..25
4. 将本 waiver 状态改为 `superseded`，并在 ACCEPTANCE §4 写入产品封板行
