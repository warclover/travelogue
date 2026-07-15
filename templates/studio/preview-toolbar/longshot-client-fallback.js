/**
 * Client longshot fallback (M-INS-0c · ADR-018 D6 / D-INS-09).
 * Captures index-longshot.html via html2canvas in a hidden iframe, then POSTs
 * bytes to Studio so the PNG lands in the trip directory.
 */
"use strict";

import { postJson } from "../js/http.js";
import { resolveCopyDisplayFromDom } from "../js/longshot-client.js";

function blobToBase64(blob) {
  return new Promise(function (resolve, reject) {
    var reader = new FileReader();
    reader.onload = function () {
      var result = String(reader.result || "");
      var comma = result.indexOf(",");
      resolve(comma >= 0 ? result.slice(comma + 1) : result);
    };
    reader.onerror = function () {
      reject(reader.error || new Error("read failed"));
    };
    reader.readAsDataURL(blob);
  });
}

function waitForTravelogueLongshot(win, timeoutMs) {
  return new Promise(function (resolve, reject) {
    var start = Date.now();
    function tick() {
      try {
        if (win && win.TravelogueLongshot && typeof win.TravelogueLongshot.captureMainToBlob === "function") {
          resolve(win.TravelogueLongshot);
          return;
        }
      } catch (_e) {
        /* cross-origin should not happen on same origin */
      }
      if (Date.now() - start > timeoutMs) {
        reject(new Error("长图页面未就绪"));
        return;
      }
      window.setTimeout(tick, 120);
    }
    tick();
  });
}

function downloadBlobFallback(blob, filename) {
  var url = URL.createObjectURL(blob);
  var a = document.createElement("a");
  a.href = url;
  a.download = filename || "travelogue.png";
  a.rel = "noopener";
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.setTimeout(function () {
    URL.revokeObjectURL(url);
  }, 2000);
}

/**
 * @returns {Promise<{ status: string, result?: object, error?: object }>}
 *   Synthetic job-shaped object for showLongshotDrawer.
 */
export function runClientLongshotFallback(root, tripId, opts) {
  opts = opts || {};
  var platform = opts.platform || "wechat_chat";
  var prefs = opts.prefs || {};
  var scale = Number(prefs.scale) || 2;
  var format = String(prefs.format || "png").toLowerCase();
  if (format === "jpg") format = "jpeg";
  var copyDisplay = resolveCopyDisplayFromDom(document);

  var iframe = document.createElement("iframe");
  iframe.setAttribute("aria-hidden", "true");
  iframe.tabIndex = -1;
  iframe.style.cssText =
    "position:fixed;left:-10000px;top:0;width:1200px;height:2400px;opacity:0;pointer-events:none;border:0;";
  iframe.src = "/" + encodeURIComponent(tripId) + "/index-longshot.html";
  document.body.appendChild(iframe);

  return new Promise(function (resolve) {
    var settled = false;
    function finish(job) {
      if (settled) return;
      settled = true;
      try {
        iframe.remove();
      } catch (_e) {
        /* ignore */
      }
      resolve(job);
    }

    var timer = window.setTimeout(function () {
      finish({
        status: "failed",
        error: { code: "E_LNG_CAPTURE_FAILED", message: "兼容模式加载超时，请重试" },
      });
    }, 90000);

    iframe.addEventListener("load", function () {
      var win = iframe.contentWindow;
      waitForTravelogueLongshot(win, 20000)
        .then(function (api) {
          return api.captureMainToBlob({
            scale: scale,
            format: format,
            quietProgress: true,
          });
        })
        .then(function (blob) {
          if (!blob) throw new Error("empty capture");
          return blobToBase64(blob).then(function (b64) {
            return { blob: blob, b64: b64 };
          });
        })
        .then(function (payload) {
          return postJson("/__travelogue/longshot/upload", {
            tripId: tripId,
            format: format,
            scale: scale,
            platform: platform,
            copyDisplay: copyDisplay,
            captureMethod: "p2",
            data: payload.b64,
          }).then(function (res) {
            return { res: res, blob: payload.blob };
          });
        })
        .then(function (pack) {
          window.clearTimeout(timer);
          var res = pack.res;
          if (res.status >= 200 && res.status < 300 && res.body && res.body.ok) {
            finish({
              status: "succeeded",
              result: {
                tripId: tripId,
                outputs: res.body.outputs || [],
                captureMethod: "p2",
                segmented: !!res.body.segmented,
                pageCount: res.body.pageCount || 1,
                platform: res.body.platform || platform,
                publishGuide: res.body.publishGuide,
                userHint: res.body.userHint || "已使用兼容模式保存",
              },
            });
            return;
          }
          // Upload failed → browser download as last resort (D-INS-09).
          try {
            downloadBlobFallback(pack.blob, tripId + "-longshot." + (format === "jpeg" ? "jpg" : "png"));
          } catch (_e) {
            /* ignore */
          }
          finish({
            status: "failed",
            error: {
              code: "E_LNG_CAPTURE_FAILED",
              message:
                (res.body && res.body.message) ||
                "无法写回本机目录，已尝试浏览器下载",
            },
          });
        })
        .catch(function (err) {
          window.clearTimeout(timer);
          finish({
            status: "failed",
            error: {
              code: "E_LNG_CAPTURE_FAILED",
              message: (err && err.message) || "兼容模式保存失败，请重试",
            },
          });
        });
    });
  });
}
