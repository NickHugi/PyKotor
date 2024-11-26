from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import qtpy

from loggerplus import RobustLogger  # pyright: ignore[reportMissingTypeStubs]
from qtpy import QtGui
from qtpy.QtCore import (
    QMimeData,
    QModelIndex,
    QUrl,
    Qt,
    Signal,  # pyright: ignore[reportPrivateImportUsage]
)
from qtpy.QtGui import QKeySequence, QStandardItem, QStandardItemModel
from qtpy.QtWidgets import (
    QAction,  # pyright: ignore[reportPrivateImportUsage]
    QFileDialog,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QWidget,
)

from pykotor.common.misc import ResRef
from pykotor.extract.file import FileResource, ResourceIdentifier
from pykotor.resource.formats.bif import read_bif
from pykotor.resource.formats.erf import ERF, ERFResource, ERFType, read_erf, write_erf
from pykotor.resource.formats.rim import RIM, read_rim, write_rim
from pykotor.resource.type import ResourceType
from pykotor.tools.misc import is_capsule_file
from toolset.gui.common.filters import RobustSortFilterProxyModel
from toolset.gui.dialogs.save.generic_file_saver import FileSaveHandler
from toolset.gui.editor import Editor
from toolset.gui.widgets.settings.installations import GlobalSettings
from toolset.utils.window import open_resource_editor
from utility.error_handling import universal_simplify_exception
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView

if TYPE_CHECKING:
    import os

    from qtpy.QtCore import (
        QAbstractItemModel,  # pyright: ignore[reportPrivateImportUsage]
        QItemSelectionModel,
        QModelIndex,
        QPoint,  # pyright: ignore[reportPrivateImportUsage]
        pyqtBoundSignal,
    )
    from qtpy.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
    from qtpy.QtWidgets import QAbstractButton, QHeaderView, QWidget

    from pykotor.extract.keyfile import BIFResource
    from pykotor.resource.formats.bif import BIF
    from pykotor.resource.formats.rim import RIMResource
    from toolset.data.installation import HTInstallation

if qtpy.QT5:
    from qtpy.QtCore import QRegExp  # pyright: ignore[reportAttributeAccessIssue]
    from qtpy.QtGui import QRegExpValidator
else:
    from qtpy.QtCore import QRegularExpression as QRegExp
    from qtpy.QtGui import QRegularExpressionValidator as QRegExpValidator


def human_readable_size(byte_size: float) -> str:
    for unit in ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]:
        if byte_size < 1024:  # noqa: PLR2004
            return f"{round(byte_size, 2)} {unit}"
        byte_size /= 1024
    return str(byte_size)


class ERFSortFilterProxyModel(RobustSortFilterProxyModel):
    def get_sort_value(
        self,
        index: QModelIndex,
    ) -> int:
        """Return the sort value based on the column."""
        src_model: QAbstractItemModel | None = self.sourceModel()
        assert isinstance(src_model, QStandardItemModel)
        if index.column() == 2:  # noqa: PLR2004
            item: QStandardItem | None = src_model.item(index.row(), 0)
            if item is None:
                RobustLogger().warning("ERFSortFilterProxyModel: item was None in get_sort_value() at index %s", index)
                return 0
            resource: ERFResource = item.data()
            return len(resource.data)
        return src_model.data(index)


class ERFEditor(Editor):
    def __init__(
        self,
        parent: QWidget | None,
        installation: HTInstallation | None = None,
    ):
        supported: list[ResourceType] = [ResourceType.RIM, ResourceType.ERF, ResourceType.MOD, ResourceType.SAV, ResourceType.BIF]
        super().__init__(parent, "ERF Editor", "none", supported, supported, installation)
        self.resize(400, 250)

        from toolset.uic.qtpy.editors.erf import Ui_MainWindow

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self._setup_menus()
        self._setup_signals()
        self._is_capsule_editor: bool = True
        self._has_changes: bool = False

        self.source_model: QStandardItemModel = QStandardItemModel(self)
        self._proxy_model: ERFSortFilterProxyModel = ERFSortFilterProxyModel(self)
        self._proxy_model.setSourceModel(self.source_model)
        self.ui.tableView.setModel(self._proxy_model)

        self.ui.tableView.setSortingEnabled(False)
        header: QHeaderView | None = self.ui.tableView.horizontalHeader()
        if header is not None:
            header.setSectionsClickable(True)
            header.setSortIndicatorShown(True)
            header.sectionClicked.connect(self.handle_header_click)
        sel_model: QItemSelectionModel | None = self.ui.tableView.selectionModel()
        if sel_model is not None:
            sel_model.selectionChanged.connect(self.on_selection_changed)

        # Ensure no sorting is applied initially
        self._proxy_model.setSortRole(Qt.ItemDataRole.InitialSortOrderRole)
        if header is not None:
            header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)

        # Disable saving file into module
        self._save_filter = self._save_filter.replace(f";;Save into module ({self.CAPSULE_FILTER})", "")
        self._open_filter = self._open_filter.replace(f";;Load from module ({self.CAPSULE_FILTER})", "")

        self.new()

    def handle_header_click(
        self,
        column: int,
    ):
        # Enable sorting when a column is clicked
        if not self.ui.tableView.isSortingEnabled():
            self.ui.tableView.setSortingEnabled(True)

        self._proxy_model.toggle_sort(column)
        self.update_sort_indicator(column)

    def update_sort_indicator(
        self,
        column: int,
    ):
        sort_state: int = self._proxy_model.sort_states.get(column, 0)
        header: QHeaderView | None = self.ui.tableView.horizontalHeader()
        if header is None:
            RobustLogger().warning("ERFEditor: horizontalHeader was None in update_sort_indicator()")
            return
        if sort_state == 0:
            header.setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        elif sort_state == 1:
            header.setSortIndicator(column, Qt.SortOrder.AscendingOrder)
        elif sort_state == 2:  # noqa: PLR2004
            header.setSortIndicator(column, Qt.SortOrder.DescendingOrder)

    def _setup_signals(self):
        self.ui.extractButton.clicked.connect(self.extract_selected)
        self.ui.loadButton.clicked.connect(self.select_files_to_add)
        self.ui.unloadButton.clicked.connect(self.remove_selected)
        self.ui.unloadButton.setShortcut(QKeySequence.StandardKey.Delete)
        self.ui.openButton.clicked.connect(self.open_selected)
        self.ui.refreshButton.clicked.connect(self.refresh)
        self.ui.tableView.sig_resource_dropped.connect(self.add_resources)
        self.ui.tableView.doubleClicked.connect(self.open_selected)

        # Custom context menu for table view
        self.ui.tableView.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.open_context_menu)

    def prompt_confirm(self) -> bool:
        result = QMessageBox.question(
            None,
            "Changes detected.",
            "The action you attempted would discard your changes. Continue?",
            buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            defaultButton=QMessageBox.StandardButton.No,
        )
        return result == QMessageBox.StandardButton.Yes

    def load(
        self,
        filepath: os.PathLike | str,
        resref: str,
        restype: ResourceType,
        data: bytes,
    ):
        if self._has_changes and not self.prompt_confirm():
            return
        self._has_changes = False
        super().load(filepath, resref, restype, data)

        self.source_model.clear()
        self.source_model.setColumnCount(3)
        self.source_model.setHorizontalHeaderLabels(["ResRef", "Type", "Size", "Offset"])
        self.ui.refreshButton.setEnabled(True)

        if restype.name in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV):
            erf: ERF = read_erf(data)
            for resource in erf:
                res_offset: int = erf.get_resource_offset(resource)
                resref_item: QStandardItem = QStandardItem(str(resource.resref))
                resref_item.setData(resource)
                restype_item: QStandardItem = QStandardItem(resource.restype.extension.upper())
                size_item: QStandardItem = QStandardItem(human_readable_size(len(resource.data)))
                offset_item: QStandardItem = QStandardItem(f"0x{res_offset[0]:X}")
                self.source_model.appendRow([resref_item, restype_item, size_item, offset_item])

        elif restype is ResourceType.RIM:
            rim: RIM = read_rim(data)
            for resource in rim:
                resref_item: QStandardItem = QStandardItem(str(resource.resref))
                resref_item.setData(resource)
                restype_item: QStandardItem = QStandardItem(resource.restype.extension.upper())
                size_item: QStandardItem = QStandardItem(human_readable_size(len(resource.data)))
                offset_item: QStandardItem = QStandardItem(f"0x{rim.get_resource_offset(resource)[0]:X}")
                self.source_model.appendRow([resref_item, restype_item, size_item, offset_item])

        elif restype is ResourceType.BIF:
            bif: BIF = read_bif(data)
            for resource in bif:
                resref_item: QStandardItem = QStandardItem(str(resource.resref))
                resref_item.setData(resource)
                restype_item: QStandardItem = QStandardItem(resource.restype.extension.upper())
                size_item: QStandardItem = QStandardItem(human_readable_size(len(resource.data)))
                offset_item: QStandardItem = QStandardItem(f"0x{bif.get_resource_offset(resource)[0]:X}")
                self.source_model.appendRow([resref_item, restype_item, size_item, offset_item])

        else:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Unable to load file",
                "The file specified is not a MOD/ERF type file.",
                parent=self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
            ).show()

    def build(self) -> tuple[bytes, bytes]:
        data = bytearray()
        resource: ERFResource | RIMResource | BIFResource

        if self._restype is ResourceType.RIM:
            rim = RIM()
            for i in range(self._proxy_model.rowCount()):
                source_index: QModelIndex = self._proxy_model.mapToSource(self._proxy_model.index(i, 0))
                item: QStandardItem | None = self.source_model.itemFromIndex(source_index)
                if item is None:
                    RobustLogger().warning(f"item was None in ERFEditor.build() at index {source_index}")
                    continue
                resource: ERFResource = item.data()
                rim.set_data(str(resource.resref), resource.restype, resource.data)
            write_rim(rim, data)

        elif self._restype in (ResourceType.ERF, ResourceType.MOD, ResourceType.SAV, ResourceType.BIF):  # sourcery skip: split-or-ifs
            erf = ERF(ERFType.from_extension(self._restype.extension))
            if self._restype is ResourceType.SAV:
                erf.is_save = True
            for i in range(self._proxy_model.rowCount()):
                source_index: QModelIndex = self._proxy_model.mapToSource(self._proxy_model.index(i, 0))
                item: QStandardItem | None = self.source_model.itemFromIndex(source_index)
                if item is None:
                    RobustLogger().warning("item was None in ERFEditor.build() at index %s", source_index)
                    continue
                resource = item.data()
                erf.set_data(str(resource.resref), resource.restype, resource.data)
            write_erf(erf, data)
        else:
            raise ValueError(f"Invalid restype for ERFEditor: {self._restype!r}")

        return bytes(data), b""

    def new(self):
        if self._has_changes and not self.prompt_confirm():
            return
        self._has_changes = False
        super().new()
        self.source_model.clear()
        self.source_model.setColumnCount(3)
        self.source_model.setHorizontalHeaderLabels(["ResRef", "Type", "Size"])
        self.ui.refreshButton.setEnabled(False)

    def save(self):
        self._has_changes = False
        # Must override the method as the superclass method breaks due to filepath always ending in .rim/mod/erf
        if self._filepath is None:
            self.save_as()
            return

        self.ui.refreshButton.setEnabled(True)

        data: tuple[bytes, bytes] = self.build()
        self._revert = data[0]
        if is_capsule_file(self._filepath.parent) and not self._filepath.is_file():
            try:
                self._save_nested_capsule(*data)
            except ValueError as e:
                msg: str = str(e)
                if msg.startswith("You must save the ERFEditor"):  # HACK(th3w1zard1): fix later.
                    QMessageBox(
                        QMessageBox.Icon.Information,
                        "New resource added to parent ERF/RIM",
                        "You've added a new ERF/RIM and tried to save inside that new ERF/RIM's editor. You must save the ERFEditor you added the nested to first. Do so and try again.",  # noqa: E501
                    ).exec()
                else:
                    raise
        else:
            with self._filepath.open("wb") as file:
                file.write(data[0])

    def open_context_menu(
        self,
        position: QPoint,
    ):
        sel_resources: list[ERFResource] = self.get_selected_resources()
        if not sel_resources:
            RobustLogger().debug("ERFEditor: Nothing selected to build context menu.")
            return

        main_menu = QMenu(self)

        extract_action = QAction("Extract to...", self)
        extract_action.triggered.connect(self.extract_selected)
        main_menu.addAction(extract_action)

        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(self.rename_selected)
        main_menu.addAction(rename_action)
        if len(sel_resources) != 1:
            rename_action.setEnabled(False)

        if self._filepath is not None:
            main_menu.addSeparator()
            if all(resource.restype.target_type().contents == "gff" for resource in sel_resources):
                main_menu.addAction("Open with GFF Editor").triggered.connect(lambda *args, fp=self._filepath, **kwargs: self.open_in_resource_editor(fp, sel_resources, self._installation, gff_specialized=False))  # noqa: E501
                if self._installation is not None:
                    main_menu.addAction("Open with Specialized Editor").triggered.connect(lambda *args, fp=self._filepath, **kwargs: self.open_in_resource_editor(fp, sel_resources, self._installation, gff_specialized=True))  # noqa: E501
                    main_menu.addAction("Open with Default Editor").triggered.connect(lambda *args, fp=self._filepath, **kwargs: self.open_in_resource_editor(fp, sel_resources, self._installation, gff_specialized=None))  # noqa: E501

            elif self._installation is not None:
                main_menu.addAction("Open with Editor").triggered.connect(lambda *args, fp=self._filepath, **kwargs: self.open_in_resource_editor(fp, sel_resources, self._installation, gff_specialized=True))  # noqa: E501

        viewport: QWidget | None = self.ui.tableView.viewport()
        if viewport is None:
            RobustLogger().warning("ERFEditor: viewport was None in open_context_menu()")
            return
        main_menu.exec(viewport.mapToGlobal(position))

    def get_selected_resources(self) -> list[ERFResource]:
        # return [self.model.itemFromIndex(rowItem).data() for rowItem in selected_rows]
        sel_model: QItemSelectionModel | None = self.ui.tableView.selectionModel()
        if sel_model is None:
            RobustLogger().warning("ERFEditor: selectionModel was None in get_selected_resources()")
            return []
        return [self.source_model.itemFromIndex(self._proxy_model.mapToSource(rowItem)).data() for rowItem in sel_model.selectedRows()]

    def extract_selected(self):
        selected_resources: list[ERFResource] = self.get_selected_resources()
        if not selected_resources:
            RobustLogger().info("ERFEditor: Nothing selected to save, no selected resources.")
            return
        FileSaveHandler(selected_resources, parent=self).save_files()

    def rename_selected(self):
        indexes: list[QModelIndex] = self.ui.tableView.selectedIndexes()
        if not indexes:
            return

        index: QModelIndex = indexes[0]
        source_index: QModelIndex = self._proxy_model.mapToSource(index)
        item: QStandardItem | None = self.source_model.itemFromIndex(source_index)
        if item is None:
            RobustLogger().warning("item was None in ERFEditor.rename_selected() at index %s", index)
            return
        resource: ERFResource = item.data()

        erfrim_filename: str = "ERF/RIM/BIF" if self._resname is None or self._restype is None else f"{self._resname}.{self._restype.extension}"
        new_resname, ok = self.get_validated_resref(erfrim_filename, resource)
        if ok:
            resource.resref = ResRef(new_resname)
            item.setText(new_resname)
            self._has_changes = True

    def get_validated_resref(
        self,
        erfrim_name: str,
        resource: ERFResource,
    ) -> tuple[str, bool]:
        dialog: QInputDialog = QInputDialog(self)
        dialog.setWindowTitle(f"Rename {erfrim_name} Resource ResRef")
        dialog.setLabelText(f"Enter new ResRef ({resource.resref}):")
        dialog.setTextValue(str(resource.resref))
        dialog.setInputMode(QInputDialog.InputMode.TextInput)

        input_field: QLineEdit | None = dialog.findChild(QLineEdit)
        if input_field is None:
            RobustLogger().warning("input_field could not be found in parent class QLineEdit")
            return "", False
        input_field.setValidator(self.resref_validator())

        while dialog.exec() == QInputDialog.DialogCode.Accepted:
            new_resname: str = dialog.textValue()
            if ResRef.is_valid(new_resname):
                return new_resname, True
            QMessageBox.warning(self, "Invalid ResRef", "ResRefs must adhere to SBCS encoding standards (typically cp1252) and be a maximum of 16 characters.")
        return "", False

    def resref_validator(self) -> QRegExpValidator:
        return QRegExpValidator(QRegExp(r"^[a-zA-Z0-9_]*$"))  # pyright: ignore[reportArgumentType, reportCallIssue]

    def remove_selected(self):
        self._has_changes = True
        for index in reversed([index for index in self.ui.tableView.selectedIndexes() if not index.column()]):
            item: QStandardItem | None = self.source_model.itemFromIndex(self._proxy_model.mapToSource(index))
            if item is None:
                RobustLogger().warning("item was None in ERFEditor.remove_selected() at index %s", index)
                continue
            self.source_model.removeRow(item.row())

    def add_resources(
        self,
        filepaths: list[str],
    ):
        self._has_changes = True
        for filepath in filepaths:
            r_filepath = Path(filepath)
            try:
                resref, restype = ResourceIdentifier.from_path(r_filepath).validate().unpack()
                data: bytes = r_filepath.read_bytes()
                resource = ERFResource(ResRef(resref), restype, data)

                resref_item = QStandardItem(str(resource.resref))
                resref_item.setData(resource)
                restype_item: QStandardItem = QStandardItem(resource.restype.extension.upper())
                resource_size_str: str = human_readable_size(len(resource.data))
                size_item: QStandardItem = QStandardItem(resource_size_str)
                self.source_model.appendRow([resref_item, restype_item, size_item])
            except Exception as e:  # noqa: BLE001
                RobustLogger().exception("Failed to add resource at '%s'", r_filepath.absolute())
                error_msg: str = str(universal_simplify_exception(e)).replace("\n", "<br>")
                QMessageBox(
                    QMessageBox.Icon.Critical,
                    "Failed to add resource",
                    f"Could not add resource at '{r_filepath.absolute()}'<br><br>{error_msg}",
                    flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
                ).exec()

    def select_files_to_add(self):
        filepaths: list[str] = QFileDialog.getOpenFileNames(self, "Load files into module")[:-1][0]
        self.add_resources(filepaths)

    def open_selected(
        self,
        *,
        gff_specialized: bool | None = None,
    ):
        sel_model: QItemSelectionModel | None = self.ui.tableView.selectionModel()
        if sel_model is None:
            RobustLogger().warning("ERFEditor: selectionModel was None in open_selected()")
            return
        erf_resources: list[ERFResource] = [self.source_model.itemFromIndex(self._proxy_model.mapToSource(index)).data() for index in sel_model.selectedRows()]
        if not erf_resources:
            return
        if self._filepath is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                f"Cannot edit resource {erf_resources[0].identifier()}. Filepath not set.",
                "This ERF/RIM must be saved to disk first, do so and try again.",
                QMessageBox.StandardButton.Ok,
                self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
            ).exec()
            return

        self.open_in_resource_editor(
            self._filepath,
            erf_resources,
            self._installation,
            self.sig_saved_file,
            gff_specialized=gff_specialized,
        )

    def open_in_resource_editor(
        self,
        filepath: Path,
        resources: list[ERFResource],
        installation: HTInstallation | None = None,
        saved_file_signal: pyqtBoundSignal | None = None,
        *,
        gff_specialized: bool | None = None,
    ):
        for resource in resources:
            new_filepath: Path = filepath
            if resource.restype in (ResourceType.ERF, ResourceType.SAV, ResourceType.RIM, ResourceType.MOD):
                RobustLogger().info(f"Nested capsule selected for opening, appending resref/restype '{resource.resref}.{resource.restype}' to the filepath.")
                new_filepath /= str(ResourceIdentifier(str(resource.resref), resource.restype))

            offset: int = self.get_resource_offset(resource)  # FIXME(th3w1zard1): figure out how to get the offset in this context?
            file_resource = FileResource(str(resource.resref), resource.restype, len(resource.data), offset, new_filepath)
            _tempPath, editor = open_resource_editor(file_resource, installation, gff_specialized=gff_specialized)
            if saved_file_signal is not None and isinstance(editor, Editor):
                editor.sig_saved_file.connect(saved_file_signal)

    def refresh(self):
        if self._has_changes and not self.prompt_confirm():
            return
        if self._filepath is None:
            QMessageBox(
                QMessageBox.Icon.Critical,
                "Nothing to refresh.",
                "This ERFEditor was never loaded from a file, so there's nothing to refresh.",
                QMessageBox.StandardButton.Ok,
                self,
                flags=Qt.WindowType.Dialog | Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowSystemMenuHint,
            ).exec()
            return
        self._has_changes = False
        data: bytes = self._filepath.read_bytes()
        self.load(self._filepath, self._resname, self._restype, data)

    def on_selection_changed(self):
        if len(self.ui.tableView.selectedIndexes()) == 0:
            self._set_ui_controls_state(state=False)
        else:
            self._set_ui_controls_state(state=True)

    def _set_ui_controls_state(
        self,
        *,
        state: bool,
    ):
        self.ui.extractButton.setEnabled(state)
        self.ui.openButton.setEnabled(state)
        self.ui.unloadButton.setEnabled(state)

    def resource_saved(
        self,
        filepath: str,
        resname: str,
        restype: ResourceType,
        data: bytes,
    ):
        if filepath != self._filepath:
            return

        sel_model: QItemSelectionModel | None = self.ui.tableView.selectionModel()
        if sel_model is None:
            RobustLogger().warning("ERFEditor: selectionModel was None in resource_saved()")
            return
        for index in sel_model.selectedRows(0):
            source_index: QModelIndex = self._proxy_model.mapToSource(index)
            item: QStandardItem | None = self.source_model.itemFromIndex(source_index)
            if item is None:
                RobustLogger().warning("ERFEditor: item was None in resource_saved() at index %s", index)
                continue
            resource: ERFResource = item.data()
            if resource.resref != resname:
                continue
            if resource.restype != restype:
                continue
            item.setData(data)

    def get_resource_offset(
        self,
        resource: ERFResource,
    ) -> int:
        for row in range(self.source_model.rowCount()):
            item: QStandardItem | None = self.source_model.item(row, 0)
            if item is None:
                RobustLogger().warning("ERFEditor: item was None in get_resource_offset() at row %s", row)
                continue
            if item.data() == resource:
                size_item: QStandardItem | None = self.source_model.item(row, 3)
                if size_item is None:
                    RobustLogger().warning("ERFEditor: size_item was None in get_resource_offset() at row %s", row)
                    continue
                return int(size_item.text(), 16)
        return 0  # Default to 0 if not found


class ERFEditorTable(RobustTableView):
    sig_resource_dropped: Signal = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)

    def dragEnterEvent(
        self,
        event: QDragEnterEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is None:
            RobustLogger().warning("ERFEditorTable: mimeData was None in dragEnterEvent()")
            return
        if mime_data.hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(
        self,
        event: QDragMoveEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is None:
            RobustLogger().warning("ERFEditorTable: mimeData was None in dragMoveEvent()")
            return
        if mime_data.hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(  # noqa: C901, PLR0911, PLR0912, PLR0915
        self,
        event: QDropEvent,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        response: QMessageBox.StandardButton | int | None = None
        mime_data: QMimeData | None = event.mimeData()
        if mime_data is None:
            RobustLogger().warning("ERFEditorTable: mimeData was None in dropEvent()")
            return
        if mime_data.hasUrls():
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            filter_model: ERFSortFilterProxyModel = cast(ERFSortFilterProxyModel, self.model())
            source_model: QStandardItemModel = cast(QStandardItemModel, filter_model.sourceModel())
            existing_items: set[str] = {f"{source_model.index(row, 0).data()}.{source_model.index(row, 1).data()}".strip().lower() for row in range(source_model.rowCount())}
            always = False
            never = False
            to_skip: list[str] = []
            links: list[str] = [str(url.toLocalFile()) for url in mime_data.urls()]
            for link in links:
                if link.lower() in existing_items:
                    if always:
                        response = QMessageBox.StandardButton.Yes
                    elif never:
                        response = QMessageBox.StandardButton.No
                    else:
                        msg_box = QMessageBox()
                        msg_box.setIcon(QMessageBox.Icon.Warning)
                        msg_box.setWindowTitle("Duplicate Resource dropped.")
                        msg_box.setText(f"'{link}' already exists in the table. Do you want to overwrite?")
                        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.YesToAll | QMessageBox.StandardButton.No | QMessageBox.StandardButton.NoToAll | QMessageBox.StandardButton.Abort)  # noqa: E501
                        button_yes: QAbstractButton | None = msg_box.button(QMessageBox.StandardButton.Yes)
                        if button_yes is None:
                            RobustLogger().warning("ERFEditorTable: button_yes was None in dropEvent()")
                            return
                        button_yes.setText("Overwrite")
                        button_yes_to_all: QAbstractButton | None = msg_box.button(QMessageBox.StandardButton.YesToAll)
                        if button_yes_to_all is None:
                            RobustLogger().warning("ERFEditorTable: button_yes_to_all was None in dropEvent()")
                            return
                        button_yes_to_all.setText("Overwrite All")
                    if response == QMessageBox.StandardButton.Yes:
                        model: QAbstractItemModel | None = self.model()
                        if model is None:
                            RobustLogger().warning("ERFEditorTable: model was None in dropEvent()")
                            return
                        for row in range(model.rowCount()):
                            cell_col_0: QStandardItem | None = source_model.item(row, 0)
                            if cell_col_0 is None:
                                RobustLogger().warning("ERFEditorTable: cell_col_0 was None in dropEvent() at row %s", row)
                                continue
                            cell_col_1: QStandardItem | None = source_model.item(row, 1)
                            if cell_col_1 is None:
                                RobustLogger().warning("ERFEditorTable: cell_col_1 was None in dropEvent() at row %s", row)
                                continue
                            filename: str = f"{cell_col_0.text()}.{cell_col_1.text()}".strip().lower()
                            if filename == link.lower().strip():
                                print(f"Removing '{filename}' from the erf/rim.")
                                model.removeRow(row)
                                break
                    elif response == QMessageBox.StandardButton.No:
                        to_skip.append(link)
                    elif response == QMessageBox.StandardButton.Abort:
                        return
                    elif response == QMessageBox.StandardButton.YesToAll:
                        always = True
                        model: QAbstractItemModel | None = self.model()
                        if model is None:
                            RobustLogger().warning("ERFEditorTable: model was None in dropEvent()")
                            return
                        for row in range(model.rowCount()):
                            cell_col_0: QStandardItem | None = source_model.item(row, 0)
                            if cell_col_0 is None:
                                RobustLogger().warning("ERFEditorTable: cell_col_0 was None in dropEvent() at row %s", row)
                                continue
                            cell_col_1: QStandardItem | None = source_model.item(row, 1)
                            if cell_col_1 is None:
                                RobustLogger().warning("ERFEditorTable: cell_col_1 was None in dropEvent() at row %s", row)
                                continue
                            filename: str = f"{cell_col_0.text()}.{cell_col_1.text()}".strip().lower()
                            if filename == link.lower().strip():
                                print(f"Removing '{filename}' from the erf/rim.")
                                model.removeRow(row)
                                break
                    elif response == QMessageBox.StandardButton.NoToAll:
                        never = True
                        to_skip.append(link)

            for link in to_skip:
                print(f"Skipping dropped filename '{link}'")
                links.remove(link)
            if not links:
                print("Nothing dropped, or everything dropped was skipped.")
                return
            self.sig_resource_dropped.emit(links)
        else:
            event.ignore()

    def startDrag(
        self,
        actions: Qt.DropAction,
    ):  # pyright: ignore[reportIncompatibleMethodOverride]
        temp_dir = Path(GlobalSettings().extractPath)

        exists: bool = temp_dir.exists()
        if not exists or not temp_dir.is_dir():
            if exists or temp_dir.is_file():
                RobustLogger().error(f"temp_dir '{temp_dir}' exists but was not a valid filesystem folder.")
            else:
                temp_dir.mkdir(parents=True, exist_ok=True)
            if not temp_dir.is_dir():
                RobustLogger().error(f"Temp directory not valid: {temp_dir}")
            return

        urls: list[QUrl] = []
        filter_model: ERFSortFilterProxyModel = cast(ERFSortFilterProxyModel, self.model())
        source_model: QStandardItemModel = cast(QStandardItemModel, filter_model.sourceModel())
        for index in (index for index in self.selectedIndexes() if not index.column()):
            resource: ERFResource = source_model.data(filter_model.mapToSource(index), Qt.ItemDataRole.UserRole + 1)
            file_stem, file_ext = str(resource.resref), resource.restype.extension
            filepath: Path = Path(temp_dir, f"{file_stem}.{file_ext}")
            filepath.write_bytes(resource.data)
            urls.append(QUrl.fromLocalFile(str(filepath)))

        mime_data = QMimeData()
        mime_data.setUrls(urls)
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)
        drag.exec(Qt.DropAction.CopyAction, Qt.DropAction.CopyAction)
