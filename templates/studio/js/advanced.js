/**
 * Travelogue Studio · advanced analysis options (Phase 3 M12-7).
 */
import { $, studioAuthHeaders } from "./dom.js";

/**
 * Bind GET/PATCH /__travelogue/config to clustering/vision/g1/layout selects.
 * @returns {{ fetchConfig: function(): Promise<void> } | null}
 */
export function bindAdvancedConfigControls() {
  var cluSelect = $("studio-cfg-clustering");
  var visSelect = $("studio-cfg-vision");
  var g1Select = $("studio-cfg-g1");
  var layoutScoringSelect = $("studio-cfg-layout-scoring");
  if (!cluSelect || !visSelect) return null;

  var _patchPending = false;

  function applyConfig(data) {
    if (!data || data.ok === false) return;
    if (data.clustering && data.clustering.enabled) {
      cluSelect.value = data.clustering.enabled;
    }
    if (data.vision && data.vision.enabled) {
      visSelect.value = data.vision.enabled;
    }
    if (g1Select && data.studio && typeof data.studio.g1ConfirmStructure === "boolean") {
      g1Select.value = data.studio.g1ConfirmStructure ? "true" : "false";
    }
    if (layoutScoringSelect && data.layout && data.layout.scoring) {
      layoutScoringSelect.value = data.layout.scoring.enabled ? "true" : "false";
    }
  }

  function fetchConfig() {
    return fetch("/__travelogue/config")
      .then(function (r) { return r.json(); })
      .then(applyConfig)
      .catch(function () { /* silent — defaults in HTML */ });
  }

  var details = $("studio-advanced-options");
  if (details) {
    details.addEventListener("toggle", function () {
      if (details.open) fetchConfig();
    });
  }

  function patchConfig() {
    if (_patchPending) return;
    _patchPending = true;
    fetch("/__travelogue/config", {
      method: "PATCH",
      headers: studioAuthHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify((function () {
        var body = {
          clustering: { enabled: cluSelect.value },
          vision: { enabled: visSelect.value },
        };
        if (g1Select) {
          body.studio = { g1ConfirmStructure: g1Select.value === "true" };
        }
        if (layoutScoringSelect) {
          body.layout = { scoring: { enabled: layoutScoringSelect.value === "true" } };
        }
        return body;
      })()),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        applyConfig(data);
        if (typeof studioToast === "function") {
          studioToast("分析选项已保存", { duration: 2000 });
        }
      })
      .catch(function () {
        if (typeof studioToast === "function") {
          studioToast("保存失败，请重试", { duration: 2500 });
        }
      })
      .finally(function () { _patchPending = false; });
  }

  cluSelect.addEventListener("change", patchConfig);
  visSelect.addEventListener("change", patchConfig);
  if (g1Select) g1Select.addEventListener("change", patchConfig);
  if (layoutScoringSelect) layoutScoringSelect.addEventListener("change", patchConfig);

  return { fetchConfig: fetchConfig };
}

export function initAdvancedOptions() {
  bindAdvancedConfigControls();
}
