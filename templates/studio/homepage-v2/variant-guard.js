/**
 * 首页 v2 · Import 进行中禁止切换 variant（FEATURE-FLAG §2 #1 · AC-HP2-23）。
 *
 * activeJobId 非空或 V2.state === Importing 时：
 *  - 隐藏「经典首页 → /classic」链
 *  - 拦截点击并 toast（防止误切 legacy 首页）
 */
import { V2, $, show, isLoopback, readActiveJobId } from "./store.js";

export function isVariantSwitchLocked() {
  return V2.state === "Importing" || !!readActiveJobId();
}

export function syncVariantGuard() {
  var classic = $("v2-classic-link");
  if (!classic) return;
  var locked = isVariantSwitchLocked();
  if (locked) {
    show(classic, false);
    classic.setAttribute("aria-disabled", "true");
    classic.setAttribute("tabindex", "-1");
    return;
  }
  classic.removeAttribute("aria-disabled");
  classic.removeAttribute("tabindex");
  if (isLoopback()) show(classic, true);
}

export function initVariantGuard() {
  syncVariantGuard();
  var classic = $("v2-classic-link");
  if (!classic || classic._v2GuardWired) return;
  classic._v2GuardWired = true;
  classic.addEventListener("click", function (e) {
    if (!isVariantSwitchLocked()) return;
    e.preventDefault();
    if (typeof studioToast === "function") {
      studioToast("正在制作中，请稍候再切换首页", { duration: 2400 });
    }
  });
}
