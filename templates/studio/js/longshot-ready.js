/**
 * D5 / FE-DFX-30 · 导出成功后「分享图已就绪」会话标记（预览页与首页书架共用）。
 */

export var LONGSHOT_READY_KEY = "travelogue.studio.longshotReady.v1";
export var LONGSHOT_READY_TTL_MS = 24 * 60 * 60 * 1000;

/**
 * @param {string} tripId
 * @param {{ store?: Storage }} [opts]
 */
export function markLongshotReady(tripId, opts) {
  opts = opts || {};
  var id = String(tripId || "").trim();
  if (!id) return false;
  var store = opts.store || (typeof sessionStorage !== "undefined" ? sessionStorage : null);
  if (!store) return false;
  var map = {};
  try {
    map = JSON.parse(store.getItem(LONGSHOT_READY_KEY) || "{}") || {};
  } catch (_e) {
    map = {};
  }
  if (typeof map !== "object" || Array.isArray(map)) map = {};
  map[id] = { ts: Date.now(), until: Date.now() + LONGSHOT_READY_TTL_MS };
  try {
    store.setItem(LONGSHOT_READY_KEY, JSON.stringify(map));
    return true;
  } catch (_w) {
    return false;
  }
}

/**
 * @param {string} tripId
 * @param {{ store?: Storage, now?: number }} [opts]
 */
export function isLongshotReady(tripId, opts) {
  opts = opts || {};
  var id = String(tripId || "").trim();
  if (!id) return false;
  var store = opts.store || (typeof sessionStorage !== "undefined" ? sessionStorage : null);
  if (!store) return false;
  var now = typeof opts.now === "number" ? opts.now : Date.now();
  var map = {};
  try {
    map = JSON.parse(store.getItem(LONGSHOT_READY_KEY) || "{}") || {};
  } catch (_e) {
    return false;
  }
  var row = map[id];
  if (!row || typeof row !== "object") return false;
  var until = Number(row.until || 0);
  if (!until || now > until) {
    try {
      delete map[id];
      store.setItem(LONGSHOT_READY_KEY, JSON.stringify(map));
    } catch (_c) {}
    return false;
  }
  return true;
}
