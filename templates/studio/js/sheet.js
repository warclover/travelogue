/**
 * Travelogue Studio · import sheet, intent fields, coach marks,
 * recent paths, import thumbs, and large-upload confirm.
 */
import { LS, UPLOAD_BYTES_SOFT_LIMIT, isGenericPlace } from "./constants.js";
import { S } from "./state.js";
import {
  $, show, formatBytes, basenameTitleFromPath,
  trapSheetFocus, releaseSheetFocusTrap, cssBackgroundImage,
} from "./dom.js";
import { setError } from "./errors.js";
import { startImport, requestNativeFolder } from "./import-bridge.js";

export function saveIntent() {
  try {
    localStorage.setItem(LS.studioIntent, JSON.stringify({
      title: ($("trip-title") && $("trip-title").value) || "",
      place: ($("trip-place") && $("trip-place").value) || "",
      feeling: ($("trip-feeling") && $("trip-feeling").value) || "",
      albumPath: S._pendingAlbumPath || "",
    }));
  } catch (e) {}
}

export function loadIntent() {
  try {
    var raw = localStorage.getItem(LS.studioIntent);
    if (!raw) return;
    var data = JSON.parse(raw);
    var sameAlbum = !data.albumPath || data.albumPath === S._pendingAlbumPath;
    if ($("trip-title") && data.title && sameAlbum) $("trip-title").value = data.title;
    if ($("trip-place")) {
      $("trip-place").value = (sameAlbum && data.place) ? data.place : "";
    }
    if ($("trip-feeling") && data.feeling && sameAlbum) $("trip-feeling").value = data.feeling;
  } catch (e) {}
}

export function validateTitleField() {
  var input = $("trip-title");
  var err = $("trip-title-error");
  if (!input || !err) return true;
  var v = (input.value || "").trim();
  if (v.length > 20) {
    err.textContent = "杂志名最多 20 个字";
    show(err, true);
    return false;
  }
  show(err, false);
  return true;
}

export function resetSheetConfirm() {
  S._pendingAlbumPath = null;
  show($("studio-sheet-confirm"), false);
  show($("studio-sheet-picked"), false);
  var picked = $("studio-sheet-picked");
  if (picked) picked.textContent = "";
  var pickBtn = $("studio-sheet-pick");
  if (pickBtn) {
    pickBtn.disabled = false;
    pickBtn.textContent = "选择照片文件夹";
  }
}

export function showSheetConfirm(albumPath) {
  S._pendingAlbumPath = albumPath;
  var picked = $("studio-sheet-picked");
  if (picked) {
    picked.textContent = "已选择：" + albumPath;
    show(picked, true);
  }
  var pickBtn = $("studio-sheet-pick");
  if (pickBtn) {
    pickBtn.disabled = true;
    pickBtn.textContent = "已选择文件夹";
  }
  var titleInput = $("trip-title");
  if (titleInput) titleInput.value = basenameTitleFromPath(albumPath);
  var placeInput = $("trip-place");
  if (placeInput) placeInput.value = "";
  loadIntent();
  show($("studio-sheet-confirm"), true);
  validateTitleField();
  if (titleInput) titleInput.focus();
}

export function isSheetOpen() { return S._sheetOpen; }

export function openImportSheet() {
  if (S.currentState === "Importing") {
    if (typeof studioToast === "function") {
      studioToast("正在制作中", { duration: 2500 });
    }
    return;
  }
  loadIntent();
  resetSheetConfirm();
  var root = $("studio-sheet-root");
  var sheet = $("studio-import-sheet");
  if (root) show(root, true);
  S._sheetOpen = true;
  document.body.classList.add("studio-sheet-open");
  setError("");
  S._sheetPreviousFocus = document.activeElement;
  if (S._sheetFocusRelease) S._sheetFocusRelease();
  if (sheet) S._sheetFocusRelease = trapSheetFocus(sheet);
  var pick = $("studio-sheet-pick");
  if (pick) pick.focus();
  maybeShowCoach(1);
}

export function closeImportSheet() {
  saveIntent();
  var root = $("studio-sheet-root");
  if (root) show(root, false);
  S._sheetOpen = false;
  document.body.classList.remove("studio-sheet-open");
  releaseSheetFocusTrap(true);
}

export function appendPlanFileToForm(form) {
  var planInput = $("plan-file");
  if (planInput && planInput.files && planInput.files[0]) {
    form.append("planFile", planInput.files[0], planInput.files[0].name);
  }
}

export function readPlanTextForImport() {
  var planInput = $("plan-file");
  if (!planInput || !planInput.files || !planInput.files[0]) {
    return Promise.resolve(null);
  }
  var file = planInput.files[0];
  if (file.size > 32768) return Promise.resolve(null);
  return file.text().catch(function () { return null; });
}

export function buildImportPayload(extra) {
  extra = extra || {};
  var title = ($("trip-title") && $("trip-title").value.trim()) || "我的旅途";
  var placeRaw = ($("trip-place") && $("trip-place").value.trim()) || "";
  var feeling = ($("trip-feeling") && $("trip-feeling").value.trim()) || "";
  var body = {
    albumPath: extra.albumPath || S._pendingAlbumPath,
    title: title.slice(0, 20),
    place: placeRaw || "旅途",
    placeUserSet: !!placeRaw && !isGenericPlace(placeRaw),
    force: !!extra.force,
  };
  if (feeling) body.userNotes = feeling.slice(0, 200);
  return body;
}

export function submitSheetImport(skipTitleEdit) {
  if (!S._pendingAlbumPath) {
    setError("请先选择照片文件夹");
    return;
  }
  if (!skipTitleEdit && !validateTitleField()) return;
  saveIntent();
  closeImportSheet();
  readPlanTextForImport().then(function (planText) {
    var body = buildImportPayload({ albumPath: S._pendingAlbumPath });
    if (planText) body.planText = planText;
    if (typeof studioToast === "function") {
      studioToast("将新建一篇杂志 · 开始制作", { duration: 2200 });
    }
    return startImport(body);
  }).catch(function (err) {
    setError((err && err.message) || String(err) || "无法开始制作，请重试");
    openImportSheet();
  });
}

export function maybeShowCoach(step) {
  var done = parseInt(localStorage.getItem(LS.coachImportV1) || "0", 10);
  if (done >= 2) return;
  if (step === 1 && done >= 1) return;
  var coach = $("studio-coach");
  var text = $("studio-coach-text");
  if (!coach || !text) return;
  var messages = [
    "从这里开始 · 照片留在本机，不上传云端",
    "选一次旅行的文件夹即可",
  ];
  text.textContent = messages[step - 1] || messages[0];
  coach.style.top = step === 1 ? "auto" : "auto";
  coach.style.bottom = step === 1 ? "120px" : "280px";
  coach.style.left = step === 1 ? "clamp(20px, 4vw, 48px)" : "50%";
  coach.style.transform = step === 1 ? "none" : "translateX(-50%)";
  show(coach, true);
  localStorage.setItem(LS.coachImportV1, String(Math.max(done, step)));
}

export function dismissCoach() {
  show($("studio-coach"), false);
  localStorage.setItem(LS.coachImportV1, "2");
}

export function replayCoachMarks() {
  localStorage.removeItem(LS.coachImportV1);
  openImportSheet();
  maybeShowCoach(1);
}

// ── Recent paths memory ──
export function getRecentPaths() {
  try { return JSON.parse(localStorage.getItem(LS.recentPaths) || "[]"); }
  catch (e) { return []; }
}
export function pushRecentPath(p) {
  if (!p) return;
  var list = getRecentPaths().filter(function (x) { return x !== p; });
  list.unshift(p);
  if (list.length > 5) list = list.slice(0, 5);
  try { localStorage.setItem(LS.recentPaths, JSON.stringify(list)); } catch (e) {}
  renderRecentPaths();
}
export function renderRecentPaths() {
  var dl = $("studio-recent-paths");
  if (!dl) return;
  dl.innerHTML = "";
  getRecentPaths().forEach(function (p) {
    var opt = document.createElement("option");
    opt.value = p;
    dl.appendChild(opt);
  });
}

// ── Import thumbs (real selected photos) ──
export function revokeThumbUrls() {
  S._thumbObjectUrls.forEach(function (u) {
    try { URL.revokeObjectURL(u); } catch (e) { /* ignore */ }
  });
  S._thumbObjectUrls = [];
}

export function setImportThumbs(urls) {
  var c = $("studio-import-thumbs");
  if (!c) return;
  var spans = c.querySelectorAll("span");
  var defaults = [
    "/__studio/assets/demo-album/demo-01.jpg",
    "/__studio/assets/demo-album/demo-02.jpg",
    "/__studio/assets/demo-album/demo-03.jpg",
    "/__studio/assets/demo-album/demo-04.jpg",
  ];
  for (var i = 0; i < spans.length; i++) {
    var u = (urls && urls[i]) || defaults[i];
    var bg = cssBackgroundImage(u);
    spans[i].style.backgroundImage = bg || "";
  }
}
export function readImportThumbsFromFiles(files) {
  if (!files || !files.length || !window.URL || !URL.createObjectURL) return;
  revokeThumbUrls();
  var picked = [];
  for (var i = 0; i < files.length && picked.length < 4; i++) {
    var f = files[i];
    var name = (f.webkitRelativePath || f.name || "").toLowerCase();
    if (/\.(jpe?g|png|webp|heic|heif)$/i.test(name)) picked.push(f);
  }
  S._thumbObjectUrls = picked.map(function (f) { return URL.createObjectURL(f); });
  setImportThumbs(S._thumbObjectUrls);
}

export function estimateUploadBytes(files) {
  var total = 0;
  if (!files) return 0;
  for (var i = 0; i < files.length; i++) total += files[i].size || 0;
  return total;
}

export function confirmLargeUpload(files) {
  var bytes = estimateUploadBytes(files);
  if (bytes <= UPLOAD_BYTES_SOFT_LIMIT) return Promise.resolve(true);
  var body =
    "已选约 " + formatBytes(bytes) + "（" + files.length + " 个文件）。" +
    "浏览器上传上限约 200MB，可能失败。建议改用「选择照片文件夹」导入。";
  if (typeof studioModal === "function") {
    return studioModal({
      title: "照片总量较大",
      body: body,
      confirmText: "仍要上传",
      cancelText: "改用文件夹",
    }).then(function (confirmed) {
      if (!confirmed) {
        openImportSheet();
        requestNativeFolder(null, null, { autoStart: false });
      }
      return confirmed;
    });
  }
  return Promise.resolve(window.confirm(body + "\n\n仍要上传？"));
}

export function initImportSheet() {
  ["studio-open-sheet", "studio-open-sheet-returning", "studio-path-toggle"].forEach(function (id) {
    var el = $(id);
    if (el) el.addEventListener("click", function () { openImportSheet(); });
  });
  var scrim = $("studio-sheet-scrim");
  if (scrim) scrim.addEventListener("click", function () {
    if (S.currentState !== "Importing") closeImportSheet();
  });
  var closeBtn = $("studio-sheet-close");
  if (closeBtn) closeBtn.addEventListener("click", closeImportSheet);
  var pick = $("studio-sheet-pick");
  if (pick) pick.addEventListener("click", function () {
    requestNativeFolder(null, null, { autoStart: false });
  });
  var startBtn = $("studio-sheet-start");
  if (startBtn) startBtn.addEventListener("click", function () { submitSheetImport(false); });
  var skipBtn = $("studio-sheet-skip");
  if (skipBtn) skipBtn.addEventListener("click", function () { submitSheetImport(true); });
  var titleInput = $("trip-title");
  if (titleInput) {
    titleInput.addEventListener("blur", saveIntent);
    titleInput.addEventListener("input", validateTitleField);
  }
  ["trip-place", "trip-feeling"].forEach(function (id) {
    var el = $(id);
    if (el) el.addEventListener("blur", saveIntent);
  });
  var help = $("studio-sheet-help");
  if (help) help.addEventListener("click", function () {
    if (typeof studioToast === "function") {
      studioToast(
        "同一次旅行的照片放一个文件夹（50–100 张最佳）。可建「精选」「素材」子文件夹。照片不会被移动或修改。",
        { duration: 6000 }
      );
    }
  });
  var coachSkip = $("studio-coach-skip");
  if (coachSkip) coachSkip.addEventListener("click", dismissCoach);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && S._sheetOpen && S.currentState !== "Importing") closeImportSheet();
  });
}
