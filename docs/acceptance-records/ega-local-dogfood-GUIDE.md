# EGA · 本机狗粮 GUIDE

| 属性 | 内容 |
|------|------|
| **对应** | [PRD-EQUAL-GRID-ADMISSION-V1.md](../PRD-EQUAL-GRID-ADMISSION-V1.md) · [ACCEPTANCE](../ACCEPTANCE-EQUAL-GRID-ADMISSION-V1.md) |
| **DOC-STATUS** | **active** |
| **更新日期** | 2026-08-04 |

---

## 1. 目的

验证等权宫 **准入** 修复：同分镜全横 burst 可竞争；非强制出宫格；不回潮假切条；电影峰路径不回退。

---

## 2. 册表

| 册 | 角色 | 关注 |
|----|------|------|
| `trips/demo-0ebda73294` | **主锚点** | 原 0×L4/L6；四横 hero-70；3:2 同分镜 |
| `trips/demo-2019` | MEGC 回归 | 16:9 L4 仍可出现；不因 EGA 回退 |

---

## 3. 步骤（M1）

1. 确认 `mosaic.equal_grid_admission.enabled=true`（默认）。  
2. 备份或记下锚点册当前 pattern 直方图。  
3. 重排：

```powershell
python -m travelogue layout trips/demo-0ebda73294 --layout auto --web-layout screens --render --no-validate
```

4. 统计：

```powershell
python -c "import json,collections; t=json.load(open(r'trips/demo-0ebda73294/trip.json',encoding='utf-8')); c=collections.Counter(s.get('patternId') for ch in t['chapters'] for s in ch.get('screens') or []); print(c['screen-landscape-4'], c['screen-landscape-6'], c['screen-mosaic-4-hero-70-sidebar'])"
```

5. 打开 `curation.mosaicDecisionLog`：原 size=4 窗对 `landscape-4` 的 `rejectedTemplates` 是否仍含 hard `shot_group_anti_slice` / `near_scene_clone`。  
6. 视觉扫：四宫是否自然；是否出现假切条。  
7. 填记录（可复制下方模板到 `ega-dogfood-YYYY-MM-DD.md`）。

### OFF 对照

```yaml
mosaic:
  equal_grid_admission:
    enabled: false
```

重排后硬拒应回潮（AC-04 成册级可选）。

---

## 4. 步骤（M2 追加）

- 查 size=6 probe：`egaEqualSixKept` / 是否出现对 `landscape-6` 的评估。  
- 无主次窗：hero-70 vs L4 比分是否符合 AC-07 精神。

---

## 5. 盲评四问

见 PRD §8.1。每问记 Pass / Fail / 持平。

---

## 6. 记录模板

```markdown
# EGA 狗粮 · YYYY-MM-DD

| 项 | 值 |
|----|-----|
| 分支 / commit | |
| EGA enabled | true |
| 册 | demo-0ebda73294 |

## 直方图

| pattern | before | after |
|---------|--------|-------|
| landscape-4 | 0 | |
| landscape-6 | 0 | |
| hero-70 | | |

## AC-05

- [ ] A 成册 ≥1 L4
- [ ] B 进池无 hard 拒（说明）

## 四问

1. …
2. …
3. …
4. …

## 结论

Go / Hold / 回滚
```
