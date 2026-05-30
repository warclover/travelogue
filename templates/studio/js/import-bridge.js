/**
 * Travelogue Studio · late-bound import actions (sheet/render → import-flow without cycle).
 */

var _startImport = null;
var _requestNativeFolder = null;

export function registerImportHandlers(handlers) {
  handlers = handlers || {};
  if (typeof handlers.startImport === "function") _startImport = handlers.startImport;
  if (typeof handlers.requestNativeFolder === "function") {
    _requestNativeFolder = handlers.requestNativeFolder;
  }
}

export function startImport(body) {
  if (!_startImport) throw new Error("Studio import handlers not registered");
  return _startImport(body);
}

export function requestNativeFolder(titleVal, placeVal, options) {
  if (!_requestNativeFolder) throw new Error("Studio import handlers not registered");
  return _requestNativeFolder(titleVal, placeVal, options);
}
