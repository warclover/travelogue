/**
 * NAS · AI 产品面门控（FE-NAS-00 / QFX D-QFX-03）
 * 仅读服务端 GET /__travelogue/config 的 aiSurfaceEnabled；不导出写 setter。
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
import { studioAuthHeaders } from "./http.js";

var _enabled = false;
var _hydratePromise = null;
var _gateTracked = false;

export function isAiSurfaceEnabled() {
  return !!_enabled;
}

function _applyAiSurfaceFromConfig(cfg) {
  if (cfg && typeof cfg.aiSurfaceEnabled === "boolean") {
    _enabled = !!cfg.aiSurfaceEnabled;
  }
  return isAiSurfaceEnabled();
}

function trackAiSurfaceGateOnce() {
  if (_gateTracked) return;
  _gateTracked = true;
  try {
    trackStudioEvent("ai_surface_gate", { enabled: isAiSurfaceEnabled() });
  } catch (_e) {
    /* ignore */
  }
}

/**
 * 幂等：全站共享一次 config 拉取（默认 false，异步后按服务端翻转）。
 * 失败不钉死 false、不误报 gate；允许后续重试。
 */
export function ensureAiSurfaceHydrated(opts) {
  opts = opts || {};
  if (_hydratePromise) return _hydratePromise;
  _hydratePromise = fetch("/__travelogue/config", {
    headers: studioAuthHeaders({}),
  })
    .then(function (r) {
      return r && r.ok ? r.json() : null;
    })
    .then(function (cfg) {
      if (!cfg || typeof cfg.aiSurfaceEnabled !== "boolean") {
        _hydratePromise = null;
        return isAiSurfaceEnabled();
      }
      _applyAiSurfaceFromConfig(cfg);
      trackAiSurfaceGateOnce();
      return isAiSurfaceEnabled();
    })
    .catch(function () {
      _hydratePromise = null;
      return isAiSurfaceEnabled();
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
