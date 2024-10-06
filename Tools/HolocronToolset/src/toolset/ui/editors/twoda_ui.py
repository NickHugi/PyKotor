
################################################################################
## Form generated from reading UI file 'twoda.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractItemView, QGroupBox, QLineEdit, QMenu, QMenuBar, QVBoxLayout, QWidget

from utility.ui_libraries.qt.widgets.itemviews.treeview import RobustTableView


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(635, 454)
        self.actionNew = QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.actionOpen = QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName("actionSave")
        self.actionSaveAs = QAction(MainWindow)
        self.actionSaveAs.setObjectName("actionSaveAs")
        self.actionRevert = QAction(MainWindow)
        self.actionRevert.setObjectName("actionRevert")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionToggleFilter = QAction(MainWindow)
        self.actionToggleFilter.setObjectName("actionToggleFilter")
        self.actionCopy = QAction(MainWindow)
        self.actionCopy.setObjectName("actionCopy")
        self.actionPaste = QAction(MainWindow)
        self.actionPaste.setObjectName("actionPaste")
        self.actionInsertRow = QAction(MainWindow)
        self.actionInsertRow.setObjectName("actionInsertRow")
        self.actionRemoveRows = QAction(MainWindow)
        self.actionRemoveRows.setObjectName("actionRemoveRows")
        self.actionRedoRowLabels = QAction(MainWindow)
        self.actionRedoRowLabels.setObjectName("actionRedoRowLabels")
        self.actionDuplicateRow = QAction(MainWindow)
        self.actionDuplicateRow.setObjectName("actionDuplicateRow")
        self.actionplaceholder = QAction(MainWindow)
        self.actionplaceholder.setObjectName("actionplaceholder")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.filterBox = QGroupBox(self.centralwidget)
        self.filterBox.setObjectName("filterBox")
        self.verticalLayout = QVBoxLayout(self.filterBox)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filterEdit = QLineEdit(self.filterBox)
        self.filterEdit.setObjectName("filterEdit")

        self.verticalLayout.addWidget(self.filterEdit)


        self.verticalLayout_2.addWidget(self.filterBox)

        self.twodaTable = RobustTableView(self.centralwidget)
        self.twodaTable.setObjectName("twodaTable")
        self.twodaTable.setStyleSheet("")
        self.twodaTable.setAlternatingRowColors(True)
        self.twodaTable.setSelectionMode(QAbstractItemView.ContiguousSelection)

        self.verticalLayout_2.addWidget(self.twodaTable)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 635, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuEdit = QMenu(self.menubar)
        self.menuEdit.setObjectName("menuEdit")
        self.menuTools = QMenu(self.menubar)
        self.menuTools.setObjectName("menuTools")
        self.menuView = QMenu(self.menubar)
        self.menuView.setObjectName("menuView")
        self.menuSetRowHeader = QMenu(self.menuView)
        self.menuSetRowHeader.setObjectName("menuSetRowHeader")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuView.menuAction())
        self.menubar.addAction(self.menuEdit.menuAction())
        self.menubar.addAction(self.menuTools.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuEdit.addAction(self.actionCopy)
        self.menuEdit.addAction(self.actionPaste)
        self.menuTools.addAction(self.actionToggleFilter)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionInsertRow)
        self.menuTools.addAction(self.actionDuplicateRow)
        self.menuTools.addAction(self.actionRemoveRows)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionRedoRowLabels)
        self.menuView.addAction(self.menuSetRowHeader.menuAction())
        self.menuSetRowHeader.addAction(self.actionplaceholder)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "MainWindow", None))
        self.actionNew.setText(QCoreApplication.translate("MainWindow", "New", None))
        self.actionOpen.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", "Save", None))
        self.actionSaveAs.setText(QCoreApplication.translate("MainWindow", "Save As", None))
        self.actionRevert.setText(QCoreApplication.translate("MainWindow", "Revert", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", "Exit", None))
        self.actionToggleFilter.setText(QCoreApplication.translate("MainWindow", "Toggle Filter", None))
#if QT_CONFIG(shortcut)
        self.actionToggleFilter.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+F", None))
#endif // QT_CONFIG(shortcut)
        self.actionCopy.setText(QCoreApplication.translate("MainWindow", "Copy", None))
#if QT_CONFIG(shortcut)
        self.actionCopy.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+C", None))
#endif // QT_CONFIG(shortcut)
        self.actionPaste.setText(QCoreApplication.translate("MainWindow", "Paste", None))
#if QT_CONFIG(shortcut)
        self.actionPaste.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+V", None))
#endif // QT_CONFIG(shortcut)
        self.actionInsertRow.setText(QCoreApplication.translate("MainWindow", "Insert Row", None))
#if QT_CONFIG(shortcut)
        self.actionInsertRow.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+I", None))
#endif // QT_CONFIG(shortcut)
        self.actionRemoveRows.setText(QCoreApplication.translate("MainWindow", "Remove Rows", None))
#if QT_CONFIG(shortcut)
        self.actionRemoveRows.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+Del", None))
#endif // QT_CONFIG(shortcut)
        self.actionRedoRowLabels.setText(QCoreApplication.translate("MainWindow", "Redo Row Labels", None))
#if QT_CONFIG(shortcut)
        self.actionRedoRowLabels.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+L", None))
#endif // QT_CONFIG(shortcut)
        self.actionDuplicateRow.setText(QCoreApplication.translate("MainWindow", "Duplicate Row", None))
#if QT_CONFIG(shortcut)
        self.actionDuplicateRow.setShortcut(QCoreApplication.translate("MainWindow", "Ctrl+D", None))
#endif // QT_CONFIG(shortcut)
        self.actionplaceholder.setText(QCoreApplication.translate("MainWindow", "placeholder", None))
        self.filterBox.setTitle(QCoreApplication.translate("MainWindow", "Filter", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
        self.menuEdit.setTitle(QCoreApplication.translate("MainWindow", "Edit", None))
        self.menuTools.setTitle(QCoreApplication.translate("MainWindow", "Tools", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", "View", None))
        self.menuSetRowHeader.setTitle(QCoreApplication.translate("MainWindow", "Set Row Header", None))
    # retranslateUi

