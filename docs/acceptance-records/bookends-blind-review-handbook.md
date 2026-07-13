# Bookends 封底盲评操作手册（DE-BE-03 · PRD §14.1）

| 属性 | 内容 |
|------|------|
| **关联** | [PRD-BOOKENDS-ENGINE-V1.md](../PRD-BOOKENDS-ENGINE-V1.md) §14.1 · [ACCEPTANCE-BOOKENDS-ENGINE-V1.md](../ACCEPTANCE-BOOKENDS-ENGINE-V1.md) |
| **导出脚本** | `scripts/bookends_closing_blind_export.py` |
| **日期** | 2026-07-13 |

## 1. 封面侧（沿用 cover-selection-plan）

1. 使用 `scoreRankedTop3`，**禁止**用多样性 `coverCandidates` 当刺激物顺序。  
2. A 率定义同既有 cover-selection 盲评。  
3. 基线可参考 `docs/acceptance-records/cover-selection-signoff.json`。

## 2. 封底侧（Bookends）

1. 导出：`python scripts/bookends_closing_blind_export.py --init-albums` 后填 `tripDir`，再 `--albums ...`。  
2. 每本刺激物：**同屏封面缩略** + 左右两侧封底（旧 heuristic vs Bookends）。  
3. 左右随机化；题干固定：「哪边封底更有收束/回望（不是更好看）」。  
4. 评委 ≥3；相册 ≥10；记录 `degraded` / 是否人像封面；平票记弃权。  
5. 目标：Bookends 偏好 ≥60%（AC-BE-41）；封面 A 率不低于冻结基线（AC-BE-40）。

## 3. 附属（AC-BE-42）

抽样 Opening 标题压字截图：无严重糊字 / 撞脸即记通过。

**图例附件（DE-BE-01）：** [bookends-pair-examples-de-be-01.html](./bookends-pair-examples-de-be-01.html)

## 4. Waiver

若真实相册不足，产品封板可用限期 waiver（模板：[bookends-product-seal-waiver.md](./bookends-product-seal-waiver.md)）；工程封板不依赖本手册完成。
