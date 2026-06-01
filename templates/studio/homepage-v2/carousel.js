/**
 * 首页 v2 · 16:9 Carousel DOM 控制器（M20-b）。
 *
 * 行为（PRD §6.4 / DATA-CONTRACT §1.3）：
 *  - spread：一屏两半页；每次滑 1 半页
 *  - D-10：到头 clamp，不 wrap；首尾箭头 disabled
 *  - 奇数尾页：最后索引左对齐，右侧留白
 *  - 键盘 ←/→；dots `aria-current`
 *  - ⤢ / 轻点 → Lightbox（M20-c 通过 V2.onExpand 接入）
 *
 * 纯逻辑见 carousel-logic.js（含 node 单测）。
 */
import {
  clampIndex, scrollLeftFor, indexFromScrollLeft, canPrev, canNext,
} from "./carousel-logic.js";
import { assetUrl } from "./manifest.js";
import { trackStudioEvent } from "../js/analytics.js";
import { shouldEagerCarouselPage } from "./layout-tier.js";
import { V2, $ } from "./store.js";

function pagePlaceholderText(page) {
  if (!page) return "";
  if (page.role === "cover") return "雨后 · 封面";
  if (page.role === "epilogue") return "— 尾声 —";
  return page.label || "";
}

function buildSlide(page, index, tier) {
  var slide = document.createElement("div");
  slide.className = "v2-carousel__slide";
  slide.setAttribute("role", "group");
  slide.setAttribute("aria-label", (page && page.label) || "页面");

  var ph = document.createElement("div");
  ph.className = "v2-carousel__slide-ph";
  ph.textContent = pagePlaceholderText(page);
  slide.appendChild(ph);

  var url = page ? assetUrl(page.webp) : "";
  if (url) {
    var eager = shouldEagerCarouselPage(index, tier);
    var attachImg = function () {
      var img = document.createElement("img");
      img.alt = (page && page.label) || "";
      img.style.width = "100%";
      img.style.height = "100%";
      img.style.objectFit = "cover";
      if (eager && index === 0) img.setAttribute("fetchpriority", "high");
      if (!eager) img.loading = "lazy";
      img.onload = function () {
        slide.innerHTML = "";
        slide.appendChild(img);
      };
      img.onerror = function () { /* 保留 placeholder */ };
      img.src = url;
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
  img.alt = pageLabel;
  img.loading = "lazy";
  img.style.width = "100%";
  img.style.height = "100%";
  img.style.objectFit = "cover";
  img.onload = function () {
    slide.innerHTML = "";
    slide.appendChild(img);
  };
  img.onerror = function () { /* 保留 placeholder */ };
  img.src = url;
}

/**
 * 初始化 carousel。返回控制器 { go, current, count }。
 * @param {object} manifest
 * @param {{ tier?: string }} [opts]
 */
export function initCarousel(manifest, opts) {
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
  var lastTracked = 0; // spread_page_view 仅在真正翻页时上报（首帧不报）

  function emitPage() {
    if (index === lastTracked) return;
    lastTracked = index;
    trackStudioEvent("spread_page_view", { page_index: index });
  }

  track.innerHTML = "";
  dotsHost.innerHTML = "";
  var slideEls = pages.map(function (page, i) {
    var slide = buildSlide(page, i, tier);
    track.appendChild(slide);
    return slide;
  });

  var dotEls = pages.map(function (page, i) {
    var dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("role", "tab");
    dot.setAttribute("aria-label", page.label || "第 " + (i + 1) + " 页");
    dot.dataset.index = String(i);
    dot.addEventListener("click", function () { go(i); });
    dotsHost.appendChild(dot);
    return dot;
  });

  if (hint) hint.textContent = "← 横滑 · 一屏两页 · 到头停止 · 共 " + pageCount + " 张 →";

  function viewportWidth() {
    return (viewport && viewport.clientWidth) || (track && track.clientWidth) || 0;
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

  function go(requested, opts) {
    opts = opts || {};
    index = clampIndex(requested, pageCount);
    if (tier === "L2") {
      ensureSlideLoaded(slideEls[index]);
      if (index + 1 < slideEls.length) ensureSlideLoaded(slideEls[index + 1]);
    }
    if (!opts.fromScroll) {
      syncing = true;
      track.scrollLeft = scrollLeftFor(index, viewportWidth());
      // 释放同步锁（scroll 事件异步）
      setTimeout(function () { syncing = false; }, 240);
    }
    syncUi();
    emitPage();
  }

  if (prevBtn) prevBtn.addEventListener("click", function () { go(index - 1); });
  if (nextBtn) nextBtn.addEventListener("click", function () { go(index + 1); });

  // 原生滚动 / 触控滑动 → 同步索引（clamp）
  var scrollTimer = null;
  track.addEventListener("scroll", function () {
    if (syncing) return;
    if (scrollTimer) clearTimeout(scrollTimer);
    scrollTimer = setTimeout(function () {
      var i = indexFromScrollLeft(track.scrollLeft, viewportWidth(), pageCount);
      if (i !== index) { index = i; syncUi(); emitPage(); }
    }, 120);
  });

  // 键盘 ←/→（AC-HP2-19）
  var webCell = $("v2-web-cell");
  if (webCell) {
    webCell.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft") { e.preventDefault(); go(index - 1); }
      else if (e.key === "ArrowRight") { e.preventDefault(); go(index + 1); }
      else if (e.key === "Enter") {
        e.preventDefault();
        if (typeof V2.onExpand === "function") V2.onExpand({ type: "scroll", index: index });
      }
    });
  }

  // ⤢ 放大 → Lightbox（M20-c）。当前通过 V2.onExpand 钩子。
  var expand = $("v2-expand-scroll");
  if (expand) {
    expand.addEventListener("click", function () {
      if (typeof V2.onExpand === "function") {
        V2.onExpand({ type: "scroll", index: index });
      }
    });
  }

  go(0);
  return {
    go: go,
    current: function () { return index; },
    count: pageCount,
  };
}
