/**
 * 首页 v2 · 用户最近画册 Bento 预览（PRD v2.0.5 · 方案 B′）。
 */
import { isDemoTrip } from "../js/constants.js";
import { isValidManifest } from "./manifest.js";

/** @typedef {import("./trips-client.js").ShelfTrip} ShelfTrip */

var _previewCache = {
  tripId: null,
  updatedAt: null,
  manifest: null,
};

export function clearBentoPreviewCache() {
  _previewCache.tripId = null;
  _previewCache.updatedAt = null;
  _previewCache.manifest = null;
}

/** 最近编辑的非 demo 画册（trips 已按 updatedAt 降序）。 */
export function pickRecentUserTrip(trips) {
  return pickBentoPreviewTrip(trips);
}

/** 最近编辑的非 demo 画册列表（updatedAt 降序）。 */
export function pickRecentUserTrips(trips) {
  return (trips || []).filter(function (t) { return !isDemoTrip(t); });
}

/**
 * Bento「最近一本」：严格取 updatedAt 最新的非 demo 画册。
 *
 * 说明：
 * - 旧逻辑会优先 hasLongshotExport，可能把焦点固定在历史老画册，
 *   导致新建游记后「最近一本」不更新。
 * - 实际预览可用性由 refreshUserBentoPreview 的候选回退链保障。
 */
export function pickBentoPreviewTrip(trips) {
  var userTrips = pickRecentUserTrips(trips);
  if (!userTrips.length) return null;
  return userTrips[0];
}

/**
 * @param {string} tripId
 * @param {{ updatedAt?: number, force?: boolean }} [opts]
 * @returns {Promise<object|null>}
 */
export function loadTripBentoPreview(tripId, opts) {
  opts = opts || {};
  if (!tripId) return Promise.resolve(null);
  if (
    !opts.force
    && _previewCache.tripId === tripId
    && _previewCache.updatedAt != null
    && opts.updatedAt != null
    && _previewCache.updatedAt === opts.updatedAt
    && _previewCache.manifest
  ) {
    return Promise.resolve(_previewCache.manifest);
  }
  return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/bento-preview?t=" + String(Date.now()))
    .then(function (r) {
      if (!r.ok) return null;
      return r.json();
    })
    .then(function (data) {
      if (!data || !data.ok) return null;
      var m = Object.assign({}, data);
      delete m.ok;
      m.source = "user";
      if (!isValidManifest(m)) return null;
      _previewCache.tripId = tripId;
      _previewCache.updatedAt = opts.updatedAt != null ? opts.updatedAt : null;
      _previewCache.manifest = m;
      return m;
    })
    .catch(function () { return null; });
}
