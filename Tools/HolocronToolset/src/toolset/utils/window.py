from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget

from pykotor.resource.type import ResourceType
from toolset.gui.editors.mdl import MDLEditor
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QMainWindow

    from toolset.data.installation import HTInstallation
    from toolset.gui.editor import Editor

TOOLSET_WINDOWS: list[QDialog | QMainWindow] = []
"""TODO: Remove this implementation, there's better ways to keep windows from being garbage collected."""

unique_sentinel = object()
def add_window(
    window: QDialog | QMainWindow,
    *,
    show: bool = True,
):
    """Prevents Qt's garbage collection by keeping a reference to the window."""
    # Save the original closeEvent method
    original_closeEvent = window.closeEvent

    # Define a new closeEvent method that also calls the original
    def new_close_event(
        event: QCloseEvent | None = unique_sentinel,  # pyright: ignore[reportArgumentType]
        *args,
        **kwargs,
    ):
        from toolset.gui.editor import Editor
        if isinstance(window, Editor) and window._filepath is not None:  # noqa: SLF001
            add_recent_file(window._filepath)  # noqa: SLF001
        if window in TOOLSET_WINDOWS:
            TOOLSET_WINDOWS.remove(window)
        # Call the original closeEvent
        if event is unique_sentinel:  # Make event arg optional just in case the class has the wrong definition.
            original_closeEvent(*args, **kwargs)
        else:
            original_closeEvent(event, *args, **kwargs)  # pyright: ignore[reportArgumentType]

    # Override the widget's closeEvent with the new one
    window.closeEvent = new_close_event  # pyright: ignore[reportAttributeAccessIssue]

    # Add the window to the global list and show it
    TOOLSET_WINDOWS.append(window)
    if show:
        if isinstance(window, QDialog):
            window.exec_()
        else:
            window.show()

def add_recent_file(file: Path):
    """Update the list of recent files."""
    settings = GlobalSettings()
    recent_files: list[str] = [str(fp) for fp in {Path(p) for p in settings.recentFiles} if fp.is_file()]
    recent_files.insert(0, str(file))
    if len(recent_files) > 15:  # noqa: PLR2004
        recent_files.pop()
    settings.recentFiles = recent_files


def open_resource_editor(
    filepath: os.PathLike | str,
    resref: str,
    restype: ResourceType,
    data: bytes,
    installation: HTInstallation | None = None,
    parent_window: QWidget | None = None,
    *,
    gff_specialized: bool | None = None,
) -> tuple[os.PathLike | str, Editor | QMainWindow] | tuple[None, None]:
    """Opens an editor for the specified resource.

    If the user settings have the editor set to inbuilt it will return
    the editor, otherwise it returns None.

    Args:
    ----
        filepath (PathLike | str): Path to the resource.
        resref (str): The ResRef.
        restype (ResourceType): The resource type.
        data (bytes): The resource data.
        parent_window (QWidget | None): The parent window.
        installation (HTInstallation | None): The installation.
        gff_specialized (bool | None): Use the editor specific to the GFF-type file. If None, uses is configured in the settings.

    Returns:
    -------
        Either the Editor object if using an internal editor, the filepath if using a external editor or None if
        no editor was successfully opened.
    """
    # To avoid circular imports, these need to be placed within the function
    from toolset.gui.editors.are import AREEditor  # noqa: PLC0415
    from toolset.gui.editors.bwm import BWMEditor  # noqa: PLC0415
    from toolset.gui.editors.dlg import DLGEditor  # noqa: PLC0415
    from toolset.gui.editors.erf import ERFEditor  # noqa: PLC0415
    from toolset.gui.editors.gff import GFFEditor  # noqa: PLC0415
    from toolset.gui.editors.git import GITEditor  # noqa: PLC0415
    from toolset.gui.editors.jrl import JRLEditor  # noqa: PLC0415
    from toolset.gui.editors.ltr import LTREditor  # noqa: PLC0415
    from toolset.gui.editors.nss import NSSEditor  # noqa: PLC0415
    from toolset.gui.editors.pth import PTHEditor  # noqa: PLC0415
    from toolset.gui.editors.ssf import SSFEditor  # noqa: PLC0415
    from toolset.gui.editors.tlk import TLKEditor  # noqa: PLC0415
    from toolset.gui.editors.tpc import TPCEditor  # noqa: PLC0415
    from toolset.gui.editors.twoda import TwoDAEditor  # noqa: PLC0415
    from toolset.gui.editors.txt import TXTEditor  # noqa: PLC0415
    from toolset.gui.editors.utc import UTCEditor  # noqa: PLC0415
    from toolset.gui.editors.utd import UTDEditor  # noqa: PLC0415
    from toolset.gui.editors.ute import UTEEditor  # noqa: PLC0415
    from toolset.gui.editors.uti import UTIEditor  # noqa: PLC0415
    from toolset.gui.editors.utm import UTMEditor  # noqa: PLC0415
    from toolset.gui.editors.utp import UTPEditor  # noqa: PLC0415
    from toolset.gui.editors.uts import UTSEditor  # noqa: PLC0415
    from toolset.gui.editors.utt import UTTEditor  # noqa: PLC0415
    from toolset.gui.editors.utw import UTWEditor  # noqa: PLC0415
    from toolset.gui.windows.audio_player import AudioPlayer  # noqa: PLC0415

    if gff_specialized is None:
        gff_specialized = GlobalSettings().gff_specializedEditors

    editor = None
    parent_window_widget = parent_window if isinstance(parent_window, QWidget) else None
    # don't send parentWindowWidget to the editors. This allows each editor to be treated as their own window.

    if restype.target_type() is ResourceType.TwoDA:
        editor = TwoDAEditor(None, installation)

    if restype.target_type() is ResourceType.SSF:
        editor = SSFEditor(None, installation)

    if restype.target_type() is ResourceType.TLK:
        editor = TLKEditor(None, installation)

    if restype.target_type() is ResourceType.LTR:
        editor = LTREditor(None, installation)

    if restype.category == "Walkmeshes":
        editor = BWMEditor(None, installation)

    if restype.category in {"Images", "Textures"} and restype is not ResourceType.TXI:
        editor = TPCEditor(None, installation)

    if restype is ResourceType.NSS:
        editor = NSSEditor(None, installation)

    if restype is ResourceType.NCS:
        QMessageBox.warning(
            parent_window_widget,
            "Cannot decompile NCS without an installation active",
            "Please select an installation from the dropdown before loading an NCS.",
        )
        return None, None

    if restype.target_type() is ResourceType.DLG:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = DLGEditor(None, installation)

    if restype.target_type() in {ResourceType.UTC, ResourceType.BTC, ResourceType.BIC}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTCEditor(None, installation)

    if restype.target_type() in {ResourceType.UTP, ResourceType.BTP}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTPEditor(None, installation)

    if restype.target_type() in {ResourceType.UTD, ResourceType.BTD}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTDEditor(None, installation)

    if restype.target_type() is ResourceType.UTS:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTSEditor(None, installation)

    if restype.target_type() in {ResourceType.UTT, ResourceType.BTT}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTTEditor(None, installation)

    if restype.target_type() in {ResourceType.UTM, ResourceType.BTM}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTMEditor(None, installation)

    if restype.target_type() is ResourceType.UTW:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTWEditor(None, installation)

    if restype.target_type() in {ResourceType.UTE, ResourceType.BTE}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTEEditor(None, installation)

    if restype.target_type() in {ResourceType.UTI, ResourceType.BTI}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = UTIEditor(None, installation)

    if restype.target_type() is ResourceType.JRL:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = JRLEditor(None, installation)

    if restype.target_type() is ResourceType.ARE:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = AREEditor(None, installation)

    if restype.target_type() is ResourceType.PTH:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = PTHEditor(None, installation)

    if restype.target_type() is ResourceType.GIT:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(None, installation)
        else:
            editor = GITEditor(None, installation)

    if restype.category == "Audio":
        editor = AudioPlayer(None)
        if parent_window_widget is not None:  # TODO(th3w1zard1): add a custom icon for AudioPlayer
            editor.setWindowIcon(parent_window_widget.windowIcon())

    if restype.name in (ResourceType.ERF, ResourceType.SAV, ResourceType.MOD, ResourceType.RIM):
        editor = ERFEditor(None, installation)

    if restype in {ResourceType.MDL, ResourceType.MDX}:
        editor = MDLEditor(None, installation)

    if editor is None and restype.target_type().contents == "gff":
        editor = GFFEditor(None, installation)

    if editor is None and restype.contents == "plaintext":
        editor = TXTEditor(None)

    if editor is not None:
        try:
            editor.load(filepath, resref, restype, data)
            editor.show()
            editor.activateWindow()

            add_window(editor)

        except Exception as e:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "An unexpected error has occurred",
                str(universal_simplify_exception(e)),
                QMessageBox.StandardButton.Ok,
                parent_window_widget,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,  # pyright: ignore[reportArgumentType]
            ).show()
            raise
        else:
            return filepath, editor
    else:
        QMessageBox(
            QMessageBox.Icon.Critical,
            "Failed to open file",
            f"The selected file format '{restype}' is not yet supported.",
            QMessageBox.StandardButton.Ok,
            parent_window_widget,
            flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,  # pyright: ignore[reportArgumentType]
        ).show()

    return None, None
