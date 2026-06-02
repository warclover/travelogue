/**
 * 首页 v2 · 用户最近画册 Bento 预览（PRD v2.0.5 · 方案 B′）。
 */
import { isDemoTrip } from "../js/constants.js";
import { isValidManifest } from "./manifest.js";

/** 最近编辑的非 demo 画册（trips 已按 updatedAt 降序）。 */
export function pickRecentUserTrip(trips) {
  return (trips || []).find(function (t) { return !isDemoTrip(t); }) || null;
}

/** 最近编辑的非 demo 画册列表（updatedAt 降序）。 */
export function pickRecentUserTrips(trips) {
  return (trips || []).filter(function (t) { return !isDemoTrip(t); });
}

/**
 * @param {string} tripId
 * @returns {Promise<object|null>}
 */
export function loadTripBentoPreview(tripId) {
  if (!tripId) return Promise.resolve(null);
  return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/bento-preview")
    .then(function (r) {
      if (!r.ok) return null;
      return r.json();
    })
    .then(function (data) {
      if (!data || !data.ok) return null;
      var m = Object.assign({}, data);
      delete m.ok;
      m.source = "user";
      return isValidManifest(m) ? m : null;
    })
    .catch(function () { return null; });
}
