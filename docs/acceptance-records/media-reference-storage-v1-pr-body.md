## Summary

- Optional **reference-mode** ingest (`ingest.copy_source_files`, default still copy) with `sourceRef` / `media.storageMode`, unified `resolve_source_path`, serial + parallel alignment.
- Storage usage / safe+deep cleanup / remount APIs + settings「存储与磁盘」; export Facade blocks when album missing (remount CTA).
- P1/P2: import-wizard copy, trip storageMode text, DLLM three-group note, content_changed remount UX, parallel reference test, shelf disk badge, incremental `mediaWarn` toast.

## Test plan

### Automation

```bash
python -m pytest \
  tests/unit/media/test_source_resolve_storage.py \
  tests/unit/export/test_export_no_absolute_paths.py \
  tests/unit/media/test_ingest_pending_assets.py \
  -q
```

### Dogfood gate (W2 exit · required before merge)

Checklist: [`docs/acceptance-records/media-reference-storage-v1-dogfood-checklist.md`](../acceptance-records/media-reference-storage-v1-dogfood-checklist.md)

- [ ] **1** Default copy on → import has `source/` + `sourceRef`, preview OK
- [ ] **2** Copy off → new import has no `source/*.jpg`; old trips untouched; wizard shows reference note
- [ ] **3** Safe cleanup → cache down; source/WebP remain; trip opens
- [ ] **4** Move album → export blocked → remount recovers; same-name content change does not mis-link
- [ ] **5** Export zip / HTML has no local album absolute paths

### Spot checks

- [ ] Settings「存储与磁盘」+ storageMode text
- [ ] Wizard「更改存储设置」focuses storage section
- [ ] Shelf「磁盘占用较高」only when over threshold

## Follow-up (non-blocking)

- Product Dialog instead of `window.confirm` for cleanup
- Batch remount across trips sharing albumRoot
- V1.1 storage preference onboarding (never silent default flip)
