/**
 * OLT M2 · 票根副券行 + 管理成品列表（DOM）。
 */
import { getJson, postJson, studioAuthHeaders } from "../js/http.js";
import { revealLongshotOutput } from "../js/longshot-client.js";
import { trackStudioEvent } from "../js/analytics.js";
import { runShelfLongshot } from "./shelf-longshot.js";
import { shelfExportRequestForTrip } from "../js/portfolio-export-logic.js";
import {
  allowReadyBadge,
  deleteConfirmCopy,
  hasManageOutputs,
  lastRecipeRequest,
  manageRows,
  outputChips,
  overflowAriaLabel,
  reexportRequest,
  revealFailToast,
  shouldInsertOutputStubs,
} from "./shelf-outputs-logic.js";

var _fly = null;
var _sheet = null;

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function el(tag, className, text) {
  var node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = text;
  return node;
}

function closeFly() {
  if (_fly && _fly.parentNode) _fly.parentNode.removeChild(_fly);
  _fly = null;
}

function closeSheet() {
  if (_sheet && _sheet.parentNode) _sheet.parentNode.removeChild(_sheet);
  _sheet = null;
}

function stop(e) {
  if (!e) return;
  e.preventDefault();
  e.stopPropagation();
}

function revealChip(trip, chip, onMissing) {
  var rel = chip && chip.revealRelPath;
  if (!trip || !trip.tripId || !rel) {
    toast(revealFailToast(), { duration: 3200 });
    if (typeof onMissing === "function") onMissing();
    return Promise.resolve(false);
  }
  return revealLongshotOutput(trip.tripId, rel).then(function (res) {
    if (res && res.status === 200 && res.body && res.body.ok) return true;
    toast(revealFailToast(), { duration: 3200 });
    if (typeof onMissing === "function") onMissing();
    return false;
  }).catch(function () {
    toast(revealFailToast(), { duration: 3200 });
    if (typeof onMissing === "function") onMissing();
    return false;
  });
}

export function runTripRecipeReexport(trip, surface) {
  var recipe = lastRecipeRequest(trip);
  var opts = shelfExportRequestForTrip(
    trip,
    Object.assign({ surface: surface || "shelf_stale" }, recipe)
  );
  return runShelfLongshot(trip, opts);
}

function reexport(trip, item) {
  var req = reexportRequest(item);
  if (req.platform === "share_zip") {
    toast("正在打包分享包…", { duration: 2400 });
    return postJson("/__travelogue/export", {
      tripId: trip.tripId,
      confirmPrivacy: true,
      allowMissingSource: true,
    }).then(function (res) {
      if (res.status === 200 && res.body && res.body.ok) {
        toast("分享包已就绪", { duration: 2800 });
        return;
      }
      toast((res.body && res.body.message) || "无法重新导出", { duration: 3200 });
    }).catch(function () {
      toast("无法重新导出", { duration: 3200 });
    });
  }
  if (req.platform === "pdf") {
    toast("PDF 请打开这本书后导出", { duration: 3200 });
    return Promise.resolve();
  }
  var opts = { surface: "outputs", platform: req.platform };
  if (req.segmentMode) opts.segmentMode = req.segmentMode;
  return runShelfLongshot(trip, opts);
}

function bindActivate(node, fn) {
  node.addEventListener("click", function (e) {
    stop(e);
    fn();
  });
  node.addEventListener("keydown", function (e) {
    if (e.key !== "Enter" && e.key !== " ") return;
    stop(e);
    fn();
  });
}

function showFly(anchor, items) {
  closeFly();
  var fly = el("div", "v2-shelf__stub-fly");
  fly.setAttribute("role", "menu");
  items.forEach(function (item) {
    var btn = el("button", "v2-shelf__stub-fly-item", item.label);
    btn.type = "button";
    btn.setAttribute("role", "menuitem");
    btn.addEventListener("click", function (e) {
      stop(e);
      closeFly();
      item.run();
    });
    fly.appendChild(btn);
  });
  document.body.appendChild(fly);
  var box = anchor.getBoundingClientRect();
  fly.style.left = Math.max(8, box.left) + "px";
  fly.style.top = Math.min(window.innerHeight - 80, box.bottom + 4) + "px";
  _fly = fly;
  var dismiss = function (e) {
    if (_fly && !_fly.contains(e.target)) closeFly();
    document.removeEventListener("mousedown", dismiss, true);
  };
  setTimeout(function () {
    document.addEventListener("mousedown", dismiss, true);
  }, 0);
}

function bindOutdatedMenu(chipEl, trip, chip, onRevealFail) {
  var pressTimer = null;
  var openMenu = function () {
    showFly(chipEl, [
      { label: "重新导出", run: function () { reexport(trip, chip); } },
      { label: "在文件夹中显示", run: function () { revealChip(trip, chip, onRevealFail); } },
    ]);
  };
  chipEl.addEventListener("contextmenu", function (e) {
    stop(e);
    openMenu();
  });
  chipEl.addEventListener("pointerdown", function (e) {
    if (e.pointerType === "mouse" && e.button !== 0) return;
    pressTimer = setTimeout(function () {
      pressTimer = null;
      openMenu();
    }, 520);
  });
  ["pointerup", "pointerleave", "pointercancel"].forEach(function (name) {
    chipEl.addEventListener(name, function () {
      if (pressTimer) clearTimeout(pressTimer);
      pressTimer = null;
    });
  });
}

export function buildOutputStubs(trip, opts) {
  opts = opts || {};
  if (!shouldInsertOutputStubs(trip)) return null;
  var view = outputChips(trip);
  var row = el("div", "v2-shelf__stubs");
  view.chips.forEach(function (chip) {
    var chipEl = el("span", "v2-shelf__stub-chip");
    chipEl.setAttribute("role", "button");
    chipEl.tabIndex = 0;
    chipEl.textContent = chip.text;
    chipEl.title = chip.title;
    chipEl.setAttribute("aria-label", chip.ariaLabel);
    if (chip.state === "outdated") {
      chipEl.classList.add("v2-shelf__stub-chip--outdated");
      chipEl.appendChild(el("span", "v2-shelf__stub-dot"));
    }
    bindActivate(chipEl, function () {
      trackStudioEvent("output_chip_click", {
        trip_id: trip.tripId,
        state: chip.state,
      });
      revealChip(trip, chip, opts.onRevealFail);
    });
    if (chip.state === "outdated") {
      bindOutdatedMenu(chipEl, trip, chip, opts.onRevealFail);
    }
    row.appendChild(chipEl);
  });
  if (view.overflow > 0) {
    var more = el("span", "v2-shelf__stub-chip v2-shelf__stub-chip--more", "+" + view.overflow);
    more.setAttribute("role", "button");
    more.tabIndex = 0;
    more.setAttribute("aria-label", overflowAriaLabel(view.overflow));
    bindActivate(more, function () {
      openManageOutputs(trip);
    });
    row.appendChild(more);
  }
  row.addEventListener("click", stop);
  row.addEventListener("pointerdown", stop);
  return row;
}

function fetchOutputs(tripId) {
  return getJson("/__travelogue/trips/" + encodeURIComponent(tripId) + "/outputs").then(function (res) {
    if (res.status !== 200 || !res.body || !res.body.ok) return [];
    return Array.isArray(res.body.outputs) ? res.body.outputs : [];
  });
}

function deleteOutput(tripId, outputId) {
  return fetch(
    "/__travelogue/trips/" + encodeURIComponent(tripId) + "/outputs/" + encodeURIComponent(outputId),
    { method: "DELETE", headers: studioAuthHeaders() }
  ).then(function (r) {
    if (r.status === 200 || r.status === 204) return { ok: true };
    return r.json().catch(function () { return {}; }).then(function (body) {
      var err = new Error((body && body.message) || "无法删除这份成品");
      err.status = r.status;
      throw err;
    });
  });
}

function renderSheetBody(host, trip, outputs, onClose) {
  host.innerHTML = "";
  var rows = manageRows(outputs);
  if (!rows.length) {
    host.appendChild(el("p", "v2-shelf-outputs__empty", "还没有成品"));
    return;
  }
  rows.forEach(function (item) {
    var row = el("div", "v2-shelf-outputs__row");
    var main = el("div");
    main.appendChild(el("p", "v2-shelf-outputs__title", item.label));
    main.appendChild(el("p", "v2-shelf-outputs__sub", item.sub));
    var acts = el("div", "v2-shelf-outputs__acts");
    var revealBtn = el("button", null, "在文件夹中显示");
    revealBtn.type = "button";
    revealBtn.addEventListener("click", function () {
      revealChip(trip, item, function () {
        fetchOutputs(trip.tripId).then(function (next) {
          renderSheetBody(host, trip, next, onClose);
        });
      });
    });
    var redoBtn = el("button", null, "重新导出");
    redoBtn.type = "button";
    redoBtn.addEventListener("click", function () {
      onClose();
      reexport(trip, item);
    });
    var delBtn = el("button", "is-danger", "删除这份成品");
    delBtn.type = "button";
    delBtn.addEventListener("click", function () {
      var body = deleteConfirmCopy(trip.title || trip.tripId, item.label);
      var run = function () {
        deleteOutput(trip.tripId, item.outputId).then(function () {
          toast("已删除这份成品", { duration: 2400 });
          return fetchOutputs(trip.tripId).then(function (next) {
            if (typeof onClose.refreshTrip === "function") onClose.refreshTrip();
            if (!next.length) {
              onClose();
              return;
            }
            renderSheetBody(host, trip, next, onClose);
          });
        }).catch(function (err) {
          toast((err && err.message) || "无法删除这份成品", { duration: 3200 });
        });
      };
      if (typeof studioModal === "function") {
        studioModal({
          title: "删除这份成品？",
          body: body,
          confirmText: "删除这份成品",
          cancelText: "取消",
          danger: true,
          focusCancel: true,
        }).then(function (ok) {
          if (ok) run();
        });
        return;
      }
      if (window.confirm(body)) run();
    });
    acts.appendChild(revealBtn);
    acts.appendChild(redoBtn);
    acts.appendChild(delBtn);
    main.appendChild(acts);
    row.appendChild(main);
    row.appendChild(el("span", "v2-shelf-outputs__state" + (item.state === "outdated" ? " is-out" : ""), item.stateLabel));
    host.appendChild(row);
  });
}

export function openManageOutputs(trip, opts) {
  opts = opts || {};
  if (!trip || !trip.tripId) return;
  closeFly();
  closeSheet();
  var backdrop = el("div", "v2-shelf-outputs");
  backdrop.setAttribute("role", "dialog");
  backdrop.setAttribute("aria-modal", "true");
  var sheet = el("div", "v2-shelf-outputs__sheet");
  var head = el("div", "v2-shelf-outputs__head");
  head.appendChild(el("h3", null, "管理成品"));
  head.appendChild(el("span", null, "《" + (trip.title || trip.tripId) + "》"));
  var closeBtn = el("button", "v2-shelf-outputs__close", "关闭");
  closeBtn.type = "button";
  var body = el("div", "v2-shelf-outputs__body");
  body.appendChild(el("p", "v2-shelf-outputs__empty", "正在读取…"));
  sheet.appendChild(head);
  sheet.appendChild(closeBtn);
  sheet.appendChild(body);
  backdrop.appendChild(sheet);
  document.body.appendChild(backdrop);
  _sheet = backdrop;
  var closer = function () {
    closeSheet();
  };
  closer.refreshTrip = opts.onChanged;
  closeBtn.addEventListener("click", closer);
  backdrop.addEventListener("click", function (e) {
    if (e.target === backdrop) closer();
  });
  fetchOutputs(trip.tripId).then(function (outputs) {
    renderSheetBody(body, trip, outputs, closer);
  }).catch(function () {
    body.innerHTML = "";
    body.appendChild(el("p", "v2-shelf-outputs__empty", "读不到成品列表，请稍后重试"));
  });
}

export { allowReadyBadge, hasManageOutputs };
