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
  var _patchQueued = false;

  function syncSeg(select) {
    if (!select || !select.id) return;
    var group = document.querySelector('[data-seg-for="' + select.id + '"]');
    if (!group) return;
    var val = select.value;
    Array.prototype.forEach.call(group.querySelectorAll(".v2-settings-seg__btn"), function (btn) {
      btn.classList.toggle("is-on", btn.getAttribute("data-value") === val);
    });
  }

  function applyConfig(data) {
    if (!data || data.ok === false) return;
    if (data.clustering && data.clustering.enabled) {
      cluSelect.value = data.clustering.enabled;
      syncSeg(cluSelect);
    }
    if (data.vision && data.vision.enabled) {
      visSelect.value = data.vision.enabled;
      syncSeg(visSelect);
    }
    if (g1Select && data.studio && typeof data.studio.g1ConfirmStructure === "boolean") {
      g1Select.value = data.studio.g1ConfirmStructure ? "true" : "false";
      syncSeg(g1Select);
    }
    if (layoutScoringSelect && data.layout && data.layout.scoring) {
      layoutScoringSelect.value = data.layout.scoring.enabled ? "true" : "false";
      syncSeg(layoutScoringSelect);
    }
    var meta = document.getElementById("v2-settings-meta-import");
    if (meta) {
      var cluLabel =
        cluSelect.value === "true" ? "开" : cluSelect.value === "false" ? "关" : "自动";
      var visLabel =
        visSelect.value === "true" ? "开" : visSelect.value === "auto" ? "自动" : "关";
      meta.textContent = "行程·" + cluLabel + " · 场景·" + visLabel;
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
    if (_patchPending) {
      _patchQueued = true;
      return;
    }
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
      .finally(function () {
        _patchPending = false;
        if (_patchQueued) {
          _patchQueued = false;
          patchConfig();
        }
      });
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
