/**
 * Travelogue Studio · shared mutable runtime state.
 * Single source of truth for cross-module state. Mutate properties on S;
 * never reassign the binding. (ESM import bindings are read-only.)
 */
export const S = {
  currentState: "Loading",
  pendingImport: null,
  activeJobId: null,
  tripsData: [],
  tripsListLimit: 20,
  tripsTotalCount: 0,
  isOffline: false,
  healthTimer: null,
  _importVisionEnabled: false,
  _pickInFlight: false,
  _importGen: 0,
  _thumbObjectUrls: [],
  _tripsLoadSeq: 0,
  _sheetOpen: false,
  _pendingAlbumPath: null,
  _sheetFocusRelease: null,
  _sheetPreviousFocus: null,
  _pipelineEstimateTiers: null,
  lastHeroSrc: "",
};
