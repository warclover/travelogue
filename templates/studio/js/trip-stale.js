/**
 * Studio · trip stale 字段统一消费（M-P2b · R-P2-05）。
 */
"use strict";

/** @typedef {{ tripId?: string, previewUrl?: string, longshotStale?: boolean, algorithmStale?: boolean, layoutCssStale?: boolean, staleHint?: string, staleHints?: string[] }} TripStaleRow */

export var STALE_LABELS = {
  longshot: "长图待更新",
  algorithm: "算法待更新",
  layoutCss: "布局待更新",
};

/**
 * @param {TripStaleRow|null|undefined} trip
 * @returns {string[]}
 */
export function tripStaleBits(trip) {
  trip = trip || {};
  var bits = [];
  if (trip.longshotStale) bits.push(STALE_LABELS.longshot);
  if (trip.algorithmStale) bits.push(STALE_LABELS.algorithm);
  if (trip.layoutCssStale) bits.push(STALE_LABELS.layoutCss);
  return bits;
}

/**
 * @param {TripStaleRow|null|undefined} trip
 * @param {string} [sep]
 * @returns {string}
 */
export function tripStaleSummary(trip, sep) {
  return tripStaleBits(trip).join(sep || " · ");
}

/**
 * @param {TripStaleRow|null|undefined} trip
 * @returns {boolean}
 */
export function hasTripStale(trip) {
  return tripStaleBits(trip).length > 0;
}

/**
 * @param {TripStaleRow|null|undefined} trip
 * @returns {string}
 */
export function primaryStaleLabel(trip) {
  var bits = tripStaleBits(trip);
  return bits[0] || "";
}

/**
 * @param {TripStaleRow|null|undefined} trip
 * @returns {string}
 */
export function tripPreviewHref(trip) {
  trip = trip || {};
  if (!trip.tripId) return trip.previewUrl || "";
  if (trip.longshotStale) {
    return "/" + trip.tripId + "/index.html?focus=longshot";
  }
  return trip.previewUrl || ("/" + trip.tripId + "/index.html");
}
