from typing import Optional, Tuple, Union

from PyQt5.QtWidgets import QMessageBox, QWidget

from gui.widgets.settings.installations import GlobalSettings
from pykotor.resource.type import ResourceType

from data.installation import HTInstallation


windows = []


def addWindow(window: QWidget) -> None:
    def removeFromList(e):
        QWidget.closeEvent(window, e)
        windows.remove(window)

    windows.append(window)
    window.closeEvent = removeFromList
    window.show()


def openResourceEditor(
        filepath: str,
        resref: str,
        restype: ResourceType,
        data: bytes,
        installation: Optional[HTInstallation] = None,
        parentwindow: QWidget = None,
        gffSpecialized: bool = None
) -> Union[Tuple[str, QWidget], Tuple[None, None]]:
    """
    Opens an editor for the specified resource. If the user settings have the editor set to inbuilt it will return
    the editor, otherwise it returns None

    Args:
        filepath: Path to the resource.
        resref: The ResRef.
        restype: The resource type.
        data: The resource data.
        parentwindow:
        installation:
        gffSpecialized: Use the editor specific to the GFF-type file. If None, uses is configured in the settings.

    Returns:
        Either the Editor object if using an internal editor, the filepath if using a external editor or None if
        no editor was successfully opened.
    """
    # To avoid circular imports, these need to be placed within the function
    from gui.editors.git import GITEditor
    from gui.editors.are import AREEditor
    from gui.editors.bwm import BWMEditor
    from gui.editors.dlg import DLGEditor
    from gui.editors.erf import ERFEditor
    from gui.editors.gff import GFFEditor
    from gui.editors.jrl import JRLEditor
    from gui.editors.nss import NSSEditor
    from gui.editors.ssf import SSFEditor
    from gui.editors.tlk import TLKEditor
    from gui.editors.tpc import TPCEditor
    from gui.editors.twoda import TwoDAEditor
    from gui.editors.txt import TXTEditor
    from gui.editors.utc import UTCEditor
    from gui.editors.utd import UTDEditor
    from gui.editors.ute import UTEEditor
    from gui.editors.uti import UTIEditor
    from gui.editors.utm import UTMEditor
    from gui.editors.utp import UTPEditor
    from gui.editors.uts import UTSEditor
    from gui.editors.utt import UTTEditor
    from gui.editors.utw import UTWEditor
    from gui.windows.audio_player import AudioPlayer

    if gffSpecialized is None:
        gffSpecialized = GlobalSettings().gffSpecializedEditors

    editor = None

    if restype in [ResourceType.TwoDA, ResourceType.TwoDA_CSV, ResourceType.TwoDA_JSON]:
        editor = TwoDAEditor(None, installation)

    if restype in [ResourceType.SSF, ResourceType.TLK_XML, ResourceType.TLK_JSON]:
        editor = SSFEditor(None, installation)

    if restype in [ResourceType.TLK, ResourceType.TLK_XML, ResourceType.TLK_JSON]:
        editor = TLKEditor(None, installation)

    if restype in [ResourceType.WOK, ResourceType.DWK, ResourceType.PWK]:
        editor = BWMEditor(None, installation)

    if restype in [ResourceType.TPC, ResourceType.TGA, ResourceType.JPG, ResourceType.BMP, ResourceType.PNG]:
        editor = TPCEditor(None, installation)

    if restype in [ResourceType.TXT, ResourceType.TXI, ResourceType.LYT, ResourceType.VIS]:
        editor = TXTEditor(None)

    if restype in [ResourceType.NSS]:
        if installation:
            editor = NSSEditor(None, installation)
        else:
            editor = TXTEditor(None, installation)

    if restype in [ResourceType.NCS]:
        if installation:
            editor = NSSEditor(None, installation)

    if restype in [ResourceType.DLG, ResourceType.DLG_XML]:
        if installation is None:
            editor = GFFEditor(None, installation)
        else:
            editor = DLGEditor(None, installation)

    if restype in [ResourceType.UTC, ResourceType.UTC_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTCEditor(None, installation, mainwindow=parentwindow)

    if restype in [ResourceType.UTP, ResourceType.UTP_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTPEditor(None, installation, mainwindow=parentwindow)

    if restype in [ResourceType.UTD, ResourceType.UTD_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTDEditor(None, installation, mainwindow=parentwindow)

    if restype in [ResourceType.UTS, ResourceType.UTS_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTSEditor(None, installation)

    if restype in [ResourceType.UTT, ResourceType.UTT_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTTEditor(None, installation)

    if restype in [ResourceType.UTM, ResourceType.UTM_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTMEditor(None, installation)

    if restype in [ResourceType.UTW, ResourceType.UTW_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTWEditor(None, installation)

    if restype in [ResourceType.UTE, ResourceType.UTE_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTEEditor(None, installation)

    if restype in [ResourceType.UTI, ResourceType.UTI_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = UTIEditor(None, installation)

    if restype in [ResourceType.JRL, ResourceType.JRL_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = JRLEditor(None, installation)

    if restype in [ResourceType.ARE, ResourceType.ARE_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = AREEditor(None, installation)

    if restype in [ResourceType.GIT, ResourceType.GIT_XML]:
        if installation is None or not gffSpecialized:
            editor = GFFEditor(None, installation)
        else:
            editor = GITEditor(None, installation)

    if restype in [ResourceType.GFF, ResourceType.GFF_XML, ResourceType.ITP, ResourceType.ITP_XML,
                   ResourceType.GUI, ResourceType.GUI_XML, ResourceType.IFO, ResourceType.IFO_XML]:
        editor = GFFEditor(None, installation)

    if restype in [ResourceType.WAV, ResourceType.MP3]:
        editor = AudioPlayer(parentwindow)

    if restype in [ResourceType.MOD, ResourceType.ERF, ResourceType.RIM]:
        editor = ERFEditor(None, installation)

    if editor is not None:
        try:
            editor.load(filepath, resref, restype, data)
            editor.show()

            addWindow(editor)

            return filepath, editor
        except Exception as e:
            QMessageBox(QMessageBox.Critical, "An unknown error occured", str(e), QMessageBox.Ok, parentwindow).show()
            raise e
    else:
        QMessageBox(QMessageBox.Critical, "Failed to open file", "The selected file is not yet supported.",
                    QMessageBox.Ok, parentwindow).show()

    return None, None
