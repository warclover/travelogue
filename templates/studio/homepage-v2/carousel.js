/**
 * 首页 v2 · 16:9 Carousel DOM 控制器（M20-b）。
 *
 * 行为（PRD §6.4 / DATA-CONTRACT §1.3）：
 *  - 一屏一页；每次滑 1 页
 *  - D-10：到头 clamp，不 wrap；首尾箭头 disabled
 *  - 奇数尾页：最后索引左对齐，右侧留白
 *  - 键盘 ←/→
 *  - dots `aria-current`
 *
 * 纯逻辑见 carousel-logic.js（含 node 单测）。
 */
import {
  clampIndex, scrollLeftFor, indexFromScrollLeft, canPrev, canNext,
} from "./carousel-logic.js";
import { pageImageUrl } from "./manifest.js";
import { trackStudioEvent } from "../js/analytics.js";
import { shouldEagerCarouselPage } from "./layout-tier.js";
import { V2, $ } from "./store.js";

var _disposeActive = function () {};

function carouselHintText(manifest, index, pageCount) {
  if (!pageCount) return "";
  var isDemo = !manifest || manifest.source !== "user";
  var prefix = isDemo ? "示例 · " : "";
  var title = (manifest && manifest.title) || "作品";
  return prefix + title + " · 第 " + (index + 1) + " / " + pageCount + " 页";
}

function pagePlaceholderText(page) {
  if (!page) return "";
  if (page.label) return page.label;
  if (page.role === "cover") return "封面";
  if (page.role === "epilogue") return "— 尾声 —";
  return "";
}

function mountCarouselSlideImage(slide, img) {
  slide.innerHTML = "";
  slide.appendChild(img);
}

function buildSlide(manifest, page, index, tier) {
  var slide = document.createElement("div");
  slide.className = "v2-carousel__slide";
  slide.setAttribute("role", "group");
  slide.setAttribute("aria-label", (page && page.label) || "页面");

  var ph = document.createElement("div");
  ph.className = "v2-carousel__slide-ph";
  ph.textContent = pagePlaceholderText(page);
  slide.appendChild(ph);

  var url = page ? pageImageUrl(manifest, page) : "";
  if (url) {
    var eager = shouldEagerCarouselPage(index, tier);
    var attachImg = function () {
      var img = document.createElement("img");
      img.className = "v2-carousel__slide-img";
      img.alt = (page && page.label) || "";
      if (eager && index === 0) img.setAttribute("fetchpriority", "high");
      if (!eager) img.loading = "lazy";
      img.onload = function () { mountCarouselSlideImage(slide, img); };
      img.onerror = function () { /* 保留 placeholder */ };
      img.src = url;
      if (img.complete && img.naturalWidth > 0) {
        mountCarouselSlideImage(slide, img);
      }
    };
    if (eager) attachImg();
    else slide.dataset.lazySrc = url;
  }
  return slide;
}

function ensureSlideLoaded(slide) {
  if (!slide || !slide.dataset.lazySrc) return;
  var url = slide.dataset.lazySrc;
  delete slide.dataset.lazySrc;
  var pageLabel = slide.getAttribute("aria-label") || "";
  var img = document.createElement("img");
  img.className = "v2-carousel__slide-img";
  img.alt = pageLabel;
  img.loading = "lazy";
  img.onload = function () { mountCarouselSlideImage(slide, img); };
  img.onerror = function () { /* 保留 placeholder */ };
  img.src = url;
  if (img.complete && img.naturalWidth > 0) {
    mountCarouselSlideImage(slide, img);
  }
}

/**
 * 初始化 carousel。返回控制器 { go, current, count }。
 * @param {object} manifest
 * @param {{ tier?: string }} [opts]
 */
export function initCarousel(manifest, opts) {
  _disposeActive();
  opts = opts || {};
  var tier = opts.tier || "L0";
  var track = $("v2-carousel-track");
  var dotsHost = $("v2-carousel-dots");
  var hint = $("v2-carousel-hint");
  var prevBtn = $("v2-carousel-prev");
  var nextBtn = $("v2-carousel-next");
  var viewport = track ? track.parentElement : null;
  if (!track || !dotsHost) return null;

  var pages = (manifest && manifest.pages) || [];
  var pageCount = pages.length;
  var index = 0;
  var syncing = false;
  var syncReleaseTimer = null;
  var lastTracked = 0; // spread_page_view 仅在真正翻页时上报（首帧不报）
  var scrollTimer = null;
  var disposed = false;
  var cleanup = [];

  function bind(el, eventName, handler, bindOpts) {
    if (!el) return;
    el.addEventListener(eventName, handler, bindOpts);
    cleanup.push(function () {
      el.removeEventListener(eventName, handler, bindOpts);
    });
  }

  function emitPage() {
    if (index === lastTracked) return;
    lastTracked = index;
    trackStudioEvent("spread_page_view", { page_index: index });
  }

  track.innerHTML = "";
  dotsHost.innerHTML = "";
  var slideEls = pages.map(function (page, i) {
    var slide = buildSlide(manifest, page, i, tier);
    track.appendChild(slide);
    return slide;
  });

  var dotEls = pages.map(function (page, i) {
    var dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-selected", "false");
    dot.setAttribute("aria-label", page.label || "第 " + (i + 1) + " 页");
    dot.dataset.index = String(i);
    bind(dot, "click", function () { go(i); });
    dotsHost.appendChild(dot);
    return dot;
  });

  if (hint) hint.textContent = carouselHintText(manifest, 0, pageCount);

  function updateHint() {
    if (hint) hint.textContent = carouselHintText(manifest, index, pageCount);
  }

  function viewportWidth() {
    return (viewport && viewport.clientWidth) || (track && track.clientWidth) || 0;
  }

  function domMaxScrollLeft() {
    var vw = viewportWidth();
    return Math.max(0, (track.scrollWidth || 0) - vw);
  }

  function scrollTargetFor(idx) {
    var slide = slideEls[idx];
    if (slide && slide.offsetLeft >= 0) return slide.offsetLeft;
    var vw = viewportWidth();
    if (idx === pageCount - 1) return domMaxScrollLeft();
    return scrollLeftFor(idx, vw, pageCount);
  }

  function indexFromDomScrollLeft(scrollLeft) {
    var sl = Number(scrollLeft) || 0;
    if (pageCount > 0 && sl >= domMaxScrollLeft() - 2) return pageCount - 1;
    for (var i = slideEls.length - 1; i >= 0; i--) {
      if (sl >= slideEls[i].offsetLeft - 2) return i;
    }
    return indexFromScrollLeft(sl, viewportWidth(), pageCount);
  }

  function syncUi() {
    dotEls.forEach(function (d, i) {
      var active = i === index;
      d.classList.toggle("is-active", active);
      d.setAttribute("aria-selected", active ? "true" : "false");
      if (active) d.setAttribute("aria-current", "true");
      else d.removeAttribute("aria-current");
    });
    if (prevBtn) prevBtn.disabled = !canPrev(index);
    if (nextBtn) nextBtn.disabled = !canNext(index, pageCount);
    updateHint();
  }

  function go(requested, opts) {
    opts = opts || {};
    index = clampIndex(requested, pageCount);
    ensureSlideLoaded(slideEls[index]);
    if (index + 1 < slideEls.length) ensureSlideLoaded(slideEls[index + 1]);
    if (index > 0) ensureSlideLoaded(slideEls[index - 1]);
    if (!opts.fromScroll) {
      syncing = true;
      if (scrollTimer) clearTimeout(scrollTimer);
      if (syncReleaseTimer) clearTimeout(syncReleaseTimer);
      var prevBehavior = track.style.scrollBehavior;
      track.style.scrollBehavior = "auto";
      track.scrollLeft = scrollTargetFor(index);
      track.style.scrollBehavior = prevBehavior;
      syncReleaseTimer = setTimeout(function () {
        syncing = false;
        syncReleaseTimer = null;
      }, 280);
    }
    syncUi();
    emitPage();
  }

  bind(prevBtn, "click", function () { go(index - 1); });
  bind(nextBtn, "click", function () { go(index + 1); });

  // 原生滚动 / 触控滑动 → 同步索引（clamp）
  bind(track, "scroll", function () {
    if (syncing) return;
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function () {
      var i = indexFromDomScrollLeft(track.scrollLeft);
      if (i !== index) { index = i; syncUi(); emitPage(); }
    }, 120);
  });

  // 键盘 ←/→（AC-HP2-19）
  var webCell = $("v2-web-cell");
  if (webCell) {
    bind(webCell, "keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(index - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(index + 1); }
    });
  }

  function dispose() {
    if (disposed) return;
    disposed = true;
    cleanup.forEach(function (fn) { fn(); });
    cleanup = [];
    if (scrollTimer) clearTimeout(scrollTimer);
    if (syncReleaseTimer) clearTimeout(syncReleaseTimer);
    scrollTimer = null;
    syncReleaseTimer = null;
    if (_disposeActive === dispose) _disposeActive = function () {};
  }
  _disposeActive = dispose;

  go(0);
  return {
    go: go,
    current: function () { return index; },
    count: pageCount,
    destroy: dispose,
  };
}
