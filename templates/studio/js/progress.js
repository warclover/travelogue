/**
 * Travelogue Studio · import progress UI.
 */
import { STAGE_LABELS } from "./constants.js";
import { $, show, cssBackgroundImage } from "./dom.js";
import { hideFailure } from "./errors.js";

var STAGE_ORDER = ["ingest", "curate", "narrate", "render"];
var COVER_TRANSITION_MS = 620;

export function stageText(job) {
  var label = STAGE_LABELS[job.stage] || "处理中…";
  var idx = job.stageIndex || 0;
  var total = job.stageCount || 4;
  var hint = job.stageHint ? "（" + job.stageHint + "）" : "";
  return idx + "/" + total + " · " + label + hint;
}

export function updateImportStages(job) {
  var list = $("studio-import-stages");
  if (!list) return;
  var stageKey = job.stage || STAGE_ORDER[0];
  var idx = STAGE_ORDER.indexOf(stageKey);
  if (idx < 0) idx = Math.max(0, (job.stageIndex || 1) - 1);
  var items = list.querySelectorAll(".studio-import__stage");
  items.forEach(function (el, i) {
    el.classList.toggle("is-done", i < idx);
    el.classList.toggle("is-active", i === idx);
  });
}

export function updateImportThumbs(job) {
  var container = $("studio-import-thumbs");
  if (!container) return;
  var spans = container.querySelectorAll("span");
  if (!spans.length) return;

  if (job.status === "succeeded") {
    container.classList.add("studio-import__thumbs--linked");
    spans.forEach(function (span) {
      span.classList.add("is-done");
      span.classList.remove("is-active", "is-pending");
    });
    return;
  }

  var linked = job.status === "running" || job.status === "queued";
  container.classList.toggle("studio-import__thumbs--linked", linked);

  var stageKey = job.stage || STAGE_ORDER[0];
  var stageIdx = STAGE_ORDER.indexOf(stageKey);
  if (stageIdx < 0) stageIdx = Math.max(0, (job.stageIndex || 1) - 1);

  var ingestCur = 0;
  var ingestTotal = 0;
  var hint = job.stageHint || "";
  var m = hint.match(/已处理\s*(\d+)\s*\/\s*(\d+)/);
  if (m) {
    ingestCur = parseInt(m[1], 10) || 0;
    ingestTotal = parseInt(m[2], 10) || 0;
  }

  var activeIdx = stageIdx;
  if (stageIdx === 0 && ingestTotal > 0) {
    activeIdx = Math.min(
      spans.length - 1,
      Math.floor((ingestCur / ingestTotal) * spans.length)
    );
  }

  spans.forEach(function (span, i) {
    span.classList.remove("is-active", "is-done", "is-pending");
    if (!linked) return;
    if (stageIdx === 0 && ingestTotal > 0) {
      span.classList.toggle("is-done", i < activeIdx);
      span.classList.toggle("is-active", i === activeIdx);
      span.classList.toggle("is-pending", i > activeIdx);
    } else {
      span.classList.toggle("is-done", i < stageIdx);
      span.classList.toggle("is-active", i === stageIdx);
      span.classList.toggle("is-pending", i > stageIdx);
    }
  });
}

export function updateProgress(job) {
  hideFailure();
  var stage = $("studio-stage");
  var line = stageText(job);
  if (job.result && job.result.intentLine && (job.stageIndex || 0) >= 2) {
    line = line + "\n" + job.result.intentLine;
  }
  if (stage) stage.textContent = line;
  updateImportStages(job);
  updateImportThumbs(job);
  var pct = Math.round(((job.stageIndex || 0) / (job.stageCount || 4)) * 100);
  var bar = $("studio-bar-fill"); if (bar) bar.style.width = pct + "%";
  var barWrap = $("studio-progress-bar");
  if (barWrap) {
    barWrap.setAttribute("aria-valuenow", String(pct));
    barWrap.setAttribute("aria-valuetext", line.replace(/\n/g, " · "));
  }
  var pctEl = $("studio-pct");
  if (pctEl) { pctEl.textContent = pct + "%"; show(pctEl, true); }
  show($("studio-cancel"), job.status === "running" || job.status === "queued");
}

function prefersReducedMotion() {
  return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
}

function groupRect(rects) {
  if (!rects.length) return null;
  var left = rects[0].left;
  var top = rects[0].top;
  var right = rects[0].right;
  var bottom = rects[0].bottom;
  for (var i = 1; i < rects.length; i++) {
    var r = rects[i];
    if (r.left < left) left = r.left;
    if (r.top < top) top = r.top;
    if (r.right > right) right = r.right;
    if (r.bottom > bottom) bottom = r.bottom;
  }
  return { left: left, top: top, width: right - left, height: bottom - top };
}

function measureSuccessCoverTarget() {
  var success = $("studio-success");
  var cover = $("studio-success-cover");
  if (!success || !cover) return null;
  var wasHidden = success.hidden;
  success.hidden = false;
  cover.hidden = false;
  cover.style.visibility = "hidden";
  var rect = cover.getBoundingClientRect();
  cover.style.visibility = "";
  cover.hidden = true;
  if (wasHidden) success.hidden = true;
  if (!rect.width || !rect.height) return null;
  return rect;
}

function resolveCoverTargetRect() {
  return measureSuccessCoverTarget() || (function () {
    var hero = $("studio-hero");
    if (!hero) return null;
    var heroRect = hero.getBoundingClientRect();
    var w = Math.min(180, heroRect.width * 0.42);
    var h = w * (16 / 9);
    return {
      left: heroRect.left + (heroRect.width - w) / 2,
      top: heroRect.top + heroRect.height * 0.18,
      width: w,
      height: h,
    };
  })();
}

export function resolveSuccessCoverUrl(tripId) {
  if (!tripId) return null;
  return "/" + tripId + "/preview.jpg?t=" + String(Date.now());
}

export function applySuccessCover(coverUrl, title) {
  var cover = $("studio-success-cover");
  var coverImg = $("studio-success-cover-img");
  if (!cover || !coverImg || !coverUrl) {
    if (cover) show(cover, false);
    return;
  }
  cover.classList.remove("is-revealed");
  coverImg.alt = title || "杂志封面";
  coverImg.onload = function () {
    show(cover, true);
    requestAnimationFrame(function () { cover.classList.add("is-revealed"); });
  };
  coverImg.onerror = function () { show(cover, false); };
  coverImg.src = coverUrl;
}

export function resetSuccessCover() {
  var cover = $("studio-success-cover");
  var coverImg = $("studio-success-cover-img");
  var overlay = $("studio-cover-transition");
  if (cover) {
    cover.classList.remove("is-revealed");
    show(cover, false);
  }
  if (coverImg) {
    coverImg.onload = null;
    coverImg.onerror = null;
    coverImg.removeAttribute("src");
  }
  if (overlay) {
    overlay.innerHTML = "";
    show(overlay, false);
  }
}

export function playSuccessCoverTransition(coverUrl, onDone) {
  onDone = onDone || function () {};
  if (!coverUrl || prefersReducedMotion()) {
    onDone({ skipped: true, coverUrl: coverUrl });
    return;
  }

  var thumbsHost = $("studio-import-thumbs");
  var importing = $("studio-hero-importing");
  if (!thumbsHost || !importing || importing.hidden) {
    onDone({ skipped: true, coverUrl: coverUrl });
    return;
  }

  var spans = thumbsHost.querySelectorAll("span");
  if (!spans.length) {
    onDone({ skipped: true, coverUrl: coverUrl });
    return;
  }

  var overlay = $("studio-cover-transition");
  if (!overlay) {
    onDone({ skipped: true, coverUrl: coverUrl });
    return;
  }

  var rects = [];
  var mergeIdx = spans.length - 1;
  spans.forEach(function (span, i) {
    rects.push(span.getBoundingClientRect());
    if (span.classList.contains("is-active")) mergeIdx = i;
  });
  var group = groupRect(rects);
  var target = resolveCoverTargetRect();
  if (!group || !target || group.width < 8 || group.height < 8) {
    onDone({ skipped: true, coverUrl: coverUrl });
    return;
  }

  var mergeSource = spans[mergeIdx];
  var startBg = mergeSource.style.backgroundImage ||
    window.getComputedStyle(mergeSource).backgroundImage;

  overlay.innerHTML = "";
  show(overlay, true);

  var ghosts = document.createElement("div");
  ghosts.className = "studio-cover-transition__ghosts";
  spans.forEach(function (span, i) {
    if (i === mergeIdx) return;
    var r = rects[i];
    var ghost = document.createElement("span");
    ghost.className = "studio-cover-transition__ghost";
    ghost.style.left = r.left + "px";
    ghost.style.top = r.top + "px";
    ghost.style.width = r.width + "px";
    ghost.style.height = r.height + "px";
    ghost.style.backgroundImage = span.style.backgroundImage ||
      window.getComputedStyle(span).backgroundImage;
    ghosts.appendChild(ghost);
  });
  overlay.appendChild(ghosts);

  var card = document.createElement("div");
  card.className = "studio-cover-transition__card";
  card.style.left = group.left + "px";
  card.style.top = group.top + "px";
  card.style.width = group.width + "px";
  card.style.height = group.height + "px";
  card.style.backgroundImage = startBg;
  overlay.appendChild(card);

  requestAnimationFrame(function () {
    requestAnimationFrame(function () {
      ghosts.classList.add("is-collapsing");
      card.style.left = target.left + "px";
      card.style.top = target.top + "px";
      card.style.width = target.width + "px";
      card.style.height = target.height + "px";
      card.classList.add("is-final");
      setTimeout(function () {
        var nextBg = cssBackgroundImage(coverUrl);
        if (nextBg) card.style.backgroundImage = nextBg;
      }, Math.round(COVER_TRANSITION_MS * 0.45));
    });
  });

  setTimeout(function () {
    overlay.innerHTML = "";
    show(overlay, false);
    onDone({ skipped: false, coverUrl: coverUrl });
  }, COVER_TRANSITION_MS);
}
