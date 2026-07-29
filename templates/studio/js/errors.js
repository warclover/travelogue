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

const FAILURE_NEXT_HINTS = {
  E_INGEST_EMPTY: "请确认文件夹里有 JPG/PNG/WebP/HEIC 照片，然后重试。",
  E_INGEST_TOO_FEW: "确认页有足够张数仍失败时，多半是智能挑选后不足 4 张：可点「设置智能选片规则」选「全部保留」或「保留连拍与近似照片」后再试。",
  E_DEMO_TOO_FEW: "示例相册需要至少 4 张照片；请改用「制作我的杂志」选自己的文件夹。",
  E_DEMO_NOT_DIR: "请粘贴或选择本机上的文件夹路径，而不是单个文件。",
  E_STUDIO_ALBUM_DENIED: "请改用 Sheet 内的「浏览文件夹」，或检查路径是否在本机允许范围内。",
  E_STUDIO_UPLOAD_EMPTY: "请重新选择包含照片的文件夹后再上传。",
  E_STUDIO_BODY_TOO_LARGE: "文件夹过大：请改用「制作我的杂志」选文件夹，或合并后分批导入。",
  E_PICK_FOLDER_UNSUPPORTED: "请粘贴路径，或使用 Sheet 底部的小文件夹上传（≤200MB）。",
  E_PICK_FOLDER_DENIED: "仅允许访问本机文件夹；请确认 Studio 有权限访问该路径。",
  E_PICK_FOLDER_FAILED: "请粘贴完整路径，或安装 desktop 依赖后重试浏览文件夹。",
  E_STUDIO_PIPELINE: "通常是临时问题：检查文件夹仍可访问后点「重试」。",
  E_AI_SURFACE_DISABLED: "当前版本不可用",
  E_LLM_AUTH: "检查文件夹是否仍可访问、照片是否足够，然后点「重试」或换文件夹再试。",
  E_LLM_PROVIDER: "当前不可用，请稍后重试。",
  E_LLM_PING: "请稍后重试。",
  E_LLM_NETWORK: "通常是临时网络问题：检查网络或代理后点「重试」，无需重新选文件夹。",
};

export function failureNextHint(code) {
  return (code && FAILURE_NEXT_HINTS[code]) || "检查文件夹路径与照片数量后，点「重试」或换文件夹再试。";
}

/** L0 Hardening · T-FAIL-01：导入失败可改用本机文案继续 */
export function isLlmAuthRecoverable(err) {
  if (!err) return false;
  if (err.recoverableWithStub === true) return true;
  return err.code === "E_LLM_AUTH";
}

export function pipelineEstimateHint(photoCount) {
  var tiers = S._pipelineEstimateTiers || DEFAULT_PIPELINE_ESTIMATES;
  var count = photoCount || 0;
  if (count <= 0) return "约 3–5 分钟";
  for (var i = 0; i < tiers.length; i++) {
    if (count <= tiers[i].maxPhotos) return tiers[i].hint;
  }
  return tiers[tiers.length - 1].hint;
}

export function formatPipelineEstimate(photoCount) {
  return "预计整体 " + pipelineEstimateHint(photoCount);
}

export function setImportEstimate(body) {
  var el = $("studio-import-estimate");
  if (!el) return;
  var count = 0;
  if (body) {
    count = body.fileCount || body.photoCount || 0;
    if (!count && body.useDemoAlbum) count = 12;
  }
  el.textContent = formatPipelineEstimate(count);
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
  var hintEl = $("studio-failure-hint");
  if (hintEl) {
    var hint = failureNextHint(code);
    hintEl.textContent = hint;
    show(hintEl, !!hint);
  }
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
  var hint = $("studio-failure-hint");
  if (hint) { hint.textContent = ""; show(hint, false); }
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
