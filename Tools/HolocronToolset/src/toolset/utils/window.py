from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from functools import singledispatch
from typing import cast

from loggerplus import RobustLogger  # type: ignore[import-untyped]
from qtpy.QtCore import Qt
from qtpy.QtWidgets import QApplication, QMainWindow, QMessageBox, QWidget

from pykotor.extract.file import FileResource  # type: ignore[import-not-found]
from pykotor.resource.type import ResourceType  # type: ignore[import-not-found]
from toolset.gui.common.localization import translate as tr, trf  # type: ignore[import-not-found]
from toolset.gui.widgets.settings.installations import GlobalSettings  # type: ignore[import-not-found]
from utility.error_handling import universal_simplify_exception  # type: ignore[import-not-found]

if TYPE_CHECKING:
    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QDialog, QMainWindow

    from toolset.data.installation import HTInstallation
    from toolset.gui.editor import Editor

TOOLSET_WINDOWS: list[QDialog | QMainWindow] = []
"""List of windows that are currently open."""
_UNIQUE_SENTINEL = object()


def add_window(
    window: QDialog | QMainWindow,
    *,
    show: bool = True,
):
    """Prevents Qt's garbage collection by keeping a reference to the window."""
    original_closeEvent = window.closeEvent

    def new_close_event(
        event: QCloseEvent | None = _UNIQUE_SENTINEL,  # type: ignore[assignment]  # pyright: ignore[reportArgumentType]
        *args,
        **kwargs,
    ):
        from toolset.gui.editor import Editor

        if isinstance(window, Editor) and window._filepath is not None:  # noqa: SLF001
            add_recent_file(window._filepath)  # noqa: SLF001
        if window in TOOLSET_WINDOWS:
            RobustLogger().debug(f"Removing window (normal): {window.__class__.__name__} ({window})")
            TOOLSET_WINDOWS.remove(window)
        if event is _UNIQUE_SENTINEL:  # Make event arg optional just in case the class has the wrong definition.
            RobustLogger().debug(f"Closing window (sentinel): {window.__class__.__name__} ({window})")
            original_closeEvent(*args, **kwargs)
        else:
            RobustLogger().debug(f"Closing window (event): {window.__class__.__name__} ({window})")
            original_closeEvent(event, *args, **kwargs)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

    window.closeEvent = new_close_event  # type: ignore[assignment]  # pyright: ignore[reportAttributeAccessIssue]
    RobustLogger().debug(f"Adding window (normal): {window.__class__.__name__} ({window})")
    if show:
        window.show()
    TOOLSET_WINDOWS.append(window)


def add_recent_file(file: Path):
    """Update the list of recent files."""
    settings = GlobalSettings()
    recent_files: list[str] = [str(fp) for fp in {Path(p) for p in settings.recentFiles} if fp.is_file()]
    recent_files.insert(0, str(file))
    if len(recent_files) > 15:  # noqa: PLR2004
        recent_files.pop()
    settings.recentFiles = recent_files


@singledispatch
def open_resource_editor(  # noqa: PLR0913
    resource_or_path: FileResource | os.PathLike | str,
    installation: HTInstallation | None = None,
    parent_window: QWidget | None = None,
    *,
    gff_specialized: bool | None = None,
    resname: str | None = None,
    restype: ResourceType | None = None,
    data: bytes | None = None,
) -> tuple[os.PathLike | str | None, Editor | QMainWindow | None]:
    raise NotImplementedError("Unsupported input type")

@open_resource_editor.register(FileResource)
def _(
    resource: FileResource,
    installation: HTInstallation | None = None,
    parent_window: QWidget | None = None,
    *,
    gff_specialized: bool | None = None,
    **kwargs
) -> tuple[os.PathLike | str | None, Editor | QMainWindow | None]:
    # Implementation for FileResource
    return _open_resource_editor_impl(
        resource=resource,
        installation=installation,
        parent_window=parent_window,
        gff_specialized=gff_specialized
    )

@open_resource_editor.register(str)
@open_resource_editor.register(os.PathLike)
def _(  # noqa: PLR0913
    path: os.PathLike | str,
    resname: str,
    restype: ResourceType,
    data: bytes,
    installation: HTInstallation | None = None,
    parent_window: QWidget | None = None,
    *,
    gff_specialized: bool | None = None,
) -> tuple[os.PathLike | str | None, Editor | QMainWindow | None]:
    return _open_resource_editor_impl(
        filepath=path,
        resname=resname,
        restype=restype,
        data=data,
        installation=installation,
        parent_window=parent_window,
        gff_specialized=gff_specialized
    )

def _open_resource_editor_impl(  # noqa: C901, PLR0913, PLR0912, PLR0915
    resource: FileResource | None = None,
    filepath: os.PathLike | str | None = None,
    resname: str | None = None,
    restype: ResourceType | None = None,
    data: bytes | None = None,
    installation: HTInstallation | None = None,
    parent_window: QWidget | None = None,
    gff_specialized: bool | None = None,
) -> tuple[os.PathLike | str | None, Editor | QMainWindow | None]:
    # To avoid circular imports, these need to be placed within the function
    from toolset.gui.editors.are import AREEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.bwm import BWMEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.dlg import DLGEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.erf import ERFEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.gff import GFFEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.git import GITEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.ifo import IFOEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.jrl import JRLEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.lip import LIPEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.ltr import LTREditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.mdl import MDLEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.nss import NSSEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.pth import PTHEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.ssf import SSFEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.tlk import TLKEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.tpc import TPCEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.twoda import TwoDAEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.txt import TXTEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.utc import UTCEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.utd import UTDEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.ute import UTEEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.uti import UTIEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.utm import UTMEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.utp import UTPEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.uts import UTSEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.utt import UTTEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.editors.utw import UTWEditor  # type: ignore[import-not-found] # noqa: PLC0415
    from toolset.gui.windows.audio_player import AudioPlayer  # type: ignore[import-not-found] # noqa: PLC0415

    if gff_specialized is None:
        gff_specialized = GlobalSettings().gffSpecializedEditors

    editor: Editor | None = None
    parent_window_widget: QWidget | None = parent_window if isinstance(parent_window, QWidget) else None

    if resource:
        try:
            data = resource.data()
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Exception occurred in open_selected_resource")
            QMessageBox(QMessageBox.Icon.Critical, tr("Failed to get the file data."), tr("An error occurred while attempting to read the data of the file.")).exec()
            return None, None
        restype = resource.restype()
        resname = resource.resname()
        filepath = resource.filepath()
    elif (
        resname
        and resname.strip()
        and restype
        and data is not None
        and filepath
    ):
        ...
    else:
        raise ValueError("Invalid input combination")

    if restype.target_type() is ResourceType.TwoDA:
        editor = TwoDAEditor(None, installation)
    elif restype.target_type() is ResourceType.SSF:
        editor = SSFEditor(None, installation)
    elif restype.target_type() is ResourceType.TLK:
        editor = TLKEditor(None, installation)
    elif restype.target_type() is ResourceType.LTR:
        editor = LTREditor(None, installation)
    elif restype.target_type() is ResourceType.LIP:  # Add LIP editor support
        editor = LIPEditor(None, installation)
    elif restype.category == "Walkmeshes":
        editor = BWMEditor(None, installation)
    elif (
        restype.category in {"Images", "Textures"}
        and restype is not ResourceType.TXI
    ):
        editor = TPCEditor(None, installation)
    elif restype is ResourceType.NSS:
        editor = NSSEditor(None, installation)
    elif restype is ResourceType.NCS:
        if installation is None:
            QMessageBox.warning(
                parent_window_widget,
                tr("Cannot decompile NCS without an installation active"),
                tr("Please select an installation from the dropdown before loading an NCS."),
            )
            return None, None
        editor = NSSEditor(None, installation)

    elif restype.target_type() is ResourceType.DLG:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = DLGEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTC, ResourceType.BTC, ResourceType.BIC}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTCEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTP, ResourceType.BTP}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTPEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTD, ResourceType.BTD}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTDEditor(None, installation)

    elif restype.target_type() is ResourceType.IFO:
        editor = IFOEditor(None, installation)

    elif restype.target_type() is ResourceType.UTS:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTSEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTT, ResourceType.BTT}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTTEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTM, ResourceType.BTM}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTMEditor(None, installation)

    elif restype.target_type() is ResourceType.UTW:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTWEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTE, ResourceType.BTE}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTEEditor(None, installation)

    elif restype.target_type() in {ResourceType.UTI, ResourceType.BTI}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTIEditor(None, installation)

    elif restype.target_type() is ResourceType.JRL:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = JRLEditor(None, installation)

    elif restype.target_type() is ResourceType.ARE:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = AREEditor(None, installation)

    elif restype.target_type() is ResourceType.PTH:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = PTHEditor(None, installation)

    elif restype.target_type() is ResourceType.GIT:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = GITEditor(None, installation)

    elif restype.category == "Audio":
        editor = AudioPlayer(None)
        editor.setWindowIcon(cast(QApplication, QApplication.instance()).windowIcon())

    elif restype.name in (ResourceType.ERF, ResourceType.SAV, ResourceType.MOD, ResourceType.RIM, ResourceType.BIF):
        editor = ERFEditor(None, installation)

    elif restype in {ResourceType.MDL, ResourceType.MDX}:
        editor = MDLEditor(None, installation)

    elif restype.target_type().contents == "gff":
        editor = GFFEditor(None, installation)

    elif restype.contents == "plaintext":
        editor = TXTEditor(None)

    if editor is None:
        QMessageBox(
            QMessageBox.Icon.Critical,
            tr("Failed to open file"),
            trf("The selected file format '{format}' is not yet supported.", format=str(restype)),
            QMessageBox.StandardButton.Ok,
            parent_window_widget,
            flags=Qt.WindowType.Window
            | Qt.WindowType.Dialog
            | Qt.WindowType.WindowStaysOnTopHint,  # pyright: ignore[reportArgumentType]
        ).show()
        return None, None

    try:
        editor.load(filepath, resname, restype, data)
        editor.show()
        editor.activateWindow()
        add_window(editor)

    except Exception as e:
        QMessageBox(
            QMessageBox.Icon.Critical,
            tr("An unexpected error has occurred"),
            str(universal_simplify_exception(e)),
            QMessageBox.StandardButton.Ok,
            parent_window_widget,
            flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,  # pyright: ignore[reportArgumentType]
        ).show()
        raise
    else:
        return filepath, editor
