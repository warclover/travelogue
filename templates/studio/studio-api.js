/**
 * Travelogue Studio · classic-script bridge for shared HTTP helpers (P5-A4).
 * Loaded before preview-toolbar.js on trip preview pages.
 */
import {
  postJson,
  patchJson,
  studioAuthHeaders,
  isJobBusyResponse,
  withJobBusyRetry,
  postJsonBusyRetry,
} from "./js/http.js";

window.StudioApi = {
  postJson: postJson,
  patchJson: patchJson,
  studioAuthHeaders: studioAuthHeaders,
  isJobBusyResponse: isJobBusyResponse,
  withJobBusyRetry: withJobBusyRetry,
  postJsonBusyRetry: postJsonBusyRetry,
};
