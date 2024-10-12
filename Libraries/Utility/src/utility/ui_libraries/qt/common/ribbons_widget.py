from __future__ import annotations

from qtpy.QtCore import QSize, Qt
from qtpy.QtGui import QAction
from qtpy.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QMenu, QSizePolicy, QTabWidget, QToolButton, QVBoxLayout, QWidget

from utility.ui_libraries.qt.common.action_definitions import FileExplorerActions
from utility.ui_libraries.qt.common.column_options_dialog import SetDefaultColumnsDialog
from utility.ui_libraries.qt.common.menu_definitions import FileExplorerMenus


class RibbonsWidget(QWidget):
    def __init__(
        self,
        parent: QWidget | None = None,
        flags: Qt.WindowFlags | Qt.WindowType | None = None,
        menus: FileExplorerMenus | None = None,
    ):
        if flags is None:
            super().__init__(parent)
        else:
            super().__init__(parent, flags)
        self.actions_definitions: FileExplorerActions = FileExplorerActions()
        self.menus: FileExplorerMenus = FileExplorerMenus() if menus is None else menus
        self.setup_main_layout()
        self.set_stylesheet()

    def setup_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.tab_widget: QTabWidget = QTabWidget()

        file_tab = QWidget()
        self.setup_file_ribbon(file_tab)
        self.tab_widget.addTab(file_tab, "File")

        home_tab = QWidget()
        self.setup_home_ribbon(home_tab)
        self.tab_widget.addTab(home_tab, "Home")

        share_tab = QWidget()
        self.tab_widget.addTab(share_tab, "Share")

        view_tab = QWidget()
        self.setup_view_ribbon(view_tab)
        self.tab_widget.addTab(view_tab, "View")

        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

    def setup_file_ribbon(self, tab: QWidget):
        # Implement file ribbon layout here
        pass

    def setup_home_ribbon(self, tab: QWidget):
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_clipboard_group())
        layout.addWidget(self.create_organize_group())
        layout.addWidget(self.create_new_group())
        layout.addWidget(self.create_open_group())
        layout.addWidget(self.create_select_group())
        layout.addStretch()

        tab.setLayout(layout)

    def setup_view_ribbon(self, tab: QWidget):
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_panes_group())
        layout.addWidget(self.create_layout_group())
        layout.addWidget(self.create_current_view_group())
        layout.addWidget(self.create_show_hide_group())
        layout.addStretch()

        tab.setLayout(layout)

    def create_clipboard_group(self) -> QGroupBox:
        group = QGroupBox("Clipboard")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        top_row.addWidget(self.create_large_button("Pin to\nQuick access", self.actions_definitions.actionPinToQuickAccess))
        top_row.addWidget(self.create_large_button("Copy", self.actions_definitions.actionCopy))
        top_row.addWidget(self.create_large_button("Paste", self.actions_definitions.actionPaste))

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.create_small_button("Cut", self.actions_definitions.actionCut))
        bottom_row.addWidget(self.create_small_button("Copy path", self.actions_definitions.actionCopyPath))
        bottom_row.addWidget(self.create_small_button("Paste shortcut", self.actions_definitions.actionPasteShortcut))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_organize_group(self) -> QGroupBox:
        group = QGroupBox("Organize")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        move_to_button = self.create_large_button("Move to", self.actions_definitions.actionMoveTo)
        move_to_button.setMenu(QMenu())
        top_row.addWidget(move_to_button)

        copy_to_button = self.create_large_button("Copy to", self.actions_definitions.actionCopyTo)
        copy_to_button.setMenu(QMenu())
        top_row.addWidget(copy_to_button)

        bottom_row = QHBoxLayout()
        delete_button = self.create_small_button("Delete", self.actions_definitions.actionDelete)
        delete_button.setMenu(QMenu())
        bottom_row.addWidget(delete_button)
        bottom_row.addWidget(self.create_small_button("Rename", self.actions_definitions.actionRename))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_new_group(self) -> QGroupBox:
        group = QGroupBox("New")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        new_folder_button = self.create_large_button("New\nfolder", self.actions_definitions.actionCreateNewFolder)
        layout.addWidget(new_folder_button)

        new_item_button = self.create_small_button("New item", self.actions_definitions.actionNewBlankFile)
        new_item_button.setMenu(QMenu())
        layout.addWidget(new_item_button)

        group.setLayout(layout)
        return group

    def create_open_group(self) -> QGroupBox:
        group = QGroupBox("Open")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        properties_button = self.create_large_button("Properties", self.actions_definitions.actionProperties)
        top_row.addWidget(properties_button)

        bottom_row = QHBoxLayout()
        open_button = self.create_small_button("Open", self.actions_definitions.actionOpen)
        open_button.setMenu(QMenu())
        bottom_row.addWidget(open_button)
        bottom_row.addWidget(self.create_small_button("Edit", self.actions_definitions.actionEdit))

        easy_access_button = self.create_small_button("Easy access", QAction())
        easy_access_button.setMenu(QMenu())
        bottom_row.addWidget(easy_access_button)

        bottom_row.addWidget(self.create_small_button("History", QAction()))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_select_group(self) -> QGroupBox:
        group = QGroupBox("Select")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_small_button("Select all", self.actions_definitions.actionSelectAll))
        layout.addWidget(self.create_small_button("Select none", self.actions_definitions.actionSelectNone))
        layout.addWidget(self.create_small_button("Invert selection", self.actions_definitions.actionInvertSelection))

        group.setLayout(layout)
        return group

    def create_panes_group(self) -> QGroupBox:
        group = QGroupBox("Panes")
        layout = QHBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        navigation_pane_button = self.create_large_button("Navigation\npane", self.actions_definitions.actionNavigationPane)
        navigation_pane_button.setMenu(QMenu())
        layout.addWidget(navigation_pane_button)
        layout.addWidget(self.create_large_button("Preview\npane", self.actions_definitions.actionPreviewPane))
        layout.addWidget(self.create_large_button("Details\npane", self.actions_definitions.actionDetailsPane))

        group.setLayout(layout)
        return group

    def create_layout_group(self) -> QGroupBox:
        group = QGroupBox("Layout")
        layout = QGridLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_small_button("Extra large\nicons", self.actions_definitions.actionExtraLargeIcons), 0, 0)
        layout.addWidget(self.create_small_button("Large\nicons", self.actions_definitions.actionLargeIcons), 0, 1)
        layout.addWidget(self.create_small_button("Medium\nicons", self.actions_definitions.actionMediumIcons), 0, 2)
        layout.addWidget(self.create_small_button("Small\nicons", self.actions_definitions.actionSmallIcons), 1, 0)
        layout.addWidget(self.create_small_button("List", self.actions_definitions.actionListView), 1, 1)
        layout.addWidget(self.create_small_button("Details", self.actions_definitions.actionDetailView), 1, 2)
        layout.addWidget(self.create_small_button("Tiles", self.actions_definitions.actionTiles), 2, 0)
        layout.addWidget(self.create_small_button("Content", self.actions_definitions.actionContent), 2, 1)

        group.setLayout(layout)
        return group

    def create_current_view_group(self) -> QGroupBox:
        group = QGroupBox("Current view")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        top_row = QHBoxLayout()
        sort_by_button = self.create_small_button("Sort by", QAction())
        sort_by_menu = QMenu()
        sort_by_menu.addAction("Name")
        sort_by_menu.addAction("Date modified")
        sort_by_menu.addAction("Type")
        sort_by_menu.addAction("Size")
        sort_by_button.setMenu(sort_by_menu)
        top_row.addWidget(sort_by_button)

        group_by_button = self.create_small_button("Group by", QAction())
        group_by_menu = QMenu()
        group_by_menu.addAction("None")
        group_by_menu.addAction("Name")
        group_by_menu.addAction("Date modified")
        group_by_menu.addAction("Type")
        group_by_menu.addAction("Size")
        group_by_button.setMenu(group_by_menu)
        top_row.addWidget(group_by_button)

        bottom_row = QHBoxLayout()
        add_columns_button = self.create_small_button("Add columns", QAction())
        add_columns_button.clicked.connect(self.show_set_default_columns_dialog)
        bottom_row.addWidget(add_columns_button)
        bottom_row.addWidget(self.create_small_button("Size all\ncolumns to fit", QAction()))

        layout.addLayout(top_row)
        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def show_set_default_columns_dialog(self):
        dialog = SetDefaultColumnsDialog(self)
        dialog.exec()

    def create_show_hide_group(self) -> QGroupBox:
        group = QGroupBox("Show/hide")
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        layout.addWidget(self.create_checkbox_button("Item check boxes", QAction()))
        layout.addWidget(self.create_checkbox_button("File name extensions", QAction()))
        layout.addWidget(self.create_checkbox_button("Hidden items", QAction()))

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.create_small_button("Hide selected\nitems", QAction()))
        bottom_row.addWidget(self.create_small_button("Options", self.actions_definitions.actionOptions))

        layout.addLayout(bottom_row)
        group.setLayout(layout)
        return group

    def create_large_button(self, text: str, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        button.setFixedSize(80, 70)
        button.setIconSize(QSize(32, 32))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        return button

    def create_small_button(self, text: str, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setFixedSize(80, 22)
        button.setIconSize(QSize(16, 16))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        return button

    def create_checkbox_button(self, text: str, action: QAction) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        button.setFixedSize(120, 22)
        button.setIconSize(QSize(16, 16))
        button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        button.setCheckable(True)
        return button

    def set_stylesheet(self):
        self.setStyleSheet("""
            QTabWidget::pane {
                border-top: 1px solid #C0C0C0;
                position: absolute;
                top: -1px;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #F0F0F0, stop: 0.4 #DEDEDE,
                                            stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
                border: 1px solid #C4C4C3;
                border-bottom-color: #C2C7CB;
                min-width: 8ex;
                padding: 2px 8px;
            }
            QTabBar::tab:selected, QTabBar::tab:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                            stop: 0 #fafafa, stop: 0.4 #f4f4f4,
                                            stop: 0.5 #e7e7e7, stop: 1.0 #e0e0e0);
            }
            QTabBar::tab:selected {
                border-color: #9B9B9B;
                border-bottom-color: #C2C7CB;
            }
            QGroupBox {
                border: 1px solid #C0C0C0;
                border-radius: 4px;
                margin-top: 0.5em;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 7px;
                padding: 0 3px 0 3px;
            }
            QToolButton {
                border: 1px solid transparent;
                border-radius: 2px;
                background-color: transparent;
            }
            QToolButton:hover {
                border: 1px solid #C0C0C0;
                background-color: #E5F3FF;
            }
            QToolButton:pressed, QToolButton:checked {
                border: 1px solid #0078D7;
                background-color: #CCE8FF;
            }
        """)

if __name__ == "__main__":
    import sys

    from qtpy.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = QWidget()
    layout = QVBoxLayout(window)

    ribbons_widget = RibbonsWidget()
    layout.addWidget(ribbons_widget)

    window.setWindowTitle("Explorer Ribbon Test")
    window.setGeometry(100, 100, 1200, 200)
    window.show()

    sys.exit(app.exec())
