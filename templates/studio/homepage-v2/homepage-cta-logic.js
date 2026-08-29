/**
 * UX-01 · 首页状态主按钮纯逻辑（无 DOM · node --test）。
 * 最近一本按 trips 既有 updatedAt 降序取；示例不计。
 */
import { isDemoTrip } from "../js/constants.js";

export var CTA_EMPTY = "empty";
export var CTA_RESUME_MAKE = "resume_make";
export var CTA_RESUME_EXPORT = "resume_export";
export var CTA_DELIVERED = "delivered";

export function pickResumeTrip(trips) {
  var rows = trips || [];
  for (var i = 0; i < rows.length; i++) {
    var trip = rows[i];
    if (trip && trip.tripId && !isDemoTrip(trip)) return trip;
  }
  return null;
}

export function editionChip(trip) {
  return String((trip && trip.edition) || "").toLowerCase() === "portfolio"
    ? "作品集"
    : "游记";
}

export function previewHref(trip, withExportPanel) {
  if (!trip) return "";
  var base = String(trip.previewUrl || "").trim()
    || ("/" + encodeURIComponent(trip.tripId) + "/index.html");
  if (!withExportPanel) return base;
  return base + (base.indexOf("?") >= 0 ? "&" : "?") + "exportPanel=1";
}

export function resolveHomepageCta(trips) {
  var trip = pickResumeTrip(trips);
  if (!trip) {
    return {
      state: CTA_EMPTY,
      primaryLabel: "选择照片文件夹",
      primaryAria: "选择照片文件夹",
      primaryAction: "import",
      secondaryLabel: "试用示例",
      secondaryAction: "demo",
      chip: "",
      trip: null,
    };
  }
  var title = String(trip.title || trip.tripId || "画册").trim() || "画册";
  var chip = editionChip(trip);
  if (!trip.hasLongshotExport) {
    return {
      state: CTA_RESUME_MAKE,
      primaryLabel: "继续制作《" + title + "》",
      primaryAria: "继续制作《" + title + "》",
      primaryAction: "preview",
      secondaryLabel: "选择照片文件夹",
      secondaryAction: "import",
      chip: chip,
      trip: trip,
    };
  }
  if (trip.longshotStale) {
    return {
      state: CTA_RESUME_EXPORT,
      primaryLabel: "按原配方重出",
      primaryAria: "按原配方重出《" + title + "》",
      primaryAction: "reexport_recipe",
      secondaryLabel: "打开《" + title + "》",
      secondaryAction: "preview",
      chip: chip,
      trip: trip,
    };
  }
  return {
    state: CTA_DELIVERED,
    primaryLabel: "选择照片文件夹",
    primaryAria: "选择照片文件夹",
    primaryAction: "import",
    secondaryLabel: "打开《" + title + "》",
    secondaryAction: "preview",
    chip: "",
    trip: trip,
  };
}
