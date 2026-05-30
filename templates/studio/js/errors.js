/**
 * Travelogue Studio · error / warning / estimate / slow-hint surfaces.
 */
import { STUDIO_ERROR_MESSAGES, DEFAULT_PIPELINE_ESTIMATES } from "./constants.js";
import { S } from "./state.js";
import { $, show, setTitle } from "./dom.js";

function setSlowHero(level) {
  var hero = $("studio-hero");
  if (!hero) return;
  hero.classList.remove("studio-hero--slow1", "studio-hero--slow2", "studio-hero--slow3");
  if (level) hero.classList.add("studio-hero--slow" + String(level));
}

export function setError(msg) {
  var progressEl = $("studio-error");
  var idleEl = $("studio-import-error");
  if (!msg) {
    if (progressEl) { show(progressEl, false); progressEl.textContent = ""; }
    if (idleEl) { show(idleEl, false); idleEl.textContent = ""; }
    return;
  }
  if (S.currentState === "Importing") {
    if (progressEl) { progressEl.textContent = msg; show(progressEl, true); }
    if (idleEl) show(idleEl, false);
  } else if (idleEl) {
    idleEl.textContent = msg;
    show(idleEl, true);
    if (progressEl) show(progressEl, false);
  } else if (progressEl) {
    progressEl.textContent = msg;
    show(progressEl, true);
  }
}

export function setWarning(msg) {
  var el = $("studio-warning");
  if (!el) return;
  if (!msg) { show(el, false); el.textContent = ""; return; }
  el.textContent = msg;
  show(el, true);
}

export function humanizeStudioError(code, message) {
  var base = code && STUDIO_ERROR_MESSAGES[code];
  if (base) {
    if (message && message !== code && message.indexOf(base) === -1 && message.length < 120) {
      return base + "（" + message + "）";
    }
    return base;
  }
  return message || code || "导入失败";
}

export function pipelineEstimateHint(photoCount) {
  var tiers = S._pipelineEstimateTiers || DEFAULT_PIPELINE_ESTIMATES;
  var count = photoCount || 0;
  if (count <= 0) return "预计 2–5 分钟";
  for (var i = 0; i < tiers.length; i++) {
    if (count <= tiers[i].maxPhotos) return tiers[i].hint;
  }
  return tiers[tiers.length - 1].hint;
}

export function setImportEstimate(body) {
  var el = $("studio-import-estimate");
  if (!el) return;
  var count = 0;
  if (body) {
    count = body.fileCount || body.photoCount || 0;
    if (!count && body.useDemoAlbum) count = 12;
  }
  el.textContent = pipelineEstimateHint(count);
  show(el, true);
}

export function loadPipelineEstimates() {
  fetch("/__travelogue/config")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (data) {
      if (data && data.pipelineEstimates && data.pipelineEstimates.length) {
        S._pipelineEstimateTiers = data.pipelineEstimates;
      }
    })
    .catch(function () {});
}

export function showFailure(msg, echoPath, code) {
  show($("studio-failure"), true);
  var msgEl = $("studio-failure-msg");
  if (msgEl) msgEl.textContent = humanizeStudioError(code, msg) || "导入失败";
  var echoEl = $("studio-failure-echo");
  if (echoEl) {
    if (echoPath) { echoEl.textContent = echoPath; show(echoEl, true); }
    else show(echoEl, false);
  }
  setTitle("导入失败");
}

export function hideFailure() {
  show($("studio-failure"), false);
  var msg = $("studio-failure-msg"); if (msg) msg.textContent = "";
  show($("studio-failure-echo"), false);
  setTitle();
}

export function showSlowHint(level) {
  setSlowHero(level);
  if (level === 3) {
    setWarning("仍可继续等待，或在「高级 · 分析选项」中关闭场景分析以加快速度");
    return;
  }
  if (level === 2) {
    setWarning("照片较多，正在仔细分析行程与场景，首次可能较慢");
    return;
  }
  setWarning("比预期久一些，请耐心等待…");
}

export function hideSlowHint() {
  setWarning("");
  setSlowHero(0);
}
