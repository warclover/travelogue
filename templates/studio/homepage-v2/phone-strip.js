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

function buildSlide(manifest, page, index, tier) {
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

  var attachImg = function () {
    var img = document.createElement("img");
    img.className = "v2-phone-strip__slide-img";
    img.alt = (page && page.label) || "";
    if (index === 0) img.setAttribute("fetchpriority", "high");
    if (tier === "L2" && index > 0) img.loading = "lazy";
    img.onload = function () {
      slide.innerHTML = "";
      slide.appendChild(img);
    };
    img.onerror = function () { /* 保留 placeholder */ };
    img.src = url;
  };

  if (shouldEagerCarouselPage(index, tier)) attachImg();
  else {
    slide.dataset.lazySrc = url;
  }
  return slide;
}

function ensureSlideLoaded(slide) {
  if (!slide || !slide.dataset.lazySrc) return;
  var url = slide.dataset.lazySrc;
  delete slide.dataset.lazySrc;
  var label = slide.getAttribute("aria-label") || "";
  var img = document.createElement("img");
  img.className = "v2-phone-strip__slide-img";
  img.alt = label;
  img.loading = "lazy";
  img.onload = function () {
    slide.innerHTML = "";
    slide.appendChild(img);
  };
  img.onerror = function () { /* 保留 placeholder */ };
  img.src = url;
}

/**
 * @param {object} manifest
 * @param {{ tier?: string }} [opts]
 */
export function initPhoneStrip(manifest, opts) {
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

  track.innerHTML = "";
  dotsHost.innerHTML = "";

  if (!pageCount) {
    track.innerHTML = '<div class="v2-phone-strip__slide-ph">暂无长图预览</div>';
    if (prevBtn) prevBtn.disabled = true;
    if (nextBtn) nextBtn.disabled = true;
    return null;
  }

  var slideEls = pages.map(function (page, i) {
    var slide = buildSlide(manifest, page, i, tier);
    track.appendChild(slide);
    return slide;
  });

  var dotEls = pages.map(function (page, i) {
    var dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-label", page.label || "第 " + (i + 1) + " 段");
    dot.dataset.index = String(i);
    dot.addEventListener("click", function () { go(i); });
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
      if (active) d.setAttribute("aria-current", "true");
      else d.removeAttribute("aria-current");
    });
    if (prevBtn) prevBtn.disabled = !canPrev(index);
    if (nextBtn) nextBtn.disabled = !canNext(index, pageCount);
  }

  function go(requested, goOpts) {
    goOpts = goOpts || {};
    index = clampIndex(requested, pageCount);
    if (tier === "L2") {
      ensureSlideLoaded(slideEls[index]);
      if (index + 1 < slideEls.length) ensureSlideLoaded(slideEls[index + 1]);
    }
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
    syncUi();
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      go(index - 1);
    });
  }
  if (nextBtn) {
    nextBtn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      go(index + 1);
    });
  }

  track.addEventListener("scroll", function () {
    if (syncing) return;
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function () {
      var i = indexFromDomScrollLeft(track.scrollLeft);
      if (i !== index) { index = i; syncUi(); }
    }, 120);
  });

  if (screen) {
    screen.onkeydown = function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(index - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(index + 1); }
    };
    screen.setAttribute(
      "aria-label",
      pageCount > 1
        ? "微信长图 · " + pageCount + " 段 · 左右键或按钮切换"
        : "微信长图预览"
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

  return { go: go, current: function () { return index; }, count: pageCount, relayout: relayout };
}
