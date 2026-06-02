/**
 * 首页 v2 · Bento 首屏渲染（示例 + 用户 Tab · 方案 A/B′）。
 */
import { V2, $, show } from "./store.js";
import { isDemoTrip } from "../js/constants.js";
import { cssBackgroundImage } from "../js/dom.js";
import { manifestAssetUrl } from "./manifest.js";
import { initCarousel } from "./carousel.js";
import { initPhoneStrip } from "./phone-strip.js";
import { resolveLayoutTier } from "./layout-tier.js";
import { trackStudioEvent } from "../js/analytics.js";
import { initBentoTabs, syncTabUi } from "./bento-tabs.js";

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

function webPhoneAnchor() {
  return document.querySelector(".v2-carousel");
}

/** 以 Web 轮播整体块（含 dots/hint）为锚定，保证底缘观感一致。 */
function syncPhoneFrameFromWeb() {
  var phone = $("v2-phone");
  if (!phone) return;
  var webViewport = webPhoneAnchor();
  var mobileCell = document.querySelector(".v2-bento__mobile");
  if (!webViewport || !webViewport.getBoundingClientRect) return;
  var h = webViewport.getBoundingClientRect().height || 0;
  var target = clampPhoneHeight(h);
  if (mobileCell) {
    var cellW = mobileCell.clientWidth || 0;
    if (cellW > 0) {
      // 宽度约束：手机框比例固定 9:16，避免溢出右列。
      var byWidth = Math.floor((cellW * 16) / 9);
      target = Math.min(target, byWidth);
    }
  }
  if (target <= 0) return;
  phone.style.setProperty("--v2-phone-height", target + "px");
  // 第二阶段：底边硬对齐，抵消不同显示器下的行内偏移。
  var wr = webViewport.getBoundingClientRect();
  var pr = phone.getBoundingClientRect();
  var delta = Math.round(pr.bottom - wr.bottom);
  if (Math.abs(delta) > 1) {
    phone.style.transform = "translateY(" + String(-delta) + "px)";
  } else {
    phone.style.transform = "";
  }
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
  var webViewport = webPhoneAnchor();
  if (typeof ResizeObserver === "function" && webViewport) {
    _phoneFrameObserver = new ResizeObserver(function () {
      schedulePhoneFrameSync();
    });
    _phoneFrameObserver.observe(webViewport);
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

/** 工作台 bench。 */
export function renderBench(manifest) {
  if (!manifest) return;
  var titleEl = $("v2-bench-title");
  var metaEl = $("v2-bench-meta");
  var thumb = $("v2-bench-thumb");
  var sampleFlag = $("v2-bench-sample-flag");
  var statPhotosEl = $("v2-bench-stat-photos");
  var statChaptersEl = $("v2-bench-stat-chapters");
  var statEstimateEl = $("v2-bench-stat-estimate");
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
  var meta = manifest.meta || {};
  if (statPhotosEl) {
    statPhotosEl.textContent = (meta.photoCount || 0) + " 张照片";
  }
  if (statChaptersEl) {
    statChaptersEl.textContent = (meta.chapterCount || 0) + " 章";
  }
  if (statEstimateEl) {
    var count = Number(meta.photoCount) || 0;
    var estimate = count > 140 ? "约 5 分钟" : count > 90 ? "约 4 分钟" : "约 3 分钟";
    statEstimateEl.textContent = estimate;
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
