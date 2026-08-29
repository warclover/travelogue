/**
 * 首页 v2 · 书架 resume 区 CTA 纯逻辑（无 DOM · node --test）。
 *
 * @typedef {object} ShelfResumeAction
 * @property {"longshot"|"algorithm"|"open"} kind
 * @property {string} label
 * @property {boolean} primary
 * @property {boolean} [focusLongshot]
 * @property {boolean} [triggerCurate]
 */

export {
  LONGSHOT_READY_KEY,
  LONGSHOT_READY_TTL_MS,
  markLongshotReady,
  isLongshotReady,
} from "../js/longshot-ready.js";

import { isLongshotReady } from "../js/longshot-ready.js";

/**
 * @param {{ longshotStale?: boolean, algorithmStale?: boolean }} trip
 * @returns {ShelfResumeAction[]}
 */
export function shelfResumeActions(trip) {
  trip = trip || {};
  var actions = [];
  if (trip.longshotStale) {
    actions.push({
      kind: "longshot",
      label: "按原配方重出",
      primary: true,
      reexportRecipe: true,
    });
  }
  if (trip.algorithmStale) {
    actions.push({
      kind: "algorithm",
      label: "重新排版",
      primary: !trip.longshotStale,
      triggerCurate: true,
    });
  }
  actions.push({
    kind: "open",
    label: "打开预览",
    primary: !trip.longshotStale && !trip.algorithmStale,
  });
  return actions;
}

/**
 * T-M4-03 · 角标矩阵：resume 条已有「更新长图」主 CTA 时，卡片长图角标降级（隐藏）。
 * 多本同时 stale 时仅最高优先级一本显示角标（opts.priorityLongshotTripId），避免满屏「需更新」。
 * @param {{ longshotStale?: boolean, tripId?: string }} trip
 * @param {{ resumeTripId?: string|null, priorityLongshotTripId?: string|null }} [opts]
 * @returns {boolean}
 */
export function shelfShowCoverLongshotBadge(trip, opts) {
  trip = trip || {};
  opts = opts || {};
  if (!trip.longshotStale) return false;
  var resumeId = opts.resumeTripId;
  if (resumeId && trip.tripId && String(resumeId) === String(trip.tripId)) {
    return false;
  }
  var priorityId = opts.priorityLongshotTripId;
  if (priorityId && trip.tripId && String(priorityId) !== String(trip.tripId)) {
    return false;
  }
  return true;
}

/**
 * 在书架列表中挑一本优先展示「分享图需更新」角标：跳过 resume 本，取列表中首本 longshotStale。
 * @param {Array<{ tripId?: string, longshotStale?: boolean }>} trips
 * @param {{ resumeTripId?: string|null }} [opts]
 * @returns {string|null}
 */
export function shelfPriorityLongshotTripId(trips, opts) {
  opts = opts || {};
  var resumeId = opts.resumeTripId != null ? String(opts.resumeTripId) : "";
  var list = Array.isArray(trips) ? trips : [];
  for (var i = 0; i < list.length; i++) {
    var t = list[i];
    if (!t || !t.longshotStale || !t.tripId) continue;
    if (resumeId && String(t.tripId) === resumeId) continue;
    return String(t.tripId);
  }
  return null;
}

/**
 * D5 · 非 stale 且会话内刚导出成功 → 显示「分享图已就绪」
 * @param {{ longshotStale?: boolean, tripId?: string }} trip
 * @param {{ store?: Storage, now?: number }} [opts]
 */
export function shelfShowCoverReadyBadge(trip, opts) {
  trip = trip || {};
  if (trip.longshotStale) return false;
  return isLongshotReady(trip.tripId, opts);
}

/**
 * Bento「我的画册」Tab 是否应展示算法过期提示条。
 * @param {{ algorithmStale?: boolean, longshotStale?: boolean }} trip
 * @returns {boolean}
 */
export function shouldShowBentoStaleBar(trip) {
  return !!(trip && trip.algorithmStale);
}

/**
 * @param {{ staleHint?: string, staleHints?: string[] }} trip
 * @returns {string}
 */
export function bentoStaleMessage(trip) {
  trip = trip || {};
  if (trip.staleHint) return String(trip.staleHint);
  var hints = trip.staleHints;
  if (Array.isArray(hints) && hints.length) return String(hints[0]);
  return "这本画册可以用新版式重新排版";
}
