from __future__ import annotations

import traceback

from pathlib import Path
from typing import TYPE_CHECKING, cast

from loggerplus import RobustLogger
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QFileDialog, QMenu, QMenuBar, QMessageBox

from pykotor.common.module import Module
from pykotor.extract.file import ResourceIdentifier
from pykotor.resource.formats.erf import ERFType, read_erf, write_erf
from pykotor.resource.formats.erf.erf_data import ERF
from pykotor.resource.formats.gff.gff_auto import bytes_gff, read_gff
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools import module
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_capsule_file, is_rim_file
from toolset.gui.dialogs.save.to_bif import BifSaveDialog, BifSaveOption
from toolset.gui.dialogs.save.to_module import SaveToModuleDialog
from toolset.gui.dialogs.save.to_rim import RimSaveDialog, RimSaveOption
from toolset.gui.editors.gff import GFFEditor
from utility.error_handling import format_exception_with_variables, universal_simplify_exception

if TYPE_CHECKING:
    from pathlib import PurePath

    from pykotor.resource.formats.rim.rim_data import RIM
    from toolset.gui.editor_base import Editor

class EditorSave:
    def __init__(self, editor: Editor):
        self.editor = editor

    def save_as(self):
        def show_invalid(exc: Exception | None, msg: str):
            msgBox = QMessageBox(
                QMessageBox.Icon.Critical,
                "Invalid filename/extension",
                f"Check the filename and try again. Could not save!{f'<br><br>{msg}' if msg else ''}",
                parent=None,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
            )
            if exc is not None:
                msgBox.setDetailedText(traceback.format_exc())
            msgBox.exec()

        filepath_str, _filter = QFileDialog.getSaveFileName(self.editor, "Save As", str(self.editor._filepath), self.editor._save_filter, "")
        if not filepath_str:
            return
        error_msg, exc = "", None
        try:
            identifier = ResourceIdentifier.from_path(filepath_str)
            if identifier.restype.is_invalid:
                show_invalid(None, str(identifier))
                return
        except ValueError as e:
            exc = e
            RobustLogger().exception("ValueError raised, assuming invalid filename/extension '%s'", filepath_str)
            error_msg = str(universal_simplify_exception(e)).replace("\n", "<br>")
            show_invalid(exc, error_msg)
            return

        if is_capsule_file(filepath_str) and f"Save into module ({self.editor.CAPSULE_FILTER})" in self.editor._save_filter:
            if self.editor._resname is None or self.editor._restype is None:
                self.editor._resname = "new"
                self.editor._restype = self.editor._write_supported[0]

            dialog2 = SaveToModuleDialog(self.editor._resname, self.editor._restype, self.editor._write_supported)
            if dialog2.exec():
                self.editor._resname = dialog2.resname()
                self.editor._restype = dialog2.restype()
                self.editor._filepath = Path(filepath_str)
        else:
            self.editor._filepath = Path(filepath_str)
            self.editor._resname, self.editor._restype = identifier.unpack()
        self.save()

        self.editor.refresh_window_title()
        for action in cast(QMenu, cast(QMenuBar, self.editor.menuBar()).actions()[0].menu()).actions():
            if action.text() == "Revert":
                action.setEnabled(True)

    def save(self):
        if self.editor._filepath is None:
            self.save_as()
            return

        try:
            data, data_ext = self.editor.build()
            if data is None:
                return

            if (
                self.editor._global_settings.attemptKeepOldGFFFields
                and self.editor._restype is not None
                and self.editor._restype.is_gff()
                and not isinstance(self.editor, GFFEditor)
                and self.editor._revert is not None
            ):
                old_gff = read_gff(self.editor._revert)
                new_gff = read_gff(data)
                new_gff.root.add_missing(old_gff.root)
                data = bytes_gff(new_gff)
            self.editor._revert = data

            self.editor.refresh_window_title()

            if is_bif_file(self.editor._filepath):
                self._save_ends_with_bif(data, data_ext)
            elif is_capsule_file(self.editor._filepath.parent):
                self._save_nested_capsule(data, data_ext)
            elif is_rim_file(self.editor._filepath.name):
                self._save_ends_with_rim(data, data_ext)
            elif is_any_erf_type_file(self.editor._filepath):
                self._save_ends_with_erf(data, data_ext)
            else:
                self._save_ends_with_other(data, data_ext)
        except Exception as e:  # noqa: BLE001
            self.editor.blink_window()
            RobustLogger().critical("Failed to write to file", exc_info=True)
            msg_box = QMessageBox(QMessageBox.Icon.Critical, "Failed to write to file", str(universal_simplify_exception(e)).replace("\n", "<br>"))
            msg_box.setDetailedText(format_exception_with_variables(e))
            msg_box.exec()
        else:
            self.editor.setWindowModified(False)  # Set modified to False after successful save

    def _save_ends_with_bif(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        dialog = BifSaveDialog(self.editor)
        dialog.exec()
        if dialog.option == BifSaveOption.MOD:
            str_filepath, filter = QFileDialog.getSaveFileName(self.editor, "Save As", "", ".MOD File (*.mod)", "")
            if not str(str_filepath).strip():
                return
            r_filepath = Path(str_filepath)
            dialog2 = SaveToModuleDialog(self.editor._resname, self.editor._restype, self.editor._write_supported)
            if dialog2.exec():
                self.editor._resname = dialog2.resname()
                self.editor._restype = dialog2.restype()
                self.editor._filepath = r_filepath
                self.save()
        elif dialog.option == BifSaveOption.Override:
            assert self.editor._installation is not None
            self.editor._filepath = self.editor._installation.override_path() / f"{self.editor._resname}.{self.editor._restype.extension}"
            self.save()

    def _save_ends_with_rim(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        if self.editor._global_settings.disableRIMSaving:
            dialog = RimSaveDialog(self.editor)
            dialog.exec()
            if dialog.option == RimSaveOption.MOD:
                self.editor._filepath = self.editor._filepath.parent / f"{Module.filepath_to_root(self.editor._filepath)}.mod"
                self.save()
            elif dialog.option == RimSaveOption.Override:
                assert self.editor._installation is not None
                self.editor._filepath = self.editor._installation.override_path() / f"{self.editor._resname}.{self.editor._restype.extension}"
                self.save()
            return

        rim: RIM = read_rim(self.editor._filepath)

        if self.editor._restype is ResourceType.MDL:
            rim.set_data(self.editor._resname, ResourceType.MDX, data_ext)

        rim.set_data(self.editor._resname, self.editor._restype, data)

        write_rim(rim, self.editor._filepath)
        self.editor.sig_saved_file.emit(str(self.editor._filepath), self.editor._resname, self.editor._restype, bytes(data))

        if self.editor._installation is not None:
            self.editor._installation.reload_module(self.editor._filepath.name)

    def _save_nested_capsule(
        self,
        data: bytes | bytearray,
        data_ext: bytes,
    ):
        nested_paths: list[PurePath] = []
        if is_any_erf_type_file(self.editor._filepath) or is_rim_file(self.editor._filepath):
            nested_paths.append(self.editor._filepath)

        r_parent_filepath: Path = self.editor._filepath.parent
        while (
            (
                ResourceType.from_extension(r_parent_filepath.suffix).name
                in (
                    ResourceType.ERF,
                    ResourceType.MOD,
                    ResourceType.SAV,
                    ResourceType.RIM,
                )
            )
            and not r_parent_filepath.exists()
            and not r_parent_filepath.is_dir()
        ):
            nested_paths.append(r_parent_filepath)
            self.editor._filepath = r_parent_filepath
            r_parent_filepath = self.editor._filepath.parent

        erf_or_rim: ERF | RIM = read_rim(self.editor._filepath) if ResourceType.from_extension(r_parent_filepath.suffix) is ResourceType.RIM else read_erf(self.editor._filepath)
        nested_capsules: list[tuple[PurePath, ERF | RIM]] = [
            (
                self.editor._filepath,
                erf_or_rim,
            )
        ]
        for capsule_path in reversed(nested_paths[:-1]):
            nested_erf_or_rim_data: bytes | None = erf_or_rim.get(
                capsule_path.stem,
                ResourceType.from_extension(capsule_path.suffix),
            )
            if nested_erf_or_rim_data is None:
                msg: str = f"You must save the ERFEditor for '{capsule_path.relative_to(r_parent_filepath)}' to before modifying its nested resources. Do so and try again."
                raise ValueError(msg)

            erf_or_rim = read_rim(nested_erf_or_rim_data) if ResourceType.from_extension(capsule_path.suffix) is ResourceType.RIM else read_erf(nested_erf_or_rim_data)
            nested_capsules.append((capsule_path, erf_or_rim))

        this_erf_or_rim = None
        for index, (_capsule_path, this_erf_or_rim) in enumerate(reversed(nested_capsules)):
            if index == 0:
                if not self.editor._is_capsule_editor:
                    this_erf_or_rim.set_data(self.editor._resname, self.editor._restype, bytes(data))
                continue
            child_index: int = len(nested_capsules) - index
            child_capsule_path, child_erf_or_rim = nested_capsules[child_index]
            if self.editor._filepath != child_capsule_path or not self.editor._is_capsule_editor:
                data = bytearray()
                write_erf(child_erf_or_rim, data) if isinstance(child_erf_or_rim, ERF) else write_rim(child_erf_or_rim, data)
            this_erf_or_rim.set_data(child_capsule_path.stem, ResourceType.from_extension(child_capsule_path.suffix), bytes(data))

        assert this_erf_or_rim is not None, "this_erf_or_rim is None somehow? This should be impossible."
        write_erf(this_erf_or_rim, self.editor._filepath) if isinstance(this_erf_or_rim, ERF) else write_rim(this_erf_or_rim, self.editor._filepath)
        self.editor.sig_saved_file.emit(str(self.editor._filepath), self.editor._resname, self.editor._restype, bytes(data))

    def _save_ends_with_erf(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        erftype: ERFType = ERFType.from_extension(self.editor._filepath)

        if self.editor._filepath.is_file():
            erf: ERF = read_erf(self.editor._filepath)
        elif self.editor._filepath.with_suffix(".rim").is_file():
            module.rim_to_mod(self.editor._filepath)
            erf = read_erf(self.editor._filepath)
        else:
            print(f"Saving '{self.editor._resname}.{self.editor._restype}' to a blank new {erftype.name} file at '{self.editor._filepath}'")
            erf = ERF(erftype)
        erf.erf_type = erftype

        if self.editor._restype is ResourceType.MDL:
            erf.set_data(self.editor._resname, ResourceType.MDX, data_ext)

        erf.set_data(self.editor._resname, self.editor._restype, data)

        write_erf(erf, self.editor._filepath)
        self.editor.sig_saved_file.emit(str(self.editor._filepath), self.editor._resname, self.editor._restype, bytes(data))
        if self.editor._installation is not None and self.editor._filepath.parent == self.editor._installation.module_path():
            self.editor._installation.reload_module(self.editor._filepath.name)

    def _save_ends_with_other(
        self,
        data: bytes,
        data_ext: bytes,
    ):
        self.editor._filepath.write_bytes(data)
        if self.editor._restype is ResourceType.MDL:
            self.editor._filepath.with_suffix(".mdx").write_bytes(data_ext)
        self.editor.sig_saved_file.emit(str(self.editor._filepath), self.editor._resname, self.editor._restype, bytes(data))