/**
 * Preview toolbar · single state source (M-P2a).
 */
"use strict";

var EDIT_HINT_KEY = "travelogue.studio.v1.editModeHintSeen";
var MODE_KEY = "travelogue.studio.v1.previewMode";
var COLLAPSE_KEY = "travelogue.studio.v1.toolbarCollapsed";
var LEGACY_READER_KEY = "travelogue.studio.readerView";
var LEGACY_COLLAPSE_KEY = "travelogue.studio.previewToolbar.collapsed";
var LONGSHOT_MODE_KEY = "travelogue.studio.v1.longshotMode";
var LONGSHOT_SCALE_KEY = "travelogue.studio.v1.longshotScale";
var LEGACY_LONGSHOT_MODE_KEY = "travelogue:longshotMode";
var LEGACY_LONGSHOT_SCALE_KEY = "travelogue:longshotScale";
var SESSION_COPY_DISPLAY = "travelogue:copyDisplay";
var SESSION_PHOTOS_ONLY = "travelogue:photosOnly";

function defaultExportPrefs() {
  return {
    range: readLongshotMode(),
    scale: readLongshotScale(),
    copy: "full",
    captions: true,
    narrative: true,
  };
}

var state = {
  mode: "reader",
  collapsed: false,
  pendingCount: 0,
  pending: [],
  exportPrefs: defaultExportPrefs(),
  surfaceReader: true,
};

var listeners = [];

export function getPreviewStore() {
  return state;
}

export function subscribePreviewStore(fn) {
  listeners.push(fn);
  return function () {
    var i = listeners.indexOf(fn);
    if (i >= 0) listeners.splice(i, 1);
  };
}

export function setPreviewStore(patch) {
  if (!patch || typeof patch !== "object") return;
  Object.keys(patch).forEach(function (key) {
    state[key] = patch[key];
  });
  listeners.forEach(function (fn) {
    try {
      fn(state);
    } catch (e) {
      /* ignore subscriber errors */
    }
  });
}

export function loadPreviewMode() {
  try {
    var v = localStorage.getItem(MODE_KEY);
    if (v === "reader" || v === "edit") return v;
    var legacy = localStorage.getItem(LEGACY_READER_KEY);
    if (legacy === "0") return "edit";
    if (legacy === "1") return "reader";
  } catch (e) {}
  return "reader";
}

export function hasSeenEditModeHint() {
  try {
    return localStorage.getItem(EDIT_HINT_KEY) === "1";
  } catch (e) {
    return false;
  }
}

export function markEditModeHintSeen() {
  try {
    localStorage.setItem(EDIT_HINT_KEY, "1");
  } catch (e2) {}
}

export function persistPreviewMode(mode) {
  try {
    localStorage.setItem(MODE_KEY, mode);
    localStorage.setItem(LEGACY_READER_KEY, mode === "reader" ? "1" : "0");
  } catch (e2) {}
}

export function loadCollapsed() {
  try {
    var v = localStorage.getItem(COLLAPSE_KEY);
    if (v === "1") return true;
    if (v === "0") return false;
    return localStorage.getItem(LEGACY_COLLAPSE_KEY) === "1";
  } catch (e) {
    return false;
  }
}

export function persistCollapsed(collapsed) {
  try {
    localStorage.setItem(COLLAPSE_KEY, collapsed ? "1" : "0");
    localStorage.setItem(LEGACY_COLLAPSE_KEY, collapsed ? "1" : "0");
  } catch (e2) {}
}

export function readLongshotScale() {
  try {
    var s = parseInt(localStorage.getItem(LONGSHOT_SCALE_KEY), 10);
    if (s === 2 || s === 3) return s;
    var legacy = parseInt(localStorage.getItem(LEGACY_LONGSHOT_SCALE_KEY), 10);
    if (legacy === 2 || legacy === 3) return legacy;
  } catch (e) {}
  return 2;
}

export function readLongshotMode() {
  try {
    var m = localStorage.getItem(LONGSHOT_MODE_KEY);
    if (m === "full" || m === "chapter") return m;
    var legacy = localStorage.getItem(LEGACY_LONGSHOT_MODE_KEY);
    if (legacy === "full" || legacy === "chapter") return legacy;
  } catch (e2) {}
  return "chapter";
}

export function writeLongshotPrefs(mode, scale) {
  try {
    localStorage.setItem(LONGSHOT_MODE_KEY, mode);
    localStorage.setItem(LONGSHOT_SCALE_KEY, String(scale));
    localStorage.setItem(LEGACY_LONGSHOT_MODE_KEY, mode);
    localStorage.setItem(LEGACY_LONGSHOT_SCALE_KEY, String(scale));
  } catch (e3) {}
  var ls = window.TravelogueLongshot;
  if (ls) {
    if (typeof ls.setUserSelectedMode === "function") ls.setUserSelectedMode(mode);
    if (typeof ls.setUserSelectedScale === "function") ls.setUserSelectedScale(scale);
  }
  setPreviewStore({
    exportPrefs: Object.assign({}, state.exportPrefs, { range: mode, scale: scale }),
  });
}

function writeSessionStorage(key, value) {
  try {
    if (value == null) sessionStorage.removeItem(key);
    else sessionStorage.setItem(key, String(value));
  } catch (e) {}
}

function longshotApi() {
  return window.TravelogueLongshot || null;
}

/** §7.2 · 文案范围 preset：full | photos */
export function applyExportCopyPreset(copy) {
  var html = document.documentElement;
  var ls = longshotApi();
  var prefs = Object.assign({}, state.exportPrefs, { copy: copy });
  if (copy === "photos") {
    if (typeof window.travelogueApplyPhotosOnly === "function") {
      window.travelogueApplyPhotosOnly(true);
    } else {
      html.setAttribute("data-photos-only", "on");
    }
    if (ls && typeof ls.applyCaptionDisplay === "function") {
      ls.applyCaptionDisplay(false);
    } else {
      html.setAttribute("data-caption-display", "off");
    }
    prefs.captions = false;
    prefs.narrative = false;
    writeSessionStorage(SESSION_PHOTOS_ONLY, "on");
    writeSessionStorage(SESSION_COPY_DISPLAY, "photos");
  } else {
    if (typeof window.travelogueApplyPhotosOnly === "function") {
      window.travelogueApplyPhotosOnly(false);
    } else {
      html.removeAttribute("data-photos-only");
    }
    html.removeAttribute("data-copy-display");
    if (ls && typeof ls.applyCaptionDisplay === "function") {
      ls.applyCaptionDisplay(true);
    } else {
      html.removeAttribute("data-caption-display");
    }
    prefs.copy = "full";
    prefs.captions = true;
    prefs.narrative = true;
    writeSessionStorage(SESSION_PHOTOS_ONLY, null);
    writeSessionStorage(SESSION_COPY_DISPLAY, "full");
  }
  setPreviewStore({ exportPrefs: prefs });
}

export function applyExportNarrative(on) {
  var html = document.documentElement;
  var prefs = Object.assign({}, state.exportPrefs, { narrative: !!on });
  if (on) {
    html.removeAttribute("data-copy-display");
    writeSessionStorage(SESSION_COPY_DISPLAY, "full");
  } else {
    html.setAttribute("data-copy-display", "photos");
    writeSessionStorage(SESSION_COPY_DISPLAY, "photos");
  }
  setPreviewStore({ exportPrefs: prefs });
}

export function applyExportCaptions(on) {
  var html = document.documentElement;
  var ls = longshotApi();
  var prefs = Object.assign({}, state.exportPrefs, { captions: !!on });
  if (ls && typeof ls.applyCaptionDisplay === "function") {
    ls.applyCaptionDisplay(!!on);
  } else if (on) {
    html.removeAttribute("data-caption-display");
  } else {
    html.setAttribute("data-caption-display", "off");
  }
  setPreviewStore({ exportPrefs: prefs });
}

/** Popover 确定：原子写入 range/scale + 文案选项 */
export function applyExportDraft(draft) {
  draft = draft || {};
  writeLongshotPrefs(draft.range || draft.mode || "chapter", draft.scale || 2);
  if (draft.copy === "photos") {
    applyExportCopyPreset("photos");
    return;
  }
  applyExportCopyPreset("full");
  if (draft.narrative === false) applyExportNarrative(false);
  if (draft.captions != null) applyExportCaptions(!!draft.captions);
}

/** §6.1 · 阅读/编辑 surface data-* 出口 */
export function applySurfaceReaderMode(readerMode) {
  var html = document.documentElement;
  if (readerMode) {
    html.setAttribute("data-reading-profile", "reader_immersive");
    html.setAttribute("data-surface-mode", "reader");
    html.removeAttribute("data-folio");
  } else {
    html.setAttribute("data-reading-profile", "studio_preview");
    html.removeAttribute("data-surface-mode");
    html.setAttribute("data-folio", "lite");
  }
  setPreviewStore({ surfaceReader: !!readerMode });
}

export function syncPendingStore(items, pendingCount) {
  var rows = (items || []).map(function (item) {
    return {
      type: item.kind,
      assetId: item.assetId || "",
      payload: item,
    };
  });
  setPreviewStore({
    pending: rows,
    pendingCount: pendingCount != null ? pendingCount : rows.length,
  });
}
