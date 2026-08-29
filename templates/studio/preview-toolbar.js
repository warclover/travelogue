/**
 * LIVE · Studio preview toolbar entry.
 * Loaded by: journal.hbs / present shell.
 * Not: templates/visual-journal/longshot.js (reader capture).
 */
"use strict";

import { initToolbarV3 } from "./preview-toolbar/init-v3.js";
import {
  registerBootstrapBridge,
  bootstrapPreviewToolbarWhenReady,
} from "./preview-toolbar/bootstrap.js";

registerBootstrapBridge({ initToolbarV3: initToolbarV3 });
bootstrapPreviewToolbarWhenReady();
