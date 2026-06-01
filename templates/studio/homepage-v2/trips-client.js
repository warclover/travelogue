/**
 * 首页 v2 · GET /trips 分页客户端（DATA-CONTRACT §2.1 · §4.1）。
 */
import { harnessTripsPageResponse } from "./harness.js";

export const SHELF_PAGE_SIZE = 20;

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
