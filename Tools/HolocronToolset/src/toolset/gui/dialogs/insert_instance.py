from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy.QtCore import Qt
from qtpy.QtGui import QBrush, QPalette
from qtpy.QtWidgets import QDialog, QDialogButtonBox, QListWidgetItem, QMessageBox

from pykotor.common.misc import ResRef
from pykotor.common.stream import BinaryWriter
from pykotor.resource.formats.erf import read_erf, write_erf
from pykotor.resource.formats.rim import read_rim, write_rim
from pykotor.resource.generics.utc import UTC, bytes_utc, read_utc
from pykotor.resource.generics.utd import UTD, bytes_utd, read_utd
from pykotor.resource.generics.ute import UTE, bytes_ute
from pykotor.resource.generics.utm import UTM, bytes_utm
from pykotor.resource.generics.utp import UTP, bytes_utp, read_utp
from pykotor.resource.generics.uts import UTS, bytes_uts
from pykotor.resource.generics.utt import UTT, bytes_utt
from pykotor.resource.generics.utw import UTW, bytes_utw
from pykotor.resource.type import ResourceType
from pykotor.tools import door, placeable
from pykotor.tools.misc import is_any_erf_type_file, is_bif_file, is_rim_file
from toolset.gui.helpers.callback import BetterMessageBox
from toolset.gui.widgets.settings.installations import GlobalSettings

if TYPE_CHECKING:
    from qtpy.QtGui import QColor
    from qtpy.QtWidgets import QPushButton, QWidget

    from pykotor.common.module import Module
    from pykotor.extract.file import FileResource, ResourceResult
    from toolset.data.installation import HTInstallation


class InsertInstanceDialog(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        module: Module,
        restype: ResourceType,
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        self._installation: HTInstallation = installation
        self._module: Module = module
        self._restype: ResourceType = restype

        self.global_settings: GlobalSettings = GlobalSettings()
        self.resname: str = ""
        self.data: bytes = b""
        self.filepath: Path | None = None

        from toolset.uic.qtpy.dialogs.insert_instance import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)
        self.ui.previewRenderer.installation = installation
        
        # Setup scrollbar event filter to prevent scrollbar interaction with controls
        from toolset.gui.common.filters import NoScrollEventFilter
        self._no_scroll_filter = NoScrollEventFilter(self)
        self._no_scroll_filter.setup_filter(parent_widget=self)
        
        self._setup_signals()
        self._setup_location_select()
        self._setup_resource_list()
        self.setMinimumHeight(500)

    def _setup_signals(self):
        self.ui.createResourceRadio.toggled.connect(self.on_resource_radio_toggled)
        self.ui.reuseResourceRadio.toggled.connect(self.on_resource_radio_toggled)
        self.ui.copyResourceRadio.toggled.connect(self.on_resource_radio_toggled)
        self.ui.resrefEdit.textEdited.connect(self.on_resref_edited)
        self.ui.resourceFilter.textChanged.connect(self.on_resource_filter_changed)
        self.ui.resourceList.itemSelectionChanged.connect(self.on_resource_selected)

    def _setup_location_select(self):
        self.ui.locationSelect.addItem(str(self._installation.override_path()), self._installation.override_path())
        for capsule in self._module.capsules():
            if is_rim_file(capsule.filepath()) and GlobalSettings().disableRIMSaving:
                continue
            self.ui.locationSelect.addItem(str(capsule.filepath()), capsule.filepath())
        self.ui.locationSelect.setCurrentIndex(self.ui.locationSelect.count() - 1)

    def _setup_resource_list(self):
        palette: QPalette = self.palette()  # Get the current application palette if needed
        text_color: QColor = palette.color(QPalette.ColorRole.WindowText)
        for resource in self._installation.core_resources():
            if resource.restype() == self._restype:
                item = QListWidgetItem(resource.resname())
                item.setToolTip(str(resource.filepath()))
                item.setData(Qt.ItemDataRole.UserRole, resource)
                self.ui.resourceList.addItem(item)

        for capsule in self._module.capsules():
            for resource in (resource for resource in capsule if resource.restype() == self._restype):
                if resource.restype() == self._restype:
                    item = QListWidgetItem(resource.resname())
                    item.setToolTip(str(resource.filepath()))
                    item.setForeground(QBrush(text_color))
                    item.setData(Qt.ItemDataRole.UserRole, resource)
                    self.ui.resourceList.addItem(item)

        if self.ui.resourceList.count() > 0:
            self.ui.resourceList.item(0).setSelected(True)  # pyright: ignore[reportOptionalMemberAccess]

    def accept(self):  # noqa: C901, PLR0912
        """Accepts resource selection and updates module accordingly.

        Processing Logic:
        ----------------
            - Checks which radio button is selected for reuse, copy or create resource
            - Sets resource name, file path and data based on selection
            - Writes data to file if resource is new
            - Adds resource location to module.
        """
        super().accept()

        new = True
        if not self.ui.resourceList.selectedItems():
            from toolset.gui.common.localization import translate as tr
            BetterMessageBox(tr("Choose an instance"), tr("You must choose an instance, use the radial buttons to determine where/how to create the GIT instance."), icon=QMessageBox.Critical).exec()
            return
        resource: FileResource = self.ui.resourceList.selectedItems()[0].data(Qt.ItemDataRole.UserRole)

        if self.ui.reuseResourceRadio.isChecked():
            new = False
            self.resname = resource.resname()
            self.filepath = resource.filepath()
            self.data = resource.data()
        elif self.ui.copyResourceRadio.isChecked():
            self.resname = self.ui.resrefEdit.text()
            self.filepath = Path(self.ui.locationSelect.currentData())
            self.data = resource.data()
        elif self.ui.createResourceRadio.isChecked():
            self.resname = self.ui.resrefEdit.text()
            self.filepath = Path(self.ui.locationSelect.currentData())
            if self._restype is ResourceType.UTC:
                self.data = bytes_utc(UTC())
            elif self._restype is ResourceType.UTP:
                self.data = bytes_utp(UTP())
            elif self._restype is ResourceType.UTD:
                self.data = bytes_utd(UTD())
            elif self._restype is ResourceType.UTE:
                self.data = bytes_ute(UTE())
            elif self._restype is ResourceType.UTT:
                self.data = bytes_utt(UTT())
            elif self._restype is ResourceType.UTS:
                self.data = bytes_uts(UTS())
            elif self._restype is ResourceType.UTM:
                self.data = bytes_utm(UTM())
            elif self._restype is ResourceType.UTW:
                self.data = bytes_utw(UTW())
            else:
                self.data = b""

        if new and self.filepath:
            if is_any_erf_type_file(self.filepath.name):
                erf = read_erf(self.filepath)
                erf.set_data(self.resname, self._restype, self.data)
                write_erf(erf, self.filepath)
            elif is_rim_file(self.filepath.name):
                rim = read_rim(self.filepath)
                rim.set_data(self.resname, self._restype, self.data)
                write_rim(rim, self.filepath)
            else:
                self.filepath = Path(self.filepath) / f"{self.resname}.{self._restype.extension}"
                BinaryWriter.dump(self.filepath, self.data)

        assert self.filepath is not None
        self._module.add_locations(self.resname, self._restype, [self.filepath])

    def on_resource_radio_toggled(self):
        self.ui.resourceList.setEnabled(not self.ui.createResourceRadio.isChecked())
        self.ui.resourceFilter.setEnabled(not self.ui.createResourceRadio.isChecked())
        self.ui.resrefEdit.setEnabled(not self.ui.reuseResourceRadio.isChecked())

        if self.ui.reuseResourceRadio.isChecked():
            button: QPushButton | None = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)  # pyright: ignore[reportArgumentType]
            assert button is not None, "buttonBox does not have an OK button assigned."
            button.setEnabled(True)

        if self.ui.copyResourceRadio.isChecked():
            button = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)  # pyright: ignore[reportArgumentType]
            assert button is not None, "buttonBox does not have an OK button assigned."
            button.setEnabled(self.is_valid_resref(self.ui.resrefEdit.text()))

        if self.ui.createResourceRadio.isChecked():
            button = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)  # pyright: ignore[reportArgumentType]
            assert button is not None, "buttonBox does not have an OK button assigned."
            button.setEnabled(self.is_valid_resref(self.ui.resrefEdit.text()))

    def on_resource_selected(self):
        """Updates the dynamic text label when a resource is selected."""
        selected_items: list[QListWidgetItem] = self.ui.resourceList.selectedItems()
        if selected_items:
            resource: FileResource = selected_items[0].data(Qt.ItemDataRole.UserRole)
            summary_text: str = self.generate_resource_summary(resource)
            self.ui.dynamicTextLabel.setText(summary_text)
            if resource.restype() is ResourceType.UTC and self.global_settings.showPreviewUTC:
                self.ui.previewRenderer.set_creature(read_utc(resource.data()))
            else:
                mdl_data: bytes | None = None
                mdx_data: bytes | None = None
                if resource.restype() is ResourceType.UTD and self.global_settings.showPreviewUTD:
                    modelname: str = door.get_model(read_utd(resource.data()), self._installation)
                    self.set_render_model(modelname)
                elif resource.restype() is ResourceType.UTP and self.global_settings.showPreviewUTP:
                    modelname: str = placeable.get_model(read_utp(resource.data()), self._installation)
                    self.set_render_model(modelname)
                elif (
                    resource.restype() in (ResourceType.MDL, ResourceType.MDX)
                    and any((
                        self.global_settings.showPreviewUTC,
                        self.global_settings.showPreviewUTD,
                        self.global_settings.showPreviewUTP,
                    ))
                ):
                    data = resource.data()
                    if resource.restype() is ResourceType.MDL:
                        mdl_data = data
                        if is_any_erf_type_file(resource.filepath().name):
                            erf = read_erf(resource.filepath())
                            mdx_data = erf.get(resource.resname(), ResourceType.MDX)
                        elif is_rim_file(resource.filepath().name):
                            rim = read_rim(resource.filepath())
                            mdx_data = rim.get(resource.resname(), ResourceType.MDX)
                        elif is_bif_file(resource.filepath().name):
                            mdx_res: ResourceResult | None = self._installation.resource(resource.resname(), ResourceType.MDX)
                            if mdx_res is not None:
                                mdx_data = mdx_res.data
                        else:
                            mdx_data = resource.filepath().with_suffix(".mdx").read_bytes()
                    elif resource.restype() is ResourceType.MDX:
                        mdx_data = data
                        if is_any_erf_type_file(resource.filepath().name):
                            erf = read_erf(resource.filepath())
                            mdl_data = erf.get(resource.resname(), ResourceType.MDL)
                        elif is_rim_file(resource.filepath().name):
                            rim = read_rim(resource.filepath())
                            mdl_data = rim.get(resource.resname(), ResourceType.MDL)
                        elif is_bif_file(resource.filepath().name):
                            mdl_res: ResourceResult | None = self._installation.resource(resource.resname(), ResourceType.MDL)
                            if mdl_res is not None:
                                mdl_data = mdl_res.data
                        else:
                            mdl_data = resource.filepath().with_suffix(".mdl").read_bytes()

                    if mdl_data is not None and mdx_data is not None:
                        self.ui.previewRenderer.setModel(mdl_data, mdx_data)
                    else:
                        self.ui.previewRenderer.clearModel()

    def set_render_model(
        self,
        modelname: str,
    ):
        mdl: ResourceResult | None = self._installation.resource(
            modelname, ResourceType.MDL
        )
        mdx: ResourceResult | None = self._installation.resource(
            modelname, ResourceType.MDX
        )
        if mdl is not None and mdx is not None:
            self.ui.previewRenderer.setModel(mdl.data, mdx.data)
        else:
            self.ui.previewRenderer.clearModel()

    def generate_resource_summary(
        self,
        resource: FileResource,
    ) -> str:
        summary: list[str] = [
            f"Name: {resource.resname()}",
            f"Type: {resource.restype().name}",
            f"Size: {len(resource.data())} bytes",
            f"Path: {resource.filepath().relative_to(self._installation.path())}"
        ]
        return "\n".join(summary)

    def on_resref_edited(
        self,
        text: str,
    ):
        button: QPushButton | None = self.ui.buttonBox.button(QDialogButtonBox.StandardButton.Ok)  # pyright: ignore[reportArgumentType]
        assert button is not None, "ok button is not setup on the buttonBox"
        button.setEnabled(self.is_valid_resref(text))

    def on_resource_filter_changed(self):
        text: str = self.ui.resourceFilter.text()
        for row in range(self.ui.resourceList.count()):
            item: QListWidgetItem | None = self.ui.resourceList.item(row)
            if item is None:
                RobustLogger().warning(f"item at row {row} was None!")
                continue
            item.setHidden(text not in item.text())

    def is_valid_resref(
        self,
        text: str,
    ) -> bool:
        return self._module.resource(text, self._restype) is None and ResRef.is_valid(text)
