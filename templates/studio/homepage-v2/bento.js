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
import { initBentoPreviewPicker } from "./bento-preview-picker.js";
import { syncPreviewUi, setBentoPreviewTripId } from "./bento-tabs.js";
import { syncBentoStaleBar } from "./bento-stale.js";
import { pickRecentUserTrips } from "./trip-preview.js";
import { openImportSheet } from "./import-entry.js";
import { HELP_COPY, trackHelpEvent } from "../js/help-onboarding.js";

var STALE_BADGE = "可重排";
var STALE_BADGE_TIP = "版式算法有更新，可点重新排版";
var STALE_LONGSHOT = "分享图需更新";
var _demoConvertWired = false;

function syncDemoConvertCta() {
  var btn = $("v2-bench-demo-convert");
  if (!btn) return;
  var onlyDemo = pickRecentUserTrips(V2.trips).length === 0;
  show(btn, onlyDemo);
  if (!_demoConvertWired) {
    _demoConvertWired = true;
    btn.addEventListener("click", function () {
      trackHelpEvent("help_demo_convert_click", {});
      openImportSheet({ forceStep: "pick" });
      var primary = $("v2-cta");
      if (primary) {
        try {
          primary.scrollIntoView({ behavior: "smooth", block: "nearest" });
        } catch (_e) {
          /* ignore */
        }
      }
    });
  }
  if (btn.textContent !== HELP_COPY.demoConvertCta) {
    btn.textContent = HELP_COPY.demoConvertCta;
  }
}

/** D-19 · 空态 CTA 在文案区，回访 CTA 在工作台。 */
export function syncCtaPlacement() {
  var group = $("v2-cta-group");
  var cta = $("v2-cta");
  var moveEl = group || cta;
  var headlineSlot = $("v2-headline-cta-slot");
  var benchSlot = $("v2-bench-cta-slot");
  var ctaRow = document.querySelector(".v2-bench__cta-row");
  if (!moveEl || !headlineSlot || !benchSlot) return;
  var isReturning = pickRecentUserTrips(V2.trips).length > 0;
  if (isReturning) {
    benchSlot.appendChild(moveEl);
    if (cta) cta.classList.remove("is-headline");
  } else {
    headlineSlot.appendChild(moveEl);
    if (cta) cta.classList.add("is-headline");
  }
  if (ctaRow) show(ctaRow, isReturning);
}

var _phoneStripApi = null;
var _phoneFrameObserver = null;
var _phoneFrameWired = false;
var _phoneSyncAttempts = 0;
var PHONE_SYNC_MAX_ATTEMPTS = 16;
/** PDG · 背景 / bench probe 世代，过期 onload 禁止回写 DOM。 */
var _bentoMediaGen = 0;

/** @returns {number} 新世代号 */
export function bumpBentoMediaGeneration() {
  _bentoMediaGen += 1;
  return _bentoMediaGen;
}
var _pendingPhoneManifest = null;
var _pendingPhoneTier = "L0";

/** 布局高度安全域。等肩模式下以 web 预览高度为准，不再用 980 硬顶矮一截。 */
var PHONE_LAYOUT_MIN = 240;
var PHONE_LAYOUT_MAX = 1600;
var PHONE_CAPTION_GAP = 6;

function clampPhoneLayoutHeight(px) {
  var v = Number(px) || 0;
  if (v <= 0) return 0;
  if (v < PHONE_LAYOUT_MIN) return PHONE_LAYOUT_MIN;
  if (v > PHONE_LAYOUT_MAX) return PHONE_LAYOUT_MAX;
  return Math.round(v);
}

function phoneCaptionReserve() {
  var caption = document.querySelector(".v2-bento__mobile .v2-cell-label");
  if (!caption) return 20;
  return Math.ceil(caption.getBoundingClientRect().height) + PHONE_CAPTION_GAP;
}

/**
 * 右列手机框与 web 预览等肩：
 * - 高度对齐 .v2-carousel__viewport
 * - 顶边对齐 viewport 顶（底边随之对齐）
 * - 列宽不够时退回 byWidth，并用 offset 垂直居中于预览带
 */
function syncPhoneFrameFromWeb() {
  var phone = $("v2-phone");
  if (!phone) return;
  var mobileCell = document.querySelector(".v2-bento__mobile");
  if (!mobileCell) return;
  var viewport = document.querySelector(".v2-carousel__viewport");
  if (!viewport) return;

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

  var vb = viewport.getBoundingClientRect();
  var cellTop = mobileCell.getBoundingClientRect().top;
  var carouselH = Math.floor(vb.height);
  if (carouselH <= 0) return;

  var byWidth = Math.floor((cellW * 16) / 9);
  var visualH = clampPhoneLayoutHeight(Math.min(carouselH, byWidth));
  if (visualH <= 0) return;

  /* 顶齐预览（含 carousel lift）；列宽不足时在预览带内垂直居中 */
  var idealOffset = Math.round(vb.top - cellTop);
  var shortfall = Math.max(0, carouselH - visualH);
  var offsetTop = idealOffset + Math.round(shortfall / 2);

  phone.style.setProperty("--v2-phone-height", visualH + "px");
  phone.style.setProperty("--v2-phone-offset-top", offsetTop + "px");
  phone.style.setProperty("--v2-phone-scale", "1");
  syncPhoneCaptionWithWebFooter();
  if (_phoneStripApi && _phoneStripApi.relayout) _phoneStripApi.relayout();
}

/** 手机框 caption 与 web carousel footer 行对齐（补偿布局差）。 */
function syncPhoneCaptionWithWebFooter() {
  var footer = document.querySelector(".v2-carousel__footer");
  var caption = document.querySelector(".v2-bento__mobile .v2-cell-label");
  if (!footer || !caption) return;
  /* 先清旧 nudge，按未补偿位置算绝对偏移，避免残差迭代 */
  caption.style.removeProperty("--v2-cell-label-nudge");
  var delta = Math.round(footer.getBoundingClientRect().top - caption.getBoundingClientRect().top);
  if (Math.abs(delta) <= 1) return;
  caption.style.setProperty("--v2-cell-label-nudge", delta + "px");
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
  var webCell = document.querySelector(".v2-bento__web");
  if (typeof ResizeObserver === "function") {
    _phoneFrameObserver = new ResizeObserver(function () {
      schedulePhoneFrameSync();
    });
    if (mobileCell) _phoneFrameObserver.observe(mobileCell);
    if (webCell) _phoneFrameObserver.observe(webCell);
  }
  window.addEventListener("resize", schedulePhoneFrameSync);
  /* 跨显示器 / 系统缩放变化时 inner* 可能不变，补 visualViewport */
  if (window.visualViewport && typeof window.visualViewport.addEventListener === "function") {
    window.visualViewport.addEventListener("resize", schedulePhoneFrameSync);
  }
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
  var gen = _bentoMediaGen;
  var img = new Image();
  img.onload = function () {
    if (gen !== _bentoMediaGen) return;
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
  var gen = _bentoMediaGen;
  var img = new Image();
  img.onload = function () {
    if (gen !== _bentoMediaGen) return;
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

/** 工作台左栏 · 新建卡（CTA 旁「最近 3 本」缩略图暂隐藏，改由预览下拉切换）。 */
export function renderBenchRecent() {
  var sample = $("v2-bench-sample");
  var recentHost = $("v2-bench-recent");
  var list = $("v2-bench-recent-list");
  var left = document.querySelector(".v2-bench__left");
  var bench = document.querySelector(".v2-bench");
  if (!recentHost || !list) return;

  list.querySelectorAll(".v2-bench__recent-card").forEach(function (el) {
    el.remove();
  });
  show(recentHost, false);
  if (left) left.classList.remove("v2-bench__left--recent");
  if (bench) bench.classList.remove("v2-bench--recent");

  var recent = pickRecentUserTrips(V2.trips).slice(0, 3);
  show(sample, !recent.length);
  syncCtaPlacement();
  syncDemoConvertCta();
  syncBenchResumeButton();
}

/** FE-FTUE-01：仅有非 demo 用户作品时挂载「继续上次」；空态不渲染 DOM。 */
function syncBenchResumeButton() {
  var host = $("v2-bench-quick-actions");
  var resumeTrip = (V2.trips || []).find(function (t) {
    return t && !isDemoTrip(t);
  });
  var resumeBtn = $("v2-bench-resume");
  if (!resumeTrip) {
    if (resumeBtn && resumeBtn.parentNode) resumeBtn.parentNode.removeChild(resumeBtn);
    return;
  }
  if (!resumeBtn) {
    if (!host) return;
    resumeBtn = document.createElement("button");
    resumeBtn.type = "button";
    resumeBtn.className = "v2-bench__ghost-btn v2-bench__ghost-btn--secondary";
    resumeBtn.id = "v2-bench-resume";
    resumeBtn.textContent = "继续上次";
    var settings = $("v2-settings-toggle");
    if (settings && settings.parentNode === host) {
      host.insertBefore(resumeBtn, settings);
    } else {
      host.insertBefore(resumeBtn, host.firstChild);
    }
  }
  resumeBtn.disabled = false;
  resumeBtn.dataset.tripId = resumeTrip.tripId || "";
  if (!resumeBtn.dataset.wired) {
    resumeBtn.dataset.wired = "1";
    resumeBtn.addEventListener("click", function () {
      var tripId = resumeBtn.dataset.tripId;
      if (!tripId) return;
      var trip = V2.trips.find(function (t) { return t.tripId === tripId; });
      if (!trip) return;
      trackStudioEvent("bench_resume_click", {
        trip_id: tripId,
        stale: !!(trip.algorithmStale || trip.longshotStale),
      });
      window.location.href = trip.previewUrl || ("/" + trip.tripId + "/index.html");
    });
  }
}

/** 工作台 bench。 */
export function renderBench(manifest) {
  renderBenchRecent();
  if (!manifest) {
    syncBenchResumeButton();
    return;
  }
  var titleEl = $("v2-bench-title");
  var metaEl = $("v2-bench-meta");
  var thumb = $("v2-bench-thumb");
  var sampleFlag = $("v2-bench-sample-flag");
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
  syncBenchResumeButton();
  if (thumb && manifest.assets && manifest.assets.background) {
    var url = manifestAssetUrl(manifest, "background");
    var gen = _bentoMediaGen;
    var probe = new Image();
    probe.onload = function () {
      if (gen !== _bentoMediaGen) return;
      var bgImg = cssBackgroundImage(url);
      if (bgImg) thumb.style.backgroundImage = bgImg;
    };
    probe.src = url;
  }
}

/** 重绘 Bento 预览区（manifest 变更 / 预览画册切换）。 */
export function renderBentoSurface(manifest) {
  bumpBentoMediaGeneration();
  resetBackgroundLayer();
  var tier = resolveLayoutTier({ manifestError: !manifest });
  V2.layoutTier = tier;
  if (!manifest) {
    if (V2.bentoPreviewTripId) {
      initCarousel({ pages: [] }, { tier: tier });
      renderPhone({ pages: [] }, tier);
    }
    renderBench(null);
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

  initBentoPreviewPicker();
  syncPreviewUi();
  syncCtaPlacement();

  trackStudioEvent("layout_tier", {
    tier: resolveLayoutTier({ manifestError: !manifest }),
    surface: "bento",
  });

  renderBentoSurface(manifest);
}
