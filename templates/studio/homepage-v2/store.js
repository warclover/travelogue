/**
 * Travelogue Studio 首页 v2 · 运行时状态 + variant 解析 + DOM 工具。
 *
 * 状态语义对齐 v3 js/state.js（五主态 + Failed/Offline），但 v2 使用独立
 * 视图层（GET /v2 专用 DOM），不复用 v3 navigation.js 的渲染分支。
 */
import { SS } from "../js/constants.js";

export const STUDIO_DEMO_SHOWCASE_BASE = "/__studio/assets/demo-showcase/";

/** v2 新增 sessionStorage 键（加法，不改 v3 既有键形状）。 */
export const V2_VARIANT_KEY = "travelogue.studio.homepageVariant";
export const V2_THEME_KEY = "travelogue.studio.v2.theme";
export const V2_THEME_DEFAULT = "sky";

/** v2 首页运行时状态（单一可变源，勿重新赋值绑定）。 */
export const V2 = {
  state: "Loading", // Loading | IdleEmpty | IdleReturning | Importing | FirstSuccess | Failed
  manifest: null,
  demoManifest: null,
  userManifest: null,
  bentoTab: "demo", // demo | mine（方案 B′）
  manifestError: false,
  trips: [],
  tripsTotal: 0,
  isOffline: false,
  activeJobId: null,
  layout: "wide", // wide | tablet_landscape | unsupported_*
  layoutTier: "L0", // L0 | L1 | L2 | L3（§12.4）
  _started: false, // 一次性启动门（首次进入支持态加载数据）
  _viewTracked: false, // homepage_view 仅最终态首帧一次（§4.4）
  importShell: "bento", // 方案 A：Import 前壳层恒为 Bento 首屏
  reroute: null, // bootstrap 注入：重新拉 trips 并路由最终态（import 结束/取消后调用）
  onExpand: null, // Lightbox 打开钩子（当前 Bento 未接入）
  theme: V2_THEME_DEFAULT, // sky | classic | dawn | mint | navy | olive | fjord | sage | taupe | grove
};

const V2_THEME_IDS = new Set([
  "classic",
  "dawn",
  "mint",
  "navy",
  "olive",
  "fjord",
  "sage",
  "taupe",
  "grove",
]);

function normalizeTheme(theme) {
  if (theme === "sky") return "sky";
  if (V2_THEME_IDS.has(theme)) return theme;
  return "sky";
}

export function $(id) {
  return document.getElementById(id);
}

export function show(el, visible) {
  if (!el) return;
  el.hidden = !visible;
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

/** 持久化 v2 variant 偏好（非路由依据；holdback 以服务端 cookie/redirect 为准）。 */
export function persistVariant(variant) {
  try {
    sessionStorage.setItem(V2_VARIANT_KEY, variant || "v2");
  } catch (e) {
    /* ignore */
  }
}

export function readThemePreference() {
  try {
    return normalizeTheme(localStorage.getItem(V2_THEME_KEY));
  } catch (e) {
    return V2_THEME_DEFAULT;
  }
}

export function applyTheme(theme) {
  var next = normalizeTheme(theme);
  V2.theme = next;
  try {
    if (next === "sky") {
      document.documentElement.removeAttribute("data-v2-theme");
    } else {
      document.documentElement.setAttribute("data-v2-theme", next);
    }
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
