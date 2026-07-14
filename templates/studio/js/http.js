/**
 * Travelogue Studio · shared JSON HTTP helpers (P5-A4).
 * Used by Studio ESM modules (homepage, preview toolbar).
 */

export function studioAuthHeaders(extra) {
  var headers = extra || {};
  var meta = document.querySelector('meta[name="studio-token"]');
  var token = meta && meta.getAttribute("content");
  if (token) headers["X-Studio-Token"] = token;
  return headers;
}

function parseJsonResponse(resp) {
  return resp.json().then(function (body) {
    return { status: resp.status, body: body, data: body };
  });
}

export function postJson(url, payload) {
  return fetch(url, {
    method: "POST",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload || {}),
  }).then(parseJsonResponse);
}

export function getJson(url) {
  return fetch(url, {
    method: "GET",
    headers: studioAuthHeaders({ Accept: "application/json" }),
  }).then(parseJsonResponse);
}

export function patchJson(url, payload) {
  return fetch(url, {
    method: "PATCH",
    headers: studioAuthHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload || {}),
  }).then(parseJsonResponse);
}

export function isJobBusyResponse(result) {
  if (!result || result.status !== 409) return false;
  var data = result.data || result.body || {};
  return data.error === "E_STUDIO_JOB_BUSY";
}

export function isTripConflictResponse(result) {
  if (!result || result.status !== 409) return false;
  var data = result.data || result.body || {};
  return data.error === "E_TRIP_CONFLICT";
}

/** DIFF-01 · auto-retry once on optimistic lock conflict, then toast. */
export function withTripConflictRetry(runRequest, options) {
  options = options || {};
  var retried = false;
  function notifyConflict() {
    if (typeof options.onConflict === "function") {
      options.onConflict();
      return;
    }
    if (typeof studioToast === "function") {
      studioToast("内容已被其他操作更新，请刷新", { duration: 4000 });
    }
  }
  return runRequest().then(function (result) {
    if (!isTripConflictResponse(result)) return result;
    if (retried) {
      notifyConflict();
      return result;
    }
    retried = true;
    return runRequest();
  });
}

export function patchJsonConflictRetry(url, payload, options) {
  return withTripConflictRetry(function () { return patchJson(url, payload); }, options);
}

export function postJsonConflictRetry(url, payload, options) {
  return withTripConflictRetry(function () { return postJson(url, payload); }, options);
}

/** P5-1.4 · toast + auto-retry when import/longshot hits E_STUDIO_JOB_BUSY (409). */
export function withJobBusyRetry(runRequest, options) {
  options = options || {};
  var maxAttempts = options.maxAttempts || 4;
  var delayMs = options.delayMs || 2000;
  var attempt = 0;
  function notifyBusy() {
    if (typeof options.onBusy === "function") {
      options.onBusy();
      return;
    }
    if (typeof studioToast === "function") {
      studioToast("排队中，请稍候…", { duration: Math.min(delayMs + 500, 3500) });
    }
  }
  function tryOnce() {
    return runRequest().then(function (result) {
      if (!isJobBusyResponse(result)) return result;
      if (attempt >= maxAttempts - 1) return result;
      attempt += 1;
      notifyBusy();
      return new Promise(function (resolve) {
        setTimeout(function () { resolve(tryOnce()); }, delayMs);
      });
    });
  }
  return tryOnce();
}

export function postJsonBusyRetry(url, payload, options) {
  return withJobBusyRetry(function () { return postJson(url, payload); }, options);
}
