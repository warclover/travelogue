/**
 * 首页 v2 · 用户画册 Bento 预览（D-14 · 可指定任意 tripId）。
 */
import { isDemoTrip } from "../js/constants.js";
import { isValidManifest } from "./manifest.js";
import { V2 } from "./store.js";
import { fetchTripsPage, SHELF_PAGE_SIZE } from "./trips-client.js";

/** @typedef {import("./trips-client.js").ShelfTrip} ShelfTrip */

var _previewCache = {
  tripId: null,
  updatedAt: null,
  manifest: null,
};

/** 已知坏数据：carousel 页 URL 重复（旧版 bento-preview）。 */
function carouselHasDuplicateUrls(manifest) {
  if (!manifest || !Array.isArray(manifest.pages)) return false;
  var urls = manifest.pages.map(function (p) { return p && p.url; }).filter(Boolean);
  if (urls.length < 2) return false;
  for (var i = 0; i < urls.length; i++) {
    for (var j = i + 1; j < urls.length; j++) {
      if (urls[i] === urls[j]) return true;
    }
  }
  return false;
}

/** @deprecated 尾声与最后一章重复 */
function epilogueDuplicatesLastChapter(manifest) {
  if (!manifest || !Array.isArray(manifest.pages)) return false;
  var chapters = manifest.pages.filter(function (p) {
    return p && p.role === "chapter";
  });
  if (!chapters.length) return false;
  var epilogue = manifest.pages[manifest.pages.length - 1];
  if (!epilogue || epilogue.role !== "epilogue") return false;
  return chapters[chapters.length - 1].url === epilogue.url;
}

function isStaleBentoPreviewManifest(manifest) {
  return carouselHasDuplicateUrls(manifest) || epilogueDuplicatesLastChapter(manifest);
}

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
 * Bento 选项排序参考：updatedAt 最新的非 demo 画册。
 */
export function pickBentoPreviewTrip(trips) {
  var userTrips = pickRecentUserTrips(trips);
  if (!userTrips.length) return null;
  return userTrips[0];
}

/** 在 trips 列表中解析指定 tripId（非 demo）。 */
export function resolvePreviewTrip(trips, tripId) {
  if (!tripId) return null;
  var rows = pickRecentUserTrips(trips);
  for (var i = 0; i < rows.length; i++) {
    if (rows[i].tripId === tripId) return rows[i];
  }
  return null;
}

/** 当前预览选择器 catalog（含分页）。 */
export function previewCatalogTrips() {
  if (V2.pickerCatalogTrips && V2.pickerCatalogTrips.length) {
    return V2.pickerCatalogTrips;
  }
  return V2.trips || [];
}

/** 分页拉取直至找到 tripId，或确认不存在。 */
export function ensureTripInCatalog(tripId) {
  if (!tripId) return Promise.resolve(null);
  var catalog = previewCatalogTrips().slice();
  var found = resolvePreviewTrip(catalog, tripId);
  if (found) return Promise.resolve(found);

  if (V2.isOffline) {
    return Promise.resolve({ tripId: tripId });
  }

  var total = typeof V2.pickerCatalogTotal === "number" && V2.pickerCatalogTotal > 0
    ? V2.pickerCatalogTotal
    : (typeof V2.tripsTotal === "number" ? V2.tripsTotal : catalog.length);
  if (catalog.length >= total) return Promise.resolve(null);

  function fetchNext() {
    return fetchTripsPage(SHELF_PAGE_SIZE, catalog.length).then(function (data) {
      var batch = data.trips || [];
      batch.forEach(function (t) {
        if (!catalog.some(function (x) { return x.tripId === t.tripId; })) {
          catalog.push(t);
        }
      });
      V2.pickerCatalogTrips = catalog;
      V2.pickerCatalogTotal = typeof data.total === "number" ? data.total : total;
      var hit = resolvePreviewTrip(catalog, tripId);
      if (hit) return hit;
      total = V2.pickerCatalogTotal;
      if (catalog.length >= total || batch.length === 0) return null;
      return fetchNext();
    }).catch(function () {
      return null;
    });
  }

  return fetchNext();
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
    && !isStaleBentoPreviewManifest(_previewCache.manifest)
  ) {
    return Promise.resolve(_previewCache.manifest);
  }
  if (opts.force) {
    try { window.__v2BentoPreviewForceFetch = true; } catch (e) { /* ignore */ }
  }
  return fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/bento-preview?t=" + String(Date.now()))
    .then(function (r) {
      if (!r.ok) return null;
      return r.json();
    })
    .then(function (data) {
      if (!data || !data.ok) return null;
      if (V2.bentoPreviewTripId && V2.bentoPreviewTripId !== tripId) return null;
      var m = Object.assign({}, data);
      delete m.ok;
      m.source = "user";
      if (!isValidManifest(m)) return null;
      if (!isStaleBentoPreviewManifest(m)) {
        _previewCache.tripId = tripId;
        _previewCache.updatedAt = opts.updatedAt != null ? opts.updatedAt : null;
        _previewCache.manifest = m;
      } else {
        clearBentoPreviewCache();
      }
      return m;
    })
    .catch(function () { return null; });
}
