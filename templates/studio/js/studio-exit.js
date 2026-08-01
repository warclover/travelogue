// @ts-nocheck
/**
 * Desktop Studio exit (POST /__travelogue/shutdown).
 */
"use strict";

import { postJson } from "./http.js";
import { trackStudioEvent } from "./analytics.js";

/**
 * @param {{ confirm?: boolean|(() => any), surface?: string }} [opts]
 * @returns {Promise<{ ok: boolean, cancelled?: boolean, message?: string }>}
 */
export function requestExitStudio(opts) {
  opts = opts || {};
  var confirmFn = opts.confirm;
  var proceed = Promise.resolve(true);
  if (typeof confirmFn === "function") {
    proceed = Promise.resolve(confirmFn());
  } else if (opts.confirm !== false) {
    proceed = Promise.resolve(
      window.confirm("确定退出 Travelogue Studio？未保存的浏览器标签可稍后关闭。")
    );
  }
  return proceed.then(function (ok) {
    if (!ok) return { ok: false, cancelled: true };
    trackStudioEvent("studio_exit_click", { surface: opts.surface || "unknown" });
    return postJson("/__travelogue/shutdown", {}).then(function (res) {
      if (res.status >= 200 && res.status < 300 && res.body && res.body.ok) {
        try {
          document.title = "Studio 已退出";
        } catch (_e) {
          /* ignore */
        }
        window.setTimeout(function () {
          try {
            window.close();
          } catch (_e2) {
            /* ignore */
          }
        }, 300);
        return { ok: true };
      }
      return {
        ok: false,
        message: (res.body && res.body.message) || "无法退出，请结束 TravelogueStudio 进程",
      };
    });
  });
}
