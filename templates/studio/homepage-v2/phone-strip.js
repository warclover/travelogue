/**
 * 首页 v2 · 9:16 手机框章节切换（与 Web carousel 对称 · 横向一屏一章）。
 *
 * 复用 carousel-logic（scroll 步长 = viewport 高）。
 */
import {
  clampIndex, scrollLeftFor, indexFromScrollLeft, canPrev, canNext,
} from "./carousel-logic.js";
import { longshotPages, longshotPageUrl } from "./manifest.js";
import { shouldEagerCarouselPage } from "./layout-tier.js";
import { $ } from "./store.js";

var _disposeActive = function () {};

/** 竖条/整卷长图：章内竖滚；竖版样张仍 cover 铺满（避免 object-fit 裁切）。 */
function useScrollPreview(page) {
  return !!(page && page.scrollPreview);
}

/** 竖图（高>宽）在章内应完整展示并可上下滚，而非 cover 裁切。 */
function shouldScrollPortraitImage(img) {
  if (!img || img.naturalWidth <= 0) return false;
  return img.naturalHeight / img.naturalWidth > 1.05;
}

function applyScrollSlideClass(slide, page, img) {
  if (useScrollPreview(page) || (img && shouldScrollPortraitImage(img))) {
    slide.classList.add("v2-phone-strip__slide--scroll");
    slide.dataset.scrollPreview = "1";
  }
}

function mountSlideImage(slide, img, onSlideReady) {
  slide.innerHTML = "";
  slide.appendChild(img);
  if (typeof onSlideReady === "function") onSlideReady();
}

function buildSlide(manifest, page, index, tier, onSlideReady) {
  var slide = document.createElement("div");
  slide.className = "v2-phone-strip__slide";
  slide.setAttribute("role", "group");
  slide.setAttribute("aria-label", (page && page.label) || "长图章节");

  var ph = document.createElement("div");
  ph.className = "v2-phone-strip__slide-ph";
  ph.textContent = (page && page.label) || "";
  slide.appendChild(ph);

  var url = longshotPageUrl(manifest, page);
  if (!url) return slide;

  if (useScrollPreview(page)) {
    slide.classList.add("v2-phone-strip__slide--scroll");
    slide.dataset.scrollPreview = "1";
  }

  var attachImg = function () {
    var img = document.createElement("img");
    img.className = "v2-phone-strip__slide-img";
    img.alt = (page && page.label) || "";
    if (index === 0) img.setAttribute("fetchpriority", "high");
    if (tier === "L2" && index > 0) img.loading = "lazy";
    img.onload = function () {
      if (!useScrollPreview(page) && img.naturalWidth > 0 && img.naturalHeight / img.naturalWidth > 2.8) {
        slide.classList.add("v2-phone-strip__slide--scroll");
      }
      mountSlideImage(slide, img, onSlideReady);
    };
    img.onerror = function () { /* 保留 placeholder */ };
    img.src = url;
    if (img.complete && img.naturalWidth > 0) {
      if (!useScrollPreview(page) && img.naturalHeight / img.naturalWidth > 2.8) {
        slide.classList.add("v2-phone-strip__slide--scroll");
      }
      mountSlideImage(slide, img, onSlideReady);
    }
  };

  if (shouldEagerCarouselPage(index, tier)) attachImg();
  else {
    slide.dataset.lazySrc = url;
  }
  return slide;
}

function ensureSlideLoaded(slide, onSlideReady) {
  if (!slide || !slide.dataset.lazySrc) return;
  var url = slide.dataset.lazySrc;
  delete slide.dataset.lazySrc;
  var label = slide.getAttribute("aria-label") || "";
  var img = document.createElement("img");
  img.className = "v2-phone-strip__slide-img";
  img.alt = label;
  img.loading = "lazy";
  img.onload = function () {
    mountSlideImage(slide, img, onSlideReady);
  };
  img.onerror = function () { /* 保留 placeholder */ };
  img.src = url;
  if (img.complete && img.naturalWidth > 0) mountSlideImage(slide, img, onSlideReady);
}

/**
 * @param {object} manifest
 * @param {{ tier?: string }} [opts]
 */
export function initPhoneStrip(manifest, opts) {
  _disposeActive();
  opts = opts || {};
  var tier = opts.tier || "L0";
  var track = $("v2-phone-track");
  var dotsHost = $("v2-phone-dots");
  var prevBtn = $("v2-phone-prev");
  var nextBtn = $("v2-phone-next");
  var screen = $("v2-phone-screen");
  var footer = $("v2-phone-strip") && $("v2-phone-strip").querySelector(".v2-phone-strip__footer");
  var viewport = track ? track.parentElement : null;
  if (!track || !dotsHost) return null;

  var pages = longshotPages(manifest);
  var pageCount = pages.length;
  var index = 0;
  var syncing = false;
  var syncReleaseTimer = null;
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

  track.innerHTML = "";
  dotsHost.innerHTML = "";

  if (!pageCount) {
    track.innerHTML = '<div class="v2-phone-strip__slide-ph">暂无长图预览</div>';
    if (prevBtn) prevBtn.disabled = true;
    if (nextBtn) nextBtn.disabled = true;
    return null;
  }

  var onSlideReady = opts.onSlideReady;
  var slideEls = pages.map(function (page, i) {
    var slide = buildSlide(manifest, page, i, tier, onSlideReady);
    track.appendChild(slide);
    return slide;
  });

  var dotEls = pages.map(function (page, i) {
    var dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-selected", "false");
    dot.setAttribute("aria-label", page.label || "第 " + (i + 1) + " 段");
    dot.dataset.index = String(i);
    bind(dot, "click", function () { go(i); });
    dotsHost.appendChild(dot);
    return dot;
  });

  function viewportWidth() {
    var vw = (viewport && viewport.clientWidth) || 0;
    if (vw > 0) return vw;
    if (slideEls.length && slideEls[0].offsetWidth) return slideEls[0].offsetWidth;
    if (track && track.clientWidth) return track.clientWidth;
    if (viewport && viewport.getBoundingClientRect) {
      return viewport.getBoundingClientRect().width || 0;
    }
    return 0;
  }

  function applyChromeVisibility() {
    var multi = pageCount > 1;
    if (prevBtn) prevBtn.hidden = !multi;
    if (nextBtn) nextBtn.hidden = !multi;
    if (footer) footer.hidden = !multi;
  }

  function domMaxScrollLeft() {
    var vw = viewportWidth();
    return Math.max(0, (track.scrollWidth || 0) - vw);
  }

  function scrollTargetFor(idx) {
    var vw = viewportWidth();
    if (pageCount > 0 && idx === pageCount - 1) return domMaxScrollLeft();
    return scrollLeftFor(idx, vw, pageCount);
  }

  function indexFromDomScrollLeft(scrollLeft) {
    var max = domMaxScrollLeft();
    if (pageCount > 0 && scrollLeft >= max - 2) return pageCount - 1;
    return indexFromScrollLeft(scrollLeft, viewportWidth(), pageCount);
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
  }

  function go(requested, goOpts) {
    goOpts = goOpts || {};
    index = clampIndex(requested, pageCount);
    ensureSlideLoaded(slideEls[index], onSlideReady);
    if (index + 1 < slideEls.length) ensureSlideLoaded(slideEls[index + 1], onSlideReady);
    if (!goOpts.fromScroll) {
      syncing = true;
      if (scrollTimer) clearTimeout(scrollTimer);
      if (syncReleaseTimer) clearTimeout(syncReleaseTimer);
      var prevBehavior = track.style.scrollBehavior;
      track.style.scrollBehavior = "auto";
      var target = scrollTargetFor(index);
      track.scrollLeft = target;
      if (index > 0 && target <= 0 && viewportWidth() <= 0) {
        requestAnimationFrame(function () {
          track.scrollLeft = scrollTargetFor(index);
        });
      }
      track.style.scrollBehavior = prevBehavior;
      syncReleaseTimer = setTimeout(function () {
        syncing = false;
        syncReleaseTimer = null;
      }, 280);
    }
    var active = slideEls[index];
    if (active && active.classList.contains("v2-phone-strip__slide--scroll")) active.scrollTop = 0;
    syncUi();
  }

  if (prevBtn) {
    bind(prevBtn, "click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      go(index - 1);
    });
  }
  if (nextBtn) {
    bind(nextBtn, "click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      go(index + 1);
    });
  }

  bind(track, "scroll", function () {
    if (syncing) return;
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function () {
      var i = indexFromDomScrollLeft(track.scrollLeft);
      if (i !== index) { index = i; syncUi(); }
    }, 120);
  });

  if (screen) {
    bind(screen, "keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(index - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(index + 1); }
    });
    screen.setAttribute(
      "aria-label",
      pageCount > 1
        ? "微信长图 · " + pageCount + " 段 · 左右切换章节 · 章内可上下滚动"
        : "微信长图预览 · 可上下滚动"
    );
  }

  applyChromeVisibility();
  requestAnimationFrame(function () {
    go(0);
    applyChromeVisibility();
  });

  function relayout() {
    go(index, { fromScroll: false });
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

  return {
    go: go,
    current: function () { return index; },
    count: pageCount,
    relayout: relayout,
    destroy: dispose,
  };
}
