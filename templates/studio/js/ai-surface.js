/**
 * NAS · AI 产品面门控（FE-NAS-00 / QFX D-QFX-09）
 * 三态：unknown | disabled | enabled；不导出写 setter。
 */
"use strict";

import { trackStudioEvent } from "./analytics.js";
import { studioAuthHeaders } from "./http.js";

var STATE_UNKNOWN = "unknown";
var STATE_DISABLED = "disabled";
var STATE_ENABLED = "enabled";
var GATE_STORAGE_KEY = "travelogue.ai_surface_gate.v1";

var _state = STATE_UNKNOWN;
var _hydratePromise = null;

export function getAiSurfaceState() {
  return _state;
}

export function isAiSurfaceEnabled() {
  return _state === STATE_ENABLED;
}

function _setState(next) {
  if (next === STATE_ENABLED || next === STATE_DISABLED || next === STATE_UNKNOWN) {
    _state = next;
  }
}

function _gateAlreadyTracked(enabled) {
  try {
    if (typeof sessionStorage === "undefined") return false;
    var raw = sessionStorage.getItem(GATE_STORAGE_KEY);
    if (!raw) return false;
    var parsed = JSON.parse(raw);
    return parsed && parsed.enabled === enabled;
  } catch (_e) {
    return false;
  }
}

function _markGateTracked(enabled) {
  try {
    if (typeof sessionStorage === "undefined") return;
    sessionStorage.setItem(
      GATE_STORAGE_KEY,
      JSON.stringify({ enabled: !!enabled })
    );
  } catch (_e) {
    /* ignore */
  }
}

function trackAiSurfaceGateOnce(enabled) {
  if (_gateAlreadyTracked(enabled)) return Promise.resolve(false);
  return Promise.resolve()
    .then(function () {
      return trackStudioEvent("ai_surface_gate", { enabled: !!enabled });
    })
    .then(function (ok) {
      if (ok) _markGateTracked(enabled);
      return !!ok;
    })
    .catch(function () {
      return false;
    });
}

/**
 * 幂等拉取 config。失败 → unknown（可重试）；成功 → enabled/disabled 并 track。
 * @returns {Promise<"unknown"|"disabled"|"enabled">}
 */
export function ensureAiSurfaceHydrated(opts) {
  opts = opts || {};
  if (_hydratePromise) return _hydratePromise;
  _hydratePromise = fetch("/__travelogue/config", {
    headers: studioAuthHeaders({}),
  })
    .then(function (r) {
      if (!r || !r.ok) {
        _hydratePromise = null;
        _setState(STATE_UNKNOWN);
        return STATE_UNKNOWN;
      }
      return r.json().then(
        function (cfg) {
          if (!cfg || typeof cfg.aiSurfaceEnabled !== "boolean") {
            _hydratePromise = null;
            _setState(STATE_UNKNOWN);
            return STATE_UNKNOWN;
          }
          var enabled = !!cfg.aiSurfaceEnabled;
          _setState(enabled ? STATE_ENABLED : STATE_DISABLED);
          return trackAiSurfaceGateOnce(enabled).then(function () {
            return _state;
          });
        },
        function () {
          _hydratePromise = null;
          _setState(STATE_UNKNOWN);
          return STATE_UNKNOWN;
        }
      );
    })
    .catch(function () {
      _hydratePromise = null;
      _setState(STATE_UNKNOWN);
      return STATE_UNKNOWN;
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
