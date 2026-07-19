/**
 * 首页 v2 · Web 书架回访区（M20-e · §8 · 方案 A）。
 *
 * Bento 首屏下方区块：标题「你的游记画册」+ resume 卡 + 网格（新建卡首位）。
 * 不整页替换 Bento；无用户画册时 hideShelf()。
 */
import { isDemoTrip } from "../js/constants.js";
import { cssBackgroundImage, studioAuthHeaders } from "../js/dom.js";
import { trackStudioEvent } from "../js/analytics.js";
import { $, show, V2 } from "./store.js";
import { openImportSheet } from "./import-entry.js";
import { fetchTripsPage, SHELF_PAGE_SIZE } from "./trips-client.js";
import { attachShelfTripMenu, closeAllShelfMenus } from "./shelf-menu.js";
import { renderBenchRecent } from "./bento.js";
import {
  shelfPriorityLongshotTripId,
  shelfResumeActions,
  shelfShowCoverLongshotBadge,
  shelfShowCoverReadyBadge,
} from "./shelf-actions-logic.js";

var READY_LONGSHOT = "分享图已就绪";
var PREVIEW_READY = "可先预览";
import { triggerHomepageRecurate } from "./bento-stale.js";
import { openSettings } from "./settings-panel.js";

var STALE_BADGE = "可更新";
var STALE_LONGSHOT = "分享图需更新";
var _shelfScrollTracked = false;
var _hostEl = null;
var _gridEl = null;
var _newCardEl = null;
var _resumeEl = null;
var _loadedTrips = [];
var _total = 0;
var _loadingMore = false;

function relativeTime(ts) {
  if (!ts) return "";
  var d = new Date(ts * 1000);
  var diff = Date.now() - d.getTime();
  var dayMs = 86400000;
  if (diff < 60000) return "刚刚";
  if (diff < 3600000) return Math.floor(diff / 60000) + " 分钟前";
  if (diff < dayMs) return Math.floor(diff / 3600000) + " 小时前";
  if (diff < 7 * dayMs) return Math.floor(diff / dayMs) + " 天前";
  return d.toLocaleDateString("zh-CN");
}

function coverUrl(trip) {
  var rel = trip.shelfCoverRelPath || trip.previewRelPath;
  return rel ? "/" + trip.tripId + "/" + rel : null;
}

function titleInitials(title) {
  var t = (title || "").trim();
  return t ? t.slice(0, 2) : "游记";
}

function openTrip(trip, focusLongshot) {
  var url = trip.previewUrl || ("/" + trip.tripId + "/index.html");
  if (focusLongshot) url += (url.indexOf("?") >= 0 ? "&" : "?") + "focus=longshot";
  window.location.href = url;
}

function el(tag, className, text) {
  var node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function buildCover(trip, host) {
  var cover = el("div", "v2-shelf__cover");
  var url = coverUrl(trip);
  if (url) {
    var bg = cssBackgroundImage(url);
    if (bg) cover.style.backgroundImage = bg;
  } else {
    cover.classList.add("v2-shelf__cover--blank");
    cover.appendChild(el("span", "v2-shelf__cover-initials", titleInitials(trip.title)));
  }
  host.appendChild(cover);
  return cover;
}

function tripSubLine(trip) {
  // FE-SR-09 / AC-SR-14 · 主 meta 只保留用户可读信息；模板锁定/stale 靠角标
  var sub = [];
  if (trip.photoCount) sub.push(trip.photoCount + " 张");
  var rel = relativeTime(trip.updatedAt);
  if (rel) sub.push(rel);
  return sub.join(" · ");
}

function onTripDeleted(trip) {
  var tripId = trip.tripId;
  _loadedTrips = _loadedTrips.filter(function (t) { return t.tripId !== tripId; });
  _total = Math.max(0, _total - 1);

  V2.trips = V2.trips.filter(function (t) { return t.tripId !== tripId; });
  V2.tripsTotal = _total;

  var card = _gridEl && _gridEl.querySelector('.v2-shelf__card[data-trip-id="' + tripId + '"]');
  if (card) {
    card.classList.add("v2-shelf__card--leaving");
    setTimeout(function () {
      if (card.parentNode) card.parentNode.removeChild(card);
    }, 200);
  }

  if (_resumeEl && _resumeEl.dataset.tripId === tripId) {
    _resumeEl.remove();
    _resumeEl = null;
    refreshResumeBar();
  }

  syncHeadCount();
  syncFooter();
  renderBenchRecent();

  if (!_loadedTrips.some(function (t) { return !isDemoTrip(t); })) {
    hideShelf();
    if (typeof V2.reroute === "function") V2.reroute();
  }
}

function refreshResumeBar() {
  if (!_hostEl) return;
  var resumeTrip = _loadedTrips.filter(function (t) { return !isDemoTrip(t); })[0];
  if (!resumeTrip) return;
  var existing = _hostEl.querySelector(".v2-shelf__resume");
  if (existing) existing.remove();
  _resumeEl = buildResume(resumeTrip);
  var grid = _hostEl.querySelector(".v2-shelf__grid");
  if (grid) _hostEl.insertBefore(_resumeEl, grid);
  else _hostEl.appendChild(_resumeEl);
}

function syncHeadCount() {
  if (!_hostEl) return;
  var countEl = _hostEl.querySelector(".v2-shelf__count");
  if (!countEl) return;
  var countBits = [_total + " 本作品"];
  var latest = _loadedTrips.filter(function (t) { return !isDemoTrip(t); })[0];
  if (latest && latest.updatedAt) {
    countBits.push("上次编辑 " + relativeTime(latest.updatedAt));
  }
  countEl.textContent = countBits.join(" · ");
}

function buildCoverWrap(trip, surface) {
  var wrap = el("div", "v2-shelf__cover-wrap");
  var openCover = el("button", "v2-shelf__open v2-shelf__open--cover");
  openCover.type = "button";
  var staleBits = [];
  if (trip.longshotStale) staleBits.push("分享图需更新");
  if (trip.algorithmStale) staleBits.push("可更新");
  var readyBadge = shelfShowCoverReadyBadge(trip);
  if (readyBadge) staleBits.push(READY_LONGSHOT);
  openCover.title = (trip.title || trip.tripId)
    + (staleBits.length ? " · " + staleBits.join(" · ") : "");
  buildCover(trip, openCover);
  openCover.addEventListener("click", function () { openTrip(trip, false); });
  wrap.appendChild(openCover);
  if (isDemoTrip(trip)) {
    wrap.appendChild(el("span", "v2-demo-flag v2-shelf__badge", "示例"));
  }
  // PRD-PIPELINE-PERF-V1 · R5.1 · intermediate preview state only (ready = default, no badge)
  if (trip.g1Pending || trip.derivativesStatus === "preview") {
    wrap.appendChild(el("span", "v2-shelf__preview-badge", PREVIEW_READY));
  }
  var resumeTrip = _loadedTrips.filter(function (t) { return !isDemoTrip(t); })[0];
  var resumeTripId = resumeTrip ? resumeTrip.tripId : null;
  var priorityLongshotTripId = shelfPriorityLongshotTripId(_loadedTrips, {
    resumeTripId: resumeTripId,
  });
  var showLongshotBadge = shelfShowCoverLongshotBadge(trip, {
    resumeTripId: resumeTripId,
    priorityLongshotTripId: priorityLongshotTripId,
  });
  if (showLongshotBadge) {
    wrap.appendChild(el("span", "v2-shelf__stale-badge", STALE_LONGSHOT));
  } else if (readyBadge) {
    wrap.appendChild(el("span", "v2-shelf__ready-badge", READY_LONGSHOT));
  } else if (trip.algorithmStale && !trip.longshotStale) {
    // 长图过期优先于「可更新」；同本不叠两枚角标
    wrap.appendChild(el("span", "v2-shelf__stale-badge", STALE_BADGE));
  }
  attachShelfTripMenu(wrap, trip, { surface: surface, onDeleted: onTripDeleted });
  return wrap;
}

function buildResume(trip) {
  var card = el("div", "v2-shelf__resume");
  card.dataset.tripId = trip.tripId;

  var thumbWrap = el("div", "v2-shelf__resume-thumb-wrap");
  var thumb = el("div", "v2-shelf__resume-thumb");
  var url = coverUrl(trip);
  if (url) {
    var bg = cssBackgroundImage(url);
    if (bg) thumb.style.backgroundImage = bg;
  } else thumb.classList.add("v2-shelf__cover--blank");
  thumbWrap.appendChild(thumb);
  attachShelfTripMenu(thumbWrap, trip, { surface: "resume", onDeleted: onTripDeleted });
  card.appendChild(thumbWrap);

  var textWrap = el("div", "v2-shelf__resume-text");
  textWrap.appendChild(el("strong", null, "继续编辑 · " + (trip.title || trip.tripId)));
  textWrap.appendChild(el("span", null, tripSubLine(trip)));
  card.appendChild(textWrap);

  var actions = el("div", "v2-shelf__resume-actions");
  shelfResumeActions(trip).forEach(function (action) {
    var btn = el("button", action.primary ? "primary" : null, action.label);
    btn.type = "button";
    btn.addEventListener("click", function () {
      trackStudioEvent("shelf_resume_click", {
        trip_id: trip.tripId,
        stale: action.kind !== "open",
        kind: action.kind,
      });
      if (action.triggerCurate) {
        triggerHomepageRecurate(trip.tripId, "shelf_resume");
        return;
      }
      openTrip(trip, !!action.focusLongshot);
    });
    actions.appendChild(btn);
  });
  card.appendChild(actions);
  return card;
}

function buildBook(trip) {
  var card = el("article", "v2-shelf__card v2-shelf__book");
  card.dataset.tripId = trip.tripId;

  card.appendChild(buildCoverWrap(trip, "grid"));

  var openMeta = el("button", "v2-shelf__open v2-shelf__open--meta");
  openMeta.type = "button";
  openMeta.appendChild(el("h3", "v2-shelf__title", trip.title || trip.tripId));
  openMeta.appendChild(el("p", "v2-shelf__sub", tripSubLine(trip)));
  openMeta.addEventListener("click", function () { openTrip(trip, false); });
  card.appendChild(openMeta);

  return card;
}

function buildNewCard() {
  var book = el("button", "v2-shelf__book v2-shelf__book--new");
  book.type = "button";
  var cover = el("div", "v2-shelf__cover v2-shelf__cover--new", "+");
  book.appendChild(cover);
  book.appendChild(el("h3", "v2-shelf__title", "新建画册"));
  book.appendChild(el("p", "v2-shelf__sub", "选择新的照片文件夹"));
  book.addEventListener("click", function () { openImportSheet(); });
  return book;
}

function syncFooter() {
  if (!_hostEl) return;
  var old = _hostEl.querySelector(".v2-shelf__footer");
  if (old) old.remove();
  if (_loadedTrips.length >= _total) return;

  var footer = el("div", "v2-shelf__footer");
  var btn = el("button", "v2-shelf__load-more", _loadingMore ? "加载中…" : "加载更多");
  btn.type = "button";
  btn.id = "v2-shelf-load-more";
  btn.disabled = _loadingMore;
  btn.addEventListener("click", loadMoreShelf);
  footer.appendChild(btn);
  footer.appendChild(el(
    "p",
    "v2-shelf__more-hint",
    "已显示 " + _loadedTrips.length + " / " + _total + " 本"
  ));
  _hostEl.appendChild(footer);
}

function appendBooks(trips) {
  if (!_gridEl || !_newCardEl) return;
  trips.forEach(function (t) {
    var exists = _loadedTrips.some(function (x) { return x.tripId === t.tripId; });
    if (exists) return;
    _loadedTrips.push(t);
    // 新建卡固定在网格首位（D-23）；新画册追加到末尾
    _gridEl.appendChild(buildBook(t));
  });
}

function loadMoreShelf() {
  if (_loadingMore || _loadedTrips.length >= _total) return;
  _loadingMore = true;
  syncFooter();
  fetchTripsPage(SHELF_PAGE_SIZE, _loadedTrips.length)
    .then(function (data) {
      appendBooks(data.trips || []);
      _total = typeof data.total === "number" ? data.total : _total;
      _loadingMore = false;
      syncFooter();
    })
    .catch(function () {
      _loadingMore = false;
      syncFooter();
      if (typeof studioToast === "function") {
        studioToast("加载失败，请重试", { duration: 2800 });
      }
    });
}

/** 隐藏书架回访区（无用户画册或 Importing 全屏时）。 */
export function hideShelf() {
  closeAllShelfMenus();
  var host = $("v2-shelf");
  if (!host) return;
  host.innerHTML = "";
  show(host, false);
  _hostEl = null;
  _gridEl = null;
  _newCardEl = null;
  _resumeEl = null;
  _loadedTrips = [];
  _total = 0;
  _loadingMore = false;
}

/** 渲染 Bento 下方书架区。trips 为首页；total 为服务端总数。 */
export function renderShelf(trips, total) {
  var host = $("v2-shelf");
  if (!host) return;
  closeAllShelfMenus();
  _hostEl = host;
  host.innerHTML = "";

  _loadedTrips = (trips || []).slice();
  _total = typeof total === "number" ? total : _loadedTrips.length;
  _loadingMore = false;

  var head = el("div", "v2-shelf__head");
  var headLeft = el("div");
  headLeft.appendChild(el("h2", "v2-shelf__title-h1", "你的游记画册"));
  var countBits = [_total + " 本作品"];
  var latestNonDemo = _loadedTrips.filter(function (t) { return !isDemoTrip(t); })[0];
  if (latestNonDemo && latestNonDemo.updatedAt) {
    countBits.push("上次编辑 " + relativeTime(latestNonDemo.updatedAt));
  }
  headLeft.appendChild(el("p", "v2-shelf__count", countBits.join(" · ")));
  head.appendChild(headLeft);
  var storageBadge = el("button", "v2-shelf__storage-badge");
  storageBadge.type = "button";
  storageBadge.hidden = true;
  storageBadge.setAttribute("aria-label", "磁盘占用较高，打开存储设置");
  storageBadge.addEventListener("click", function () {
    openSettings({ focus: "storage", source: "shelf_storage_badge" });
  });
  head.appendChild(storageBadge);
  host.appendChild(head);
  refreshShelfStorageBadge(storageBadge);

  var resumeTrip = latestNonDemo;
  if (resumeTrip) {
    _resumeEl = buildResume(resumeTrip);
    host.appendChild(_resumeEl);
  } else {
    _resumeEl = null;
  }

  var grid = el("div", "v2-shelf__grid");
  _gridEl = grid;
  // D-23：新建画册卡固定在网格第 1 位（恢复卡之后、画册卡之前）
  _newCardEl = buildNewCard();
  grid.appendChild(_newCardEl);
  _loadedTrips.forEach(function (t) { grid.appendChild(buildBook(t)); });
  host.appendChild(grid);

  syncFooter();
  show(host, true);
  wireShelfScrollObserver(host);
}

function wireShelfScrollObserver(host) {
  if (_shelfScrollTracked || !host || typeof IntersectionObserver !== "function") return;
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting || _shelfScrollTracked) return;
      _shelfScrollTracked = true;
      trackStudioEvent("shelf_scroll_into_view", {});
      observer.disconnect();
    });
  }, { threshold: 0.15 });
  observer.observe(host);
}

/** D-MRS-13 · 占用超阈值时书架非阻断角标（无弹窗） */
function refreshShelfStorageBadge(badgeEl) {
  if (!badgeEl) return;
  fetch("/__travelogue/storage/usage", { headers: studioAuthHeaders() })
    .then(function (r) {
      return r.json();
    })
    .then(function (data) {
      if (!data || data.ok === false || !data.overThreshold) {
        badgeEl.hidden = true;
        badgeEl.textContent = "";
        return;
      }
      badgeEl.hidden = false;
      badgeEl.textContent = "磁盘占用较高";
      badgeEl.title = "作品库占用较高，可打开设置清理";
    })
    .catch(function () {
      badgeEl.hidden = true;
    });
}

export { loadMoreShelf, SHELF_PAGE_SIZE };
