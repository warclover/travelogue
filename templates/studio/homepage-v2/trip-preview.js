/**
 * 首页 v2 · 用户最近画册 Bento 预览（PRD §4.4 · 最近一本单卡）。
 */
import { V2 } from "./store.js";
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

/** 当前 Bento 主预览 manifest：有用户画册时用最近一本，否则示例。 */
export function activeBentoManifest() {
  if (V2.userManifest) return V2.userManifest;
  return V2.demoManifest;
}

/**
 * trips 加载后拉取最近一本预览 manifest，并刷新 Bento 面。
 * @param {import("./trips-client.js").ShelfTrip[]} trips
 * @param {{ force?: boolean }} [opts]
 */
export function refreshUserBentoPreview(trips, opts) {
  opts = opts || {};
  var primary = pickBentoPreviewTrip(trips);
  if (!primary) {
    V2.userManifest = null;
    V2.userPreviewTrip = null;
    V2.manifest = activeBentoManifest();
    return import("./bento-stale.js").then(function (stale) {
      stale.syncBentoStaleBar();
      return null;
    });
  }

  var candidates = pickRecentUserTrips(trips);
  var ordered = [primary].concat(
    candidates.filter(function (t) { return t.tripId !== primary.tripId; })
  );
  var matchedTrip = null;

  function tryAt(i) {
    if (i >= ordered.length) return Promise.resolve(null);
    var trip = ordered[i];
    return loadTripBentoPreview(trip.tripId, {
      updatedAt: trip.updatedAt,
      force: !!opts.force,
    }).then(function (manifest) {
      if (manifest) {
        manifest.tripId = manifest.tripId || trip.tripId;
        matchedTrip = trip;
        return manifest;
      }
      return tryAt(i + 1);
    });
  }

  return tryAt(0).then(function (manifest) {
    V2.userManifest = manifest || null;
    V2.userPreviewTrip = manifest ? matchedTrip : null;
    V2.manifest = activeBentoManifest();
    var chain = Promise.resolve();
    if (V2.manifest) {
      chain = import("./bento.js").then(function (bento) {
        bento.renderBentoSurface(V2.manifest);
      });
    }
    return chain.then(function () {
      return import("./bento-stale.js").then(function (stale) {
        stale.syncBentoStaleBar();
        return V2.userManifest;
      });
    });
  });
}
