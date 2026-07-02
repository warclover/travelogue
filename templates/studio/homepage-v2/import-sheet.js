/**
 * 首页 v2 · Import Sheet（M20-d · §7 / §7.1 a11y）。
 *
 * - role=dialog · aria-modal；打开 trap 焦点至 Sheet，关闭归还触发 CTA
 * - Esc 关闭；scrim 点击关闭；关闭按钮 ≥44px
 * - 主按钮 pick-folder（autoStart）；路径导入仅在 Sheet details 内
 * 复用：http.js postJson（pick-folder）、constants.js SHEET_FOCUSABLE、共享 analytics。
 */
import { SHEET_FOCUSABLE, UPLOAD_BYTES_SOFT_LIMIT } from "../js/constants.js";
import { postJson } from "../js/http.js";
import {
  trackStudioEvent,
  trackImportPhotoCullPref,
  trackImportKeepDupesPref,
} from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { startV2Import, startV2UploadImport, buildImportPayload } from "./import-run.js";

let _open = false;
let _previousFocus = null;
let _trapHandler = null;
let _pickInFlight = false;
let _uploadInFlight = false;
let _pendingAlbumPath = null;
let _pendingUploadFiles = null;
let _pendingPhotoCount = null;
let _importStarted = false; // 本次 Sheet 会话是否已发起 import（区分 abandon）
let _photoCullTouched = false;
let _keepDupesTouched = false;
let _activeMode = "quick_share";
const IMPORT_DRAFT_KEY = "travelogue.studio.importDraft";
const IMPORT_MODE_KEY = "travelogue.studio.lastImportMode";
const _featureFlags = {
  importDualModeEnabled: true,
  importSheetLargeEnabled: true,
};

function setV2BackgroundInert(inert) {
  var ids = ["v2-bento-hero", "v2-shelf"];
  ids.forEach(function (id) {
    var el = $(id);
    if (!el) return;
    if (inert) {
      el.setAttribute("inert", "");
      el.setAttribute("aria-hidden", "true");
    } else {
      el.removeAttribute("inert");
      el.removeAttribute("aria-hidden");
    }
  });
}

function setError(msg) {
  var el = $("v2-sheet-error");
  if (!el) return;
  el.textContent = msg || "";
  show(el, !!msg);
}

function focusableEls(container) {
  return Array.prototype.slice
    .call(container.querySelectorAll(SHEET_FOCUSABLE))
    .filter(function (el) {
      return el.offsetParent !== null || el === document.activeElement;
    });
}

function trapFocus(sheet) {
  _trapHandler = function (e) {
    if (e.key !== "Tab") return;
    var els = focusableEls(sheet);
    if (!els.length) return;
    var first = els[0];
    var last = els[els.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  };
  sheet.addEventListener("keydown", _trapHandler);
}

function releaseTrap(sheet) {
  if (_trapHandler && sheet) sheet.removeEventListener("keydown", _trapHandler);
  _trapHandler = null;
}

function updateQuickStartLabel() {
  var btn = $("v2-sheet-start-quick");
  if (!btn) return;
  btn.textContent = _pendingUploadFiles && _pendingUploadFiles.length
    ? "开始上传"
    : "开始制作";
}

function resetConfirm() {
  _pendingAlbumPath = null;
  _pendingUploadFiles = null;
  show($("v2-sheet-confirm"), false);
  switchMode("quick_share", { persist: false });
  updateQuickStartLabel();
  var pick = $("v2-sheet-pick");
  if (pick) {
    pick.disabled = false;
    pick.textContent = "选择本次旅行的照片文件夹";
  }
}

function showConfirm(albumPath) {
  _pendingAlbumPath = albumPath;
  _pendingUploadFiles = null;
  _pendingPhotoCount = null;
  fetchAlbumPhotoCount(albumPath).then(function (count) {
    _pendingPhotoCount = count;
    updateLayoutDensityWarn();
    updatePhotoCullOptoutUi();
    saveSheetDraft();
  });
  var picked = $("v2-sheet-picked");
  if (picked) picked.textContent = "已选择：" + albumPath;
  var titleInput = $("v2-trip-title");
  if (titleInput && !titleInput.value) {
    var parts = String(albumPath).replace(/[\\/]+$/, "").split(/[\\/]/);
    titleInput.value = (parts[parts.length - 1] || "").slice(0, 20);
  }
  var pick = $("v2-sheet-pick");
  if (pick) {
    pick.disabled = true;
    pick.textContent = "已选择文件夹";
  }
  show($("v2-sheet-confirm"), true);
  restoreModeAndDraft();
  updateQuickStartLabel();
  var quickStart = $("v2-sheet-start-quick");
  if (_activeMode === "fine_craft" && titleInput) titleInput.focus();
  else if (quickStart) quickStart.focus();
}

function showUploadConfirm(files) {
  _pendingAlbumPath = null;
  _pendingUploadFiles = files ? Array.prototype.slice.call(files) : [];
  _pendingPhotoCount = _pendingUploadFiles.length;
  var picked = $("v2-sheet-picked");
  if (picked) {
    picked.textContent = "已选择：浏览器上传（" + _pendingPhotoCount + " 张）";
  }
  var pick = $("v2-sheet-pick");
  if (pick) {
    pick.disabled = false;
    pick.textContent = "选择本次旅行的照片文件夹";
  }
  switchMode("quick_share", { persist: false });
  updatePhotoCullOptoutUi();
  saveSheetDraft();
  show($("v2-sheet-confirm"), true);
  restoreModeAndDraft();
  updateQuickStartLabel();
  var startQuick = $("v2-sheet-start-quick");
  if (startQuick) startQuick.focus();
}

function safeGet(id) {
  var el = $(id);
  if (!el) return "";
  return String(el.value || "").trim();
}

function safeSet(id, val) {
  var el = $(id);
  if (!el) return;
  el.value = val || "";
}

var LAYOUT_DENSITY_VALUES = ["balanced", "hero_first", "collage_first"];

function readLayoutDensity() {
  var checked = document.querySelector('input[name="v2-layout-density"]:checked');
  var v = checked ? String(checked.value || "").trim() : "balanced";
  return LAYOUT_DENSITY_VALUES.indexOf(v) >= 0 ? v : "balanced";
}

function setLayoutDensity(value) {
  var v = LAYOUT_DENSITY_VALUES.indexOf(String(value || "").trim()) >= 0
    ? String(value).trim()
    : "balanced";
  var inputs = document.querySelectorAll('input[name="v2-layout-density"]');
  inputs.forEach(function (input) {
    input.checked = input.value === v;
  });
  updateLayoutDensityWarn();
}

function updateLayoutDensityWarn() {
  var warn = $("v2-layout-density-warn");
  if (!warn) return;
  var collage = readLayoutDensity() === "collage_first";
  var fewPhotos = _pendingPhotoCount != null && _pendingPhotoCount < 35;
  show(warn, collage && fewPhotos);
}

function readPhotoCullEnabled() {
  var el = $("v2-photo-cull-enabled");
  if (!el) return false;
  return !!el.checked;
}

function setPhotoCullEnabled(enabled) {
  var el = $("v2-photo-cull-enabled");
  if (!el) return;
  el.checked = enabled === true;
  updatePhotoCullOptoutUi();
}

function updatePhotoCullOptoutUi() {
  // 智能挑选状态变化会影响「保留连拍」副文案分支（§5.4），级联刷新
  updateKeepDupesNoteUi();
  var optout = $("v2-photo-cull-optout");
  if (!optout) return;
  if (readPhotoCullEnabled()) {
    optout.textContent = "";
    show(optout, false);
    return;
  }
  var parts = [];
  if (_pendingPhotoCount != null) {
    parts.push("不做智能挑选，" + _pendingPhotoCount + " 张照片将参与排版。");
  } else {
    parts.push("不做智能挑选，文件夹内照片将参与排版。");
  }
  parts.push("相同文件仍会自动去重，与智能挑选无关。");
  optout.textContent = parts.join(" ");
  show(optout, true);
}

function readKeepDupesEnabled() {
  var el = $("v2-keep-dupes-enabled");
  if (!el) return false;
  return !!el.checked;
}

function setKeepDupesEnabled(enabled) {
  var el = $("v2-keep-dupes-enabled");
  if (!el) return;
  el.checked = enabled === true;
  updateKeepDupesNoteUi();
}

function updateKeepDupesNoteUi() {
  var note = $("v2-keep-dupes-note");
  if (!note) return;
  if (!readKeepDupesEnabled()) {
    note.textContent = "";
    show(note, false);
    return;
  }
  // PRD-P9-F2 §5.4 · 副文案按智能挑选是否开启分两支
  if (readPhotoCullEnabled()) {
    note.textContent =
      "将保留相近照片进入排版池；智能挑选仍可能在成册时择优。取消「智能挑选照片」可完整成组。";
  } else {
    note.textContent = "将保留时间相近或画面相似的照片，适合完整记录精彩瞬间。";
  }
  show(note, true);
}

function fetchAlbumPhotoCount(albumPath) {
  return postJson("/__travelogue/album-preview", { albumPath: albumPath })
    .then(function (res) {
      var data = res.body || {};
      if (res.status >= 400 || !data.ok) return null;
      var n = Number(data.photoCount);
      return Number.isFinite(n) && n >= 0 ? n : null;
    })
    .catch(function () {
      return null;
    });
}

function readSheetDraft() {
  try {
    var raw = sessionStorage.getItem(IMPORT_DRAFT_KEY);
    if (!raw) return {};
    var parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (_e) {
    return {};
  }
}

function saveSheetDraft() {
  var draft = {
    mode: _activeMode,
    title: safeGet("v2-trip-title"),
    place: safeGet("v2-trip-place"),
    dateStart: safeGet("v2-date-start"),
    dateEnd: safeGet("v2-date-end"),
    userNotes: safeGet("v2-user-notes"),
    travelNotes: safeGet("v2-travel-notes"),
    featuredDir: safeGet("v2-featured-dir"),
    materialDir: safeGet("v2-material-dir"),
    layoutDensity: readLayoutDensity(),
    photoCullEnabled: readPhotoCullEnabled(),
    photoCullTouched: _photoCullTouched,
    keepNearDuplicates: readKeepDupesEnabled(),
    keepDupesTouched: _keepDupesTouched,
    photoCount: _pendingPhotoCount,
    planFileName: (function () {
      var input = $("v2-plan-file");
      if (!input || !input.files || !input.files[0]) return "";
      return String(input.files[0].name || "");
    })(),
  };
  try {
    sessionStorage.setItem(IMPORT_DRAFT_KEY, JSON.stringify(draft));
    sessionStorage.setItem(IMPORT_MODE_KEY, _activeMode);
  } catch (_e) {
    /* ignore */
  }
}

function restoreModeAndDraft() {
  var draft = readSheetDraft();
  var mode = String(draft.mode || "").trim();
  if (!mode) {
    try {
      mode = String(sessionStorage.getItem(IMPORT_MODE_KEY) || "").trim();
    } catch (_e) {
      mode = "";
    }
  }
  switchMode(mode === "fine_craft" ? "fine_craft" : "quick_share", { persist: false });
  safeSet("v2-trip-title", draft.title || "");
  safeSet("v2-trip-place", draft.place || "");
  safeSet("v2-date-start", draft.dateStart || "");
  safeSet("v2-date-end", draft.dateEnd || "");
  safeSet("v2-user-notes", draft.userNotes || "");
  safeSet("v2-travel-notes", draft.travelNotes || "");
  safeSet("v2-featured-dir", draft.featuredDir || "");
  safeSet("v2-material-dir", draft.materialDir || "");
  setLayoutDensity(draft.layoutDensity || "balanced");
  setPhotoCullEnabled(draft.photoCullEnabled === true);
  _photoCullTouched = !!draft.photoCullTouched;
  setKeepDupesEnabled(draft.keepNearDuplicates === true);
  _keepDupesTouched = !!draft.keepDupesTouched;
  _pendingPhotoCount = typeof draft.photoCount === "number" ? draft.photoCount : null;
  updateLayoutDensityWarn();
  updatePhotoCullOptoutUi();
  var planName = $("v2-plan-file-name");
  if (planName) {
    planName.textContent = draft.planFileName
      ? ("已选计划文件：" + draft.planFileName)
      : "";
  }
}

function switchMode(nextMode, opts) {
  opts = opts || {};
  if (!_featureFlags.importDualModeEnabled) {
    _activeMode = "quick_share";
  } else {
    _activeMode = nextMode === "fine_craft" ? "fine_craft" : "quick_share";
  }
  var quickTab = $("v2-sheet-mode-quick");
  var fineTab = $("v2-sheet-mode-fine");
  var quickPanel = $("v2-sheet-panel-quick");
  var finePanel = $("v2-sheet-panel-fine");
  if (quickTab) {
    quickTab.setAttribute("aria-selected", _activeMode === "quick_share" ? "true" : "false");
    quickTab.setAttribute("tabindex", _activeMode === "quick_share" ? "0" : "-1");
  }
  if (fineTab) {
    fineTab.setAttribute("aria-selected", _activeMode === "fine_craft" ? "true" : "false");
    fineTab.setAttribute("tabindex", _activeMode === "fine_craft" ? "0" : "-1");
  }
  show(quickPanel, _activeMode === "quick_share");
  show(finePanel, _activeMode === "fine_craft");
  if (opts.persist !== false) saveSheetDraft();
}

function applyFeatureFlags() {
  var sheet = $("v2-import-sheet");
  if (sheet) {
    sheet.classList.toggle("v2-sheet--legacy-size", !_featureFlags.importSheetLargeEnabled);
  }
  var tabs = document.querySelector(".v2-sheet__mode-tabs");
  var finePanel = $("v2-sheet-panel-fine");
  if (!_featureFlags.importDualModeEnabled) {
    if (tabs) show(tabs, false);
    if (finePanel) show(finePanel, false);
    _activeMode = "quick_share";
  } else if (tabs) {
    show(tabs, true);
  }
}

function loadFeatureFlags() {
  return fetch("/__travelogue/config")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      var studio = (data && data.studio) || {};
      if (typeof studio.importDualModeEnabled === "boolean") {
        _featureFlags.importDualModeEnabled = studio.importDualModeEnabled;
      }
      if (typeof studio.importSheetLargeEnabled === "boolean") {
        _featureFlags.importSheetLargeEnabled = studio.importSheetLargeEnabled;
      }
      applyFeatureFlags();
    })
    .catch(function () {
      applyFeatureFlags();
    });
}

function readPlanFileText() {
  var input = $("v2-plan-file");
  if (!input || !input.files || !input.files[0]) return Promise.resolve(null);
  var file = input.files[0];
  var name = String(file.name || "");
  var lower = name.toLowerCase();
  if (!(lower.endsWith(".txt") || lower.endsWith(".md"))) {
    return Promise.reject(new Error("计划文件仅支持 .txt / .md"));
  }
  if ((file.size || 0) > 32 * 1024) {
    return Promise.reject(new Error("计划文件不能超过 32KB"));
  }
  return new Promise(function (resolve, reject) {
    var reader = new FileReader();
    reader.onload = function () {
      var text = String(reader.result || "").trim();
      resolve(text || null);
    };
    reader.onerror = function () {
      reject(new Error("读取计划文件失败，请重试"));
    };
    reader.readAsText(file, "utf-8");
  });
}

function maybeShowDateHint(start, end) {
  if ((start && !end) || (!start && end)) {
    if (typeof studioToast === "function") {
      studioToast("另一侧将用照片时间自动推断", { duration: 2200 });
    }
  }
}

function validateFineFields() {
  var start = safeGet("v2-date-start");
  var end = safeGet("v2-date-end");
  if (start && !/^\d{4}-\d{2}-\d{2}$/.test(start)) return "开始日期格式无效，请使用 YYYY-MM-DD";
  if (end && !/^\d{4}-\d{2}-\d{2}$/.test(end)) return "结束日期格式无效，请使用 YYYY-MM-DD";
  if (start && end && start > end) return "开始日期不能晚于结束日期";
  return "";
}

function buildSheetPayload() {
  var title = safeGet("v2-trip-title");
  var body = buildImportPayload(_pendingAlbumPath, title);
  body.mode = _activeMode;
  var place = safeGet("v2-trip-place");
  var userNotes = safeGet("v2-user-notes");
  var travelNotes = safeGet("v2-travel-notes");
  var dateStart = safeGet("v2-date-start");
  var dateEnd = safeGet("v2-date-end");
  var featuredDir = safeGet("v2-featured-dir");
  var materialDir = safeGet("v2-material-dir");
  if (_activeMode === "fine_craft") {
    var err = validateFineFields();
    if (err) {
      setError(err);
      return null;
    }
  }
  maybeShowDateHint(dateStart, dateEnd);
  if (place) body.place = place;
  if (userNotes) body.userNotes = userNotes.slice(0, 200);
  if (travelNotes) body.travelNotes = travelNotes.slice(0, 500);
  if (dateStart || dateEnd) {
    body.dateRange = { source: "user" };
    if (dateStart) body.dateRange.start = dateStart;
    if (dateEnd) body.dateRange.end = dateEnd;
  }
  if (featuredDir) body.featuredDir = featuredDir;
  if (materialDir) body.materialDir = materialDir;
  if (_activeMode === "fine_craft") {
    body.layoutDensity = readLayoutDensity();
  }
  body.photoCullEnabled = readPhotoCullEnabled();
  body.keepNearDuplicates = readKeepDupesEnabled();
  if (_pendingPhotoCount != null) body.eligibleCount = _pendingPhotoCount;
  return body;
}

export function openImportSheet() {
  if (V2.state === "Importing") {
    if (typeof studioToast === "function") studioToast("正在制作中", { duration: 2200 });
    return;
  }
  if (_open) return;
  var root = $("v2-sheet-root");
  var sheet = $("v2-import-sheet");
  if (!root || !sheet) return;
  _previousFocus = document.activeElement;
  _importStarted = false;
  show(root, true);
  document.body.classList.add("v2-sheet-open");
  setV2BackgroundInert(true);
  _open = true;
  setError("");
  trapFocus(sheet);
  var pick = $("v2-sheet-pick");
  if (pick && !pick.disabled) pick.focus();
  trackStudioEvent("open_sheet", { state: V2.state, surface: "bench" });
  trackStudioEvent("import_mode_view", { mode: "quick_share" });
}

export function closeImportSheet(reason) {
  if (!_open) return;
  var root = $("v2-sheet-root");
  var sheet = $("v2-import-sheet");
  if (root) show(root, false);
  document.body.classList.remove("v2-sheet-open");
  setV2BackgroundInert(false);
  _open = false;
  releaseTrap(sheet);
  trackStudioEvent("sheet_close", { reason: reason || "dismiss" });
  // 未发起 import 即关闭 → abandon（§13.2 漏斗）
  if (!_importStarted) trackStudioEvent("sheet_abandon", {});
  // 焦点归还触发 CTA（§7.1）
  if (_previousFocus && typeof _previousFocus.focus === "function") {
    _previousFocus.focus();
  } else {
    var cta = $("v2-cta");
    if (cta) cta.focus();
  }
}

function pickFolder() {
  if (_pickInFlight) {
    if (typeof studioToast === "function") {
      studioToast("文件夹选择器已打开，请在其窗口中操作", { duration: 2200 });
    }
    return;
  }
  _pickInFlight = true;
  setError("");
  var pickToast = typeof studioToast === "function"
    ? studioToast("正在打开文件夹选择器…", { duration: 0 })
    : null;
  postJson("/__travelogue/pick-folder", {})
    .then(function (res) {
      var data = res.body || {};
      if (data.cancelled) return;
      if (res.status >= 400 || data.ok === false || !data.albumPath) {
        var msg = data.message || data.detail ||
          "无法打开本机选文件夹。请在「其他导入方式」粘贴路径。";
        setError(msg);
        var details = document.querySelectorAll(".v2-sheet__details");
        if (details && details[1]) details[1].open = true;
        return;
      }
      trackStudioEvent("pick_folder", { via: "native" });
      showConfirm(data.albumPath);
    })
    .catch(function () {
      setError("无法连接选文件夹服务。请粘贴路径，或确认 Studio 正在运行。");
    })
    .finally(function () {
      if (pickToast && pickToast.parentNode) pickToast.parentNode.removeChild(pickToast);
      _pickInFlight = false;
    });
}

function submitWithPath() {
  var input = $("v2-album-path");
  var path = input ? (input.value || "").trim() : "";
  if (!path) {
    setError("请填写照片文件夹路径，例如 D:\\Photos\\Kyoto2025");
    return;
  }
  showConfirm(path);
}

function estimateUploadBytes(files) {
  var total = 0;
  for (var i = 0; i < files.length; i++) total += files[i].size || 0;
  return total;
}

function formatBytes(bytes) {
  if (!bytes || bytes <= 0) return "0B";
  var units = ["B", "KB", "MB", "GB"];
  var val = bytes;
  var idx = 0;
  while (val >= 1024 && idx < units.length - 1) {
    val /= 1024;
    idx += 1;
  }
  var fixed = val >= 10 || idx === 0 ? Math.round(val) : Math.round(val * 10) / 10;
  return fixed + units[idx];
}

function confirmLargeUpload(files) {
  var bytes = estimateUploadBytes(files);
  if (bytes <= UPLOAD_BYTES_SOFT_LIMIT) return Promise.resolve(true);
  var body =
    "已选约 " + formatBytes(bytes) + "（" + files.length + " 个文件）。" +
    " 建议总量≤200MB，超过后可能变慢或失败。";
  if (typeof studioModal === "function") {
    return studioModal({
      title: "照片总量较大",
      body: body,
      confirmText: "仍要上传",
      cancelText: "改用文件夹",
    });
  }
  return Promise.resolve(window.confirm(body + "\n\n仍要上传？"));
}

function handleUploadInput() {
  if (_uploadInFlight) return;
  var input = $("v2-album-upload");
  var files = input && input.files ? Array.prototype.slice.call(input.files) : [];
  if (!files.length) return;
  _uploadInFlight = true;
  setError("");
  confirmLargeUpload(files).then(function (proceed) {
    if (!proceed) return;
    showUploadConfirm(files);
  }).catch(function () {
    /* ignore */
  }).finally(function () {
    if (input) input.value = "";
    _uploadInFlight = false;
  });
}

function startUploadFromConfirm() {
  var files = _pendingUploadFiles ? Array.prototype.slice.call(_pendingUploadFiles) : [];
  if (!files.length) {
    setError("请先选择要上传的照片");
    return;
  }
  saveSheetDraft();
  _importStarted = true;
  _pendingUploadFiles = null;
  closeImportSheet("start_upload");
  if (typeof studioToast === "function") {
    studioToast("已选择 " + files.length + " 张照片，开始上传…", { duration: 2200 });
  }
  return startV2UploadImport(files, {
    source: "浏览器上传",
    photoCullEnabled: readPhotoCullEnabled(),
    keepNearDuplicates: readKeepDupesEnabled(),
    mode: _activeMode,
  }).catch(function () {
    /* 错误由 import-run 内部展示 */
  });
}

function startFromConfirm() {
  if (_pendingUploadFiles && _pendingUploadFiles.length) {
    return startUploadFromConfirm();
  }
  if (!_pendingAlbumPath) {
    setError("请先选择照片文件夹");
    return;
  }
  var body = buildSheetPayload();
  if (!body) return;
  readPlanFileText().then(function (planText) {
    if (planText) body.planText = planText;
    saveSheetDraft();
    _importStarted = true;
    closeImportSheet("start");
    if (typeof studioToast === "function") {
      studioToast(
        _activeMode === "fine_craft" ? "已按精细制作启动" : "将新建一篇画册 · 开始制作",
        { duration: 2000 }
      );
    }
    return startV2Import(body, { source: "本机文件夹" }).catch(function () {
      /* 错误已在 import-run 内 toast + reroute */
    });
  }).catch(function (err) {
    setError(err && err.message ? err.message : "读取计划文件失败，请重试");
  });
}

function loadTemplateSelectOptions() {
  var sel = $("v2-template-mode");
  if (!sel) return;
  fetch("/__travelogue/templates")
    .then(function (r) { return r.json(); })
    .then(function (data) {
      if (!data || !data.ok) return;
      var smart = document.createElement("option");
      smart.value = "smart";
      smart.textContent = data.smartLabel || "智能匹配（推荐）";
      sel.innerHTML = "";
      sel.appendChild(smart);
      (data.templates || []).forEach(function (t) {
        var opt = document.createElement("option");
        opt.value = "manual:" + (t.templateId || "");
        opt.textContent = (t.label || t.templateId) + "（手动指定）";
        sel.appendChild(opt);
      });
      sel.value = "smart";
      updateTemplateModeHint(data, sel.value);
    })
    .catch(function () { /* keep static HTML options */ });
}

function updateTemplateModeHint(data, value) {
  var hint = $("v2-template-hint");
  if (!hint) return;
  var hints = (data && data.modeHints) || {};
  var v = String(value || "smart");
  if (v.indexOf("manual:") === 0) {
    hint.textContent = hints.manual || "全程使用你指定的模板。";
    return;
  }
  hint.textContent = hints.smart || hint.textContent;
}

function wireTemplateSelect() {
  var sel = $("v2-template-mode");
  if (!sel || sel.dataset.wired === "1") return;
  sel.dataset.wired = "1";
  trackStudioEvent("template_selector_impression", { surface: "v2_sheet" });
  sel.addEventListener("change", function () {
    var v = String(sel.value || "smart");
    trackStudioEvent("template_mode_changed", { value: v });
    if (v.indexOf("manual:") === 0) {
      trackStudioEvent("template_manual_selected", { template_id: v.slice(7) });
    }
    fetch("/__travelogue/templates")
      .then(function (r) { return r.json(); })
      .then(function (data) { updateTemplateModeHint(data, v); })
      .catch(function () {});
  });
}

export function initImportSheet() {
  loadFeatureFlags();
  loadTemplateSelectOptions();
  wireTemplateSelect();
  var cta = $("v2-cta");
  if (cta) cta.addEventListener("click", function () {
    trackStudioEvent("cta_click", { surface: "bench" });
    openImportSheet();
  });

  var scrim = $("v2-sheet-scrim");
  if (scrim) scrim.addEventListener("click", function () {
    if (V2.state !== "Importing") closeImportSheet("scrim");
  });
  var closeBtn = $("v2-sheet-close");
  if (closeBtn) closeBtn.addEventListener("click", function () { closeImportSheet("close_btn"); });

  var pick = $("v2-sheet-pick");
  if (pick) pick.addEventListener("click", pickFolder);
  var repick = $("v2-sheet-repick");
  if (repick) repick.addEventListener("click", function () {
    resetConfirm();
    pickFolder();
  });
  var repickFine = $("v2-sheet-repick-fine");
  if (repickFine) repickFine.addEventListener("click", function () {
    resetConfirm();
    pickFolder();
  });
  var startQuick = $("v2-sheet-start-quick");
  if (startQuick) startQuick.addEventListener("click", function () {
    switchMode("quick_share");
    startFromConfirm();
  });
  var startFine = $("v2-sheet-start-fine");
  if (startFine) startFine.addEventListener("click", function () {
    switchMode("fine_craft");
    startFromConfirm();
  });
  var tabQuick = $("v2-sheet-mode-quick");
  if (tabQuick) tabQuick.addEventListener("click", function () {
    switchMode("quick_share");
    trackStudioEvent("import_mode_switch", { mode: "quick_share", via: "click" });
  });
  var tabFine = $("v2-sheet-mode-fine");
  if (tabFine) tabFine.addEventListener("click", function () {
    switchMode("fine_craft");
    trackStudioEvent("import_mode_switch", { mode: "fine_craft", via: "click" });
  });
  function onTabKeydown(e) {
    if (!_featureFlags.importDualModeEnabled) return;
    if (e.key !== "ArrowLeft" && e.key !== "ArrowRight" && e.key !== "Home" && e.key !== "End") return;
    e.preventDefault();
    if (e.key === "ArrowLeft" || e.key === "Home") {
      switchMode("quick_share");
      if (tabQuick) tabQuick.focus();
    } else {
      switchMode("fine_craft");
      if (tabFine) tabFine.focus();
    }
    trackStudioEvent("import_mode_switch", { mode: _activeMode, via: "keyboard" });
  }
  if (tabQuick) tabQuick.addEventListener("keydown", onTabKeydown);
  if (tabFine) tabFine.addEventListener("keydown", onTabKeydown);

  var photoCull = $("v2-photo-cull-enabled");
  if (photoCull) {
    photoCull.addEventListener("change", function () {
      _photoCullTouched = true;
      updatePhotoCullOptoutUi();
      saveSheetDraft();
      trackImportPhotoCullPref({
        enabled: readPhotoCullEnabled(),
        mode: _activeMode,
        photo_count: _pendingPhotoCount,
        pref_source: "draft",
      });
    });
  }

  var keepDupes = $("v2-keep-dupes-enabled");
  if (keepDupes) {
    keepDupes.addEventListener("change", function () {
      _keepDupesTouched = true;
      updateKeepDupesNoteUi();
      saveSheetDraft();
      trackImportKeepDupesPref({
        enabled: readKeepDupesEnabled(),
        mode: _activeMode,
        photo_count: _pendingPhotoCount,
        pref_source: "draft",
      });
    });
  }

  var draftIds = [
    "v2-trip-title",
    "v2-trip-place",
    "v2-date-start",
    "v2-date-end",
    "v2-user-notes",
    "v2-travel-notes",
    "v2-plan-file",
    "v2-featured-dir",
    "v2-material-dir",
  ];
  draftIds.forEach(function (id) {
    var el = $(id);
    if (!el) return;
    el.addEventListener("input", function () {
      setError("");
      saveSheetDraft();
    });
    el.addEventListener("change", saveSheetDraft);
  });
  var densityInputs = document.querySelectorAll('input[name="v2-layout-density"]');
  var _lastLayoutDensity = readLayoutDensity();
  Array.prototype.forEach.call(densityInputs, function (input) {
    input.addEventListener("change", function () {
      var next = readLayoutDensity();
      trackStudioEvent("layout_density_change", { from: _lastLayoutDensity, to: next });
      _lastLayoutDensity = next;
      saveSheetDraft();
      updateLayoutDensityWarn();
    });
  });
  var chips = document.querySelectorAll(".v2-sheet__chip[data-fill]");
  if (chips && chips.length) {
    Array.prototype.forEach.call(chips, function (chip) {
      chip.addEventListener("click", function () {
        var targetId = chip.getAttribute("data-fill") || "";
        var target = $(targetId);
        if (!target) return;
        target.value = chip.textContent || "";
        saveSheetDraft();
        target.focus();
      });
    });
  }
  var planInput = $("v2-plan-file");
  var planName = $("v2-plan-file-name");
  if (planInput) {
    planInput.addEventListener("change", function () {
      var file = planInput.files && planInput.files[0] ? planInput.files[0] : null;
      if (planName) planName.textContent = file ? ("已选计划文件：" + file.name) : "";
      saveSheetDraft();
    });
  }
  var pathBtn = $("v2-path-submit");
  if (pathBtn) pathBtn.addEventListener("click", submitWithPath);
  var pathInput = $("v2-album-path");
  if (pathInput) pathInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); submitWithPath(); }
  });
  var uploadInput = $("v2-album-upload");
  if (uploadInput) uploadInput.addEventListener("change", handleUploadInput);

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _open && V2.state !== "Importing") closeImportSheet("esc");
  });
}
