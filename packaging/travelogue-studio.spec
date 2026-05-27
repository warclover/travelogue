# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Travelogue Studio exe (M11)."""

from pathlib import Path

block_cipher = None
root = Path(SPECPATH).resolve().parent

datas = [
    (str(root / "templates"), "templates"),
    (str(root / "schemas"), "schemas"),
    (str(root / "docs" / "experience-matrix.yaml"), "docs"),
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
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="TravelogueStudio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
