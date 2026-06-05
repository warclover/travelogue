/**
 * 首页 v2 · GET /trips 分页客户端（DATA-CONTRACT §2.1 · §4.1）。
 */
import { harnessTripsPageResponse } from "./harness.js";
import { studioAuthHeaders } from "../js/http.js";

export const SHELF_PAGE_SIZE = 20;

/**
 * @typedef {object} ShelfTrip
 * @property {string} tripId
 * @property {string} [title]
 * @property {number} [photoCount]
 * @property {number} [updatedAt]
 * @property {string} [previewUrl]
 * @property {string|null} [previewRelPath]
 * @property {boolean} [longshotStale]
 * @property {boolean} [algorithmStale]
 * @property {boolean} [aestheticStale]
 * @property {boolean} [cullStale]
 * @property {boolean} [layoutStale]
 * @property {boolean} [previewStale]
 * @property {string[]} [staleHints]
 * @property {string|null} [staleHint]
 */

/**
 * @param {number} limit
 * @param {number} offset
 * @returns {Promise<{ok:boolean,trips:object[],total:number}>}
 */
export function fetchTripsPage(limit, offset) {
  var harness = harnessTripsPageResponse(limit, offset);
  if (harness) return harness;
  return fetch("/__travelogue/trips?limit=" + limit + "&offset=" + offset)
    .then(function (r) {
      if (!r.ok) throw new Error("trips unavailable");
      return r.json();
    })
    .then(function (data) {
      return {
        ok: true,
        trips: data.trips || [],
        total: typeof data.total === "number" ? data.total : (data.trips || []).length,
      };
    });
}

export function fetchTripsFirstPage() {
  return fetchTripsPage(SHELF_PAGE_SIZE, 0);
}

/**
 * DELETE /__travelogue/trips/{tripId}（M13）。
 * @param {string} tripId
 * @returns {Promise<void>}
 */
export function deleteTrip(tripId) {
  return fetch("/__travelogue/trips/" + encodeURIComponent(tripId), {
    method: "DELETE",
    headers: studioAuthHeaders(),
  }).then(function (r) {
    if (r.status === 204 || r.status === 200) return;
    return r.json().catch(function () { return {}; }).then(function (data) {
      var err = new Error((data && data.message) || "delete failed");
      err.code = data && data.error;
      err.status = r.status;
      throw err;
    });
  });
}
