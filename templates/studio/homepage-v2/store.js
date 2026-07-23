/**
 * Travelogue Studio 首页 v2 · 运行时状态 + variant 解析 + DOM 工具。
 *
 * 状态语义对齐 classic 首页五主态（empty / returning / importing 等），
 * v2 使用独立视图层（M21-c 后主入口 GET /）。
 */
import { SS } from "../js/constants.js";

export const STUDIO_DEMO_SHOWCASE_BASE = "/__studio/assets/demo-showcase/";

/** v2 新增 sessionStorage 键（加法；值 `v2`|`classic`，兼容 legacy `v3`）。 */
export const V2_VARIANT_KEY = "travelogue.studio.homepageVariant";
export const V2_THEME_KEY = "travelogue.studio.v2.theme";
export const V2_BENTO_PREVIEW_TRIP_KEY = "travelogue.studio.v2.bentoPreviewTripId";
/** D-13 session：本 tab 内曾选「我的最近一本」（供 D-14 迁移读取）。 */
export const V2_BENTO_TAB_SESSION_KEY = "travelogue.studio.v2.bentoTab";
/** D-13 session：mine Tab 激活时的预览 tripId。 */
export const V2_BENTO_PREVIEW_TRIP_SESSION_KEY = "travelogue.studio.v2.bentoPreviewTripIdSession";
/** D-14 一次性迁移完成标记（localStorage）。 */
export const V2_BENTO_D14_MIGRATED_KEY = "travelogue.studio.v2.bentoD14Migrated";
/** D-14 离线：最近一次成功的 GET /trips 首屏快照（JSON `{ v, trips, total }`）。 */
export const V2_TRIPS_CACHE_KEY = "travelogue.studio.v2.tripsCache";
/** Bump when trips row shape changes (e.g. shelfCoverRelPath). */
export const V2_TRIPS_CACHE_VERSION = 2;
export const V2_THEME_DEFAULT = "mist";

/** v2 首页运行时状态（单一可变源，勿重新赋值绑定）。 */
export const V2 = {
  state: "Loading", // Loading | IdleEmpty | IdleReturning | Importing | FirstSuccess | Failed
  manifest: null,
  demoManifest: null,
  userManifest: null,
  /** GET /trips 行：当前 userManifest 对应的画册（stale / curate CTA）。 */
  userPreviewTrip: null,
  /** D-14：null = 示例作品；非 null = 指定用户画册 tripId。 */
  bentoPreviewTripId: null,
  bentoTab: "demo", // 派生：bentoPreviewTripId ? "mine" : "demo"
  manifestError: false,
  trips: [],
  tripsTotal: 0,
  /** D-14 P3 · 预览选择器已加载的 trips 页（含分页追加） */
  pickerCatalogTrips: [],
  pickerCatalogTotal: 0,
  isOffline: false,
  activeJobId: null,
  layout: "wide", // wide | tablet_landscape | unsupported_*
  layoutTier: "L0", // L0 | L1 | L2 | L3（§12.4）
  _started: false, // 一次性启动门（首次进入支持态加载数据）
  _viewTracked: false, // homepage_view 仅最终态首帧一次（§4.4）
  importShell: "bento", // 方案 A：Import 前壳层恒为 Bento 首屏
  reroute: null, // bootstrap 注入：重新拉 trips 并路由最终态（import 结束/取消后调用）
  onExpand: null, // Lightbox 打开钩子（当前 Bento 未接入）
  theme: V2_THEME_DEFAULT, // sky | classic | dawn | mist | folio | atelier
};

export const V2_THEME_IDS = ["classic", "dawn", "mist", "folio", "atelier"];
export const V2_THEME_LABELS = {
  sky: "清新浅蓝",
  classic: "经典深色",
  dawn: "暖阳珊瑚",
  mist: "雾蓝纸本",
  folio: "纸墨装帧",
  atelier: "木紫文艺",
};
export const V2_THEME_FEATURED = ["mist", "folio", "dawn", "classic"];
export const V2_THEME_MORE = ["atelier", "sky"];
const V2_THEME_ID_SET = new Set(V2_THEME_IDS);

function normalizeTheme(theme) {
  if (theme === "sky") return "sky";
  if (V2_THEME_ID_SET.has(theme)) return theme;
  return V2_THEME_DEFAULT;
}

export function $(id) {
  return document.getElementById(id);
}

export function show(el, visible) {
  if (!el) return;
  el.hidden = !visible;
}

export function setV2SkipLinkTarget(targetId) {
  var skip = document.querySelector(".v2-skip-link");
  if (!skip || !targetId) return;
  skip.setAttribute("href", "#" + targetId);
}

export function isLoopback() {
  var h = location.hostname;
  return h === "127.0.0.1" || h === "localhost" || h === "::1";
}

/** 读取 sessionStorage.activeJobId（v3 共享键，只读）。 */
export function readActiveJobId() {
  try {
    return sessionStorage.getItem(SS.activeJobId) || null;
  } catch (e) {
    return null;
  }
}

/** Holdback variant 归一化（legacy `v3` → `classic`）。 */
export function normalizeHomepageVariant(raw) {
  var v = String(raw || "").trim().toLowerCase();
  if (v === "v2") return "v2";
  if (v === "classic" || v === "v3") return "classic";
  return v || "v2";
}

/** 读取 sessionStorage.homepageVariant（兼容 legacy `v3`）。 */
export function readHomepageVariant() {
  try {
    return normalizeHomepageVariant(sessionStorage.getItem(V2_VARIANT_KEY));
  } catch (e) {
    return "v2";
  }
}

/** 持久化 v2 variant 偏好（非路由依据；holdback 以服务端 cookie/redirect 为准）。 */
export function persistVariant(variant) {
  try {
    sessionStorage.setItem(V2_VARIANT_KEY, normalizeHomepageVariant(variant) || "v2");
  } catch (e) {
    /* ignore */
  }
}

export function readThemePreference() {
  try {
    var raw = localStorage.getItem(V2_THEME_KEY);
    if (!raw) return V2_THEME_DEFAULT;
    return normalizeTheme(raw);
  } catch (e) {
    return V2_THEME_DEFAULT;
  }
}

export function applyTheme(theme) {
  var next = normalizeTheme(theme);
  V2.theme = next;
  try {
    // Wave7：sky 也写 data-v2-theme="sky"（不再靠「无属性」映射 cyan）
    document.documentElement.setAttribute("data-v2-theme", next);
  } catch (e) {
    /* ignore */
  }
  return next;
}

export function persistTheme(theme) {
  var next = normalizeTheme(theme);
  try {
    localStorage.setItem(V2_THEME_KEY, next);
  } catch (e) {
    /* ignore */
  }
  return next;
}

/** 派生 bentoTab（兼容 stale / 遥测 shim）。 */
export function syncDerivedBentoTab() {
  V2.bentoTab = V2.bentoPreviewTripId ? "mine" : "demo";
}

export function readBentoPreviewTripId() {
  try {
    var raw = localStorage.getItem(V2_BENTO_PREVIEW_TRIP_KEY);
    if (!raw) return null;
    var id = String(raw).trim();
    return id || null;
  } catch (e) {
    return null;
  }
}

export function persistBentoPreviewTripId(tripId) {
  try {
    if (!tripId) localStorage.removeItem(V2_BENTO_PREVIEW_TRIP_KEY);
    else localStorage.setItem(V2_BENTO_PREVIEW_TRIP_KEY, String(tripId));
  } catch (e) {
    /* ignore */
  }
}

export function clearBentoPreviewTripId() {
  persistBentoPreviewTripId(null);
}

/** PDG · 删除中 / 刚删 ID（防 reroute 复活 preference）。 */
var _deletingTripIds = Object.create(null);
var _recentlyDeletedTripIds = Object.create(null);

export function markTripDeleting(tripId) {
  if (!tripId) return;
  _deletingTripIds[String(tripId)] = true;
}

export function clearTripDeleting(tripId) {
  if (!tripId) return;
  delete _deletingTripIds[String(tripId)];
}

export function isTripDeleting(tripId) {
  return !!(tripId && _deletingTripIds[String(tripId)]);
}

export function noteTripDeleted(tripId) {
  if (!tripId) return;
  var id = String(tripId);
  _recentlyDeletedTripIds[id] = true;
  delete _deletingTripIds[id];
}

export function isTripDeleteBlocked(tripId) {
  if (!tripId) return false;
  var id = String(tripId);
  return !!(_deletingTripIds[id] || _recentlyDeletedTripIds[id]);
}

/** @returns {{ trips: object[], total: number } | null} */
export function readTripsCache() {
  try {
    var raw = localStorage.getItem(V2_TRIPS_CACHE_KEY);
    if (!raw) return null;
    var data = JSON.parse(raw);
    if (!data || data.v !== V2_TRIPS_CACHE_VERSION || !Array.isArray(data.trips)) return null;
    return {
      trips: data.trips,
      total: typeof data.total === "number" ? data.total : data.trips.length,
    };
  } catch (e) {
    return null;
  }
}

export function persistTripsCache(trips, total) {
  try {
    var payload = {
      v: V2_TRIPS_CACHE_VERSION,
      trips: (trips || []).slice(),
      total: typeof total === "number" ? total : (trips || []).length,
    };
    localStorage.setItem(V2_TRIPS_CACHE_KEY, JSON.stringify(payload));
  } catch (e) {
    /* ignore */
  }
}
