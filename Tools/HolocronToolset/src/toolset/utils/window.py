from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QMessageBox, QWidget

from pykotor.resource.formats.erf.erf_data import ERFType
from pykotor.resource.type import ResourceType
from toolset.gui.editors.mdl import MDLEditor
from toolset.gui.widgets.settings.installations import GlobalSettings
from utility.error_handling import universal_simplify_exception

if TYPE_CHECKING:
    import os

    from PyQt5.QtCore import QObject
    from PyQt5.QtWidgets import QMainWindow

    from gui.editor import Editor
    from toolset.data.installation import HTInstallation

WINDOWS: list[QWidget] = []


def addWindow(window: QWidget):
    def removeFromList(a0):
        QWidget.closeEvent(window, a0)
        if window in WINDOWS:
            WINDOWS.remove(window)

    WINDOWS.append(window)
    window.closeEvent = removeFromList
    window.show()


def openResourceEditor(
    filepath: os.PathLike | str,
    resref: str,
    restype: ResourceType,
    data: bytes,
    installation: HTInstallation | None = None,
    parentWindow: QWidget | QObject | None = None,
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

    if restype in {ResourceType.TwoDA, ResourceType.TwoDA_CSV, ResourceType.TwoDA_JSON}:
        editor = TwoDAEditor(parentWindowWidget, installation)

    if restype in {ResourceType.SSF, ResourceType.SSF_XML}:
        editor = SSFEditor(parentWindowWidget, installation)

    if restype in {ResourceType.TLK, ResourceType.TLK_XML, ResourceType.TLK_JSON}:
        editor = TLKEditor(parentWindowWidget, installation)

    if restype in {ResourceType.WOK, ResourceType.DWK, ResourceType.PWK}:
        editor = BWMEditor(parentWindowWidget, installation)

    if restype in {ResourceType.TPC, ResourceType.TGA, ResourceType.JPG, ResourceType.BMP, ResourceType.PNG}:
        editor = TPCEditor(parentWindowWidget, installation)

    if restype in {ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS}:
        editor = TXTEditor(parentWindowWidget)

    if restype in {ResourceType.NSS, ResourceType.NCS}:
        if installation:
            editor = NSSEditor(parentWindowWidget, installation)
        elif restype == ResourceType.NSS:
            QMessageBox.warning(parentWindowWidget, "No installation loaded", "The toolset cannot use its full nss editor features until you select an installation.")
            editor = TXTEditor(parentWindowWidget, installation)
        else:
            QMessageBox.warning(parentWindowWidget, "Cannot decompile NCS without an installation active", "Please select an installation from the dropdown before loading an NCS.")
            return None, None

    if restype in {ResourceType.DLG, ResourceType.DLG_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = DLGEditor(parentWindowWidget, installation)

    if restype in {ResourceType.UTC, ResourceType.UTC_XML}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTCEditor(parentWindowWidget, installation, mainwindow=parentWindow)

    if restype in {ResourceType.UTP, ResourceType.UTP_XML}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTPEditor(parentWindowWidget, installation, mainwindow=parentWindow)

    if restype in {ResourceType.UTD, ResourceType.UTD_XML}:
        if installation is None or not gff_specialized:
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTDEditor(parentWindowWidget, installation, mainwindow=parentWindow)

    if restype in {ResourceType.UTS, ResourceType.UTS_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTSEditor(parentWindowWidget, installation)

    if restype in {ResourceType.UTT, ResourceType.UTT_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTTEditor(parentWindowWidget, installation)

    if restype in {ResourceType.UTM, ResourceType.UTM_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTMEditor(parentWindowWidget, installation)

    if restype in {ResourceType.UTW, ResourceType.UTW_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTWEditor(parentWindowWidget, installation)

    if restype in {ResourceType.UTE, ResourceType.UTE_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTEEditor(parentWindowWidget, installation)

    if restype in {ResourceType.UTI, ResourceType.UTI_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = UTIEditor(parentWindowWidget, installation)

    if restype in {ResourceType.JRL, ResourceType.JRL_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = JRLEditor(parentWindowWidget, installation)

    if restype in {ResourceType.ARE, ResourceType.ARE_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = AREEditor(parentWindowWidget, installation)

    if restype in {ResourceType.PTH, ResourceType.PTH_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = PTHEditor(parentWindowWidget, installation)

    if restype in {ResourceType.GIT, ResourceType.GIT_XML}:
        if installation is None or not gff_specialized:  # noqa: SIM108
            editor = GFFEditor(parentWindowWidget, installation)
        else:
            editor = GITEditor(parentWindowWidget, installation)

    if restype in {
        ResourceType.GFF,
        ResourceType.GFF_XML,
        ResourceType.ITP,
        ResourceType.ITP_XML,
        ResourceType.GUI,
        ResourceType.GUI_XML,
        ResourceType.IFO,
        ResourceType.IFO_XML,
        ResourceType.RES,
        ResourceType.RES_XML,
        ResourceType.FAC,
        ResourceType.FAC_XML,
    }:
        editor = GFFEditor(None, installation)

    if restype in {ResourceType.WAV, ResourceType.MP3}:
        editor = AudioPlayer(parentWindowWidget)

    if restype.name in ERFType.__members__ or restype == ResourceType.RIM:
        editor = ERFEditor(parentWindowWidget, installation)

    if restype in {ResourceType.MDL, ResourceType.MDX}:
        editor = MDLEditor(parentWindowWidget, installation)

    if editor is not None:
        try:
            editor.load(filepath, resref, restype, data)
            editor.show()

            addWindow(editor)

        except Exception as e:
            QMessageBox(
                QMessageBox.Critical,
                "An unexpected error has occurred",
                str(universal_simplify_exception(e)),
                QMessageBox.Ok,
                parentWindowWidget
            ).show()
            raise
        else:
            return filepath, editor
    else:
        QMessageBox(
            QMessageBox.Critical,
            "Failed to open file",
            f"The selected file format '{restype}' is not yet supported.",
            QMessageBox.Ok,
            parentWindowWidget
        ).show()

    return None, None
