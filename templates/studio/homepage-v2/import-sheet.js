/**
 * 首页 v2 · Import Sheet（M20-d · §7 / §7.1 a11y）。
 *
 * - role=dialog · aria-modal；打开 trap 焦点至 Sheet，关闭归还触发 CTA
 * - Esc 关闭；scrim 点击关闭；关闭按钮 ≥44px
 * - 主按钮 pick-folder（autoStart）；路径导入仅在 Sheet details 内
 * 复用：http.js postJson（pick-folder）、constants.js SHEET_FOCUSABLE、共享 analytics。
 */
import { SHEET_FOCUSABLE } from "../js/constants.js";
import { postJson } from "../js/http.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2, $, show } from "./store.js";
import { startV2Import, buildImportPayload } from "./import-run.js";

let _open = false;
let _previousFocus = null;
let _trapHandler = null;
let _pickInFlight = false;
let _pendingAlbumPath = null;
let _importStarted = false; // 本次 Sheet 会话是否已发起 import（区分 abandon）

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

function resetConfirm() {
  _pendingAlbumPath = null;
  show($("v2-sheet-confirm"), false);
  var pick = $("v2-sheet-pick");
  if (pick) {
    pick.disabled = false;
    pick.textContent = "选择本次旅行的照片文件夹";
  }
}

function showConfirm(albumPath) {
  _pendingAlbumPath = albumPath;
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
  if (titleInput) titleInput.focus();
}

export function openImportSheet() {
  if (V2.state === "Importing") {
    if (typeof studioToast === "function") studioToast("正在制作中", { duration: 2200 });
    return;
  }
  var root = $("v2-sheet-root");
  var sheet = $("v2-import-sheet");
  if (!root || !sheet) return;
  _previousFocus = document.activeElement;
  _importStarted = false;
  show(root, true);
  document.body.classList.add("v2-sheet-open");
  _open = true;
  setError("");
  trapFocus(sheet);
  var pick = $("v2-sheet-pick");
  if (pick && !pick.disabled) pick.focus();
  trackStudioEvent("open_sheet", { state: V2.state, surface: "bench" });
}

export function closeImportSheet(reason) {
  if (!_open) return;
  var root = $("v2-sheet-root");
  var sheet = $("v2-import-sheet");
  if (root) show(root, false);
  document.body.classList.remove("v2-sheet-open");
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

function startFromConfirm() {
  if (!_pendingAlbumPath) {
    setError("请先选择照片文件夹");
    return;
  }
  var titleInput = $("v2-trip-title");
  var title = titleInput ? (titleInput.value || "").trim() : "";
  var body = buildImportPayload(_pendingAlbumPath, title);
  _importStarted = true;
  closeImportSheet("start");
  if (typeof studioToast === "function") {
    studioToast("将新建一篇画册 · 开始制作", { duration: 2000 });
  }
  startV2Import(body, { source: "本机文件夹" }).catch(function () {
    /* 错误已在 import-run 内 toast + reroute */
  });
}

export function initImportSheet() {
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
  var start = $("v2-sheet-start");
  if (start) start.addEventListener("click", startFromConfirm);
  var pathBtn = $("v2-path-submit");
  if (pathBtn) pathBtn.addEventListener("click", submitWithPath);
  var pathInput = $("v2-album-path");
  if (pathInput) pathInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); submitWithPath(); }
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _open && V2.state !== "Importing") closeImportSheet("esc");
  });
}
