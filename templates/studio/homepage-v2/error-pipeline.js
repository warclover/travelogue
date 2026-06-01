/**
 * 首页 v2 · JS error 管道（M20-i · TELEMETRY §3）。
 *
 * window.error + unhandledrejection → js_error 事件（分 variant）。
 * §17.2 回滚判据「JS error rate ↑>2×」的数据来源。
 * 节流：单页最多 MAX 条，避免错误风暴打爆 jsonl。
 */
import { trackStudioEvent } from "../js/analytics.js";

const MAX_ERRORS_PER_SESSION = 10;
let _sent = 0;

function report(kind, message, source, line) {
  if (_sent >= MAX_ERRORS_PER_SESSION) return;
  _sent += 1;
  trackStudioEvent("js_error", {
    variant: "v2",
    kind: kind,
    // 截断：仅诊断用，避免 PII / 超长
    message: String(message || "").slice(0, 300),
    source: String(source || "").slice(0, 200),
    line: typeof line === "number" ? line : null,
  });
}

export function initErrorPipeline() {
  window.addEventListener("error", function (e) {
    var msg = e && e.message ? e.message : (e && e.error ? String(e.error) : "error");
    var src = e && e.filename ? e.filename : "";
    report("error", msg, src, e && e.lineno);
  });
  window.addEventListener("unhandledrejection", function (e) {
    var reason = e && e.reason;
    var msg = reason && reason.message ? reason.message : String(reason || "rejection");
    report("unhandledrejection", msg, "", null);
  });
}
