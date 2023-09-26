from typing import Optional, Tuple

from PyQt5.QtGui import QColor, QImage, QPixmap
from PyQt5.QtWidgets import QColorDialog, QLabel, QWidget

from pykotor.common.geometry import Vector2
from pykotor.common.misc import Color, ResRef
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.are import (
    ARE,
    ARENorthAxis,
    AREWindPower,
    dismantle_are,
    read_are,
)
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from toolset.gui.widgets.long_spinbox import LongSpinBox


class AREEditor(Editor):
    def __init__(self, parent: Optional[QWidget], installation: Optional[HTInstallation] = None):
        supported = [ResourceType.ARE]
        super().__init__(parent, "ARE Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        self._are: ARE = ARE()

        from toolset.uic.editors.are import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setupMenus()
        self._setupSignals()
        self._setupInstallation(installation)

        self.ui.dirtColor1Edit.allowAlpha = True
        self.ui.dirtColor2Edit.allowAlpha = True
        self.ui.dirtColor3Edit.allowAlpha = True

        self.new()

    def _setupSignals(self) -> None:
        self.ui.tagGenerateButton.clicked.connect(self.generateTag)

    def _setupInstallation(self, installation: HTInstallation) -> None:
        self._installation = installation

        self.ui.nameEdit.setInstallation(installation)

        cameras = installation.htGetCache2DA(HTInstallation.TwoDA_CAMERAS)

        self.ui.cameraStyleSelect.clear()
        [self.ui.cameraStyleSelect.addItem(label.title()) for label in cameras.get_column("name")]

        self.ui.dirtGroup.setVisible(installation.tsl)
        self.ui.grassEmissiveEdit.setVisible(installation.tsl)
        self.ui.grassEmissiveLabel.setVisible(installation.tsl)
        self.ui.snowCheck.setVisible(installation.tsl)
        self.ui.rainCheck.setVisible(installation.tsl)
        self.ui.lightningCheck.setVisible(installation.tsl)

    def load(self, filepath: str, resref: str, restype: ResourceType, data: bytes) -> None:
        super().load(filepath, resref, restype, data)

        are = read_are(data)
        self._loadARE(are)

    def _loadARE(self, are: ARE) -> None:
        self._are = are

        # Basic
        self.ui.nameEdit.setLocstring(are.name)
        self.ui.tagEdit.setText(are.tag)
        self.ui.cameraStyleSelect.setCurrentIndex(are.camera_style)
        self.ui.envmapEdit.setText(are.default_envmap.get())
        self.ui.disableTransitCheck.setChecked(are.disable_transit)
        self.ui.unescapableCheck.setChecked(are.unescapable)
        self.ui.alphaTestSpin.setValue(are.alpha_test)
        self.ui.stealthCheck.setChecked(are.stealth_xp)
        self.ui.stealthMaxSpin.setValue(are.stealth_xp_max)
        self.ui.stealthLossSpin.setValue(are.stealth_xp_loss)

        # Map
        self.ui.mapAxisSelect.setCurrentIndex(are.north_axis)
        self.ui.mapZoomSpin.setValue(are.map_zoom)
        self.ui.mapResXSpin.setValue(are.map_res_x)
        self.ui.mapImageX1Spin.setValue(are.map_point_1.x)
        self.ui.mapImageX2Spin.setValue(are.map_point_2.x)
        self.ui.mapImageY1Spin.setValue(are.map_point_1.y)
        self.ui.mapImageY2Spin.setValue(are.map_point_2.y)
        self.ui.mapWorldX1Spin.setValue(are.world_point_1.x)
        self.ui.mapWorldX2Spin.setValue(are.world_point_2.x)
        self.ui.mapWorldY1Spin.setValue(are.world_point_1.y)
        self.ui.mapWorldY2Spin.setValue(are.world_point_2.y)

        # Weather
        self.ui.fogEnabledCheck.setChecked(are.fog_enabled)
        self.ui.fogColorEdit.setColor(are.fog_color)
        self.ui.fogNearSpin.setValue(are.fog_near)
        self.ui.fogFarSpin.setValue(are.fog_far)
        self.ui.ambientColorEdit.setColor(are.sun_ambient)
        self.ui.diffuseColorEdit.setColor(are.sun_diffuse)
        self.ui.dynamicColorEdit.setColor(are.dynamic_light)
        self.ui.windPowerSelect.setCurrentIndex(are.wind_power)
        self.ui.rainCheck.setChecked(are.chance_rain == 100)
        self.ui.snowCheck.setChecked(are.chance_snow == 100)
        self.ui.lightningCheck.setChecked(are.chance_lightning == 100)
        self.ui.shadowsCheck.setChecked(are.shadows)
        self.ui.shadowsSpin.setValue(are.shadow_opacity)

        # Terrain
        self.ui.grassTextureEdit.setText(are.grass_texture.get())
        self.ui.grassDiffuseEdit.setColor(are.grass_diffuse)
        self.ui.grassAmbientEdit.setColor(are.grass_ambient)
        self.ui.grassEmissiveEdit.setColor(are.grass_emissive)
        self.ui.grassDensitySpin.setValue(are.grass_density)
        self.ui.grassSizeSpin.setValue(are.grass_size)
        self.ui.grassProbLLSpin.setValue(are.grass_prob_ll)
        self.ui.grassProbLRSpin.setValue(are.grass_prob_lr)
        self.ui.grassProbULSpin.setValue(are.grass_prob_ul)
        self.ui.grassProbURSpin.setValue(are.grass_prob_ur)
        self.ui.dirtColor1Edit.setColor(are.dirty_argb_1)
        self.ui.dirtColor2Edit.setColor(are.dirty_argb_2)
        self.ui.dirtColor3Edit.setColor(are.dirty_argb_3)
        self.ui.dirtFormula1Spin.setValue(are.dirty_formula_1)
        self.ui.dirtFormula2Spin.setValue(are.dirty_formula_2)
        self.ui.dirtFormula3Spin.setValue(are.dirty_formula_3)
        self.ui.dirtFunction1Spin.setValue(are.dirty_func_1)
        self.ui.dirtFunction2Spin.setValue(are.dirty_func_2)
        self.ui.dirtFunction3Spin.setValue(are.dirty_func_3)
        self.ui.dirtSize1Spin.setValue(are.dirty_size_1)
        self.ui.dirtSize2Spin.setValue(are.dirty_size_2)
        self.ui.dirtSize3Spin.setValue(are.dirty_size_3)

        # Scripts
        self.ui.onEnterEdit.setText(are.on_enter.get())
        self.ui.onExitEdit.setText(are.on_exit.get())
        self.ui.onHeartbeatEdit.setText(are.on_heartbeat.get())
        self.ui.onUserDefinedEdit.setText(are.on_user_defined.get())

        # Comments
        self.ui.commentsEdit.setPlainText(are.comment)

    def build(self) -> Tuple[bytes, bytes]:
        are = self._are

        # Basic
        are.name = self.ui.nameEdit.locstring()
        are.tag = self.ui.tagEdit.text()
        are.camera_style = self.ui.cameraStyleSelect.currentIndex()
        are.default_envmap = ResRef(self.ui.envmapEdit.text())
        are.unescapable = self.ui.unescapableCheck.isChecked()
        are.disable_transit = self.ui.disableTransitCheck.isChecked()
        are.alpha_test = self.ui.alphaTestSpin.value()
        are.stealth_xp = self.ui.stealthCheck.isChecked()
        are.stealth_xp_max = self.ui.stealthMaxSpin.value()
        are.stealth_xp_loss = self.ui.stealthLossSpin.value()

        # Map
        are.north_axis = ARENorthAxis(self.ui.mapAxisSelect.currentIndex())
        are.map_zoom = self.ui.mapZoomSpin.value()
        are.map_res_x = self.ui.mapResXSpin.value()
        are.map_point_1 = Vector2(self.ui.mapImageX1Spin.value(), self.ui.mapImageY1Spin.value())
        are.map_point_2 = Vector2(self.ui.mapImageX2Spin.value(), self.ui.mapImageY2Spin.value())
        are.world_point_1 = Vector2(self.ui.mapWorldX1Spin.value(), self.ui.mapWorldY1Spin.value())
        are.world_point_2 = Vector2(self.ui.mapWorldX2Spin.value(), self.ui.mapWorldY2Spin.value())

        # Weather
        are.fog_enabled = self.ui.fogEnabledCheck.isChecked()
        are.fog_color = self.ui.fogColorEdit.color()
        are.fog_near = self.ui.fogNearSpin.value()
        are.fog_far = self.ui.fogFarSpin.value()
        are.sun_ambient = self.ui.ambientColorEdit.color()
        are.sun_diffuse = self.ui.diffuseColorEdit.color()
        are.dynamic_light = self.ui.dynamicColorEdit.color()
        are.wind_power = AREWindPower(self.ui.windPowerSelect.currentIndex())
        are.chance_rain = 100 if self.ui.rainCheck.isChecked() else 0
        are.chance_snow = 100 if self.ui.snowCheck.isChecked() else 0
        are.chance_lightning = 100 if self.ui.lightningCheck.isChecked() else 0
        are.shadows = self.ui.shadowsCheck.isChecked()
        are.shadow_opacity = self.ui.shadowsSpin.value()

        # Terrain
        are.grass_texture = ResRef(self.ui.grassTextureEdit.text())
        are.grass_diffuse = self.ui.grassDiffuseEdit.color()
        are.grass_ambient = self.ui.ambientColorEdit.color()
        are.grass_emissive = self.ui.grassEmissiveEdit.color()
        are.grass_size = self.ui.grassSizeSpin.value()
        are.grass_density = self.ui.grassDensitySpin.value()
        are.grass_prob_ll = self.ui.grassProbLLSpin.value()
        are.grass_prob_lr = self.ui.grassProbLRSpin.value()
        are.grass_prob_ul = self.ui.grassProbULSpin.value()
        are.grass_prob_ur = self.ui.grassProbURSpin.value()
        are.dirty_argb_1 = self.ui.dirtColor1Edit.color()
        are.dirty_argb_2 = self.ui.dirtColor2Edit.color()
        are.dirty_argb_3 = self.ui.dirtColor3Edit.color()
        are.dirty_formula_1 = self.ui.dirtFormula1Spin.value()
        are.dirty_formula_2 = self.ui.dirtFormula2Spin.value()
        are.dirty_formula_3 = self.ui.dirtFormula3Spin.value()
        are.dirty_func_1 = self.ui.dirtFunction1Spin.value()
        are.dirty_func_2 = self.ui.dirtFunction2Spin.value()
        are.dirty_func_3 = self.ui.dirtFunction3Spin.value()
        are.dirty_size_1 = self.ui.dirtSize1Spin.value()
        are.dirty_size_2 = self.ui.dirtSize2Spin.value()
        are.dirty_size_3 = self.ui.dirtSize3Spin.value()

        # Scripts
        are.on_enter = ResRef(self.ui.onEnterEdit.text())
        are.on_exit = ResRef(self.ui.onExitEdit.text())
        are.on_heartbeat = ResRef(self.ui.onHeartbeatEdit.text())
        are.on_user_defined = ResRef(self.ui.onUserDefinedEdit.text())

        # Comments
        are.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        write_gff(dismantle_are(self._are), data)
        return data, b""

    def new(self) -> None:
        super().new()
        self._loadARE(ARE())

    def changeColor(self, colorSpin: LongSpinBox) -> None:
        qcolor = QColorDialog.getColor(QColor(colorSpin.value()))
        color = Color.from_bgr_integer(qcolor.rgb())
        colorSpin.setValue(color.bgr_integer())

    def redoColorImage(self, value: int, colorLabel: QLabel) -> None:
        color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format_RGB888))
        colorLabel.setPixmap(pixmap)

    def changeName(self) -> None:
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring)
        if dialog.exec_():
            self._loadLocstring(self.ui.nameEdit, dialog.locstring)

    def generateTag(self) -> None:
        self.ui.tagEdit.setText("newarea" if self._resref is None or self._resref == "" else self._resref)
