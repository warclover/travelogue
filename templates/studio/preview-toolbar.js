/**
 * Travelogue Studio · preview page toolbar (ESM).
 */
"use strict";

import { initToolbarV3 } from "./preview-toolbar/init-v3.js";
import {
  registerBootstrapBridge,
  bootstrapPreviewToolbarWhenReady,
} from "./preview-toolbar/bootstrap.js";

registerBootstrapBridge({ initToolbarV3: initToolbarV3 });
bootstrapPreviewToolbarWhenReady();
