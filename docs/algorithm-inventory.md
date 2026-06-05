# Travelogue 算法清单附录

| 属性 | 内容 |
|------|------|
| **版本** | v1.0 |
| **日期** | 2026-06-04 |
| **关联** | [ARCHITECTURE-OVERVIEW.md](./ARCHITECTURE-OVERVIEW.md) · [ADR-007](./adr/007-native-clustering.md) |

本文档为算法清单的**可检索附录**：§1 为自研启发式与可选依赖对照；§2 为「文件路径 → 公开/核心函数」索引（`_` 前缀内部函数仅列关键入口相关项）。

---

## §1 自研启发式 vs 可选依赖对照

**图例**

| 列 | 含义 |
|----|------|
| **实现** | `native` = 纯 Python/规则，无深度学习；`hybrid` = 自研编排 + 第三方算子；`external` = 主要依赖外部库/服务 |
| **默认可用** | 出厂默认路径是否**不装**可选 extra 也能跑通 |
| **安装** | `pip install -e .` 基座；extras 见 `pyproject.toml` / 文档 |

### 1.1 摄取与媒体（Agent 0）

| 能力 | 实现 | 默认可用 | 可选依赖 | 配置/开关 |
|------|------|----------|----------|-----------|
| MD5 内容指纹去重 | native | ✅ | — | ingest `dedupe` |
| dHash + 汉明距离近重复 | native | ✅ | PIL | `ingest.phash_*` |
| 边缘方差清晰度 | native | ✅ | PIL | 写入 `quality.sharpness` |
| 连拍分组（时间间隔） | native | ✅ | — | `ingest.burst_seconds` |
| sRGB 亮度 / 主色 | native | ✅ | PIL | ingest 色彩回填 |
| CIE Lab ΔE76 | native | ✅ | — | 排版打分用 |
| 三角窗 / 色度偏好 | native | ✅ | — | 封面打分 |
| 中心裁切 / WebP 衍生 | native | ✅ | PIL | `image_ops` |
| 媒体类型启发式 | native | ✅ | — | `media_classify` |
| 归档日期离群标记 | native | ✅ | — | `refine_archive_media_class` |
| Haar 人脸检测 | hybrid | ✅（无 OpenCV 则跳过） | `opencv-python` | ingest 人脸/焦点 |
| GPS 城市反查 | external | ✅（关则跳过） | 网络 + Nominatim | `geocode.enabled` |
| 视频裁切/H.264 | external | 含视频时需要 | 系统 `ffmpeg` / `ffprobe` | ingest 视频路径 |

### 1.2 分段与聚类（Agent 1 · ClusteringLayer）

| 能力 | 实现 | 默认可用 | 可选依赖 | 配置/开关 |
|------|------|----------|----------|-----------|
| Haversine 距离 | native | ✅ | — | `geo_events` |
| 时间间隙 / 自适应 p75·p90 阈值 | native | ✅ | — | `curation.geo.event_gap_mode` |
| 地理邻近切分 + 事件合并 | native | ✅ | — | `proximity_km` 等 |
| 日历分段 date_fallback | native | ✅ | — | `time_segments` |
| 按日分桶 / 小桶合并 / 章数 cap | native | ✅ | — | `bucket_planning` · PRD 3–5 章 |
| Geo 段 merge + cap 3–5 | native | ✅ | — | `clustering_buckets` |
| Geo×Scene 子分段 | native | ✅ | 需 scene 标签时依赖 vision | `scene_subsegments` |
| 启发式 8 维 embedding | native | ✅ | numpy | CLIP 不可用回退 |
| OpenCLIP ViT-B/32 embedding | external | ❌（默认关 vision） | `pip install -e '.[clip]'` · torch · open_clip | `vision.enabled` |
| CLIP 零样本 subjectClass | external | ❌ | 同上 | 与 embedding 同批 |
| L2 归一化 + medoid | native | ✅ | numpy | `scene_clusters` |
| HDBSCAN 场景聚类 | external | ❌ | `scikit-learn` · numpy | `curation.scene.algorithm` |
| DBSCAN 回退 | external | ❌ | sklearn | HDBSCAN 失败时 |
| 嵌入 NPZ 缓存 / 增量 | native | ✅ | numpy | `.cluster-cache/` |
| 并行 embed batch | hybrid | ❌ | torch（CLIP 时） | `vision.parallel_embed` |

### 1.3 策展与排版（Agent 1 · Curate）

| 能力 | 实现 | 默认可用 | 可选依赖 | 配置/开关 |
|------|------|----------|----------|-----------|
| 五拍叙事弧 / CV 推断 profile | native | ✅ | — | `curation.arc_mode` |
| 封面·英雄多因子打分 | native | ✅ | — | `curate_scoring` |
| 三分法 / 饱和度封面加成 | native | ✅ | — | `curate_scoring` |
| 桶内排序（burst·scene run·时间） | native | ✅ | — | `cluster_run_sort` |
| 贪心逐屏规划 legacy | native | ✅ | — | `screen_planner` |
| Beam Search 日桶重排 | native | ❌ | — | `scoring.enabled` + `beam_width` |
| 多维加权 layout 打分 | native | ✅ | — | `layout_scoring` |
| Mosaic 窗口枚举 + 打分 | native | ✅ | — | `mosaic/*` · Phase 15 |
| 搜索预算 / 超时 | native | ✅ | — | `search_budget` |
| 降级 force legacy | native | ✅ | — | `degradation` |
| 意图关键词峰值章 | native | ✅ | — | `intent_hints` |
| 人脸模板 1-NN 余弦 | hybrid | ✅ | OpenCV 提脸；无则 face_count 代理 | `cohort` / featured subjects |
| 轻量 face_crop_embedding v1 | native | ✅ | numpy | `face_embed` |

### 1.4 质量闸口（Phase 9）

| 能力 | 实现 | 默认可用 | 可选依赖 | 配置/开关 |
|------|------|----------|----------|-----------|
| 分位数模糊阈值 P2 | native | ✅ | — | `photo_cull` |
| 规则 cullScore + 配额 | native | ✅ | — | `cull.mode=rules` |
| 重复组 / 曝光极端规则 | native | ✅ | — | `photo_cull` |
| ToPIQ-NR 美学分 | external | ❌ | `pyiqa` · torch（建议 GPU） | `cull.mode=ml/auto` |

### 1.5 叙事与其它

| 能力 | 实现 | 默认可用 | 可选依赖 | 配置/开关 |
|------|------|----------|----------|-----------|
| 规则叙事 stub | native | ✅ | — | `narrate.py` |
| LLM 叙事 | external | ❌ | API Key · HTTP | `llm` 配置 |
| Jaccard 分段验收 | native | ✅ | — | `cluster_eval` · 测试 fixture |
| DOM / golden 布局回归 | native | ✅ | Playwright（CI） | `render/*` |

### 1.6 推荐安装矩阵（按场景）

| 场景 | 建议安装 |
|------|----------|
| **最小可运行**（geo + legacy 排版） | 基座 + PIL |
| **P3-Lite 聚类** | 基座（无需 torch） |
| **P3-Full 场景簇** | `.[clip]` + sklearn + numpy |
| **Phase 9 ML 筛图** | pyiqa + torch（CUDA 可选） |
| **人脸 / cohort** | opencv-python |
| **含视频 trip** | ffmpeg + ffprobe |

---

## §2 文件路径 → 函数索引

仅列**算法相关**模块；编排类（`curate.py` 管线粘合、`clustering.py` 层调度）见 §2.8。

### 2.1 `travelogue/media/`

| 文件 | 函数 | 算法摘要 |
|------|------|----------|
| `phash.py` | `dhash_hex` | dHash 64-bit |
| | `hamming_distance_hex` | 汉明距离 |
| | `is_near_duplicate` | 阈值判重 |
| `sharpness.py` | `sharpness_score` | 边缘滤波方差 |
| `color_metrics.py` | `mean_luma` | sRGB 相对亮度 |
| | `dominant_tone_hex` | 缩略图平均色 |
| | `delta_e_cie76` | CIE76 ΔE |
| | `triangular_score` | 三角窗评分 |
| | `dominant_tone_chroma_score` | Lab 色度偏好 |
| `subject_detect.py` | `detect_faces_in_image` | Haar 多尺度 |
| | `analyze_subject` | 人脸→焦点/显著框 |
| `face_embed.py` | `l2_normalize` | L2 归一 |
| | `cosine_similarity` | 余弦相似度 |
| | `face_crop_embedding` | 64×64 确定性嵌入 |
| | `mean_embedding` | 模板平均向量 |
| `geocode.py` | `reverse_geocode_city` | Nominatim + 缓存 |
| `ingest.py` | `content_signature` | MD5 文件摘要 |
| | `_find_phash_asset_index` | phash 去重索引 |
| | `_is_burst_duplicate` | 连拍时间去重 |
| | `ingest_into_trip` | 摄取主入口 |

### 2.2 `travelogue/curation/` · 分段与聚类

| 文件 | 函数 | 算法摘要 |
|------|------|----------|
| `geo_events.py` | `haversine_km` | 大圆距离 |
| | `gps_coverage_ratio` | GPS 覆盖率 |
| | `_adaptive_gap_threshold_hours` | 间隙分布自适应 |
| | `_time_split_groups` | 时间切 stay |
| | `_geo_split_group` | 距离切分 |
| | `_merge_event_chunks` | 事件合并 |
| | `detect_geo_events` | **Geo 事件主入口** |
| `time_segments.py` | `cluster_time_segments` | 日历/城市规则分段 |
| | `parse_asset_date` | 拍摄日期解析 |
| `clustering_buckets.py` | `merge_small_geo_events` | 小事件合并 |
| | `cap_geo_segments` | 3–5 章 cap |
| | `build_buckets_from_clustering` | 聚类→桶 |
| `scene_subsegments.py` | `split_geo_segment_by_scene` | 场景 run 切子段 |
| | `apply_scene_subsegments` | 写回 trip |
| `scene_clusters.py` | `_normalize_embedding_matrix` | L2 行归一 |
| | `_cluster_labels` | HDBSCAN/DBSCAN |
| | `_pick_medoid` | 簇 medoid |
| | `compute_scene_clusters` | **场景聚类主入口** |
| | `assign_scene_cluster_fields` | 写 asset 字段 |
| `cluster_eval.py` | `segment_jaccard` | Jaccard |
| | `geo_segment_agreement_rate` | Golden 一致率 |
| `cluster_run_sort.py` | `sort_bucket_asset_ids_run_aware` | burst/scene/时间排序 |

### 2.3 `travelogue/vision/`

| 文件 | 函数 | 算法摘要 |
|------|------|----------|
| `clip_encoder.py` | `_heuristic_vector` | 8 维启发式向量 |
| | `ClipEncoder.embed_assets` | CLIP 或启发式批量嵌入 |
| | `ClipEncoder._subject_class_for` | 零样本 argmax |
| | `get_clip_encoder` | 单例编码器 |
| `cache.py` | `prepare_scene_embeddings` | 缓存计划+嵌入 |
| | `compute_change_ratio` | 增量变更比例 |
| | `merge_embedding_vectors` | 向量合并 |

### 2.4 `travelogue/curation/` · 排版与搜索

| 文件 | 函数 | 算法摘要 |
|------|------|----------|
| `bucket_planning.py` | `group_assets_by_day` | 按日分桶 |
| | `normalize_bucket_counts` | 章数归一 |
| | `merge_small_buckets` | 小桶合并 |
| | `group_assets_by_segments` | 段→桶 |
| `arc_patterns.py` | `infer_arc_profile` | CV→flat/moderate/dynamic |
| | `arc_segments_for_trip` | 章→弧段标签 |
| | `arc_pattern_bonus` | 弧-版式匹配加分 |
| `burst_utils.py` | `burst_group_map` | 连拍图构建 |
| | `time_near_sequential` | 时间链判定 |
| | `sort_ids_by_sharpness` | 清晰度排序 |
| `layout_scoring.py` | `score_aspect_match` | 纵横比匹配 |
| | `score_temporal_coherence` | 时间连贯 |
| | `score_tone_continuity` | ΔE 色调 |
| | `score_burst_integrity` | 连拍完整 |
| | `score_gravity_balance` | 视觉重心连续 |
| | `score_screen_plan` | 全章加权总分 |
| | `rank_screens` | 候选排序 |
| `layout_search.py` | `maybe_replan_chapters` | beam 重排入口 |
| `search_budget.py` | `SearchBudget` | 超时/评估配额 |
| `screen_planner.py` | `_plan_one_screen` | 贪心单屏 |
| | `plan_screens_for_chapter` | **章内组屏主入口** |
| | `attach_screens_day_buckets` | 日桶附屏 |
| `curate_scoring.py` | `cover_score` / `pick_cover_asset_id` | 封面打分选型 |
| | `pick_chapter_hero` | 章英雄图 |
| | `sort_bucket_asset_ids` | 桶内排序 |
| `degradation.py` | `assess_degradation` | legacy 降级判定 |
| `cohort_faces.py` | `build_subject_templates` | 种子脸模板 |
| | `_match_present_subjects` | 1-NN 余弦匹配 |
| | `apply_cohort_tags` | 写 cohort 元数据 |
| `media_classify.py` | `classify_media_class` | 截图/缩略图启发式 |
| `photo_cull.py` | `run_photo_cull` | **质量闸口主入口** |
| `photo_cull_ml.py` | `apply_aesthetic_scores` | pyiqa 美学回填 |

### 2.5 `travelogue/curation/mosaic/`

| 文件 | 函数 | 算法摘要 |
|------|------|----------|
| `candidates.py` | `generate_window_candidates` | 滑动窗候选 |
| | `generate_five_candidates` | 5 图窗候选 |
| `compose.py` | `score_window_candidates` | 窗内打分 |
| | `pick_best_window` | 最优窗 |
| `scorer.py` | `score_candidate` | Mosaic 多维惩罚/加分 |
| `search.py` | `replan_day_buckets_beam` | **Beam Search 主入口** |
| `builders.py` | `build_screen` | 候选→screen 结构 |
| | `try_order_for_pattern` | 槽位排列 |
| `hook.py` | `try_mosaic_window` | 规划期 Mosaic 挂钩 |
| `trip.py` | `compose_trip` | 全 trip Mosaic 合成 |
| `replan.py` | `replan_screen` | 单屏局部重排 |
| `selfheal.py` | `try_self_heal_pick` | 失败收紧重试 |

### 2.6 评估与其它

| 文件 | 函数 | 算法摘要 |
|------|------|----------|
| `asset_quality.py` | `partition_low_resolution_assets` | 低分辨率分区 |
| | `apply_layout_eligibility_marks` | 可排版标记 |
| `intent_hints.py` | `peak_chapter_hints` | 用户备注峰值章 |
| `clustering.py` | `run_clustering_layer` | **聚类层主入口** |
| `curate.py` | `run_curate` | **策展主入口** |

### 2.7 服务层（非排版核心）

| 文件 | 函数 | 说明 |
|------|------|------|
| `services/llm_narrate.py` | — | LLM 调用（外部 API） |
| `services/narrate.py` | — | 规则叙事 |
| `render/golden_regression.py` | — | 布局 golden 对比 |
| `render/dom_compare.py` | — | DOM 结构对比 |

### 2.8 管线入口速查

```
ingest_into_trip          → media/ingest.py
run_clustering_layer      → curation/clustering.py
  ├ detect_geo_events     → geo_events.py
  └ compute_scene_clusters→ scene_clusters.py (+ vision/cache.py)
run_curate                → curation/curate.py
  ├ run_photo_cull        → photo_cull.py
  ├ plan_screens_*        → screen_planner.py
  └ maybe_replan_chapters → layout_search.py → mosaic/search.py
```

---

## §3 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-04 | 初版：§1 依赖对照 + §2 函数索引 |
