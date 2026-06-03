/**
 * 首页 v2 · Bento 首屏渲染（示例 + 用户 Tab · 方案 A/B′）。
 */
import { V2, $, show } from "./store.js";
import { isDemoTrip } from "../js/constants.js";
import { cssBackgroundImage, formatUpdatedAt } from "../js/dom.js";
import { manifestAssetUrl } from "./manifest.js";
import { initCarousel } from "./carousel.js";
import { initPhoneStrip } from "./phone-strip.js";
import { resolveLayoutTier } from "./layout-tier.js";
import { trackStudioEvent } from "../js/analytics.js";
import { initBentoTabs, syncTabUi } from "./bento-tabs.js";
import { pickRecentUserTrips } from "./trip-preview.js";

var _phoneStripApi = null;
var _phoneFrameObserver = null;
var _phoneFrameWired = false;

function clampPhoneHeight(px) {
  var v = Number(px) || 0;
  if (v <= 0) return 0;
  if (v < 520) return 520;
  if (v > 980) return 980;
  return Math.round(v);
}

var PHONE_VISUAL_SCALE = 1.15;

function webPhoneAnchor() {
  return document.querySelector(".v2-carousel");
}

/** 以 Web 轮播 viewport 定手机高度（两侧 footer 行由 CSS Grid 底边对齐）。 */
function syncPhoneFrameFromWeb() {
  var phone = $("v2-phone");
  if (!phone) return;
  var carousel = webPhoneAnchor();
  var viewport = carousel && carousel.querySelector(".v2-carousel__viewport");
  var mobileCell = document.querySelector(".v2-bento__mobile");
  if (!viewport || !viewport.getBoundingClientRect) return;
  var h = viewport.getBoundingClientRect().height || 0;
  var target = clampPhoneHeight(h);
  if (mobileCell) {
    var cellW = mobileCell.clientWidth || 0;
    if (cellW > 0) {
      var byWidth = Math.floor((cellW * 16) / 9 / PHONE_VISUAL_SCALE);
      target = Math.min(target, byWidth);
    }
  }
  if (target <= 0) return;
  phone.style.setProperty("--v2-phone-height", target + "px");
  phone.style.setProperty("--v2-phone-scale", String(PHONE_VISUAL_SCALE));
  if (_phoneStripApi && _phoneStripApi.relayout) _phoneStripApi.relayout();
}

function schedulePhoneFrameSync() {
  requestAnimationFrame(function () {
    syncPhoneFrameFromWeb();
  });
}

function ensurePhoneFrameSync() {
  if (_phoneFrameWired) return;
  _phoneFrameWired = true;
  var viewport = document.querySelector(".v2-carousel__viewport");
  if (typeof ResizeObserver === "function" && viewport) {
    _phoneFrameObserver = new ResizeObserver(function () {
      schedulePhoneFrameSync();
    });
    _phoneFrameObserver.observe(viewport);
  }
  window.addEventListener("resize", schedulePhoneFrameSync);
}

function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {
    return false;
  }
}

function resetBackgroundLayer() {
  var bg = $("v2-bento-bg");
  if (!bg) return;
  bg.style.backgroundImage = "";
  bg.classList.remove("is-kenburns");
}

/** 背景：预加载成功才铺图，失败保留暗色渐变兜底（§11.4 / §12.4 L3）。 */
export function renderBackground(manifest, tier) {
  var bg = $("v2-bento-bg");
  if (!bg || !manifest || !manifest.assets) return;
  var url = manifestAssetUrl(manifest, "background");
  if (!url) return;
  var img = new Image();
  img.onload = function () {
    var bgImg = cssBackgroundImage(url);
    if (bgImg) bg.style.backgroundImage = bgImg;
    var motionOk = tier !== "L1" && tier !== "L3";
    var userOk = manifest.source !== "user" || motionOk;
    if (userOk && motionOk && !prefersReducedMotion()) bg.classList.add("is-kenburns");
  };
  img.onerror = function () { /* 保留 CSS 暗色兜底 */ };
  img.src = url;
}

/**
 * 冷启动 Importing 静帧背景（§9.2 / AC-HP2-17）。
 */
export function renderColdStartBackground(manifest) {
  var bg = $("v2-bento-bg");
  if (!bg) return;
  if (bg.style.backgroundImage) return;
  if (!manifest || !manifest.assets) return;
  var url = manifestAssetUrl(manifest, "background");
  if (!url) return;
  var img = new Image();
  img.onload = function () {
    var bgImg = cssBackgroundImage(url);
    if (bgImg) bg.style.backgroundImage = bgImg;
    bg.classList.remove("is-kenburns");
  };
  img.src = url;
}

/** 9:16 长图 · 竖向一屏一章（箭头 / 圆点 / ↑↓）。 */
export function renderPhone(manifest, tier) {
  _phoneStripApi = initPhoneStrip(manifest, { tier: tier });
  schedulePhoneFrameSync();
}

/** 工作台左栏 · 最近 3 本画册卡（无「最近编辑」标 / 无张数，仅标题）。 */
export function renderBenchRecent() {
  var sample = $("v2-bench-sample");
  var recentHost = $("v2-bench-recent");
  var list = $("v2-bench-recent-list");
  var left = document.querySelector(".v2-bench__left");
  var bench = document.querySelector(".v2-bench");
  if (!sample || !recentHost || !list) return;

  var recent = pickRecentUserTrips(V2.trips).slice(0, 3);
  list.innerHTML = "";

  if (!recent.length) {
    show(sample, true);
    show(recentHost, false);
    if (left) left.classList.remove("v2-bench__left--recent");
    if (bench) bench.classList.remove("v2-bench--recent");
    return;
  }

  recent.forEach(function (trip, idx) {
    var card = document.createElement("a");
    card.className = "v2-bench__recent-card";
    var href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    if (trip.longshotStale) href = "/" + trip.tripId + "/index.html?focus=longshot";
    card.href = href;
    card.title = (trip.title || trip.tripId)
      + (trip.updatedAt ? " · " + formatUpdatedAt(trip.updatedAt) : "")
      + (trip.longshotStale ? " · 长图待更新" : "");

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
      stale.className = "v2-bench__recent-card__stale";
      stale.textContent = "长图待更新";
      card.appendChild(stale);
    }

    var meta = document.createElement("div");
    meta.className = "v2-bench__recent-card__meta";
    var title = document.createElement("p");
    title.className = "v2-bench__recent-card__title";
    title.textContent = trip.title || trip.tripId;
    meta.appendChild(title);
    card.appendChild(meta);
    list.appendChild(card);
  });

  show(sample, false);
  show(recentHost, true);
  if (left) left.classList.add("v2-bench__left--recent");
  if (bench) bench.classList.add("v2-bench--recent");
}

/** 工作台 bench。 */
export function renderBench(manifest) {
  renderBenchRecent();
  if (!manifest) return;
  var titleEl = $("v2-bench-title");
  var metaEl = $("v2-bench-meta");
  var thumb = $("v2-bench-thumb");
  var sampleFlag = $("v2-bench-sample-flag");
  var resumeBtn = $("v2-bench-resume");
  var recentBtn = $("v2-bench-recent");
  if (titleEl && manifest.title) titleEl.textContent = manifest.title;
  if (sampleFlag) {
    show(sampleFlag, manifest.source !== "user");
  }
  if (metaEl) {
    var meta = manifest.meta || {};
    var parts = manifest.source === "user" ? ["我的画册"] : ["自动生成"];
    if (meta.photoCount) parts.push(meta.photoCount + " 张");
    if (meta.chapterCount) parts.push(meta.chapterCount + " 章");
    metaEl.textContent = parts.join(" · ");
  }
  var resumeTrip = V2.trips.find(function (t) {
    return !isDemoTrip(t);
  });
  if (resumeBtn) {
    resumeBtn.disabled = !resumeTrip;
    resumeBtn.dataset.tripId = resumeTrip ? resumeTrip.tripId : "";
    if (!resumeBtn.dataset.wired) {
      resumeBtn.dataset.wired = "1";
      resumeBtn.addEventListener("click", function () {
        var tripId = resumeBtn.dataset.tripId;
        if (!tripId) return;
        var trip = V2.trips.find(function (t) { return t.tripId === tripId; });
        if (!trip) return;
        window.location.href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
      });
    }
  }
  if (recentBtn && !recentBtn.dataset.wired) {
    recentBtn.dataset.wired = "1";
    recentBtn.addEventListener("click", function () {
      var shelf = $("v2-shelf");
      if (shelf && !shelf.hidden) {
        shelf.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
      if (typeof studioToast === "function") {
        studioToast("暂无最近作品", { duration: 1800 });
      }
    });
  }
  if (thumb && manifest.assets && manifest.assets.background) {
    var url = manifestAssetUrl(manifest, "background");
    var probe = new Image();
    probe.onload = function () {
      var bgImg = cssBackgroundImage(url);
      if (bgImg) thumb.style.backgroundImage = bgImg;
    };
    probe.src = url;
  }
}

/** 重绘 Bento 预览区（Tab 切换 / manifest 变更）。 */
export function renderBentoSurface(manifest) {
  resetBackgroundLayer();
  var tier = resolveLayoutTier({ manifestError: !manifest });
  V2.layoutTier = tier;
  if (!manifest) return;
  renderBackground(manifest, tier);
  initCarousel(manifest, { tier: tier });
  renderPhone(manifest, tier);
  renderBench(manifest);
  ensurePhoneFrameSync();
  schedulePhoneFrameSync();
}

/** 渲染 Bento 首屏壳层 + 当前 manifest 面。 */
export function renderBentoEmpty(manifest) {
  show($("v2-loading"), false);
  show($("v2-headline"), true);
  show($("v2-frame"), true);
  show($("v2-importing"), false);

  initBentoTabs();
  syncTabUi();

  trackStudioEvent("layout_tier", {
    tier: resolveLayoutTier({ manifestError: !manifest }),
    surface: "bento",
  });

  renderBentoSurface(manifest);
}
