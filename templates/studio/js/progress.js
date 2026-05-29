/**
 * Travelogue Studio · import progress UI.
 */
import { STAGE_LABELS } from "./constants.js";
import { $, show } from "./dom.js";
import { hideFailure } from "./errors.js";

export function stageText(job) {
  var label = STAGE_LABELS[job.stage] || "处理中…";
  var idx = job.stageIndex || 0;
  var total = job.stageCount || 4;
  var hint = job.stageHint ? "（" + job.stageHint + "）" : "";
  return idx + "/" + total + " · " + label + hint;
}

export function updateProgress(job) {
  hideFailure();
  var stage = $("studio-stage");
  var line = stageText(job);
  if (job.result && job.result.intentLine && (job.stageIndex || 0) >= 2) {
    line = line + "\n" + job.result.intentLine;
  }
  if (stage) stage.textContent = line;
  var pct = Math.round(((job.stageIndex || 0) / (job.stageCount || 4)) * 100);
  var bar = $("studio-bar-fill"); if (bar) bar.style.width = pct + "%";
  var pctEl = $("studio-pct");
  if (pctEl) { pctEl.textContent = pct + "%"; show(pctEl, true); }
  show($("studio-cancel"), job.status === "running" || job.status === "queued");
}
