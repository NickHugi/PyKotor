from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtCore
from qtpy.QtCore import (
    QSize,
    QSortFilterProxyModel,
    QThread,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QIcon, QPixmap, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QDialog,
    QFrame,
    QMenu,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QTreeView,
    QVBoxLayout,
)

from pykotor.common.misc import EquipmentSlot, InventoryItem, ResRef
from pykotor.extract.capsule import Capsule
from pykotor.extract.installation import SearchLocation
from pykotor.resource.formats.tlk import read_tlk
from pykotor.resource.generics.uti import read_uti
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_bif_file, is_capsule_file
from pykotor.tools.path import CaseAwarePath
from toolset.data.installation import HTInstallation

if TYPE_CHECKING:
    import os

    from typing import Sequence

    from qtpy.QtCore import (
        QAbstractItemModel,  # pyright: ignore[reportPrivateImportUsage]
        QModelIndex,
        QObject,
        QPoint,
    )
    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
    from qtpy.QtWidgets import QLabel, QWidget

    from pykotor.extract.capsule import LazyCapsule
    from pykotor.extract.file import ResourceIdentifier, ResourceResult
    from pykotor.resource.formats.tlk import TLK
    from pykotor.resource.formats.twoda.twoda_data import TwoDA
    from pykotor.resource.generics.uti import UTI

_RESNAME_ROLE = Qt.ItemDataRole.UserRole + 1
_FILEPATH_ROLE = Qt.ItemDataRole.UserRole + 2
_SLOTS_ROLE = Qt.ItemDataRole.UserRole + 3


class SlotMapping(NamedTuple):
    label: QLabel
    frame: DropFrame
    empty_image: str


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
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinimizeButtonHint
        )
        from toolset.uic.qtpy.dialogs.inventory import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.contentsTable.is_store = is_store

        self.ui.coreTree.setSortingEnabled(True)
        self.ui.coreTree.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self.ui.modulesTree.setSortingEnabled(True)
        self.ui.modulesTree.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self.ui.overrideTree.setSortingEnabled(True)
        self.ui.overrideTree.sortByColumn(0, Qt.SortOrder.DescendingOrder)
        self.ui.coreSearchEdit.textEdited.connect(self.do_search)
        self.ui.modulesSearchEdit.textEdited.connect(self.do_search)
        self.ui.overrideSearchEdit.textEdited.connect(self.do_search)

        self._installation: HTInstallation = installation
        self._capsules: Sequence[LazyCapsule] = capsules
        self._slow_map: dict[EquipmentSlot, SlotMapping] = {
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

        self.ui.implantFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.IMPLANT, resname, filepath, name))
        self.ui.headFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.HEAD, resname, filepath, name))
        self.ui.gauntletFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.GAUNTLET, resname, filepath, name))
        self.ui.armlFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.LEFT_ARM, resname, filepath, name))
        self.ui.armorFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.ARMOR, resname, filepath, name))
        self.ui.armrFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.RIGHT_ARM, resname, filepath, name))
        self.ui.handlFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.LEFT_HAND, resname, filepath, name))
        self.ui.beltFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.BELT, resname, filepath, name))
        self.ui.handrFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.RIGHT_HAND, resname, filepath, name))
        self.ui.hideFrame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.HIDE, resname, filepath, name))
        self.ui.claw1Frame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.CLAW1, resname, filepath, name))
        self.ui.claw2Frame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.CLAW2, resname, filepath, name))
        self.ui.claw3Frame.sig_item_dropped.connect(lambda filepath, resname, name: self.set_equipment(EquipmentSlot.CLAW3, resname, filepath, name))

        self.ui.implantFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.implantFrame, point))
        self.ui.headFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.headFrame, point))
        self.ui.gauntletFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.gauntletFrame, point))
        self.ui.armlFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.armlFrame, point))
        self.ui.armorFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.armorFrame, point))
        self.ui.armrFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.armrFrame, point))
        self.ui.handlFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.handlFrame, point))
        self.ui.beltFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.beltFrame, point))
        self.ui.handrFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.handrFrame, point))
        self.ui.hideFrame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.hideFrame, point))
        self.ui.claw1Frame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.claw1Frame, point))
        self.ui.claw2Frame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.claw2Frame, point))
        self.ui.claw3Frame.customContextMenuRequested.connect(lambda point: self.open_item_context_menu(self.ui.claw3Frame, point))

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

        for slot in (slot for slot in EquipmentSlot if slot in self._slow_map):
            image = self._slow_map[slot].empty_image.format("droid" if droid else "human")
            self._slow_map[slot].label.setPixmap(QPixmap(image))

        for slot, item in self.equipment.items():
            self.set_equipment(slot, str(item.resref))

        for item in self.inventory:
            try:
                self.ui.contentsTable.add_item(str(item.resref), droppable=item.droppable, infinite=item.infinite)
            except FileNotFoundError:  # noqa: PERF203
                RobustLogger().error(f"{item.resref}.uti did not exist in the installation", exc_info=True)
            except (OSError, ValueError):  # noqa: PERF203
                RobustLogger().error(f"{item.resref}.uti is corrupted", exc_info=True)

        self.ui.tabWidget_2.setVisible(not hide_equipment)

        if self._installation.cache_core_items is not None:
            self._installation.cache_core_items._proxy_model = QSortFilterProxyModel()  # noqa: SLF001
        self.build_items()

    def accept(self):
        super().accept()
        self.inventory.clear()
        for i in range(self.ui.contentsTable.rowCount()):
            table_item: QTableWidgetItem | None = self.ui.contentsTable.item(i, 1)
            if not isinstance(table_item, ItemContainer):
                continue
            self.inventory.append(InventoryItem(ResRef(table_item.resname), table_item.droppable, table_item.infinite))

        self.equipment.clear()
        widget: DropFrame | QObject
        for widget in self.ui.standardEquipmentTab.children() + self.ui.naturalEquipmentTab.children():  # pyright: ignore[reportGeneralTypeIssues]
            # HACK(NickHugi): isinstance is not working (possibly due to how DropFrame is imported in _ui.py file.
            # Also make sure there is an item in the slot otherwise the GFF will create a struct for each slot.
            if "DropFrame" in widget.__class__.__name__ and getattr(widget, "resname", None):
                casted_widget: DropFrame = cast(DropFrame, widget)
                self.equipment[casted_widget.slot] = InventoryItem(ResRef(casted_widget.resname), casted_widget.droppable, casted_widget.infinite)

    def build_items(self):
        item_builder_dialog = ItemBuilderDialog(self, self._installation, list(self._capsules))
        if item_builder_dialog.exec():
            if self._installation.cache_core_items is None:
                self._installation.cache_core_items = core_model = item_builder_dialog.core_model
            else:
                core_model: ItemModel = self._installation.cache_core_items
            self.ui.coreTree.setModel(core_model.proxy_model())

            self.ui.modulesTree.setModel(item_builder_dialog.modules_model.proxy_model())
            self.ui.overrideTree.setModel(item_builder_dialog.override_model.proxy_model())
        else:
            self.reject()

    def get_item_image(
        self,
        uti: UTI,
    ) -> QPixmap:
        return self._installation.get_item_icon_from_uti(uti)

    def get_item(
        self,
        resname: str,
        filepath: os.PathLike | str,
    ) -> tuple[str, str, UTI]:
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
            bif_result: ResourceResult | None = self._installation.resource(resname, ResourceType.UTI, [SearchLocation.CHITIN])
            if bif_result is None:
                raise FileNotFoundError
            uti = read_uti(bif_result.data)
            name = self._installation.string(uti.name, "[No Name]")
        else:
            uti = read_uti(Path(filepath).read_bytes())
        return str(filepath), name, uti

    def set_equipment(
        self,
        slot: EquipmentSlot,
        resname: str,
        filepath: str = "",
        name: str = "",
    ):
        # sourcery skip: remove-redundant-exception, simplify-single-exception-tuple
        slot_picture: QLabel = self._slow_map[slot].label
        if resname:
            try:
                filepath, name, uti = self.get_item(resname, filepath)
            except FileNotFoundError:
                RobustLogger().exception(f"Failed to get the equipment item '{resname}.uti' for the InventoryEditor")
                return

            slot_picture.setToolTip(f"{resname}\n{filepath}\n{name}")
            slot_picture.setPixmap(self.get_item_image(uti))
            slot_frame: DropFrame = self._slow_map[slot].frame

            slot_frame.set_item(resname, filepath, name, droppable=False, infinite=False)
        else:
            image: str = self._slow_map[slot].empty_image.format("droid" if self._droid else "human")
            slot_picture.setToolTip("")
            slot_picture.setPixmap(QPixmap(image))

    def do_search(
        self,
        text: str,
    ):
        self.ui.coreSearchEdit.setText(text)
        cast(QSortFilterProxyModel, self.ui.coreTree.model()).setFilterFixedString(text)
        self.ui.modulesSearchEdit.setText(text)
        cast(QSortFilterProxyModel, self.ui.modulesTree.model()).setFilterFixedString(text)
        self.ui.overrideSearchEdit.setText(text)
        cast(QSortFilterProxyModel, self.ui.overrideTree.model()).setFilterFixedString(text)

    def open_item_context_menu(
        self,
        widget: DropFrame | ItemContainer,
        point: QPoint,
    ):
        menu = QMenu(self)

        if widget.has_item:
            if self.is_store:
                infinite_action = menu.addAction("Infinite")
                infinite_action.setCheckable(True)
                infinite_action.setChecked(widget.infinite)
                infinite_action.triggered.connect(widget.toggle_infinite)
            else:
                droppable_action = menu.addAction("Droppable")
                droppable_action.setCheckable(True)
                droppable_action.setChecked(widget.droppable)
                droppable_action.triggered.connect(widget.toggle_droppable)

            menu.addSeparator()
            menu.addAction("Remove Item").triggered.connect(widget.remove_item)
        else:
            menu.addAction("No Item").setEnabled(False)

        menu.addSeparator()
        menu.addAction("Set Item ResRef").triggered.connect(lambda: self.prompt_set_item_resref_dialog(cast(DropFrame, widget)))
        menu.exec(widget.mapToGlobal(point))

    def prompt_set_item_resref_dialog(
        self,
        widget: DropFrame,
    ):
        dialog: SetItemResRefDialog = SetItemResRefDialog(self)

        if not dialog.exec():
            return
        self.set_equipment(widget.slot, dialog.resref())


class ItemContainer:
    def __init__(
        self,
        *,
        droppable: bool = False,
        infinite: bool = False,
    ):
        self.resname: str = ""
        self.filepath: str = ""
        self.name: str = ""
        self.has_item: bool = False
        self.droppable: bool = droppable
        self.infinite: bool = infinite

    def remove_item(self):
        self.resname = ""
        self.filepath = ""
        self.name = ""
        self.has_item = False
        self.droppable = False
        self.infinite = False

    def set_item(
        self,
        resname: str,
        filepath: str,
        name: str,
        *,
        droppable: bool,
        infinite: bool,
    ):
        self.resname = resname
        self.filepath = filepath
        self.name = name
        self.has_item = True
        self.droppable = droppable
        self.infinite = infinite

    def toggle_droppable(self):
        self.droppable = not self.droppable

    def toggle_infinite(self):
        self.infinite = not self.infinite


class DropFrame(ItemContainer, QFrame):
    sig_item_dropped = QtCore.Signal(object, object, object)  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        parent: QWidget | None,
    ):
        QFrame.__init__(self)
        ItemContainer.__init__(self)
        self.setFrameShape(QFrame.Shape.Box)
        self.setAcceptDrops(True)
        self.slot: EquipmentSlot = EquipmentSlot.HIDE

    def dragEnterEvent(
        self,
        event: QDragEnterEvent,
    ):
        if not isinstance(event.source(), QTreeView):
            return
        tree: QObject | None = event.source()
        if not isinstance(tree, QTreeView):
            return
        proxy_model: QAbstractItemModel | None = tree.model()
        if not isinstance(proxy_model, QSortFilterProxyModel):
            return
        src_index = proxy_model.mapToSource(tree.selectedIndexes()[0])
        src_model: QAbstractItemModel | None = proxy_model.sourceModel()
        if not isinstance(src_model, ItemModel):
            return
        item: QStandardItem | None = src_model.itemFromIndex(src_index)
        if not item or not item.data(_SLOTS_ROLE) & self.slot.value:
            return
        event.accept()

    def dragMoveEvent(
        self,
        event: QDragMoveEvent,
    ):
        src_object: QObject | None = event.source()
        if not isinstance(src_object, QTreeView):
            return
        tree: QTreeView = src_object
        proxy_model: QAbstractItemModel | None = tree.model()
        assert isinstance(proxy_model, QSortFilterProxyModel), f"Expected QSortFilterProxyModel, got {type(proxy_model).__name__}"
        model: QAbstractItemModel | None = proxy_model.sourceModel()
        assert isinstance(model, ItemModel), f"Expected ItemModel, got {type(model).__name__}"
        src_index = proxy_model.mapToSource(tree.selectedIndexes()[0])
        item: QStandardItem | None = model.itemFromIndex(src_index)
        if not item or not item.data(_SLOTS_ROLE) & self.slot.value:
            return
        event.accept()

    def dropEvent(
        self,
        event: QDropEvent,
    ):
        src_object: QObject | None = event.source()
        if not isinstance(src_object, QTreeView):
            return
        event.setDropAction(Qt.DropAction.CopyAction)

        tree: QTreeView = src_object
        proxy_model: QAbstractItemModel | None = tree.model()
        assert isinstance(proxy_model, QSortFilterProxyModel), f"Expected QSortFilterProxyModel, got {type(proxy_model).__name__}"
        model: QAbstractItemModel | None = proxy_model.sourceModel()
        assert isinstance(model, ItemModel), f"Expected ItemModel, got {type(model).__name__}"
        index: QModelIndex = proxy_model.mapToSource(tree.selectedIndexes()[0])
        item: QStandardItem | None = model.itemFromIndex(index)
        if item is None:
            return
        if item.data(_SLOTS_ROLE) & self.slot.value:
            event.accept()
            self.set_item(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text(), droppable=False, infinite=False)
            self.sig_item_dropped.emit(self.filepath, self.resname, self.name)

    def remove_item(self):
        ItemContainer.remove_item(self)
        cast(InventoryEditor, self.window()).set_equipment(self.slot, "")  # type: ignore[arg-type]

    def toggle_droppable(self):
        ItemContainer.toggle_droppable(self)


class InventoryTable(QTableWidget):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)
        self.itemChanged.connect(self.resname_changed)
        self.customContextMenuRequested.connect(self.open_context_menu)
        self.is_store: bool = False

    def add_item(
        self,
        resname: str,
        *,
        droppable: bool,
        infinite: bool,
    ):
        rowID: int = self.rowCount()
        self.insertRow(rowID)
        filepath, name, uti = cast(InventoryEditor, self.window()).get_item(resname, "")
        icon_item: QTableWidgetItem = self._set_uti(uti)
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
        resname_item = InventoryTableResnameItem(resname, filepath, name, droppable=droppable, infinite=infinite)
        self._set_row(rowID, icon_item, resname_item, name_item)

    def dropEvent(
        self,
        event: QDropEvent,
    ):
        if isinstance(event.source(), QTreeView):
            event.setDropAction(Qt.DropAction.CopyAction)

            tree: QObject | None = event.source()
            if not isinstance(tree, QTreeView):
                return

            proxy_model: QAbstractItemModel | None = tree.model()
            assert isinstance(proxy_model, QSortFilterProxyModel), f"Expected QSortFilterProxyModel, got {type(proxy_model).__name__}"
            model: QAbstractItemModel | None = proxy_model.sourceModel()
            assert isinstance(model, ItemModel), f"Expected ItemModel, got {type(model).__name__}"
            index: QModelIndex = proxy_model.mapToSource(tree.selectedIndexes()[0])
            item: QStandardItem | None = model.itemFromIndex(index)
            assert item is not None, f"Expected QStandardItem, got {type(item).__name__}"
            event.accept()
            rowID: int = self.rowCount()
            self.insertRow(rowID)
            filepath, name, uti = cast(InventoryEditor, self.window()).get_item(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE))
            icon_item: QTableWidgetItem = self._set_uti(uti)
            name_item = QTableWidgetItem(item.text())
            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            resname_item = InventoryTableResnameItem(item.data(_RESNAME_ROLE), item.data(_FILEPATH_ROLE), item.text(), droppable=False, infinite=False)
            self._set_row(rowID, icon_item, resname_item, name_item)

    def _set_row(
        self,
        row_id: int,
        icon_item: QTableWidgetItem,
        resname_item: InventoryTableResnameItem,
        name_item: QTableWidgetItem,
    ):
        self.setItem(row_id, 0, icon_item)
        self.setItem(row_id, 1, resname_item)
        self.setItem(row_id, 2, name_item)

    def _set_uti(
        self,
        uti: UTI,
    ) -> QTableWidgetItem:
        pixmap: QPixmap = cast(InventoryEditor, self.window()).get_item_image(uti)
        result: QTableWidgetItem = QTableWidgetItem(QIcon(pixmap), "")
        result.setSizeHint(QSize(48, 48))
        result.setFlags(result.flags() ^ Qt.ItemFlag.ItemIsEditable)
        return result

    def resname_changed(
        self,
        table_item: QTableWidgetItem,
    ):
        if isinstance(table_item, InventoryTableResnameItem):
            filepath, name, uti = cast(InventoryEditor, self.window()).get_item(table_item.text(), "")
            icon = QIcon(cast(InventoryEditor, self.window()).get_item_image(uti))

            table_item.set_item(table_item.text(), filepath, name, droppable=table_item.droppable, infinite=table_item.infinite)
            item = self.item(table_item.row(), 0)
            if item is None:
                return
            item.setIcon(icon)
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            self.setItem(table_item.row(), 2, name_item)

    def open_context_menu(
        self,
        point: QPoint,
    ):
        if len(self.selectedIndexes()) == 0:
            return
        sel_model: QtCore.QItemSelectionModel | None = self.selectionModel()
        if sel_model is None:
            return
        row: int = sel_model.selectedRows(1)[0].row()
        item_container: QTableWidgetItem | None = self.item(row, 1)
        if item_container is None:
            return
        if not isinstance(item_container, ItemContainer):
            return
        menu = QMenu(self)
        if self.is_store:
            infinite_action = QAction("Infinite")
            infinite_action.setCheckable(True)
            infinite_action.setChecked(item_container.infinite)
            infinite_action.triggered.connect(item_container.toggle_infinite)
            menu.addAction(infinite_action)
        else:
            droppable_action = QAction("Droppable")
            droppable_action.setCheckable(True)
            droppable_action.setChecked(item_container.droppable)
            droppable_action.triggered.connect(item_container.toggle_droppable)
            menu.addAction(droppable_action)

        remove_action = QAction("Remove Item")
        remove_action.triggered.connect(item_container.remove_item)

        menu.addSeparator()
        menu.addAction(remove_action)

        menu.exec(self.mapToGlobal(point))


class InventoryTableResnameItem(ItemContainer, QTableWidgetItem):
    def __init__(
        self,
        resname: str,
        filepath: str,
        name: str,
        *,
        droppable: bool,
        infinite: bool,
    ):
        ItemContainer.__init__(self, droppable=droppable, infinite=infinite)
        QTableWidgetItem.__init__(self, resname)
        self.set_item(resname, filepath, name, droppable=droppable, infinite=infinite)

    def remove_item(self):
        tbl_widget: QTableWidget | None = self.tableWidget()
        if tbl_widget is None:
            return
        tbl_widget.removeRow(self.row())


class ItemBuilderDialog(QDialog):
    """Popup dialog responsible for extracting a list of resources from the game files."""

    def __init__(
        self,
        parent: QWidget,
        installation: HTInstallation,
        capsules: list[LazyCapsule],
    ):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog  # pyright: ignore[reportArgumentType]
            | Qt.WindowType.WindowCloseButtonHint
            & ~Qt.WindowType.WindowContextHelpButtonHint
            & ~Qt.WindowType.WindowMinMaxButtonsHint
        )

        self._progress_bar: QProgressBar = QProgressBar(self)
        self._progress_bar.setMaximum(0)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(False)

        self.resize(250, 40)
        main_layout: QVBoxLayout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self._progress_bar)

        self.setWindowTitle("Building Item Lists...")
        self.core_model: ItemModel = ItemModel(parent)
        self.modules_model: ItemModel = ItemModel(parent)
        self.override_model: ItemModel = ItemModel(parent)
        self._tlk: TLK = read_tlk(CaseAwarePath(installation.path(), "dialog.tlk"))
        self._installation: HTInstallation = installation
        self._capsules: list[LazyCapsule] = capsules

        self._worker: ItemBuilderWorker = ItemBuilderWorker(installation, capsules)
        self._worker.sig_uti_loaded.connect(self.on_uti_loaded)
        self._worker.sig_finished.connect(self.on_finished)
        self._worker.start()

    def on_uti_loaded(
        self,
        uti: UTI,
        result: ResourceResult,
    ):
        baseitems: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
        if baseitems is None:
            return
        name: str = result.resname if uti is None else self._installation.string(uti.name, result.resname)

        # Split category by base item:
        # TODO(th3w1zard1): What is this for and why is it commented out?
        #  categoryNameID = baseitems.get_row(uti.base_item).get_integer("name")
        #  categoryLabel = baseitems.get_cell(uti.base_item, "label")
        #  category = self._tlk.get(categoryNameID).text if self._tlk.get(categoryNameID) is not None else categoryLabel

        slots: int = 0 if uti is None else baseitems.get_row(uti.base_item).get_integer("equipableslots", 0)
        category: str = self.get_category(uti)

        if result.filepath.suffix.lower() in {".bif", ".key"}:
            self.core_model.add_item(result.resname, category, result.filepath, name, slots)
        elif is_capsule_file(result.filepath):
            self.modules_model.add_item(result.resname, category, result.filepath, name, slots)
        else:
            self.override_model.add_item(result.resname, category, result.filepath, name, slots)

    def on_finished(self):
        self.accept()

    def get_category(
        self,
        uti: UTI | None,
    ) -> str:
        if uti is None:
            slots: int = -1
            droid: bool = False
        else:
            baseitems: TwoDA | None = self._installation.ht_get_cache_2da(HTInstallation.TwoDA_BASEITEMS)
            if baseitems is None:
                return "Unknown"
            slots = baseitems.get_row(uti.base_item).get_integer("equipableslots", 0)
            droid = baseitems.get_row(uti.base_item).get_integer("droidorhuman", 0) == 2  # noqa: PLR2004

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
    sig_uti_loaded: Signal = Signal(object, object)  # pyright: ignore[reportPrivateImportUsage]
    sig_finished: Signal = Signal()  # pyright: ignore[reportPrivateImportUsage]

    def __init__(
        self,
        installation: HTInstallation,
        capsules: list[LazyCapsule],
    ):
        super().__init__()
        self._installation: HTInstallation = installation
        self._capsules: list[LazyCapsule] = capsules

    def run(self):
        queries: list[ResourceIdentifier] = []
        if self._installation.cache_core_items is None:
            queries.extend(resource.identifier() for resource in self._installation.core_resources() if resource.restype() is ResourceType.UTI)
        queries.extend(resource.identifier() for resource in self._installation.override_resources() if resource.restype() is ResourceType.UTI)
        for capsule in self._capsules:
            queries.extend(resource.identifier() for resource in capsule if resource.restype() is ResourceType.UTI)
        results: dict[ResourceIdentifier, ResourceResult | None] = self._installation.resources(
            queries,
            [
                SearchLocation.OVERRIDE,
                SearchLocation.CHITIN,
                SearchLocation.CUSTOM_MODULES,
            ],
            capsules=self._capsules,
        )
        for identifier, resource_result in results.items():
            if resource_result is None:
                RobustLogger().warning("Could not find UTI resource '%s'", identifier)
                continue
            uti: UTI | None = None
            try:  # FIXME(th3w1zard1): this section seems to crash often.
                uti = read_uti(resource_result.data)
            except Exception:  # pylint: disable=W0718  # noqa: BLE001
                RobustLogger().exception("Error reading UTI resource while building items.")
            else:
                self.sig_uti_loaded.emit(uti, resource_result)
        self.sig_finished.emit()


class ItemModel(QStandardItemModel):
    def __init__(
        self,
        parent: QWidget,
    ):
        super().__init__(parent)

        self._category_items: dict[str, QStandardItem] = {}
        self._proxy_model: QSortFilterProxyModel = QSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self)
        self._proxy_model.setRecursiveFilteringEnabled(True)  # type: ignore[arg-type]
        self._proxy_model.setFilterCaseSensitivity(False if qtpy.QT5 else Qt.CaseSensitivity.CaseInsensitive)  # type: ignore[arg-type]

    def proxy_model(self) -> QSortFilterProxyModel:
        return self._proxy_model

    def _get_category_item(
        self,
        category: str,
    ) -> QStandardItem:
        if category not in self._category_items:
            category_item: QStandardItem = QStandardItem(category)
            category_item.setSelectable(False)
            self._category_items[category] = category_item
            self.appendRow(category_item)
        return self._category_items[category]

    def add_item(
        self,
        resname: str,
        category: str,
        filepath: os.PathLike | str,
        name: str,
        slots: int,
    ):
        item = QStandardItem(name.strip() or resname.strip())
        item.setToolTip(f"{resname}\n{filepath}\n{name}")
        item.setData(filepath, _FILEPATH_ROLE)
        item.setData(resname, _RESNAME_ROLE)
        item.setData(slots, _SLOTS_ROLE)
        self._get_category_item(category).appendRow(item)


class SetItemResRefDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)

        from toolset.uic.qtpy.dialogs.set_item_resref import Ui_Dialog

        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def resref(self) -> str:
        return self.ui.resrefEdit.text()
