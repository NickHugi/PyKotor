from __future__ import annotations

from typing import TYPE_CHECKING

from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QStackedWidget, QStyle, QToolButton, QWhatsThis

from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialogcombobox import QFileDialogComboBox  # noqa: TID252
from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialoglineedit import QFileDialogLineEdit  # noqa: TID252
from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialoglistview import QFileDialogListView  # noqa: TID252
from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialogtreeview import QFileDialogTreeView  # noqa: TID252
from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qsidebar import QSidebar  # noqa: TID252
from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.ui_qfiledialog import Ui_QFileDialog  # noqa: TID252
from utility.ui_libraries.qt.widgets.itemviews.headerview import RobustHeaderView
from utility.ui_libraries.qt.widgets.itemviews.listview import RobustListView
from utility.ui_libraries.qt.widgets.itemviews.tableview import RobustTableView
from utility.ui_libraries.qt.widgets.itemviews.tileview import RobustTileView

if TYPE_CHECKING:
    from typing_extensions import Self

    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.private.qfiledialog import QFileDialog
    from utility.ui_libraries.qt.filesystem.explorer.qfiledialog.tests.oldtst_qtpyfiledialog import TestQFileDialog  # noqa: TID252



class UI_PyFileExplorer(Ui_QFileDialog):  # noqa: N801
    def __init__(self):
        super().__init__(self)

    def listView(self) -> RobustListView | None:
        return next((view for view in self.stackedWidget.all_views if isinstance(view, RobustListView)), None)

    def tableView(self) -> RobustTableView | None:
        return next((view for view in self.stackedWidget.all_views if isinstance(view, RobustTableView)), None)

    def headerView(self) -> RobustHeaderView | None:
        return next((view for view in self.stackedWidget.all_views if isinstance(view, RobustHeaderView)), None)

    def tilesView(self) -> RobustTileView | None:
        return next((view for view in self.stackedWidget.all_views if isinstance(view, RobustTileView)), None)

    def setupUi(self, PyQFileDialog: QFileDialog) -> Self:  # noqa: N803
        super().setupUi(PyQFileDialog)
        self._override_ui_elements(PyQFileDialog)
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
        self.listView().setHidden(self.toggleHiddenButton.isChecked())
        self.tableView().setHidden(self.toggleHiddenButton.isChecked())
        self.tilesView().setHidden(self.toggleHiddenButton.isChecked())

    def _override_ui_elements(self, PyQFileDialog: TestQFileDialog):  # noqa: N803
        """Override the UI elements of the QFileDialog.

        This is done by replacing the original widgets with our custom widgets.
        This allows us to have more control over the widgets and to add our
        custom functionality to them.

        Because we cannot access the private attributes of the QFileDialog, we need
        to override the widgets manually, without overriding more than the ones
        that are needed.
        """
        # Override lookInCombo
        self.lookInCombo = QFileDialogComboBox(PyQFileDialog)
        self.gridlayout.replaceWidget(self.lookInCombo, self.lookInCombo)

        # Override fileNameEdit
        self.fileNameEdit = QFileDialogLineEdit(PyQFileDialog)
        self.gridlayout.replaceWidget(self.fileNameEdit, self.fileNameEdit)

        # Override sidebar
        self.sidebar = QSidebar(PyQFileDialog)
        self.splitter.replaceWidget(0, self.sidebar)

        # Override stackedWidget

        self.stackedWidget = QStackedWidget(self.frame)
        self.vboxlayout.replaceWidget(self.stackedWidget, self.stackedWidget)

        # Override listView
        self.listView = QFileDialogListView(self.stackedWidget)
        self.stackedWidget.addWidget(self.listView)

        # Override treeView

        self.treeView = QFileDialogTreeView(self.stackedWidget)
        self.stackedWidget.addWidget(self.treeView)

        # Add custom buttons
        self.add_custom_buttons(PyQFileDialog)
