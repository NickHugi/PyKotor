from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from loggerplus import RobustLogger
from qtpy import QtCore
from qtpy.QtCore import Qt
from qtpy.QtGui import QPixmap
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QListWidgetItem,
    QMenu,
    QShortcut,
    QTreeWidgetItem,
)

from pykotor.common.misc import ResRef
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.gff import write_gff
from pykotor.resource.generics.uti import UTI, UTIProperty, dismantle_uti, read_uti
from pykotor.resource.type import ResourceType
from toolset.data.installation import HTInstallation
from toolset.gui.dialogs.edit.locstring import LocalizedStringDialog
from toolset.gui.dialogs.load_from_location_result import (
    FileSelectionWindow,
    ResourceItems,
)
from toolset.gui.editor import Editor
from toolset.utils.window import add_window

if TYPE_CHECKING:

    import os

    from qtpy.QtWidgets import QWidget
    from typing_extensions import Literal

    from pykotor.extract.file import LocationResult
    from pykotor.resource.formats.twoda.twoda_data import TwoDA


class UTIEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation = None,
    ):
        """Initializes the Item Editor window.

        Args:
        ----
            parent: {QWidget}: The parent widget
            installation: {HTInstallation}: The KOTOR installation.
        """
        supported = [ResourceType.UTI]
        super().__init__(parent, "Item Editor", "item", supported, supported, installation)

        self._uti = UTI()

        from toolset.uic.qtpy.editors.uti import Ui_MainWindow
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()
        self._installation: HTInstallation

        self._setupInstallation(installation)
        self.ui.descEdit.set_installation(installation)

        self.setMinimumSize(700, 350)

        QShortcut("Del", self).activated.connect(self.onDelShortcut)

        self.ui.iconLabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)  # pyright: ignore[reportArgumentType]
        self.ui.iconLabel.customContextMenuRequested.connect(self._iconLabelContextMenu)

        self.new()

    def _setup_signals(self):
        """Set up signal connections for UI elements."""
        self.ui.tagGenerateButton.clicked.connect(self.generate_tag)
        self.ui.tagGenerateButton.setToolTip("Reset this custom tag so it matches the resref")
        self.ui.resrefGenerateButton.clicked.connect(self.generateResref)
        self.ui.editPropertyButton.clicked.connect(self.editSelectedProperty)
        self.ui.removePropertyButton.clicked.connect(self.remove_selectedProperty)
        self.ui.addPropertyButton.clicked.connect(self.addSelectedProperty)
        self.ui.availablePropertyList.doubleClicked.connect(self.onAvailablePropertyListDoubleClicked)
        self.ui.assignedPropertiesList.doubleClicked.connect(self.onAssignedPropertyListDoubleClicked)

        self.ui.modelVarSpin.valueChanged.connect(self.onUpdateIcon)
        self.ui.bodyVarSpin.valueChanged.connect(self.onUpdateIcon)
        self.ui.textureVarSpin.valueChanged.connect(self.onUpdateIcon)
        self.ui.baseSelect.currentIndexChanged.connect(self.onUpdateIcon)

    def _setupInstallation(
        self,
        installation: HTInstallation,
    ):
        """Sets up the installation for editing.

        Args:
        ----
            installation (HTInstallation): The installation to set up.

        Processing Logic:
        ----------------
            - Sets the installation property on the UI
            - Loads required 2DAs into the installation cache
            - Populates base item select from baseitems 2DA
            - Populates available properties list from item properties 2DA
            - Adds subproperties from subtype 2DAs to their parent properties.
        """
        self._installation = installation
        self.ui.nameEdit.set_installation(installation)
        self.ui.descEdit.set_installation(installation)

        required: list[str] = [HTInstallation.TwoDA_BASEITEMS, HTInstallation.TwoDA_ITEM_PROPERTIES]
        installation.ht_batch_cache_2da(required)

        baseitems: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        itemProperties: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_ITEM_PROPERTIES)
        self.ui.baseSelect.clear()
        if baseitems is None:
            RobustLogger().error("Failed to retrieve BASEITEMS 2DA.")
        else:
            self.ui.baseSelect.setItems(baseitems.get_column("label"))
            self.ui.baseSelect.setContext(baseitems, installation, HTInstallation.TwoDA_BASEITEMS)

        self.ui.availablePropertyList.clear()
        if itemProperties is not None:
            for i in range(itemProperties.get_height()):
                propName = UTIEditor.propertyName(installation, i)
                item = QTreeWidgetItem([propName])
                self.ui.availablePropertyList.addTopLevelItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

                subtypeResname = itemProperties.get_cell(i, "subtyperesref")
                if not subtypeResname:
                    item.setData(0, Qt.ItemDataRole.UserRole, i)
                    item.setData(0, Qt.ItemDataRole.UserRole + 1, i)
                    continue

                subtype = installation.ht_get_cache_2da(subtypeResname)
                if subtype is None:
                    RobustLogger().warning(f"Failed to retrieve subtype '{subtypeResname}' for property name '{propName}' at index {i}. Skipping...")
                    continue

                for j in range(subtype.get_height()):
                    if subtypeResname == "spells":
                        print("   ", j)
                    name = UTIEditor.subpropertyName(installation, i, j)
                    if not name or not name.strip():  # possible HACK: this fixes a bug where there'd be a bunch of blank entries.
                        continue
                    child = QTreeWidgetItem([name])
                    child.setData(0, Qt.ItemDataRole.UserRole, i)
                    child.setData(0, Qt.ItemDataRole.UserRole + 1, j)
                    item.addChild(child)

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        super().load(filepath, resref, restype, data)

        uti = read_uti(data)
        self._loadUTI(uti)

    def _loadUTI(self, uti: UTI):
        """Loads a UTI object into the UI.

        Args:
        ----
            uti: UTI - The UTI object to load

        Loads UTI data:
            - Loads basic UTI data like name, description etc into corresponding UI elements.
            - Loads properties and comments from UTI object into UI lists and text editors.
        """
        self._uti = uti

        # Basic
        self.ui.nameEdit.setLocstring(uti.name)
        self.ui.descEdit.setLocstring(uti.description)
        self.ui.tagEdit.setText(uti.tag)
        self.ui.resrefEdit.setText(str(uti.resref))
        self.ui.baseSelect.setCurrentIndex(uti.base_item)
        self.ui.costSpin.setValue(uti.cost)
        self.ui.additionalCostSpin.setValue(uti.add_cost)
        self.ui.upgradeSpin.setValue(uti.upgrade_level)
        self.ui.plotCheckbox.setChecked(bool(uti.plot))
        self.ui.chargesSpin.setValue(uti.charges)
        self.ui.stackSpin.setValue(uti.stack_size)
        self.ui.modelVarSpin.setValue(uti.model_variation)
        self.ui.bodyVarSpin.setValue(uti.body_variation)
        self.ui.textureVarSpin.setValue(uti.texture_variation)

        # Properties
        self.ui.assignedPropertiesList.clear()
        for utiProperty in uti.properties:
            text = self.propertySummary(utiProperty)
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, utiProperty)
            self.ui.assignedPropertiesList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

        # Comments
        self.ui.commentsEdit.setPlainText(uti.comment)

    def build(self) -> tuple[bytes, bytes]:
        """Builds a UTI object from UI input.

        Args:
        ----
            self: The object instance

        Returns:
        -------
            tuple[bytes, bytes]: Byte data and empty string
        """
        uti: UTI = deepcopy(self._uti)

        # Basic
        uti.name = self.ui.nameEdit.locstring()
        uti.description = self.ui.descEdit.locstring()
        uti.tag = self.ui.tagEdit.text()
        uti.resref = ResRef(self.ui.resrefEdit.text())
        uti.base_item = self.ui.baseSelect.currentIndex()
        uti.cost = self.ui.costSpin.value()
        uti.add_cost = self.ui.additionalCostSpin.value()
        uti.upgrade_level = self.ui.upgradeSpin.value()
        uti.plot = self.ui.plotCheckbox.isChecked()
        uti.charges = self.ui.chargesSpin.value()
        uti.stack_size = self.ui.stackSpin.value()
        uti.model_variation = self.ui.modelVarSpin.value()
        uti.body_variation = self.ui.bodyVarSpin.value()
        uti.texture_variation = self.ui.textureVarSpin.value()
        uti.properties.clear()
        for i in range(self.ui.assignedPropertiesList.count()):
            item = self.ui.assignedPropertiesList.item(i)
            if item is None:
                RobustLogger().warning(f"Failed to retrieve property item at index {i} from assigned properties list. Skipping...")
                continue
            uti.properties.append(item.data(Qt.ItemDataRole.UserRole))

        # Comments
        uti.comment = self.ui.commentsEdit.toPlainText()

        data = bytearray()
        gff = dismantle_uti(uti)
        write_gff(gff, data)

        return data, b""

    def new(self):
        super().new()
        self._loadUTI(UTI())

    def changeName(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.nameEdit.locstring())
        if not dialog.exec():
            return
        self._load_locstring(self.ui.nameEdit.ui.locstringText, dialog.locstring)  # pyright: ignore[reportArgumentType]

    def changeDesc(self):
        dialog = LocalizedStringDialog(self, self._installation, self.ui.descEdit.locstring())
        if not dialog.exec():
            return
        self._load_locstring(self.ui.descEdit.ui.locstringText, dialog.locstring)  # pyright: ignore[reportArgumentType]

    def generate_tag(self):
        resrefText = self.ui.resrefEdit.text()
        if not resrefText or not resrefText.strip():
            self.generateResref()
        self.ui.tagEdit.setText(self.ui.resrefEdit.text())

    def generateResref(self):
        if self._resname and self._resname.strip():
            self.ui.resrefEdit.setText(self._resname)
        else:
            self.ui.resrefEdit.setText("m00xx_itm_000")

    def editSelectedProperty(self):
        if not self.ui.assignedPropertiesList.selectedItems():
            return
        utiProperty: UTIProperty = self.ui.assignedPropertiesList.selectedItems()[0].data(Qt.ItemDataRole.UserRole)
        dialog = PropertyEditor(self._installation, utiProperty)
        if not dialog.exec():
            return
        self.ui.assignedPropertiesList.selectedItems()[0].setData(Qt.ItemDataRole.UserRole, dialog.utiProperty())
        self.ui.assignedPropertiesList.selectedItems()[0].setText(self.propertySummary(dialog.utiProperty()))

    def addSelectedProperty(self):
        if not self.ui.availablePropertyList.selectedItems():
            return
        item = self.ui.availablePropertyList.selectedItems()[0]
        propertyId = item.data(0, Qt.ItemDataRole.UserRole)
        if propertyId is None:
            return
        subtypeId = item.data(0, Qt.ItemDataRole.UserRole + 1)
        self._add_property_main(propertyId, subtypeId)

    def _add_property_main(
        self,
        propertyId: int,
        subtypeId: int,
    ):
        """Adds a property to an item.

        Args:
        ----
            propertyId: The id of the property to add.
            subtypeId: The subtype id of the item.

        Processing Logic:
        ----------------
            - Gets the item properties table from the installation.
            - Creates a UTIProperty object and populates it with data from the table.
            - Adds a summary of the property to the assigned properties list widget.
            - Sets the UTIProperty as user data on the list item.
        """
        itemprops: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_ITEM_PROPERTIES)
        if itemprops is None:
            return

        utiProperty = UTIProperty()
        utiProperty.property_name = propertyId
        utiProperty.subtype = subtypeId
        utiProperty.cost_table = itemprops.get_row(propertyId).get_integer("costtableresref", 255)
        utiProperty.cost_value = 0
        utiProperty.param1 = itemprops.get_row(propertyId).get_integer("param1resref", 255)
        utiProperty.param1_value = 0
        utiProperty.chance_appear = 100

        text: str = self.propertySummary(utiProperty)
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, utiProperty)
        self.ui.assignedPropertiesList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

    def remove_selectedProperty(self):
        if not self.ui.assignedPropertiesList.selectedItems():
            return
        index = self.ui.assignedPropertiesList.selectedIndexes()[0]
        self.ui.assignedPropertiesList.takeItem(index.row())

    def propertySummary(
        self,
        utiProperty: UTIProperty,
    ) -> str:  # sourcery skip: assign-if-exp, reintroduce-else
        """Retrieve the property, subproperty and cost names from the UTIEditor.

        Processing Logic:
        ----------------
            - It returns a formatted string combining the retrieved names.
            - If a cost or subproperty is not present, it is omitted from the returned string.
        """
        propName: str = UTIEditor.propertyName(self._installation, utiProperty.property_name)
        subpropName: str | None = UTIEditor.subpropertyName(self._installation, utiProperty.property_name, utiProperty.subtype)
        costName: str | None = UTIEditor.costName(self._installation, utiProperty.cost_table, utiProperty.cost_value)

        if costName and subpropName:
            return f"{propName}: {subpropName} [{costName}]"
        if subpropName:
            return f"{propName}: {subpropName}"
        if costName:
            return f"{propName}: [{costName}]"
        return f"{propName}"

    def _generateIconTooltip(self, *, asHtml: bool = False) -> str:  # sourcery skip: lift-return-into-if
        """Generates a detailed tooltip for the iconLabel."""
        baseItem = self.ui.baseSelect.currentIndex()
        modelVariation = self.ui.modelVarSpin.value()
        textureVariation = self.ui.textureVarSpin.value()

        assert self._installation is not None
        baseItemName = self._installation.get_item_base_name(baseItem)
        modelVarName = self._installation.get_model_var_name(modelVariation)
        textureVarName = self._installation.get_texture_var_name(textureVariation)
        iconPath = self._installation.get_item_icon_path(baseItem, modelVariation, textureVariation)

        if asHtml:
            tooltip = (
                f"<b>Base Item:</b> {baseItemName} (ID: {baseItem})<br>"
                f"<b>Model Variation:</b> {modelVarName} (ID: {modelVariation})<br>"
                f"<b>Texture Variation:</b> {textureVarName} (ID: {textureVariation})<br>"
                f"<b>Icon Name:</b> {iconPath}"
            )
        else:
            tooltip = (
                f"Base Item: {baseItemName} (ID: {baseItem})\n"
                f"Model Variation: {modelVarName} (ID: {modelVariation})\n"
                f"Texture Variation: {textureVarName} (ID: {textureVariation})\n"
                f"Icon Name: {iconPath}"
            )
        return tooltip

    def _iconLabelContextMenu(self, position):
        contextMenu = QMenu(self)
        copyMenu = QMenu("Copy..")

        baseItem = self.ui.baseSelect.currentIndex()
        modelVariation = self.ui.modelVarSpin.value()
        textureVariation = self.ui.textureVarSpin.value()
        iconPath = self._installation.get_item_icon_path(baseItem, modelVariation, textureVariation)

        summaryItemIconAction = QAction("Icon Summary", self)
        summaryItemIconAction.triggered.connect(lambda: self._copyIconTooltip())

        copyBaseItemAction = QAction(f"Base Item: {baseItem}", self)
        copyBaseItemAction.triggered.connect(lambda: self._copyToClipboard(f"{baseItem}"))

        copyModelVariationAction = QAction(f"Model Variation: {modelVariation}", self)
        copyModelVariationAction.triggered.connect(lambda: self._copyToClipboard(f"{modelVariation}"))

        copyTextureVariationAction = QAction(f"Texture Variation: {textureVariation}", self)
        copyTextureVariationAction.triggered.connect(lambda: self._copyToClipboard(f"{textureVariation}"))

        copyIconPathAction = QAction(f"Icon Name: '{iconPath}'", self)
        copyIconPathAction.triggered.connect(lambda: self._copyToClipboard(f"{iconPath}"))

        copyMenu.addAction(summaryItemIconAction)
        copyMenu.addSeparator()
        copyMenu.addAction(copyBaseItemAction)
        copyMenu.addAction(copyModelVariationAction)
        copyMenu.addAction(copyTextureVariationAction)
        copyMenu.addAction(copyIconPathAction)

        fileMenu = contextMenu.addMenu("File...")
        assert fileMenu is not None
        locations = self._installation.locations(
            ([iconPath], [ResourceType.TGA, ResourceType.TPC]),
            order=[
                SearchLocation.OVERRIDE,
                SearchLocation.TEXTURES_GUI,
                SearchLocation.TEXTURES_TPA,
                SearchLocation.TEXTURES_TPB,
                SearchLocation.TEXTURES_TPC
            ]
        )
        flatLocations = [item for sublist in locations.values() for item in sublist]
        if flatLocations:
            for location in flatLocations:
                displayPathStr = str(location.filepath.relative_to(self._installation.path()))
                locMenu = fileMenu.addMenu(displayPathStr)
                resourceMenuBuilder = ResourceItems(resources=[location])
                resourceMenuBuilder.build_menu(locMenu)

            fileMenu.addAction("Details...").triggered.connect(lambda: self._openDetails(flatLocations))

        contextMenu.addMenu(copyMenu)
        contextMenu.exec(self.ui.iconLabel.mapToGlobal(position))  # pyright: ignore[reportArgumentType]

    def _openDetails(self, locations: list[LocationResult]):
        selectionWindow = FileSelectionWindow(locations, self._installation)
        selectionWindow.show()
        selectionWindow.activateWindow()
        add_window(selectionWindow)

    def _copyIconTooltip(self):
        tooltipText = self._generateIconTooltip(asHtml=False)
        self._copyToClipboard(tooltipText)

    def _copyToClipboard(self, text: str):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def onUpdateIcon(self, *args, **kwargs):
        baseItem: int = self.ui.baseSelect.currentIndex()
        modelVariation: int = self.ui.modelVarSpin.value()
        textureVariation: int = self.ui.textureVarSpin.value()
        pixmap = self._installation.getItemIcon(baseItem, modelVariation, textureVariation)
        self.ui.iconLabel.setPixmap(QPixmap(pixmap))  # pyright: ignore[reportArgumentType]
        # Update the tooltip whenever the icon changes
        self.ui.iconLabel.setToolTip(self._generateIconTooltip(asHtml=True))

    def onAvailablePropertyListDoubleClicked(self):
        for item in self.ui.availablePropertyList.selectedItems():
            if item.childCount() != 0:
                continue
            self.addSelectedProperty()

    def onAssignedPropertyListDoubleClicked(self):
        self.editSelectedProperty()

    def onDelShortcut(self):
        if not self.ui.assignedPropertiesList.hasFocus():
            return
        self.remove_selectedProperty()

    @staticmethod
    def propertyName(
        installation: HTInstallation,
        prop: int,
    ) -> str:
        properties: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_ITEM_PROPERTIES)
        if properties is None:
            RobustLogger().error("Failed to retrieve ITEM_PROPERTIES 2DA.")
            return "Unknown"
        stringref: int | None = properties.get_row(prop).get_integer("name")
        if stringref is None:
            RobustLogger().error(f"Failed to retrieve name stringref for property {prop}.")
            return "Unknown"
        return installation.talktable().string(stringref)

    @staticmethod
    def subpropertyName(
        installation: HTInstallation,
        prop: int,
        subprop: int,
    ) -> None | str:
        """Gets the name of a subproperty of an item property.

        Args:
        ----
            installation: HTInstallation - The installation object
            prop: int - The property index
            subprop: int - The subproperty index.

        Returns:
        -------
            string - The name of the subproperty
        """
        properties: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_ITEM_PROPERTIES)
        if properties is None:
            RobustLogger().error("Failed to retrieve ITEM_PROPERTIES 2DA.")
            return None
        subtypeResname: str | None = properties.get_cell(prop, "subtyperesref")
        if not subtypeResname:
            RobustLogger().error(f"Failed to retrieve subtypeResname for property {prop}.")
            return None
        subproperties: TwoDA | None = installation.ht_get_cache_2da(subtypeResname)
        if subproperties is None:
            return None
        headerStrref: Literal["name", "string_ref"] = "name" if "name" in subproperties.get_headers() else "string_ref"
        nameStrref: int | None = subproperties.get_row(subprop).get_integer(headerStrref)
        return subproperties.get_cell(subprop, "label") if nameStrref is None else installation.talktable().string(nameStrref)

    @staticmethod
    def costName(
        installation: HTInstallation,
        cost: int,
        value: int,
    ) -> str | None:
        costtableList: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_IPRP_COSTTABLE)
        if costtableList is None:
            RobustLogger().error("Failed to retrieve IPRP_COSTTABLE 2DA.")
            return None

        costtable_name: str | None = costtableList.get_cell(cost, "name")
        if costtable_name is None:
            RobustLogger().error(f"Failed to retrieve costtable 'name' for cost '{cost}'.")
            return None

        costtable: TwoDA | None = installation.ht_get_cache_2da(costtable_name)
        if costtable is None:
            RobustLogger().error(f"Failed to retrieve '{costtable_name}' 2DA.")
            return None

        try:
            stringref: int | None = costtable.get_row(value).get_integer("name")
            if stringref is not None:
                return installation.talktable().string(stringref)
        except (IndexError, Exception):  # noqa: BLE001
            RobustLogger().warning("Could not get the costtable 2DA row/value", exc_info=True)
        return None

    @staticmethod
    def paramName(
        installation: HTInstallation,
        paramtable: int,
        param: int,
    ) -> str | None:
        RobustLogger().info(f"Attempting to get param name for paramtable: {paramtable}, param: {param}")

        # Get the IPRP_PARAMTABLE 2DA
        paramtable_list: TwoDA | None = installation.ht_get_cache_2da(HTInstallation.TwoDA_IPRP_PARAMTABLE)
        paramtable_2da: TwoDA | None = None
        if paramtable_list is None:
            RobustLogger().error("Failed to retrieve IPRP_PARAMTABLE 2DA.")
            return None

        try:
            # Get the specific parameter table 2DA
            table_resref = paramtable_list.get_cell(paramtable, "tableresref")
            RobustLogger().info(f"Retrieved table_resref: '{table_resref}' for paramtable: '{paramtable}'")

            paramtable_2da = installation.ht_get_cache_2da(table_resref)
            if paramtable_2da is None:
                RobustLogger().error(f"Failed to retrieve 2DA file: {table_resref}.")
                return None

            # Get the string reference for the parameter name
            param_row = paramtable_2da.get_row(param)
            stringref: int | None = param_row.get_integer("name")
            if stringref is None:
                RobustLogger().warning(f"Failed to get 'name' value for param '{param}' in '{table_resref}'")
                RobustLogger().info(f"Available columns in '{table_resref}': '{paramtable_2da.get_headers()}'")
                RobustLogger().info(f"Row data for param '{param}': '{param_row._data}'")  # noqa: SLF001
                return None

            # Get the actual string from the talk table
            result = installation.talktable().string(stringref)
            RobustLogger().info(f"Retrieved param name: {result} for stringref: {stringref}")
            return result  # noqa: TRY300

        except IndexError:
            RobustLogger().exception(f"paramtable: {paramtable}, param: {param}")
            RobustLogger().info(f"IPRP_PARAMTABLE height: {paramtable_list.get_height()}, width: {paramtable_list.get_width()}")
            RobustLogger().info(f"Available rows in IPRP_PARAMTABLE: {paramtable_list.get_labels()}")
        except KeyError:
            RobustLogger().exception("Likely missing column in 2DA.")
            if "paramtable_2da" in locals() and paramtable_2da is not None:
                RobustLogger().info(f"Available columns in '{table_resref}': {paramtable_2da.get_headers()}")
        except Exception:  # noqa: BLE001
            RobustLogger().exception("Unexpected error in param_name", exc_info=True)

        return None


class PropertyEditor(QDialog):
    def __init__(
        self,
        installation: HTInstallation,
        utiProperty: UTIProperty,
    ):
        """Initializes the UTI property editor dialog.

        Args:
        ----
            installation: {HTInstallation object}: The installation object
            utiProperty: {UTIProperty object}: The UTI property object

        Processing Logic:
        ----------------
            - Connects UI elements to callback functions
            - Populates cost and parameter lists from installation data
            - Populates upgrade dropdown from installation data
            - Sets initial values of textboxes from utiProperty.
        """
        super().__init__()
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        from toolset.uic.qtpy.dialogs.property import Ui_Dialog
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.costSelectButton.clicked.connect(self.selectCost)
        self.ui.parameterSelectButton.clicked.connect(self.selectParam)
        self.ui.costList.doubleClicked.connect(self.selectCost)
        self.ui.parameterList.doubleClicked.connect(self.selectParam)

        self._installation = installation
        self._utiProperty: UTIProperty = utiProperty

        costtableList = installation.ht_get_cache_2da(HTInstallation.TwoDA_IPRP_COSTTABLE)  # noqa: F841
        if costtableList is None:
            RobustLogger().warning("Failed to get IPRP_COSTTABLE")
            return
        if utiProperty.cost_table != 0xFF:  # noqa: PLR2004
            costtable = installation.ht_get_cache_2da(costtableList.get_cell(utiProperty.cost_table, "name"))
            if costtable is None:
                RobustLogger().warning(f"Failed to get costtable for name: {costtableList.get_cell(utiProperty.cost_table, 'name')}")
                return
            for i in range(costtable.get_height()):
                costName = UTIEditor.costName(installation, utiProperty.cost_table, i)
                if not costName:
                    RobustLogger().warning(f"No costName at index {i}")
                item = QListWidgetItem(costName)
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.ui.costList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

        if utiProperty.param1 != 0xFF:  # noqa: PLR2004
            paramList = installation.ht_get_cache_2da(HTInstallation.TwoDA_IPRP_PARAMTABLE)
            if paramList is None:
                RobustLogger().warning("Failed to get IPRP_PARAMTABLE")
                return

            paramtable_resref = paramList.get_cell(utiProperty.param1, "tableresref")
            if paramtable_resref is None:
                RobustLogger().warning(f"No tableresref found for param1: {utiProperty.param1}")
                return

            paramtable = installation.ht_get_cache_2da(paramtable_resref)
            if paramtable is None:
                RobustLogger().warning(f"Failed to get paramtable for resref: {paramtable_resref}")
                return

            for i in range(paramtable.get_height()):
                paramName = UTIEditor.paramName(installation, utiProperty.param1, i)
                if not paramName:
                    RobustLogger().warning(f"No paramName at index {i}")
                item = QListWidgetItem(paramName)
                item.setData(Qt.ItemDataRole.UserRole, i)
                self.ui.parameterList.addItem(item)  # pyright: ignore[reportArgumentType, reportCallIssue]

        upgrades = installation.ht_get_cache_2da(HTInstallation.TwoDA_UPGRADES)
        if upgrades is not None:
            upgrade_items = [
                upgrades.get_cell(i, "label").replace("_", " ").title()
                for i in range(upgrades.get_height())
            ]
        else:
            upgrade_items = []

        self.ui.upgradeSelect.setItems(
            upgrade_items,
            cleanupStrings=False
        )
        self.ui.upgradeSelect.setContext(upgrades, installation, HTInstallation.TwoDA_UPGRADES)
        if utiProperty.upgrade_type is not None:
            self.ui.upgradeSelect.setCurrentIndex(utiProperty.upgrade_type + 1)

        self.reloadTextboxes()

    def reloadTextboxes(self):
        """Reloads textboxes with property names."""
        propertyName: str = UTIEditor.propertyName(self._installation, self._utiProperty.property_name)
        self.ui.propertyEdit.setText(propertyName or "")

        subpropertyName: str | None = UTIEditor.subpropertyName(self._installation, self._utiProperty.property_name, self._utiProperty.subtype)
        self.ui.subpropertyEdit.setText(subpropertyName or "")

        costName: str | None = UTIEditor.costName(self._installation, self._utiProperty.cost_table, self._utiProperty.cost_value)
        self.ui.costEdit.setText(costName or "")

        paramName: str | None = UTIEditor.paramName(self._installation, self._utiProperty.param1, self._utiProperty.param1_value)
        self.ui.parameterEdit.setText(paramName or "")

    def selectCost(self):
        cur_item: QListWidgetItem | None = self.ui.costList.currentItem()  # pyright: ignore[reportAssignmentType]
        if not cur_item:
            return

        self._utiProperty.cost_value = cur_item.data(Qt.ItemDataRole.UserRole)
        self.reloadTextboxes()

    def selectParam(self):
        cur_item: QListWidgetItem | None = self.ui.parameterList.currentItem()  # pyright: ignore[reportAssignmentType]
        if not cur_item:
            return

        self._utiProperty.param1_value = cur_item.data(Qt.ItemDataRole.UserRole)
        self.reloadTextboxes()

    def utiProperty(self) -> UTIProperty:
        self._utiProperty.upgrade_type = self.ui.upgradeSelect.currentIndex() - 1
        if self.ui.upgradeSelect.currentIndex() == 0:
            self._utiProperty.upgrade_type = None
        return self._utiProperty
