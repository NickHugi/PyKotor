from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional, cast

from qtpy.QtWidgets import QFileDialog, QMenu, QMenuBar

from pykotor.extract.capsule import Capsule
from pykotor.extract.file import ResourceIdentifier
from pykotor.tools.misc import is_capsule_file
from toolset.gui.dialogs.load_from_module import LoadFromModuleDialog
from toolset.gui.editor.base import Editor

if TYPE_CHECKING:
    import os

    from pykotor.resource.type import ResourceType
    from toolset.gui.editor.base import Editor


class EditorFile:
    def __init__(self, editor: Editor):
        self.editor: Editor = editor

    def open(self):
        filepath_str, _filter = QFileDialog.getOpenFileName(self.editor, "Open file", "", self.editor._open_filter, "")
        if not str(filepath_str).strip():
            return
        r_filepath = Path(filepath_str)

        if is_capsule_file(r_filepath) and f"Load from module ({self.editor.CAPSULE_FILTER})" in self.editor._open_filter:
            self._load_module_from_dialog_info(r_filepath)
        else:
            data: bytes = r_filepath.read_bytes()
            res_ident: ResourceIdentifier = ResourceIdentifier.from_path(r_filepath).validate()
            self.load(r_filepath, res_ident.resname, res_ident.restype, data)

    def _load_module_from_dialog_info(
        self,
        r_filepath: Path,
    ):
        dialog = LoadFromModuleDialog(Capsule(r_filepath), self.editor._read_supported)
        if dialog.exec():
            resname: str | None = dialog.resname()
            restype: ResourceType | None = dialog.restype()
            data: bytes | None = dialog.data()
            assert resname is not None
            assert restype is not None
            assert data is not None
            self.load(r_filepath, resname, restype, data)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        self.editor._filepath = Path(filepath)
        self.editor._resname = resref
        self.editor._restype = restype
        self.editor._revert = data
        for action in cast(QMenu, cast(QMenuBar, self.editor.menuBar()).actions()[0].menu()).actions():
            if action.text() == "Revert":
                action.setEnabled(True)
                break
        self.editor.refresh_window_title()
        self.editor.sig_loaded_file.emit(str(self.editor._filepath), self.editor._resname, self.editor._restype, data)

    def new(self):
        self.editor._revert = b""
        self.editor._filepath = self.editor.setup_extract_path() / f"{self.editor._resname}.{self.editor._restype.extension}"
        menu_bar: QMenuBar | None = cast(Optional[QMenuBar], self.editor.menuBar())
        assert menu_bar is not None, "Menu bar is None somehow? This should be impossible."
        for action in cast(QMenu, menu_bar.actions()[0].menu()).actions():
            if action.text() != "Revert":
                continue
            action.setEnabled(False)
        self.editor.refresh_window_title()
        self.editor.sig_new_file.emit()

    def revert(self):
        if self.editor._revert is None:
            print("No data to revert from")
            self.editor.blink_window()
            return
        self.load(self.editor._filepath, self.editor._resname, self.editor._restype, self.editor._revert)
