/**
 * 首页 v2 · Bento 首屏渲染（示例 + 用户 Tab · 方案 A/B′）。
 */
import { V2, $, show, setV2SkipLinkTarget } from "./store.js";
import { isDemoTrip } from "../js/constants.js";
import { cssBackgroundImage, formatUpdatedAt } from "../js/dom.js";
import { manifestAssetUrl } from "./manifest.js";
import { initCarousel } from "./carousel.js";
import { initPhoneStrip } from "./phone-strip.js";
import { resolveLayoutTier } from "./layout-tier.js";
import { trackStudioEvent } from "../js/analytics.js";
import { syncBentoStaleBar, triggerHomepageRecurate } from "./bento-stale.js";
import { shelfResumeActions } from "./shelf-actions-logic.js";
import { tripPreviewHref } from "../js/trip-stale.js";

var _phoneStripApi = null;
var _phoneFrameObserver = null;
var _phoneFrameWired = false;
var _phoneSyncAttempts = 0;
var PHONE_SYNC_MAX_ATTEMPTS = 16;
var _pendingPhoneManifest = null;
var _pendingPhoneTier = "L0";

function clampPhoneHeight(px) {
  var v = Number(px) || 0;
  if (v <= 0) return 0;
  if (v < 520) return 520;
  if (v > 980) return 980;
  return Math.round(v);
}

var PHONE_VISUAL_SCALE = 1.10;
var PHONE_VISUAL_SCALE_MAX = 1.22;
var PHONE_CAPTION_GAP = 6;

function phoneCaptionReserve() {
  var caption = document.querySelector(".v2-bento__mobile .v2-cell-label");
  if (!caption) return 20;
  return Math.ceil(caption.getBoundingClientRect().height) + PHONE_CAPTION_GAP;
}

/** 按右列可用宽高放大手机框；底边由 grid 锚定，左侧 web 预览不受影响。 */
function syncPhoneFrameFromWeb() {
  var phone = $("v2-phone");
  if (!phone) return;
  var mobileCell = document.querySelector(".v2-bento__mobile");
  if (!mobileCell) return;

  var cellW = mobileCell.clientWidth || 0;
  var cellH = mobileCell.clientHeight || 0;
  if (cellW <= 0 || cellH <= 0) {
    if (_phoneSyncAttempts < PHONE_SYNC_MAX_ATTEMPTS) {
      _phoneSyncAttempts += 1;
      requestAnimationFrame(syncPhoneFrameFromWeb);
    }
    return;
  }
  _phoneSyncAttempts = 0;

  var availableH = Math.max(0, cellH - phoneCaptionReserve());
  var byWidth = Math.floor((cellW * 16) / (9 * PHONE_VISUAL_SCALE));
  var byHeight = Math.floor(availableH / PHONE_VISUAL_SCALE);
  var target = clampPhoneHeight(Math.min(byWidth, byHeight));
  if (target <= 0) return;

  var scale = PHONE_VISUAL_SCALE;
  var maxScale = Math.min(
    availableH / target,
    (cellW * 16) / (9 * target)
  );
  if (maxScale > scale) {
    scale = Math.min(maxScale, PHONE_VISUAL_SCALE_MAX);
  }

  phone.style.setProperty("--v2-phone-height", target + "px");
  phone.style.setProperty("--v2-phone-scale", String(scale));
  if (_phoneStripApi && _phoneStripApi.relayout) _phoneStripApi.relayout();
}

function schedulePhoneFrameSync() {
  requestAnimationFrame(function () {
    syncPhoneFrameFromWeb();
    requestAnimationFrame(syncPhoneFrameFromWeb);
  });
}

function ensurePhoneFrameSync() {
  if (_phoneFrameWired) return;
  _phoneFrameWired = true;
  var mobileCell = document.querySelector(".v2-bento__mobile");
  if (typeof ResizeObserver === "function" && mobileCell) {
    _phoneFrameObserver = new ResizeObserver(function () {
      schedulePhoneFrameSync();
    });
    _phoneFrameObserver.observe(mobileCell);
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

function mountPhoneStrip(manifest, tier) {
  _phoneStripApi = initPhoneStrip(manifest, {
    tier: tier,
    onSlideReady: function () {
      if (_phoneStripApi && _phoneStripApi.relayout) _phoneStripApi.relayout();
    },
  });
  if (_phoneStripApi && _phoneStripApi.relayout) _phoneStripApi.relayout();
}

/** 9:16 长图 · 竖向一屏一章（箭头 / 圆点 / ↑↓）。 */
export function renderPhone(manifest, tier) {
  _pendingPhoneManifest = manifest;
  _pendingPhoneTier = tier || "L0";
  schedulePhoneFrameSync();
  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      if (!_pendingPhoneManifest) return;
      mountPhoneStrip(_pendingPhoneManifest, _pendingPhoneTier);
    });
  });
}

function openBenchTrip(trip, focusLongshot) {
  var url = trip.previewUrl || tripPreviewHref(trip);
  if (focusLongshot) {
    url += (url.indexOf("?") >= 0 ? "&" : "?") + "focus=longshot";
  }
  window.location.href = url;
}

function resolveDemoTrip() {
  return V2.trips.find(function (t) { return isDemoTrip(t); }) || null;
}

function syncBenchContinueButton() {
  var btn = $("v2-bench-continue");
  if (!btn) return;
  var trip = V2.userPreviewTrip;
  if (trip) {
    var actions = shelfResumeActions(trip);
    var primary = actions.filter(function (a) { return a.primary; })[0] || actions[0];
    btn.textContent = primary && primary.kind === "open" ? "继续" : (primary && primary.label) || "继续";
    btn.disabled = false;
    return;
  }
  btn.textContent = "继续";
  btn.disabled = !resolveDemoTrip();
}

function wireBenchContinue() {
  var btn = $("v2-bench-continue");
  if (!btn || btn.dataset.wired === "1") return;
  btn.dataset.wired = "1";
  btn.addEventListener("click", function () {
    var trip = V2.userPreviewTrip || resolveDemoTrip();
    if (!trip) return;
    var actions = shelfResumeActions(trip);
    var primary = actions.filter(function (a) { return a.primary; })[0] || actions[0];
    trackStudioEvent("shelf_resume_click", {
      trip_id: trip.tripId,
      stale: primary && primary.kind !== "open",
      kind: primary ? primary.kind : "open",
      surface: "bench",
    });
    if (primary && primary.triggerCurate) {
      triggerHomepageRecurate(trip.tripId, "bench_continue");
      return;
    }
    openBenchTrip(trip, !!(primary && primary.focusLongshot));
  });
}

/** 工作台 bench · 最近一本单卡（§4.4）。 */
export function renderBench(manifest) {
  if (!manifest) return;
  var titleEl = $("v2-bench-title");
  var metaEl = $("v2-bench-meta");
  var thumb = $("v2-bench-thumb");
  var sampleFlag = $("v2-bench-sample-flag");
  var trip = V2.userPreviewTrip;

  if (titleEl) {
    titleEl.textContent = (trip && trip.title) || manifest.title || (trip && trip.tripId) || "最近一本";
  }
  if (sampleFlag) {
    show(sampleFlag, !trip);
  }
  if (metaEl) {
    var meta = manifest.meta || {};
    var parts = trip ? ["最近一本"] : ["示例作品"];
    if (meta.photoCount) parts.push(meta.photoCount + " 张");
    if (meta.chapterCount) parts.push(meta.chapterCount + " 章");
    if (trip && trip.updatedAt) parts.push(formatUpdatedAt(trip.updatedAt));
    metaEl.textContent = parts.join(" · ");
  }

  wireBenchContinue();
  syncBenchContinueButton();

  if (thumb) {
    var coverUrl = null;
    if (trip && trip.previewRelPath) {
      coverUrl = "/" + trip.tripId + "/" + trip.previewRelPath;
    } else if (manifest.assets && manifest.assets.background) {
      coverUrl = manifestAssetUrl(manifest, "background");
    }
    thumb.style.backgroundImage = "";
    if (coverUrl) {
      var probe = new Image();
      probe.onload = function () {
        var bgImg = cssBackgroundImage(coverUrl);
        if (bgImg) thumb.style.backgroundImage = bgImg;
      };
      probe.src = coverUrl;
    }
  }
}

/** 书架变更后重绘 Bench「最近一本」卡（§4.4）。 */
export function renderBenchRecent() {
  renderBench(V2.manifest || V2.demoManifest);
}

/** 重绘 Bento 预览区（Tab 切换 / manifest 变更）。 */
export function renderBentoSurface(manifest) {
  resetBackgroundLayer();
  var tier = resolveLayoutTier({ manifestError: !manifest });
  V2.layoutTier = tier;
  if (!manifest) {
    syncBentoStaleBar();
    return;
  }
  renderBackground(manifest, tier);
  initCarousel(manifest, { tier: tier });
  renderPhone(manifest, tier);
  renderBench(manifest);
  syncBentoStaleBar();
  ensurePhoneFrameSync();
  schedulePhoneFrameSync();
}

/** 渲染 Bento 首屏壳层 + 当前 manifest 面。 */
export function renderBentoEmpty(manifest) {
  show($("v2-loading"), false);
  show($("v2-headline"), true);
  show($("v2-frame"), true);
  show($("v2-importing"), false);
  setV2SkipLinkTarget("v2-cta");

  trackStudioEvent("layout_tier", {
    tier: resolveLayoutTier({ manifestError: !manifest }),
    surface: "bento",
  });

  renderBentoSurface(manifest);
}
