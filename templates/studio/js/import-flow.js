/**
 * Travelogue Studio · import orchestration, success page, uploads, resume.
 */
import { LS, SS, IMPORT_PHOTO_CAP, SUCCESS_LONGSHOT_SCALE, SUCCESS_SLOW_MS } from "./constants.js";
import { S } from "./state.js";
import { $, show, syncImportUiDisabled, setBusy } from "./dom.js";
import { studioAuthHeaders, withJobBusyRetry, isJobBusyResponse, postJson } from "./http.js";
import {
  setError, setWarning, hideFailure, showFailure, humanizeStudioError, setImportEstimate,
} from "./errors.js";
import { transitionTo } from "./render.js";
import { pollJob, postImport, postMultipartImport, waitJob, loadTrips } from "./api.js";
import {
  openImportSheet, showSheetConfirm, submitSheetImport, pushRecentPath,
  appendPlanFileToForm, revokeThumbUrls, setImportThumbs, readImportThumbsFromFiles,
  confirmLargeUpload, maybeShowCoach, dismissCoach,
} from "./sheet.js";

// ── Import flows ──
export function focusPathImport(message) {
  var form = $("studio-import-form");
  var input = $("album-path");
  show(form, true);
  if (message) setError(message);
  if (input) {
    input.focus();
    input.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
}

export function submitPathImport() {
  var path = ($("album-path").value || "").trim();
  if (!path) {
    setError("请填写照片文件夹路径，例如 D:\\Photos\\Kyoto2025");
    openImportSheet();
    return;
  }
  pushRecentPath(path);
  if (!S._sheetOpen) openImportSheet();
  showSheetConfirm(path);
  setError("");
}

export function requestNativeFolder(titleVal, placeVal, options) {
  options = options || {};
  var autoStart = options.autoStart === true;
  if (S._pickInFlight) {
    if (typeof studioToast === "function") {
      studioToast("文件夹选择器已打开，请在其窗口中操作", { duration: 2500 });
    }
    return Promise.resolve();
  }
  S._pickInFlight = true;
  syncImportUiDisabled();
  setError("");
  var pickToastEl = null;
  if (typeof studioToast === "function") {
    pickToastEl = studioToast("正在打开文件夹选择器…", { duration: 0 });
  }
  return fetch("/__travelogue/pick-folder", {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: "{}",
  }).then(function (resp) {
    return resp.json().then(function (data) { return { status: resp.status, data: data }; });
  }).then(function (result) {
    if (result.data && result.data.cancelled) return;
    if (!result.data || result.data.ok === false || result.status >= 400) {
      var msg = (result.data && (result.data.message || result.data.detail))
        || "无法打开本机选文件夹。请粘贴路径，或重启 Studio 后重试。";
      focusPathImport(msg);
      return;
    }
    if (result.status === 200 && result.data && result.data.albumPath) {
      var pathInput = $("album-path");
      if (pathInput) pathInput.value = result.data.albumPath;
      if (titleVal && $("trip-title")) $("trip-title").value = titleVal;
      if (placeVal && $("trip-place")) $("trip-place").value = placeVal;
      if (!S._sheetOpen) openImportSheet();
      showSheetConfirm(result.data.albumPath);
      maybeShowCoach(2);
      dismissCoach();
      if (autoStart) submitSheetImport(true);
      return;
    }
    openImportSheet();
    setError("无法打开本机选文件夹。请用「其他导入方式」粘贴路径。");
  }).catch(function () {
    openImportSheet();
    setError("无法连接选文件夹服务。请粘贴路径，或确认 Studio 正在运行。");
  }).finally(function () {
    if (pickToastEl && pickToastEl.parentNode) {
      pickToastEl.parentNode.removeChild(pickToastEl);
    }
    S._pickInFlight = false;
    syncImportUiDisabled();
  });
}

// ── Success page · longshot ──
let _successTimer = null;
let _successTripId = null;
let _successLongshotPoll = null;

export function clearSuccessTimer() {
  if (_successTimer) { clearInterval(_successTimer); _successTimer = null; }
}

export function clearSuccessLongshotPoll() {
  if (_successLongshotPoll) { clearInterval(_successLongshotPoll); _successLongshotPoll = null; }
}

export function setSuccessLongshotStatus(text, isError) {
  var el = $("studio-success-longshot-status");
  if (!el) return;
  el.textContent = text || "";
  el.classList.toggle("is-error", !!isError);
  show(el, !!text);
}

export function revealSuccessLongshot(relPath) {
  if (!_successTripId || !relPath) return;
  fetch("/__travelogue/reveal", {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ tripId: _successTripId, relPath: relPath }),
  }).catch(function () {
    if (typeof studioToast === "function") {
      studioToast("无法在文件夹中显示，请手动打开 trips 目录", { duration: 4000 });
    }
  });
}

export function onSuccessLongshotDone(job) {
  var btn = $("studio-success-longshot");
  if (btn) btn.disabled = false;
  if (job.status === "failed") {
    var err = job.error || {};
    setSuccessLongshotStatus(
      humanizeStudioError(err.code, err.message || err.code || "长图导出失败"),
      true
    );
    return;
  }
  var outputs = (job.result && job.result.outputs) || [];
  if (!outputs.length) {
    setSuccessLongshotStatus("长图已生成", false);
    return;
  }
  var seg = outputs.length > 1 ? "（共 " + outputs.length + " 张，可依次发微信）" : "";
  var hint = (job.result && job.result.userHint) || "";
  if (hint) {
    setSuccessLongshotStatus(hint + " · " + outputs[0] + seg, false);
  } else {
    setSuccessLongshotStatus("长图已保存 " + outputs[0] + seg + " · 点击再次导出可更新", false);
  }
  revealSuccessLongshot(outputs[0]);
  var wechat = $("studio-success-wechat");
  if (wechat) {
    wechat.open = true;
    show(wechat, true);
  }
}

export function pollSuccessLongshot(jobId, started) {
  clearSuccessLongshotPoll();
  var slowShown = false;
  _successLongshotPoll = setInterval(function () {
    if (!slowShown && Date.now() - started > SUCCESS_SLOW_MS) {
      slowShown = true;
      setSuccessLongshotStatus("比预期久一些，仍在生成长图…", false);
    }
    pollJob(jobId).then(function (job) {
      if (job.status === "running" || job.status === "queued") {
        var hint = job.stageHint || job.stageLabel;
        if (hint) setSuccessLongshotStatus("正在生成长图… " + hint, false);
        return;
      }
      clearSuccessLongshotPoll();
      onSuccessLongshotDone(job);
    }).catch(function () {
      clearSuccessLongshotPoll();
      var btn = $("studio-success-longshot");
      if (btn) btn.disabled = false;
      setSuccessLongshotStatus("网络错误，请重试", true);
    });
  }, 500);
}

export function startSuccessLongshot() {
  if (!_successTripId) {
    setSuccessLongshotStatus("尚未就绪，请稍候再试", true);
    return;
  }
  var btn = $("studio-success-longshot");
  if (btn && btn.disabled) return;
  if (btn) btn.disabled = true;
  setSuccessLongshotStatus("正在生成长图…", false);
  function postSuccessLongshot() {
    return postJson("/__travelogue/longshot", {
      tripId: _successTripId,
      scale: SUCCESS_LONGSHOT_SCALE,
      format: "png",
    });
  }
  withJobBusyRetry(postSuccessLongshot)
    .then(function (res) {
      if (isJobBusyResponse(res)) {
        if (btn) btn.disabled = false;
        setSuccessLongshotStatus("排队中，请稍候…", true);
        return;
      }
      if (res.status === 409) {
        if (btn) btn.disabled = false;
        setSuccessLongshotStatus((res.body && res.body.message) || "请稍候再试", true);
        return;
      }
      if (res.status !== 202 || !res.body.jobId) {
        if (btn) btn.disabled = false;
        setSuccessLongshotStatus("无法开始长图导出", true);
        return;
      }
      pollSuccessLongshot(res.body.jobId, Date.now());
    })
    .catch(function () {
      if (btn) btn.disabled = false;
      setSuccessLongshotStatus("网络错误，请重试", true);
    });
}

export function isFirstTime() { return !localStorage.getItem(LS.firstPreviewDone); }
export function markFirstPreviewDone(tripId) {
  localStorage.setItem(LS.firstPreviewDone, "1");
  if (tripId) localStorage.setItem("travelogue.studio.firstTripId", tripId);
}

export function handleImportSuccess(job) {
  var result = job.result || {};
  var url = result.previewUrl;
  var openUrl = url;
  var tripId = result.tripId;
  _successTripId = tripId || null;
  setSuccessLongshotStatus("", false);
  clearSuccessLongshotPoll();
  var wechatGuide = $("studio-success-wechat");
  if (wechatGuide) {
    wechatGuide.open = false;
    show(wechatGuide, false);
  }
  var notice = result.clusterNotice;
  if (notice && typeof studioToast === "function") {
    studioToast(notice, { duration: 4500 });
  }
  var first = isFirstTime();
  if (first) markFirstPreviewDone(tripId);

  var openLink = $("studio-success-open");
  var msg = $("studio-success-msg");
  if (openLink && url) openLink.href = url;

  // F-P4-PRV-06: upgrade to the "peak" deep link when available.
  // Graceful: if this resolves after auto-open fires, the base URL is used.
  if (tripId) {
    fetch("/__travelogue/trips/" + encodeURIComponent(tripId) + "/entry")
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.ok && data.previewUrl) {
          openUrl = data.scrollShareUrl || data.previewUrl;
          if (openLink) openLink.href = openUrl;
        }
      })
      .catch(function () {});
  }
  var title = result.title || ($("trip-title") && $("trip-title").value) || "我的旅途";
  var featured = result.featuredCount;
  var segments = result.segmentCount;
  var photoCount = result.photoCount || 0;
  if (msg) {
    if (featured > 0) {
      msg.textContent = "《" + title + "》已生成 · " + featured + " 张精选已用于封面与章首";
    } else {
      msg.textContent = "《" + title + "》已生成 · 可在预览中标记精选照片";
    }
    if (segments > 0) msg.textContent += " · " + segments + " 段行程";
    if (photoCount >= IMPORT_PHOTO_CAP) {
      msg.textContent += " · 已优先保留精选与前 " + IMPORT_PHOTO_CAP + " 张";
    }
  }

  var chipsHost = $("studio-success-chips");
  if (chipsHost) {
    chipsHost.innerHTML = "";
    if (featured > 0) {
      var c1 = document.createElement("span");
      c1.className = "studio-success__chip";
      c1.textContent = "精选 " + featured + " 张";
      chipsHost.appendChild(c1);
    }
    if (segments > 0) {
      var c2 = document.createElement("span");
      c2.className = "studio-success__chip";
      c2.textContent = "行程 " + segments + " 段";
      chipsHost.appendChild(c2);
    }
    if (photoCount >= IMPORT_PHOTO_CAP) {
      var c3 = document.createElement("span");
      c3.className = "studio-success__chip";
      c3.textContent = "优先精选 · 前 " + IMPORT_PHOTO_CAP + " 张";
      chipsHost.appendChild(c3);
    }
    show(chipsHost, chipsHost.childElementCount > 0);
  }

  transitionTo("Success");

  // P5-2.5: no auto-open preview; primary action is longshot on success page.
  var countdownP = document.querySelector(".studio-success__countdown");
  if (countdownP) show(countdownP, false);
  clearSuccessTimer();
}

export function startImport(body) {
  var gen = ++S._importGen;
  S.pendingImport = body;
  try {
    if (!body.uploadForm) {
      sessionStorage.setItem(SS.activePending, JSON.stringify(body));
    } else {
      sessionStorage.removeItem(SS.activePending);
    }
  } catch (e) {}
  if (body && body.albumPath) pushRecentPath(body.albumPath);
  setError("");
  hideFailure();
  transitionTo("Importing");
  revokeThumbUrls();
  setImportThumbs(null);
  setImportEstimate(body);
  var stage = $("studio-stage"); if (stage) stage.textContent = "准备导入…";
  var bar = $("studio-bar-fill"); if (bar) bar.style.width = "0%";
  var pctEl = $("studio-pct"); if (pctEl) show(pctEl, false);

  return withJobBusyRetry(function () { return postImport(body); }).then(function (result) {
    if (result.status === 409 && result.data.error === "E_DEMO_EXISTS") {
      return (typeof studioModal === "function"
        ? studioModal({
            title: "该游记已存在",
            body: "是否覆盖已有内容？覆盖后无法撤销。",
            confirmText: "覆盖并重新导入",
            cancelText: "取消",
          })
        : Promise.resolve(window.confirm(result.data.message || "该游记已存在。是否覆盖？"))
      ).then(function (confirmed) {
        if (!confirmed) throw new Error("已取消覆盖");
        body.force = true;
        return startImport(body);
      });
    }
    if (result.status !== 202) {
      throw { code: result.data.error, message: result.data.message || result.data.error || "导入失败" };
    }
    try { sessionStorage.setItem(SS.activeJobId, result.data.jobId); } catch (e) {}
    return waitJob(result.data.jobId, gen);
  }).then(function (job) {
    try { sessionStorage.removeItem(SS.activeJobId); sessionStorage.removeItem(SS.activePending); } catch (e) {}
    handleImportSuccess(job);
    loadTrips();
  }).catch(function (err) {
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
    if ((err.message || "") === "已取消") {
      setError("已取消导入");
      rememberCancelled();
      transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      return;
    }
    if ((err.message || "") === "已取消覆盖") {
      transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      return;
    }
    var echoPath = "";
    if (S.pendingImport && S.pendingImport.albumPath) echoPath = S.pendingImport.albumPath;
    transitionTo("Failed");
    showFailure(err.message || String(err), echoPath, err.code);
  }).finally(function () {
    setBusy();
  });
}

export function rememberCancelled() {
  if (!S.pendingImport) return;
  var echo = "";
  if (S.pendingImport.albumPath) echo = S.pendingImport.albumPath;
  else if (S.pendingImport.fileCount) echo = "浏览器上传（" + S.pendingImport.fileCount + " 张照片）";
  else if (S.pendingImport.useDemoAlbum) echo = "示例相册";
  var data = { echo: echo, body: S.pendingImport.uploadForm ? null : S.pendingImport };
  try { localStorage.setItem(LS.lastCancelled, JSON.stringify(data)); } catch (e) {}
}

export function uploadAndImport(files, titleVal, placeVal) {
  if (!files || !files.length) return;
  return confirmLargeUpload(files).then(function (proceed) {
    if (!proceed) return;
    return uploadAndImportCore(files, titleVal, placeVal);
  });
}

export function uploadAndImportCore(files, titleVal, placeVal) {
  if (!files || !files.length) return;
  var gen = ++S._importGen;
  if (files.length > 100) {
    setWarning("照片较多（" + files.length + " 张），建议精选后导入，效果更佳。");
  } else {
    setWarning("");
  }

  var form = new FormData();
  form.append("title", titleVal || ($("trip-title") && $("trip-title").value) || "我的旅途");
  form.append("place", placeVal || ($("trip-place") && $("trip-place").value) || "旅途");
  var feeling = ($("trip-feeling") && $("trip-feeling").value.trim()) || "";
  if (feeling) form.append("userNotes", feeling.slice(0, 200));
  appendPlanFileToForm(form);
  for (var i = 0; i < files.length; i++) {
    form.append("files[]", files[i], files[i].webkitRelativePath || files[i].name);
  }

  S.pendingImport = { uploadForm: true, files: files, fileCount: files.length };
  try { sessionStorage.removeItem(SS.activePending); } catch (e) {}
  setError("");
  hideFailure();
  transitionTo("Importing");
  readImportThumbsFromFiles(files);
  setImportEstimate({ fileCount: files.length });
  var stage = $("studio-stage"); if (stage) stage.textContent = "上传照片中…";
  var bar = $("studio-bar-fill"); if (bar) bar.style.width = "0%";
  var progress = $("upload-progress");
  show(progress, true);
  if (progress) progress.value = 0;

  return postMultipartImport(form, {
    onUploadProgress: function (ev) {
      if (ev.lengthComputable && progress) {
        progress.value = Math.round((ev.loaded / ev.total) * 100);
      }
    },
  }).then(function (result) {
    if (isJobBusyResponse(result)) {
      if (typeof studioToast === "function") {
        studioToast("排队中，请稍候…", { duration: 2800 });
      }
      throw { code: "E_STUDIO_JOB_BUSY", message: "排队中，请稍候" };
    }
    return result;
  }).then(function (result) {
    show(progress, false);
    if (result.status === 409 && result.data.error === "E_DEMO_EXISTS") {
      return (typeof studioModal === "function"
        ? studioModal({
            title: "该游记已存在",
            body: "是否覆盖已有内容？覆盖后无法撤销。",
            confirmText: "覆盖并重新导入",
            cancelText: "取消",
          })
        : Promise.resolve(window.confirm(result.data.message || "该游记已存在。是否覆盖？"))
      ).then(function (confirmed) {
        if (!confirmed) throw new Error("已取消覆盖");
        return uploadAndImportWithForce(files, titleVal, placeVal, gen);
      });
    }
    if (result.status !== 202) {
      throw { code: result.data.error, message: result.data.message || result.data.error || "上传失败" };
    }
    try { sessionStorage.setItem(SS.activeJobId, result.data.jobId); } catch (e) {}
    return waitJob(result.data.jobId, gen);
  }).then(function (job) {
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
    handleImportSuccess(job);
    loadTrips();
  }).catch(function (err) {
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
    if ((err.message || "") === "已取消" || (err.message || "") === "已取消覆盖") {
      rememberCancelled();
      transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      return;
    }
    transitionTo("Failed");
    var echo = "";
    if (S.pendingImport && S.pendingImport.fileCount) {
      echo = "浏览器上传（" + S.pendingImport.fileCount + " 张照片）";
    }
    showFailure(err.message || String(err), echo, err.code);
  }).finally(function () {
    revokeThumbUrls();
    setBusy();
    show(progress, false);
  });
}

export function uploadAndImportWithForce(files, titleVal, placeVal, gen) {
  var retryForm = new FormData();
  retryForm.append("title", titleVal || "我的旅途");
  retryForm.append("place", placeVal || "旅途");
  retryForm.append("force", "true");
  appendPlanFileToForm(retryForm);
  for (var j = 0; j < files.length; j++) {
    retryForm.append("files[]", files[j], files[j].webkitRelativePath || files[j].name);
  }
  return postMultipartImport(retryForm).then(function (retryResult) {
    if (retryResult.status !== 202) {
      throw new Error(retryResult.data.message || retryResult.data.error || "上传失败");
    }
    try { sessionStorage.setItem(SS.activeJobId, retryResult.data.jobId); } catch (e) {}
    return waitJob(retryResult.data.jobId, gen);
  });
}

// ── Resume in-flight import after page reload ──
export function resumeActiveJobIfAny() {
  var jobId = "";
  var pendingRaw = "";
  try {
    jobId = sessionStorage.getItem(SS.activeJobId) || "";
    pendingRaw = sessionStorage.getItem(SS.activePending) || "";
  } catch (e) {}
  if (!jobId) return false;
  if (pendingRaw) {
    try {
      S.pendingImport = JSON.parse(pendingRaw);
      if (S.pendingImport && S.pendingImport.uploadForm) {
        try {
          sessionStorage.removeItem(SS.activeJobId);
          sessionStorage.removeItem(SS.activePending);
        } catch (e) {}
        return false;
      }
    } catch (e) { S.pendingImport = null; }
  }
  var gen = ++S._importGen;
  transitionTo("Importing");
  setImportThumbs(null);
  var stage = $("studio-stage"); if (stage) stage.textContent = "恢复上次导入…";
  waitJob(jobId, gen).then(function (job) {
    try { sessionStorage.removeItem(SS.activeJobId); sessionStorage.removeItem(SS.activePending); } catch (e) {}
    handleImportSuccess(job);
    loadTrips({ keepLimit: true });
  }).catch(function (err) {
    try { sessionStorage.removeItem(SS.activeJobId); } catch (e) {}
    if ((err.message || "") === "已取消") {
      rememberCancelled();
      transitionTo(S.tripsData.length > 0 ? "IdleReturning" : "IdleEmpty");
      return;
    }
    transitionTo("Failed");
    var echo = (S.pendingImport && S.pendingImport.albumPath) || "";
    showFailure(err.message || String(err), echo);
  }).finally(function () { setBusy(); });
  return true;
}
