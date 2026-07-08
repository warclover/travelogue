# Preview toolbar modules (M-C5 Phase 2)

Physical ESM split from `preview-toolbar.js` (entry URL unchanged).

| Module | Domain |
|--------|--------|
| `dock.js` | Icon dock, screenplay control, tooltips, scroll fade |
| `share.js` | `?share=1` minimal toolbar |
| `inline-edit.js` | Cover title inline edit (AC-ARC-14b) |
| `longshot.js` | Longshot export, stale hint, zip export, job poll (AC-ARC-14c) |
| `shell.js` | Shared chrome: toast, collapse, toolbar height, trip path helpers |

Sheet/drawers and `initToolbarV3` remain in `../preview-toolbar.js` until the next split batch.
