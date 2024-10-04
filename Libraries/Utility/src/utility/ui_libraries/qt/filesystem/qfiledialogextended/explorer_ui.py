from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import (
    QComboBox,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QListView,
    QSplitter,
    QStackedWidget,
    QStyle,
    QToolButton,
    QTreeView,
    QVBoxLayout,
    QWhatsThis,
    QWidget,
)

from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.private.qfiledialogcombobox import QFileDialogComboBox  # noqa: TID252
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.private.qfiledialoglineedit import QFileDialogLineEdit  # noqa: TID252
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.private.qsidebar import QSidebar  # noqa: TID252
from utility.ui_libraries.qt.adapters.filesystem.qfiledialog.rewritten.ui_qfiledialog import Ui_QFileDialog  # noqa: TID252
from utility.ui_libraries.qt.widgets.widgets.stacked_view import DynamicStackedView

if TYPE_CHECKING:
    from qtpy.QtWidgets import QFileDialog, QLayout
    from typing_extensions import Self

    from utility.ui_libraries.qt.filesystem.qfiledialogextended.explorer import QFileExplorer

class UI_PyFileExplorer(Ui_QFileDialog if TYPE_CHECKING else object):  # noqa: N801
    def setupUi(self, QFileExplorer: QFileExplorer) -> Self:  # noqa: N803, PLR0915
        gridlayout: QLayout | None = QFileExplorer.layout()
        assert isinstance(gridlayout, QGridLayout)
        self.gridlayout: QGridLayout = gridlayout

        # Look In label and combo
        look_in_label: QLabel | None = QFileExplorer.findChild(QLabel, "lookInLabel")
        assert isinstance(look_in_label, QLabel)
        self.lookInLabel: QLabel = look_in_label

        look_in_combo: QComboBox | None = QFileExplorer.findChild(QComboBox, "lookInCombo")
        assert isinstance(look_in_combo, QComboBox)
        self.lookInCombo: QComboBox = look_in_combo

        # Toolbar buttons
        back_button: QToolButton | None = QFileExplorer.findChild(QToolButton, "backButton")
        assert isinstance(back_button, QToolButton)
        self.backButton: QToolButton = back_button

        forward_button: QToolButton | None = QFileExplorer.findChild(QToolButton, "forwardButton")
        assert isinstance(forward_button, QToolButton)
        self.forwardButton: QToolButton = forward_button

        to_parent_button: QToolButton | None = QFileExplorer.findChild(QToolButton, "toParentButton")
        assert isinstance(to_parent_button, QToolButton)
        self.toParentButton: QToolButton = to_parent_button

        new_folder_button: QToolButton | None = QFileExplorer.findChild(QToolButton, "newFolderButton")
        assert isinstance(new_folder_button, QToolButton)
        self.newFolderButton: QToolButton = new_folder_button

        list_mode_button: QToolButton | None = QFileExplorer.findChild(QToolButton, "listModeButton")
        assert isinstance(list_mode_button, QToolButton)
        self.listModeButton: QToolButton = list_mode_button

        detail_mode_button: QToolButton | None = QFileExplorer.findChild(QToolButton, "detailModeButton")
        assert isinstance(detail_mode_button, QToolButton)
        self.detailModeButton: QToolButton = detail_mode_button

        # Splitter
        splitter: QSplitter | None = QFileExplorer.findChild(QSplitter, "splitter")
        assert isinstance(splitter, QSplitter)
        self.splitter: QSplitter = splitter

        # Sidebar
        sidebar: QFrame | None = QFileExplorer.findChild(QFrame, "sidebar")  # QFileDialogSidebar
        assert isinstance(sidebar, QFrame)
        self.sidebar: QFrame = sidebar

        # Main frame
        frame: QFrame | None = QFileExplorer.findChild(QFrame, "frame")
        assert isinstance(frame, QFrame)
        self.frame: QFrame = frame

        # Stacked widget for list and tree views
        stacked_widget: QStackedWidget | None = QFileExplorer.findChild(QStackedWidget, "stackedWidget")
        assert isinstance(stacked_widget, QStackedWidget)
        self.stackedWidget = stacked_widget
        assert self.stackedWidget.count() == 2, "StackedWidget should contain 2 pages"

        # List view page
        page: QWidget | None = self.stackedWidget.widget(0)
        assert isinstance(page, QWidget)
        self.page: QWidget = page

        list_view: QListView | None = QFileExplorer.findChild(QListView, "listView")  # QFileDialogListView
        assert isinstance(list_view, QListView)
        self.listView: QListView = list_view

        # Tree view page
        page_2: QWidget | None = self.stackedWidget.widget(1)
        assert isinstance(page_2, QWidget)
        self.page_2: QWidget = page_2

        tree_view: QTreeView | None = QFileExplorer.findChild(QTreeView, "treeView")  # QFileDialogTreeView
        assert isinstance(tree_view, QTreeView)
        self.treeView: QTreeView = tree_view

        # File name label and edit
        file_name_label: QLabel | None = QFileExplorer.findChild(QLabel, "fileNameLabel")
        assert isinstance(file_name_label, QLabel)
        self.fileNameLabel: QLabel = file_name_label

        file_name_edit: QLineEdit | None = QFileExplorer.findChild(QLineEdit, "fileNameEdit")  # QFileDialogLineEdit
        assert isinstance(file_name_edit, QLineEdit)
        self.fileNameEdit: QLineEdit = file_name_edit

        # Button box
        button_box: QDialogButtonBox | None = QFileExplorer.findChild(QDialogButtonBox, "buttonBox")
        assert isinstance(button_box, QDialogButtonBox)
        self.buttonBox: QDialogButtonBox = button_box

        # File type label and combo
        file_type_label: QLabel | None = QFileExplorer.findChild(QLabel, "fileTypeLabel")
        assert isinstance(file_type_label, QLabel)
        self.fileTypeLabel: QLabel = file_type_label

        file_type_combo: QComboBox | None = QFileExplorer.findChild(QComboBox, "fileTypeCombo")
        assert isinstance(file_type_combo, QComboBox)
        self.fileTypeCombo: QComboBox = file_type_combo

        # Define layouts based on found widgets
        vboxlayout: QLayout | None = self.frame.layout()
        assert isinstance(vboxlayout, QVBoxLayout)
        self.vboxlayout: QVBoxLayout = vboxlayout

        vboxlayout1: QLayout | None = self.page.layout()
        assert isinstance(vboxlayout1, QVBoxLayout)
        self.vboxlayout1: QVBoxLayout = vboxlayout1

        vboxlayout2: QLayout | None = self.page_2.layout()
        assert isinstance(vboxlayout2, QVBoxLayout)
        self.vboxlayout2: QVBoxLayout = vboxlayout2

        hboxlayout: QLayout | None = self.gridlayout.itemAtPosition(0, 1).layout()
        assert isinstance(hboxlayout, QHBoxLayout)
        self.hboxlayout: QHBoxLayout = hboxlayout

        # Assert correct widget containment
        assert self.gridlayout.itemAtPosition(0, 0).widget() == self.lookInLabel
        assert self.gridlayout.itemAtPosition(0, 1).layout() == self.hboxlayout
        assert self.gridlayout.itemAtPosition(1, 0).widget() == self.splitter
        assert self.gridlayout.itemAtPosition(2, 0).widget() == self.fileNameLabel
        assert self.gridlayout.itemAtPosition(2, 1).widget() == self.fileNameEdit
        assert self.gridlayout.itemAtPosition(2, 2).widget() == self.buttonBox
        assert self.gridlayout.itemAtPosition(3, 0).widget() == self.fileTypeLabel
        assert self.gridlayout.itemAtPosition(3, 1).widget() == self.fileTypeCombo

        assert self.hboxlayout.itemAt(0).widget() == self.lookInCombo
        assert self.hboxlayout.itemAt(1).widget() == self.backButton
        assert self.hboxlayout.itemAt(2).widget() == self.forwardButton
        assert self.hboxlayout.itemAt(3).widget() == self.toParentButton
        assert self.hboxlayout.itemAt(4).widget() == self.newFolderButton
        assert self.hboxlayout.itemAt(5).widget() == self.listModeButton
        assert self.hboxlayout.itemAt(6).widget() == self.detailModeButton

        assert self.splitter.widget(0) == self.sidebar
        assert self.splitter.widget(1) == self.frame

        assert self.vboxlayout.itemAt(0).widget() == self.stackedWidget

        assert self.stackedWidget.widget(0) == self.page
        assert self.stackedWidget.widget(1) == self.page_2

        assert self.vboxlayout1.itemAt(0).widget() == self.listView
        assert self.vboxlayout2.itemAt(0).widget() == self.treeView

        assert self.page.layout() == self.vboxlayout1
        assert self.page_2.layout() == self.vboxlayout2
        return self


    def add_custom_buttons(self, file_dialog: QFileDialog):  # noqa: N803
        self.toggleHiddenButton = QToolButton(file_dialog)

        self.toggleHiddenButton.setIcon(QIcon.fromTheme("view-hidden"))
        self.toggleHiddenButton.setToolTip("Show/hide hidden files")
        self.toggleHiddenButton.setCheckable(True)
        self.hboxlayout.addWidget(self.toggleHiddenButton)

        # Add whatsThisButton
        self.whatsThisButton = QToolButton(file_dialog)
        dialog_style: QStyle | None = file_dialog.style()
        if dialog_style is None:
            raise RuntimeError("QFileDialog.style() returned None")  # pragma: no cover

        self.whatsThisButton.setIcon(dialog_style.standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion))

        self.whatsThisButton.setToolTip("What's This?")
        self.whatsThisButton.setAutoRaise(True)
        self.hboxlayout.addWidget(self.whatsThisButton)

        self.whatsThisButton.clicked.connect(QWhatsThis.enterWhatsThisMode)

        self.toggleHiddenButton.clicked.connect(self.on_toggle_hidden_files)

    def on_toggle_hidden_files(self):
        self.listView.setHidden(self.toggleHiddenButton.isChecked())
        self.stackedWidget.table_view().setHidden(self.toggleHiddenButton.isChecked())
        self.treeView.setHidden(self.toggleHiddenButton.isChecked())

    def _override_ui_elements(self, QFileDialog: QFileDialog):  # noqa: N803
        """Override the UI elements of the QFileDialog.

        This is done by replacing the original widgets with our custom widgets.
        This allows us to have more control over the widgets and to add our
        custom functionality to them.

        Because we cannot access the private attributes of the QFileDialog, we need
        to override the widgets manually, without overriding more than the ones
        that are needed.
        """
        # Override lookInCombo
        self.lookInCombo = QFileDialogComboBox(QFileDialog)
        self.gridlayout.replaceWidget(self.lookInCombo, self.lookInCombo)

        # Override fileNameEdit
        self.fileNameEdit = QFileDialogLineEdit(QFileDialog)
        self.gridlayout.replaceWidget(self.fileNameEdit, self.fileNameEdit)

        # Override sidebar
        self.sidebar = QSidebar(QFileDialog)
        self.splitter.replaceWidget(0, self.sidebar)

        # Override stackedWidget
        stackedWidget = DynamicStackedView()
        self.vboxlayout.replaceWidget(self.stackedWidget, stackedWidget)
        self.stackedWidget: QStackedWidget | DynamicStackedView = stackedWidget
        listView = self.stackedWidget.list_view()
        treeView = self.stackedWidget.tree_view()
        assert treeView is not None, "TreeView not found in DynamicView stackedWidget"
        assert listView is not None, "ListView not found in DynamicView stackedWidget"
        self.listView = listView
        self.treeView = treeView

        # Add custom buttons
        self.add_custom_buttons(QFileDialog)
