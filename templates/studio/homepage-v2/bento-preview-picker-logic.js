/**
 * 首页 v2 · 预览画册 Combobox 纯逻辑（无 DOM · node --test）。
 */
import { isDemoTrip } from "../js/constants.js";

export function tripLabel(trip) {
  return (trip && (trip.title || trip.tripId) || "").trim() || (trip && trip.tripId) || "";
}

export function matchesPreviewSearch(trip, query) {
  if (!query) return true;
  var q = String(query).toLowerCase();
  var title = String(trip && trip.title || "").toLowerCase();
  var id = String(trip && trip.tripId || "").toLowerCase();
  return title.indexOf(q) >= 0 || id.indexOf(q) >= 0;
}

export function stalePreviewLabel(trip) {
  if (!trip) return "";
  if (trip.longshotStale) return "长图待更新";
  if (trip.algorithmStale) return "算法待更新";
  return "";
}

export function filterUserTrips(trips) {
  return (trips || []).filter(function (t) { return !isDemoTrip(t); });
}

/** AC-D14-06：无用户画册时禁用 Combobox trigger。 */
export function shouldDisablePreviewPicker(trips) {
  return filterUserTrips(trips).length === 0;
}
