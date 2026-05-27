"""Windows IFileOpenDialog folder picker (M11-1)."""

from __future__ import annotations

import sys
from pathlib import Path

FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
FOS_PATHMUSTEXIST = 0x00000800
SIGDN_FILESYSPATH = 0x80058000


def pick_folder(*, title: str = "选择照片文件夹") -> Path | None:
    if sys.platform != "win32":
        return None
    try:
        return _pick_folder_ifiledialog(title)
    except Exception:
        return None


def _pick_folder_ifiledialog(title: str) -> Path | None:
    import comtypes
    from comtypes import GUID
    from comtypes.client import CreateObject

    comtypes.CoInitialize()
    try:
        dialog = CreateObject(
            GUID("{DC1C5A9C-E88A-4dde-B5A1-60F82A20AEF7}"),
            interface=GUID("{D57C7288-D4AD-4768-BE02-9D96953223E0}"),
        )
        dialog.SetOptions(FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM | FOS_PATHMUSTEXIST)
        dialog.SetTitle(title)
        if dialog.Show(None):
            return None
        item = dialog.GetResult()
        path = item.GetDisplayName(SIGDN_FILESYSPATH)
        if not path:
            return None
        return Path(str(path))
    finally:
        comtypes.CoUninitialize()
