# FRP · Dogfood 目视清单（AC-FRP-D1–D3）

| 属性 | 内容 |
|------|------|
| **关联** | [ACCEPTANCE-FOOD-ROLE-POLICY.md](../ACCEPTANCE-FOOD-ROLE-POLICY.md) · [PRD-FOOD-ROLE-POLICY-V1.md](../PRD-FOOD-ROLE-POLICY-V1.md) |
| **自动基线** | [food-role-policy.fixture.json](./food-role-policy.fixture.json)（fixture 量化对比 · 已绿） |
| **Fixture** | [trip.frp_mixed_travel_food.json](../../schemas/fixtures/trip.frp_mixed_travel_food.json) |
| **日期** | 2026-07-24 |

---

## 0. 一键自动（工程）

```powershell
python scripts/food_role_policy_acceptance.py --write-fixture --write docs/acceptance-records/food-role-policy.fixture.json
```

Fixture 对比预期（已入库）：

| 指标 | Legacy（近似 FRP 前） | FRP 默认 |
|------|----------------------|----------|
| 封面 | 高分美食 `f_hero` | 非美食风景 |
| 高光池 | 含美食 | 不含美食 |
| 单张美食屏 | 更多 | 更少 |
| 同餐段 | 易拆散 | 聚成 food-grid |

---

## 1. 真人 trip 目视（产品 · 待签）

选 1 本本地「旅行 + 美食混拍」相册，re-curate 后勾选：

| ID | 检查项 | 结果 |
|----|--------|------|
| **D1** | 记录 tripId；对比封面 / 单张美食屏数 / food-grid 数（可附截图） | ☐ |
| **D2** | 封面第一印象是地方/人/氛围，不是菜单 | ☐ |
| **D3** | 同桌菜以拼图出现，不逐道全幅刷屏 | ☐ |

建议把对比 JSON 另存为：

`docs/acceptance-records/food-role-policy.<trip-id>.json`

---

## 2. 签字

| 角色 | 结果 | 日期 | 备注 |
|------|------|------|------|
| 工程（fixture 自动） | ✅ | 2026-07-24 | `food-role-policy.fixture.json` status=passed |
| 产品（真人 D1–D3） | ☐ | | |
