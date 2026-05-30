/**
 * Travelogue Studio · state transitions without importing render (breaks ESM cycles).
 */
import { S } from "./state.js";

var _render = null;
var _leaveSuccess = null;

export function registerRender(fn) {
  _render = fn;
}

export function registerLeaveSuccessHandler(fn) {
  _leaveSuccess = fn;
}

export function transitionTo(state) {
  if (S.currentState === "Success" && state !== "Success" && _leaveSuccess) {
    _leaveSuccess();
  }
  S.currentState = state;
  if (_render) _render();
}

export function renderNow() {
  if (_render) _render();
}
