# Preview toolbar modules (M-C5 Phase 2)

Physical ESM split from `preview-toolbar.js` (entry URL unchanged).

| Module | Domain |
|--------|--------|
| `dock.js` | Icon dock, screenplay control, tooltips, scroll fade |
| `share.js` | `?share=1` minimal toolbar |
| `inline-edit.js` | Cover title inline edit (AC-ARC-14b) |
| `longshot.js` | Longshot export, stale hint, zip export, job poll (AC-ARC-14c) |
| `shell.js` | Shared chrome: toast, collapse, toolbar height, trip path helpers |
| `drawers.js` | Overlay drawers: edit, structure, cohort (G1) |
| `core.js` | Layout pending state, sheet dirty tracking, rerender/narrate jobs |
| `bootstrap.js` | v4 shell mount, share short-circuit, DOM ready wiring |
| `features.js` | Template/cover/featured/reader-mode preview UX |

`initToolbarV3` remains in `../preview-toolbar.js`. Bootstrap (`bootstrap.js`) mounts v4 shell and wires DOM ready. Type-check: `npx tsc -p preview-toolbar/jsconfig.json`.
