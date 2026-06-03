/**
 * 首页 v2 · 书架 TripCardMenu（M13 · hover ⋯ + 删除确认）。
 */
import { isDemoTrip } from "../js/constants.js";
import { trackStudioEvent } from "../js/analytics.js";
import { V2 } from "./store.js";
import { deleteTrip } from "./trips-client.js";
import { runShelfLongshot } from "./shelf-longshot.js";

var _openMenuEl = null;
var _docBound = false;

function toast(msg, opts) {
  if (typeof studioToast === "function") studioToast(msg, opts);
}

function closeMenu(menuEl) {
  if (!menuEl) return;
  menuEl.dataset.open = "false";
  menuEl.hidden = true;
  var btn = menuEl.parentElement && menuEl.parentElement.querySelector(".v2-shelf__menu-btn");
  if (btn) {
    btn.classList.remove("is-active");
    btn.setAttribute("aria-expanded", "false");
  }
  var card = menuEl.closest(".v2-shelf__card, .v2-shelf__resume");
  if (card) card.classList.remove("is-menu-open");
  if (_openMenuEl === menuEl) _openMenuEl = null;
}

export function closeAllShelfMenus() {
  if (_openMenuEl) closeMenu(_openMenuEl);
}

function bindDocDismiss() {
  if (_docBound) return;
  _docBound = true;
  document.addEventListener("click", function (e) {
    if (!_openMenuEl) return;
    if (e.target.closest(".v2-shelf__menu-btn") || e.target.closest(".v2-shelf__menu")) return;
    closeMenu(_openMenuEl);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && _openMenuEl) closeMenu(_openMenuEl);
  });
}

function openMenu(menuEl, menuBtn) {
  if (_openMenuEl && _openMenuEl !== menuEl) closeMenu(_openMenuEl);
  _openMenuEl = menuEl;
  menuEl.dataset.open = "true";
  menuEl.hidden = false;
  menuBtn.classList.add("is-active");
  menuBtn.setAttribute("aria-expanded", "true");
  var card = menuEl.closest(".v2-shelf__card, .v2-shelf__resume");
  if (card) card.classList.add("is-menu-open");
}

function confirmDelete(trip, surface, onSuccess) {
  var title = trip.title || trip.tripId;
  var body =
    "将移除画册「" + title + "」及其排版与预览记录。" +
    "你电脑上的原始照片不会被删除，之后可以用同一文件夹重新导入。";

  var runDelete = function () {
    trackStudioEvent("shelf_delete_confirm", { trip_id: trip.tripId, surface: surface });
    return deleteTrip(trip.tripId).then(function () {
      trackStudioEvent("shelf_delete_success", {
        trip_id: trip.tripId,
        surface: surface,
        remaining_count: Math.max(0, (V2.tripsTotal || 1) - 1),
      });
      toast("已删除「" + title + "」", { duration: 3000 });
      if (typeof onSuccess === "function") onSuccess(trip);
      if (typeof V2.reroute === "function") V2.reroute();
    }).catch(function (err) {
      var msg = (err && err.message) ? err.message : "删除失败，请重试";
      if (err && err.status === 401) msg = "未授权，请刷新页面后重试";
      toast(msg, { duration: 3200 });
    });
  };

  if (typeof studioModal !== "function") {
    if (window.confirm("删除这本画册？\n\n" + body)) runDelete();
    return;
  }

  studioModal({
    title: "删除这本画册？",
    body: body,
    confirmText: "删除",
    cancelText: "取消",
    danger: true,
    focusCancel: true,
  }).then(function (ok) {
    if (!ok) {
      trackStudioEvent("shelf_delete_cancel", { trip_id: trip.tripId, surface: surface });
      return;
    }
    runDelete();
  });
}

/**
 * 在封面容器上挂载 ⋯ 菜单。
 * @param {HTMLElement} coverWrap
 * @param {object} trip
 * @param {{ surface: string, onDeleted?: function }} opts
 */
export function attachShelfTripMenu(coverWrap, trip, opts) {
  opts = opts || {};
  var surface = opts.surface || "grid";
  var demo = isDemoTrip(trip);

  var menuBtn = document.createElement("button");
  menuBtn.type = "button";
  menuBtn.className = "v2-shelf__menu-btn";
  menuBtn.setAttribute("aria-label", "更多操作");
  menuBtn.setAttribute("aria-haspopup", "menu");
  menuBtn.setAttribute("aria-expanded", "false");
  menuBtn.textContent = "⋯";

  var menu = document.createElement("div");
  menu.className = "v2-shelf__menu";
  menu.setAttribute("role", "menu");
  menu.dataset.open = "false";
  menu.hidden = true;

  var longshotItem = document.createElement("button");
  longshotItem.type = "button";
  longshotItem.className = "v2-shelf__menu-item";
  longshotItem.setAttribute("role", "menuitem");
  longshotItem.textContent = "保存长图";

  var deleteItem = document.createElement("button");
  deleteItem.type = "button";
  deleteItem.className = "v2-shelf__menu-item v2-shelf__menu-item--danger";
  deleteItem.setAttribute("role", "menuitem");
  deleteItem.textContent = "删除画册";
  if (demo) {
    deleteItem.disabled = true;
    deleteItem.title = "示例画册无法删除";
  }

  menu.appendChild(longshotItem);
  menu.appendChild(deleteItem);
  coverWrap.appendChild(menuBtn);
  coverWrap.appendChild(menu);

  menuBtn.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (menu.dataset.open === "true") {
      closeMenu(menu);
      return;
    }
    trackStudioEvent("shelf_menu_open", { trip_id: trip.tripId, surface: surface });
    openMenu(menu, menuBtn);
  });

  longshotItem.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    closeMenu(menu);
    runShelfLongshot(trip, { surface: surface });
  });

  deleteItem.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (deleteItem.disabled) return;
    closeMenu(menu);
    confirmDelete(trip, surface, opts.onDeleted);
  });

  bindDocDismiss();
}
