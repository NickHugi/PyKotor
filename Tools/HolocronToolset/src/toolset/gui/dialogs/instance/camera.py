from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy import QtCore
from qtpy.QtGui import QIcon, QPixmap
from qtpy.QtWidgets import QDialog

if TYPE_CHECKING:
    from qtpy.QtWidgets import QWidget

    from pykotor.resource.generics.git import GITCamera


class CameraDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        camera: GITCamera,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            QtCore.Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            & ~QtCore.Qt.WindowType.WindowContextHelpButtonHint
            & ~QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )

        from toolset.uic.qtpy.dialogs.instance.camera import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)

        self.setWindowTitle("Edit Camera")
        self.setWindowIcon(QIcon(QPixmap(":/images/icons/k1/camera.png")))

        self.ui.xPosSpin.setValue(camera.position.x)
        self.ui.yPosSpin.setValue(camera.position.y)
        self.ui.zPosSpin.setValue(camera.position.z)
        self.ui.xOrientSpin.setValue(camera.orientation.x)
        self.ui.yOrientSpin.setValue(camera.orientation.y)
        self.ui.zOrientSpin.setValue(camera.orientation.z)
        self.ui.wOrientSpin.setValue(camera.orientation.w)
        self.ui.cameraIdSpin.setValue(camera.camera_id)
        self.ui.fovSpin.setValue(camera.fov)
        self.ui.heightSpin.setValue(camera.height)
        self.ui.micRangeSpin.setValue(camera.mic_range)
        self.ui.pitchSpin.setValue(camera.pitch)

        self.camera: GITCamera = camera

    def accept(self):
        super().accept()
        self.camera.position.x = self.ui.xPosSpin.value()
        self.camera.position.y = self.ui.yPosSpin.value()
        self.camera.position.z = self.ui.zPosSpin.value()
        self.camera.orientation.x = self.ui.xOrientSpin.value()
        self.camera.orientation.y = self.ui.yOrientSpin.value()
        self.camera.orientation.z = self.ui.zOrientSpin.value()
        self.camera.orientation.w = self.ui.wOrientSpin.value()
        self.camera.camera_id = self.ui.cameraIdSpin.value()
        self.camera.fov = self.ui.fovSpin.value()
        self.camera.height = self.ui.heightSpin.value()
        self.camera.mic_range = self.ui.micRangeSpin.value()
        self.camera.pitch = self.ui.pitchSpin.value()
