/**
 * 首页 v2 · Web 书架（M20-e · §8）。
 *
 * IdleReturning 态：标题「你的游记画册」+ resume 卡 + 网格 + 新建卡。
 * - 封面：previewRelPath → /{tripId}/{previewRelPath}；无封面 → forest 底 + 首字
 * - 副文案：photoCount 张 · 相对时间；longshotStale → 「长图待更新」/「更新长图」
 * - demo trip → 「示例」徽章（§8.1）
 * - §8.2 / §4.1：total > 20 → limit/offset 分页 +「加载更多」
 */
import { isDemoTrip } from "../js/constants.js";
import { cssBackgroundImage } from "../js/dom.js";
import { trackStudioEvent } from "../js/analytics.js";
import { $, show } from "./store.js";
import { openImportSheet } from "./import-sheet.js";
import { fetchTripsPage, SHELF_PAGE_SIZE } from "./trips-client.js";

var _hostEl = null;
var _gridEl = null;
var _newCardEl = null;
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
  return trip.previewRelPath ? "/" + trip.tripId + "/" + trip.previewRelPath : null;
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
}

function buildResume(trip) {
  var card = el("div", "v2-shelf__resume");
  var thumb = el("div", "v2-shelf__resume-thumb");
  var url = coverUrl(trip);
  if (url) {
    var bg = cssBackgroundImage(url);
    if (bg) thumb.style.backgroundImage = bg;
  } else thumb.classList.add("v2-shelf__cover--blank");
  card.appendChild(thumb);

  var textWrap = el("div", "v2-shelf__resume-text");
  textWrap.appendChild(el("strong", null, "继续编辑 · " + (trip.title || trip.tripId)));
  var subBits = [];
  if (trip.photoCount) subBits.push(trip.photoCount + " 张");
  var rel = relativeTime(trip.updatedAt);
  if (rel) subBits.push(rel);
  if (trip.longshotStale) subBits.push("长图待更新");
  textWrap.appendChild(el("span", null, subBits.join(" · ")));
  card.appendChild(textWrap);

  var actions = el("div", "v2-shelf__resume-actions");
  if (trip.longshotStale) {
    var stale = el("button", null, "更新长图");
    stale.type = "button";
    stale.addEventListener("click", function () {
      trackStudioEvent("shelf_resume_click", { trip_id: trip.tripId, stale: true });
      openTrip(trip, true);
    });
    actions.appendChild(stale);
  }
  var open = el("button", "primary", "打开预览");
  open.type = "button";
  open.addEventListener("click", function () {
    trackStudioEvent("shelf_resume_click", { trip_id: trip.tripId, stale: !!trip.longshotStale });
    openTrip(trip, false);
  });
  actions.appendChild(open);
  card.appendChild(actions);
  return card;
}

function buildBook(trip) {
  var book = el("button", "v2-shelf__book");
  book.type = "button";
  book.title = (trip.title || trip.tripId) + (trip.longshotStale ? " · 长图待更新" : "");
  buildCover(trip, book);
  if (isDemoTrip(trip)) {
    var badge = el("span", "v2-demo-flag v2-shelf__badge", "示例");
    book.appendChild(badge);
  }
  book.appendChild(el("h3", "v2-shelf__title", trip.title || trip.tripId));
  var sub = [];
  if (trip.photoCount) sub.push(trip.photoCount + " 张");
  var rel = relativeTime(trip.updatedAt);
  if (rel) sub.push(rel);
  if (trip.longshotStale) sub.push("长图待更新");
  book.appendChild(el("p", "v2-shelf__sub", sub.join(" · ")));
  book.addEventListener("click", function () { openTrip(trip, false); });
  return book;
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
    _gridEl.insertBefore(buildBook(t), _newCardEl);
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

/** 渲染书架。trips 为首页；total 为服务端总数。 */
export function renderShelf(trips, total) {
  show($("v2-loading"), false);
  show($("v2-headline"), false);
  show($("v2-frame"), false);
  show($("v2-importing"), false);
  show($("v2-topbar"), false);

  var host = $("v2-shelf");
  if (!host) return;
  _hostEl = host;
  host.innerHTML = "";

  _loadedTrips = (trips || []).slice();
  _total = typeof total === "number" ? total : _loadedTrips.length;
  _loadingMore = false;

  var head = el("div", "v2-shelf__head");
  var headLeft = el("div");
  headLeft.appendChild(el("h1", "v2-shelf__title-h1", "你的游记画册"));
  var countBits = [_total + " 本作品"];
  if (_loadedTrips[0] && _loadedTrips[0].updatedAt) {
    countBits.push("上次编辑 " + relativeTime(_loadedTrips[0].updatedAt));
  }
  headLeft.appendChild(el("p", "v2-shelf__count", countBits.join(" · ")));
  head.appendChild(headLeft);
  var newBtn = el("button", "v2-shelf__new", "+ 选择文件夹新建");
  newBtn.type = "button";
  newBtn.addEventListener("click", function () { openImportSheet(); });
  head.appendChild(newBtn);
  host.appendChild(head);

  var resumeTrip = _loadedTrips.filter(function (t) { return !isDemoTrip(t); })[0];
  if (resumeTrip) host.appendChild(buildResume(resumeTrip));

  var grid = el("div", "v2-shelf__grid");
  _gridEl = grid;
  _loadedTrips.forEach(function (t) { grid.appendChild(buildBook(t)); });
  _newCardEl = buildNewCard();
  grid.appendChild(_newCardEl);
  host.appendChild(grid);

  syncFooter();
  show(host, true);
}

export { loadMoreShelf, SHELF_PAGE_SIZE };
