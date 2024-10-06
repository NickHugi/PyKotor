
################################################################################
## Form generated from reading UI file 'erf.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################
from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QMetaObject, QRect, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QAbstractItemView, QHBoxLayout, QMenu, QMenuBar, QPushButton, QVBoxLayout, QWidget

from toolset.gui.editors.erf import ERFEditorTable


class Ui_MainWindow:
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.resize(306, 369)
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
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tableView = ERFEditorTable(self.centralwidget)
        self.tableView.setObjectName("tableView")
        self.tableView.setAcceptDrops(True)
        self.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableView.setDragEnabled(True)
        self.tableView.setDragDropMode(QAbstractItemView.DragDrop)
        self.tableView.setDefaultDropAction(Qt.CopyAction)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setGridStyle(Qt.NoPen)
        self.tableView.verticalHeader().setVisible(False)

        self.verticalLayout.addWidget(self.tableView)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.extractButton = QPushButton(self.centralwidget)
        self.extractButton.setObjectName("extractButton")
        self.extractButton.setEnabled(False)

        self.horizontalLayout_2.addWidget(self.extractButton)

        self.openButton = QPushButton(self.centralwidget)
        self.openButton.setObjectName("openButton")
        self.openButton.setEnabled(False)

        self.horizontalLayout_2.addWidget(self.openButton)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.loadButton = QPushButton(self.centralwidget)
        self.loadButton.setObjectName("loadButton")

        self.horizontalLayout.addWidget(self.loadButton)

        self.unloadButton = QPushButton(self.centralwidget)
        self.unloadButton.setObjectName("unloadButton")
        self.unloadButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.unloadButton)

        self.refreshButton = QPushButton(self.centralwidget)
        self.refreshButton.setObjectName("refreshButton")
        self.refreshButton.setEnabled(False)

        self.horizontalLayout.addWidget(self.refreshButton)


        self.verticalLayout.addLayout(self.horizontalLayout)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 306, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menuFile.addAction(self.actionNew)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionSave)
        self.menuFile.addAction(self.actionSaveAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionRevert)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)

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
        self.extractButton.setText(QCoreApplication.translate("MainWindow", "Extract", None))
        self.openButton.setText(QCoreApplication.translate("MainWindow", "Open", None))
        self.loadButton.setText(QCoreApplication.translate("MainWindow", "Add", None))
        self.unloadButton.setText(QCoreApplication.translate("MainWindow", "Remove", None))
        self.refreshButton.setText(QCoreApplication.translate("MainWindow", "Reload", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", "File", None))
    # retranslateUi

