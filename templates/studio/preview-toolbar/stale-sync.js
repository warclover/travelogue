/**
 * Preview toolbar · trip stale 同步（M-P2b).
 */
"use strict";

import { STALE_LABELS } from "../js/trip-stale.js";
import { setLayoutPending } from "./pending.js";
import { showStaleHint } from "./export-state.js";

export function refreshStaleHint(root, tripId) {
  fetch("/__travelogue/trips")
    .then(function (resp) { return resp.json(); })
    .then(function (data) {
      var trips = data.trips || [];
      var trip = trips.filter(function (t) { return t.tripId === tripId; })[0];
      if (!trip) return;
      if (trip.layoutCssStale) {
        var pendingText = root.querySelector(".preview-toolbar__pending-text");
        if (pendingText) {
          pendingText.textContent = STALE_LABELS.layoutCss + " · 应用排版后生效";
        }
        setLayoutPending(true);
        return;
      }
      if (trip.longshotStale) {
        showStaleHint(root);
      }
    })
    .catch(function () {});
}
