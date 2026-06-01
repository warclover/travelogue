/**
 * 首页 v2 · M20-a Bento 空态渲染。
 * - 背景层（Ken Burns / 静帧降级）
 * - 16:9 carousel 骨架（slides + dots；完整 clamp/spread 见 M20-b）
 * - 9:16 长图样张
 * - 工作台 bench 文案（来自 manifest.meta）
 * 素材未齐时全部走 placeholder，不白屏（AC-HP2-22）。
 */
import { V2, $, show } from "./store.js";
import { cssBackgroundImage } from "../js/dom.js";
import { assetUrl } from "./manifest.js";
import { initCarousel } from "./carousel.js";
import { resolveLayoutTier } from "./layout-tier.js";
import { trackStudioEvent } from "../js/analytics.js";

function prefersReducedMotion() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) {
    return false;
  }
}

/** 背景：预加载成功才铺图，失败保留暗色渐变兜底（§11.4 / §12.4 L3）。 */
export function renderBackground(manifest, tier) {
  var bg = $("v2-bento-bg");
  if (!bg || !manifest || !manifest.assets) return;
  var url = assetUrl(manifest.assets.background);
  if (!url) return;
  var img = new Image();
  img.onload = function () {
    var bgImg = cssBackgroundImage(url);
    if (bgImg) bg.style.backgroundImage = bgImg;
    var motionOk = tier !== "L1" && tier !== "L3";
    if (motionOk && !prefersReducedMotion()) bg.classList.add("is-kenburns");
  };
  img.onerror = function () {
    /* 保留 CSS 暗色兜底，不闪白 */
  };
  img.src = url;
}

/**
 * 冷启动 Importing 静帧背景（§9.2 / AC-HP2-17）。
 * 关 tab 后再开 / activeJobId 恢复时无「Import 前壳层」，
 * 用 demo 封面静帧 + veil（**不** Ken Burns），不闪 Idle。幂等。
 */
export function renderColdStartBackground(manifest) {
  var bg = $("v2-bento-bg");
  if (!bg) return;
  if (bg.style.backgroundImage) return; // 已有壳层背景（暖启动），不覆盖
  if (!manifest || !manifest.assets) return;
  var url = assetUrl(manifest.assets.background);
  if (!url) return;
  var img = new Image();
  img.onload = function () {
    var bgImg = cssBackgroundImage(url);
    if (bgImg) bg.style.backgroundImage = bgImg;
    bg.classList.remove("is-kenburns"); // 静帧：明确禁动效
  };
  img.src = url;
}

/** 9:16 长图样张：成功铺图，失败显示占位提示。L2 使用 lazy。 */
export function renderPhone(manifest, tier) {
  var screen = $("v2-phone-screen");
  if (!screen || !manifest || !manifest.assets) return;
  screen.innerHTML = "";
  var url = assetUrl(manifest.assets.longshot);
  var img = new Image();
  img.alt = "微信长图样张";
  if (tier === "L2") img.loading = "lazy";
  img.onerror = function () {
    screen.innerHTML =
      '<div class="v2-carousel__slide-ph" style="min-height:240px">长图样张加载中…</div>';
  };
  img.src = url;
  screen.appendChild(img);

  var expand = $("v2-expand-phone");
  if (expand && !expand._v2wired) {
    expand._v2wired = true;
    expand.addEventListener("click", function () {
      if (typeof V2.onExpand === "function") V2.onExpand({ type: "longshot" });
    });
  }
}

/** 工作台 bench：标题 / meta 来自 manifest（in-product 禁用「AI」字样，§3.2/§15）。 */
export function renderBench(manifest) {
  if (!manifest) return;
  var titleEl = $("v2-bench-title");
  var metaEl = $("v2-bench-meta");
  var thumb = $("v2-bench-thumb");
  if (titleEl && manifest.title) titleEl.textContent = manifest.title;
  if (metaEl) {
    var meta = manifest.meta || {};
    var parts = ["自动生成"];
    if (meta.photoCount) parts.push(meta.photoCount + " 张");
    if (meta.chapterCount) parts.push(meta.chapterCount + " 章");
    metaEl.textContent = parts.join(" · ");
  }
  if (thumb && manifest.assets && manifest.assets.background) {
    var url = assetUrl(manifest.assets.background);
    var probe = new Image();
    probe.onload = function () {
      var bgImg = cssBackgroundImage(url);
      if (bgImg) thumb.style.backgroundImage = bgImg;
    };
    probe.src = url;
  }
}

/** 渲染整个 Bento 空态（IdleEmpty）。manifest 可为 null（降级）。 */
export function renderBentoEmpty(manifest) {
  show($("v2-loading"), false);
  show($("v2-headline"), true);
  show($("v2-frame"), true);
  show($("v2-shelf"), false);
  show($("v2-importing"), false);

  var tier = resolveLayoutTier({ manifestError: !manifest });
  V2.layoutTier = tier;
  trackStudioEvent("layout_tier", { tier: tier, surface: "bento" });

  if (manifest) {
    renderBackground(manifest, tier);
    initCarousel(manifest, { tier: tier });
    renderPhone(manifest, tier);
    renderBench(manifest);
  }
}
