"""Windows folder picker (M11-1): IFileOpenDialog with tkinter fallback."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_log = logging.getLogger(__name__)

FOS_PICKFOLDERS = 0x00000020
FOS_FORCEFILESYSTEM = 0x00000040
FOS_PATHMUSTEXIST = 0x00000800
SIGDN_FILESYSPATH = 0x80058000


def pick_folder(*, title: str = "选择照片文件夹") -> Path | None:
    if sys.platform != "win32":
        return None
    try:
        chosen = _pick_folder_ifiledialog(title)
        if chosen is not None:
            return chosen
    except Exception:
        _log.debug("IFileOpenDialog folder pick failed; using tkinter fallback", exc_info=True)
    return _pick_folder_tk(title)


def _pick_folder_tk(title: str) -> Path | None:
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        path = filedialog.askdirectory(title=title, mustexist=True)
    finally:
        root.destroy()
    if not path:
        return None
    return Path(path)


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
        hr = dialog.Show(None)
        if hr not in (0, False):
            return None
        item = dialog.GetResult()
        path = item.GetDisplayName(SIGDN_FILESYSPATH)
        if not path:
            return None
        return Path(str(path))
    finally:
        comtypes.CoUninitialize()
