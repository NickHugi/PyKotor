from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtCore import Qt
from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from toolset.data.indoorkit import Kit
    from toolset.data.indoormap import IndoorMap
    from toolset.data.installation import HTInstallation


class IndoorMapSettings(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        indoor_map: IndoorMap,
        kits: list[Kit],
    ):
        """Initializes the indoor map editor dialog.

        Args:
        ----
            parent (QWidget): The parent widget.
            installation (HTInstallation): The installation.
            indoor_map (IndoorMap): The indoor map to edit.
            kits (list[Kit]): Available kits.


        Returns:
        -------
            None
        Processing Logic:
        ----------------
            - Initializes UI elements from indoor_map properties
            - Populates skybox selector with options from available kits
            - Sets initial skybox selection.
        """
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
        )

        from toolset.uic.qtpy.dialogs.indoor_settings import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.nameEdit.set_installation(installation)

        self._indoorMap: IndoorMap = indoor_map
        self._kits: list[Kit] = kits

        self.ui.nameEdit.set_locstring(indoor_map.name)
        self.ui.colorEdit.setColor(indoor_map.lighting)
        self.ui.warpCodeEdit.setText(indoor_map.module_id)

        self.ui.skyboxSelect.addItem("[None]", "")
        for kit in kits:
            for skybox in kit.skyboxes:
                self.ui.skyboxSelect.addItem(skybox, skybox)
        self.ui.skyboxSelect.setCurrentText(indoor_map.skybox)

    def _setup_signals(self): ...

    def accept(self):
        super().accept()

        self._indoorMap.name = self.ui.nameEdit.locstring()
        self._indoorMap.lighting = self.ui.colorEdit.color()
        self._indoorMap.module_id = self.ui.warpCodeEdit.text()
        self._indoorMap.skybox = self.ui.skyboxSelect.currentData()
