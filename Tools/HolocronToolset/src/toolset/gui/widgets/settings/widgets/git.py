from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore

from toolset.gui.common.filters import NoScrollEventFilter
from toolset.gui.widgets.settings.editor_settings.git import GITSettings
from toolset.gui.widgets.settings.widgets.base import SettingsWidget

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget


class GITWidget(SettingsWidget):
    sig_settings_edited = QtCore.Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.settings: GITSettings = GITSettings()

        from toolset.uic.qtpy.widgets.settings.git import Ui_Form

        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.ui.undefinedMaterialColourEdit.allowAlpha = True
        self.ui.dirtMaterialColourEdit.allowAlpha = True
        self.ui.obscuringMaterialColourEdit.allowAlpha = True
        self.ui.grassMaterialColourEdit.allowAlpha = True
        self.ui.stoneMaterialColourEdit.allowAlpha = True
        self.ui.woodMaterialColourEdit.allowAlpha = True
        self.ui.waterMaterialColourEdit.allowAlpha = True
        self.ui.nonWalkMaterialColourEdit.allowAlpha = True
        self.ui.transparentMaterialColourEdit.allowAlpha = True
        self.ui.carpetMaterialColourEdit.allowAlpha = True
        self.ui.metalMaterialColourEdit.allowAlpha = True
        self.ui.puddlesMaterialColourEdit.allowAlpha = True
        self.ui.swampMaterialColourEdit.allowAlpha = True
        self.ui.mudMaterialColourEdit.allowAlpha = True
        self.ui.leavesMaterialColourEdit.allowAlpha = True
        self.ui.lavaMaterialColourEdit.allowAlpha = True
        self.ui.bottomlessPitMaterialColourEdit.allowAlpha = True
        self.ui.deepWaterMaterialColourEdit.allowAlpha = True
        self.ui.doorMaterialColourEdit.allowAlpha = True
        self.ui.nonWalkGrassMaterialColourEdit.allowAlpha = True

        self.ui.coloursResetButton.clicked.connect(self.resetColours)
        self.ui.controlsResetButton.clicked.connect(self.resetControls)

        self.setup_values()

        # Install the event filter on all child widgets
        self.noScrollEventFilter: NoScrollEventFilter = NoScrollEventFilter(self)
        self.installEventFilters(self, self.noScrollEventFilter)

    def _setupColourValues(self):
        for colorEdit in [widget for widget in dir(self.ui) if "ColourEdit" in widget]:
            self._registerColour(getattr(self.ui, colorEdit), colorEdit[:-4])

    def _setupBindValues(self):
        for bindEdit in [widget for widget in dir(self.ui) if "BindEdit" in widget]:
            self._registerBind(getattr(self.ui, bindEdit), bindEdit[:-4])

    def setup_values(self):
        self._setupColourValues()
        self._setupBindValues()

    def resetColours(self):
        self.settings.resetMaterialColors()
        self._setupColourValues()

    def resetControls(self):
        self.settings.resetControls()
        self._setupBindValues()
