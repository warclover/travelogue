/**
 * NAS · AI 产品面门控（FE-NAS-00）
 * 仅读服务端 GET /__travelogue/config 的 aiSurfaceEnabled；禁止假装读 process env。
 */
"use strict";

var _enabled = false;
var _hydratePromise = null;

export function isAiSurfaceEnabled() {
  return !!_enabled;
}

export function setAiSurfaceEnabled(value) {
  _enabled = !!value;
}

export function hydrateAiSurfaceFromConfig(cfg) {
  if (cfg && typeof cfg.aiSurfaceEnabled === "boolean") {
    setAiSurfaceEnabled(cfg.aiSurfaceEnabled);
  }
  return isAiSurfaceEnabled();
}

/**
 * 幂等：全站共享一次 config 拉取（默认 false，异步后翻转 dark）。
 */
export function ensureAiSurfaceHydrated(opts) {
  opts = opts || {};
  if (_hydratePromise) return _hydratePromise;
  var headers = {};
  try {
    if (typeof window !== "undefined" && window.__studioAuthHeaders) {
      headers = window.__studioAuthHeaders({}) || {};
    }
  } catch (_e) {
    /* ignore */
  }
  _hydratePromise = fetch("/__travelogue/config", { headers: headers })
    .then(function (r) {
      return r && r.ok ? r.json() : null;
    })
    .then(function (cfg) {
      hydrateAiSurfaceFromConfig(cfg || {});
      return isAiSurfaceEnabled();
    })
    .catch(function () {
      setAiSurfaceEnabled(false);
      return false;
    });
  return _hydratePromise;
}

export function whenAiSurface(fn) {
  if (typeof fn !== "function") return;
  if (isAiSurfaceEnabled()) {
    try {
      fn();
    } catch (_e) {
      /* ignore */
    }
  }
}
