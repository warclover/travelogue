/**
 * 首页 v2 · 预览画册 Combobox（D-14 · Phase 2/3 缩略图 popover + 搜索/分页）。
 */
import {
  V2,
  $,
  readBentoPreviewTripId,
  STUDIO_DEMO_SHOWCASE_BASE,
} from "./store.js";
import { manifestAssetUrl } from "./manifest.js";
import {
  pickRecentUserTrips,
  resolvePreviewTrip,
  previewCatalogTrips,
} from "./trip-preview.js";
import { fetchTripsPage, SHELF_PAGE_SIZE } from "./trips-client.js";
import { setBentoPreviewTripId, refreshBentoUserPreview } from "./bento-tabs.js";
import {
  tripLabel,
  matchesPreviewSearch,
  stalePreviewLabel,
  shouldDisablePreviewPicker,
} from "./bento-preview-picker-logic.js";

var _wired = false;
var _open = false;
var _scrim = null;
var _anchor = null;
var _focusRestore = null;
var _docBound = false;
var _searchQuery = "";
var _loadingMore = false;

var DEMO_LABEL = "示例作品";

function demoThumbUrl() {
  var m = V2.demoManifest;
  if (m) {
    var url = manifestAssetUrl(m, "background");
    if (url) return url;
  }
  return STUDIO_DEMO_SHOWCASE_BASE + "background.webp";
}

function tripThumbUrl(trip) {
  if (!trip || !trip.tripId) return demoThumbUrl();
  if (trip.previewRelPath) return "/" + trip.tripId + "/" + trip.previewRelPath;
  return "/" + trip.tripId + "/preview.jpg";
}

function optionsHost() {
  return $("v2-bento-preview-options");
}

function syncCatalogFromTrips(trips, total) {
  V2.pickerCatalogTrips = (trips || []).slice();
  V2.pickerCatalogTotal = typeof total === "number" ? total : V2.pickerCatalogTrips.length;
}

function catalogTotal() {
  return typeof V2.pickerCatalogTotal === "number" && V2.pickerCatalogTotal > 0
    ? V2.pickerCatalogTotal
    : previewCatalogTrips().length;
}

function ensureScrim() {
  if (_scrim) return _scrim;
  _scrim = document.createElement("div");
  _scrim.id = "v2-preview-combobox-scrim";
  _scrim.className = "v2-preview-combobox-scrim";
  _scrim.hidden = true;
  _scrim.addEventListener("click", closePopover);
  document.body.appendChild(_scrim);
  return _scrim;
}

function ensurePopoverPortaled(popover) {
  if (!popover || popover.dataset.portaled === "1") return;
  document.body.appendChild(popover);
  popover.dataset.portaled = "1";
}

function ensurePopoverShell(listbox) {
  if (!listbox || listbox.dataset.shell === "1") return;
  listbox.dataset.shell = "1";
  listbox.innerHTML = "";

  var toolbar = document.createElement("div");
  toolbar.className = "v2-preview-combobox__toolbar";

  var search = document.createElement("input");
  search.type = "search";
  search.id = "v2-bento-preview-search";
  search.className = "v2-preview-combobox__search";
  search.placeholder = "搜索画册";
  search.setAttribute("aria-label", "搜索预览画册");
  search.autocomplete = "off";
  search.addEventListener("input", function () {
    _searchQuery = search.value.trim();
    rebuildListbox();
    syncLoadMoreVisibility();
  });
  search.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      var first = optionsHost() && optionsHost().querySelector(".v2-preview-combobox__option");
      if (first) first.focus();
    }
  });
  toolbar.appendChild(search);

  var host = document.createElement("div");
  host.id = "v2-bento-preview-options";
  host.className = "v2-preview-combobox__options";

  var loadMore = document.createElement("button");
  loadMore.type = "button";
  loadMore.id = "v2-bento-preview-load-more";
  loadMore.className = "v2-preview-combobox__load-more";
  loadMore.textContent = "加载更多";
  loadMore.hidden = true;
  loadMore.addEventListener("click", function () {
    loadMorePreviewTrips();
  });

  listbox.appendChild(toolbar);
  listbox.appendChild(host);
  listbox.appendChild(loadMore);
}

function positionPopover(popover, trigger) {
  var rect = trigger.getBoundingClientRect();
  var gap = 6;
  var margin = 12;
  var width = Math.min(Math.max(rect.width, 260), window.innerWidth - margin * 2);
  popover.style.width = width + "px";
  popover.style.left = Math.max(margin, rect.left) + "px";
  popover.style.right = "auto";
  var maxH = Math.min(window.innerHeight * 0.55, 360);
  popover.style.maxHeight = maxH + "px";
  popover.hidden = false;
  var popH = popover.offsetHeight;
  var spaceBelow = window.innerHeight - rect.bottom - margin;
  if (spaceBelow >= popH + gap || spaceBelow >= rect.top - margin) {
    popover.style.top = (rect.bottom + gap) + "px";
    popover.style.bottom = "auto";
  } else {
    popover.style.bottom = (window.innerHeight - rect.top + gap) + "px";
    popover.style.top = "auto";
  }
}

function closePopover() {
  var popover = $("v2-bento-preview-listbox");
  var trigger = $("v2-bento-preview-trigger");
  if (!popover || !trigger) return;
  _open = false;
  popover.hidden = true;
  trigger.setAttribute("aria-expanded", "false");
  if (_scrim) _scrim.hidden = true;
  var restore = _focusRestore;
  _focusRestore = null;
  if (restore && typeof restore.focus === "function") restore.focus();
}

function openPopover() {
  var popover = $("v2-bento-preview-listbox");
  var trigger = $("v2-bento-preview-trigger");
  if (!popover || !trigger || V2.state === "Importing") return;
  ensurePopoverPortaled(popover);
  ensurePopoverShell(popover);
  rebuildListbox();
  syncLoadMoreVisibility();
  _focusRestore = document.activeElement;
  _open = true;
  trigger.setAttribute("aria-expanded", "true");
  ensureScrim().hidden = false;
  positionPopover(popover, trigger);
  var search = $("v2-bento-preview-search");
  if (search) {
    search.value = _searchQuery;
    search.focus();
    return;
  }
  var selected = optionsHost() && optionsHost().querySelector(
    '.v2-preview-combobox__option[aria-selected="true"]'
  );
  if (selected && typeof selected.focus === "function") selected.focus();
}

function chooseOption(tripId, source) {
  closePopover();
  setBentoPreviewTripId(tripId, { source: source || "select" });
}

function buildOptionEl(tripId, label, trip, isSelected) {
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "v2-preview-combobox__option";
  btn.setAttribute("role", "option");
  btn.dataset.tripId = tripId || "";
  btn.setAttribute("aria-selected", isSelected ? "true" : "false");

  var thumb = document.createElement("span");
  thumb.className = "v2-preview-combobox__option-thumb";
  thumb.setAttribute("aria-hidden", "true");
  thumb.style.backgroundImage = "url(\"" + tripThumbUrl(trip || (tripId ? { tripId: tripId } : null)) + "\")";

  var text = document.createElement("span");
  text.className = "v2-preview-combobox__option-text";
  var title = document.createElement("span");
  title.className = "v2-preview-combobox__option-title";
  title.textContent = label;
  text.appendChild(title);

  var chip = stalePreviewLabel(trip);
  if (chip) {
    var stale = document.createElement("span");
    stale.className = "v2-preview-combobox__option-stale";
    stale.textContent = chip;
    text.appendChild(stale);
  }

  btn.appendChild(thumb);
  btn.appendChild(text);
  btn.addEventListener("click", function () {
    chooseOption(tripId || null);
  });
  return btn;
}

function listboxTrips() {
  var catalog = previewCatalogTrips();
  var userTrips = pickRecentUserTrips(catalog);
  if (
    V2.bentoPreviewTripId
    && !userTrips.some(function (t) { return t.tripId === V2.bentoPreviewTripId; })
  ) {
    var orphan = V2.userPreviewTrip || resolvePreviewTrip(catalog, V2.bentoPreviewTripId);
    if (orphan) userTrips = [orphan].concat(userTrips);
  }
  if (_searchQuery) {
    userTrips = userTrips.filter(function (t) { return matchesPreviewSearch(t, _searchQuery); });
  }
  return userTrips;
}

function rebuildListbox() {
  var host = optionsHost();
  if (!host) return;
  var current = V2.bentoPreviewTripId || "";
  var userTrips = listboxTrips();
  host.innerHTML = "";

  if (!_searchQuery) {
    host.appendChild(buildOptionEl("", DEMO_LABEL, null, current === ""));
  }

  userTrips.forEach(function (trip) {
    host.appendChild(buildOptionEl(
      trip.tripId,
      tripLabel(trip),
      trip,
      trip.tripId === current
    ));
  });

  if (_searchQuery && !userTrips.length) {
    var empty = document.createElement("p");
    empty.className = "v2-preview-combobox__empty";
    empty.textContent = "无匹配画册";
    host.appendChild(empty);
  }

  syncNativeSelect();
}

function syncLoadMoreVisibility() {
  var btn = $("v2-bento-preview-load-more");
  if (!btn) return;
  var catalog = previewCatalogTrips();
  var hasMore = catalog.length < catalogTotal();
  btn.hidden = !hasMore || !!_searchQuery || V2.isOffline;
  btn.disabled = _loadingMore;
  btn.textContent = _loadingMore ? "加载中…" : "加载更多";
  if (hasMore && !_searchQuery) {
    btn.textContent += "（" + catalog.length + " / " + catalogTotal() + "）";
  }
}

export function loadMorePreviewTrips() {
  if (_loadingMore || V2.isOffline) return Promise.resolve();
  var catalog = previewCatalogTrips().slice();
  if (catalog.length >= catalogTotal()) return Promise.resolve();
  _loadingMore = true;
  syncLoadMoreVisibility();
  return fetchTripsPage(SHELF_PAGE_SIZE, catalog.length).then(function (data) {
    var batch = data.trips || [];
    batch.forEach(function (t) {
      if (!catalog.some(function (x) { return x.tripId === t.tripId; })) {
        catalog.push(t);
      }
    });
    syncCatalogFromTrips(catalog, data.total);
    rebuildListbox();
  }).catch(function () {
    /* ignore */
  }).finally(function () {
    _loadingMore = false;
    syncLoadMoreVisibility();
  });
}

function syncNativeSelect() {
  var select = $("v2-bento-preview-select");
  if (!select) return;
  var catalog = previewCatalogTrips();
  var userTrips = pickRecentUserTrips(catalog);
  if (
    V2.bentoPreviewTripId
    && !userTrips.some(function (t) { return t.tripId === V2.bentoPreviewTripId; })
  ) {
    var orphan = V2.userPreviewTrip || resolvePreviewTrip(catalog, V2.bentoPreviewTripId);
    if (orphan) userTrips = [orphan].concat(userTrips);
  }

  while (select.options.length > 1) {
    select.remove(1);
  }

  userTrips.forEach(function (trip) {
    var opt = document.createElement("option");
    opt.value = trip.tripId;
    opt.textContent = tripLabel(trip);
    select.appendChild(opt);
  });

  select.value = V2.bentoPreviewTripId || "";
}

function syncComboboxTrigger() {
  var tripId = V2.bentoPreviewTripId || "";
  var labelEl = $("v2-bento-preview-label");
  var host = optionsHost();
  var trigger = $("v2-bento-preview-trigger");

  if (tripId) {
    var trip = resolvePreviewTrip(previewCatalogTrips(), tripId)
      || V2.userPreviewTrip
      || { tripId: tripId };
    if (labelEl) labelEl.textContent = tripLabel(trip) || tripId;
  } else {
    if (labelEl) labelEl.textContent = DEMO_LABEL;
  }

  if (host) {
    host.querySelectorAll(".v2-preview-combobox__option").forEach(function (el) {
      el.setAttribute("aria-selected", (el.dataset.tripId || "") === tripId ? "true" : "false");
    });
  }

  syncPickerAvailability(trigger);
}

var NO_USER_TRIPS_TITLE = "暂无用户画册，仅可预览示例作品";

function syncPickerAvailability(trigger) {
  if (!trigger) trigger = $("v2-bento-preview-trigger");
  if (!trigger) return;
  var hasUser = !shouldDisablePreviewPicker(previewCatalogTrips());
  trigger.disabled = !hasUser;
  if (!hasUser) {
    trigger.title = NO_USER_TRIPS_TITLE;
    trigger.setAttribute("aria-disabled", "true");
  } else {
    trigger.removeAttribute("title");
    trigger.removeAttribute("aria-disabled");
  }
}

export function syncPreviewSelectOptions(trips) {
  syncCatalogFromTrips(trips || V2.trips, V2.tripsTotal);
  rebuildListbox();
  syncComboboxTrigger();
  syncLoadMoreVisibility();
}

export function syncPreviewSelectValue() {
  syncNativeSelect();
  syncComboboxTrigger();
}

/** 启动时读 localStorage、D-13 迁移，并校验 trip 是否仍在列表中。 */
export function applyStoredBentoPreviewPreference(trips) {
  syncCatalogFromTrips(trips || V2.trips, V2.tripsTotal);
  return import("./bento-preview-migrate.js").then(function (migrate) {
    migrate.migrateD13BentoPreference(trips);
    var stored = readBentoPreviewTripId();
    if (!stored) {
      V2.bentoPreviewTripId = null;
      return refreshBentoUserPreview(trips);
    }
    V2.bentoPreviewTripId = stored;
    return refreshBentoUserPreview(trips, { tripId: stored });
  });
}

function bindDocDismiss() {
  if (_docBound) return;
  _docBound = true;
  document.addEventListener("click", function (e) {
    if (!_open) return;
    if (e.target.closest("#v2-bento-preview-combobox")
      || e.target.closest("#v2-bento-preview-listbox")
      || e.target.closest("#v2-preview-combobox-scrim")) return;
    closePopover();
  });
  document.addEventListener("keydown", function (e) {
    if (!_open) return;
    if (e.key === "Escape") {
      e.preventDefault();
      closePopover();
    }
  });
}

function wireListboxKeyboard(listbox, trigger) {
  listbox.addEventListener("keydown", function (e) {
    var host = optionsHost();
    if (!host) return;
    var options = Array.prototype.slice.call(
      host.querySelectorAll(".v2-preview-combobox__option")
    );
    if (!options.length) return;
    var idx = options.indexOf(document.activeElement);
    if (e.key === "ArrowDown") {
      e.preventDefault();
      var next = idx < 0 ? 0 : Math.min(options.length - 1, idx + 1);
      options[next].focus();
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      var prev = idx <= 0 ? 0 : idx - 1;
      options[prev].focus();
    } else if (e.key === "Enter" || e.key === " ") {
      if (idx >= 0) {
        e.preventDefault();
        chooseOption(options[idx].dataset.tripId || null);
      }
    } else if (e.key === "Tab") {
      closePopover();
    }
  });

  trigger.addEventListener("keydown", function (e) {
    if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
      if (!_open) {
        e.preventDefault();
        openPopover();
      }
    }
  });
}

export function initBentoPreviewPicker() {
  if (_wired) return;
  _wired = true;
  var trigger = $("v2-bento-preview-trigger");
  var listbox = $("v2-bento-preview-listbox");
  if (!trigger || !listbox) return;

  _anchor = trigger;
  ensurePopoverShell(listbox);
  bindDocDismiss();
  wireListboxKeyboard(listbox, trigger);

  trigger.addEventListener("click", function () {
    if (trigger.disabled) return;
    if (_open) closePopover();
    else openPopover();
  });

  window.addEventListener("resize", function () {
    if (!_open || !_anchor) return;
    positionPopover(listbox, _anchor);
  });

  syncPreviewSelectOptions(V2.trips);
  syncPreviewSelectValue();
}
