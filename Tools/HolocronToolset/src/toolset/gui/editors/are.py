from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QColor, QImage, QPixmap
from qtpy.QtWidgets import QColorDialog

from pykotor.common.misc import Color, ResRef
from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.bwm import read_bwm
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.formats.lyt import read_lyt
from pykotor.resource.generics.are import ARE, ARENorthAxis, AREWindPower, dismantle_are, read_are
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.editor import Editor
from utility.common.geometry import SurfaceMaterial, Vector2

if TYPE_CHECKING:
    import os

    from qtpy.QtWidgets import QLabel, QWidget

    from pykotor.extract.file import ResourceResult
    from pykotor.resource.formats.bwm import BWM
    from pykotor.resource.formats.lyt import LYT
    from pykotor.resource.formats.tpc import TPC
    from pykotor.resource.formats.twoda import TwoDA
    from pykotor.resource.generics.are import ARERoom
    from toolset.gui.widgets.long_spinbox import LongSpinBox


class AREEditor(Editor):
    def __init__(self, parent: QWidget | None, installation: HTInstallation | None = None):
        supported: list[ResourceType] = [ResourceType.ARE]
        super().__init__(parent, "ARE Editor", "none", supported, supported, installation)
        self.setMinimumSize(400, 600)  # Lock the window size

        self._are: ARE = ARE()
        self._minimap = None
        self._rooms: list[ARERoom] = []  # TODO(th3w1zard1): define somewhere in ui.

        from toolset.uic.qtpy.editors.are import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()
        if installation is not None:  # will only be none in the unittests
            self._setup_installation(installation)

        self.ui.dirtColor1Edit.allow_alpha = True
        self.ui.dirtColor2Edit.allow_alpha = True
        self.ui.dirtColor3Edit.allow_alpha = True

        self.ui.minimapRenderer.default_material_color = QColor(0, 0, 255, 127)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.NON_WALK] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.NON_WALK_GRASS] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.UNDEFINED] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.material_colors[SurfaceMaterial.OBSCURING] = QColor(255, 0, 0, 80)
        self.ui.minimapRenderer.hide_walkmesh_edges = True
        self.ui.minimapRenderer.highlight_boundaries = False
        self.ui.minimapRenderer.highlight_on_hover = False

        self.new()

    def _setup_signals(self):
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)

        self.ui.mapAxisSelect.currentIndexChanged.connect(self.redoMinimap)
        self.ui.mapWorldX1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapWorldX2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapWorldY2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapWorldY2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageX1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageX2Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageY1Spin.valueChanged.connect(self.redoMinimap)
        self.ui.mapImageY2Spin.valueChanged.connect(self.redoMinimap)

        self.relevant_script_resnames: list[str] = sorted(
            iter(
                {
                    res.resname().lower()
                    for res in self._installation.get_relevant_resources(
                        ResourceType.NCS, self._filepath
                    )
                }
            )
        )

        self.ui.onEnterSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onExitSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onHeartbeatSelect.populate_combo_box(self.relevant_script_resnames)
        self.ui.onUserDefinedSelect.populate_combo_box(self.relevant_script_resnames)

    def _setup_installation(self, installation: HTInstallation):
        self._installation = installation

        self.ui.nameEdit.set_installation(installation)

        cameras: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_CAMERAS)

        self.ui.cameraStyleSelect.clear()
        self.ui.cameraStyleSelect.set_context(cameras, self._installation, HTInstallation.TwoDA_CAMERAS)
        for label in cameras.get_column("name"):
            self.ui.cameraStyleSelect.addItem(label.title())

        self.ui.dirtGroup.setVisible(installation.tsl)
        self.ui.grassEmissiveEdit.setVisible(installation.tsl)
        self.ui.grassEmissiveLabel.setVisible(installation.tsl)
        self.ui.snowCheck.setVisible(installation.tsl)
        self.ui.rainCheck.setVisible(installation.tsl)
        self.ui.lightningCheck.setVisible(installation.tsl)

        installation.setup_file_context_menu(self.ui.onEnterSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onExitSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onHeartbeatSelect, [ResourceType.NSS, ResourceType.NCS])
        installation.setup_file_context_menu(self.ui.onUserDefinedSelect, [ResourceType.NSS, ResourceType.NCS])

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        are: ARE = read_are(data)
        self._loadARE(are)
        self.adjustSize()

    def _loadARE(self, are: ARE):
        if not self._installation:
            print("Load an installation first.")
            return
        self._rooms = are.rooms
        if self._resname:
            res_result_lyt: ResourceResult | None = self._installation.resource(self._resname, ResourceType.LYT)
            if res_result_lyt:
                lyt: LYT = read_lyt(res_result_lyt.data)
                queries: list[ResourceIdentifier] = [ResourceIdentifier(room.model, ResourceType.WOK) for room in lyt.rooms]

                wok_results: dict[ResourceIdentifier, ResourceResult | None] = self._installation.resources(queries)
                walkmeshes: list[BWM] = [read_bwm(result.data) for result in wok_results.values() if result]
                self.ui.minimapRenderer.set_walkmeshes(walkmeshes)

            order: list[SearchLocation] = [SearchLocation.OVERRIDE, SearchLocation.TEXTURES_GUI, SearchLocation.MODULES]
            self._minimap: TPC | None = self._installation.texture(f"lbl_map{self._resname}", order)
            if self._minimap is None:
                print(f"Could not find texture 'lbl_map{self._resname}' required for minimap")
            else:
                self.ui.minimapRenderer.set_minimap(are, self._minimap)
                self.ui.minimapRenderer.center_camera()

        max_value: int = 100

        # Basic
        self.ui.nameEdit.set_locstring(are.name)
        self.ui.tagEdit.setText(are.tag)
        self.ui.cameraStyleSelect.setCurrentIndex(are.camera_style)
        self.ui.envmapEdit.setText(str(are.default_envmap))
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
        self.ui.fogColorEdit.set_color(are.fog_color)
        self.ui.fogNearSpin.setValue(are.fog_near)
        self.ui.fogFarSpin.setValue(are.fog_far)
        self.ui.ambientColorEdit.set_color(are.sun_ambient)
        self.ui.diffuseColorEdit.set_color(are.sun_diffuse)
        self.ui.dynamicColorEdit.set_color(are.dynamic_light)
        self.ui.windPowerSelect.setCurrentIndex(are.wind_power)
        self.ui.rainCheck.setChecked(are.chance_rain == max_value)
        self.ui.snowCheck.setChecked(are.chance_snow == max_value)
        self.ui.lightningCheck.setChecked(are.chance_lightning == max_value)
        self.ui.shadowsCheck.setChecked(are.shadows)
        self.ui.shadowsSpin.setValue(are.shadow_opacity)

        # Terrain
        self.ui.grassTextureEdit.setText(str(are.grass_texture))
        self.ui.grassDiffuseEdit.set_color(are.grass_diffuse)
        self.ui.grassAmbientEdit.set_color(are.grass_ambient)
        self.ui.grassEmissiveEdit.set_color(are.grass_emissive)
        self.ui.grassDensitySpin.setValue(are.grass_density)
        self.ui.grassSizeSpin.setValue(are.grass_size)
        self.ui.grassProbLLSpin.setValue(are.grass_prob_ll)
        self.ui.grassProbLRSpin.setValue(are.grass_prob_lr)
        self.ui.grassProbULSpin.setValue(are.grass_prob_ul)
        self.ui.grassProbURSpin.setValue(are.grass_prob_ur)
        self.ui.dirtColor1Edit.set_color(are.dirty_argb_1)
        self.ui.dirtColor2Edit.set_color(are.dirty_argb_2)
        self.ui.dirtColor3Edit.set_color(are.dirty_argb_3)
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
        self.ui.onEnterSelect.set_combo_box_text(str(are.on_enter))
        self.ui.onExitSelect.set_combo_box_text(str(are.on_exit))
        self.ui.onHeartbeatSelect.set_combo_box_text(str(are.on_heartbeat))
        self.ui.onUserDefinedSelect.set_combo_box_text(str(are.on_user_defined))

        # Comments
        self.ui.commentsEdit.setPlainText(are.comment)

    def build(self) -> tuple[bytes, bytes]:
        self._are = self._buildARE()

        data = bytearray()
        write_gff(dismantle_are(self._are, self._installation.game()), data)
        return bytes(data), b""

    def _buildARE(self) -> ARE:
        are = ARE()

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
        are.on_enter = ResRef(self.ui.onEnterSelect.currentText())
        are.on_exit = ResRef(self.ui.onExitSelect.currentText())
        are.on_heartbeat = ResRef(self.ui.onHeartbeatSelect.currentText())
        are.on_user_defined = ResRef(self.ui.onUserDefinedSelect.currentText())

        # Comments
        are.comment = self.ui.commentsEdit.toPlainText()

        # Remaining.
        are.rooms = self._rooms

        return are

    def new(self):
        super().new()
        self._loadARE(ARE())

    def redoMinimap(self):
        if self._minimap:
            are: ARE = self._buildARE()
            self.ui.minimapRenderer.set_minimap(are, self._minimap)

    def change_color(self, color_spin: LongSpinBox):
        qcolor: QColor = QColorDialog.getColor(QColor(color_spin.value()))
        color = Color.from_bgr_integer(qcolor.rgb())
        color_spin.setValue(color.bgr_integer())

    def redo_color_image(self, value: int, color_label: QLabel):
        color = Color.from_bgr_integer(value)
        r, g, b = int(color.r * 255), int(color.g * 255), int(color.b * 255)
        data = bytes([r, g, b] * 16 * 16)
        pixmap = QPixmap.fromImage(QImage(data, 16, 16, QImage.Format.Format_RGB888))
        color_label.setPixmap(pixmap)

    def change_name(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if dialog.exec():
            self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)

    def generate_tag(self):
        self.ui.tagEdit.setText("newarea" if self._resname is None or self._resname == "" else self._resname)
