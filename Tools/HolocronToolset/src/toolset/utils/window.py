from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog, QMainWindow, QMessageBox, QWidget

from pykotor.resource.type import ResourceType
from toolset.gui.editors.mdl import MDLEditor
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception
from utility.system.path import Path

if TYPE_CHECKING:
    import os

    from qtpy.QtGui import QCloseEvent
    from qtpy.QtWidgets import QMainWindow

    from toolset.data.installation import HTInstallation
    from toolset.gui.editor import Editor

WINDOWS: list[QWidget] = []

unique_sentinel = object()
def addWindow(window: QWidget | QDialog | QMainWindow, *, show: bool = True):
    """Prevents Qt's garbage collection by keeping a reference to the window."""
    # Save the original closeEvent method
    original_closeEvent = window.closeEvent

    # Define a new closeEvent method that also calls the original
    def newCloseEvent(
        event: QCloseEvent | None = unique_sentinel,  # type: ignore[reportArgumentType]
        *args,
        **kwargs,
    ):
        from toolset.gui.editor import Editor
        if isinstance(window, Editor) and window._filepath is not None:  # noqa: SLF001
            addRecentFile(window._filepath)  # noqa: SLF001
        if window in WINDOWS:
            WINDOWS.remove(window)
        # Call the original closeEvent
        if event is unique_sentinel:  # Make event arg optional just in case the class has the wrong definition.
            original_closeEvent(*args, **kwargs)
        else:
            original_closeEvent(event, *args, **kwargs)  # type: ignore[reportArgumentType]

    # Override the widget's closeEvent with the new one
    window.closeEvent = newCloseEvent  # type: ignore[reportAttributeAccessIssue]

    # Add the window to the global list and show it
    WINDOWS.append(window)
    if show:
        if isinstance(window, QDialog):
            window.exec_()
        else:
            window.show()

def addRecentFile(file: Path):
    """Update the list of recent files."""
    settings = GlobalSettings()
    recentFiles: list[str] = [str(fp) for fp in {Path(p) for p in settings.recentFiles} if fp.safe_isfile()]
    recentFiles.append(str(file))
    if len(recentFiles) > 15:
        recentFiles.pop()
    settings.recentFiles = recentFiles


def openResourceEditor(
    filepath: os.PathLike | str,
    resref: str,
    restype: ResourceType,
    data: bytes,
    installation: HTInstallation | None = None,
    parentWindow: QWidget | None = None,
    *,
    gff_specialized: bool | None = None,
) -> tuple[os.PathLike | str, Editor | QMainWindow] | tuple[None, None]:
    """Opens an editor for the specified resource.

    If the user settings have the editor set to inbuilt it will return
    the editor, otherwise it returns None.

    Args:
    ----
        filepath: Path to the resource.
        resref: The ResRef.
        restype: The resource type.
        data: The resource data.
        parentwindow:
        installation:
        gff_specialized: Use the editor specific to the GFF-type file. If None, uses is configured in the settings.

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
    parentWindowWidget = parentWindow if isinstance(parentWindow, QWidget) else None
    # don't send parentWindowWidget to the editors. This allows each editor to be treated as their own window.

    if restype.target_type() is ResourceType.TwoDA:
        editor = TwoDAEditor(None, installation)

    if restype.target_type() is ResourceType.SSF:
        editor = SSFEditor(None, installation)

    if restype.target_type() is ResourceType.TLK:
        editor = TLKEditor(None, installation)

    if restype.category == "Walkmeshes":
        editor = BWMEditor(None, installation)

    if restype.category in {"Images", "Textures"} and restype is not ResourceType.TXI:
        editor = TPCEditor(None, installation)

    if restype in {ResourceType.NSS, ResourceType.NCS}:
        if installation:
            editor = NSSEditor(None, installation)
        elif restype is ResourceType.NSS:
            QMessageBox.warning(
                parentWindowWidget,
                "No installation loaded",
                "The toolset cannot use its full nss editor features until you select an installation.",
            )
            editor = TXTEditor(None, installation)
        else:
            QMessageBox.warning(
                parentWindowWidget,
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
        if parentWindowWidget is not None:  # TODO(th3w1zard1): add a custom icon for AudioPlayer
            editor.setWindowIcon(parentWindowWidget.windowIcon())

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

            addWindow(editor)

        except Exception as e:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "An unexpected error has occurred",
                str(universal_simplify_exception(e)),
                QMessageBox.StandardButton.Ok,
                parentWindowWidget,
                flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
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
            parentWindowWidget,
            flags=Qt.WindowType.Window | Qt.WindowType.Dialog | Qt.WindowType.WindowStaysOnTopHint,
        ).show()

    return None, None
