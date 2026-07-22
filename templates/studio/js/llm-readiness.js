/**
 * PMX D2 · 单一 LLM 就绪读取（与设置面板同源 /__travelogue/llm/status）。
 * 导入主链 stub 与「能否重新生成」两维分离：本模块只表达全局能力。
 */

var _cache = null;
var _inflight = null;

/**
 * @returns {Promise<"unknown"|"unavailable"|"available">}
 */
export function loadLlmReadiness(options) {
  var force = options && options.force;
  if (!force && _cache) {
    return Promise.resolve(_cache);
  }
  if (!force && _inflight) return _inflight;
  _inflight = fetch("/__travelogue/llm/status")
    .then(function (r) {
      return r.ok ? r.json() : null;
    })
    .then(function (st) {
      var state = "unknown";
      if (st && typeof st.llmAvailable === "boolean") {
        state = st.llmAvailable ? "available" : "unavailable";
      } else if (st && st.readiness) {
        var ready = String(st.readiness);
        state = /就绪|ready|available/i.test(ready) ? "available" : "unavailable";
      }
      _cache = state;
      try {
        window.dispatchEvent(
          new CustomEvent("travelogue:llm-status", {
            detail: {
              llmAvailable: state === "available",
              readiness: state,
              raw: st,
            },
          })
        );
      } catch (_e) {}
      return state;
    })
    .catch(function () {
      return "unknown";
    })
    .then(function (state) {
      _inflight = null;
      return state;
    });
  return _inflight;
}

export function clearLlmReadinessCache() {
  _cache = null;
}
