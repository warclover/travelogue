/**
 * Travelogue Studio · preview toolbar entry (M-P2a).
 */
"use strict";

import { initPreviewToolbar } from "./bootstrap.js";

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initPreviewToolbar);
} else {
  initPreviewToolbar();
}
