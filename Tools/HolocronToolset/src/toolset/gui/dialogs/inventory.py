from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

import qtpy

from qtpy import QtCore
from qtpy.QtCore import QSize, QSortFilterProxyModel, QThread
from qtpy.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,
    QApplication,
    QDialog,
    QFrame,
    QMainWindow,
    QMenu,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
)

from pykotor.common.misc import EquipmentSlot, InventoryItem, ResRef
from pykotor.common.stream import BinaryReader
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tlk import read_tlk
from pykotor.resource.generics.uti import read_uti
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation
from utility.logger_util import RobustRootLogger

if TYPE_CHECKING:
    import os

    from typing import Sequence

    from qtpy.QtCore import QModelIndex, QPoint
    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
    from qtpy.QtWidgets import QLabel, QWidget

    from pykotor.extract.capsule import LazyCapsule
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.uti import UTI

_RESNAME_ROLE = QtCore.Qt.ItemDataRole.UserRole + 1
_FILEPATH_ROLE = QtCore.Qt.ItemDataRole.UserRole + 2
_SLOTS_ROLE = QtCore.Qt.ItemDataRole.UserRole + 3


class SlotMapping(NamedTuple):
    label: QLabel
    frame: DropFrame
    emptyImage: str


class InventoryEditor(QDialog):
    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        capsules: Sequence[LazyCapsule],
        folders: list[str],
        inventory: list[InventoryItem],
        equipment: dict[EquipmentSlot, InventoryItem],
        *,
        droid: bool = False,
        hide_equipment: bool = False,
        is_store: bool = False,
    ):
        """Initializes the inventory dialog.

        Args:
        ----
            parent (QWidget): Parent widget
            installation (HTInstallation): Toolset installation
            capsules (Sequence[LazyCapsule]): List of capsules
            folders (list[str]): List of folders
            inventory (list[InventoryItem]): List of inventory items
            equipment (dict[EquipmentSlot, InventoryItem]): Equipped items
            droid (bool): True if droid inventory
            hide_equipment (bool): True if equipment tab hidden
            is_store (bool): True if store inventory

        Processes Logic:
        ---------------
            1. Sets up UI elements
            2. Maps equipment slots to images
            3. Populates equipped items
            4. Populates inventory table
            5. Builds item trees
            6. Connects signals.
        """
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinimizeButtonHint)

        if qtpy.API_NAME == "PySide2":
            from toolset.uic.pyside2.dialogs.inventory import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PySide6":
            from toolset.uic.pyside6.dialogs.inventory import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt5":
            from toolset.uic.pyqt5.dialogs.inventory import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        elif qtpy.API_NAME == "PyQt6":
            from toolset.uic.pyqt6.dialogs.inventory import Ui_Dialog  # noqa: PLC0415  # pylint: disable=C0415
        else:
            raise ImportError(f"Unsupported Qt bindings: {qtpy.API_NAME}")

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.contentsTable.is_store = is_store

        self.ui.coreTree.setSortingEnabled(True)
        self.ui.coreTree.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder)
        self.ui.modulesTree.setSortingEnabled(True)
        self.ui.modulesTree.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder)
        self.ui.overrideTree.setSortingEnabled(True)
        self.ui.overrideTree.sortByColumn(0, QtCore.Qt.SortOrder.DescendingOrder)
        self.ui.coreSearchEdit.textEdited.connect(self.doSearch)
        self.ui.modulesSearchEdit.textEdited.connect(self.doSearch)
        self.ui.modulesSearchEdit.textEdited.connect(self.doSearch)

        self._installation: HTInstallation = installation
        self._capsules: list[Capsule] = capsules
        self._slotMap: dict[EquipmentSlot, SlotMapping] = {
            EquipmentSlot.IMPLANT: SlotMapping(self.ui.implantPicture, self.ui.implantFrame, ":/images/inventory/{}_implant.png"),
            EquipmentSlot.HEAD: SlotMapping(self.ui.headPicture, self.ui.headFrame, ":/images/inventory/{}_head.png"),
            EquipmentSlot.GAUNTLET: SlotMapping(self.ui.gauntletPicture, self.ui.gauntletFrame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.LEFT_ARM: SlotMapping(self.ui.armlPicture, self.ui.armlFrame, ":/images/inventory/{}_forearm_l.png"),
            EquipmentSlot.ARMOR: SlotMapping(self.ui.armorPicture, self.ui.armorFrame, ":/images/inventory/{}_armor.png"),
            EquipmentSlot.RIGHT_ARM: SlotMapping(self.ui.armrPicture, self.ui.armrFrame, ":/images/inventory/{}_forearm_r.png"),
            EquipmentSlot.LEFT_HAND: SlotMapping(self.ui.handlPicture, self.ui.handlFrame, ":/images/inventory/{}_hand_l.png"),
            EquipmentSlot.BELT: SlotMapping(self.ui.beltPicture, self.ui.beltFrame, ":/images/inventory/{}_belt.png"),
            EquipmentSlot.RIGHT_HAND: SlotMapping(self.ui.handrPicture, self.ui.handrFrame, ":/images/inventory/{}_hand_r.png"),
            EquipmentSlot.CLAW1: SlotMapping(self.ui.claw1Picture, self.ui.claw1Frame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.CLAW2: SlotMapping(self.ui.claw2Picture, self.ui.claw2Frame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.CLAW3: SlotMapping(self.ui.claw3Picture, self.ui.claw3Frame, ":/images/inventory/{}_gauntlet.png"),
            EquipmentSlot.HIDE: SlotMapping(self.ui.hidePicture, self.ui.hideFrame, ":/images/inventory/{}_armor.png"),
        }
        self._droid: bool = droid
        self.inventory: list[InventoryItem] = inventory
        self.equipment: dict[EquipmentSlot, InventoryItem] = equipment
        self.is_store: bool = is_store

        self.ui.implantFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.IMPLANT, resname, filepath, name))
        self.ui.headFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.HEAD, resname, filepath, name))
        self.ui.gauntletFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.GAUNTLET, resname, filepath, name))
        self.ui.armlFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.LEFT_ARM, resname, filepath, name))
        self.ui.armorFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.ARMOR, resname, filepath, name))
        self.ui.armrFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.RIGHT_ARM, resname, filepath, name))
        self.ui.handlFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.LEFT_HAND, resname, filepath, name))
        self.ui.beltFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.BELT, resname, filepath, name))
        self.ui.handrFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.RIGHT_HAND, resname, filepath, name))
        self.ui.hideFrame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.HIDE, resname, filepath, name))
        self.ui.claw1Frame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW1, resname, filepath, name))
        self.ui.claw2Frame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW2, resname, filepath, name))
        self.ui.claw3Frame.itemDropped.connect(lambda filepath, resname, name: self.setEquipment(EquipmentSlot.CLAW3, resname, filepath, name))

        self.ui.implantFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.implantFrame, point))
        self.ui.headFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.headFrame, point))
        self.ui.gauntletFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.gauntletFrame, point))
        self.ui.armlFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.armlFrame, point))
        self.ui.armorFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.armorFrame, point))
        self.ui.armrFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.armrFrame, point))
        self.ui.handlFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.handlFrame, point))
        self.ui.beltFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.beltFrame, point))
        self.ui.handrFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.handrFrame, point))
        self.ui.hideFrame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.hideFrame, point))
        self.ui.claw1Frame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.claw1Frame, point))
        self.ui.claw2Frame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.claw2Frame, point))
        self.ui.claw3Frame.customContextMenuRequested.connect(lambda point: self.openItemContextMenu(self.ui.claw3Frame, point))

        self.ui.okButton.clicked.connect(self.accept)
        self.ui.cancelButton.clicked.connect(self.reject)

        self.ui.implantFrame.slot = EquipmentSlot.IMPLANT
        self.ui.headFrame.slot = EquipmentSlot.HEAD
        self.ui.gauntletFrame.slot = EquipmentSlot.GAUNTLET
        self.ui.armlFrame.slot = EquipmentSlot.LEFT_ARM
        self.ui.armorFrame.slot = EquipmentSlot.ARMOR
        self.ui.armrFrame.slot = EquipmentSlot.RIGHT_ARM
        self.ui.handlFrame.slot = EquipmentSlot.LEFT_HAND
        self.ui.beltFrame.slot = EquipmentSlot.BELT
        self.ui.handrFrame.slot = EquipmentSlot.RIGHT_HAND
        self.ui.hideFrame.slot = EquipmentSlot.HIDE
        self.ui.claw1Frame.slot = EquipmentSlot.CLAW1
        self.ui.claw2Frame.slot = EquipmentSlot.CLAW2
        self.ui.claw3Frame.slot = EquipmentSlot.CLAW3

        self.ui.contentsTable.setColumnWidth(0, 64)

        for slot in (slot for slot in EquipmentSlot if slot in self._slotMap):
            image = self._slotMap[slot].emptyImage.format("droid" if droid else "human")
            self._slotMap[slot].label.setPixmap(QPixmap(image))

        for slot, item in self.equipment.items():
            self.setEquipment(slot, str(item.resref))

        for item in self.inventory:
            self.ui.contentsTable.addItem(str(item.resref), item.droppable, item.infinite)

        self.ui.tabWidget_2.setVisible(not hide_equipment)

        self.buildItems()

    def accept(self):
        super().accept()
        self.inventory = []
        for i in range(self.ui.contentsTable.rowCount()):
            tableItem: ItemContainer = self.ui.contentsTable.item(i, 1)  # FIXME(th3w1zard1): QTableWidgetItem | None cannot be assigned to ItemContainer, needs a .data(role) call.
            self.inventory.append(InventoryItem(ResRef(tableItem.resname), tableItem.droppable, tableItem.infinite))

        self.equipment = {}
        widget: DropFrame
        for widget in self.ui.standardEquipmentTab.children() + self.ui.naturalEquipmentTab.children():  # type: ignore[reportGeneralTypeIssues]
            # HACK: isinstance is not working (possibly due to how DropFrame is imported in _ui.py file.
            # Also make sure there is an item in the slot otherwise the GFF will create a struct for each slot.
            if "DropFrame" in widget.__class__.__name__ and widget.resname:
                self.equipment[widget.slot] = InventoryItem(ResRef(widget.resname), widget.droppable, widget.infinite)

    def buildItems(self):
        """Builds item trees from a dialog.

        Args:
        ----
            self: {The class instance}.

        Returns:
        -------
            None: {Does not return anything}

        Processing Logic:
        ----------------
            - Opens an ItemBuilderDialog
            - Checks if dialog was accepted
            - Caches core items model if not already cached
            - Sets core, modules and override trees models from the dialog.
        """
        itemBuilderDialog = ItemBuilderDialog(self, self._installation, self._capsules)
        if itemBuilderDialog.exec_():
            if self._installation.cacheCoreItems is None:
                coreModel = itemBuilderDialog.coreModel
                self._installation.cacheCoreItems = coreModel
            else:
                coreModel = self._installation.cacheCoreItems
            self.ui.coreTree.setModel(coreModel.proxyModel())  # FIXME(th3w1zard1): coreModel.proxyModel() needs a .data(role) call.

            self.ui.modulesTree.setModel(itemBuilderDialog.modulesModel.proxyModel())
            self.ui.overrideTree.setModel(itemBuilderDialog.overrideModel.proxyModel())
        else:
            self.reject()

    def getItemImage(self, uti: UTI) -> QPixmap:
        return self._installation.getItemIconFromUTI(uti)

    def getItem(
        self,
        resname: str,
        filepath: os.PathLike | str,
    ) -> tuple[str, str, UTI]:
        """Gets item resource data from filepath or installation.

        Args:
        ----
            resname: str - Name of the resource
            filepath: str - Path to resource file

        Returns:
        -------
            filepath: str - Path to resource file
            name: str - Name of the item
            uti: UTI - Universal type identifier object

        Processing Logic:
        ----------------
            - If no filepath is provided, get resource from installation
            - If filepath ends with .rim/.mod/.erf, get resource from capsule file
            - If filepath ends with .bif, get resource from installation searching CHITIN
            - Else load resource directly from filepath
            - Return filepath, name extracted from UTI, and UTI object
        """
        uti: UTI | None = None
        name: str = ""
        if not filepath:
            result: ResourceResult | None = self._installation.resource(resname, ResourceType.UTI)
            if result is None:
                raise FileNotFoundError
            uti = read_uti(result.data)
            filepath = result.filepath
            name = self._installation.string(uti.name, "[No Name]")
        elif is_capsule_file(filepath):
            uti_resource: bytes | None = Capsule(filepath).resource(resname, ResourceType.UTI)
            if uti_resource is None:
                raise FileNotFoundError
            uti = read_uti(uti_resource)
            name = self._installation.string(uti.name, "[No Name]")
        elif is_bif_file(filepath):
            bif_result = self._installation.resource(resname, ResourceType.UTI, [SearchLocation.CHITIN])
            if bif_result is None:
                raise FileNotFoundError
            uti = read_uti(bif_result.data)
            name = self._installation.string(uti.name, "[No Name]")
        else:
            uti = read_uti(BinaryReader.load_file(filepath))
        return str(filepath), name, uti

    def setEquipment(
        self,
        slot: EquipmentSlot,
        resname: str,
        filepath: str = "",
        name: str = "",
    ):
        # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
        """Sets equipment in a given slot.

        Args:
        ----
            slot (EquipmentSlot): The slot to set the equipment
            resname (str): The resource name of the equipment
            filepath (str): The file path of the equipment image
            name (str): The name of the equipment

        Processing Logic:
        ----------------
            - Gets the label and frame for the given slot
            - If resname is provided:
                - Gets the filepath, name and uti for the item from the item database
                - Sets the tooltip, pixmap and calls setItem on the slot frame
            - Else:
                - Sets an empty image, clears the tooltip.
        """
        slotPicture: QLabel = self._slotMap[slot].label
        if resname:
            try:
                filepath, name, uti = self.getItem(resname, filepath)
            except FileNotFoundError:
                RobustRootLogger.exception(f"Failed to get the equipment item '{resname}.uti' for the InventoryEditor")
                return

            slotPicture.setToolTip(f"{resname}\n{filepath}\n{name}")
            slotPicture.setPixmap(self.getItemImage(uti))
            slotFrame: DropFrame = self._slotMap[slot].frame

            slotFrame.setItem(resname, filepath, name, False, False)
        else:
            image: str = self._slotMap[slot].emptyImage.format("droid" if self._droid else "human")
            slotPicture.setToolTip("")
            slotPicture.setPixmap(QPixmap(image))

    def doSearch(self, text: str):
        self.ui.coreSearchEdit.setText(text)
        self.ui.modulesSearchEdit.setText(text)
        self.ui.overrideSearchEdit.setText(text)
        self.ui.coreTree.model().setFilterFixedString(text)
        self.ui.modulesTree.model().setFilterFixedString(text)
        self.ui.overrideTree.model().setFilterFixedString(text)

    def openItemContextMenu(
        self,
        widget: DropFrame | ItemContainer,
        point: QPoint,
    ):
        """Opens an item context menu at a given point.

        Args:
        ----
            widget: ItemContainer: Widget the menu is for
            point: QPoint: Point to open menu at

        Processing Logic:
        ----------------
            - Create a QMenu at the given point
            - Add actions like Infinite, Droppable based on widget properties
            - Add Remove Item action
            - Add No Item action if no item present
            - Add Set Item ResRef action
            - Execute the menu.
        """
        menu = QMenu(self)

        if widget.hasItem:
            if self.is_store:
                infiniteAction = QAction("Infinite")
                infiniteAction.setCheckable(True)
                infiniteAction.setChecked(widget.infinite)
                infiniteAction.triggered.connect(widget.toggleInfinite)
                menu.addAction(infiniteAction)
            else:
                droppableAction = QAction("Droppable")
                droppableAction.setCheckable(True)
                droppableAction.setChecked(widget.droppable)
                droppableAction.triggered.connect(widget.toggleDroppable)
                menu.addAction(droppableAction)

            removeAction = QAction("Remove Item")
            removeAction.triggered.connect(widget.removeItem)

            menu.addSeparator()
            menu.addAction(removeAction)
        else:
            noItemAction = QAction("No Item")
            noItemAction.setEnabled(False)
            menu.addAction(noItemAction)

        menu.addSeparator()
        # TODO:
        #setItemAction = QAction("Set Item ResRef")
        #setItemAction.triggered.connect(lambda: self.promptSetItemResRefDialog(widget))
        #menu.addAction(setItemAction)

        menu.exec_(widget.mapToGlobal(point))

    def promptSetItemResRefDialog(self, widget: DropFrame):
        dialog = SetItemResRefDialog()

        if dialog.exec_():
            self.setEquipment(widget.slot, dialog.resref())


class ItemContainer:
    def __init__(
        self,
        droppable: bool = False,
        infinite: bool = False,
    ):
        self.resname: str = ""
        self.filepath: str = ""
        self.name: str = ""
        self.hasItem: bool = False
        self.droppable: bool = droppable
        self.infinite: bool = infinite

    def removeItem(self):
        self.resname = ""
        self.filepath = ""
        self.name = ""
        self.hasItem = False
        self.droppable = False
        self.infinite = False

    def setItem(
        self,
        resname: str,
        filepath: str,
        name: str,
        droppable: bool,
        infinite: bool,
    ):
        self.resname = resname
        self.filepath = filepath
        self.name = name
        self.hasItem = True
        self.droppable = droppable
        self.infinite = infinite

    def toggleDroppable(self):
        self.droppable = not self.droppable

    def toggleInfinite(self):
        self.infinite = not self.infinite


class DropFrame(ItemContainer, QFrame):
    itemDropped = QtCore.Signal(object, object, object)

    def __init__(self, parent: QWidget | None):
        QFrame.__init__(self)
        ItemContainer.__init__(self)
        self.setFrameShape(QFrame.Shape.Box)
        self.setAcceptDrops(True)
        self.slot: EquipmentSlot = EquipmentSlot.HIDE

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events for slots.

        Args:
        ----
            e: QDragEnterEvent - drag enter event

        Processing Logic:
        ----------------
            - Check if drag source is a QTreeView
            - Get source model from proxy model
            - Map selected index from proxy to source model
            - Get item from source model index
            - Accept drag if item slots match receiver slot.
        """
        if not isinstance(event.source(), QTreeView):
            return
        tree: QTreeView | None = event.source()
        proxyModel: QSortFilterProxyModel = tree.model()
        index = proxyModel.mapToSource(tree.selectedIndexes()[0])
        model: ItemModel = proxyModel.sourceModel()
        item: QStandardItem | None = model.itemFromIndex(index)
        if not item.data(_SLOTS_ROLE) & self.slot.value:
            return
        event.accept()

    def dragMoveEvent(self, event: QDragMoveEvent):
        """Moves an item between slots if the drag and drop events match.

        Args:
        ----
            e: QDragMoveEvent: The drag move event

        Processing Logic:
        ----------------
            - Check if drag source is a QTreeView
            - Get the QTreeView, QSortFilterProxyModel and ItemModel
            - Map the selected index from proxy to source model
            - Get the item from the mapped index
            - Check if item's slots match the target slot
            - Accept the drag move event if slots match.
        """
        if not isinstance(event.source(), QTreeView):
            return
        tree: QTreeView = event.source()
        proxyModel: QSortFilterProxyModel = tree.model()
        model: ItemModel = proxyModel.sourceModel()
        index = proxyModel.mapToSource(tree.selectedIndexes()[0])
        item: QStandardItem | None = model.itemFromIndex(index)
        if not item.data(_SLOTS_ROLE) & self.slot.value:
            return
        event.accept()

    def dropEvent(self, event: QDropEvent):
        """Handles dropped items from a tree view onto the widget.

        Args:
        ----
            e: QDropEvent: The drop event

        Processes dropped items:
            - Checks if the drop source is a QTreeView
            - Sets the drop action to Copy
            - Gets the source tree view and model
            - Maps the selected index to the source model
            - Gets the dropped item
            - Checks if the item's slots match the widget's slot
            - Accepts the drop if they match
            - Sets the new item on the widget
            - Emits a signal with the new item details.
        """
        if isinstance(event.source(), QTreeView):
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)

            tree: QTreeView | None = event.source()  # type: ignore[]
            proxyModel: QSortFilterProxyModel = tree.model()
            index = proxyModel.mapToSource(tree.selectedIndexes()[0])
            model: ItemModel | None = proxyModel.sourceModel()
            item: QStandardItem | None = model.itemFromIndex(index)
            if item.data(_SLOTS_ROLE) & self.slot.value:
                event.accept()
                self.setItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text(), False, False)
                self.itemDropped.emit(self.filepath, self.resname, self.name)

    def removeItem(self):
        ItemContainer.removeItem(self)
        self.window().setEquipment(self.slot, "")  # type: ignore[]

    def toggleDroppable(self):
        ItemContainer.toggleDroppable(self)


class InventoryTable(QTableWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.itemChanged.connect(self.resnameChanged)
        self.customContextMenuRequested.connect(self.openContextMenu)
        self.is_store: bool = False

    def addItem(
        self,
        resname: str,
        droppable: bool,
        infinite: bool,
    ):
        """Adds an item to the inventory table.

        Args:
        ----
            resname: The resource name of the item to add
            droppable: Whether the item can be dropped
            infinite: Whether the item stack is infinite

        Processing Logic:
        ----------------
            - Gets the row count and inserts a new row
            - Gets the item info from the window
            - Creates icon and name table widgets
            - Creates a custom resname table widget
            - Sets the row with the item info.
        """
        rowID: int = self.rowCount()
        self.insertRow(rowID)
        filepath, name, uti = self.window().getItem(resname, "")
        iconItem: QTableWidgetItem = self._set_uti(uti)
        nameItem = QTableWidgetItem(name)
        nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
        resnameItem = InventoryTableResnameItem(resname, filepath, name, droppable, infinite)
        self._set_row(rowID, iconItem, resnameItem, nameItem)

    def dropEvent(self, event: QDropEvent | None):
        """Handles drag and drop events on the inventory table.

        Args:
        ----
            e: QDropEvent(None): The drop event

        Processing Logic:
        ----------------
            - Check if drop source is a QTreeView
            - Set drop action to Copy
            - Get selected item from source tree view
            - Insert new row at end of table
            - Populate row with icon, resname and name from dropped item.
        """
        if isinstance(event.source(), QTreeView):
            event.setDropAction(QtCore.Qt.DropAction.CopyAction)

            tree: QTreeView = event.source()
            proxyModel: QSortFilterProxyModel = tree.model()
            model: ItemModel = proxyModel.sourceModel()
            index: QModelIndex = proxyModel.mapToSource(tree.selectedIndexes()[0])
            item: QStandardItem = model.itemFromIndex(index)
            event.accept()
            rowID: int = self.rowCount()
            self.insertRow(rowID)
            filepath, name, uti = self.window().getItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE))
            iconItem: QTableWidgetItem = self._set_uti(uti)
            nameItem = QTableWidgetItem(item.text())
            nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            resnameItem = InventoryTableResnameItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text(), False, False)
            self._set_row(rowID, iconItem, resnameItem, nameItem)

    def _set_row(
        self,
        rowID: int,
        iconItem: QTableWidgetItem,
        resnameItem: InventoryTableResnameItem,
        nameItem: QTableWidgetItem,
    ):
        self.setItem(rowID, 0, iconItem)
        self.setItem(rowID, 1, resnameItem)
        self.setItem(rowID, 2, nameItem)

    def _set_uti(self, uti: UTI) -> QTableWidgetItem:
        pixmap = self.window().getItemImage(uti)
        result = QTableWidgetItem(QIcon(pixmap), "")
        result.setSizeHint(QSize(48, 48))
        result.setFlags(result.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
        return result

    def resnameChanged(self, tableItem: QTableWidgetItem):
        """Changes the name of an item in the inventory table.

        Args:
        ----
            tableItem (QTableWidgetItem): The item whose name is to be changed.

        Processing Logic:
        ----------------
            - Checks if the item passed is an InventoryTableResnameItem
            - Gets the filepath, name and UTI of the item from the window
            - Sets the new name, filepath and other properties of the item
            - Sets the icon of the item using the UTI
            - Sets the non-editable name in the name column.
        """
        if isinstance(tableItem, InventoryTableResnameItem):
            filepath, name, uti = self.window().getItem(tableItem.text(), "")
            icon = QIcon(self.window().getItemImage(uti))

            tableItem.setItem(tableItem.text(), filepath, name, tableItem.droppable, tableItem.infinite)
            self.item(tableItem.row(), 0).setIcon(icon)
            nameItem = QTableWidgetItem(name)
            nameItem.setFlags(nameItem.flags() ^ QtCore.Qt.ItemFlag.ItemIsEditable)
            self.setItem(tableItem.row(), 2, nameItem)

    def openContextMenu(self, point: QPoint):
        """Opens context menu for selected item.

        Args:
        ----
            point (QPoint): Point where to open the menu.

        Processing Logic:
        ----------------
            - Check if any item is selected
            - Get the selected item container
            - Create menu and add actions based on item type
            - Execute menu at the given point.
        """
        if len(self.selectedIndexes()) == 0:
            return

        itemContainer: QTableWidgetItem | None = self.item(self.selectionModel().selectedRows(1)[0].row(), 1)
        if isinstance(itemContainer, ItemContainer):
            menu = QMenu(self)
            if self.is_store:
                infiniteAction = QAction("Infinite")
                infiniteAction.setCheckable(True)
                infiniteAction.setChecked(itemContainer.infinite)
                infiniteAction.triggered.connect(itemContainer.toggleInfinite)
                menu.addAction(infiniteAction)
            else:
                droppableAction = QAction("Droppable")
                droppableAction.setCheckable(True)
                droppableAction.setChecked(itemContainer.droppable)
                droppableAction.triggered.connect(itemContainer.toggleDroppable)
                menu.addAction(droppableAction)

            removeAction = QAction("Remove Item")
            removeAction.triggered.connect(itemContainer.removeItem)

            menu.addSeparator()
            menu.addAction(removeAction)

            menu.exec_(self.mapToGlobal(point))


class InventoryTableResnameItem(ItemContainer, QTableWidgetItem):
    def __init__(
        self,
        resname: str,
        filepath: str,
        name: str,
        droppable: bool,
        infinite: bool,
    ):
        ItemContainer.__init__(self, droppable, infinite)
        QTableWidgetItem.__init__(self, resname)
        self.setItem(resname, filepath, name, droppable, infinite)

    def removeItem(self):
        self.tableWidget().removeRow(self.row())


class ItemBuilderDialog(QDialog):  # FIXME(th3w1zard1): There is UI code used in this builder!!! Should only manage UI code in main thread.
    """Popup dialog responsible for extracting a list of resources from the game files."""

    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        capsules: list[Capsule],
    ):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowStaysOnTopHint & ~QtCore.Qt.WindowContextHelpButtonHint & ~QtCore.Qt.WindowMinMaxButtonsHint)


        self._progressBar = QProgressBar(self)
        self._progressBar.setMaximum(0)
        self._progressBar.setValue(0)
        self._progressBar.setTextVisible(False)

        self.resize(250, 40)
        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self._progressBar)

        self.setWindowTitle("Building Item Lists...")

        main_window = next(
            (
                widget
                for widget in QApplication.topLevelWidgets()
                if isinstance(widget, QMainWindow)
                and widget.__class__.__name__ == "ToolWindow"
            ),
            None,
        )
        self.coreModel = ItemModel(main_window)
        self.modulesModel = ItemModel(parent)
        self.overrideModel = ItemModel(parent)
        self._tlk: TLK = read_tlk(CaseAwarePath(installation.path(), "dialog.tlk"))
        self._installation: HTInstallation = installation
        self._capsules: list[Capsule] = capsules

        self._worker = ItemBuilderWorker(installation, capsules)
        self._worker.utiLoaded.connect(self.utiLoaded)
        self._worker.finished.connect(self.finished)
        self._worker.start()

    def utiLoaded(self, uti: UTI, result: ResourceResult):
        baseitems = self._installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
        name = result.resname if uti is None else self._installation.string(uti.name, result.resname)

        # Split category by base item:
        # TODO(th3w1zard1): What is this for and why is it commented out?
        #  categoryNameID = baseitems.get_row(uti.base_item).get_integer("name")
        #  categoryLabel = baseitems.get_cell(uti.base_item, "label")
        #  category = self._tlk.get(categoryNameID).text if self._tlk.get(categoryNameID) is not None else categoryLabel

        slots: int = 0 if uti is None else baseitems.get_row(uti.base_item).get_integer("equipableslots", 0)
        category: str = self.getCategory(uti)

        if result.filepath.suffix.lower() in {".bif", ".key"}:
            self.coreModel.addItem(result.resname, category, result.filepath, name, slots)
        elif is_capsule_file(result.filepath):
            self.modulesModel.addItem(result.resname, category, result.filepath, name, slots)
        else:
            self.overrideModel.addItem(result.resname, category, result.filepath, name, slots)

    def finished(self):
        self.accept()

    def getCategory(self, uti: UTI | None) -> str:
        """Gets the category for an item based on its equipable slots.

        Args:
        ----
            uti: {UTI object}: Item to get category for

        Returns:
        -------
            str: Category name for the item

        Processing Logic:
        ----------------
            - Check equipable slots of item against slot bitmasks
            - Return category based on first matching slot
            - Return default categories if no slots match.
        """
        if uti is None:
            slots: int = -1
            droid: bool = False
        else:
            baseitems: TwoDA = self._installation.htGetCache2DA(HTInstallation.TwoDA_BASEITEMS)
            slots = baseitems.get_row(uti.base_item).get_integer("equipableslots", 0)
            droid = baseitems.get_row(uti.base_item).get_integer("droidorhuman", 0) == 2

        if slots & (EquipmentSlot.CLAW1.value | EquipmentSlot.CLAW2.value | EquipmentSlot.CLAW3.value):
            return "Creature Claw"
        if slots & EquipmentSlot.HEAD.value:
            return "Droid Sensors" if droid else "Headgear"
        if slots & EquipmentSlot.IMPLANT.value:
            return "Droid Utilities" if droid else "Implants"
        if slots & EquipmentSlot.GAUNTLET.value and not droid:
            return "Gauntlets"
        if slots & EquipmentSlot.LEFT_ARM.value:
            return "Droid Special Weapons" if droid else "Shields"
        if slots & EquipmentSlot.ARMOR.value:
            return "Droid Plating" if droid else "Armor"
        if slots & EquipmentSlot.LEFT_HAND.value:
            return "Weapons (Single)"
        if slots & EquipmentSlot.RIGHT_HAND.value:
            return "Weapons (Double)"
        if slots & EquipmentSlot.BELT.value:
            return "Droid Shields" if droid else "Belts"
        if slots & EquipmentSlot.HIDE.value:
            return "Creature Hide"
        if slots == 0:  # sourcery skip: assign-if-exp, reintroduce-else
            return "Miscellaneous"
        return "Unknown"


class ItemBuilderWorker(QThread):
    utiLoaded = QtCore.Signal(object, object)
    finished = QtCore.Signal()

    def __init__(self, installation: HTInstallation, capsules: list[Capsule]):
        super().__init__()
        self._installation: HTInstallation = installation
        self._capsules: list[Capsule] = capsules

    def run(self):
        """Runs the resource loading process.

        Args:
        ----
            self: The object instance

        Processing Logic:
        ----------------
            - Queries a list of resource identifiers from the installation
            - Extends the queries list with override resources
            - Extends the queries list with resources from each capsule
            - Requests the resources from the installation
            - Tries to read each result as a UTI
            - Emits signals for each loaded UTI and when finished.
        """
        queries: list[ResourceIdentifier] = []
        if self._installation.cacheCoreItems is None:
            queries.extend(
                resource.identifier()
                for resource in self._installation.core_resources() if resource.restype() is ResourceType.UTI
            )
        queries.extend(
            resource.identifier()
            for resource in self._installation.override_resources() if resource.restype() is ResourceType.UTI
        )
        for capsule in self._capsules:
            queries.extend(
                resource.identifier()
                for resource in capsule if resource.restype() is ResourceType.UTI
            )
        results: dict[ResourceIdentifier, ResourceResult | None] = self._installation.resources(
            queries,
            [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.CUSTOM_MODULES],
            capsules=self._capsules,
        )
        for identifier, resource_result in results.items():
            if resource_result is None:
                RobustRootLogger().warning("Could not find UTI resource '%s'", identifier)
                continue
            uti: UTI | None = None
            try:  # FIXME(th3w1zard1): this section seems to crash often.
                uti = read_uti(resource_result.data)
            except Exception:  # pylint: disable=W0718  # noqa: BLE001
                RobustRootLogger().exception("Error reading UTI resource while building items.")
            else:
                self.utiLoaded.emit(uti, resource_result)
        self.finished.emit()


class ItemModel(QStandardItemModel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self._categoryItems: dict[str, QStandardItem] = {}
        self._proxyModel = QSortFilterProxyModel(self)
        self._proxyModel.setSourceModel(self)
        self._proxyModel.setRecursiveFilteringEnabled(True)  # type: ignore[arg-type]
        self._proxyModel.setFilterCaseSensitivity(False if qtpy.API_NAME in ("PyQt5", "PySide2") else QtCore.Qt.CaseInsensitive)  # type: ignore[arg-type]

    def proxyModel(self) -> QSortFilterProxyModel:
        return self._proxyModel

    def _getCategoryItem(self, category: str) -> QStandardItem:
        if category not in self._categoryItems:
            categoryItem = QStandardItem(category)
            categoryItem.setSelectable(False)
            self._categoryItems[category] = categoryItem
            self.appendRow(categoryItem)
        return self._categoryItems[category]

    def addItem(
        self,
        resname: str,
        category: str,
        filepath: os.PathLike | str,
        name: str,
        slots: int,
    ):
        """Adds an item to the resource list.

        Args:
        ----
            resname: Name of the resource in one line.
            category: Category of the item in one line.
            filepath: Path to the resource file in one line.
            name: Optional display name in one line.
            slots: Number of slots the item uses in one line.

        Returns:
        -------
            None: No value is returned in one line.

        Processing Logic:
        ----------------
            - The function creates a QStandardItem with the name or resource name.
            - Tooltip, filepath, resname, and slots are set as item data.
            - The item is appended to the category item in the model.
        """
        item = QStandardItem(name or resname)
        item.setToolTip(f"{resname}\n{filepath}\n{name}")
        item.setData(filepath, _FILEPATH_ROLE)
        item.setData(resname, _RESNAME_ROLE)
        item.setData(slots, _SLOTS_ROLE)
        self._getCategoryItem(category).appendRow(item)


class SetItemResRefDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)

        from editors import ui_setitemresref  # TODO: ??

        self.ui = ui_setitemresref.Ui_Dialog()
        self.ui.setupUi(self)

    def resref(self) -> str:
        return self.ui.resrefEdit.text()
