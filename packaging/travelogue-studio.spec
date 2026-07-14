# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Travelogue Studio (Desktop Installer V1 · M-INS-0a).

Main artifact: **onedir** (not onefile). Windowed (console=False), UPX off.
See docs/adr/018-desktop-installer-layout.md and packaging/README.md.
"""

from __future__ import annotations

from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent

# --- P0 bundled resources (build fails if any missing) ---
_REQUIRED = [
    root / "templates",
    root / "schemas",
    root / "docs" / "experience-matrix.yaml",
    root / "config" / "platform_profiles.yaml",
    root / "config.yaml.example",
    root / "templates" / "studio",
    root / "templates" / "studio" / "assets" / "demo-album",
    root / "templates" / "visual-journal",
]

_missing = [str(p) for p in _REQUIRED if not p.exists()]
if _missing:
    raise SystemExit(
        "PyInstaller datas: missing required P0 resources:\n  - " + "\n  - ".join(_missing)
    )

datas = [
    (str(root / "templates"), "templates"),
    (str(root / "schemas"), "schemas"),
    (str(root / "docs" / "experience-matrix.yaml"), "docs"),
    (str(root / "config" / "platform_profiles.yaml"), "config"),
    (str(root / "config.yaml.example"), "."),
]

# Heavy / optional stacks — never ship in V1 Studio installer (F-INS-PACK-04/11).
# Also keep optional ML/vision/dev stacks out of Analysis when possible (size + false deps).
excludes = [
    "torch",
    "torchvision",
    "torchaudio",
    "open_clip",
    "open_clip_torch",
    "pyiqa",
    "tensorflow",
    "tensorboard",
    "jax",
    "jaxlib",
    # Optional runtime (lazy-imported); Gate A uses html2canvas track, not Chromium.
    "playwright",
    # Dev / analysis noise often pulled via optional imports
    "pytest",
    "_pytest",
    "IPython",
    "jupyter",
    "notebook",
]

hiddenimports = [
    "comtypes",
    "comtypes.client",
    "comtypes.gen",
    "pybars",
    "pybars._compiler",
    "yaml",
    "jsonschema",
    "travelogue.desktop.folder_dialog",
    "travelogue.desktop.demo_album",
    "travelogue.web.studio_subprocess",
]

a = Analysis(
    [str(root / "travelogue" / "desktop" / "launcher.py")],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TravelogueStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="TravelogueStudio",
)
