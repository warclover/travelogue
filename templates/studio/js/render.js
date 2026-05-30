/**
 * Travelogue Studio · state machine + homepage rendering.
 */
import { LS } from "./constants.js";
import { S } from "./state.js";
import { $, show, setTitle, formatUpdatedAt, syncImportUiDisabled, cssBackgroundImage } from "./dom.js";
import { closeImportSheet, getRecentPaths } from "./sheet.js";
import { requestNativeFolder, startImport } from "./import-bridge.js";
import { registerRender } from "./navigation.js";

// ── Hero background (LCP-friendly: try small variant first when available) ──
export function updateHeroBackground() {
  var img = $("studio-hero-image");
  if (!img) return;
  if (S.tripsData.length > 0) {
    var trip = S.tripsData[0];
    var rel = trip.previewRelPath;
    if (rel) {
      var url = "/" + trip.tripId + "/" + rel;
      if (url === S.lastHeroSrc) return;
      S.lastHeroSrc = url;
      var pre = new Image();
      pre.onload = function () {
        var bg = cssBackgroundImage(url);
        if (bg) img.style.backgroundImage = bg;
        img.classList.remove("studio-hero__image--default");
      };
      pre.onerror = function () {
        img.style.backgroundImage = "";
        img.classList.add("studio-hero__image--default");
      };
      pre.src = url;
      return;
    }
  }
  S.lastHeroSrc = "";
  img.style.backgroundImage = "";
  img.classList.add("studio-hero__image--default");
}

export function render() {
  var hasTrips = S.tripsData.length > 0;
  var isImporting = S.currentState === "Importing";
  var isFailed = S.currentState === "Failed";
  var isSuccess = S.currentState === "Success";
  var isLoading = S.currentState === "Loading";

  if (isImporting) setTitle("正在生成…");
  else if (isFailed) setTitle("导入失败");
  else setTitle();

  show($("studio-offline"), S.isOffline);
  syncImportUiDisabled();

  // Hero variant data attribute (controls veil / blur)
  var hero = $("studio-hero");
  var variant;
  if (isImporting) variant = "importing";
  else if (isLoading) variant = "loading";
  else if (isFailed) variant = "failed";
  else if (isSuccess) variant = "success";
  else if (hasTrips) variant = "returning";
  else variant = "empty";
  if (hero) hero.setAttribute("data-variant", variant);

  updateHeroBackground();

  show($("studio-hero-loading"), isLoading);
  show($("studio-hero-empty"), !hasTrips && !isImporting && !isFailed && !isSuccess && !isLoading);
  show($("studio-hero-returning"), hasTrips && !isImporting && !isFailed && !isSuccess && !isLoading);
  show($("studio-hero-importing"), isImporting);
  show($("studio-failure"), isFailed);
  show($("studio-success"), isSuccess);

  var quietOverlay = isImporting || isFailed || isSuccess || isLoading;
  show($("studio-hero-secondary"), !quietOverlay);
  var secondaryLabel = $("studio-secondary-label");
  if (secondaryLabel) {
    secondaryLabel.textContent = hasTrips ? "或者" : "还没自己的照片？";
  }

  if (quietOverlay) closeImportSheet();
  show($("studio-import-form"), false);
  show($("studio-advanced-options"), !quietOverlay);

  show($("studio-scroll-hint"), !quietOverlay);
  var scrollText = $("studio-scroll-hint-text");
  if (scrollText) {
    if (hasTrips) {
      var count = S.tripsTotalCount || S.tripsData.length;
      scrollText.textContent = "向下 · 全部 " + count + " 篇游记";
    } else {
      scrollText.textContent = "向下 · 看看别人做的";
    }
  }

  var dot = $("studio-status-dot");
  var statusText = $("studio-status-text");
  if (dot && statusText) {
    dot.classList.remove("studio-topbar__dot--offline", "studio-topbar__dot--importing");
    if (S.isOffline) { dot.classList.add("studio-topbar__dot--offline"); statusText.textContent = "未连接"; }
    else if (isImporting) { dot.classList.add("studio-topbar__dot--importing"); statusText.textContent = "正在装帧中…"; }
    else { statusText.textContent = "本地运行中"; }
  }

  if (hasTrips && !isImporting && !isFailed && !isSuccess) {
    renderContinueCard();
    renderHybridHero();
    renderRecentPathHint();
  } else {
    show($("studio-continue-card"), false);
    show($("studio-recent-path-hint"), false);
    var h1 = document.querySelector(".studio-hero__title--after-card");
    if (h1) show(h1, true);
  }

  show($("studio-gallery"), !hasTrips && !isImporting && !isFailed && !isSuccess && !isLoading);
  show($("studio-trips"), hasTrips && !isImporting && !isFailed && !isSuccess);
  if (hasTrips && !isImporting && !isFailed && !isSuccess) renderAllTrips();

  var below = $("studio-below");
  if (below) {
    var anyBelow = !isImporting && !isFailed && !isSuccess && !isLoading;
    below.style.display = anyBelow ? "" : "none";
  }

  renderFooterStats();
  renderCancelNotice();
}

export function renderContinueCard() {
  var host = $("studio-continue-card");
  if (!host || !S.tripsData.length) {
    show(host, false);
    return;
  }
  var trip = S.tripsData[0];
  host.innerHTML = "";
  show(host, true);
  var titleAfter = $("studio-hero-returning");
  var h1 = titleAfter && titleAfter.querySelector(".studio-hero__title--after-card");
  if (h1) show(h1, false);

  var thumb = document.createElement("div");
  thumb.className = "studio-continue-card__thumb";
  if (trip.previewRelPath) {
    var img = document.createElement("img");
    img.alt = trip.title || "";
    img.src = "/" + trip.tripId + "/" + trip.previewRelPath;
    img.onerror = function () { img.remove(); };
    thumb.appendChild(img);
  }
  host.appendChild(thumb);

  var t = document.createElement("p");
  t.className = "studio-continue-card__title";
  t.textContent = trip.title || trip.tripId;
  host.appendChild(t);

  var sub = document.createElement("p");
  sub.className = "studio-continue-card__sub";
  sub.textContent = formatUpdatedAt(trip.updatedAt) || "继续上次的杂志";
  host.appendChild(sub);

  var actions = document.createElement("div");
  actions.className = "studio-continue-card__actions";

  var cont = document.createElement("a");
  cont.className = "studio-btn studio-btn--gold";
  cont.href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
  cont.textContent = "继续编辑";
  actions.appendChild(cont);

  if (trip.longshotStale) {
    var lng = document.createElement("a");
    lng.className = "studio-btn studio-btn--ghost-inverse";
    lng.href = "/" + trip.tripId + "/index.html?focus=longshot";
    lng.textContent = "更新长图";
    actions.appendChild(lng);
  }
  host.appendChild(actions);
}

// ── Returning hero: left text + right 3 recent cards ──
export function renderHybridHero() {
  var eyebrow = $("studio-recent-eyebrow");
  if (eyebrow && S.tripsData[0] && S.tripsData[0].updatedAt) {
    eyebrow.textContent = "最近编辑 · " + formatUpdatedAt(S.tripsData[0].updatedAt);
  } else if (eyebrow) {
    eyebrow.textContent = "最近编辑";
  }

  var list = $("studio-hero-recent-list");
  if (!list) return;
  list.innerHTML = "";

  var recent = S.tripsData.slice(0, 3);
  recent.forEach(function (trip, idx) {
    var card = document.createElement("a");
    card.className = "studio-hero__recent-card";
    var href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    if (trip.longshotStale) href = "/" + trip.tripId + "/index.html?focus=longshot";
    card.href = href;
    card.title = (trip.title || trip.tripId) + (trip.longshotStale ? " · 长图待更新" : "");

    if (idx === 0 &&
        localStorage.getItem(LS.firstPreviewDone) === "1" &&
        !localStorage.getItem(LS.firstReturnHighlight) &&
        S.currentState === "IdleReturning") {
      card.classList.add("studio-hero__recent-card--highlight");
      setTimeout(function () {
        card.classList.remove("studio-hero__recent-card--highlight");
        localStorage.setItem(LS.firstReturnHighlight, "1");
      }, 5000);
    }

    if (trip.previewRelPath) {
      var img = document.createElement("img");
      img.alt = trip.title || "游记封面";
      img.loading = idx === 0 ? "eager" : "lazy";
      img.src = "/" + trip.tripId + "/" + trip.previewRelPath;
      img.onerror = function () { img.remove(); };
      card.appendChild(img);
    }

    if (trip.longshotStale) {
      var stale = document.createElement("span");
      stale.className = "studio-hero__recent-card__stale";
      stale.textContent = "长图待更新";
      card.appendChild(stale);
    }

    var meta = document.createElement("div");
    meta.className = "studio-hero__recent-card__meta";
    var t = document.createElement("p");
    t.className = "studio-hero__recent-card__title";
    t.textContent = trip.title || trip.tripId;
    meta.appendChild(t);
    var sub = document.createElement("p");
    sub.className = "studio-hero__recent-card__sub";
    var subParts = [];
    if (trip.photoCount) subParts.push(trip.photoCount + " 张");
    if (trip.updatedAt) subParts.push(formatUpdatedAt(trip.updatedAt));
    sub.textContent = subParts.join(" · ");
    meta.appendChild(sub);
    card.appendChild(meta);

    list.appendChild(card);
  });
}

/** P5-H4 · Returning hero: suggest reusing the most recent import path. */
export function renderRecentPathHint() {
  var host = $("studio-recent-path-hint");
  if (!host) {
    var ctaRow = document.querySelector("#studio-hero-returning .studio-hero__cta-row");
    if (!ctaRow || !ctaRow.parentNode) return;
    host = document.createElement("p");
    host.id = "studio-recent-path-hint";
    host.className = "studio-recent-path-hint";
    host.hidden = true;
    ctaRow.parentNode.insertBefore(host, ctaRow.nextSibling);
  }
  var recent = getRecentPaths();
  if (!recent.length) {
    show(host, false);
    return;
  }
  var path = recent[0];
  host.innerHTML = "";
  var label = document.createElement("span");
  label.textContent = "继续使用 ";
  var pathSpan = document.createElement("span");
  pathSpan.className = "studio-recent-path-hint__path";
  pathSpan.textContent = path;
  pathSpan.title = path;
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "studio-recent-path-hint__action";
  btn.textContent = "导入";
  btn.addEventListener("click", function () {
    var titleEl = $("trip-title");
    var placeEl = $("trip-place");
    var title = titleEl && titleEl.value ? titleEl.value.trim() : "";
    var place = placeEl && placeEl.value ? placeEl.value.trim() : "";
    startImport({
      albumPath: path,
      title: title || undefined,
      place: place || undefined,
    });
  });
  host.appendChild(label);
  host.appendChild(pathSpan);
  host.appendChild(document.createTextNode("？"));
  host.appendChild(btn);
  show(host, true);
}

// ── Trip cards (all trips grid) ──
export function renderTripCard(trip, options) {
  options = options || {};
  var isDemo = trip.tripId && trip.tripId.indexOf("demo") >= 0;
  var href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
  if (trip.longshotStale) {
    href = "/" + trip.tripId + "/index.html?focus=longshot";
  }

  var card = document.createElement("a");
  card.className = "studio-trip-card";
  card.href = href;
  card.title = trip.title || trip.tripId;

  // Highlight first return (only on the latest trip)
  var needsHighlight = false;
  if (options.highlight &&
      localStorage.getItem(LS.firstPreviewDone) === "1" &&
      !localStorage.getItem(LS.firstReturnHighlight) &&
      S.currentState === "IdleReturning") {
    needsHighlight = true;
  }
  if (needsHighlight) {
    card.classList.add("studio-trip-card--highlight");
    setTimeout(function () {
      card.classList.remove("studio-trip-card--highlight");
      localStorage.setItem(LS.firstReturnHighlight, "1");
    }, 5000);
  }

  if (trip.previewRelPath) {
    var img = document.createElement("img");
    img.alt = trip.title || "游记封面";
    img.loading = options.eager ? "eager" : "lazy";
    if (options.eager) img.setAttribute("fetchpriority", "high");
    img.src = "/" + trip.tripId + "/" + trip.previewRelPath;
    img.onerror = function () {
      img.remove();
      var ph = document.createElement("div");
      ph.className = "studio-trip-card__placeholder";
      ph.textContent = trip.title || trip.tripId;
      card.insertBefore(ph, card.firstChild);
    };
    card.appendChild(img);
  } else {
    var placeholder = document.createElement("div");
    placeholder.className = "studio-trip-card__placeholder";
    placeholder.textContent = trip.title || trip.tripId;
    card.appendChild(placeholder);
  }

  if (isDemo) {
    var badge = document.createElement("span");
    badge.className = "studio-trip-card__demo";
    badge.textContent = "示例";
    card.appendChild(badge);
  }

  var meta = document.createElement("div");
  meta.className = "studio-trip-card__meta";

  var name = document.createElement("p");
  name.className = "studio-trip-card__title";
  name.textContent = trip.title || trip.tripId;
  meta.appendChild(name);

  var sub = document.createElement("p");
  sub.className = "studio-trip-card__sub";
  var subParts = [];
  if (trip.photoCount) subParts.push(trip.photoCount + " 张");
  if (trip.updatedAt) subParts.push(formatUpdatedAt(trip.updatedAt));
  sub.textContent = subParts.join(" · ");
  if (trip.longshotStale) {
    var stale = document.createElement("span");
    stale.className = "studio-trip-card__stale";
    stale.textContent = "长图待更新";
    sub.appendChild(document.createTextNode(" "));
    sub.appendChild(stale);
  }
  meta.appendChild(sub);

  card.appendChild(meta);
  return card;
}

export function renderAllTrips() {
  var list = $("studio-trips-list");
  var count = $("studio-trips-count");
  if (!list) return;
  list.innerHTML = "";

  S.tripsData.forEach(function (trip, i) {
    list.appendChild(renderTripCard(trip, { highlight: i === 0, eager: i < 8 }));
  });

  var addCard = document.createElement("button");
  addCard.type = "button";
  addCard.className = "studio-trip-card studio-trip-card--add";
  addCard.textContent = "新建游记";
  addCard.addEventListener("click", function () {
    requestNativeFolder($("trip-title").value, $("trip-place").value);
  });
  list.appendChild(addCard);

  if (count) {
    var total = S.tripsTotalCount || S.tripsData.length;
    count.textContent = "共 " + total + " 篇";
  }

  var moreBtn = $("studio-trips-more");
  if (moreBtn) show(moreBtn, S.tripsData.length < S.tripsTotalCount);
}

export function renderFooterStats() {
  var el = $("studio-footer-stats");
  if (!el) return;
  if (S.tripsData.length === 0) {
    el.textContent = "照片与游记保存在本机 · 不上传云端";
    return;
  }
  var total = S.tripsTotalCount || S.tripsData.length;
  var photos = S.tripsData.reduce(function (s, t) { return s + (t.photoCount || 0); }, 0);
  el.textContent = "已生成 " + total + " 篇 · 累计 " + photos + " 张照片 · 全部保存在本机";
}

export function renderCancelNotice() {
  var raw = "";
  try { raw = localStorage.getItem(LS.lastCancelled) || ""; } catch (e) {}
  var data = null;
  if (raw) { try { data = JSON.parse(raw); } catch (e) { data = null; } }

  function applyTo(el) {
    if (!el) return;
    if (!data || !data.echo) { show(el, false); return; }
    el.innerHTML = "";
    var label = document.createElement("span");
    label.textContent = "上次取消：" + data.echo;
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "studio-cancel-notice__action";
    btn.textContent = "重新开始";
    btn.addEventListener("click", function () {
      if (data.body) startImport(data.body);
      try { localStorage.removeItem(LS.lastCancelled); } catch (e) {}
    });
    var dismiss = document.createElement("button");
    dismiss.type = "button";
    dismiss.className = "studio-cancel-notice__action";
    dismiss.textContent = "忽略";
    dismiss.style.opacity = ".6";
    dismiss.addEventListener("click", function () {
      try { localStorage.removeItem(LS.lastCancelled); } catch (e) {}
      show(el, false);
    });
    el.appendChild(label);
    el.appendChild(btn);
    el.appendChild(dismiss);
    show(el, true);
  }
  applyTo($("studio-cancel-notice"));
  applyTo($("studio-cancel-notice-returning"));
}

registerRender(render);
