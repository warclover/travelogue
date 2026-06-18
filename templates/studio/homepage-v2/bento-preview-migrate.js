/**
 * D-13 → D-14 一次性迁移（PRD §6.8.7）。
 *
 * 无 localStorage preference 时，若本 session 曾处于「我的最近一本」Tab，
 * 将当时预览 tripId 写入 bentoPreviewTripId。
 */
import {
  readBentoPreviewTripId,
  persistBentoPreviewTripId,
  V2_BENTO_TAB_SESSION_KEY,
  V2_BENTO_PREVIEW_TRIP_SESSION_KEY,
  V2_BENTO_D14_MIGRATED_KEY,
} from "./store.js";
import { pickRecentUserTrips } from "./trip-preview.js";

export function readSessionBentoTab() {
  try {
    var raw = sessionStorage.getItem(V2_BENTO_TAB_SESSION_KEY);
    return raw === "mine" ? "mine" : raw === "demo" ? "demo" : null;
  } catch (e) {
    return null;
  }
}

export function persistSessionBentoTab(tab) {
  try {
    if (tab === "mine") sessionStorage.setItem(V2_BENTO_TAB_SESSION_KEY, "mine");
    else sessionStorage.removeItem(V2_BENTO_TAB_SESSION_KEY);
  } catch (e) {
    /* ignore */
  }
}

export function readSessionLegacyPreviewTripId() {
  try {
    var raw = sessionStorage.getItem(V2_BENTO_PREVIEW_TRIP_SESSION_KEY);
    if (!raw) return null;
    var id = String(raw).trim();
    return id || null;
  } catch (e) {
    return null;
  }
}

export function persistSessionLegacyPreviewTripId(tripId) {
  try {
    if (tripId) sessionStorage.setItem(V2_BENTO_PREVIEW_TRIP_SESSION_KEY, String(tripId));
    else sessionStorage.removeItem(V2_BENTO_PREVIEW_TRIP_SESSION_KEY);
  } catch (e) {
    /* ignore */
  }
}

function markD14Migrated() {
  try {
    localStorage.setItem(V2_BENTO_D14_MIGRATED_KEY, "1");
  } catch (e) {
    /* ignore */
  }
}

function alreadyMigrated() {
  try {
    return localStorage.getItem(V2_BENTO_D14_MIGRATED_KEY) === "1";
  } catch (e) {
    return false;
  }
}

/**
 * @param {Array<object>} trips GET /trips 首屏行
 * @returns {string|null} 写入 preference 的 tripId；无迁移则 null
 */
export function migrateD13BentoPreference(trips) {
  if (readBentoPreviewTripId()) return null;
  if (alreadyMigrated()) return null;

  var sessionTab = readSessionBentoTab();
  if (sessionTab !== "mine") {
    markD14Migrated();
    return null;
  }

  var tripId = readSessionLegacyPreviewTripId();
  if (!tripId) {
    var recent = pickRecentUserTrips(trips || []);
    tripId = recent.length ? recent[0].tripId : null;
  }
  if (!tripId) {
    markD14Migrated();
    return null;
  }

  persistBentoPreviewTripId(tripId);
  markD14Migrated();
  persistSessionBentoTab("mine");
  persistSessionLegacyPreviewTripId(tripId);
  return tripId;
}
