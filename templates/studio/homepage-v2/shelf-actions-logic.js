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
      label: "更新长图",
      primary: true,
      focusLongshot: true,
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
